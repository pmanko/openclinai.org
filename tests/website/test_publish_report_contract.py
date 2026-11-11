"""Publication consumes v2 pure-JSON packets across all families without harness imports."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PUBLISH_SCRIPT = ROOT / "scripts" / "publish-report.py"


def _load_publish():
    spec = importlib.util.spec_from_file_location("publish_report_contract", PUBLISH_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_v2_packet(
    directory: Path,
    *,
    family: str = "chartsearchai",
    slug: str = "2026-11-10-sample-study",
    title: str = "How accurately does Med Agent Hub read HIV charts on a shared GPU?",
    summary: str = "We tested two clinical AI setups across three HIV patient charts and 35 clinical questions.",
    takeaway: str = "Med Agent Hub improved accuracy and completeness by 14 points with zero unsafe answers.",
    scoreline: str = "",
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "editorial.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.editorial.v2",
                "schema_version": 2,
                "slug": slug,
                "title": title,
                "summary": summary,
                "takeaway": takeaway,
                "family": family,
                "featured": True,
                "date": "10 Nov 2026",
            }
        ),
        encoding="utf-8",
    )
    (directory / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": slug,
                "report_family": family,
                "date": "10 Nov 2026",
                "cells": 2,
                "patients": "Fixture Patient",
                "scoreline": scoreline,
                "scout": (
                    []
                    if family == "catalyst"
                    else [
                        {
                            "backend": "frozen-model · 12B",
                            "n": 2,
                            "benchmark_score": 73.0,
                            "harm_count": 1,
                        }
                    ]
                ),
            }
        ),
        encoding="utf-8",
    )
    (directory / "report-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.report.v2",
                "schema_version": 2,
                "runs": [
                    {
                        "id": slug,
                        "backends": ["frozen-model · 12B"],
                        "arm_cards": {
                            "frozen-model · 12B": {
                                "title": "Frozen Model 12B",
                                "short_title": "Frozen Model 12B",
                            }
                        },
                        "source_card_pool": {},
                        "refs_pool": {},
                        "scenarios": [
                            {
                                "scenario_id": "s1",
                                "turns": [
                                    {
                                        "turn": 1,
                                        "question": "What is the latest lab?",
                                        "cells": {
                                            "frozen-model · 12B": {
                                                "status": "complete",
                                                "answer_md": "Latest lab is normal.",
                                            }
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (directory / "dashboard-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.dashboard.v2",
                "schema_version": 2,
                "status": {"run": slug, "arms": [], "scenarios": []},
                "record_pool": {},
                "sources_pool": {},
                "refs_pool": {},
                "details": {},
            }
        ),
        encoding="utf-8",
    )
    return directory


def test_stage_stages_v2_packets_across_families_and_compiles_catalog(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    assets = reports / "assets"
    assets.mkdir(parents=True)
    for asset_name in ("report-shell.css", "report-shell.js", "dashboard-shell.css", "dashboard-shell.js"):
        (assets / asset_name).write_text("/* asset */\n", encoding="utf-8")
    (reports / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")

    chart_pkt = _make_v2_packet(
        tmp_path / "chart-pkt",
        family="chartsearchai",
        slug="2026-11-10-chart-study",
        title="How accurately does Med Agent Hub read HIV charts on a shared GPU?",
    )
    cat_pkt = _make_v2_packet(
        tmp_path / "cat-pkt",
        family="catalyst",
        slug="2026-11-10-catalyst-study",
        title="Can an AI-drafted SQL conversation survive real clinical refinement?",
        scoreline="Gold checks: 1/1 passed · Advisory judge median: 90/100",
    )

    for pkt, slug in ((chart_pkt, "2026-11-10-chart-study"), (cat_pkt, "2026-11-10-catalyst-study")):
        res = subprocess.run(
            [
                sys.executable,
                str(PUBLISH_SCRIPT),
                "stage",
                str(pkt),
                "--slug",
                slug,
                "--reports-root",
                str(reports),
                "--root",
                str(ROOT),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        staged_files = {p.name for p in (reports / slug).iterdir() if p.is_file()}
        assert staged_files == {
            "editorial.json",
            "run-summary.json",
            "report-data.json",
            "dashboard-data.json",
            "index.html",
            "dashboard.html",
        }

    html = (reports / "index.html").read_text(encoding="utf-8")
    assert "ChartSearchAI" in html and "Catalyst SQL" in html
    assert "Gold checks: 1/1 passed" in html
    assert "Advisory judge median: 90/100" in html
    assert "frozen-model · 12B" in html


def test_stage_rejects_v1_html_in_json_and_forbidden_copy(tmp_path: Path) -> None:
    mod = _load_publish()
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")
    pkt = _make_v2_packet(tmp_path / "bad-pkt", slug="2026-11-10-bad-study")

    # Inject forbidden HTML key into cell
    rep = json.loads((pkt / "report-data.json").read_text(encoding="utf-8"))
    rep["runs"][0]["scenarios"][0]["turns"][0]["cells"]["frozen-model · 12B"]["answer_html"] = "<p>html</p>"
    (pkt / "report-data.json").write_text(json.dumps(rep), encoding="utf-8")

    with pytest.raises(ValueError, match="forbidden HTML keys"):
        mod.stage_report(run_dir=pkt, slug="2026-11-10-bad-study", reports_root=reports, root=tmp_path)

    # Restore valid v2 JSON, test forbidden title pattern
    pkt2 = _make_v2_packet(
        tmp_path / "bad-title",
        slug="2026-11-10-bad-title",
        title="Full evaluation full-default, 2026-11-10 (38e68e2a)",
    )
    with pytest.raises(ValueError, match="title rejected"):
        mod.stage_report(run_dir=pkt2, slug="2026-11-10-bad-title", reports_root=reports, root=tmp_path)
