"""Curated catalog contracts for staged packets and frozen model/score metadata.

Publication does not evaluate runs, resolve live model profiles or read source
experiment workspaces. Score-table rendering and packet boundaries stay covered.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_MOD_PATH = ROOT / "scripts" / "build-reports-index.py"


def _load():
    assert _MOD_PATH.exists(), "scripts/build-reports-index.py missing"
    spec = importlib.util.spec_from_file_location("build_reports_index_contract", _MOD_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _packet(reports: Path, slug: str) -> Path:
    packet = reports / slug
    packet.mkdir(parents=True)
    (packet / "index.html").write_text("<h1>Reviewed report</h1>", encoding="utf-8")
    return packet


@pytest.mark.parametrize("arm", [
    "med-agent-team-low", "med-agent-team-med", "med-agent-team-high",
    "med-agent-team-parity", "med-agent-team-12b",
])
def test_human_arm_preserves_recorded_team_identifiers(arm):
    bri = _load()
    assert bri.human_arm(arm) == (arm, arm)


def test_human_arm_preserves_validated_and_indepth_flags():
    bri = _load()
    arm = "med-agent-team-high-validated-indepth"
    assert bri.human_arm(arm) == (arm, arm)


def test_human_arm_does_not_infer_tier_from_prefix():
    bri = _load()
    assert bri.human_arm("med-agent-team-zzz") == ("med-agent-team-zzz", "med-agent-team-zzz")


def test_human_arm_preserves_single_indepth_identifier():
    bri = _load()
    assert bri.human_arm("single-12b-indepth") == ("single-12b-indepth", "single-12b-indepth")


def test_scout_table_preserves_frozen_single_model_identifier():
    bri = _load()
    html = bri._scout_table([{
        "backend": "gemma-4-12b · 12B · Q8_0", "n": 2, "benchmark_score": 75.0,
    }])
    assert 'title="gemma-4-12b · 12B · Q8_0"' in html
    assert '>gemma-4-12b · 12B · Q8_0</td>' in html
    assert 'class="bench best">75.0' in html


def test_gather_preserves_frozen_scores_without_evaluating(tmp_path, monkeypatch):
    bri = _load()
    packet = _packet(tmp_path, "recorded-team")
    scout = [{"backend": "med-agent-team-low", "n": 1,
              "benchmark_score": 73.0, "harm_count": 1}]
    (packet / "meta.json").write_text(json.dumps({"scout": scout}), encoding="utf-8")
    (packet / "results.jsonl").write_text(
        json.dumps({"backend_id": "a-new-model", "request": {"patient": "p1"}}) + "\n",
        encoding="utf-8",
    )
    (packet / "run_manifest.json").write_text(
        json.dumps({"patients": {"p1": {"display": "p1 - Fixture Patient"}}}), encoding="utf-8",
    )
    monkeypatch.setattr(bri, "REPORTS", tmp_path)
    gathered = bri.gather("recorded-team")
    assert gathered["scout"] == scout
    assert gathered["cells"] == 1
    assert gathered["patients"] == "Fixture Patient"
    html = bri._card({"slug": "recorded-team", "title": "Recorded team"})
    assert "med-agent-team-low" in html
    assert "a-new-model" not in html
    assert 'class="harm"' in html


def test_scout_table_escapes_recorded_model_metadata():
    bri = _load()
    html = bri._scout_table([{"backend": 'unknown <model> & "profile"', "n": 1}])
    assert 'unknown &lt;model&gt; &amp; &quot;profile&quot;' in html
    assert '<model>' not in html


def _stub_human_arm(monkeypatch, bri):
    monkeypatch.setattr(bri, "human_arm", lambda arm: (f"Name {arm}", f"detail {arm}"))


def test_scout_table_unscored_fallback():
    bri = _load()
    html = bri._scout_table([])
    assert "not yet scored" in html
    assert "<table" not in html


def test_scout_table_marks_best_and_harm(monkeypatch):
    bri = _load()
    _stub_human_arm(monkeypatch, bri)
    scout = [
        {"backend": "a", "n": 5, "benchmark_score": 80.0, "accuracy_mean": 8.0,
         "completeness_mean": 7.0, "relevance_mean": 9.0, "harm_count": 0,
         "confabulation_count": 0, "fabricated_citation_count": 0},
        {"backend": "b", "n": 5, "benchmark_score": 60.0, "accuracy_mean": 6.0,
         "completeness_mean": 6.0, "relevance_mean": 6.0, "harm_count": 2,
         "confabulation_count": 1, "fabricated_citation_count": 0},
    ]
    html = bri._scout_table(scout)
    assert 'class="bench best">80.0' in html
    assert 'class="harm"' in html
    assert "harm: 2 · confabulations: 1 · fabricated citations: 0" in html
    assert "Name a" in html and "Name b" in html


def test_scout_table_renders_indepth_block_for_arms_with_background(monkeypatch):
    bri = _load()
    _stub_human_arm(monkeypatch, bri)
    scout = [
        {"backend": "team", "n": 4, "benchmark_score": 70.0, "accuracy_mean": 7.0,
         "completeness_mean": 7.0, "relevance_mean": 7.0, "harm_count": 0,
         "confabulation_count": 0, "fabricated_citation_count": 0,
         "background": {"n_background": 4, "benchmark_score": 88.5, "support_mean": 9.0,
                        "added_value_mean": 8.0, "new_harm_count": 0, "padded_count": 1}},
        {"backend": "single", "n": 4, "benchmark_score": 65.0, "accuracy_mean": 6.5,
         "completeness_mean": 6.5, "relevance_mean": 6.5, "harm_count": 0,
         "confabulation_count": 0, "fabricated_citation_count": 0, "background": {}},
    ]
    html = bri._scout_table(scout)
    assert "In-Depth Benchmark" in html
    assert "scored separately on" in html
    assert "88.5" in html
    assert "70.0" in html and "65.0" in html


def test_scout_table_no_indepth_block_when_no_background(monkeypatch):
    bri = _load()
    _stub_human_arm(monkeypatch, bri)
    scout = [{"backend": "x", "n": 3, "benchmark_score": 50.0, "accuracy_mean": 5.0,
              "completeness_mean": 5.0, "relevance_mean": 5.0, "harm_count": 0,
              "confabulation_count": 0, "fabricated_citation_count": 0}]
    assert "In-Depth Benchmark" not in bri._scout_table(scout)


def test_main_writes_curated_index_and_warns_on_staged_but_unlisted(tmp_path, monkeypatch, capsys):
    bri = _load()
    reports = tmp_path / "reports"
    for slug in ("listed-run", "second-run", "ghost-run"):
        packet = _packet(reports, slug)
        (packet / "meta.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({
        "intro": "hello", "scoring_note": "note",
        "runs": [{"slug": "second-run", "title": "Second Run"},
                 {"slug": "listed-run", "title": "Listed Run", "summary": "s", "takeaway": "t"}],
    }), encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    monkeypatch.setattr(bri, "MANIFEST", manifest)
    bri.main()
    html = (reports / "index.html").read_text(encoding="utf-8")
    assert "hello" in html
    assert html.index("Second Run") < html.index("Listed Run")
    assert "ghost-run" not in html
    assert "ghost-run is staged" in capsys.readouterr().err


def test_card_includes_gather_facts_and_dashboard_link(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    packet = _packet(reports, "fact-run")
    (packet / "dashboard.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    monkeypatch.setattr(bri, "gather", lambda slug: {
        "patients": "12 patients", "cells": 24, "date": "2026-07-21", "scout": [],
    })
    html = bri._card({"slug": "fact-run", "title": "Fact Run", "summary": "summary", "takeaway": "take"})
    assert "12 patients" in html
    assert "24 graded answers" in html
    assert "2026-07-21" in html
    assert 'href="fact-run/dashboard.html"' in html


def test_index_html_uses_publication_theme_toggle_assets(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    reports.mkdir()
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({"intro": "i", "scoring_note": "n", "runs": []}), encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    monkeypatch.setattr(bri, "MANIFEST", manifest)
    bri.main()
    html = (reports / "index.html").read_text(encoding="utf-8")
    assert bri.THEME_TOGGLE_BUTTON_HTML in html
    assert bri.THEME_TOGGLE_CSS in html
    assert bri.theme_bootstrap_js("oc-theme-index") in html
    assert bri.theme_toggle_js("oc-theme-index") in html
    assert "aria-label='Toggle light or dark mode'" in html
    assert "localStorage.getItem('oc-theme-index')" in html
    assert "localStorage.setItem('oc-theme-index',n)" in html


def test_card_renders_meta_scoreline_instead_of_unscored_disclaimer(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    packet = _packet(reports, "catalyst-run")
    (packet / "meta.json").write_text(json.dumps({
        "run_path": "does-not-resolve", "scoreline": "12/12 conversations passed - 384 assertions",
    }), encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    html = bri._card({"slug": "catalyst-run", "title": "T", "summary": "S"})
    assert "384 assertions" in html
    assert "not yet scored" not in html


def test_run_dir_for_rejects_packet_traversal(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    reports.mkdir()
    outside = tmp_path / "private-run"
    outside.mkdir()
    (outside / "results.jsonl").write_text(
        json.dumps({"backend_id": "private-model"}) + "\n", encoding="utf-8",
    )
    monkeypatch.setattr(bri, "REPORTS", reports)
    assert bri._run_dir_for("../private-run") is None
    assert bri._run_dir_for(str(outside)) is None
    assert bri.gather("../private-run")["cells"] is None


def test_catalyst_gather_uses_exact_staged_packet_not_source_workspace(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "external-publication"
    packet = _packet(reports, "catalyst-run")
    source = tmp_path / "source-workspace"
    source.mkdir()
    (source / "results.json").write_text("not publishable JSON", encoding="utf-8")
    (packet / "meta.json").write_text(json.dumps({
        "report_family": "catalyst", "run_path": "../source-workspace",
        "suite_id": "suite-1", "suite_sha256": "a" * 64,
    }), encoding="utf-8")
    (packet / "results.json").write_text(json.dumps({
        "resultCount": 2, "passedCount": 1,
        "results": [{"assertions": [
            {"name": "base_gold_execution_match", "passed": True},
            {"name": "successor_gold_execution_match", "passed": False},
        ]}],
    }), encoding="utf-8")
    (packet / "judge.jsonl").write_text(
        json.dumps({"composite": 80}) + "\n" + json.dumps({"composite": 100}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bri, "ROOT", tmp_path / "unrelated-owner")
    monkeypatch.setattr(bri, "REPORTS", reports)
    assert bri._run_dir_for("catalyst-run") == packet.resolve()
    gathered = bri.gather("catalyst-run")
    assert gathered["family"] == "catalyst"
    assert gathered["cells"] == 2
    assert gathered["scout"] == []
    assert gathered["scoreline"] == "Gold checks: 1/2 passed · Advisory judge median: 90/100"
    html = bri._card({"slug": "catalyst-run", "title": "Catalyst", "summary": "S"})
    assert "Catalyst SQL" in html
    assert "2 conversations" in html


def test_run_dir_for_rejects_symlink_outside_publication_packets(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    reports.mkdir()
    outside = tmp_path / "private-run"
    outside.mkdir()
    (outside / "results.json").write_text("private results", encoding="utf-8")
    (reports / "bad").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(bri, "REPORTS", reports)
    assert bri._run_dir_for("bad") is None
    assert bri.gather("bad")["cells"] is None


def test_the_decision_document_is_reachable_from_the_index(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    packet = _packet(reports, "cmp-run")
    (packet / "comparison.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    monkeypatch.setattr(bri, "gather", lambda slug: {
        "patients": "", "cells": 36, "date": "2026-08-25", "scout": [], "family": "catalyst",
    })
    html = bri._card({"slug": "cmp-run", "title": "Cmp", "summary": "s"})
    assert 'href="cmp-run/comparison.html"' in html
    assert "Compare the teams" in html
    assert "Read the report" in html


def test_a_comparison_run_says_how_the_teams_did_on_the_index(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    packet = _packet(reports, "cmp")
    (packet / "meta.json").write_text(json.dumps({"report_family": "catalyst"}), encoding="utf-8")

    def row(team, passed, valid=True):
        return {"profileId": team, "passed": passed, "measurementValid": valid,
                "assertions": [{"name": "successor_gold_execution_match", "passed": passed}]}

    (packet / "results.json").write_text(json.dumps({"resultCount": 4, "results": [
        row("team-a", True), row("team-a", True),
        row("team-b", True), row("team-b", False, valid=False),
    ]}), encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    gathered = bri.gather("cmp")
    assert "2 teams" in gathered["scoreline"]
    assert "team-a 2/2" in gathered["scoreline"]
    assert "team-b 1/2" in gathered["scoreline"]
    assert "1 invalid measurement" in gathered["scoreline"]
    assert gathered["scoreline"] in bri._card({"slug": "cmp", "title": "Comparison"})


def test_a_catalyst_card_links_the_staged_run_seed(tmp_path, monkeypatch):
    bri = _load()
    reports = tmp_path / "reports"
    packet = _packet(reports, "seeded-run")
    (packet / "run-config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(bri, "REPORTS", reports)
    monkeypatch.setattr(bri, "gather", lambda slug: {
        "patients": "", "cells": 36, "date": "2026-08-25", "scout": [], "family": "catalyst",
    })
    html = bri._card({"slug": "seeded-run", "title": "Seeded", "summary": "s"})
    assert 'href="seeded-run/run-config.json"' in html
    assert "Run seed (JSON)" in html


@pytest.mark.parametrize("existing_catalog", [False, True])
def test_partial_archive_build_fails_before_catalog_or_sitemap_changes(tmp_path, monkeypatch, existing_catalog):
    bri = _load()
    reports = tmp_path / "reports"
    _packet(reports, "available")
    if existing_catalog:
        (reports / "index.html").write_text("Previous live catalog")
        (reports / "sitemap.xml").write_text("Previous live sitemap")
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({"runs": [
        {"slug": "available", "title": "Available"},
        {"slug": "archived-elsewhere", "title": "Live archive"},
        {"slug": "unavailable", "title": "Retained history", "availability": "unavailable"},
    ]}))
    before = {path.relative_to(tmp_path): path.read_bytes()
              for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="incomplete staged report archive.*archived-elsewhere"):
        bri.main(["--reports-root", str(reports), "--manifest", str(manifest)])
    after = {path.relative_to(tmp_path): path.read_bytes()
             for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


def test_check_only_allows_incoming_slug_without_creating_files(tmp_path, capsys):
    bri = _load()
    reports = tmp_path / "absent-reports"
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({"runs": [
        {"slug": "incoming", "title": "Replacement"},
        {"slug": "unavailable", "title": "History", "availability": "unavailable"},
    ]}))
    before = manifest.read_bytes()
    bri.main(["--reports-root", str(reports), "--manifest", str(manifest),
              "--check-archive", "--pending-slug", "incoming"])
    assert "archive is complete" in capsys.readouterr().out
    assert not reports.exists()
    assert manifest.read_bytes() == before
    # The real build must validate the incoming packet after staging.
    with pytest.raises(ValueError, match="missing index.html for: incoming"):
        bri.main(["--reports-root", str(reports), "--manifest", str(manifest)])
    assert not reports.exists()


def test_pending_slug_is_restricted_to_check_only(tmp_path):
    bri = _load()
    with pytest.raises(SystemExit) as error:
        bri.main(["--pending-slug", "incoming"])
    assert error.value.code == 2


@pytest.mark.parametrize("slug", ["../outside", "/absolute", "UPPER"])
def test_archive_validation_rejects_invalid_curated_slugs(tmp_path, slug):
    bri = _load()
    with pytest.raises(ValueError, match="invalid curated report slug"):
        bri.validate_archive([{"slug": slug}], tmp_path)


def test_archive_validation_cannot_use_a_report_outside_the_archive(tmp_path):
    bri = _load()
    reports = tmp_path / "reports"
    reports.mkdir()
    outside = _packet(tmp_path / "private", "outside")
    (reports / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="missing index.html for: linked"):
        bri.validate_archive([{"slug": "linked"}], reports)


@pytest.mark.parametrize("staged", [False, True])
def test_explicitly_unavailable_report_stays_unlinked_even_if_staged(tmp_path, staged):
    bri = _load()
    reports = tmp_path / "reports"
    reports.mkdir()
    if staged:
        _packet(reports, "unavailable")
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({"runs": [
        {"slug": "unavailable", "title": "History", "availability": "unavailable"},
    ]}))
    bri.main(["--reports-root", str(reports), "--manifest", str(manifest)])
    assert "History" in (reports / "index.html").read_text()
    assert "Report unavailable" in (reports / "index.html").read_text()
    assert 'href="unavailable/index.html"' not in (reports / "index.html").read_text()
    assert "/unavailable/index.html" not in (reports / "sitemap.xml").read_text()
