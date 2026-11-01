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


def test_judge_match_compares_the_canonical_cards_not_the_actor_names():
    import importlib.util
    spec = importlib.util.spec_from_file_location("review_driver2", ROOT / "review" / "bin" / "review.py")
    assert spec and spec.loader
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)

    def summary(model, effort="high", brief="b1", actor="p1", aggregation="single-pass"):
        return {"recorded": True, "aggregation": aggregation, "canonical": [actor],
                "cards": [{"actor_id": actor, "model": model, "reasoning_effort": effort, "brief_sha256": brief}]}

    assert review.judge_match(summary("gpt-6-astra"), summary("gpt-6-astra", actor="other"))
    assert not review.judge_match(summary("gpt-6-astra"), summary("claude-opus-5-5"))
    assert not review.judge_match(summary("gpt-6-astra"), summary("gpt-6-astra", effort="medium"))
    assert not review.judge_match(summary("gpt-6-astra"), summary("gpt-6-astra", brief="b2"))
    assert not review.judge_match(summary("gpt-6-astra"), {"recorded": False, "cards": [], "canonical": []})
    blinded = summary("gpt-6-astra")
    blinded["cards"][0]["blinded"] = True
    unblinded = summary("gpt-6-astra")
    unblinded["cards"][0]["blinded"] = False
    assert not review.judge_match(blinded, unblinded)


def test_role_invokes_stub_claude_codex_and_gemini_with_matching_session_cards(tmp_path):
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for cli, version_out in (("claude", "claude-code 2.0"), ("codex", "codex-cli 0.160.1"), ("gemini", "gemini-cli 1.0")):
        stub = bin_dir / cli
        stub.write_text(
            "#!/usr/bin/env bash\n"
            f'if [ "${{1:-}}" = "--version" ]; then echo "{version_out}"; exit 0; fi\n'
            f'printf "%s\\n" "$@" > "{tmp_path}/{cli}.args"\n'
            "out_Next=0\n"
            'for arg in "$@"; do\n'
            '  if [ "$out_Next" = 1 ]; then echo "[]" > "$arg"; out_Next=0; fi\n'
            '  if [ "$arg" = "-o" ]; then out_Next=1; fi\n'
            "done\n"
            'echo "[]"\n'
        )
        stub.chmod(0o755)

    prompt = tmp_path / "judge.prompt.md"
    prompt.write_text("Score.\n")
    base_env = {k: v for k, v in os.environ.items() if k not in ("REVIEW_MODEL", "REVIEW_REASONING")}
    base_env["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"

    # 1. Claude explicit model & effort
    c_out = tmp_path / "claude.md"
    rc = subprocess.run([str(ROLE), "claude", "judge", str(tmp_path), str(prompt), str(c_out)],
                        env={**base_env, "REVIEW_MODEL": "claude-opus-5-5", "REVIEW_REASONING": "high"},
                        capture_output=True, text=True).returncode
    assert rc == 0
    c_args = (tmp_path / "claude.args").read_text().splitlines()
    c_card = json.loads((tmp_path / "claude.md.card.json").read_text())
    assert "--model" in c_args and c_args[c_args.index("--model") + 1] == c_card["model"] == "claude-opus-5-5"
    assert "--effort" in c_args and c_args[c_args.index("--effort") + 1] == c_card["reasoning_effort"] == "high"

    # 2. Codex default model & effort
    x_out = tmp_path / "codex.md"
    rc = subprocess.run([str(ROLE), "codex", "judge", str(tmp_path), str(prompt), str(x_out)],
                        env=base_env, capture_output=True, text=True).returncode
    assert rc == 0
    x_args = (tmp_path / "codex.args").read_text().splitlines()
    x_card = json.loads((tmp_path / "codex.md.card.json").read_text())
    assert "-m" in x_args and x_args[x_args.index("-m") + 1] == x_card["model"] == "gpt-6.1-sol"
    assert f'model_reasoning_effort="{x_card["reasoning_effort"]}"' in x_args
    assert x_card["reasoning_effort"] == "medium"

    # 3. Gemini default records unrecorded rather than Codex defaults
    g_out = tmp_path / "gemini.md"
    rc = subprocess.run([str(ROLE), "gemini", "judge", str(tmp_path), str(prompt), str(g_out)],
                        env=base_env, capture_output=True, text=True).returncode
    assert rc == 0
    g_card = json.loads((tmp_path / "gemini.md.card.json").read_text())
    assert g_card["agent"] == "gemini"
    assert g_card["model"] == "unrecorded"
    assert g_card["reasoning_effort"] == "unrecorded"


def test_parse_judges_resolves_defaults_and_rejects_nonpositive_passes(monkeypatch):
    import importlib.util
    from types import SimpleNamespace
    import pytest

    spec = importlib.util.spec_from_file_location("review_driver3", ROOT / "review" / "bin" / "review.py")
    assert spec and spec.loader
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)

    monkeypatch.delenv("REVIEW_MODEL", raising=False)
    monkeypatch.delenv("REVIEW_REASONING", raising=False)
    parsed = review.parse_judges(SimpleNamespace(agent="codex", judge_passes=1, judges=[]))
    assert parsed == [{"agent": "codex", "model": "gpt-6.1-sol", "effort": "medium", "passes": 1}]

    for invalid in (0, -2):
        with pytest.raises(SystemExit):
            review.parse_judges(SimpleNamespace(agent="codex", judge_passes=invalid, judges=[]))

    repaired = review.last_json('```json\n[{"note": "literal, } value",}]\n```')
    assert repaired == [{"note": "literal, } value"}]


def test_judge_sessions_validates_cell_coverage_and_isolates_blinded_inputs(tmp_path, monkeypatch):
    import importlib.util
    from types import SimpleNamespace
    import pytest

    spec = importlib.util.spec_from_file_location("review_driver4", ROOT / "review" / "bin" / "review.py")
    assert spec and spec.loader
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)

    monkeypatch.setenv("JUDGE_ATTEMPTS", "2")
    monkeypatch.setenv("JUDGE_RETRY_DELAY", "0")

    run_dir = tmp_path / "run"
    (run_dir / "judge-bundles").mkdir(parents=True)
    (run_dir / "charts").mkdir(parents=True)
    (run_dir / "charts" / "p1.snapshot.txt").write_text("Chart text\n")
    (run_dir / "judge-blind-map.json").write_text('{"secret": true}\n')
    (run_dir / "judge-bundles" / "s1.jsonl").write_text(
        json.dumps({"scenario_id": "s1", "backend_id": "A"}) + "\n"
    )

    seen_workdirs = []
    calls = {"n": 0}

    def fake_run_role(args, role, workdir, prompt, out, agent=None, env=None):
        calls["n"] += 1
        seen_workdirs.append(workdir)
        out.with_suffix(".md.card.json").write_text(
            json.dumps({"agent": "codex", "agent_version": "0.160.1", "model": "gpt-6.1-sol",
                        "reasoning_effort": "medium", "sampling": "provider default",
                        "started_at": "2026-10-27T01:00:00Z", "finished_at": "2026-10-27T01:01:00Z"})
        )
        if calls["n"] == 1:
            return "```json\n[]\n```"
        row = {"scenario_id": "s1", "backend_id": "A", "accuracy": 9, "completeness": 9,
               "relevance": 9, "harm": False}
        return f"```json\n{json.dumps([row])}\n```"

    review.run_role = fake_run_role
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    rows_path, card_path = review.judge_sessions(
        SimpleNamespace(agent="codex"), run_dir, out_dir, 1, 1,
        {"agent": "codex", "model": "gpt-6.1-sol", "effort": "medium"}, blind=True
    )
    assert calls["n"] == 2
    assert len(json.loads(rows_path.read_text())) == 1
    assert seen_workdirs[-1] != run_dir
    assert not (seen_workdirs[-1] / "judge-blind-map.json").exists()
    assert (seen_workdirs[-1] / "charts" / "p1.snapshot.txt").is_file()
    card = json.loads(card_path.read_text())
    assert card["sessions"] == 1 and len(card["session_cards"]) == 1

