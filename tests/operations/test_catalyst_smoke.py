from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("catalyst_smoke", ROOT / "scripts" / "catalyst-smoke.py")
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


READY = {"status": "ready", "checks": {"catalyst": {"ready": True}, "hub": {"ready": True}}}
OPTIONS = {
    "contractVersion": "catalyst.query-options.v1",
    "defaultProfileId": "catalyst-query-e4b-qwen14b",
    "profiles": [
        {"id": "catalyst-query-e4b-qwen14b", "available": True},
        {"id": "catalyst-query-qwen-coder-1.5b", "available": False},
    ],
}
PREVIEW = {
    "contractVersion": "catalyst.preview.v1",
    "previewId": "preview-1",
    "queryDigest": "digest-1",
    "sql": "SELECT count(*) AS patients FROM clinlims.patient",
    "state": "awaiting_acceptance",
}
TABLE = {
    "contractVersion": "catalyst.table.v1",
    "table": {"columns": [{"name": "patients"}], "rows": [[1]], "rowCount": {"returned": 1, "total": 1}},
    "source": {"id": "openelis"},
}


def _gateway(monkeypatch, responses):
    calls = []
    replies = iter(responses)

    def call(method, url, payload, timeout):
        calls.append((method, url, payload))
        return next(replies)

    monkeypatch.setattr(smoke, "_call", call)
    return calls


def test_a_question_becomes_sql_that_runs_and_returns_rows(monkeypatch):
    # The gateway answers a question with 201 Created and its preview.
    calls = _gateway(monkeypatch, [(200, READY), (200, OPTIONS), (201, PREVIEW), (200, TABLE)])

    result = smoke.smoke("http://gateway/", question="How many patients are there?", profile=None, timeout=30)

    assert result["profile"] == "catalyst-query-e4b-qwen14b"
    assert result["sql"] == PREVIEW["sql"]
    assert result["row_count"] == 1
    assert result["columns"] == ["patients"]
    assert [(m, u) for m, u, _ in calls] == [
        ("GET", "http://gateway/health"),
        ("GET", "http://gateway/v1/catalyst/query-options"),
        ("POST", "http://gateway/v1/catalyst/queries"),
        ("POST", "http://gateway/v1/catalyst/previews/preview-1/execute"),
    ]
    assert calls[2][2] == {
        "contractVersion": "catalyst.question.request.v1",
        "deploymentMode": "demo",
        "profileId": "catalyst-query-e4b-qwen14b",
        "question": "How many patients are there?",
    }
    execute = calls[3][2]
    assert execute["previewId"] == "preview-1" and execute["queryDigest"] == "digest-1"
    assert execute["accept"] is True and execute["idempotencyKey"].startswith("smoke-")


def test_a_gateway_that_is_not_ready_stops_the_smoke_and_names_the_failing_checks(monkeypatch):
    calls = _gateway(
        monkeypatch,
        [(503, {"status": "not_ready", "checks": {"catalyst": {"ready": True}, "analytics": {"ready": False}}})],
    )

    with pytest.raises(RuntimeError, match=r"not ready: \['analytics'\]"):
        smoke.smoke("http://gateway", question="q", profile=None, timeout=30)
    assert len(calls) == 1


def test_an_unavailable_profile_stops_the_smoke_before_any_question(monkeypatch):
    calls = _gateway(monkeypatch, [(200, READY), (200, OPTIONS)])

    with pytest.raises(RuntimeError, match="is not available"):
        smoke.smoke("http://gateway", question="q", profile="catalyst-query-qwen-coder-1.5b", timeout=30)
    assert len(calls) == 2


def test_a_profile_the_gateway_does_not_offer_is_refused(monkeypatch):
    _gateway(monkeypatch, [(200, READY), (200, OPTIONS)])

    with pytest.raises(RuntimeError, match="not offered"):
        smoke.smoke("http://gateway", question="q", profile="missing", timeout=30)


def test_a_question_that_ends_without_runnable_sql_fails_the_smoke(monkeypatch):
    clarification = {
        "contractVersion": "catalyst.query.v1",
        "status": "needs_clarification",
        "message": "Which patients do you mean?",
    }
    _gateway(monkeypatch, [(200, READY), (200, OPTIONS), (200, clarification)])

    with pytest.raises(RuntimeError, match="did not produce runnable SQL: status 'needs_clarification': Which patients do you mean"):
        smoke.smoke("http://gateway", question="q", profile=None, timeout=30)


def test_a_hub_failure_on_the_question_fails_the_smoke_with_its_code(monkeypatch):
    _gateway(
        monkeypatch,
        [(200, READY), (200, OPTIONS), (502, {"error": {"code": "hub_unavailable", "message": "connection refused"}})],
    )

    with pytest.raises(RuntimeError, match=r"failed \(502\): hub_unavailable: connection refused"):
        smoke.smoke("http://gateway", question="q", profile=None, timeout=30)


def test_sql_that_fails_to_run_fails_the_smoke(monkeypatch):
    failed = {"contractVersion": "catalyst.execution.outcome.v1", "status": "failed", "message": "relation does not exist"}
    _gateway(monkeypatch, [(200, READY), (200, OPTIONS), (200, PREVIEW), (200, failed)])

    with pytest.raises(RuntimeError, match="did not run.*relation does not exist"):
        smoke.smoke("http://gateway", question="q", profile=None, timeout=30)


def test_sql_that_returns_no_rows_fails_the_smoke(monkeypatch):
    empty = {**TABLE, "table": {"columns": [], "rows": [], "rowCount": {"returned": 0, "total": 0}}}
    _gateway(monkeypatch, [(200, READY), (200, OPTIONS), (200, PREVIEW), (200, empty)])

    with pytest.raises(RuntimeError, match="returned no rows"):
        smoke.smoke("http://gateway", question="q", profile=None, timeout=30)


def test_the_cli_targets_the_umbrella_gateway_port_and_writes_the_result(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.delenv("GATEWAY_PORT", raising=False)
    monkeypatch.setattr(
        smoke, "smoke", lambda url, **kwargs: calls.append((url, kwargs)) or {"schema_version": "catalyst_smoke.v1"}
    )
    output = tmp_path / "smoke.json"
    monkeypatch.setattr(sys, "argv", ["catalyst-smoke.py", "--output", str(output)])

    assert smoke.main() == 0
    assert calls == [("http://127.0.0.1:18000", {"question": smoke.DEFAULT_QUESTION, "profile": None, "timeout": 300})]
    assert json.loads(output.read_text(encoding="utf-8")) == {"schema_version": "catalyst_smoke.v1"}
    assert json.loads(capsys.readouterr().out) == {"schema_version": "catalyst_smoke.v1"}
