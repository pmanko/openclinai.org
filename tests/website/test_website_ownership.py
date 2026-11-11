"""Website sources and static publication belong to the umbrella, independent of the harness."""

from __future__ import annotations

from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import threading
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "targets/validation-harness"


def _load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").removesuffix(".py"), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _ResourceCollector(HTMLParser):
    """Collect local stylesheet, script, and external JSON packet references from rendered HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.data_packets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        if tag == "link" and attr_map.get("rel") == "stylesheet" and attr_map.get("href"):
            self.links.append(attr_map["href"])
        elif tag == "script":
            if attr_map.get("src"):
                self.scripts.append(attr_map["src"])
            if attr_map.get("data-src"):
                self.data_packets.append(attr_map["data-src"])


def test_harness_carries_no_website_sources_or_publication_tooling():
    """Invariant: the harness produces artifacts; it never owns website sources or publishers."""
    for relative in ("landing", "site", "reports/reports-index.json", ".github/workflows/pages.yml"):
        assert not (HARNESS / relative).exists(), relative
    for script in (ROOT / "scripts").iterdir():
        if script.name.startswith(("publish-", "cloud-", "build-reports", "build-landing", "stage-report")):
            assert not (HARNESS / "scripts" / script.name).exists(), script.name


def test_publication_does_not_import_or_install_the_harness():
    """Invariant: publication reads captured artifacts and never imports or runs the harness."""
    for script in (ROOT / "scripts").iterdir():
        if script.name.startswith(("publish-", "preview-report", "build-reports")):
            text = script.read_text(encoding="utf-8")
            for coupling in ("from harness", "import harness", "harness-cli", "uv run"):
                assert coupling not in text, (script.name, coupling)


def test_relocated_media_is_checked_before_it_is_staged_in_git():
    """Invariant: no video and no file over 400 KiB is committed to landing website sources."""
    video = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}
    for path in (ROOT / "landing").rglob("*"):
        if not path.is_file():
            continue
        assert path.suffix.lower() not in video, path
        assert path.stat().st_size <= 400 * 1024, (path, path.stat().st_size)


def test_publisher_and_preview_serve_lightweight_shells_with_loadable_resources(tmp_path: Path):
    """Behavior: staging and previewing a v2 fixture packet keeps HTML shells lightweight while all referenced local assets and JSON packets resolve cleanly."""
    publish_mod = _load_script("publish-report.py")
    preview_mod = _load_script("preview-report.py")

    slug = "2026-11-10-shell-fixture"
    run_dir = tmp_path / "fixture_run"
    run_dir.mkdir()
    large_answer = "Clinical chart observation verified against longitudinal vitals. " * 600
    (run_dir / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": slug,
                "report_family": "chartsearchai",
                "date": "10 Nov 2026",
                "cells": 1,
                "patients": "Fixture Patient",
                "scout": [{"backend": "arm-a", "n": 1, "benchmark_score": 90.0, "harm_count": 0}],
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
                        "catalog_meta": {"title": "Shell separation fixture"},
                        "arm_cards": {"arm-a": {"title": "Arm A", "short_title": "Arm A"}},
                        "source_card_pool": {},
                        "refs_pool": {},
                        "scenarios": [
                            {
                                "scenario_id": "s1",
                                "turns": [
                                    {
                                        "turn": 1,
                                        "question": "What are the patient's vitals?",
                                        "cells": {"arm-a": {"answer_text": large_answer}},
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
    (run_dir / "dashboard-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.dashboard.v2",
                "schema_version": 2,
                "status": {"run": slug, "arms": ["arm-a"], "scenarios": ["s1"]},
                "record_pool": {"0": {"note": large_answer}},
                "sources_pool": {},
                "refs_pool": {},
                "details": {},
            }
        ),
        encoding="utf-8",
    )

    reports_out = tmp_path / "staged_reports"
    assets_out = reports_out / "assets"
    assets_out.mkdir(parents=True)
    for asset in (ROOT / "reports" / "assets").iterdir():
        if asset.is_file():
            (assets_out / asset.name).write_bytes(asset.read_bytes())

    staged_index = publish_mod.stage_report(
        run_dir=run_dir,
        slug=slug,
        title="Fixture evaluation: does shell separation load all resources?",
        summary="We ran one clinical question against a 38 KB fixture payload to verify external packet loading.",
        takeaway="Both report and diagnostic shells stayed under 10 KB while referencing loadable packets.",
        family="chartsearchai",
        reports_root=reports_out,
        root=tmp_path,
    )
    staged_dir = staged_index.parent
    for page_path in (staged_dir / "index.html", staged_dir / "dashboard.html"):
        assert page_path.is_file()
        assert page_path.stat().st_size <= 10 * 1024
        collector = _ResourceCollector()
        collector.feed(page_path.read_text(encoding="utf-8"))
        assert collector.links and collector.scripts and collector.data_packets
        for ref in [*collector.links, *collector.scripts, *collector.data_packets]:
            clean_rel = urlparse(ref).path
            resolved = (page_path.parent / clean_rel).resolve()
            assert resolved.is_file() and resolved.stat().st_size > 0, (page_path.name, ref)

    server = preview_mod.create_preview_server(
        run_dir, host="127.0.0.1", port=0, assets_dir=ROOT / "reports" / "assets"
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        for route in ("/", "/dashboard.html"):
            with urlopen(base_url + route, timeout=5) as resp:
                assert resp.status == 200
                html_body = resp.read().decode("utf-8")
            assert len(html_body.encode("utf-8")) <= 10 * 1024
            collector = _ResourceCollector()
            collector.feed(html_body)
            assert collector.links and collector.scripts and collector.data_packets
            for ref in [*collector.links, *collector.scripts, *collector.data_packets]:
                target_url = base_url + (ref if ref.startswith("/") else "/" + ref.lstrip("./"))
                with urlopen(target_url, timeout=5) as sub_resp:
                    assert sub_resp.status == 200
                    assert len(sub_resp.read()) > 0
    finally:
        server.shutdown()
        server.server_close()
