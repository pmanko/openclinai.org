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
    date: str = "2026-11-10",
    judged: bool = True,
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
                "date": date,
            }
        ),
        encoding="utf-8",
    )
    scout_rows = (
        []
        if family == "catalyst" or not judged
        else [
            {
                "backend": "frozen-model · 12B",
                "n": 2,
                "benchmark_score": 73.0,
                "harm_count": 1,
            }
        ]
    )
    (directory / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": slug,
                "report_family": family,
                "date": date,
                "cells": 2,
                "patients": "Fixture Patient",
                "scoreline": scoreline,
                "scout": scout_rows,
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
                        "judge": scout_rows,
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


def test_stage_rejects_unknown_keys_via_closed_positive_v2_schema_and_forbidden_copy(tmp_path: Path) -> None:
    mod = _load_publish()
    assert not hasattr(mod, "FORBIDDEN_HTML_KEYS"), "legacy negative HTML denylist must not exist"
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")
    pkt = _make_v2_packet(tmp_path / "bad-pkt", slug="2026-11-10-bad-study")

    # Closed positive keyset rejects any unknown key (including legacy HTML or statistical_benchmark)
    rep = json.loads((pkt / "report-data.json").read_text(encoding="utf-8"))
    rep["runs"][0]["scenarios"][0]["turns"][0]["cells"]["frozen-model · 12B"]["answer_html"] = "<p>html</p>"
    (pkt / "report-data.json").write_text(json.dumps(rep), encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected key"):
        mod.stage_report(run_dir=pkt, slug="2026-11-10-bad-study", reports_root=reports, root=tmp_path)

    pkt_stat = _make_v2_packet(tmp_path / "stat-pkt", slug="2026-11-10-stat-study")
    s_obj = json.loads((pkt_stat / "run-summary.json").read_text(encoding="utf-8"))
    s_obj["statistical_benchmark"] = {"arms": []}
    (pkt_stat / "run-summary.json").write_text(json.dumps(s_obj), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected key.*statistical_benchmark"):
        mod.stage_report(run_dir=pkt_stat, slug="2026-11-10-stat-study", reports_root=reports, root=tmp_path)

    pkt_ord = _make_v2_packet(tmp_path / "ord-pkt", slug="2026-11-10-ord-study")
    ed_obj = json.loads((pkt_ord / "editorial.json").read_text(encoding="utf-8"))
    ed_obj["catalog_order"] = 0
    (pkt_ord / "editorial.json").write_text(json.dumps(ed_obj), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected key.*catalog_order"):
        mod.stage_report(run_dir=pkt_ord, slug="2026-11-10-ord-study", reports_root=reports, root=tmp_path)

    # Restore valid v2 JSON, test forbidden title pattern
    pkt2 = _make_v2_packet(
        tmp_path / "bad-title",
        slug="2026-11-10-bad-title",
        title="Full evaluation full-default, 2026-11-10 (38e68e2a)",
    )
    with pytest.raises(ValueError, match="title rejected"):
        mod.stage_report(run_dir=pkt2, slug="2026-11-10-bad-title", reports_root=reports, root=tmp_path)


def test_stage_requires_judged_benchmark_unless_diagnostic_and_enforces_iso_date(tmp_path: Path) -> None:
    mod = _load_publish()
    reports = tmp_path / "reports"
    assets = reports / "assets"
    assets.mkdir(parents=True)
    for asset_name in ("report-shell.css", "report-shell.js", "dashboard-shell.css", "dashboard-shell.js"):
        (assets / asset_name).write_text("/* asset */\n", encoding="utf-8")
    (reports / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")

    # Non-ISO human date rejected
    bad_date = _make_v2_packet(
        tmp_path / "human-date",
        slug="2026-11-10-human-date",
        date="10 Nov 2026",
    )
    with pytest.raises(ValueError, match="canonical ISO date 'YYYY-MM-DD'"):
        mod.stage_report(run_dir=bad_date, slug="2026-11-10-human-date", reports_root=reports, root=ROOT)

    # Unjudged WAHS / ChartSearchAI run rejected by default
    unjudged = _make_v2_packet(
        tmp_path / "unjudged-wahs",
        family="wahs",
        slug="2026-11-11-unjudged-wahs-study",
        date="2026-11-11",
        judged=False,
    )
    with pytest.raises(ValueError, match="requires judged Benchmark /100 scores"):
        mod.stage_report(run_dir=unjudged, slug="2026-11-11-unjudged-wahs-study", reports_root=reports, root=ROOT)

    # Explicit diagnostic=True (--diagnostic) permits staging latency/engineering diagnostic runs
    staged = mod.stage_report(
        run_dir=unjudged,
        slug="2026-11-11-unjudged-wahs-study",
        diagnostic=True,
        reports_root=reports,
        root=ROOT,
    )
    assert staged.is_file()
    ed_staged = json.loads((reports / "2026-11-11-unjudged-wahs-study" / "editorial.json").read_text(encoding="utf-8"))
    assert ed_staged["diagnostic"] is True
    assert ed_staged["date"] == "2026-11-11"


def test_revamped_report_shell_has_4_tabs_only_and_supports_domain_guardrails() -> None:
    shell_js = ROOT / "reports" / "assets" / "report-shell.js"
    shell_css = ROOT / "reports" / "assets" / "report-shell.css"
    js_txt = shell_js.read_text(encoding="utf-8")
    css_txt = shell_css.read_text(encoding="utf-8")

    assert "All Sections" not in js_txt
    assert "rtab-all" not in js_txt
    assert "rtab-all" not in css_txt
    assert "statistical_benchmark" not in js_txt
    assert "const defaultTab = 'overview';" in js_txt
    assert "domain_guardrails" in js_txt
    assert "seed_replicates" in js_txt

    chk = subprocess.run(["node", "--check", str(shell_js)], capture_output=True, text=True, check=False)
    assert chk.returncode == 0, chk.stderr
