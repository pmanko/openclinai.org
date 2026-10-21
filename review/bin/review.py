#!/usr/bin/env python3
"""Drive `make review`: threads, fresh-session roles, rounds, and the optional layers.

Writes everything to work/review/<repo>-<pr>/: threads.json, the prompts, each role's
answer, findings-<round>.json and round-<round>.md. Posts nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

UMBRELLA = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(UMBRELLA / "review" / "lib"))
from reviewkit.git import git  # noqa: E402
from reviewkit.probes import work_dir  # noqa: E402

BIN = UMBRELLA / "review" / "bin"
BRIEFS = UMBRELLA / "review" / "briefs"
REPOS = {"chartsearchai": "targets/chartsearchai", "esm": "targets/chartsearchai-esm",
         "querystore": "targets/querystore"}
OPENMRS = re.compile(r"github\.com[:/]+(openmrs/[^/\s]+?)(\.git)?$")


def upstream(checkout: Path) -> tuple[str, str]:
    """The remote that points at the OpenMRS repository, and its owner/name."""
    for line in git(checkout, "remote", "-v").splitlines():
        name, url = line.split()[:2]
        m = OPENMRS.search(url)
        if m:
            return name, m.group(1)
    raise SystemExit(f"{checkout}: no remote points at github.com/openmrs")


def fetch_pr(checkout: Path, remote: str, pr: int) -> str:
    git(checkout, "fetch", "-q", remote, f"+pull/{pr}/head:refs/review/pr/{pr}")
    return git(checkout, "rev-parse", f"refs/review/pr/{pr}").strip()


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
    out = subprocess.run(["gh", "pr", "list", "-R", slug, "--author", author, "--state", "open",
                          "--json", "number,title,headRefName", "-L", "100"],
                         capture_output=True, text=True, check=True).stdout
    layers = []
    for p in json.loads(out):
        sha = fetch_pr(checkout, remote, p["number"])
        anc = lambda a, b: subprocess.run(["git", "-C", str(checkout), "merge-base",
                                           "--is-ancestor", a, b]).returncode == 0
        if anc(sha, head) or anc(head, sha):
            count = int(git(checkout, "rev-list", "--count", sha, f"^{remote}/main").strip() or 0)
            layers.append({**p, "head": sha, "commits": count})
    return sorted(layers, key=lambda l: l["commits"])


def last_json(text: str):
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    if not blocks:
        raise SystemExit("the role's answer has no ```json block")
    return json.loads(blocks[-1])


def settle(findings: list[dict]) -> list[dict]:
    """A blocking finding needs a failure mode and evidence; otherwise it is a question."""
    for f in findings:
        if f.get("blocking") and not (f.get("failure_mode") and f.get("evidence")):
            f["blocking"] = False
            f["downgraded"] = "blocking without a failure mode and evidence"
    return findings


def run_role(args, role: str, workdir: Path, prompt: str, out: Path) -> str:
    prompt_file = out.with_suffix(".prompt.md")
    if role != "fixer":
        prompt += ("\nYour final message is saved as your answer: do not write it to a file, and "
                   "leave the repository as you found it.\n")
    prompt_file.write_text(prompt)
    rc = subprocess.run([str(BIN / "role.sh"), args.agent, role, str(workdir),
                         str(prompt_file), str(out)]).returncode
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
        lines += [f"- **{kind}** `{f.get('file')}:{f.get('line')}` {f.get('finding')}",
                  f"  - failure mode: {f.get('failure_mode') or '-'}",
                  f"  - evidence: {f.get('evidence') or '-'}"]
    (round_dir / f"round-{k}.md").write_text("\n".join(lines) + "\n")


def harness(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "--directory", str(UMBRELLA / "targets/validation-harness"),
                           "run", "harness-cli", *args], capture_output=True, text=True)


HARNESS = UMBRELLA / "targets/validation-harness"
DATA = HARNESS / "datasets/validation"
LLM_SETTINGS = ("chartsearchai.llm.engine", "chartsearchai.llm.remote.endpointUrl",
                "chartsearchai.llm.remote.modelName")
HUB_TAP = f"http://host.docker.internal:{os.environ.get('HUB_TAP_PORT', '8079')}"


def openmrs(shell: str) -> str:
    """Run a command with the umbrella's OpenMRS REST helpers loaded."""
    return subprocess.run(["bash", "-c", f". scripts/openmrs-settings-lib.sh; {shell}"],
                          cwd=UMBRELLA, capture_output=True, text=True, check=True).stdout


def rest_get(path: str) -> dict:
    return json.loads(openmrs('openmrs_curl -fsS -u "$OPENMRS_SETTINGS_USER:$OPENMRS_SETTINGS_PASS" '
                              f'"$OPENMRS_SETTINGS_BASE_URL/ws/rest/v1/{path}"'))


@contextmanager
def run_environment(data_root: Path, set_id: str, record: Path):
    """Bring the parity taps up for sets with provider arms; restore what was found."""
    cset = json.loads((data_root / "comparison_sets" / f"{set_id}.json").read_text())
    backends = json.loads((data_root / "backends.json").read_text())
    if not any(backends[b].get("kind") == "provider_arm" for b in cset["backend_ids"]):
        yield {}
        return
    found = {r["property"]: r["value"] for r in
             rest_get("systemsetting?q=chartsearchai.llm&v=full")["results"]
             if r["property"] in LLM_SETTINGS}
    record.write_text(json.dumps(found, indent=1))
    subprocess.run([str(UMBRELLA / "scripts/parity-engine-up.sh")], check=True, cwd=UMBRELLA)
    try:
        yield {"MED_AGENT_LLM_BASE_URL": HUB_TAP}
    finally:
        for name in LLM_SETTINGS:
            if name in found:
                openmrs(f"set_openmrs_property {json.dumps(name)} {json.dumps(found[name] or '')}")
            else:
                openmrs('openmrs_curl -fsS -o /dev/null -X DELETE -u "$OPENMRS_SETTINGS_USER:'
                        '$OPENMRS_SETTINGS_PASS" "$OPENMRS_SETTINGS_BASE_URL/ws/rest/v1/'
                        f'systemsetting/{name}?purge=true"')
        subprocess.run(["make", "-C", str(UMBRELLA), "med-agent-hub-up"], check=True,
                       env={k: v for k, v in os.environ.items() if k != "MED_AGENT_LLM_BASE_URL"})
        print(f"restored {', '.join(found) or 'nothing'} as found; Hub back on its configured engine")


def run_set(make_target: str, comparison_set: str, out: Path, env: dict | None = None,
            data_root: Path | None = None) -> Path:
    """Run a comparison set through the umbrella's make target; return the run directory."""
    cmd = ["make", "-C", str(UMBRELLA), make_target, f"SET={comparison_set}"]
    if data_root:
        cmd.append(f"VALIDATE_DATA_ROOT={data_root}")
    proc = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    out.write_text(proc.stdout + proc.stderr)
    m = re.search(r"results -> (\S+)/results\.jsonl", proc.stdout)
    if proc.returncode or not m:
        raise SystemExit(f"{make_target} {comparison_set} failed; see {out}")
    run_dir = Path(m.group(1))
    return run_dir if run_dir.is_absolute() else UMBRELLA / "targets/validation-harness" / run_dir


def scenarios(args, head: str, out_dir: Path) -> int:
    """L3: deploy the PR head (backend modules), replay the set, check its expectations."""
    deploy = BIN / "deploy-head.sh"
    module = args.repo if args.repo in ("querystore", "chartsearchai") else None
    try:
        if module:
            subprocess.run([str(deploy), module, head], check=True)
        with run_environment(DATA, args.scenarios, out_dir / "settings-as-found.json") as env:
            run_dir = run_set("validate-run", args.scenarios,
                              out_dir / f"scenarios-{args.scenarios}.log", env)
        expect = harness("validate", "expect", "--run-dir", str(run_dir))
    finally:
        if module:
            subprocess.run([str(deploy), module, "--restore"], check=True)
    summary = f"# Scenarios {args.scenarios} at {head[:7]}\n\nRun: {run_dir}\n\n```\n{expect.stdout}```\n"
    (out_dir / f"scenarios-{args.scenarios}.md").write_text(summary)
    print(expect.stdout.strip().splitlines()[-1] if expect.stdout.strip() else expect.stderr)
    return expect.returncode


GATE_KEYS = ("set", "gold", "metric", "direction", "baseline_run", "baseline", "threshold",
             "date", "signed_off")


def read_gate(name: str) -> dict:
    """A gate file is `key: value` lines, committed before the run it governs."""
    path = UMBRELLA / "review" / "gates" / f"{name}.md"
    if not path.is_file():
        raise SystemExit(f"no gate {path}")
    rel = str(path.relative_to(UMBRELLA))
    if not git(UMBRELLA, "log", "-1", "--format=%H", "--", rel, check=False).strip() \
            or git(UMBRELLA, "status", "--porcelain", "--", rel).strip():
        raise SystemExit(f"{rel} must be committed, unchanged, before the gate runs")
    gate = {}
    for line in path.read_text().splitlines():
        m = re.match(r"^([a-z_]+):\s*(.+?)\s*$", line)
        if m:
            gate[m.group(1)] = m.group(2)
    missing = [k for k in GATE_KEYS if k not in gate]
    if missing:
        raise SystemExit(f"{rel} lacks {', '.join(missing)}")
    if gate["direction"] not in ("higher", "lower"):
        raise SystemExit(f"{rel}: direction must be higher or lower")
    gate["committed"] = git(UMBRELLA, "log", "-1", "--format=%h %cI", "--", rel).strip()
    return gate


def gate_passes(gate: dict, value: float | None) -> bool:
    if value is None:
        return False
    threshold = float(gate["threshold"])
    return value >= threshold if gate["direction"] == "higher" else value <= threshold


def run_gate(args, checkout: Path, base: str, head: str, out_dir: Path) -> int:
    """L4: the pre-registered gate's set on base and head; the head's number decides."""
    gate = read_gate(args.gate)
    module = args.repo if args.repo in ("querystore", "chartsearchai") else None
    if not module:
        raise SystemExit("a model gate deploys a backend module; REPO must be querystore or chartsearchai")
    deploy = BIN / "deploy-head.sh"
    measured = {}
    try:
        with run_environment(DATA, gate["set"], out_dir / "settings-as-found.json") as env:
            for label, ref in (("base", base), ("head", head)):
                subprocess.run([str(deploy), module, ref], check=True)
                run_dir = run_set("validate-run", gate["set"], out_dir / f"gate-{args.gate}-{label}.log", env)
                scored = harness("validate", "score-citations", "--run-dir", str(run_dir),
                                 "--gold", str(DATA / gate["gold"]))
                if scored.returncode:
                    raise SystemExit(f"scoring {run_dir} failed: {scored.stderr[-500:]}")
                summary = json.loads((run_dir / "citation_scores.json").read_text())["summary"]
                arm = gate.get("backend") or next(iter(summary))
                measured[label] = {"ref": ref, "run": str(run_dir), "summary": summary[arm],
                                   "value": summary[arm].get(gate["metric"])}
    finally:
        subprocess.run([str(deploy), module, "--restore"], check=True)
    passed = gate_passes(gate, measured["head"]["value"])
    lines = [f"# Gate {args.gate}: {'PASS' if passed else 'FAIL'}", "",
             f"Pre-registered {gate['date']} by {gate['signed_off']} (committed {gate['committed']}): "
             f"{gate['metric']} {'>=' if gate['direction'] == 'higher' else '<='} {gate['threshold']} "
             f"on {gate['set']}; baseline {gate['baseline']} from run {gate['baseline_run']}.", "",
             "| Arm | Commit | Run | " + gate["metric"] + " |", "| --- | --- | --- | ---: |"]
    for label, m in measured.items():
        lines.append(f"| {label} | {m['ref'][:7]} | {m['run']} | {m['value']} |")
    (out_dir / f"gate-{args.gate}.md").write_text("\n".join(lines) + "\n")
    print(lines[0], f"head {measured['head']['value']} base {measured['base']['value']}")
    return 0 if passed else 1


def measure(set_id: str, gold: str) -> int:
    """Run a set on the stack as deployed and score it: the number a gate pre-registers."""
    out_dir = work_dir() / f"measure-{set_id}-{time.strftime('%Y%m%d-%H%M%S')}"
    out_dir.mkdir(parents=True)
    with run_environment(DATA, set_id, out_dir / "settings-as-found.json") as env:
        run_dir = run_set("validate-run", set_id, out_dir / "run.log", env)
    scored = harness("validate", "score-citations", "--run-dir", str(run_dir), "--gold", str(DATA / gold))
    print(f"run {run_dir.name}\n{scored.stdout}")
    return scored.returncode


def advertised_profiles() -> set[str]:
    data = rest_get("chartsearchai/models").get("data", [])
    return {m["id"] for m in data if m.get("available")}


def run_full(args) -> int:
    """L5: the full matrix, extra arms from the Hub's advertised profiles, judged and reported."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = work_dir() / f"full-{stamp}"
    out_dir.mkdir(parents=True)
    data_root = DATA
    if args.profiles:
        wanted = [p.strip() for p in args.profiles.split(",") if p.strip()]
        offered = advertised_profiles()
        missing = [p for p in wanted if p not in offered]
        if missing:
            raise SystemExit(f"not advertised by the Hub now: {', '.join(missing)} "
                             f"(advertised: {', '.join(sorted(offered))})")
        data_root = out_dir / "data"
        shutil.copytree(DATA, data_root)
        backends = json.loads((data_root / "backends.json").read_text())
        cset_path = data_root / "comparison_sets" / f"{args.set}.json"
        cset = json.loads(cset_path.read_text())
        for profile in wanted:
            arm = f"hub-profile-{profile}"
            backends[arm] = {"label": f"Hub profile {profile} (advertised)", "kind": "provider_arm",
                             "provider": "hub",
                             "endpointUrl": "http://med-agent-hub:8080/v1/chat/completions",
                             "modelName": profile}
            cset["backend_ids"].append(arm)
        (data_root / "backends.json").write_text(json.dumps(backends, indent=1))
        cset_path.write_text(json.dumps(cset, indent=1))
    with run_environment(data_root, args.set, out_dir / "settings-as-found.json") as env:
        run_dir = run_set("validate-run", args.set, out_dir / "run.log", env,
                          data_root if data_root != DATA else None)
    subprocess.run(["make", "-C", str(HARNESS), "validate-judge-prep", f"RUN={run_dir}"], check=True,
                   capture_output=True)
    answer = run_role(args, "judge", run_dir, (BRIEFS / "judge.md").read_text() +
                      f"\n## Inputs\n\n- Run directory: {run_dir}\n", out_dir / "judge.md")
    rows = out_dir / "judge-rows.json"
    rows.write_text(json.dumps(last_json(answer)))
    subprocess.run(["make", "-C", str(HARNESS), "validate-judge-finalize", f"RUN={run_dir}",
                    f"ROWS={rows}"], check=True, capture_output=True)
    report = harness("validate", "report", "--run-dir", str(run_dir))
    judged = [json.loads(l) for l in (run_dir / "judge.jsonl").read_text().splitlines() if l.strip()]
    lines = [f"# Full evaluation {args.set} ({stamp})", "", f"Run: {run_dir}",
             f"Report: {report.stdout.strip()}", "", "| Arm | Cells | Accuracy | Completeness | "
             "Relevance | Harm |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for arm in sorted({r["backend_id"] for r in judged}):
        rs = [r for r in judged if r["backend_id"] == arm]
        mean = lambda k: round(sum(r[k] for r in rs) / len(rs), 2)
        lines.append(f"| {arm} | {len(rs)} | {mean('accuracy')} | {mean('completeness')} | "
                     f"{mean('relevance')} | {sum(r['harm'] for r in rs)} |")
    if args.baseline:
        lines += ["", f"Compared with run {args.baseline}: "
                  f"{HARNESS / 'artifacts/validate' / args.baseline / 'report.html'}"]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int)
    ap.add_argument("--repo", default="chartsearchai", choices=REPOS)
    ap.add_argument("--agent", default="claude", choices=("claude", "codex", "gemini", "human"))
    ap.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--stack", action="store_true")
    ap.add_argument("--replies", action="store_true", help="draft replies from the last round")
    ap.add_argument("--scenarios", help="L3: a harness comparison set with turn checks")
    ap.add_argument("--no-review", action="store_true", help="skip the reviewer rounds")
    ap.add_argument("--gate", help="L4: a pre-registered gate under review/gates/")
    ap.add_argument("--gate-base", help="the base the gate compares with (default: the layer below)")
    ap.add_argument("--full", action="store_true", help="L5: the full evaluation matrix")
    ap.add_argument("--set", default="full-default")
    ap.add_argument("--profiles", help="extra arms: comma-separated profiles the Hub advertises")
    ap.add_argument("--baseline", help="an earlier full run id to cite for comparison")
    ap.add_argument("--measure", help="run a set on the deployed stack and score it against --gold")
    ap.add_argument("--gold", help="gold file under the harness's datasets/validation/")
    ap.add_argument("--checkout", help="a checkout other than the umbrella's for --repo")
    args = ap.parse_args()
    if args.measure:
        return measure(args.measure, args.gold)
    if args.full and not args.pr:
        return run_full(args)
    if not args.pr:
        ap.error("--pr is required unless --full runs alone")

    checkout = Path(args.checkout).resolve() if args.checkout else UMBRELLA / REPOS[args.repo]
    remote, slug = upstream(checkout)
    out_dir = work_dir() / f"{args.repo}-{args.pr}"
    out_dir.mkdir(parents=True, exist_ok=True)
    threads = out_dir / "threads.json"
    subprocess.run([str(BIN / "threads.py"), slug, str(args.pr), str(threads)], check=True)
    meta = json.loads(threads.read_text())

    if args.replies:
        fetch_pr(checkout, remote, args.pr)
        rounds = sorted(out_dir.glob("findings-*.json"))
        ledger = work_dir() / "ledger"
        prompt = (BRIEFS / "reply.md").read_text() + (
            f"\n## Inputs\n\n- Threads: {threads}\n- Last round: {rounds[-1] if rounds else 'none'}\n"
            f"- Probe ledger (red and green lines by commit): {ledger}\n"
            f"- Commits on the PR: `git log {meta['base']}..refs/review/pr/{args.pr}`\n")
        run_role(args, "reply", checkout, prompt, out_dir / "replies.md")
        print(f"drafted {out_dir / 'replies.md'}")
        return 0

    for k in range(1, 0 if args.no_review else args.rounds + 1):
        head = fetch_pr(checkout, remote, args.pr)
        wt = work_dir() / "wt-review" / args.repo
        brief = (BRIEFS / "reviewer.md").read_text()
        inputs = [f"- Repository checkout at the PR head {head}: {wt}",
                  f"- Base: {remote}/{meta['base']}", f"- Threads and ticket: {threads}",
                  f"- Effort: {args.effort}" + (" (from round 2 on, blocking findings only)"
                                               if k > 1 else "")]
        previous = out_dir / f"findings-{k - 1}.json"
        if previous.exists():
            inputs.append(f"- Previous round: {previous}")
        target = head
        if args.stack:
            layers = stack(checkout, remote, slug, meta["author"], args.pr, head)
            target = layers[-1]["head"] if layers else head
            brief += "\n" + (BRIEFS / "stack.md").read_text()
            inputs.append("- Stack, bottom to top (the checkout is the merged top "
                          f"{target[:7]}):\n" + "\n".join(
                              f"  - #{l['number']} {l['title']} ({l['head'][:7]})" for l in layers))
        worktree(checkout, wt, target)
        answer = run_role(args, "reviewer", wt, brief + "\n## Inputs\n\n" + "\n".join(inputs) + "\n",
                          out_dir / f"reviewer-{k}.md")
        data = last_json(answer)
        data.update(repo=args.repo, pr=args.pr, head=head,
                    findings=settle(data.get("findings", [])))
        record(out_dir, k, data)
        blocking = [f for f in data["findings"] if f.get("blocking")]
        print(f"round {k}: {len(blocking)} blocking, "
              f"{len(data['findings']) - len(blocking)} questions -> {out_dir / f'round-{k}.md'}")
        if not blocking or k == args.rounds:
            break
        if args.agent == "human":
            print("fix the blocking findings on the PR branch, push, and re-run")
            return 3
        fix_wt = worktree(checkout, work_dir() / "wt-fix" / args.repo,
                          head, branch=meta["head_branch"])
        run_role(args, "fixer", fix_wt, (BRIEFS / "fixer.md").read_text() +
                 f"\n## Inputs\n\n- Findings to fix: {out_dir / f'findings-{k}.json'}\n"
                 f"- Push with: git push origin HEAD:{meta['head_branch']}\n",
                 out_dir / f"fixer-{k}.md")
    status = 0
    head = fetch_pr(checkout, remote, args.pr)
    if args.scenarios:
        status |= scenarios(args, head, out_dir)
    if args.gate:
        base = args.gate_base
        if not base:
            layers = [l for l in stack(checkout, remote, slug, meta["author"], args.pr, head)
                      if l["head"] != head and subprocess.run(
                          ["git", "-C", str(checkout), "merge-base", "--is-ancestor", l["head"], head]
                      ).returncode == 0]
            base = layers[-1]["head"] if layers else git(
                checkout, "merge-base", head, f"{remote}/{meta['base']}").strip()
        status |= run_gate(args, checkout, base, head, out_dir)
    if args.full:
        status |= run_full(args)
    return status


if __name__ == "__main__":
    sys.exit(main())
