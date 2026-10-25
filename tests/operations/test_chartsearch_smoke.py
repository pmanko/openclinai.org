from __future__ import annotations

import importlib.util
import json
import sys
import urllib.parse
from email.message import Message
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "chartsearch_smoke", ROOT / "scripts" / "chartsearch-smoke.py"
)
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class FakeResponse:
    def __init__(self, body: bytes | list[bytes], headers: dict[str, str] | None = None):
        self._body = body
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def __iter__(self):
        assert isinstance(self._body, list)
        return iter(self._body)

    def read(self):
        assert isinstance(self._body, bytes)
        return self._body


def _sse(events):
    chunks: list[bytes] = []
    for name, payload in events:
        data = payload if isinstance(payload, str) else json.dumps(payload)
        chunks.extend([f"event: {name}\n".encode(), f"data: {data}\n".encode(), b"\n"])
    return chunks


def _answer(**overrides):
    payload = {
        "session": "session-1",
        "messageId": "message-1",
        "provider": "hub",
        "model": "single-12b-checked",
        "answer": "The most recent visit was an OPD visit on 2026-01-26 [1].",
        "answerValidation": {"status": "checking"},
        "references": [{"index": 1, "resolutionStatus": "resolved", "groundingStatus": "checking"}],
    }
    payload.update(overrides)
    return payload


def _final(**overrides):
    """A checked Answer with a verified citation, plus an In-Depth claim the checks
    marked unsupported: what the Hub returns when a claim says more than its record."""
    payload = _answer(
        answerValidation={"status": "checked", "label": "Checked"},
        references=[
            {
                "index": 1,
                "source": "querystore",
                "resolutionStatus": "resolved",
                "groundingStatus": "verified",
                "usage": [{"location": "answer", "text": "the visit"}],
            },
            {
                "index": 14,
                "source": "querystore",
                "resolutionStatus": "resolved",
                "groundingStatus": "unsupported",
                "usage": [{"location": "indepth", "text": "a baseline"}],
            },
        ],
        inDepth={"status": "complete", "answer": "The visit also recorded 93% [14]."},
    )
    payload.update(overrides)
    return payload


def _turn(final, *, turn_done=None, pending=True):
    events = [("turn_started", {}), ("heartbeat", {"elapsedMs": 500}), ("answer_done", _answer())]
    events.append(("answer_validation", final))
    if pending:
        events.append(("indepth_pending", {**final, "inDepth": {"status": "pending", "answer": ""}}))
    events.append(("heartbeat", {"elapsedMs": 2000}))
    events.append(("indepth_done", final))
    events.append(("turn_done", turn_done or {"session": "session-1", "messageId": "message-1", "provider": "hub"}))
    return _sse(events)


def _stream(monkeypatch, chunks):
    monkeypatch.setattr(
        smoke.urllib.request, "urlopen", lambda *_args, **_kwargs: FakeResponse(chunks)
    )
    return smoke._stream_turn(
        "http://openmrs/chat/stream",
        patient="patient-1",
        provider="hub",
        profile="single-12b-checked",
        question="Latest visit?",
        session="session-1",
        username="eval-doctor",
        password="secret",
        timeout=30,
    )


def test_smoke_logs_in_finds_the_patient_asks_and_reads_the_stored_answer(monkeypatch):
    final = _final()
    history = {
        "session": "session-1",
        "messages": [{"messageId": "message-1", "role": "assistant", "content": final["answer"]}],
    }
    responses = iter(
        [
            FakeResponse(json.dumps({"authenticated": True, "user": {"display": "eval-doctor"}}).encode()),
            FakeResponse(json.dumps({"uuid": "patient-1", "display": "2428TU-4 - Sample Patient"}).encode()),
            FakeResponse(json.dumps({"session": "session-1", "provider": "hub"}).encode()),
            FakeResponse(_turn(final)),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(json.dumps({"session": "session-2", "provider": "hub"}).encode()),
        ]
    )
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return next(responses)

    monkeypatch.setattr(smoke.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(smoke, "_runtime_identity", lambda _url: {"deployment": {"revision": "hub-sha"}})

    result = smoke.smoke(
        "http://openmrs/openmrs",
        patient="patient-1",
        provider="hub",
        profile="single-12b-checked",
        question="Latest visit?",
        username="eval-doctor",
        password="secret",
        timeout=30,
        clear_after=True,
    )

    assert result["schema_version"] == "chartsearchai_smoke.v1"
    assert result["patient_display"] == "2428TU-4 - Sample Patient"
    assert result["answer"] == final["answer"]
    assert result["answer_validation"] == "checked"
    assert result["answer_citations"] == 1
    assert result["reference_count"] == 2
    assert result["in_depth_status"] == "complete"
    assert result["events"] == [
        "turn_started", "answer_done", "answer_validation", "indepth_pending", "indepth_done", "turn_done",
    ]
    assert result["stored"] is True and result["cleared_after"] is True
    assert result["runtime_identity"]["deployment"]["revision"] == "hub-sha"
    assert [r.full_url for r in requests] == [
        "http://openmrs/openmrs/ws/rest/v1/session",
        "http://openmrs/openmrs/ws/rest/v1/patient/patient-1?v=default",
        "http://openmrs/openmrs/ws/rest/v1/chartsearchai/chat/new",
        "http://openmrs/openmrs/ws/rest/v1/chartsearchai/chat/stream",
        "http://openmrs/openmrs/ws/rest/v1/chartsearchai/chat?patient=patient-1&session=session-1",
        "http://openmrs/openmrs/ws/rest/v1/chartsearchai/chat/new",
    ]
    assert all(r.get_header("Authorization") for r in requests)
    assert json.loads(requests[3].data) == {
        "patient": "patient-1",
        "provider": "hub",
        "profile": "single-12b-checked",
        "question": "Latest visit?",
        "session": "session-1",
    }


def test_an_in_depth_claim_the_checks_marked_unsupported_does_not_fail_the_smoke(monkeypatch):
    result = _stream(monkeypatch, _turn(_final()))

    assert result["answer_citations"] == 1
    assert result["reference_count"] == 2


def test_an_answer_citation_that_does_not_resolve_fails_the_smoke(monkeypatch):
    final = _final()
    final["references"][0]["resolutionStatus"] = "unresolved"
    final["references"][0]["groundingStatus"] = "unchecked"

    with pytest.raises(RuntimeError, match=r"did not resolve to records: \[1\]"):
        _stream(monkeypatch, _turn(final))


def test_an_answer_that_cites_nothing_fails_the_smoke(monkeypatch):
    with pytest.raises(RuntimeError, match="cites no record"):
        _stream(monkeypatch, _turn(_final(references=[])))


def test_answer_citations_fall_back_to_every_reference_without_usage():
    references = [{"index": 1, "resolutionStatus": "resolved"}, {"index": 2, "resolutionStatus": "resolved"}]

    assert smoke.answer_citations({"references": references}) == references


def test_an_error_event_fails_the_smoke_with_its_text(monkeypatch):
    with pytest.raises(RuntimeError, match="context source unavailable"):
        _stream(monkeypatch, _sse([("error", "context source unavailable")]))


def test_a_turn_error_fails_the_smoke_with_its_problem_code(monkeypatch):
    chunks = _sse(
        [("turn_started", {}), ("turn_error", {"error": "Patient context failed", "problemCode": "context_unavailable"})]
    )

    with pytest.raises(RuntimeError, match=r"context_unavailable.*Patient context failed"):
        _stream(monkeypatch, chunks)


def test_a_stream_that_ends_before_turn_done_fails_the_smoke(monkeypatch):
    with pytest.raises(RuntimeError, match="before turn_done"):
        _stream(monkeypatch, _turn(_final())[:-3])


def test_a_stream_without_an_answer_fails_the_smoke(monkeypatch):
    chunks = _sse([("turn_started", {}), ("turn_done", {"session": "session-1", "messageId": "message-1", "provider": "hub"})])

    with pytest.raises(RuntimeError, match="before answer_done"):
        _stream(monkeypatch, chunks)


@pytest.mark.parametrize(
    ("final_overrides", "turn_done", "message"),
    [
        ({"session": "session-2"}, None, "different session"),
        ({}, {"session": "session-1", "messageId": "message-2", "provider": "hub"}, "different assistant messages"),
        ({"provider": "bundled"}, None, "provider 'bundled', not 'hub'"),
    ],
)
def test_an_answer_for_another_session_message_or_provider_fails_the_smoke(
    monkeypatch, final_overrides, turn_done, message
):
    with pytest.raises(RuntimeError, match=message):
        _stream(monkeypatch, _turn(_final(**final_overrides), turn_done=turn_done))


def test_a_failed_login_stops_the_smoke_before_any_question(monkeypatch):
    monkeypatch.setattr(smoke, "_get_json", lambda *_args, **_kwargs: {"authenticated": False})
    monkeypatch.setattr(smoke, "_post_json", lambda *_args, **_kwargs: pytest.fail("no chat should start"))

    with pytest.raises(RuntimeError, match="eval-doctor could not log in"):
        smoke.smoke(
            "http://openmrs/openmrs", patient="patient-1", provider="hub", profile="p",
            question="Latest visit?", username="eval-doctor", password="secret", timeout=30, clear_after=False,
        )


def test_an_answer_missing_from_the_stored_chat_fails_the_smoke(monkeypatch):
    gets = iter(
        [{"authenticated": True}, {"display": "Sample Patient"}]
        + [{"session": "session-1", "messages": []}] * 10
    )
    monkeypatch.setattr(smoke, "_get_json", lambda *_args, **_kwargs: next(gets))
    monkeypatch.setattr(smoke, "_post_json", lambda *_args, **_kwargs: {"session": "session-1", "provider": "hub"})
    monkeypatch.setattr(smoke, "_stream_turn", lambda *_args, **_kwargs: {"message_id": "message-1", "answer": "A [1]."})
    monkeypatch.setattr(smoke.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="not stored in the chat session"):
        smoke.smoke(
            "http://openmrs/openmrs", patient="patient-1", provider="hub", profile="p",
            question="Latest visit?", username="eval-doctor", password="secret", timeout=30, clear_after=False,
        )


def test_the_default_profile_is_the_one_advertised_product_default(monkeypatch):
    calls = []

    def get_json(url, **kwargs):
        calls.append((url, kwargs))
        return {"data": [{"id": "hub-default", "visibility": "product", "available": True, "default": True}]}

    monkeypatch.setattr(smoke, "_get_json", get_json)

    assert smoke.discover_default_profile(
        "http://openmrs/openmrs", username="admin", password="secret", timeout=9
    ) == "hub-default"
    assert calls == [
        ("http://openmrs/openmrs/ws/rest/v1/chartsearchai/models", {"username": "admin", "password": "secret", "timeout": 9})
    ]


def test_two_advertised_defaults_are_refused(monkeypatch):
    monkeypatch.setattr(
        smoke,
        "_get_json",
        lambda *_args, **_kwargs: {
            "data": [
                {"id": profile, "visibility": "product", "available": True, "default": True}
                for profile in ("one", "two")
            ]
        },
    )

    with pytest.raises(RuntimeError, match="exactly one available default product profile"):
        smoke.discover_default_profile("http://openmrs/openmrs", username="admin", password="secret", timeout=9)


def test_the_cli_asks_about_the_sample_patient_with_the_advertised_default(tmp_path, monkeypatch, capsys):
    result = {"schema_version": "chartsearchai_smoke.v1"}
    calls = []
    monkeypatch.setattr(
        smoke, "discover_default_profile",
        lambda openmrs_url, **kwargs: calls.append(("discover", openmrs_url, kwargs)) or "single-12b-checked",
    )
    monkeypatch.setattr(
        smoke, "smoke", lambda openmrs_url, **kwargs: calls.append(("smoke", openmrs_url, kwargs)) or result
    )
    output = tmp_path / "smoke.json"
    monkeypatch.setattr(sys, "argv", ["chartsearch-smoke.py", "--output", str(output), "--clear-after"])

    assert smoke.main() == 0
    assert calls[0] == (
        "discover", "http://127.0.0.1:8088/openmrs", {"username": "admin", "password": "Admin123", "timeout": 300},
    )
    assert calls[1][1] == "http://127.0.0.1:8088/openmrs"
    assert calls[1][2]["patient"] == smoke.SAMPLE_PATIENT
    assert calls[1][2]["profile"] == "single-12b-checked"
    assert calls[1][2]["clear_after"] is True
    assert json.loads(output.read_text(encoding="utf-8")) == result
    assert json.loads(capsys.readouterr().out) == result


def test_the_cli_can_check_runtime_identity_without_a_question(tmp_path, monkeypatch, capsys):
    identity = {"deployment": {"revision": "hub-commit"}}
    output = tmp_path / "identity" / "runtime.json"
    monkeypatch.setattr(smoke, "_runtime_identity", lambda _url: identity)
    monkeypatch.setattr(smoke, "smoke", lambda *_args, **_kwargs: pytest.fail("no question should be asked"))
    monkeypatch.setattr(sys, "argv", ["chartsearch-smoke.py", "--identity-only", "--output", str(output)])

    assert smoke.main() == 0
    expected = {"schema_version": "chartsearchai_runtime_identity.v1", "runtime_identity": identity}
    assert json.loads(output.read_text(encoding="utf-8")) == expected
    assert json.loads(capsys.readouterr().out) == expected


def test_artifact_content_rejects_missing_path(tmp_path):
    with pytest.raises(RuntimeError, match="artifact does not exist"):
        smoke._artifact_content(tmp_path / "missing")


def test_runtime_identity_binds_built_and_deployed_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    chartsearchai = tmp_path / "targets" / "chartsearchai"
    querystore = tmp_path / "targets" / "querystore"
    esm_repo = tmp_path / "targets" / "chartsearchai-esm"
    hub_repo = tmp_path / "targets" / "med-agent-hub"
    for repo in (chartsearchai, querystore, esm_repo, hub_repo):
        repo.mkdir(parents=True)

    omod = tmp_path / "artifacts/openmrs/modules/chartsearchai-1.0.0-SNAPSHOT.omod"
    omod.parent.mkdir(parents=True)
    omod.write_bytes(b"omod")
    querystore_omod = tmp_path / "artifacts/openmrs/modules/querystore-1.0.0-SNAPSHOT.omod"
    querystore_omod.write_bytes(b"querystore-omod")
    esm = tmp_path / "artifacts/openmrs/spa-custom"
    esm.mkdir(parents=True)
    (esm / "app.js").write_bytes(b"esm")

    def write_provenance(repo, artifact, path):
        content = smoke._artifact_content(artifact)
        payload = {
            "source_commit": f"{repo.name}-commit",
            "source_tree": "tree-sha",
            "source_tree_clean": True,
            "artifact_kind": content["kind"],
            "artifact_sha256": content["sha256"],
            "artifact_size_bytes": content["size_bytes"],
            "artifact_files": content.get("files"),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    omod_manifest = (
        tmp_path / "artifacts/chartsearchai-local/module-provenance/chartsearchai-1.0.0-SNAPSHOT.omod.provenance.json"
    )
    omod_provenance = write_provenance(chartsearchai, omod, omod_manifest)
    deployed_manifest = tmp_path / "artifacts/chartsearchai-local/deployed-chartsearchai-omod.json"
    deployed_manifest.parent.mkdir(parents=True, exist_ok=True)
    deployed_manifest.write_text(json.dumps(omod_provenance), encoding="utf-8")
    querystore_manifest = (
        tmp_path / "artifacts/chartsearchai-local/module-provenance/querystore-1.0.0-SNAPSHOT.omod.provenance.json"
    )
    querystore_provenance = write_provenance(querystore, querystore_omod, querystore_manifest)
    deployed_querystore_manifest = tmp_path / "artifacts/chartsearchai-local/deployed-querystore-omod.json"
    deployed_querystore_manifest.write_text(json.dumps(querystore_provenance), encoding="utf-8")
    (esm / "importmap.json").write_text(
        json.dumps(
            {
                "imports": {
                    "@openmrs/esm-chartsearchai-app": (
                        "./openmrs-esm-chartsearchai-app-multiturn/openmrs-esm-chartsearchai-app.js"
                    )
                }
            }
        ),
        encoding="utf-8",
    )
    esm_manifest = tmp_path / "artifacts/openmrs/chartsearchai-esm.provenance.json"
    write_provenance(esm_repo, esm, esm_manifest)
    (hub_repo / "server").mkdir()
    (hub_repo / "server/levels.yaml").write_text("profiles: {}\n", encoding="utf-8")
    (tmp_path / "compose").mkdir()
    (tmp_path / "compose/openmrs-2.8-refapp.yml").write_text("services: {}\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/chartsearch-configure.sh").write_text("#!/bin/sh\n")

    monkeypatch.setattr(
        smoke, "_git_identity", lambda repo: {"commit": f"{repo.name}-commit", "tree_clean": True}
    )

    hub_revision = ["med-agent-hub-commit"]

    def check_output(args, **_kwargs):
        if args[:3] == ["git", "rev-parse", "HEAD^{tree}"]:
            return "tree-sha\n"
        if args[:2] == ["docker", "inspect"]:
            return json.dumps([{"Id": "container-id", "Image": "sha256:image"}])
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps(
                [{"Config": {"Labels": {"org.opencontainers.image.revision": hub_revision[0]}}}]
            )
        if args[:2] == ["docker", "exec"]:
            mounted = querystore_omod if "querystore" in args[-1] else omod
            return f"{smoke._sha256(mounted)}  {mounted.name}\n"
        raise AssertionError(args)

    monkeypatch.setattr(smoke.subprocess, "check_output", check_output)

    def urlopen(url, **_kwargs):
        relative = urllib.parse.unquote(url.rsplit("/spa/", 1)[1])
        return FakeResponse((esm / relative).read_bytes())

    monkeypatch.setattr(smoke.urllib.request, "urlopen", urlopen)

    identity = smoke._runtime_identity("http://openmrs/openmrs")

    assert identity["deployment"] == {
        "container_id": "container-id",
        "image_id": "sha256:image",
        "revision": "med-agent-hub-commit",
    }
    assert identity["artifacts"]["chartsearchai_omod"]["mounted_sha256"] == smoke._sha256(omod)
    assert identity["querystore"] == {"commit": "querystore-commit", "tree_clean": True}
    assert identity["artifacts"]["querystore_omod"]["mounted_sha256"] == smoke._sha256(querystore_omod)
    assert identity["artifacts"]["querystore_omod"]["deployed_provenance_path"] == (
        "artifacts/chartsearchai-local/deployed-querystore-omod.json"
    )
    assert identity["artifacts"]["chartsearchai_esm"]["served_files"] == {
        "app.js": smoke._sha256(esm / "app.js"),
        "importmap.json": smoke._sha256(esm / "importmap.json"),
    }

    hub_revision[0] = "stale-hub-commit"
    with pytest.raises(RuntimeError, match="running med-agent-hub image"):
        smoke._runtime_identity("http://openmrs/openmrs")
