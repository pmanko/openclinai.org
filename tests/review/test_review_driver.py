"""`make review` driver on a fixture repository, a stubbed `gh` and the human agent."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "review" / "bin" / "review.py"

GH = """#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:3] == ["api", "graphql"]:
    print(json.dumps({"data": {"repository": {"pullRequest": {
        "number": 1, "title": "Clamp", "body": "Fixes the low end", "url": "u",
        "author": {"login": "dev"}, "baseRefName": "main", "headRefName": "fix",
        "headRefOid": "x", "state": "OPEN", "closingIssuesReferences": {"nodes": []},
        "comments": {"nodes": []}, "reviewThreads": {"nodes": [{"id": "t1",
        "isResolved": False, "isOutdated": False, "path": "calc.py", "line": 2,
        "originalLine": 2, "comments": {"nodes": [{"author": {"login": "maint"},
        "createdAt": "2026-10-20T00:00:00Z", "body": "Low end?", "url": "c1"}]}}]}}}}}))
elif sys.argv[1:3] == ["pr", "view"]:
    print(os.environ["REVIEW_IDENTITY"])
else:
    print("[]")
"""


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def test_review_checks_the_actual_checkout_revision_and_cleanliness(tmp_path):
    import pytest
    import runpy
    verify = runpy.run_path(str(REVIEW))["verify_checkout"]
    git(tmp_path, "init", "-q")
    (tmp_path / "behavior.py").write_text("value = 1\n")
    git(tmp_path, "add", "behavior.py")
    git(tmp_path, "-c", "user.email=d@example.test", "-c", "user.name=D", "commit", "-qm", "base")
    revision = git(tmp_path, "rev-parse", "HEAD")
    verify(tmp_path, revision)
    (tmp_path / "behavior.py").write_text("value = 2\n")
    with pytest.raises(ValueError):
        verify(tmp_path, revision)
    git(tmp_path, "add", "behavior.py")
    git(tmp_path, "-c", "user.email=d@example.test", "-c", "user.name=D", "commit", "-qm", "changed")
    with pytest.raises(ValueError):
        verify(tmp_path, revision)


def test_fixer_requires_explicit_authorization(tmp_path, monkeypatch):
    import runpy
    from types import SimpleNamespace
    api = runpy.run_path(str(REVIEW))
    state = api['main'].__globals__
    monkeypatch.setitem(state, 'UMBRELLA', tmp_path)
    monkeypatch.setitem(state, 'work_dir', lambda: tmp_path / 'work')
    monkeypatch.setitem(state, 'upstream', lambda *args: ('origin', 'fixture/repo'))
    monkeypatch.setitem(state, 'fetch_pr', lambda *args: 'head')
    monkeypatch.setitem(state, 'current_identity', lambda *args: dict(headRefOid='head', baseRefOid='base', baseRefName='main'))
    def fake_git(repo, *args):
        if args[0] == 'rev-parse': return 'head' if args[1] == 'HEAD' else 'base'
        if args[0] == 'diff': return 'calc.py'
        return ''
    monkeypatch.setitem(state, 'git', fake_git)
    def checkout(repo, path, revision, branch=None):
        path.mkdir(parents=True, exist_ok=True)
        (path / 'calc.py').write_text('value = 1\n')
        return path
    monkeypatch.setitem(state, 'worktree', checkout)
    def threads(command, **kwargs):
        Path(command[3]).write_text(json.dumps(dict(base='main', head_branch='fix', author='fixture')))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(state['subprocess'], 'run', threads)
    roles = []
    def role(args, name, wt, prompt, output):
        roles.append(name)
        return '```json\n' + json.dumps(dict(head='head', reviewed_files=['calc.py'],
            unreviewed_files=[], tests=[dict(command='fixture test', result='not run: fixture dependency unavailable')],
            findings=[dict(file='calc.py', line=1, finding='boundary fails', blocking=True,
                           failure_mode='boundary is incorrect', evidence='fixture assertion failed')])) + '\n```'
    monkeypatch.setitem(state, 'run_role', role)
    argv = ['review.py', '--repo', 'umbrella', '--repository', 'fixture/repo', '--pr', '1',
            '--agent', 'codex', '--rounds', '2', '--no-consumer']
    for flag, expected in [([], ['reviewer']), (['--fix'], ['reviewer', 'fixer', 'reviewer'])]:
        roles.clear()
        monkeypatch.setattr(sys, 'argv', argv + flag)
        assert api['main']() == 0
        assert roles == expected
        report = json.loads(next((tmp_path / 'work').rglob('result.json')).read_text())
        assert report['scope'] == 'source_review'
        assert report['tests'][0]['result'].startswith('not run:')


def test_a_round_records_findings_and_downgrades_unevidenced_blockers(tmp_path):
    upstream = tmp_path / "github.com" / "openmrs" / "calc.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(upstream))
    repo = tmp_path / "calc"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "-c", "user.email=d@example.test", "-c", "user.name=D", "commit", "-q",
        "--allow-empty", "-m", "base")
    git(repo, "remote", "add", "upstream", str(upstream))
    git(repo, "push", "-q", "upstream", "main")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "calc.py").write_text("x = 1\n")
    git(repo, "add", "calc.py")
    git(repo, "-c", "user.email=d@example.test", "-c", "user.name=D", "commit", "-q", "-m", "fix")
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "-q", "upstream", "HEAD:refs/pull/1/head")

    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "gh").write_text(GH)
    (stub / "gh").chmod(0o755)
    work = tmp_path / "work"
    env = {**os.environ, "PATH": f"{stub}:{os.environ['PATH']}", "REVIEW_WORK": str(work)}
    identity = dict(headRefOid=head, baseRefOid=base, baseRefName="main")
    env["REVIEW_IDENTITY"] = json.dumps(identity)
    cmd = [sys.executable, str(REVIEW), "--pr", "1", "--repo", "querystore",
           "--checkout", str(repo), "--agent", "human", "--effort", "low"]

    first = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert first.returncode == 3, first.stderr
    out_dir = next(work.rglob("reviewer-1.prompt.md")).parent
    prompt = (out_dir / "reviewer-1.prompt.md").read_text()
    assert head in prompt and "Effort: low" in prompt
    assert json.loads((out_dir / "threads.json").read_text())["threads"][0]["awaiting_reply"]
    assert next((work / "wt-review").rglob("calc.py")).read_text() == "x = 1\n"

    answer = {"head": head, "reviewed_files": ["calc.py"], "unreviewed_files": [], "tests": [], "findings": [
        {"file": "calc.py", "line": 1, "finding": "x is wrong", "blocking": True},
        {"file": "calc.py", "line": 1, "finding": "x breaks y", "blocking": True,
         "failure_mode": "if merged, y fails", "evidence": "pytest: 1 failed"}]}
    (out_dir / "reviewer-1.md").write_text("Done.\n```json\n" + json.dumps(answer) + "\n```\n")
    second = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert "1 blocking, 1 questions" in second.stdout
    findings = json.loads((out_dir / "findings-1.json").read_text())["findings"]
    assert [f["blocking"] for f in findings] == [False, True]
    assert "downgraded" in findings[0]

    # A source review with no findings cannot certify a changed PR comparison.
    answer["findings"] = []
    (out_dir / "reviewer-1.md").write_text("```json\n" + json.dumps(answer) + "\n```\n")
    for changed in ({"headRefOid": base}, {"baseRefOid": head}, {"baseRefName": "release"}):
        env["REVIEW_IDENTITY"] = json.dumps({**identity, **changed})
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads((out_dir / "result.json").read_text())
        assert report["execution"] == "superseded"
        assert report["assessment"] == "undetermined"

    # Select a consumer outside the default pair, from an independent Git history.
    import shutil
    umbrella = tmp_path / "umbrella"
    shutil.copytree(ROOT / "review", umbrella / "review")
    git(umbrella, "init", "-q")
    git(umbrella, "-c", "user.email=d@example.test", "-c", "user.name=D", "commit", "-qm",
        "consumer", "--allow-empty")
    consumer_head = git(umbrella, "rev-parse", "HEAD")
    env["REVIEW_IDENTITY"] = json.dumps(identity)
    selected = [cmd[0], str(umbrella / "review/bin/review.py"), *cmd[2:],
                "--consumer-repo", "umbrella", "--consumer-head", consumer_head]
    result = subprocess.run(selected, env=env, capture_output=True, text=True)
    assert result.returncode == 3, result.stderr
    assert not (out_dir / "reviewer-1.md").exists()
    assert list((out_dir / "history").rglob("reviewer-1.md"))
    (out_dir / "reviewer-1.md").write_text("```json\n" + json.dumps(answer) + "\n```\n")
    result = subprocess.run(selected, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((out_dir / "result.json").read_text())
    assert report["consumer_repo"] == "umbrella"
    assert report["consumer_head"] == consumer_head
    assert git(out_dir / "consumer/umbrella", "rev-parse", "HEAD") == consumer_head

    # Auxiliary commands must leave the completed review and its thread snapshot intact.
    saved = (out_dir / "result.json").read_bytes()
    thread_snapshot = (out_dir / "threads.json").read_bytes()
    pending_reply = subprocess.run([*cmd, "--replies"], env=env, capture_output=True, text=True)
    assert pending_reply.returncode == 3
    assert (out_dir / "result.json").read_bytes() == saved
    (out_dir / "replies.md").write_text("Draft reply only.\n")
    result = subprocess.run([*cmd, "--replies"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (out_dir / "result.json").read_bytes() == saved
    assert (out_dir / "threads.json").read_bytes() == thread_snapshot
    auxiliary = subprocess.run([*cmd, "--no-review"], env=env, capture_output=True, text=True)
    assert auxiliary.returncode == 0, auxiliary.stderr
    assert (out_dir / "result.json").read_bytes() == saved
    assert (out_dir / "threads.json").read_bytes() == thread_snapshot
    for count in ("0", "-1"):
        result = subprocess.run([*cmd, "--rounds", count], env=env, capture_output=True, text=True)
        assert result.returncode == 2
        assert (out_dir / "result.json").read_bytes() == saved

    # Even explicitly requested fix rounds must not act on a superseded report.
    answer["findings"] = [{"file": "calc.py", "line": 1, "finding": "x breaks y", "blocking": True,
                            "failure_mode": "y fails", "evidence": "fixture assertion failed"}]
    (out_dir / "reviewer-1.md").write_text("```json\n" + json.dumps(answer) + "\n```\n")
    env["REVIEW_IDENTITY"] = json.dumps({**identity, "headRefOid": base})
    result = subprocess.run([*cmd, "--fix", "--rounds", "2"], env=env, capture_output=True, text=True)
    assert result.returncode == 3, result.stdout + result.stderr
    (out_dir / "reviewer-1.md").write_text("```json\n" + json.dumps(answer) + "\n```\n")
    result = subprocess.run([*cmd, "--fix", "--rounds", "2"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads((out_dir / "result.json").read_text())["execution"] == "superseded"

    # Two forks with identical commits and PR numbers must not reuse a human answer.
    other = tmp_path / "github.com/another/calc.git"
    git(tmp_path, "clone", "-q", "--bare", str(upstream), str(other))
    git(repo, "remote", "add", "other", str(other))
    git(repo, "push", "-q", "other", "HEAD:refs/pull/1/head")
    env["REVIEW_IDENTITY"] = json.dumps(identity)
    saved = (out_dir / "result.json").read_bytes()
    result = subprocess.run([*cmd, "--repository", "another/calc"], env=env, capture_output=True, text=True)
    assert result.returncode == 3, result.stdout + result.stderr
    assert (out_dir / "result.json").read_bytes() == saved
    prompts = list(work.glob("*/reviewer-1.prompt.md"))
    assert len(prompts) == 2
    assert len(list((work / "wt-review").rglob("calc.py"))) == 2

    # Explicitly requested contract evidence cannot disappear into a clean result.
    missing = [cmd[0], str(umbrella / "review/bin/review.py"), *cmd[2:],
               "--consumer-repo", "hub", "--consumer-head", consumer_head]
    result = subprocess.run(missing, env=env, capture_output=True, text=True)
    assert result.returncode not in (0, 3), result.stdout + result.stderr
    report = json.loads((out_dir / "result.json").read_text())
    assert report["execution"] == "error" and report["assessment"] == "undetermined"
    assert report["requested_consumer_repo"] == "hub"
    assert report["requested_consumer_head"] == consumer_head
