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
