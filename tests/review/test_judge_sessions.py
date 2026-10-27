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
    args = SimpleNamespace(agent="codex", judges=["codex:gpt-6-astra:high", "claude:claude-opus-5-5:high"])
    assert review.parse_judges(args) == [
        {"agent": "codex", "model": "gpt-6-astra", "effort": "high"},
        {"agent": "claude", "model": "claude-opus-5-5", "effort": "high"}]
    monkeypatch.setenv("REVIEW_MODEL", "m")
    monkeypatch.setenv("REVIEW_REASONING", "low")
    assert review.parse_judges(SimpleNamespace(agent="codex", judges=[])) == [
        {"agent": "codex", "model": "m", "effort": "low"}]
