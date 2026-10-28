"""A blinded judge pass is one session per scenario bundle; the pass's rows and card are merged."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def _review():
    spec = importlib.util.spec_from_file_location("review_driver3", ROOT / "review" / "bin" / "review.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_blinded_pass_runs_one_session_per_bundle_and_merges_rows_and_card(tmp_path):
    review = _review()
    run = tmp_path / "run"
    (run / "judge-bundles").mkdir(parents=True)
    for s in ("s1", "s2"):
        (run / "judge-bundles" / f"{s}.jsonl").write_text(json.dumps({"scenario_id": s, "backend_id": "A"}) + "\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    for s in ("s1", "s2"):  # the human agent's answers already exist, one per bundle
        (out_dir / f"judge-{s}.md").write_text(
            "Scored.\n```json\n" + json.dumps([{"scenario_id": s, "backend_id": "A", "accuracy": 8}]) + "\n```\n")
    args = SimpleNamespace(agent="human", judge_passes=1, judges=[], blind=True)

    rows_path, card_path = review.judge_sessions(args, run, out_dir, 1, 1,
                                                 {"agent": "human", "model": "", "effort": ""}, True)

    rows = json.loads(rows_path.read_text())
    assert [r["scenario_id"] for r in rows] == ["s1", "s2"]
    card = json.loads(card_path.read_text())
    assert card["sessions"] == 2 and card["blinded"] is True
    assert card["agent"] == "human" and (card["pass_index"], card["passes"]) == (1, 1)
    assert len(card["brief_sha256"]) == 64
    assert (out_dir / "judge-s1.md.card.json").exists() and (out_dir / "judge-s2.md.card.json").exists()
    assert "Cells for this session" in (out_dir / "judge-s1.prompt.md").read_text()


def test_parse_judges_reads_agent_model_effort_or_falls_back_to_the_run(monkeypatch):
    review = _review()
    args = SimpleNamespace(agent="codex", judge_passes=3,
                           judges=["codex:gpt-6-astra:high", "claude:claude-opus-5-5:high:1"])
    assert review.parse_judges(args) == [
        {"agent": "codex", "model": "gpt-6-astra", "effort": "high", "passes": 3},
        {"agent": "claude", "model": "claude-opus-5-5", "effort": "high", "passes": 1}]
    monkeypatch.setenv("REVIEW_MODEL", "m")
    monkeypatch.setenv("REVIEW_REASONING", "low")
    assert review.parse_judges(SimpleNamespace(agent="codex", judges=[])) == [
        {"agent": "codex", "model": "m", "effort": "low", "passes": 1}]
    for bad in ("codex:gpt-6-astra", "codex:gpt-6-astra:high:two", "codex:gpt-6-astra:high:0"):
        try:
            review.parse_judges(SimpleNamespace(agent="codex", judges=[bad]))
        except SystemExit:
            continue
        raise AssertionError(f"{bad} was accepted")


def _judged_run(tmp_path, passes):
    """A run whose headline was aggregated from gpt-6-astra passes p1..pN."""
    run = tmp_path / "run"
    built = []
    for i in range(1, passes + 1):
        actor = f"codex-gpt-6-astra-high-p{i}"
        (run / "judges" / actor).mkdir(parents=True)
        (run / "judges" / actor / "manifest.json").write_text(json.dumps(
            {"agent": "codex", "model": "gpt-6-astra", "reasoning_effort": "high",
             "pass_index": i, "passes": passes, "blinded": True}))
        built.append(actor)
    (run / "judges" / "canonical.json").write_text(json.dumps({"built_from": built}))
    return run


def _stub_harness(review, monkeypatch, run, calls):
    """Finalize writes the pass's card where the harness would; every make and uv call is kept."""
    def sessions(args, run_dir, out_dir, pass_index, passes, judge, blind, tag="judge"):
        calls.append(("session", judge["model"], pass_index, passes, blind))
        return out_dir / f"{tag}.rows.json", out_dir / f"{tag}.card.json"

    def run_cmd(cmd, **kwargs):
        calls.append(("cmd", cmd))
        if "validate-judge-finalize" in cmd:
            model, index = calls[-2][1], calls[-2][2]
            actor = f"{'claude' if 'claude' in model else 'codex'}-{model}-high-p{index}"
            (run / "judges" / actor).mkdir(parents=True, exist_ok=True)
            (run / "judges" / actor / "manifest.json").write_text(json.dumps(
                {"agent": actor.split("-")[0], "model": model, "reasoning_effort": "high",
                 "pass_index": index}))
            return SimpleNamespace(stdout=f"stored {run}/judges/{actor}/judge.jsonl\n", returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(review, "judge_sessions", sessions)
    monkeypatch.setattr(review.subprocess, "run", run_cmd)


def test_adding_a_judge_keeps_the_earlier_passes_in_the_headline(tmp_path, monkeypatch):
    review = _review()
    run = _judged_run(tmp_path, 3)
    calls = []
    _stub_harness(review, monkeypatch, run, calls)
    keep, _, blinded = review.run_judges(run)
    assert blinded is True
    args = SimpleNamespace(agent="codex", judge_passes=1, blind=blinded,
                           judges=["claude:claude-opus-5-5:high:1"])

    headline = review.judge_passes(args, run, tmp_path, keep)

    assert headline == [f"codex-gpt-6-astra-high-p{i}" for i in (1, 2, 3)] + ["claude-claude-opus-5-5-high-p1"]
    assert ("session", "claude-opus-5-5", 1, 1, True) in calls
    finalize = [c[1] for c in calls if c[0] == "cmd" and "validate-judge-finalize" in c[1]]
    assert len(finalize) == 1 and "JUDGE_PROMOTE=1" not in finalize[0]
    aggregate = [c[1] for c in calls if c[0] == "cmd" and "scripts/judge-aggregate.py" in c[1]]
    assert len(aggregate) == 1 and aggregate[0].count("--actor") == 4


def test_more_passes_of_a_judge_continue_its_numbering(tmp_path, monkeypatch):
    review = _review()
    run = _judged_run(tmp_path, 3)
    calls = []
    _stub_harness(review, monkeypatch, run, calls)
    args = SimpleNamespace(agent="codex", judge_passes=1, blind=True, judges=["codex:gpt-6-astra:high:2"])

    headline = review.judge_passes(args, run, tmp_path, review.run_judges(run)[0])

    assert [c[2:4] for c in calls if c[0] == "session"] == [(4, 5), (5, 5)]
    assert headline[-2:] == ["codex-gpt-6-astra-high-p4", "codex-gpt-6-astra-high-p5"]


def test_one_new_pass_on_an_unjudged_run_is_promoted(tmp_path, monkeypatch):
    review = _review()
    run = tmp_path / "run"
    (run / "judges").mkdir(parents=True)
    calls = []
    _stub_harness(review, monkeypatch, run, calls)
    args = SimpleNamespace(agent="claude", judge_passes=1, blind=False, judges=["claude:claude-opus-5-5:high"])

    assert review.judge_passes(args, run, tmp_path) == ["claude-claude-opus-5-5-high-p1"]
    finalize = [c[1] for c in calls if c[0] == "cmd" and "validate-judge-finalize" in c[1]]
    assert "JUDGE_PROMOTE=1" in finalize[0]
    assert not [c for c in calls if c[0] == "cmd" and "scripts/judge-aggregate.py" in c[1]]


def test_last_json_forgives_a_trailing_comma_in_the_verdict_block():
    review = _review()
    answer = "Scored.\n```json\n[{\"scenario_id\": \"s1\", \"accuracy\": 8,}, ]\n```\n"

    assert review.last_json(answer) == [{"scenario_id": "s1", "accuracy": 8}]
