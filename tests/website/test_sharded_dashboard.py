"""Tests for sharded `dashboard-details/*.json` validation, staging, and preview serving."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.error
from pathlib import Path
from urllib.request import urlopen

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    mod_name = name.replace("-", "_").replace(".py", "") + "_sharded_test"
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / "scripts" / name)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_sharded_packet(run_dir: Path, slug: str, *, include_shard_file: bool = True, extra_cell_key: str | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": slug,
                "report_family": "wahs",
                "date": "2026-11-12",
                "cells": 1,
                "patients": "Fixture Patient",
                "scout": [{"backend": "arm-a", "n": 1, "benchmark_score": 88.0, "harm_count": 0}],
                "judging": {"recorded": True, "sentence": "Judged by fixture evaluator."},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "report-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.report.v2",
                "schema_version": 2,
                "runs": [
                    {
                        "id": slug,
                        "backends": ["arm-a"],
                        "judge": [{"backend": "arm-a", "n": 1, "benchmark_score": 88.0, "harm_count": 0}],
                        "catalog_meta": {"title": "Sharded dashboard fixture"},
                        "arm_cards": {"arm-a": {"title": "Arm A", "short_title": "Arm A"}},
                        "source_card_pool": {},
                        "refs_pool": {},
                        "scenarios": [
                            {
                                "scenario_id": "s1",
                                "turns": [
                                    {
                                        "turn": 1,
                                        "question": "What does the chart show?",
                                        "cells": {"arm-a": {"answer_text": "Lisinopril 10 mg daily [1]."}},
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
    shard_rel = "dashboard-details/00-arm-a-12345678.json"
    (run_dir / "dashboard-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.dashboard.v2",
                "schema_version": 2,
                "family": "wahs",
                "status": {
                    "run": slug,
                    "family": "wahs",
                    "backends": ["arm-a"],
                    "scenarios": ["s1"],
                    "arms": {"arm-a": {"label": "Arm A"}},
                    "grid": [{"scenario": "s1", "backend": "arm-a", "state": "done"}],
                },
                "record_pool": [],
                "sources_pool": [],
                "refs_pool": [],
                "details": {},
                "detail_shards": {"arm-a": shard_rel},
            }
        ),
        encoding="utf-8",
    )
    if include_shard_file:
        cell_obj = {
            "scenario": "s1",
            "backend": "arm-a",
            "expectations": {},
            "catalystExpected": None,
            "turns": [{"turn": 1, "question": "Q?", "answer": "Lisinopril 10 mg daily [1].", "status": 200}],
            "judge": {},
        }
        if extra_cell_key:
            cell_obj[extra_cell_key] = "<p>disallowed</p>"
        (run_dir / "dashboard-details").mkdir(parents=True, exist_ok=True)
        (run_dir / shard_rel).write_text(json.dumps({"s1|arm-a": cell_obj}), encoding="utf-8")


def test_sharded_dashboard_stage_validate_and_preview(tmp_path: Path) -> None:
    publish_mod = _load_script("publish-report.py")
    preview_mod = _load_script("preview-report.py")
    index_mod = _load_script("build-reports-index.py")

    slug = "2026-11-12-sharded-fixture"
    run_dir = tmp_path / "run_ok"
    _make_sharded_packet(run_dir, slug)

    reports_out = tmp_path / "reports"
    assets_out = reports_out / "assets"
    assets_out.mkdir(parents=True)
    for asset in (ROOT / "reports" / "assets").iterdir():
        if asset.is_file():
            (assets_out / asset.name).write_bytes(asset.read_bytes())

    staged_index = publish_mod.stage_report(
        run_dir=run_dir,
        slug=slug,
        title="Sharded fixture: does lazy detail loading validate?",
        summary="This fixture verifies that sharded dashboard-details files stage cleanly and pass validation.",
        takeaway="Only the arm shard requested by a cell click is staged and validated without inline bloat.",
        family="wahs",
        reports_root=reports_out,
        root=ROOT,
    )
    staged_dir = staged_index.parent
    staged_shard = staged_dir / "dashboard-details" / "00-arm-a-12345678.json"
    assert staged_shard.is_file()
    staged_shard_data = json.loads(staged_shard.read_text(encoding="utf-8"))
    assert staged_shard_data["s1|arm-a"]["turns"][0]["answer"] == "Lisinopril 10 mg daily [1]."

    manifest = json.loads((reports_out / "reports-index.json").read_text(encoding="utf-8"))
    runs_list = manifest["runs"] if isinstance(manifest, dict) else manifest
    index_mod.validate_archive(runs_list, reports_out)

    # Preview server serves dashboard-details/*.json with 200 and rejects path traversal.
    srv = preview_mod.create_preview_server(
        run_dir, host="127.0.0.1", port=0, assets_dir=ROOT / "reports" / "assets"
    )
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        base = f"http://127.0.0.1:{srv.server_port}"
        with urlopen(base + "/dashboard-details/00-arm-a-12345678.json", timeout=5) as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
            assert "s1|arm-a" in body
        with pytest.raises(urllib.error.HTTPError) as err:
            urlopen(base + "/dashboard-details/../secret.json", timeout=5)
        assert err.value.code == 404
    finally:
        srv.shutdown()
        srv.server_close()

    # Deleting a referenced detail shard causes validate_archive to fail closed.
    staged_shard.unlink()
    with pytest.raises(ValueError, match="referenced in detail_shards is missing"):
        index_mod.validate_archive(runs_list, reports_out)


def test_sharded_dashboard_rejects_missing_and_unexpected_keys(tmp_path: Path) -> None:
    publish_mod = _load_script("publish-report.py")
    reports_out = tmp_path / "reports"
    reports_out.mkdir(parents=True)
    (reports_out / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")

    missing_dir = tmp_path / "run_missing"
    _make_sharded_packet(missing_dir, "2026-11-12-missing-shard", include_shard_file=False)
    with pytest.raises(ValueError, match="missing dashboard detail shard"):
        publish_mod.stage_report(
            run_dir=missing_dir,
            slug="2026-11-12-missing-shard",
            title="Missing shard test fixture validation",
            summary="Verifies publish-report rejects packets whose declared detail_shards target is absent.",
            takeaway="Missing shard files fail closed during staging before touching reports/.",
            family="wahs",
            reports_root=reports_out,
            root=tmp_path,
        )

    bad_key_dir = tmp_path / "run_bad_key"
    _make_sharded_packet(bad_key_dir, "2026-11-12-bad-shard-key", extra_cell_key="answer_html")
    with pytest.raises(ValueError, match="unexpected key.*answer_html"):
        publish_mod.stage_report(
            run_dir=bad_key_dir,
            slug="2026-11-12-bad-shard-key",
            title="Disallowed HTML key in shard fixture",
            summary="Verifies publish-report rejects unknown or HTML keys inside sharded cell detail JSON.",
            takeaway="Closed keyset validation covers every detail shard file in addition to dashboard-data.json.",
            family="wahs",
            reports_root=reports_out,
            root=tmp_path,
        )
