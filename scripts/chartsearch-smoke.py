#!/usr/bin/env python3
"""Smoke the local ChartSearchAI stack: the deployed artifacts are the pinned builds,
an evaluation account can log in, the sample patient is loaded, and one question
through the configured provider comes back as an Answer whose citations resolve.

It is the acceptance step after setup and after a component pin moves. It needs the
local stack and model, so it is not a CI test. What the provider puts inside the
answer envelope (claim labels, In-Depth state, review verdicts) is the provider's
contract and is tested in the Hub; this smoke only checks that the stack delivers
an answer end to end.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATIENT = "dd75c020-1691-11df-97a5-7038c432aabf"
DEFAULT_QUESTION = "In one short sentence, what was the most recent documented clinical visit?"
TERMINAL_EVENTS = ("answer_done", "answer_validation", "indepth_done", "indepth_error")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_content(path: Path) -> dict[str, Any]:
    if path.is_file():
        return {"kind": "file", "sha256": _sha256(path), "size_bytes": path.stat().st_size}
    if not path.is_dir():
        raise RuntimeError(f"artifact does not exist: {path}")
    files = [
        {
            "path": str(item.relative_to(path)),
            "sha256": _sha256(item),
            "size_bytes": item.stat().st_size,
        }
        for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    ]
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {
        "kind": "directory",
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": sum(item["size_bytes"] for item in files),
        "files": files,
    }


def _git_identity(path: Path) -> dict[str, Any]:
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=path, text=True
        ).strip(),
        "tree_clean": not bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=path,
                text=True,
            ).strip()
        ),
    }


def _artifact_identity(
    name: str,
    repo: Path,
    artifact: Path,
    manifest: Path,
) -> dict[str, Any]:
    if not artifact.exists() or not manifest.is_file():
        raise RuntimeError(f"{name} artifact or provenance is missing")
    provenance = json.loads(manifest.read_text(encoding="utf-8"))
    identity = _git_identity(repo)
    content = _artifact_content(artifact)
    source_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True
    ).strip()
    if provenance.get("source_commit") != identity["commit"]:
        raise RuntimeError(f"{name} provenance does not match the current commit")
    if provenance.get("source_tree") != source_tree:
        raise RuntimeError(f"{name} provenance does not match the current source tree")
    if provenance.get("artifact_kind") != content["kind"]:
        raise RuntimeError(f"{name} provenance has the wrong artifact kind")
    if provenance.get("artifact_sha256") != content["sha256"]:
        raise RuntimeError(f"{name} provenance does not match the staged artifact")
    if provenance.get("artifact_size_bytes") != content["size_bytes"]:
        raise RuntimeError(f"{name} provenance has the wrong artifact size")
    if provenance.get("artifact_files") != content.get("files"):
        raise RuntimeError(f"{name} provenance does not match the staged artifact files")
    return {
        "path": str(artifact.relative_to(ROOT)),
        "kind": content["kind"],
        "sha256": content["sha256"],
        "size_bytes": content["size_bytes"],
        **({"files": content["files"]} if content["kind"] == "directory" else {}),
        "provenance_path": str(manifest.relative_to(ROOT)),
        "provenance": provenance,
    }


def _runtime_identity(openmrs_url: str) -> dict[str, Any]:
    container = json.loads(
        subprocess.check_output(
            ["docker", "inspect", "harness-med-agent-hub"], text=True
        )
    )[0]
    image_id = container["Image"]
    image = json.loads(
        subprocess.check_output(["docker", "image", "inspect", image_id], text=True)
    )[0]
    labels = (image.get("Config") or {}).get("Labels") or {}
    artifact_specs = {
        "chartsearchai_omod": (
            ROOT / "targets/chartsearchai",
            ROOT / "artifacts/openmrs/modules/chartsearchai-1.0.0-SNAPSHOT.omod",
            ROOT
            / "artifacts/chartsearchai-local/module-provenance/"
            "chartsearchai-1.0.0-SNAPSHOT.omod.provenance.json",
        ),
        "querystore_omod": (
            ROOT / "targets/querystore",
            ROOT / "artifacts/openmrs/modules/querystore-1.0.0-SNAPSHOT.omod",
            ROOT
            / "artifacts/chartsearchai-local/module-provenance/"
            "querystore-1.0.0-SNAPSHOT.omod.provenance.json",
        ),
        "chartsearchai_esm": (
            ROOT / "targets/chartsearchai-esm",
            ROOT / "artifacts/openmrs/spa-custom",
            ROOT / "artifacts/openmrs/chartsearchai-esm.provenance.json",
        ),
    }
    artifacts = {
        name: _artifact_identity(name, repo, artifact, manifest)
        for name, (repo, artifact, manifest) in artifact_specs.items()
    }
    module_specs = {
        "chartsearchai_omod": (
            ROOT / "artifacts/chartsearchai-local/deployed-chartsearchai-omod.json",
            "/openmrs/data/modules/chartsearchai-1.0.0-SNAPSHOT.omod",
        ),
        "querystore_omod": (
            ROOT / "artifacts/chartsearchai-local/deployed-querystore-omod.json",
            "/openmrs/data/modules/querystore-1.0.0-SNAPSHOT.omod",
        ),
    }
    for name, (deployed_manifest, mounted_path) in module_specs.items():
        if not deployed_manifest.is_file():
            raise RuntimeError(f"deployed {name} provenance is missing")
        if json.loads(deployed_manifest.read_text()) != artifacts[name]["provenance"]:
            raise RuntimeError(f"deployed {name} provenance is stale")
        mounted_sha256 = subprocess.check_output(
            [
                "docker",
                "exec",
                "harness-openmrs-backend",
                "sha256sum",
                mounted_path,
            ],
            text=True,
        ).split()[0]
        if mounted_sha256 != artifacts[name]["sha256"]:
            raise RuntimeError(f"mounted {name} differs from the staged artifact")
        artifacts[name]["mounted_sha256"] = mounted_sha256
        artifacts[name]["deployed_provenance_path"] = str(
            deployed_manifest.relative_to(ROOT)
        )
    esm = artifacts["chartsearchai_esm"]
    served_files: dict[str, str] = {}
    for item in esm.get("files") or []:
        relative = item["path"]
        served_url = f"{openmrs_url.rstrip('/')}/spa/{urllib.parse.quote(relative)}"
        with urllib.request.urlopen(served_url, timeout=30) as response:
            served_sha256 = hashlib.sha256(response.read()).hexdigest()
        if served_sha256 != item["sha256"]:
            raise RuntimeError(f"served ChartSearchAI ESM asset differs: {relative}")
        served_files[relative] = served_sha256
    importmap_path = ROOT / "artifacts/openmrs/spa-custom/importmap.json"
    importmap = json.loads(importmap_path.read_text(encoding="utf-8"))
    import_target = (importmap.get("imports") or {}).get("@openmrs/esm-chartsearchai-app")
    expected_target = "./openmrs-esm-chartsearchai-app-multiturn/openmrs-esm-chartsearchai-app.js"
    if import_target != expected_target:
        raise RuntimeError("served ChartSearchAI import-map target is not the staged bundle")
    artifacts["chartsearchai_esm"]["import_map_target"] = import_target
    artifacts["chartsearchai_esm"]["served_files"] = served_files
    source_revisions = {
        "workspace": _git_identity(ROOT),
                "harness": _git_identity(ROOT / "targets/validation-harness"),
        "med_agent_hub": _git_identity(ROOT / "targets/med-agent-hub"),
        "chartsearchai": _git_identity(ROOT / "targets/chartsearchai"),
        "chartsearchai_esm": _git_identity(ROOT / "targets/chartsearchai-esm"),
        "querystore": _git_identity(ROOT / "targets/querystore"),
    }
    deployed_hub_revision = labels.get("org.opencontainers.image.revision")
    if deployed_hub_revision != source_revisions["med_agent_hub"]["commit"]:
        raise RuntimeError("running med-agent-hub image does not match the pinned source")
    return {
        **source_revisions,
        "deployment": {
            "container_id": container["Id"],
            "image_id": image_id,
            "revision": deployed_hub_revision,
        },
        "artifacts": artifacts,
        "configuration": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
            for name, path in {
                "hub_profiles": ROOT / "targets/med-agent-hub/server/levels.yaml",
                "compose": ROOT / "compose/openmrs-2.8-refapp.yml",
                "relay_configuration": ROOT / "scripts/chartsearch-configure.sh",
            }.items()
        },
    }

def _request(
    url: str,
    *,
    username: str,
    password: str,
    payload: dict[str, Any] | None = None,
    accept: str = "application/json",
) -> urllib.request.Request:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {"Accept": accept, "Authorization": f"Basic {token}"}
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
        method = "POST"
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def _get_json(url: str, *, username: str, password: str, timeout: int) -> dict[str, Any]:
    request = _request(url, username=username, password=password)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _post_json(
    url: str,
    payload: dict[str, Any],
    *,
    username: str,
    password: str,
    timeout: int,
) -> dict[str, Any]:
    request = _request(url, username=username, password=password, payload=payload)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    return json.loads(body) if body else {}


def discover_default_profile(
    openmrs_url: str,
    *,
    username: str,
    password: str,
    timeout: int,
) -> str:
    api = f"{openmrs_url.rstrip('/')}/ws/rest/v1/chartsearchai"
    payload = _get_json(f"{api}/models", username=username, password=password, timeout=timeout)
    defaults = [
        item
        for item in payload.get("data", [])
        if item.get("visibility") == "product"
        and item.get("available") is True
        and item.get("default") is True
    ]
    if len(defaults) != 1 or not str(defaults[0].get("id") or "").strip():
        raise RuntimeError(
            "hub must advertise exactly one available default product profile; "
            f"found {defaults!r}"
        )
    return str(defaults[0]["id"])


def answer_citations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """The references the Answer itself cites.

    A reference says where it is used in `usage`; one used only in the In-Depth is
    the In-Depth's and carries the label the provider's checks gave it. Without any
    usage information every reference counts as the Answer's.
    """
    references = [r for r in (payload.get("references") or []) if isinstance(r, dict)]
    if not any(r.get("usage") for r in references):
        return references
    return [
        r
        for r in references
        if any(
            isinstance(u, dict) and u.get("location") in {"answer", "block"}
            for u in (r.get("usage") or [])
        )
    ]


def _stream_turn(
    stream_url: str,
    *,
    patient: str,
    provider: str,
    profile: str,
    question: str,
    session: str,
    username: str,
    password: str,
    timeout: int,
) -> dict[str, Any]:
    """Ask one question and return what the stack delivered.

    The stream must reach `turn_done` for the session it was asked in, with an
    Answer whose citations all resolve to records. Heartbeats and the provider's
    intermediate phases are recorded, not judged.
    """
    payload = {
        "patient": patient,
        "provider": provider,
        "profile": profile,
        "question": question,
        "session": session,
    }
    request = _request(
        stream_url, username=username, password=password, payload=payload,
        accept="text/event-stream",
    )
    started = time.monotonic()
    event = ""
    data_lines: list[str] = []
    events: list[str] = []
    answer_done_ms: int | None = None
    final: dict[str, Any] | None = None
    turn_done: dict[str, Any] | None = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode(errors="replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                value = line.split(":", 1)[1]
                data_lines.append(value[1:] if value.startswith(" ") else value)
            elif line == "" and data_lines:
                data = "\n".join(data_lines)
                event_name, event, data_lines = event, "", []
                if not data.strip() or event_name == "heartbeat":
                    continue
                if event_name == "error":
                    raise RuntimeError(f"ChartSearchAI returned an error: {data}")
                payload = json.loads(data)
                if event_name == "turn_error":
                    code = str(payload.get("problemCode") or "unknown_error")
                    message = str(payload.get("error") or payload.get("message") or data)
                    raise RuntimeError(f"ChartSearchAI turn_error [{code}]: {message}")
                events.append(event_name)
                if event_name in TERMINAL_EVENTS:
                    final = payload
                    if event_name == "answer_done":
                        answer_done_ms = round((time.monotonic() - started) * 1000)
                if event_name == "turn_done":
                    turn_done = payload
                    break
    if final is None or answer_done_ms is None:
        raise RuntimeError("ChartSearchAI ended the turn before answer_done")
    if turn_done is None:
        raise RuntimeError("ChartSearchAI ended the stream before turn_done")
    answer = str(final.get("answer") or "").strip()
    if not answer:
        raise RuntimeError("the turn finished without an Answer")
    message_id = final.get("messageId")
    if not message_id or turn_done.get("messageId") != message_id:
        raise RuntimeError("answer and turn_done name different assistant messages")
    for phase, payload in (("answer", final), ("turn_done", turn_done)):
        if payload.get("session") not in {None, session}:
            raise RuntimeError(f"{phase} came back on a different session than requested")
        if payload.get("provider") != provider:
            raise RuntimeError(f"{phase} came from provider {payload.get('provider')!r}, not {provider!r}")
    citations = answer_citations(final)
    if not citations:
        raise RuntimeError("the Answer cites no record")
    unresolved = [c.get("index") for c in citations if c.get("resolutionStatus") != "resolved"]
    if unresolved:
        raise RuntimeError(f"Answer citations did not resolve to records: {unresolved}")
    return {
        "message_id": message_id,
        "profile": final.get("model") or final.get("resolvedModel"),
        "answer": answer,
        "answer_validation": (final.get("answerValidation") or {}).get("status"),
        "answer_citations": len(citations),
        "reference_count": len(final.get("references") or []),
        "in_depth_status": (final.get("inDepth") or {}).get("status"),
        "events": events,
        "answer_done_ms": answer_done_ms,
        "done_ms": round((time.monotonic() - started) * 1000),
    }


def smoke(
    openmrs_url: str,
    *,
    patient: str,
    provider: str,
    profile: str,
    question: str,
    username: str,
    password: str,
    timeout: int,
    clear_after: bool,
) -> dict[str, Any]:
    rest = f"{openmrs_url.rstrip('/')}/ws/rest/v1"
    api = f"{rest}/chartsearchai"
    session_info = _get_json(f"{rest}/session", username=username, password=password, timeout=timeout)
    if session_info.get("authenticated") is not True:
        raise RuntimeError(f"{username} could not log in to OpenMRS")
    record = _get_json(f"{rest}/patient/{patient}?v=default", username=username, password=password, timeout=timeout)
    if not str(record.get("display") or "").strip():
        raise RuntimeError(f"patient {patient} is not loaded")
    fresh = _post_json(
        f"{api}/chat/new", {"patient": patient, "provider": provider},
        username=username, password=password, timeout=timeout,
    )
    session = str(fresh.get("session") or "").strip()
    if not session or fresh.get("provider") != provider:
        raise RuntimeError("a new chat session for the requested provider was not created")
    streamed = _stream_turn(
        f"{api}/chat/stream",
        patient=patient, provider=provider, profile=profile, question=question,
        session=session, username=username, password=password, timeout=timeout,
    )
    history_url = f"{api}/chat?{urllib.parse.urlencode({'patient': patient, 'session': session})}"
    stored = None
    for attempt in range(10):
        history = _get_json(history_url, username=username, password=password, timeout=timeout)
        stored = next(
            (
                row for row in history.get("messages") or []
                if row.get("messageId") == streamed["message_id"] and row.get("role") == "assistant"
            ),
            None,
        )
        if stored is not None and str(stored.get("content") or "").strip() == streamed["answer"]:
            break
        if attempt < 9:
            time.sleep(0.25)
    else:
        raise RuntimeError("the answer was not stored in the chat session")
    result = {
        "schema_version": "chartsearchai_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "openmrs_url": openmrs_url,
        "username": username,
        "patient": patient,
        "patient_display": record["display"],
        "provider": provider,
        "profile": profile,
        "question": question,
        "session": session,
        **streamed,
        "stored": True,
        "cleared_after": clear_after,
        "runtime_identity": _runtime_identity(openmrs_url),
    }
    if clear_after:
        cleared = _post_json(
            f"{api}/chat/new", {"patient": patient, "provider": provider},
            username=username, password=password, timeout=timeout,
        )
        if not str(cleared.get("session") or "").strip():
            raise RuntimeError("the chat could not be cleared after the smoke")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--openmrs-url", default="http://127.0.0.1:8088/openmrs")
    parser.add_argument("--patient", default=SAMPLE_PATIENT, help="Patient UUID (default: the HIV sample patient).")
    parser.add_argument(
        "--identity-only", action="store_true",
        help="Only check that the deployed artifacts are the pinned builds; no model request.",
    )
    parser.add_argument("--provider", default="hub", help="Configured ChartSearchAI provider (default: hub).")
    parser.add_argument("--profile", help="Hub profile; default: the advertised product default.")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--username", default=os.environ.get("CHARTSEARCH_ADMIN_USER", "admin"),
        help="OpenMRS account (default: CHARTSEARCH_ADMIN_USER, else the demo administrator).",
    )
    parser.add_argument(
        "--password", default=os.environ.get("CHARTSEARCH_ADMIN_PASSWORD", "Admin123"),
        help="Its password (default: CHARTSEARCH_ADMIN_PASSWORD, else the local demo password).",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--clear-after", action="store_true", help="Start a fresh chat for the patient afterwards.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.identity_only:
        result = {
            "schema_version": "chartsearchai_runtime_identity.v1",
            "runtime_identity": _runtime_identity(args.openmrs_url),
        }
    else:
        profile = args.profile or discover_default_profile(
            args.openmrs_url, username=args.username, password=args.password, timeout=args.timeout,
        )
        result = smoke(
            args.openmrs_url,
            patient=args.patient, provider=args.provider, profile=profile, question=args.question,
            username=args.username, password=args.password, timeout=args.timeout,
            clear_after=args.clear_after,
        )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
