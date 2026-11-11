#!/usr/bin/env python3
"""Drive `make review`: PR threads, fresh-session reviewer/fixer/reply roles, and stack consolidation.

Writes everything to work/review/<component>-<encoded-repository>-<pr>/: threads.json, the prompts,
each role's answer, findings-<round>.json and round-<round>.md. Posts nothing and never runs
clinical AI benchmark evaluations or report publication (see scripts/run-eval.py and
scripts/publish-report.py).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

UMBRELLA = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(UMBRELLA / "review" / "lib"))
from reviewkit.git import git  # noqa: E402
from reviewkit.probes import work_dir  # noqa: E402
from reviewkit.stack import consolidate, merge_ledger  # noqa: E402

BIN = UMBRELLA / "review" / "bin"
BRIEFS = UMBRELLA / "review" / "briefs"
ACTIVE_RESULT = None
REPOS = {
    "chartsearchai": "targets/chartsearchai",
    "esm": "targets/chartsearchai-esm",
    "querystore": "targets/querystore",
    "hub": "targets/med-agent-hub",
    "harness": "targets/validation-harness",
    "umbrella": ".",
}
CONSUMERS = {
    "querystore": "chartsearchai",
    "chartsearchai": "querystore",
    "esm": "chartsearchai",
    "hub": "harness",
    "harness": "hub",
}
OPENMRS = re.compile(r"github\.com[:/]+(openmrs/[^/\s]+?)(\.git)?$")


def upstream(checkout: Path, repository: str | None = None) -> tuple[str, str]:
    """Select the requested GitHub repository, or the default OpenMRS upstream."""
    for line in git(checkout, "remote", "-v").splitlines():
        name, url = line.split()[:2]
        m = (
            re.search(r"github\.com[:/]+([^/\s]+/[^/\s]+?)(\.git)?$", url)
            if repository
            else OPENMRS.search(url)
        )
        if m and (repository is None or m.group(1) == repository):
            return name, m.group(1)
    raise SystemExit(f"{checkout}: no remote points at github.com/{repository or 'openmrs/*'}")


def fetch_pr(checkout: Path, remote: str, pr: int) -> str:
    git(checkout, "fetch", "-q", remote, f"+pull/{pr}/head:refs/review/pr/{pr}")
    return git(checkout, "rev-parse", f"refs/review/pr/{pr}").strip()


def current_identity(slug: str, pr: int) -> dict:
    out = subprocess.run(
        ["gh", "pr", "view", str(pr), "-R", slug, "--json", "headRefOid,baseRefOid,baseRefName"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    identity = json.loads(out)
    if not isinstance(identity, dict) or any(
        not isinstance(identity.get(k), str) or not identity[k]
        for k in ("headRefOid", "baseRefOid", "baseRefName")
    ):
        raise ValueError("PR identity is unavailable")
    return identity


def verify_checkout(path: Path, revision: str) -> None:
    """A model-reported revision cannot override the checkout it actually used."""
    if git(path, "rev-parse", "HEAD").strip() != revision or git(path, "status", "--porcelain").strip():
        raise ValueError(f"review checkout changed during execution: {path}")


def worktree(checkout: Path, path: Path, ref: str, branch: str | None = None) -> Path:
    if not (path / ".git").exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        git(checkout, "worktree", "prune")
        if branch:
            git(checkout, "worktree", "add", "-q", str(path), branch)
        else:
            git(checkout, "worktree", "add", "-q", "--detach", str(path), ref)
    if branch:
        git(path, "checkout", "-q", branch)
        git(path, "reset", "-q", "--hard", ref)
    else:
        git(path, "checkout", "-q", "--detach", "-f", ref)
    git(path, "clean", "-fdq", "-e", "node_modules")
    deps = checkout / "node_modules"
    if deps.is_dir() and not (path / "node_modules").exists():
        (path / "node_modules").symlink_to(deps)
    return path


def stack(checkout: Path, remote: str, slug: str, author: str, pr: int, head: str) -> list[dict]:
    """Open PRs by the same author whose heads lie on one line with this PR's head."""
    out = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "-R",
            slug,
            "--author",
            author,
            "--state",
            "open",
            "--json",
            "number,title,headRefName,baseRefName,baseRefOid,createdAt",
            "-L",
            "1000",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    candidates = json.loads(out)
    if len(candidates) >= 1000:
        raise ValueError("Stack discovery reached its result cap; refusing an incomplete stack")
    layers = []
    from reviewkit.stack import ancestor

    anc = lambda a, b: ancestor(checkout, a, b)
    for p in candidates:
        sha = fetch_pr(checkout, remote, p["number"])
        commits = set(git(checkout, "rev-list", sha, f"^{remote}/main").splitlines())
        layers.append(
            {
                **p,
                "head": sha,
                "base": p["baseRefOid"],
                "created_at": p["createdAt"],
                "commits": len(commits),
                "feature_commits": commits,
            }
        )
    selected = {pr}
    if pr not in {p["number"] for p in layers}:
        raise ValueError("Requested PR is missing from stack discovery")
    while True:
        included = [p for p in layers if p["number"] in selected]
        additions = {
            p["number"]
            for p in layers
            if any(
                p["baseRefName"] == q["headRefName"]
                or q["baseRefName"] == p["headRefName"]
                or bool(p["feature_commits"] & q["feature_commits"])
                for q in included
            )
        }
        if additions.issubset(selected):
            break
        selected.update(additions)
    layers = [{k: v for k, v in p.items() if k != "feature_commits"} for p in layers if p["number"] in selected]
    ordered = sorted(layers, key=lambda l: l["commits"])
    if any(not anc(a["head"], b["head"]) for a, b in zip(ordered, ordered[1:])):
        raise SystemExit(
            "Connected stack has divergent heads; use a curated consolidation manifest with each examined revision"
        )
    return ordered


def last_json(text: str):
    """The last ```json block of a role's answer, parsed."""
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    if not blocks:
        raise SystemExit("the role's answer has no ```json block")
    block = blocks[-1]
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        repaired = re.sub(
            r'("(?:\\.|[^"\\])*")|,\s*([}\]])',
            lambda m: m.group(1) if m.group(1) is not None else m.group(2),
            block,
        )
        return json.loads(repaired)


def validate_review(data: dict, head: str, changed: list[str]) -> None:
    """Reject incomplete or misattributed review evidence before recording assessment."""
    if not isinstance(data, dict) or data.get("head") != head:
        raise ValueError("review revision mismatch")
    for name in ("findings", "reviewed_files", "unreviewed_files", "tests"):
        if not isinstance(data.get(name), list):
            raise ValueError(f"missing or invalid {name}")
    if any(not isinstance(p, str) for p in data["reviewed_files"] + data["unreviewed_files"]):
        raise ValueError("invalid file coverage")
    if set(changed) != set(data["reviewed_files"]) | set(data["unreviewed_files"]):
        raise ValueError("review must account for every changed file")
    for finding in data["findings"]:
        if (
            not isinstance(finding, dict)
            or not isinstance(finding.get("blocking"), bool)
            or not isinstance(finding.get("line"), int)
            or not isinstance(finding.get("file"), str)
            or not isinstance(finding.get("finding"), str)
        ):
            raise ValueError("invalid finding")


def settle(findings: list[dict]) -> list[dict]:
    """A blocking finding needs a failure mode and evidence; otherwise it is a question."""
    for f in findings:
        if f.get("blocking") and not (f.get("failure_mode") and f.get("evidence")):
            f["blocking"] = False
            f["downgraded"] = "blocking without a failure mode and evidence"
    return findings


def run_role(
    args,
    role: str,
    workdir: Path,
    prompt: str,
    out: Path,
    agent: str | None = None,
    env: dict | None = None,
) -> str:
    """One fresh session of the agent (the run's, or ``agent``), with ``env`` added."""
    prompt_file = out.with_suffix(".prompt.md")
    scratch = out.parent / "scratch"
    scratch.mkdir(exist_ok=True)
    prompt += f"\nKeep all working scripts and logs in {scratch}, never /tmp. Preserve reproduction scripts there.\n"
    if role != "fixer":
        prompt += (
            "\nYour final message is saved as your answer: do not write it to a file, and "
            "leave the repository as you found it.\n"
        )
    if (agent or getattr(args, "agent", None)) == "human" and out.exists() and prompt_file.exists():
        previous_prompt = prompt_file.read_text()
        if previous_prompt != prompt:
            archive = (
                out.parent
                / "history"
                / hashlib.sha256(previous_prompt.encode() + out.read_bytes()).hexdigest()[:16]
            )
            archive.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, archive / out.name)
            (archive / prompt_file.name).write_text(previous_prompt)
            out.unlink()
    prompt_file.write_text(prompt)
    role_script = out.with_suffix(".role.sh")
    role_script.write_bytes((BIN / "role.sh").read_bytes())
    rc = subprocess.run(
        ["bash", str(role_script), agent or args.agent, role, str(workdir), str(prompt_file), str(out)],
        env={**os.environ, **(env or {})},
    ).returncode
    if rc == 3:
        sys.exit(3)
    if rc or not out.exists():
        raise SystemExit(f"{role} failed (exit {rc}); see {out}")
    return out.read_text()


def record(round_dir: Path, k: int, data: dict) -> None:
    (round_dir / f"findings-{k}.json").write_text(json.dumps(data, indent=1))
    lines = [f"# Round {k}: {data['repo']}#{data['pr']} at {data['head'][:7]}", ""]
    for f in data["findings"]:
        kind = "BLOCKING" if f.get("blocking") else "question"
        lines += [
            f"- **{kind}** `{f.get('file')}:{f.get('line')}` {f.get('finding')}",
            f"  - failure mode: {f.get('failure_mode') or '-'}",
            f"  - evidence: {f.get('evidence') or '-'}",
        ]
    (round_dir / f"round-{k}.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    global ACTIVE_RESULT
    ACTIVE_RESULT = None
    ap = argparse.ArgumentParser(description="Run PR code review, stack review, reply drafting, and fixer rounds.")
    ap.add_argument("--pr", type=int, required=True, help="Pull request number to review")
    ap.add_argument("--repository", help="Exact GitHub owner/repository; selects the matching remote")
    ap.add_argument("--fix", action="store_true", help="Authorize fixer commits and pushes between rounds")
    ap.add_argument("--repo", default="chartsearchai", choices=REPOS)
    ap.add_argument("--agent", default="claude", choices=("claude", "codex", "gemini", "human"))
    ap.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--stack", action="store_true")
    ap.add_argument("--replies", action="store_true", help="draft replies from the last round")
    ap.add_argument("--no-review", action="store_true", help="skip the reviewer rounds")
    ap.add_argument("--checkout", help="a checkout other than the umbrella's for --repo")
    ap.add_argument("--threads-until", help="ISO instant: review the PR as it stood then")
    ap.add_argument("--consumer-head", help="Explicit consumer revision for cross-repository review")
    ap.add_argument("--consumer-repo", choices=REPOS, help="Override the component on the other side of this contract")
    ap.add_argument("--no-consumer", action="store_true", help="omit the other repository's checkout")
    ap.add_argument("--head", help="review this local ref instead of the PR's pushed head (review before the push)")
    ap.add_argument("--base", help="with --head: the local ref of the layer below, instead of the remote base branch")
    args = ap.parse_args()
    if args.rounds < 1:
        ap.error("--rounds must be at least 1")
    if args.no_consumer and (args.consumer_head or args.consumer_repo):
        ap.error("--no-consumer cannot select a consumer repository or revision")
    if args.base and not args.head:
        ap.error("--base needs --head")
    if args.stack and args.fix:
        ap.error("--stack is report-only; fix an explicitly selected owning PR separately")
    if args.head and args.stack:
        ap.error("--head reviews one local layer; --stack reads the pushed stack")

    checkout = Path(args.checkout).resolve() if args.checkout else UMBRELLA / REPOS[args.repo]
    remote, slug = upstream(checkout, args.repository)
    git(checkout, "fetch", "-q", remote)
    repository_key = quote(slug, safe="")
    out_dir = work_dir() / f"{args.repo}-{repository_key}-{args.pr}"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_lock = (out_dir / "run.lock").open("w")
    fcntl.flock(run_lock, fcntl.LOCK_EX)
    if not args.replies and not args.no_review:
        ACTIVE_RESULT = out_dir / "result.json"
        ACTIVE_RESULT.write_text(
            json.dumps(
                {
                    "execution": "running",
                    "assessment": "undetermined",
                    "repository": slug,
                    "pr": args.pr,
                    "requested_consumer_repo": args.consumer_repo,
                    "requested_consumer_head": args.consumer_head,
                }
            )
        )
    threads = out_dir / (
        "reply-threads.json"
        if args.replies
        else "evaluation-threads.json"
        if args.no_review
        else "threads.json"
    )
    subprocess.run(
        [str(BIN / "threads.py"), slug, str(args.pr), str(threads)]
        + (["--until", args.threads_until] if args.threads_until else []),
        check=True,
    )
    meta = json.loads(threads.read_text())
    snapshot_hash = hashlib.sha256(threads.read_bytes()).hexdigest()

    if args.replies:
        fetch_pr(checkout, remote, args.pr)
        rounds = sorted(out_dir.glob("findings-*.json"))
        ledger = work_dir() / "ledger"
        prompt = (BRIEFS / "reply.md").read_text() + (
            f"\n## Inputs\n\n- Threads: {threads} (snapshot {snapshot_hash})\n"
            f"- Last round: {rounds[-1] if rounds else 'none'}\n"
            f"- Probe ledger (red and green lines by commit): {ledger}\n"
            f"- Commits on the PR: `git log {meta['base']}..refs/review/pr/{args.pr}`\n"
        )
        run_role(args, "reply", checkout, prompt, out_dir / "replies.md")
        print(f"drafted {out_dir / 'replies.md'}")
        return 0

    for k in range(1, 0 if args.no_review else args.rounds + 1):
        head = (
            git(checkout, "rev-parse", "--verify", f"{args.head}^{{commit}}").strip()
            if args.head
            else fetch_pr(checkout, remote, args.pr)
        )
        base = git(checkout, "rev-parse", args.base if args.base else f"{remote}/{meta['base']}").strip()
        wt = work_dir() / "wt-review" / args.repo / repository_key / str(args.pr)
        brief = (BRIEFS / "reviewer.md").read_text()
        inputs = [
            f"- Repository checkout at the {'local, not yet pushed' if args.head else 'PR'} head {head}: {wt}",
            f"- Base: {base}",
            f"- Prepared Python interpreter: {os.environ.get('REVIEW_PYTHON', 'not supplied; report dependency gaps')}",
            f"- Threads and ticket: {threads} (snapshot {snapshot_hash})",
            f"- Effort: {args.effort}" + (" (from round 2 on, blocking findings only)" if k > 1 else ""),
        ]
        previous = out_dir / f"findings-{k - 1}.json"
        if previous.exists():
            inputs.append(f"- Previous round: {previous}")
        target = head
        requested_base = base
        ledger_path = work_dir() / "stacks" / repository_key / "issues.json"
        if args.stack:
            layers = stack(checkout, remote, slug, meta["author"], args.pr, head)
            target = layers[-1]["head"] if layers else head
            if layers:
                base = layers[0]["base"]
                inputs[1] = f"- Base of the complete stack: {base}"
            brief += "\n" + (BRIEFS / "stack.md").read_text()
            inputs.append("- Layer snapshots: " + json.dumps(layers))
            if ledger_path.exists():
                inputs.append(
                    "- Known issue identities (reuse root-cause keys; absence is not resolution): "
                    + ledger_path.read_text()
                )
            inputs.append(
                "- Stack, bottom to top (the checkout is the merged top "
                f"{target[:7]}):\n"
                + "\n".join(f"  - #{l['number']} {l['title']} ({l['head'][:7]})" for l in layers)
            )
        worktree(checkout, wt, target)
        consumer = None if args.no_consumer else args.consumer_repo or CONSUMERS.get(args.repo)
        missing_consumer = False
        if args.consumer_head and not consumer:
            ap.error("--consumer-head needs a consumer; select one with --consumer-repo")
        if consumer and not (UMBRELLA / REPOS[consumer] / ".git").exists():
            if args.consumer_repo or args.consumer_head:
                raise ValueError(f"requested consumer {consumer} is unavailable")
            inputs.append(f"- Consumer {consumer} is unavailable; its contract is unverified.")
            missing_consumer = True
            consumer = None
        if consumer:
            consumer_checkout = UMBRELLA / REPOS[consumer]
            consumer_sha = git(consumer_checkout, "rev-parse", args.consumer_head or "HEAD").strip()
            consumer_wt = worktree(consumer_checkout, out_dir / "consumer" / consumer, consumer_sha)
            inputs.append(
                f"- Consumer repository ({consumer}) at supplied local revision {consumer_sha[:7]}, read-only: "
                f"{consumer_wt}"
            )
        answer = run_role(
            args,
            "reviewer",
            wt,
            brief + "\n## Inputs\n\n" + "\n".join(inputs) + "\n",
            out_dir / f"reviewer-{k}.md",
        )
        verify_checkout(wt, target)
        if consumer:
            verify_checkout(consumer_wt, consumer_sha)
        data = last_json(answer)
        changed = git(wt, "diff", "--name-only", f"{base}...{target}").splitlines()
        validate_review(data, target, changed)
        fresh = current_identity(slug, args.pr) if not args.head else None
        stale = bool(
            fresh
            and (
                fresh["headRefOid"] != head
                or fresh["baseRefOid"] != requested_base
                or fresh["baseRefName"] != meta["base"]
            )
        )
        if args.stack and layers:
            for layer in layers:
                current = current_identity(slug, layer["number"])
                stale |= current["headRefOid"] != layer["head"] or current["baseRefOid"] != layer["base"]
        data.update(
            scope="source_review",
            repo=args.repo,
            repository=slug,
            pr=args.pr,
            requested_head=head,
            base=base,
            pr_base=requested_base,
            base_branch=meta["base"],
            identity_after=fresh,
            consumer_repo=consumer,
            consumer_head=consumer_sha if consumer else None,
            execution=(
                "superseded"
                if stale
                else "partial"
                if data["unreviewed_files"] or missing_consumer
                else "complete"
            ),
            behavior_verification="see evidence; not inferred from source review",
            findings=settle(data["findings"]),
        )
        if args.stack and not stale:
            observations, decisions = [], []
            for index, finding in enumerate(data["findings"]):
                required = (
                    "issue_key",
                    "introduced_commit",
                    "origin_file",
                    "origin_evidence",
                    "owner_pr",
                    "affected_prs",
                )
                if any(name not in finding for name in required):
                    raise ValueError("Stack finding lacks canonical identity or introduction evidence")
                occurrence_ids = []
                for number in finding["affected_prs"]:
                    layer = next((p for p in layers if p["number"] == number), None)
                    if layer is None:
                        raise ValueError("Affected PR is outside the examined stack")
                    oid = f"{index}:{number}"
                    occurrence_ids.append(oid)
                    observations.append(dict(id=oid, pr=number, head=layer["head"], finding=finding))
                decisions.append(
                    dict(
                        issue_key=finding["issue_key"],
                        title=finding["finding"],
                        introduced_commit=finding["introduced_commit"],
                        origin_file=finding["origin_file"],
                        origin_evidence=finding["origin_evidence"],
                        owner_pr=finding["owner_pr"],
                        status=finding.get("attribution_status", "open"),
                        occurrences=occurrence_ids,
                        regression_of=finding.get("regression_of"),
                    )
                )
            data["stack_plan"] = consolidate(slug, checkout, layers, observations, decisions)
            if data["stack_plan"]["attribution_pending"] and data["execution"] == "complete":
                data["execution"] = "partial"
            if data["execution"] == "complete":
                merge_ledger(ledger_path, data["stack_plan"])
        data["dependency_files"] = {
            str(p.relative_to(wt)): hashlib.sha256(p.read_bytes()).hexdigest()
            for name in ("uv.lock", "poetry.lock", "yarn.lock", "package-lock.json", "pyproject.toml")
            if (p := wt / name).is_file()
        }
        data["assessment"] = (
            "undetermined"
            if data["execution"] != "complete"
            else "findings"
            if data["findings"]
            else "no_findings"
        )
        ACTIVE_RESULT.write_text(json.dumps(data, indent=2))
        record(out_dir, k, data)
        blocking = [f for f in data["findings"] if f.get("blocking")]
        print(
            f"round {k}: {len(blocking)} blocking, "
            f"{len(data['findings']) - len(blocking)} questions -> {out_dir / f'round-{k}.md'}"
        )
        if data["execution"] != "complete" or not blocking or k == args.rounds or not args.fix:
            break
        if args.agent == "human":
            print("fix the blocking findings on the PR branch, push, and re-run")
            return 3
        fix_wt = worktree(
            checkout,
            work_dir() / "wt-fix" / args.repo / repository_key / str(args.pr),
            head,
            branch=meta["head_branch"],
        )
        run_role(
            args,
            "fixer",
            fix_wt,
            (BRIEFS / "fixer.md").read_text()
            + f"\n## Inputs\n\n- Findings to fix: {out_dir / f'findings-{k}.json'}\n"
            f"- Push with: git push -- {shlex.quote(remote)} {shlex.quote('HEAD:' + meta['head_branch'])}\n",
            out_dir / f"fixer-{k}.md",
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException as exc:
        if ACTIVE_RESULT and not (isinstance(exc, SystemExit) and exc.code in (None, 0)):
            data = json.loads(ACTIVE_RESULT.read_text())
            data.update(execution="error", assessment="undetermined", error=str(exc))
            ACTIVE_RESULT.write_text(json.dumps(data, indent=2))
        raise
