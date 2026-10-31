#!/usr/bin/env python3
"""Drive `make review`: threads, fresh-session roles, rounds, and the optional layers.

Writes everything to work/review/<repo>-<pr>/: threads.json, the prompts, each role's
answer, findings-<round>.json and round-<round>.md. Posts nothing.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
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
ACTIVE_RESULT = None
REPOS = {"chartsearchai": "targets/chartsearchai", "esm": "targets/chartsearchai-esm",
         "querystore": "targets/querystore", "hub": "targets/med-agent-hub",
         "harness": "targets/validation-harness", "umbrella": "."}
# The other side of the contract. Select its feature revision explicitly when stacks
# differ; otherwise use its current local checkout and record that limitation.
CONSUMERS = {"querystore": "chartsearchai", "chartsearchai": "querystore", "esm": "chartsearchai", "hub": "harness", "harness": "hub"}
OPENMRS = re.compile(r"github\.com[:/]+(openmrs/[^/\s]+?)(\.git)?$")


def upstream(checkout: Path, repository: str | None = None) -> tuple[str, str]:
    """The remote that points at the OpenMRS repository, and its owner/name."""
    for line in git(checkout, "remote", "-v").splitlines():
        name, url = line.split()[:2]
        m = re.search(r"github\.com[:/]+([^/\s]+/[^/\s]+?)(\.git)?$", url) if repository else OPENMRS.search(url)
        if m and (repository is None or m.group(1) == repository):
            return name, m.group(1)
    raise SystemExit(f"{checkout}: no remote points at github.com/openmrs")


def fetch_pr(checkout: Path, remote: str, pr: int) -> str:
    git(checkout, "fetch", "-q", remote, f"+pull/{pr}/head:refs/review/pr/{pr}")
    return git(checkout, "rev-parse", f"refs/review/pr/{pr}").strip()


def current_identity(slug: str, pr: int) -> dict:
    out = subprocess.run(["gh", "pr", "view", str(pr), "-R", slug, "--json",
                          "headRefOid,baseRefOid,baseRefName"],
                         capture_output=True, text=True, check=True).stdout
    identity = json.loads(out)
    if not isinstance(identity, dict) or any(not isinstance(identity.get(k), str) or not identity[k]
            for k in ("headRefOid", "baseRefOid", "baseRefName")):
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
    ordered = sorted(layers, key=lambda l: l["commits"])
    if any(not anc(a["head"], b["head"]) for a, b in zip(ordered, ordered[1:])):
        raise SystemExit("Ambiguous stack: descendant branches diverge")
    return ordered


def last_json(text: str):
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    if not blocks:
        raise SystemExit("the role's answer has no ```json block")
    return json.loads(blocks[-1])


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
        if not isinstance(finding, dict) or not isinstance(finding.get("blocking"), bool) or not isinstance(finding.get("line"), int) or not isinstance(finding.get("file"), str) or not isinstance(finding.get("finding"), str):
            raise ValueError("invalid finding")


def settle(findings: list[dict]) -> list[dict]:
    """A blocking finding needs a failure mode and evidence; otherwise it is a question."""
    for f in findings:
        if f.get("blocking") and not (f.get("failure_mode") and f.get("evidence")):
            f["blocking"] = False
            f["downgraded"] = "blocking without a failure mode and evidence"
    return findings


def run_role(args, role: str, workdir: Path, prompt: str, out: Path) -> str:
    prompt_file = out.with_suffix(".prompt.md")
    scratch = out.parent / "scratch"
    scratch.mkdir(exist_ok=True)
    prompt += f"\nKeep all working scripts and logs in {scratch}, never /tmp. Preserve reproduction scripts there.\n"
    if role != "fixer":
        prompt += ("\nYour final message is saved as your answer: do not write it to a file, and "
                   "leave the repository as you found it.\n")
    prompt_file.write_text(prompt)
    role_script = out.with_suffix(".role.sh")
    role_script.write_bytes((BIN / "role.sh").read_bytes())
    rc = subprocess.run(["bash", str(role_script), args.agent, role, str(workdir),
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
            data_root: Path | None = None, resume: str | None = None) -> Path:
    """Run a comparison set through the umbrella's make target; return the run directory.

    With ``resume``, the cells that run completed cleanly are carried over and only the rest
    run, so arms added since are the only new work.
    """
    cmd = ["make", "-C", str(UMBRELLA), make_target, f"SET={comparison_set}"]
    if data_root:
        cmd.append(f"VALIDATE_DATA_ROOT={data_root}")
    if resume:
        cmd.append(f"RESUME={Path(resume).resolve()}")
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
                          data_root if data_root != DATA else None, args.resume)
    subprocess.run(["make", "-C", str(HARNESS), "validate-judge-prep", f"RUN={run_dir}"], check=True,
                   capture_output=True)
    answer = run_role(args, "judge", run_dir, (BRIEFS / "judge.md").read_text() +
                      f"\n## Inputs\n\n- Run directory: {run_dir}\n", out_dir / "judge.md")
    rows = out_dir / "judge-rows.json"
    rows.write_text(json.dumps(last_json(answer)))
    subprocess.run(["make", "-C", str(HARNESS), "validate-judge-finalize", f"RUN={run_dir}",
                    f"ROWS={rows}"], check=True, capture_output=True)
    report = harness("validate", "report", "--run-dir", str(run_dir))
    lines = [f"# Full evaluation {args.set} ({stamp})", "", f"Run: {run_dir}",
             f"Report: {report.stdout.strip()}", ""] + arm_table(run_dir)
    if args.baseline:
        lines += ["", f"Compared with run {args.baseline}: "
                  f"{HARNESS / 'artifacts/validate' / args.baseline / 'report.html'}"]
    if args.publish_evaluation and not args.no_publish:
        lines += ["", f"Published: {publish_full(run_dir, args.set)}"]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def arm_means(run_dir: Path) -> dict[str, dict]:
    """Each arm's judged cell count, mean scores and harm flags."""
    judged = [json.loads(l) for l in (run_dir / "judge.jsonl").read_text().splitlines() if l.strip()]
    out = {}
    for arm in sorted({r["backend_id"] for r in judged}):
        rs = [r for r in judged if r["backend_id"] == arm]
        mean = lambda k: round(sum(r[k] for r in rs) / len(rs), 2)
        out[arm] = {"cells": len(rs), "accuracy": mean("accuracy"), "completeness": mean("completeness"),
                    "relevance": mean("relevance"), "harm": sum(r["harm"] for r in rs)}
    return out


def arm_table(run_dir: Path) -> list[str]:
    lines = ["| Arm | Cells | Accuracy | Completeness | Relevance | Harm |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for arm, m in arm_means(run_dir).items():
        lines.append(f"| {arm} | {m['cells']} | {m['accuracy']} | {m['completeness']} | "
                     f"{m['relevance']} | {m['harm']} |")
    return lines


def publish_full(run_dir: Path, set_id: str) -> str:
    """Freeze the run's dashboard beside its report and publish both to the reports site.

    The frozen dashboard is the live one with every cell embedded, so the published page
    drills into each turn as the live page did. Returns the published URL.
    """
    subprocess.run(["uv", "--directory", str(HARNESS), "run", "python", "scripts/validate-dashboard.py",
                    "--freeze", str(run_dir / "dashboard.html"), "--run", str(run_dir)],
                   check=True, capture_output=True)
    day = time.strftime("%Y-%m-%d", time.localtime(run_dir.stat().st_mtime))
    slug = f"l5-{set_id}-{day}-{run_dir.name[:8]}"
    means = arm_means(run_dir)
    # The index's score table is the report's own judge summary, frozen beside the report.
    scout = subprocess.run(
        ["uv", "--directory", str(HARNESS), "run", "python", "-c",
         "import json, sys\nfrom harness.validate.reconcile import scout_summary\n"
         "rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]\n"
         "print(json.dumps(scout_summary(rows, list(dict.fromkeys(r['backend_id'] for r in rows)))))",
         str(run_dir / "judge.jsonl")], check=True, capture_output=True, text=True).stdout
    (run_dir / "meta.json").write_text(json.dumps({"scout": json.loads(scout)}, indent=2) + "\n")
    # The index shows the judged scores as a table; the catalog's editor writes the takeaway.
    # A run already in the catalog keeps the copy written for it.
    listed = {r["slug"] for r in json.loads((UMBRELLA / "reports/reports-index.json").read_text())["runs"]}
    title = "" if slug in listed else f"Full evaluation {set_id}, {day} ({run_dir.name[:8]})"
    summary = "" if slug in listed else (
        f"Full evaluation (L5) of the {set_id} comparison on the assembled local stack: "
        f"{len(means)} setups, {sum(m['cells'] for m in means.values())} graded conversations.")
    proc = subprocess.run([str(UMBRELLA / "scripts/publish-report.sh"), "chartsearchai", str(run_dir), slug,
                           title, summary],
                          cwd=UMBRELLA, capture_output=True, text=True)
    (run_dir.parent / f"{run_dir.name}-publish.log").write_text(proc.stdout + proc.stderr)
    log = run_dir.parent / f"{run_dir.name}-publish.log"
    m = re.search(r"==> published: (\S+)", proc.stdout)
    if not proc.returncode and m:
        return m.group(1)
    raise SystemExit(f"publishing {slug} failed; see {log}")


def run_set_id(run_dir: Path) -> str:
    """The comparison set a run recorded in its run event."""
    for line in (run_dir / "events.jsonl").read_text().splitlines():
        event = json.loads(line) if line.strip() else {}
        if event.get("event_type") == "run" and event.get("comparison_set"):
            return event["comparison_set"]
    raise SystemExit(f"{run_dir}: no comparison_set in its run event")


def main() -> int:
    global ACTIVE_RESULT
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int)
    ap.add_argument("--repository", help="Exact GitHub owner/repository; selects the matching remote")
    ap.add_argument("--fix", action="store_true", help="Authorize fixer commits and pushes between rounds")
    ap.add_argument("--publish-evaluation", action="store_true")
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
    ap.add_argument("--no-publish", action="store_true",
                    help="L5: keep the report and dashboard local instead of publishing them")
    ap.add_argument("--publish", metavar="RUN_DIR", help="publish an already judged L5 run")
    ap.add_argument("--resume", metavar="RUN_DIR",
                    help="L5: carry that run's clean cells over and run only the rest (an added arm)")
    ap.add_argument("--measure", help="run a set on the deployed stack and score it against --gold")
    ap.add_argument("--gold", help="gold file under the harness's datasets/validation/")
    ap.add_argument("--checkout", help="a checkout other than the umbrella's for --repo")
    ap.add_argument("--threads-until", help="ISO instant: review the PR as it stood then")
    ap.add_argument("--consumer-head", help="Explicit consumer revision for cross-repository review")
    ap.add_argument("--consumer-repo", choices=REPOS, help="Override the component on the other side of this contract")
    ap.add_argument("--no-consumer", action="store_true", help="omit the other repository's checkout")
    ap.add_argument("--head", help="review this local ref instead of the PR's pushed head (review before the push)")
    ap.add_argument("--base", help="with --head: the local ref of the layer below, instead of the remote base branch")
    args = ap.parse_args()
    if args.no_consumer and (args.consumer_head or args.consumer_repo):
        ap.error("--no-consumer cannot select a consumer repository or revision")
    if args.base and not args.head:
        ap.error("--base needs --head")
    if args.head and args.stack:
        ap.error("--head reviews one local layer; --stack reads the pushed stack")
    if args.measure:
        return measure(args.measure, args.gold)
    if args.publish:
        run_dir = Path(args.publish).resolve()
        print(f"Published: {publish_full(run_dir, run_set_id(run_dir))}")
        return 0
    if args.full and not args.pr:
        return run_full(args)
    if not args.pr:
        ap.error("--pr is required unless --full runs alone")

    checkout = Path(args.checkout).resolve() if args.checkout else UMBRELLA / REPOS[args.repo]
    remote, slug = upstream(checkout, args.repository)
    git(checkout, "fetch", "-q", remote)
    out_dir = work_dir() / f"{args.repo}-{args.pr}"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_lock = (out_dir / "run.lock").open("w")
    fcntl.flock(run_lock, fcntl.LOCK_EX)
    ACTIVE_RESULT = out_dir / "result.json"
    ACTIVE_RESULT.write_text(json.dumps({"execution": "running", "assessment": "undetermined"}))
    threads = out_dir / "threads.json"
    subprocess.run([str(BIN / "threads.py"), slug, str(args.pr), str(threads)]
                   + (["--until", args.threads_until] if args.threads_until else []), check=True)
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
        # A local head is the round before the push: the PR's threads and body still apply, the
        # code under review is the checkout's own ref, and the base is the local layer below.
        head = (git(checkout, "rev-parse", "--verify", f"{args.head}^{{commit}}").strip() if args.head
                else fetch_pr(checkout, remote, args.pr))
        base = git(checkout, "rev-parse", args.base if args.base else f"{remote}/{meta['base']}").strip()
        wt = work_dir() / "wt-review" / args.repo / str(args.pr)
        brief = (BRIEFS / "reviewer.md").read_text()
        inputs = [f"- Repository checkout at the {'local, not yet pushed' if args.head else 'PR'} head {head}: {wt}",
                  f"- Base: {base}", f"- Prepared Python interpreter: {os.environ.get('REVIEW_PYTHON', 'not supplied; report dependency gaps')}", f"- Threads and ticket: {threads}",
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
        consumer = None if args.no_consumer else args.consumer_repo or CONSUMERS.get(args.repo)
        if args.consumer_head and not consumer:
            ap.error("--consumer-head needs a consumer; select one with --consumer-repo")
        if consumer and not (UMBRELLA / REPOS[consumer] / ".git").exists():
            inputs.append(f"- Consumer {consumer} is unavailable; its contract is unverified.")
            consumer = None
        if consumer:
            consumer_checkout = UMBRELLA / REPOS[consumer]
            consumer_sha = git(consumer_checkout, "rev-parse", args.consumer_head or "HEAD").strip()
            consumer_wt = worktree(consumer_checkout, out_dir / "consumer" / consumer, consumer_sha)
            inputs.append(f"- Consumer repository ({consumer}) at supplied local revision {consumer_sha[:7]}, read-only: "
                          f"{consumer_wt}")
        answer = run_role(args, "reviewer", wt, brief + "\n## Inputs\n\n" + "\n".join(inputs) + "\n",
                          out_dir / f"reviewer-{k}.md")
        verify_checkout(wt, target)
        if consumer:
            verify_checkout(consumer_wt, consumer_sha)
        data = last_json(answer)
        changed = git(wt, "diff", "--name-only", f"{base}...{target}").splitlines()
        validate_review(data, target, changed)
        fresh = current_identity(slug, args.pr) if not args.head else None
        stale = bool(fresh and (fresh["headRefOid"] != head or fresh["baseRefOid"] != base
                               or fresh["baseRefName"] != meta["base"]))
        if args.stack and layers:
            stale |= current_identity(slug, layers[-1]["number"])["headRefOid"] != target
        data.update(repo=args.repo, repository=slug, pr=args.pr, requested_head=head, base=base,
                    base_branch=meta["base"], identity_after=fresh,
                    consumer_repo=consumer,
                    consumer_head=consumer_sha if consumer else None,
                    execution=("superseded" if stale else "partial" if data["unreviewed_files"] else "complete"),
                    behavior_verification="see evidence; not inferred from source review",
                    findings=settle(data["findings"]))
        data["dependency_files"] = {str(p.relative_to(wt)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for name in ("uv.lock", "poetry.lock", "yarn.lock", "package-lock.json", "pyproject.toml")
                                    if (p := wt / name).is_file()}
        data["assessment"] = ("undetermined" if data["execution"] != "complete" else
                              "findings" if data["findings"] else "no_findings")
        ACTIVE_RESULT.write_text(json.dumps(data, indent=2))
        record(out_dir, k, data)
        blocking = [f for f in data["findings"] if f.get("blocking")]
        print(f"round {k}: {len(blocking)} blocking, "
              f"{len(data['findings']) - len(blocking)} questions -> {out_dir / f'round-{k}.md'}")
        if not blocking or k == args.rounds or not args.fix:
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
    try:
        sys.exit(main())
    except BaseException as exc:
        if ACTIVE_RESULT and not (isinstance(exc, SystemExit) and exc.code in (None, 0)):
            ACTIVE_RESULT.write_text(json.dumps({"execution": "error", "assessment": "undetermined",
                                                "error": str(exc)}, indent=2))
        raise
