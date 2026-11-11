"""Publication stages v2 pure-JSON packets and previews local runs without the harness."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("publish_report", ROOT / "scripts/publish-report.py")
assert SPEC and SPEC.loader
publish = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publish)

PREV_SPEC = importlib.util.spec_from_file_location("preview_report", ROOT / "scripts/preview-report.py")
assert PREV_SPEC and PREV_SPEC.loader
preview = importlib.util.module_from_spec(PREV_SPEC)
PREV_SPEC.loader.exec_module(preview)


def v2_packet(tmp_path: Path, name: str = "external-packet") -> Path:
    source = tmp_path / name
    source.mkdir(parents=True, exist_ok=True)
    (source / "editorial.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.editorial.v2",
                "schema_version": 2,
                "slug": "2026-11-10-hiv-chart-grounding-study",
                "title": "How accurately does Med Agent Hub read HIV charts on a shared GPU?",
                "summary": "We tested two clinical AI setups across three HIV patient charts and 35 clinical questions.",
                "takeaway": "Med Agent Hub improved accuracy and completeness by 14 points with zero unsafe answers.",
                "family": "chartsearchai",
                "featured": True,
                "date": "10 Nov 2026",
            }
        ),
        encoding="utf-8",
    )
    (source / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": "2026-11-10-hiv-chart-grounding-study",
                "report_family": "chartsearchai",
                "comparison_set": "recorded-comparison",
                "date": "10 Nov 2026",
                "cells": 2,
                "patients": "Fixture Patient",
                "scout": [
                    {
                        "backend": "arm-a",
                        "n": 2,
                        "benchmark_score": 88.5,
                        "accuracy_mean": 9.0,
                        "completeness_mean": 8.8,
                        "relevance_mean": 9.2,
                        "harm_count": 0,
                    }
                ],
                "judging": {"recorded": True, "sentence": "Judged by frontier evaluator."},
            }
        ),
        encoding="utf-8",
    )
    (source / "report-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.report.v2",
                "schema_version": 2,
                "runs": [
                    {
                        "id": "run-1",
                        "backends": ["arm-a"],
                        "arm_cards": {"arm-a": {"title": "Med Agent Hub", "short_title": "Med Agent Hub"}},
                        "source_card_pool": {"1": {"id": "1", "kind": "obs", "date": "2026-01-10", "title": "CD4 count", "value": "450"}},
                        "refs_pool": {"r1": [{"id": "1", "label": "[1]"}]},
                        "scenarios": [
                            {
                                "scenario_id": "s1",
                                "turns": [
                                    {
                                        "turn": 1,
                                        "question": "What is the latest CD4?",
                                        "cells": {
                                            "arm-a": {
                                                "status": "complete",
                                                "answer_md": "Latest CD4 is 450 [1].",
                                                "claims": {"answer": {"source_ids": ["1"], "refs_key": "r1"}},
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
    (source / "dashboard-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.dashboard.v2",
                "schema_version": 2,
                "status": {"run": "run-1", "arms": [{"id": "arm-a", "label": "Med Agent Hub"}], "scenarios": []},
                "record_pool": {},
                "sources_pool": {},
                "refs_pool": {},
                "details": {},
            }
        ),
        encoding="utf-8",
    )
    return source


def test_staging_works_in_isolated_python_without_a_harness_package(tmp_path: Path):
    source = v2_packet(tmp_path)
    owner = tmp_path / "owner"
    reports = owner / "reports"
    reports.mkdir(parents=True)
    (reports / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")
    slug = "2026-11-10-hiv-chart-grounding-study"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/publish-report.py"),
            "stage",
            str(source),
            "--slug",
            slug,
            "--root",
            str(owner),
            "--reports-root",
            str(reports),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    destination = reports / slug
    for fname in ("editorial.json", "run-summary.json", "report-data.json", "dashboard-data.json", "index.html", "dashboard.html"):
        assert (destination / fname).is_file(), fname
    summary = json.loads((destination / "run-summary.json").read_text(encoding="utf-8"))
    assert summary["comparison_set"] == "recorded-comparison"


def test_packet_requires_v2_json_and_failure_preserves_existing_report(tmp_path: Path):
    source = v2_packet(tmp_path)
    (source / "report-data.json").unlink()
    reports = tmp_path / "reports"
    existing = reports / "2026-11-10-example-study"
    existing.mkdir(parents=True)
    (existing / "index.html").write_text("previous publication", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="v2 report-data.json required"):
        publish.stage_report(run_dir=source, slug="2026-11-10-example-study", reports_root=reports, root=tmp_path)
    assert (existing / "index.html").read_text(encoding="utf-8") == "previous publication"


def test_symlinks_cannot_publish_files_outside_the_packet(tmp_path: Path):
    source = v2_packet(tmp_path)
    private = tmp_path / "private.json"
    private.write_text("not publishable", encoding="utf-8")
    (source / "linked.json").symlink_to(private)
    with pytest.raises(ValueError, match="must not contain symlinks"):
        publish.stage_report(
            run_dir=source,
            slug="2026-11-10-example-study",
            reports_root=tmp_path / "reports",
            root=tmp_path,
        )


@pytest.mark.parametrize(
    "slug",
    [
        "..",
        "../outside",
        "UPPER",
        "with space",
        "l5-full-default-2026-11-10-38e68e2a",
        "2026-11-10-study-38e68e2a",
    ],
)
def test_unsafe_or_auto_minted_slugs_are_rejected_before_copying(tmp_path: Path, slug: str):
    with pytest.raises(ValueError, match="slug"):
        publish.stage_report(
            run_dir=v2_packet(tmp_path, name="pkt"),
            slug=slug,
            reports_root=tmp_path / "reports",
            root=tmp_path,
        )


def test_staging_cannot_replace_its_own_input(tmp_path: Path):
    source = v2_packet(tmp_path, name="2026-11-10-valid-study")
    with pytest.raises(ValueError, match="overlap"):
        publish.stage_report(
            run_dir=source,
            slug=source.name,
            reports_root=tmp_path,
            root=tmp_path,
        )


def test_preview_report_serves_shell_and_json_over_http(tmp_path: Path):
    source = v2_packet(tmp_path, name="local-run")
    srv = preview.create_preview_server(source, host="127.0.0.1", port=0)
    host, port = srv.server_address[:2]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://{host}:{port}/") as resp:
            html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "/assets/report-shell.js" in html
            assert "id='report-editorial'" in html
        with urlopen(f"http://{host}:{port}/dashboard.html") as resp:
            dhtml = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "/assets/dashboard-shell.js" in dhtml
        with urlopen(f"http://{host}:{port}/report-data.json") as resp:
            rdata = json.loads(resp.read().decode("utf-8"))
            assert rdata["schema"] == "openclinai.report.v2"
        with urlopen(f"http://{host}:{port}/assets/report-shell.js") as resp:
            js = resp.read().decode("utf-8")
            assert "report-data" in js
    finally:
        srv.shutdown()
        srv.server_close()
