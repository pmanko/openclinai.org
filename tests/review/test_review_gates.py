"""Gate files: committed before the run, complete, and decided by direction and threshold."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("review_driver", ROOT / "review/bin/review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

GATE = """# Kidney cell

set: context-cohort
gold: gold/context-cohort-2026-10.json
metric: meanF1
direction: higher
baseline_run: abc
baseline: 0.70
threshold: 0.68
date: 2026-10-21
signed_off: owner
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def umbrella(tmp_path, monkeypatch):
    (tmp_path / "review" / "gates").mkdir(parents=True)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "o@example.test")
    git(tmp_path, "config", "user.name", "O")
    monkeypatch.setattr(review, "UMBRELLA", tmp_path)
    return tmp_path


def test_a_gate_must_be_committed_unchanged_and_complete(umbrella):
    gate = umbrella / "review" / "gates" / "kidney.md"
    gate.write_text(GATE)
    with pytest.raises(SystemExit, match="must be committed"):
        review.read_gate("kidney")
    git(umbrella, "add", ".")
    git(umbrella, "commit", "-q", "-m", "gate")
    assert review.read_gate("kidney")["threshold"] == "0.68"
    gate.write_text(GATE.replace("0.68", "0.60"))
    with pytest.raises(SystemExit, match="must be committed"):
        review.read_gate("kidney")
    gate.write_text(GATE.replace("signed_off: owner\n", ""))
    git(umbrella, "commit", "-q", "-am", "unsigned")
    with pytest.raises(SystemExit, match="lacks signed_off"):
        review.read_gate("kidney")


def test_the_head_number_decides_by_direction():
    higher = {"threshold": "0.68", "direction": "higher"}
    lower = {"threshold": "2", "direction": "lower"}
    assert review.gate_passes(higher, 0.70) and not review.gate_passes(higher, 0.60)
    assert review.gate_passes(lower, 1) and not review.gate_passes(lower, 3)
    assert not review.gate_passes(higher, None)
