from __future__ import annotations

import importlib.util
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_script(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name,
        REPOSITORY_ROOT / "scripts" / filename,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reader_v2_run(root: Path) -> Path:
    run_dir = root / "artifacts" / "catalyst-notebook-validation" / "reader-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        run_dir / "run-summary.json",
        {
            "schema": "openclinai.summary.v2",
            "schema_version": 2,
            "slug": "catalyst-phase1",
            "report_family": "catalyst",
            "suite_id": "reader-suite-v1",
            "suite_sha256": "a" * 64,
            "date": "26 Aug 2026",
            "cells": 1,
            "patients": "",
            "scoreline": "1 model teams · 1 conversations · full-evidence reader review",
            "scout": [],
        },
    )
    _write_json(
        run_dir / "report-data.json",
        {
            "schema": "openclinai.report.v2",
            "schema_version": 2,
            "runs": [
                {
                    "id": "catalyst-phase1",
                    "backends": ["team-a"],
                    "arm_cards": {"team-a": {"title": "Team A", "short_title": "Team A"}},
                    "source_card_pool": {},
                    "refs_pool": {},
                    "scenarios": [
                        {
                            "scenario_id": "A1",
                            "turns": [
                                {
                                    "turn": 1,
                                    "question": "List the patient measurements.",
                                    "cells": {
                                        "team-a": {
                                            "status": "complete",
                                            "answer_md": "Here are the recorded measurements.",
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        run_dir / "dashboard-data.json",
        {
            "schema": "openclinai.dashboard.v2",
            "schema_version": 2,
            "status": {"run": "catalyst-phase1", "arms": [{"id": "team-a", "label": "Team A"}], "scenarios": []},
            "record_pool": {},
            "sources_pool": {},
            "refs_pool": {},
            "details": {},
        },
    )
    return run_dir


def _stage_reader_run(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    run_dir = _reader_v2_run(root)
    reports_root = root / "artifacts" / "reports"
    destination = reports_root / "catalyst-phase1"
    destination.mkdir(parents=True)
    for stale_name in (
        "comparison.html",
        "judge.jsonl",
        "score.json",
        "obsolete-evidence.json",
    ):
        (destination / stale_name).write_text("stale publication content\n")
    stale_nested = destination / "old-assets"
    stale_nested.mkdir()
    (stale_nested / "unused.txt").write_text("stale\n")

    manifest = reports_root / "reports-index.json"
    _write_json(
        manifest,
        {
            "intro": "Explore recorded clinical AI conversations.",
            "scoring_note": "",
            "runs": [],
        },
    )
    publish_module = _load_script("publish_report_reader_test", "publish-report.py")

    published = publish_module.stage_report(
        run_dir=run_dir,
        slug="catalyst-phase1",
        family="catalyst",
        reports_root=reports_root,
        manifest_path=manifest,
        root=root,
        title="Catalyst Phase 1 model-team evidence review",
        summary="A full-context comparison of the recorded SQL generation conversations across clinical cohorts.",
        takeaway="Read the SQL execution evidence and the attached human review together before selecting a team.",
    )
    assert published == destination / "index.html"
    return reports_root, manifest


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.hidden_depth == 0:
            self.parts.append(data)


def _visible_text(html: str) -> str:
    parser = _VisibleText()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def test_reader_publication_cleanly_replaces_an_existing_catalyst_slug(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reports_root, _ = _stage_reader_run(tmp_path, monkeypatch)
    destination = reports_root / "catalyst-phase1"

    assert (destination / "index.html").is_file()
    assert (destination / "dashboard.html").is_file()
    assert (destination / "editorial.json").is_file()
    assert (destination / "run-summary.json").is_file()
    assert (destination / "report-data.json").is_file()
    assert (destination / "dashboard-data.json").is_file()
    for stale_name in (
        "comparison.html",
        "judge.jsonl",
        "score.json",
        "obsolete-evidence.json",
        "old-assets",
    ):
        assert not (destination / stale_name).exists()

    summary = json.loads((destination / "run-summary.json").read_text(encoding="utf-8"))
    assert summary["report_family"] == "catalyst"
    assert summary["suite_id"] == "reader-suite-v1"
    assert re.fullmatch(r"[a-f0-9]{64}", summary["suite_sha256"])


def test_reader_led_reports_index_uses_neutral_visible_language(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reports_root, manifest = _stage_reader_run(tmp_path, monkeypatch)
    index_module = _load_script("reports_index_reader_test", "build-reports-index.py")

    index_module.main(
        [
            "--root",
            str(tmp_path),
            "--reports-root",
            str(reports_root),
        ]
    )

    index_html = (reports_root / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(index_html)
    assert "1 model teams · 1 conversations · full-evidence reader review" in visible
    assert "Compare the teams" not in visible
    assert not re.search(
        r"\b(?:pass|passed|verdict|qualified)\b",
        visible,
        flags=re.IGNORECASE,
    )
