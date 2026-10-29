import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "capture_chart_fixture", ROOT / "scripts" / "capture-chart-fixture.py"
)
CAPTURE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CAPTURE)
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_validation_corpus", ROOT / "scripts" / "verify-validation-corpus.py"
)
VERIFY_CORPUS = importlib.util.module_from_spec(VERIFY_SPEC)
assert VERIFY_SPEC and VERIFY_SPEC.loader
VERIFY_SPEC.loader.exec_module(VERIFY_CORPUS)


LEDGER = {
    "patient": "patient-1",
    "hub_revision": "a" * 40,
    "snapshot_id": "snap-1",
    "total": 2,
    "chart_snapshot": "[1] (2026-01-02) Visit -- Adult outpatient\n[2] (2026-01-02) Finding -- Weight: 71 kg\n",
    "mappings": [
        {"index": 1, "resourceType": "visit", "resourceUuid": "visit-1"},
        {"index": 2, "resourceType": "obs", "resourceUuid": "obs-1"},
    ],
}


def test_fixture_refresh_takes_the_hubs_ledger_and_preserves_curated_identity():
    original = {
        "slug": "patient-a",
        "patient": {"uuid": "patient-1", "birthdate": "1990-01-01"},
        "chart_snapshot": "stale",
        "mappings": [],
    }

    refreshed = CAPTURE.updated_fixture(original, LEDGER, captured_at="2026-07-12T00:00:00+00:00")

    assert refreshed["slug"] == "patient-a"
    assert refreshed["patient"] == original["patient"]
    assert refreshed["chart_snapshot"] == LEDGER["chart_snapshot"]
    assert refreshed["valid_uuids"] == ["obs-1", "visit-1"]
    assert refreshed["provenance"]["resource_types"] == {"obs": 1, "visit": 1}
    assert refreshed["provenance"]["med_agent_hub_commit"] == "a" * 40
    assert refreshed["provenance"]["querystore_snapshot_id"] == "snap-1"


def _fixture(tmp_path, patient):
    path = tmp_path / f"{patient}.json"
    path.write_text(
        json.dumps({"slug": patient, "patient": {"uuid": patient}, "chart_snapshot": "original", "mappings": []}),
        encoding="utf-8",
    )
    return path


def test_all_fixture_capture_writes_nothing_when_a_patient_has_no_ledger(tmp_path, monkeypatch):
    fixtures = [_fixture(tmp_path, "p1"), _fixture(tmp_path, "p2")]
    before = [path.read_text(encoding="utf-8") for path in fixtures]
    monkeypatch.setattr(CAPTURE, "_fixture_paths", lambda *_args: fixtures)
    monkeypatch.setattr(CAPTURE, "hub_ledgers", lambda patients, _container: {"p1": {**LEDGER, "patient": "p1"}})

    assert CAPTURE.main(["--all"]) == 1
    assert [path.read_text(encoding="utf-8") for path in fixtures] == before


def test_successful_fixture_capture_replaces_staged_file_atomically(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, "p1")
    monkeypatch.setattr(CAPTURE, "ROOT", tmp_path)
    monkeypatch.setattr(CAPTURE, "_fixture_paths", lambda *_args: [fixture])
    monkeypatch.setattr(CAPTURE, "hub_ledgers", lambda patients, _container: {"p1": {**LEDGER, "patient": "p1"}})
    replacements = []
    real_replace = CAPTURE.os.replace

    def replace(source, destination):
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(CAPTURE.os, "replace", replace)

    assert CAPTURE.main(["--all"]) == 0
    assert replacements == [(tmp_path / ".p1.json.tmp", fixture)]
    assert json.loads(fixture.read_text())["valid_uuids"] == ["obs-1", "visit-1"]


def test_verify_corpus_cli_reports_matching_live_ledger(monkeypatch, capsys):
    expected = {"p1": {"chart_snapshot": LEDGER["chart_snapshot"], "mappings": LEDGER["mappings"]}}
    monkeypatch.setattr(VERIFY_CORPUS, "expected_ledgers", lambda *_args: expected)
    monkeypatch.setattr(VERIFY_CORPUS, "hub_ledgers", lambda patients, _container: {"p1": LEDGER})
    monkeypatch.setattr(VERIFY_CORPUS, "alignment_issues", lambda *_args: [])
    monkeypatch.setattr(VERIFY_CORPUS.sys, "argv", ["verify-validation-corpus.py", "--set", "set"])

    assert VERIFY_CORPUS.main() == 0
    assert "p1: 2 exact fixture/live records" in capsys.readouterr().out


def test_verify_corpus_cli_reports_alignment_issues(monkeypatch, capsys):
    monkeypatch.setattr(VERIFY_CORPUS, "expected_ledgers", lambda *_args: {"p1": {"chart_snapshot": "x", "mappings": []}})
    monkeypatch.setattr(VERIFY_CORPUS, "hub_ledgers", lambda patients, _container: {"p1": LEDGER})
    monkeypatch.setattr(VERIFY_CORPUS, "alignment_issues", lambda *_args: ["p1: rendered chart text differs"])
    monkeypatch.setattr(VERIFY_CORPUS.sys, "argv", ["verify-validation-corpus.py", "--set", "set"])

    assert VERIFY_CORPUS.main() == 1
    assert "p1: rendered chart text differs" in capsys.readouterr().out


def _hub_ledger_module():
    spec = importlib.util.spec_from_file_location("hub_ledger", ROOT / "scripts" / "hub_ledger.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hub_ledgers_run_the_hubs_querystore_export_in_its_container(monkeypatch):
    module = _hub_ledger_module()
    calls = []

    class Done:
        returncode = 0
        stdout = json.dumps({**LEDGER, "patient": "p1"}) + "\n" + json.dumps({**LEDGER, "patient": "p2"}) + "\n"
        stderr = ""

    def run(command, **_kwargs):
        calls.append(command)
        return Done()

    monkeypatch.setattr(module.subprocess, "run", run)

    ledgers = module.hub_ledgers(["p1", "p2"], "hub")
    assert sorted(ledgers) == ["p1", "p2"]
    assert calls == [["docker", "exec", "hub", "python", "-m", "server.querystore_export",
                      "--patient", "p1", "--patient", "p2"]]


def test_hub_ledgers_report_the_hubs_error(monkeypatch):
    module = _hub_ledger_module()

    class Failed:
        returncode = 1
        stdout = ""
        stderr = "ERROR: QueryStore is not configured in this Hub"

    monkeypatch.setattr(module.subprocess, "run", lambda *_a, **_k: Failed())
    with pytest.raises(RuntimeError, match="not configured"):
        module.hub_ledgers(["p1"], "hub")
