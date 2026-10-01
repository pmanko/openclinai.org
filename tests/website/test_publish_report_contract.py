"""Publication consumes reviewed, pre-rendered packets without harness imports."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "publish-report.sh"
STAGE_SCRIPT = ROOT / "scripts" / "stage-report.py"
SOURCE_SHA = "a" * 64


def _load_stage():
    spec = importlib.util.spec_from_file_location("stage_report_contract", STAGE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _files(directory: Path) -> dict[str, bytes]:
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


def _assert_staged_packet(source: Path, destination: Path) -> None:
    source_files = _files(source)
    staged_files = _files(destination)
    expected = (set(source_files) - {"report.html"}) | {"index.html", "meta.json"}
    assert set(staged_files) == expected
    assert staged_files["index.html"] == source_files["report.html"]
    for name, content in source_files.items():
        if name not in {"report.html", "meta.json"}:
            assert staged_files[name] == content


def _catalyst_run(
    directory: Path,
    *,
    index_source_sha: str | None = None,
    **manifest_extra: object,
) -> Path:
    run = directory / "run"
    run.mkdir(parents=True)
    (run / "report.html").write_text('<h1>Reviewed Catalyst report</h1>', encoding="utf-8")
    (run / "suite.json").write_text(json.dumps({"id": "suite-under-test-v1"}), encoding="utf-8")
    (run / "run_manifest.json").write_text(
        json.dumps({"run_id": "r1", **manifest_extra}), encoding="utf-8",
    )
    if index_source_sha is not None:
        (run / "evidence-index.json").write_text(json.dumps({
            "contractVersion": "harness.catalyst-notebook.evidence-index.v1",
            "entries": [{
                "path": "suite.json", "kind": "suite_definition",
                "sha256": hashlib.sha256((run / "suite.json").read_bytes()).hexdigest(),
                "metadata": {"sourceSha256": index_source_sha},
            }],
        }), encoding="utf-8")
    return run


@pytest.fixture
def chart_fixture(tmp_path: Path) -> Path:
    run = tmp_path / "chart-packet"
    run.mkdir()
    (run / "report.html").write_text('<h1>Reviewed chart report</h1>', encoding="utf-8")
    (run / "events.jsonl").write_text(
        json.dumps({"event_type": "run", "comparison_set": "demo"}) + "\n", encoding="utf-8",
    )
    (run / "results.jsonl").write_text(
        json.dumps({"backend_id": "frozen-model", "request": {"patient": "p1"}}) + "\n",
        encoding="utf-8",
    )
    (run / "run_manifest.json").write_text(
        json.dumps({"patients": {"p1": {"display": "Fixture Patient"}}}), encoding="utf-8",
    )
    (run / "meta.json").write_text(json.dumps({
        "scout": [{"backend": "frozen-model · 12B · Q8_0", "n": 1,
                   "benchmark_score": 73.0, "harm_count": 1}],
        "scoreline": "Recorded fixture evaluation",
    }), encoding="utf-8")
    return run


@pytest.fixture
def catalyst_fixture(tmp_path: Path) -> Path:
    run = _catalyst_run(tmp_path / "catalyst-packet")
    (run / "results.json").write_text(json.dumps({
        "resultCount": 1,
        "results": [{"assertions": [{"name": "base_gold_execution_match", "passed": True}]}],
    }), encoding="utf-8")
    (run / "judge.jsonl").write_text(json.dumps({"composite": 90}) + "\n", encoding="utf-8")
    evidence = run / "scenarios" / "team-a" / "s1"
    evidence.mkdir(parents=True)
    (evidence / "evidence.json").write_text('{"reviewed": true}', encoding="utf-8")
    return run


def _publish(reports_root: Path, family: str, run_dir: Path, slug: str, title: str):
    # This isolated publication catalog owns only these fixture packets.
    if not (reports_root / "reports-index.json").exists():
        reports_root.mkdir(parents=True, exist_ok=True)
        (reports_root / "reports-index.json").write_text('{"runs": []}', encoding="utf-8")
    return subprocess.run(
        ["bash", str(SCRIPT), family, str(run_dir), slug, title, "summary", "takeaway"],
        cwd=ROOT,
        env={**os.environ, "PUBLISH_DRY_RUN": "1", "REPORTS_ROOT": str(reports_root)},
        text=True, capture_output=True, check=False,
    )


def test_dry_run_stages_both_families_and_preserves_curation(
    tmp_path: Path, chart_fixture: Path, catalyst_fixture: Path,
) -> None:
    reports = tmp_path / "reports"
    chart_before = _files(chart_fixture)
    catalyst_before = _files(catalyst_fixture)
    chart = _publish(reports, "chartsearchai", chart_fixture, "chart-fixture", "Chart title")
    catalyst = _publish(reports, "catalyst", catalyst_fixture, "catalyst-fixture", "Catalyst title")
    assert chart.returncode == 0, chart.stdout + chart.stderr
    assert catalyst.returncode == 0, catalyst.stdout + catalyst.stderr
    _assert_staged_packet(chart_fixture, reports / "chart-fixture")
    _assert_staged_packet(catalyst_fixture, reports / "catalyst-fixture")
    assert (reports / "catalyst-fixture" / "scenarios").is_dir()
    assert (reports / "index.html").is_file()
    assert (reports / "reports-index.json").is_file()
    assert _files(chart_fixture) == chart_before
    assert _files(catalyst_fixture) == catalyst_before

    chart_meta = json.loads((reports / "chart-fixture" / "meta.json").read_text(encoding="utf-8"))
    catalyst_meta = json.loads((reports / "catalyst-fixture" / "meta.json").read_text(encoding="utf-8"))
    assert chart_meta["report_family"] == "chartsearchai"
    assert chart_meta["comparison_set"] == "demo"
    assert "suite_id" not in chart_meta
    assert chart_meta["run_path"] == ""
    assert chart_meta["scout"] == json.loads(chart_before["meta.json"])["scout"]
    assert chart_meta["scoreline"] == "Recorded fixture evaluation"
    assert catalyst_meta["report_family"] == "catalyst"
    assert catalyst_meta["suite_id"] == "suite-under-test-v1"
    assert catalyst_meta["suite_sha256"] == hashlib.sha256(catalyst_before["suite.json"]).hexdigest()
    assert "comparison_set" not in catalyst_meta
    assert catalyst_meta["run_path"] == ""
    assert str(tmp_path) not in json.dumps([chart_meta, catalyst_meta])

    html = (reports / "index.html").read_text(encoding="utf-8")
    assert "ChartSearchAI" in html and "Catalyst SQL" in html
    assert "Gold checks: 1/1 passed" in html
    assert "Advisory judge median: 90/100" in html
    assert "frozen-model · 12B · Q8_0" in html
    assert 'class="bench best">73.0' in html
    assert 'class="harm"' in html

    (reports / "catalyst-fixture" / "obsolete.txt").write_text("old evidence", encoding="utf-8")
    republished = _publish(reports, "catalyst", catalyst_fixture, "catalyst-fixture", "Replacement title")
    assert republished.returncode == 0, republished.stdout + republished.stderr
    _assert_staged_packet(catalyst_fixture, reports / "catalyst-fixture")
    manifest = json.loads((reports / "reports-index.json").read_text(encoding="utf-8"))
    entries = [row for row in manifest["runs"] if row["slug"] == "catalyst-fixture"]
    assert entries == [{"slug": "catalyst-fixture", "title": "Replacement title",
                        "summary": "summary", "takeaway": "takeaway", "family": "catalyst"}]
    assert _files(chart_fixture) == chart_before
    assert _files(catalyst_fixture) == catalyst_before


def test_dry_run_accepts_external_packet_and_copies_only_exact_packet(
    tmp_path: Path, catalyst_fixture: Path,
) -> None:
    private = catalyst_fixture.parent / "private.txt"
    private.write_text("do not publish", encoding="utf-8")
    reports = tmp_path / "external-output"
    result = _publish(reports, "catalyst", catalyst_fixture, "external-run", "External")
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_staged_packet(catalyst_fixture, reports / "external-run")
    assert not (reports / "external-run" / "private.txt").exists()
    assert private.read_text(encoding="utf-8") == "do not publish"
    meta = json.loads((reports / "external-run" / "meta.json").read_text(encoding="utf-8"))
    assert meta["run_path"] == ""
    assert str(tmp_path) not in json.dumps(meta)


def test_stage_module_directly_covers_family_contracts(
    tmp_path: Path, chart_fixture: Path, catalyst_fixture: Path,
) -> None:
    mod = _load_stage()
    reports = tmp_path / "reports"
    manifest = tmp_path / "reports-index.json"
    manifest.write_text(json.dumps({"intro": "i", "scoring_note": "n", "runs": []}), encoding="utf-8")
    for family, source, slug, title in (
        ("chartsearchai", chart_fixture, "chart-direct", "Chart direct"),
        ("catalyst", catalyst_fixture, "catalyst-direct", "Catalyst direct"),
    ):
        published = mod.stage_report(
            family=family, run_dir=source, slug=slug, reports_root=reports,
            manifest_path=manifest, root=tmp_path, title=title,
        )
        assert published == reports / slug / "index.html"
        _assert_staged_packet(source, reports / slug)
        meta = json.loads((reports / slug / "meta.json").read_text(encoding="utf-8"))
        assert meta["run_path"] == source.relative_to(tmp_path).as_posix()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert [row["title"] for row in payload["runs"]] == ["Catalyst direct", "Chart direct"]
    mod.stage_report(
        family="catalyst", run_dir=catalyst_fixture, slug="catalyst-direct",
        reports_root=reports, manifest_path=manifest, root=tmp_path,
        title="Replacement", summary="Updated summary", takeaway="Updated takeaway",
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(payload["runs"]) == 2
    assert payload["intro"] == "i" and payload["scoring_note"] == "n"
    assert payload["runs"][0] == {
        "slug": "catalyst-direct", "family": "catalyst", "title": "Replacement",
        "summary": "Updated summary", "takeaway": "Updated takeaway",
    }


def test_stage_module_rejects_invalid_inputs(tmp_path: Path, catalyst_fixture: Path) -> None:
    mod = _load_stage()
    manifest = tmp_path / "index.json"
    manifest.write_text(json.dumps({"runs": []}), encoding="utf-8")
    kwargs = {"run_dir": catalyst_fixture, "slug": "valid-slug",
              "reports_root": tmp_path / "reports", "manifest_path": manifest, "root": ROOT}
    for family, slug, message in (
        ("unknown", "valid-slug", "unsupported report family"),
        ("catalyst", "../escape", "slug must contain"),
    ):
        with pytest.raises(ValueError, match=message):
            mod.stage_report(family=family, **{**kwargs, "slug": slug})
    with pytest.raises(FileNotFoundError, match="run directory not found"):
        mod.stage_report(family="catalyst", **{**kwargs, "run_dir": tmp_path / "missing"})
    unrendered = tmp_path / "unrendered"
    unrendered.mkdir()
    with pytest.raises(FileNotFoundError, match="pre-rendered report.html required"):
        mod.stage_report(family="catalyst", **{**kwargs, "run_dir": unrendered})
    with pytest.raises(ValueError, match="overlap"):
        mod.stage_report(family="catalyst", **{
            **kwargs, "reports_root": catalyst_fixture.parent, "slug": catalyst_fixture.name,
        })
    with pytest.raises(ValueError, match="overlap"):
        mod.stage_report(family="catalyst", **{**kwargs, "reports_root": catalyst_fixture / "reports"})
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"runs": []}
    assert not (tmp_path / "reports").exists()
    assert not (catalyst_fixture / "reports").exists()


def test_catalyst_suite_identity_accepts_agreeing_manifest_values(tmp_path: Path) -> None:
    mod = _load_stage()
    # Without recorded source identity, the copied suite supplies the digest.
    derived = _catalyst_run(tmp_path / "derived")
    derived_sha = hashlib.sha256((derived / "suite.json").read_bytes()).hexdigest()
    assert mod._catalyst_suite_identity(derived) == ("suite-under-test-v1", derived_sha)
    # Source and re-serialized suite bytes differ; preserve the recorded source digest.
    agreeing = _catalyst_run(tmp_path / "agreeing", index_source_sha=SOURCE_SHA,
                             suite_id="suite-under-test-v1", suite_sha256=SOURCE_SHA)
    assert SOURCE_SHA != hashlib.sha256((agreeing / "suite.json").read_bytes()).hexdigest()
    assert mod._catalyst_suite_identity(agreeing) == ("suite-under-test-v1", SOURCE_SHA)


def test_catalyst_suite_identity_rejects_manifest_suite_mismatch(tmp_path: Path) -> None:
    mod = _load_stage()
    wrong_id = _catalyst_run(tmp_path / "wrong-id", suite_id="some-other-suite-v9")
    with pytest.raises(ValueError, match="suite_id"):
        mod._catalyst_suite_identity(wrong_id)
    wrong_sha = _catalyst_run(tmp_path / "wrong-sha", index_source_sha=SOURCE_SHA, suite_sha256="b" * 64)
    with pytest.raises(ValueError, match="suite_sha256"):
        mod._catalyst_suite_identity(wrong_sha)


def test_catalyst_suite_identity_rejects_unidentifiable_suite(tmp_path: Path) -> None:
    mod = _load_stage()
    anonymous = tmp_path / "anonymous"
    anonymous.mkdir()
    (anonymous / "suite.json").write_text(json.dumps({}), encoding="utf-8")
    (anonymous / "run_manifest.json").write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing suite_id"):
        mod._catalyst_suite_identity(anonymous)
    malformed = _catalyst_run(tmp_path / "malformed", suite_sha256="not-a-digest")
    with pytest.raises(ValueError, match="lowercase SHA-256 digest"):
        mod._catalyst_suite_identity(malformed)


def test_comparison_set_skips_blanks_and_requires_a_run_event(tmp_path: Path) -> None:
    mod = _load_stage()
    run = tmp_path / "chart-run"
    run.mkdir()
    events = run / "events.jsonl"
    events.write_text("\n".join(["", json.dumps({"event_type": "scenario"}), ""]), encoding="utf-8")
    with pytest.raises(ValueError, match="comparison_set"):
        mod._comparison_set(run)
    events.write_text("\n".join([
        "", json.dumps({"event_type": "run", "comparison_set": "demo"}), "",
    ]), encoding="utf-8")
    assert mod._comparison_set(run) == "demo"


def test_stage_module_rejects_symlinked_run_contents(tmp_path: Path) -> None:
    mod = _load_stage()
    secret = tmp_path / "outside-secret.txt"
    secret.write_text("do not publish", encoding="utf-8")
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "nested-secret.txt").write_text("also secret", encoding="utf-8")
    manifest = tmp_path / "index.json"
    manifest.write_text(json.dumps({"runs": []}), encoding="utf-8")
    reports = tmp_path / "reports"
    file_run = _catalyst_run(tmp_path / "file-link")
    (file_run / "leak.txt").symlink_to(secret)
    nested_run = _catalyst_run(tmp_path / "dir-link")
    (nested_run / "sub").mkdir()
    (nested_run / "sub" / "leak").symlink_to(outside_dir, target_is_directory=True)
    dangling_run = _catalyst_run(tmp_path / "dangling-link")
    (dangling_run / "leak.txt").symlink_to(tmp_path / "missing-secret")
    for slug, run in (("symlinked-file", file_run), ("symlinked-dir", nested_run),
                      ("dangling-link", dangling_run)):
        existing = reports / slug
        existing.mkdir(parents=True)
        (existing / "index.html").write_text("previous publication", encoding="utf-8")
        with pytest.raises(ValueError, match="symlink"):
            mod.stage_report(family="catalyst", run_dir=run, slug=slug,
                             reports_root=reports, manifest_path=manifest, root=ROOT)
        assert _files(existing) == {"index.html": b"previous publication"}
        assert not (reports / f".{slug}.staging").exists()
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"runs": []}
    assert not (reports / "symlinked-file" / "leak.txt").exists()
    assert not (reports / "symlinked-dir" / "sub" / "leak").exists()


def test_stage_module_main_reports_errors_and_success(
    tmp_path: Path, catalyst_fixture: Path, capsys,
) -> None:
    mod = _load_stage()
    manifest = tmp_path / "index.json"
    manifest.write_text(json.dumps({"runs": []}), encoding="utf-8")
    common = ["catalyst", str(catalyst_fixture), "main-stage", "--reports-root",
              str(tmp_path / "reports"), "--manifest", str(manifest), "--root", str(ROOT)]
    assert mod.main(common) == 0
    assert "staged catalyst report" in capsys.readouterr().out
    _assert_staged_packet(catalyst_fixture, tmp_path / "reports" / "main-stage")
    assert mod.main(["catalyst", str(tmp_path / "missing"), *common[2:]]) == 1
    assert "run directory not found" in capsys.readouterr().err
