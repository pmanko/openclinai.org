"""Git hook entry points: pre-commit, commit-msg, pre-push."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from .commits import parse_trailers
from .git import ZERO, clean_env, common_dir, git, git_ok
from .guards import check_staged
from .probes import UMBRELLA, probe_commit, record_baseline

OPENMRS_URL = re.compile(r"github\.com[:/]+openmrs/", re.I)


def _say(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)


def pre_commit(repo: Path) -> int:
    report = check_staged(repo)
    _say(*report.notes)
    if report.blocking:
        _say("commit refused:", *report.blocking)
        return 1
    return 0


def commit_msg(repo: Path, message_file: str) -> int:
    trailers = parse_trailers(Path(message_file).read_text(encoding="utf-8"), repo)
    if trailers.errors:
        _say("commit refused:", *trailers.errors)
        return 1
    return 0


def _is_umbrella(repo: Path) -> bool:
    return common_dir(repo) == common_dir(UMBRELLA)


def _default_branch(repo: Path, remote: str) -> str:
    head = git(repo, "symbolic-ref", "-q", f"refs/remotes/{remote}/HEAD", check=False).strip()
    return head.rsplit("/", 1)[-1] if head else "main"


def pre_push(repo: Path, remote: str, url: str, updates: list[str]) -> int:
    if _is_umbrella(repo):
        for cmd in (["python3", "-m", "unittest", "discover", "-s", "tests"],
                    ["python3", "scripts/check_workspace.py"]):
            proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True,
                                  env=clean_env())
            if proc.returncode:
                _say(f"push refused: {' '.join(cmd)} failed", proc.stdout[-3000:],
                     proc.stderr[-3000:])
                return 1
        return 0

    refused, to_probe = [], []
    for update in updates:
        local_ref, local_sha, remote_ref, remote_sha = update.split()
        if local_sha == ZERO:
            continue
        branch = remote_ref.removeprefix("refs/heads/")
        if branch == _default_branch(repo, remote):
            refused.append(f"{remote_ref}: never push a repository's default branch; open a PR")
            continue
        if remote_sha != ZERO and not git_ok(repo, "merge-base", "--is-ancestor",
                                             remote_sha, local_sha):
            tracking = git(repo, "rev-parse", "-q", "--verify",
                           f"refs/remotes/{remote}/{branch}", check=False).strip()
            seen = git(repo, "reflog", "show", "--format=%H", local_ref, check=False).split()
            if tracking != remote_sha and remote_sha not in seen:
                refused.append(f"{remote_ref}: the remote is at {remote_sha[:7]}, which neither your "
                               "last fetch nor this branch's history has; fetch and look before "
                               "overwriting it")
                continue
        revs = git(repo, "rev-list", "--no-merges", "--reverse", local_sha,
                   "--not", "--remotes").split()
        to_probe.extend(r for r in revs if r not in to_probe)

    for sha in to_probe:
        outcome = probe_commit(repo, sha)
        _say(*outcome.lines)
        if not outcome.ok:
            refused.append(f"{sha[:7]} failed its probe")
    if refused:
        _say("push refused:", *refused)
        return 1
    return 0


def baseline(repo: Path) -> int:
    """Record commits already on non-OpenMRS remotes as pushed before the probes."""
    upstream = []
    for line in git(repo, "remote", "-v").splitlines():
        name, url = line.split()[:2]
        if OPENMRS_URL.search(url) and name not in upstream:
            upstream.append(name)
    exclude = [f"--remotes={u}" for u in upstream]
    revs = git(repo, "rev-list", "--no-merges", "--remotes",
               *(["--not", *exclude] if exclude else [])).split()
    return record_baseline(repo, revs)


def main(argv: list[str]) -> int:
    name, args = argv[0], argv[1:]
    repo = Path.cwd()
    if name == "pre-commit":
        return pre_commit(repo)
    if name == "commit-msg":
        return commit_msg(repo, args[0])
    if name == "pre-push":
        return pre_push(repo, args[0], args[1], sys.stdin.read().splitlines())
    raise SystemExit(f"unknown hook {name}")
