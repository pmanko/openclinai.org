"""Revert and mutation probes (L1) for one commit, with a ledger under work/review.

Revert probe: the commit's tests fail with its main-code files put back to the parent
and pass at the commit. Mutation probe: each Mutation: trailer, applied at the commit,
makes the tests fail. Probes run in a persistent worktree per repository so builds stay
incremental. A commit whose patch was already probed with the same trailers, or recorded
as pushed before the probes existed, is not probed again.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .commits import commit_changes, commit_trailers, derived_tests, detect_runner
from .git import clean_env, common_dir, git, patch_id, repo_name, toplevel

UMBRELLA = Path(__file__).resolve().parents[3]
RUNNERS = UMBRELLA / "review" / "bin" / "runners"


def work_dir() -> Path:
    return Path(os.environ.get("REVIEW_WORK", UMBRELLA / "work" / "review"))


@dataclass
class Outcome:
    sha: str
    ok: bool
    status: str  # probed, skip, cached, baseline, no-main, blocked
    lines: list[str] = field(default_factory=list)


@dataclass
class Run:
    code: int
    ran: int
    failed: list[str]
    log: Path


class Ledger:
    def __init__(self, repo: Path):
        self.path = work_dir() / "ledger" / f"{repo_name(repo)}.jsonl"

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def find(self, pid: str, trailer_key: str) -> dict | None:
        for rec in reversed(self.records()):
            if rec.get("patch_id") != pid:
                continue
            if rec["status"] == "baseline" and not trailer_key:
                return rec
            if rec["status"] in ("probed", "skip") and rec["ok"] \
                    and rec.get("trailers", "") == trailer_key:
                return rec
        return None

    def append(self, rec: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rec["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with self.path.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")


def _ensure_worktree(repo: Path, sha: str) -> Path:
    wt = work_dir() / "wt" / repo_name(repo)
    if (wt / ".git").exists():
        if common_dir(wt) != common_dir(repo):
            raise RuntimeError(f"{wt} is a worktree of another repository")
    else:
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(repo, "worktree", "prune")
        git(repo, "worktree", "add", "-q", "--detach", str(wt), sha)
    _reset(wt, sha)
    source = toplevel(repo)
    for deps in ("node_modules",):
        if (source / deps).is_dir() and not (wt / deps).exists():
            (wt / deps).symlink_to(source / deps)
    return wt


def _reset(wt: Path, sha: str) -> None:
    git(wt, "checkout", "-q", "--detach", "-f", sha)
    git(wt, "reset", "-q", "--hard", sha)
    git(wt, "clean", "-fdq", "-e", "node_modules")


def _run(runner: str, wt: Path, tests: list[str], log: Path) -> Run:
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([str(RUNNERS / f"{runner}.sh"), str(wt), str(log), *tests],
                          capture_output=True, text=True, env=clean_env())
    ran, failed = 0, []
    for line in proc.stdout.splitlines():
        if line.startswith("RAN "):
            ran = int(line.split()[1])
        elif line.startswith("FAILED "):
            failed.append(line[7:].strip())
    return Run(proc.returncode, ran, failed, log)


def _first(run: Run) -> str:
    return (run.failed[0][:160] if run.failed else "")


def _expect_red(run: Run, sha7: str, what: str) -> tuple[bool, str]:
    if run.code == 1:
        return True, f"red   {sha7} {what}: {len(run.failed)} of {run.ran} failed: {_first(run)}"
    if run.code == 2:
        return True, f"red   {sha7} {what}: the build fails (see {run.log})"
    if run.code == 0:
        return False, (f"BLOCK {sha7} {what}: {run.ran} passed; the tests do not "
                       "detect it")
    if run.code == 3:
        return False, f"BLOCK {sha7} {what}: no named test ran (see {run.log})"
    return False, f"BLOCK {sha7} {what}: runner error {run.code} (see {run.log})"


def _expect_green(run: Run, sha7: str) -> tuple[bool, str]:
    if run.code == 0:
        return True, f"green {sha7}: {run.ran} passed"
    reason = {1: f"{len(run.failed)} of {run.ran} failed: {_first(run)}",
              2: "the build fails", 3: "no named test ran"}.get(run.code, f"runner error {run.code}")
    return False, f"BLOCK {sha7} at the commit: {reason} (see {run.log})"


def probe_commit(repo: Path, sha: str) -> Outcome:
    sha = git(repo, "rev-parse", sha).strip()
    sha7 = sha[:7]
    changes = commit_changes(repo, sha)
    main = [c for c in changes if c.kind == "main"]
    if not main:
        return Outcome(sha, True, "no-main")
    trailers = commit_trailers(repo, sha)
    if trailers.errors:
        return Outcome(sha, False, "blocked", [f"BLOCK {sha7} {e}" for e in trailers.errors])

    ledger = Ledger(repo)
    pid = patch_id(repo, sha) or sha
    key = trailers.key()
    previous = ledger.find(pid, key)
    if previous:
        what = ("pushed before the probes were installed" if previous["status"] == "baseline"
                else f"same patch as {previous['sha'][:7]}")
        return Outcome(sha, True, "cached", [f"skip  {sha7} {what}"])
    record = {"sha": sha, "patch_id": pid, "trailers": key}
    if trailers.skip:
        line = f"skip  {sha7} Probe: skip ({trailers.skip})"
        ledger.append({**record, "status": "skip", "ok": True, "lines": [line]})
        return Outcome(sha, True, "skip", [line])

    lock_path = work_dir() / "wt" / f"{repo_name(repo)}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        wt = _ensure_worktree(repo, sha)
        runner = detect_runner(wt)
        if not runner:
            return Outcome(sha, False, "blocked", [f"BLOCK {sha7} no test runner found"])
        tests = trailers.tests or derived_tests(changes, runner)
        if not tests:
            return Outcome(sha, False, "blocked", [
                f"BLOCK {sha7} changes main code with no test: add or name one in "
                "Tests:, or add Probe: skip (<reason>)"])
        logs = work_dir() / "logs" / repo_name(repo)
        lines, ok = [], True
        try:
            for change in main:
                if change.status == "A":
                    (wt / change.path).unlink()
                else:
                    git(wt, "checkout", "-q", f"{sha}^", "--", change.path)
            good, line = _expect_red(_run(runner, wt, tests, logs / f"{sha7}-revert.log"),
                                     sha7, f"revert of {len(main)} main file(s)")
            ok &= good
            lines.append(line)
            _reset(wt, sha)
            good, line = _expect_green(_run(runner, wt, tests, logs / f"{sha7}-green.log"), sha7)
            ok &= good
            lines.append(line)
            for n, mutation in enumerate(trailers.mutations, 1):
                target = wt / mutation.path
                text = target.read_text(encoding="utf-8") if target.is_file() else ""
                count = text.count(mutation.old)
                if count != 1:
                    ok = False
                    lines.append(f"BLOCK {sha7} mutation {mutation.label()}: the old text "
                                 f"occurs {count} times in {mutation.path}; it must occur once")
                    continue
                target.write_text(text.replace(mutation.old, mutation.new), encoding="utf-8")
                good, line = _expect_red(
                    _run(runner, wt, tests, logs / f"{sha7}-mutation{n}.log"),
                    sha7, f"mutation {mutation.label()}")
                ok &= good
                lines.append(line)
                _reset(wt, sha)
        finally:
            _reset(wt, sha)
    ledger.append({**record, "status": "probed", "ok": ok, "tests": tests, "lines": lines})
    return Outcome(sha, ok, "probed" if ok else "blocked", lines)


def record_baseline(repo: Path, revs: list[str]) -> int:
    """Record main-code commits in revs as pushed before the probes were installed."""
    ledger = Ledger(repo)
    known = {r.get("patch_id") for r in ledger.records()}
    count = 0
    for sha in revs:
        if not any(c.kind == "main" for c in commit_changes(repo, sha)):
            continue
        pid = patch_id(repo, sha)
        if pid and pid not in known:
            ledger.append({"sha": sha, "patch_id": pid, "status": "baseline", "ok": True})
            known.add(pid)
            count += 1
    return count
