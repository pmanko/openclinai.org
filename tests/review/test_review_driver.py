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
    out_dir = work / "querystore-1"
    prompt = (out_dir / "reviewer-1.prompt.md").read_text()
    assert head in prompt and "Effort: low" in prompt
    assert json.loads((out_dir / "threads.json").read_text())["threads"][0]["awaiting_reply"]
    assert (work / "wt-review" / "querystore" / "1" / "calc.py").read_text() == "x = 1\n"

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
