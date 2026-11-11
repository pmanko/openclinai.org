#!/usr/bin/env python3
"""Workspace wrapper for running clinical AI evaluations, gates, and blind judging.

Evaluation and blind-session judging live in targets/validation-harness
(harness-cli validate run / judge / report). This script coordinates OpenMRS
settings/module swaps when running against the local Docker stack and delegates
judging and v2 JSON packet generation to the validation harness.
Publishing is handled explicitly via scripts/publish-report.py.
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
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

UMBRELLA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UMBRELLA / "review" / "lib"))
from reviewkit.git import git  # noqa: E402
from reviewkit.probes import work_dir  # noqa: E402

BIN = UMBRELLA / "review" / "bin"
BRIEFS = UMBRELLA / "review" / "briefs"
HARNESS = UMBRELLA / "targets" / "validation-harness"
DATA = HARNESS / "datasets" / "validation"
LLM_SETTINGS = (
    "chartsearchai.llm.engine",
    "chartsearchai.llm.remote.endpointUrl",
    "chartsearchai.llm.remote.modelName",
)
HUB_TAP = f"http://host.docker.internal:{os.environ.get('HUB_TAP_PORT', '8079')}"

DEFAULT_JUDGE_SETTINGS = {
    "claude": ("claude-sonnet-5-5", "medium"),
    "codex": ("gpt-6.1-sol", "medium"),
    "gemini": ("unrecorded", "unrecorded"),
    "human": ("human", ""),
}
_ALLOC_LOCK = threading.Lock()


def last_json(text: str):
    """Extract and parse the last ```json block, tolerating trailing commas outside strings."""
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


def run_role(
    args,
    role: str,
    workdir: Path,
    prompt: str,
    out: Path,
    agent: str | None = None,
    env: dict | None = None,
) -> str:
    prompt_file = out.with_suffix(".prompt.md")
    scratch = out.parent / "scratch"
    scratch.mkdir(exist_ok=True)
    prompt += (
        f"\nKeep all working scripts and logs in {scratch}, never /tmp. Preserve reproduction scripts there.\n"
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


def harness(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "--directory", str(HARNESS), "run", "harness-cli", *args],
        capture_output=True,
        text=True,
    )


def openmrs(shell: str) -> str:
    return subprocess.run(
        ["bash", "-c", f". scripts/openmrs-settings-lib.sh; {shell}"],
        cwd=UMBRELLA,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def rest_get(path: str) -> dict:
    return json.loads(
        openmrs(
            'openmrs_curl -fsS -u "$OPENMRS_SETTINGS_USER:$OPENMRS_SETTINGS_PASS" '
            f'"$OPENMRS_SETTINGS_BASE_URL/ws/rest/v1/{path}"'
        )
    )


@contextmanager
def run_environment(data_root: Path, set_id: str, record: Path):
    cset = json.loads((data_root / "comparison_sets" / f"{set_id}.json").read_text())
    backends = json.loads((data_root / "backends.json").read_text())
    if not any(backends[b].get("kind") == "provider_arm" for b in cset["backend_ids"]):
        yield {}
        return
    found = {
        r["property"]: r["value"]
        for r in rest_get("systemsetting?q=chartsearchai.llm&v=full")["results"]
        if r["property"] in LLM_SETTINGS
    }
    record.write_text(json.dumps(found, indent=1))
    subprocess.run([str(UMBRELLA / "scripts/parity-engine-up.sh")], check=True, cwd=UMBRELLA)
    try:
        yield {"MED_AGENT_LLM_BASE_URL": HUB_TAP}
    finally:
        for name in LLM_SETTINGS:
            if name in found:
                openmrs(f"set_openmrs_property {json.dumps(name)} {json.dumps(found[name] or '')}")
            else:
                openmrs(
                    'openmrs_curl -fsS -o /dev/null -X DELETE -u "$OPENMRS_SETTINGS_USER:'
                    '$OPENMRS_SETTINGS_PASS" "$OPENMRS_SETTINGS_BASE_URL/ws/rest/v1/'
                    f'systemsetting/{name}?purge=true"'
                )
        subprocess.run(
            ["make", "-C", str(UMBRELLA), "med-agent-hub-up"],
            check=True,
            env={k: v for k, v in os.environ.items() if k != "MED_AGENT_LLM_BASE_URL"},
        )


def run_set(
    make_target: str,
    comparison_set: str,
    out: Path,
    env: dict | None = None,
    data_root: Path | None = None,
    resume: str | None = None,
) -> Path:
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
    return run_dir if run_dir.is_absolute() else HARNESS / run_dir


GATE_KEYS = (
    "set",
    "gold",
    "metric",
    "direction",
    "baseline_run",
    "baseline",
    "threshold",
    "date",
    "signed_off",
)


def read_gate(name: str) -> dict:
    path = UMBRELLA / "review" / "gates" / f"{name}.md"
    if not path.is_file():
        raise SystemExit(f"no gate {path}")
    rel = str(path.relative_to(UMBRELLA))
    if (
        not git(UMBRELLA, "log", "-1", "--format=%H", "--", rel, check=False).strip()
        or git(UMBRELLA, "status", "--porcelain", "--", rel).strip()
    ):
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


def advertised_profiles() -> dict[str, str]:
    data = rest_get("chartsearchai/models").get("data", [])
    return {m["id"]: str(m.get("label") or m["id"]) for m in data if m.get("available")}


def profile_arms(offered: dict[str, str], wanted: list[str]) -> dict[str, dict]:
    return {
        f"hub-profile-{profile}": {
            "label": offered.get(profile) or profile,
            "kind": "provider_arm",
            "provider": "hub",
            "endpointUrl": "http://med-agent-hub:8080/v1/chat/completions",
            "modelName": profile,
        }
        for profile in wanted
    }


def _resolve_data_root(raw: Path | str | None) -> Path:
    if not raw:
        return DATA
    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    if p.exists():
        return p.resolve()
    return (UMBRELLA / p).resolve()


@contextmanager
def _run_judge_lock(run_dir: Path):
    judges_dir = run_dir / "judges"
    judges_dir.mkdir(parents=True, exist_ok=True)
    lock_path = judges_dir / ".alloc.lock"
    with _ALLOC_LOCK:
        with open(lock_path, "a+", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield judges_dir
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def parse_judges(args) -> list[dict]:
    raw_passes = getattr(args, "judge_passes", 1)
    default = 1 if raw_passes is None else int(raw_passes)
    if default < 1:
        raise SystemExit(f"--judge-passes must be at least 1, got {raw_passes!r}")
    judges = []
    for spec in getattr(args, "judges", None) or []:
        parts = spec.split(":")
        if len(parts) not in (3, 4) or not all(parts) or (len(parts) == 4 and not parts[3].isdigit()):
            raise SystemExit(f"--judge wants agent:model:effort[:passes], got {spec!r}")
        passes = int(parts[3]) if len(parts) == 4 else default
        if passes < 1:
            raise SystemExit(f"--judge {spec!r}: passes must be at least 1")
        judges.append({"agent": parts[0], "model": parts[1], "effort": parts[2], "passes": passes})
    if judges:
        return judges
    default_model, default_effort = DEFAULT_JUDGE_SETTINGS.get(args.agent, ("gpt-6.1-sol", "medium"))
    return [
        {
            "agent": args.agent,
            "model": os.environ.get("REVIEW_MODEL") or default_model,
            "effort": os.environ.get("REVIEW_REASONING") or default_effort,
            "passes": default,
        }
    ]


def run_judges(run_dir: Path) -> tuple[list[str], dict[tuple, int], bool]:
    try:
        built = json.loads((run_dir / "judges" / "canonical.json").read_text()).get("built_from") or []
    except (OSError, json.JSONDecodeError):
        built = []
    last: dict[tuple, int] = {}
    blinded = False
    for manifest in sorted((run_dir / "judges").glob("*/manifest.json")):
        try:
            card = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        key = (
            str(card.get("agent") or ""),
            str(card.get("model") or ""),
            str(card.get("reasoning_effort") or ""),
        )
        last[key] = max(last.get(key, 0), int(card.get("pass_index") or 1))
        blinded = blinded or (manifest.parent.name in built and bool(card.get("blinded")))
    return [str(a) for a in built], last, blinded


def _reserve_judge_passes(run_dir: Path, judges: list[dict]) -> list[tuple[dict, int, int]]:
    with _run_judge_lock(run_dir) as judges_dir:
        _, last, _ = run_judges(run_dir)
        res_file = judges_dir / ".reserved.json"
        try:
            raw_res = json.loads(res_file.read_text()) if res_file.exists() else {}
        except (OSError, json.JSONDecodeError):
            raw_res = {}
        reserved: dict[tuple, int] = {}
        for k_str, val in raw_res.items():
            parts = k_str.split("\0")
            if len(parts) == 3 and isinstance(val, int):
                reserved[tuple(parts)] = val
        allocations = []
        for judge in judges:
            key = (judge["agent"], judge["model"], judge["effort"])
            start = max(last.get(key, 0), reserved.get(key, 0))
            end = start + judge["passes"]
            reserved[key] = end
            allocations.append((judge, start, end))
        res_file.write_text(json.dumps({"\0".join(k): v for k, v in reserved.items()}, indent=1))
        return allocations


def _expected_session_cells(cells_path: Path) -> list[tuple[str, str]]:
    if not cells_path.is_file():
        return []
    expected = []
    for line in cells_path.read_text().splitlines():
        if not line.strip():
            continue
        cell = json.loads(line)
        expected.append((str(cell["scenario_id"]), str(cell["backend_id"])))
    return expected


def _validate_session_rows(rows, expected: list[tuple[str, str]]) -> list[dict]:
    if not isinstance(rows, list) or not rows:
        raise ValueError("verdict JSON must be a non-empty list of cell rows")
    seen: list[tuple[str, str]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {idx} is not an object")
        for req in ("scenario_id", "backend_id", "accuracy"):
            if req not in row:
                raise ValueError(f"row {idx} is missing {req!r}")
        for axis in ("accuracy", "completeness", "relevance"):
            if axis in row:
                val = row[axis]
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    raise ValueError(f"row {idx} {axis!r} must be numeric")
        if "harm" in row and not isinstance(row["harm"], bool):
            raise ValueError(f"row {idx} 'harm' must be boolean")
        seen.append((str(row["scenario_id"]), str(row["backend_id"])))
    if len(set(seen)) != len(seen):
        raise ValueError("duplicate (scenario_id, backend_id) in verdict rows")
    if expected and set(seen) != set(expected):
        missing = sorted(set(expected) - set(seen))
        extra = sorted(set(seen) - set(expected))
        raise ValueError(f"cell coverage mismatch (missing={missing}, unexpected={extra})")
    return rows


def _prepare_blind_session_dir(run_dir: Path, out_dir: Path, tag: str, bundle: Path) -> tuple[Path, Path]:
    session_dir = out_dir / f"{tag}-input-{bundle.stem}"
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    staged_bundle = session_dir / bundle.name
    shutil.copy2(bundle, staged_bundle)
    charts_src = run_dir / "charts"
    if charts_src.is_dir():
        shutil.copytree(charts_src, session_dir / "charts")
    return session_dir, staged_bundle


def judge_card(answer: Path, pass_index: int, passes: int) -> Path:
    session = json.loads(answer.with_suffix(".md.card.json").read_text())
    brief = BRIEFS / "judge.md"
    session.update(
        {
            "brief_sha256": hashlib.sha256(brief.read_bytes()).hexdigest(),
            "brief_path": str(brief.relative_to(UMBRELLA)),
            "pass_index": pass_index,
            "passes": passes,
        }
    )
    card = answer.with_suffix(".card.json")
    card.write_text(json.dumps(session, indent=1))
    return card


def judge_sessions(
    args,
    run_dir: Path,
    out_dir: Path,
    pass_index: int,
    passes: int,
    judge: dict,
    blind: bool,
    tag: str = "judge",
) -> tuple[Path, Path]:
    base = out_dir / f"{tag}.md"
    brief = (BRIEFS / "judge.md").read_text()
    env = {
        k: v
        for k, v in (("REVIEW_MODEL", judge.get("model")), ("REVIEW_REASONING", judge.get("effort")))
        if v
    }
    if blind:
        bundles = sorted((run_dir / "judge-bundles").glob("*.jsonl"))
        if not bundles:
            raise SystemExit(f"{run_dir}: no judge-bundles; run validate-judge-prep with BLIND=1")
        sessions = []
        for b in bundles:
            s_dir, s_bundle = _prepare_blind_session_dir(run_dir, out_dir, tag, b)
            s_inputs = (
                f"\n## Inputs\n\n- Session directory (bounded input containing only this scenario's "
                f"bundle and chart snapshots; do not read outside {s_dir} or inspect maps, other "
                f"scenarios, or earlier judgments): {s_dir}\n"
                f"- Rubric: {HARNESS / '.claude/skills/clinical-answer-scoring/rubric.md'}\n"
                f"- Cells for this session: {s_bundle} (one scenario; its arms are lettered, so score each "
                "answer on its own against the chart and keep the letter as backend_id)\n"
            )
            sessions.append((out_dir / f"{tag}-{b.stem}.md", brief + s_inputs, s_dir, s_bundle))
    else:
        inputs = (
            f"\n## Inputs\n\n- Run directory: {run_dir}\n"
            f"- Rubric: {HARNESS / '.claude/skills/clinical-answer-scoring/rubric.md'}\n"
        )
        sessions = [(base, brief + inputs, run_dir, run_dir / "judge-cells.jsonl")]

    attempts = max(1, int(os.environ.get("JUDGE_ATTEMPTS", "4")))
    retry_delay = int(os.environ.get("JUDGE_RETRY_DELAY", "60"))

    def one(session):
        out, prompt, workdir, cells_path = session
        expected = _expected_session_cells(cells_path)
        for attempt in range(1, attempts + 1):
            try:
                answer = run_role(args, "judge", workdir, prompt, out, agent=judge["agent"], env=env)
                return _validate_session_rows(last_json(answer), expected)
            except SystemExit as e:
                if e.code == 3 or attempt == attempts:
                    raise
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == attempts:
                    raise SystemExit(f"{out}: the judge's verdict block is invalid ({e})")
            time.sleep(retry_delay * attempt)
        return []

    parallel = max(1, int(os.environ.get("JUDGE_PARALLEL", "4")))
    with ThreadPoolExecutor(max_workers=min(parallel, len(sessions))) as pool:
        rows = [r for session_rows in pool.map(one, sessions) for r in session_rows]
    rows_path = base.with_suffix(".rows.json")
    rows_path.write_text(json.dumps(rows))
    cards = [json.loads(out.with_suffix(".md.card.json").read_text()) for out, _, _, _ in sessions]
    identities = {
        (
            c.get("agent"),
            c.get("agent_version"),
            c.get("model"),
            c.get("reasoning_effort"),
            c.get("sampling"),
        )
        for c in cards
    }
    if len(identities) > 1:
        raise SystemExit(f"{base}: session cards diverged within one pass: {identities}")
    merged = {
        **cards[0],
        "started_at": min(c.get("started_at", "") for c in cards),
        "finished_at": max(c.get("finished_at", "") for c in cards),
        "sessions": len(cards),
        "session_cards": cards,
        "blinded": blind,
    }
    base.with_suffix(".md.card.json").write_text(json.dumps(merged, indent=1))
    return rows_path, judge_card(base, pass_index=pass_index, passes=passes)


def judge_passes(args, run_dir: Path, out_dir: Path, keep: list[str] | None = None) -> list[str]:
    keep = list(keep or [])
    judges = parse_judges(args)
    blind = bool(getattr(args, "blind", False))
    allocations = _reserve_judge_passes(run_dir, judges)
    total_new = sum(j["passes"] for j in judges)
    actors = []
    for k, (judge, start, end) in enumerate(allocations, 1):
        for i in range(start + 1, end + 1):
            tag = (
                "judge"
                + (f"-j{k}" if len(judges) > 1 else "")
                + (f"-p{i}" if total_new > 1 or start else "")
            )
            rows, card = judge_sessions(args, run_dir, out_dir, i, end, judge, blind, tag)
            with _run_judge_lock(run_dir):
                done = subprocess.run(
                    [
                        "make",
                        "-C",
                        str(HARNESS),
                        "validate-judge-finalize",
                        f"RUN={run_dir}",
                        f"ROWS={rows}",
                        f"JUDGE_CARD={card}",
                    ]
                    + (["JUDGE_PROMOTE=1"] if total_new == 1 and not keep else []),
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
            m = re.search(r"judges/([^/\s]+)/judge\.jsonl", done)
            if not m:
                raise SystemExit(f"finalize named no actor for {tag}:\n{done}")
            actors.append(m.group(1))
    headline = keep + [a for a in actors if a not in keep]
    if len(headline) > 1:
        with _run_judge_lock(run_dir):
            subprocess.run(
                [
                    "uv",
                    "--directory",
                    str(HARNESS),
                    "run",
                    "python",
                    "scripts/judge-aggregate.py",
                    str(run_dir),
                ]
                + [a for actor in headline for a in ("--actor", actor)],
                check=True,
                capture_output=True,
                text=True,
            )
    return headline


def judge_match(a: dict, b: dict) -> bool:
    def key(summary: dict) -> tuple:
        cards = [c for c in summary.get("cards", []) if c.get("actor_id") in summary.get("canonical", [])]
        return (
            summary.get("aggregation") or "",
            len(cards),
            tuple(
                sorted(
                    (
                        str(c.get("model")),
                        str(c.get("reasoning_effort")),
                        str(c.get("brief_sha256")),
                        bool(c.get("blinded")),
                        int(c.get("sessions") or 1),
                    )
                    for c in cards
                )
            ),
        )

    return bool(a.get("recorded")) and bool(b.get("recorded")) and key(a) == key(b)


def judging(run_dir: Path) -> dict:
    out = subprocess.run(
        [
            "uv",
            "--directory",
            str(HARNESS),
            "run",
            "python",
            "-c",
            "import json, sys\nfrom harness.validate.judging import judge_summary\n"
            "print(json.dumps(judge_summary(sys.argv[1])))",
            str(run_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(out)


def arm_means(run_dir: Path) -> dict[str, dict]:
    judged = [json.loads(l) for l in (run_dir / "judge.jsonl").read_text().splitlines() if l.strip()]
    out = {}
    for arm in sorted({r["backend_id"] for r in judged}):
        rs = [r for r in judged if r["backend_id"] == arm]
        mean = lambda k: round(sum(r[k] for r in rs) / len(rs), 2)
        out[arm] = {
            "cells": len(rs),
            "accuracy": mean("accuracy"),
            "completeness": mean("completeness"),
            "relevance": mean("relevance"),
            "harm": sum(r["harm"] for r in rs),
        }
    return out


def arm_table(run_dir: Path) -> list[str]:
    lines = [
        "| Arm | Cells | Accuracy | Completeness | Relevance | Harm |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm, m in arm_means(run_dir).items():
        lines.append(
            f"| {arm} | {m['cells']} | {m['accuracy']} | {m['completeness']} | "
            f"{m['relevance']} | {m['harm']} |"
        )
    return lines


def baseline_note(run_dir: Path, base: Path) -> str:
    mine, theirs = judging(run_dir), judging(base)
    if judge_match(mine, theirs):
        return "Like for like: the baseline was judged the same way."
    return (
        f"Not like for like: the baseline reads \"{theirs['sentence']}\" while this run reads "
        f"\"{mine['sentence']}\"."
    )


def run_full(args) -> int:
    """Run a comparison set matrix, judge it, and emit v2 JSON report packets."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = work_dir() / f"full-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    explicit_data_root = getattr(args, "data_root", None)
    source = _resolve_data_root(getattr(args, "data_root", None) or DATA)
    data_root = source
    if getattr(args, "profiles", None):
        wanted = [p.strip() for p in args.profiles.split(",") if p.strip()]
        offered = advertised_profiles()
        missing = [p for p in wanted if p not in offered]
        if missing:
            raise SystemExit(
                f"not advertised by the Hub now: {', '.join(missing)} "
                f"(advertised: {', '.join(sorted(offered))})"
            )
        data_root = out_dir / "data"
        shutil.copytree(source, data_root)
        backends = json.loads((data_root / "backends.json").read_text())
        cset_path = data_root / "comparison_sets" / f"{args.set}.json"
        cset = json.loads(cset_path.read_text())
        for arm, backend in profile_arms(offered, wanted).items():
            backends[arm] = backend
            cset["backend_ids"].append(arm)
        (data_root / "backends.json").write_text(json.dumps(backends, indent=1))
        cset_path.write_text(json.dumps(cset, indent=1))
    with run_environment(data_root, args.set, out_dir / "settings-as-found.json") as env:
        run_dir = run_set(
            "validate-run",
            args.set,
            out_dir / "run.log",
            env,
            data_root if (explicit_data_root is not None or data_root != DATA) else None,
            getattr(args, "resume", None),
        )
    subprocess.run(
        ["make", "-C", str(HARNESS), "validate-judge-prep", f"RUN={run_dir}"]
        + (["BLIND=1"] if getattr(args, "blind", False) else []),
        check=True,
        capture_output=True,
    )
    judge_passes(args, run_dir, out_dir)
    report = harness("validate", "report", "--run-dir", str(run_dir))
    lines = [
        f"# Evaluation {args.set} ({stamp})",
        "",
        f"Run: {run_dir}",
        f"Report packet: {report.stdout.strip()}",
        f"Local preview: python3 scripts/preview-report.py {run_dir}",
        f"Stage report:  python3 scripts/publish-report.py stage {run_dir} --slug <slug>",
        "",
        judging(run_dir)["sentence"],
        "",
    ] + arm_table(run_dir)
    if getattr(args, "baseline", None):
        base = HARNESS / "artifacts/validate" / args.baseline
        lines += [
            "",
            f"Compared with run {args.baseline}: {base}",
            baseline_note(run_dir, base),
        ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def rejudge(args) -> int:
    adding = bool(getattr(args, "add_judges", None))
    run_dir = Path(args.add_judges if adding else args.rejudge).resolve()
    keep, _, blinded = run_judges(run_dir) if adding else ([], {}, False)
    if adding and not keep:
        raise SystemExit(f"{run_dir} has no judged headline to add to; use --rejudge")
    args.blind = bool(args.blind) or blinded
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = work_dir() / f"{'add-judges' if adding else 'rejudge'}-{stamp}"
    out_dir.mkdir(parents=True)
    subprocess.run(
        ["make", "-C", str(HARNESS), "validate-judge-prep", f"RUN={run_dir}"]
        + (["BLIND=1"] if args.blind else []),
        check=True,
        capture_output=True,
    )
    actors = judge_passes(args, run_dir, out_dir, keep)
    report = harness("validate", "report", "--run-dir", str(run_dir))
    title = "Added judges to" if adding else "Re-judged"
    lines = [
        f"# {title} {run_dir.name} ({stamp})",
        "",
        f"Headline passes: {', '.join(actors)}",
        f"Report packet: {report.stdout.strip()}",
        "",
        judging(run_dir)["sentence"],
        "",
    ] + arm_table(run_dir)
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Run clinical AI evaluation sets and multi-judge sessions.")
    ap.add_argument("--full", action="store_true", help="Run full evaluation matrix and judge passes")
    ap.add_argument("--set", default="full-default", help="Comparison set ID")
    ap.add_argument("--data-root", type=Path, help="Optional custom validation dataset root")
    ap.add_argument("--profiles", help="Comma-separated extra Hub profiles to evaluate")
    ap.add_argument("--baseline", help="Earlier run ID for baseline comparison")
    ap.add_argument("--agent", default="claude", choices=("claude", "codex", "gemini", "human"))
    ap.add_argument("--judge-passes", type=int, default=1)
    ap.add_argument("--judge", dest="judges", action="append", metavar="AGENT:MODEL:EFFORT[:PASSES]")
    ap.add_argument("--blind", action="store_true", help="Blind and isolate scenario bundles per session")
    ap.add_argument("--rejudge", metavar="RUN_DIR", help="Re-judge an existing run directory")
    ap.add_argument("--add-judges", metavar="RUN_DIR", help="Add judge passes to an existing run directory")
    ap.add_argument("--resume", metavar="RUN_DIR", help="Resume an interrupted or expanded run")
    args = ap.parse_args()
    if args.rejudge or args.add_judges:
        return rejudge(args)
    if args.full:
        return run_full(args)
    ap.error("Specify --full, --rejudge <run_dir>, or --add-judges <run_dir>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
