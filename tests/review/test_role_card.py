"""role.sh records the session beside every answer: the card a judge pass is named by."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROLE = ROOT / "review" / "bin" / "role.sh"


def test_role_writes_a_session_card_beside_the_answer(tmp_path):
    prompt = tmp_path / "judge.prompt.md"
    prompt.write_text("Score the cells.\n")
    out = tmp_path / "judge.md"
    out.write_text("[]\n")  # the human agent's answer already exists, so the role completes

    rc = subprocess.run([str(ROLE), "human", "judge", str(tmp_path), str(prompt), str(out)],
                        capture_output=True, text=True).returncode

    assert rc == 0
    card = json.loads((tmp_path / "judge.md.card.json").read_text())
    assert card["agent"] == "human"
    assert card["role"] == "judge"
    assert card["model"] == "human"
    assert card["sampling"] == "provider default"
    assert card["started_at"] <= card["finished_at"]


def test_a_human_role_without_an_answer_asks_for_one_and_writes_no_card(tmp_path):
    prompt = tmp_path / "reviewer.prompt.md"
    prompt.write_text("Review.\n")
    out = tmp_path / "reviewer.md"

    proc = subprocess.run([str(ROLE), "human", "reviewer", str(tmp_path), str(prompt), str(out)],
                          capture_output=True, text=True)

    assert proc.returncode == 3
    assert "write your answer to" in proc.stdout
    assert not (tmp_path / "reviewer.md.card.json").exists()


def test_the_judge_card_adds_the_brief_hash_and_the_pass_to_the_session(tmp_path):
    import hashlib
    import importlib.util
    spec = importlib.util.spec_from_file_location("review_driver", ROOT / "review" / "bin" / "review.py")
    assert spec and spec.loader
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    answer = tmp_path / "judge-p2.md"
    answer.write_text("[]\n")
    (tmp_path / "judge-p2.md.card.json").write_text(json.dumps(
        {"agent": "codex", "agent_version": "0.160.1", "model": "gpt-6-astra",
         "reasoning_effort": "high", "sampling": "provider default", "role": "judge",
         "started_at": "2026-10-27T01:00:00Z", "finished_at": "2026-10-27T01:06:00Z"}))

    card = json.loads(review.judge_card(answer, pass_index=2, passes=3).read_text())

    brief = ROOT / "review" / "briefs" / "judge.md"
    assert card["brief_sha256"] == hashlib.sha256(brief.read_bytes()).hexdigest()
    assert card["brief_path"] == "review/briefs/judge.md"
    assert (card["pass_index"], card["passes"]) == (2, 3)
    assert card["model"] == "gpt-6-astra" and card["agent_version"] == "0.160.1"
