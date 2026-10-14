"""Behavior of the HIV research baseline tool and the setup that consumes it.

Docker, make and Elasticsearch are stubs that record every call into one log, so
these tests show what the tools refuse to do and in what order they act: a
baseline that this stack cannot restore never reaches OpenMRS, its database or
its index, and a usable one replaces both only after OpenMRS has stopped.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import subprocess
import sys
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts" / "hiv-baseline.py"
SETUP = ROOT / "scripts" / "chartsearch-research-setup.sh"
INDICES = {"querystore_obs": 3, "querystore_patient": 2}


def _manifest(**overrides: object) -> dict:
    manifest = {
        "schema_version": "openclinai_hiv_baseline.v1",
        "dataset": {"sha256": "d" * 64, "bytes": 1, "source_schema": "openmrs"},
        "embedding": {"model_sha256": "m" * 64, "vocab_sha256": "v" * 64},
        "elasticsearch_version": "8.13.4",
        "indices": INDICES,
        "built_from": {},
    }
    manifest.update(overrides)
    return manifest


def _manifest_archive(tmp_path: Path, manifest: dict) -> Path:
    """The tar stream `docker cp <container>:/baseline/manifest.json -` writes."""
    body = json.dumps(manifest).encode()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        entry = tarfile.TarInfo("manifest.json")
        entry.size = len(body)
        archive.addfile(entry, io.BytesIO(body))
    path = tmp_path / "manifest.tar"
    path.write_bytes(buffer.getvalue())
    return path


def _stub_bin(tmp_path: Path, log: Path, manifest_tar: Path | None, image_present: bool = True) -> Path:
    binaries = tmp_path / "bin"
    binaries.mkdir()
    docker = binaries / "docker"
    docker.write_text(f"""#!/bin/bash
echo "docker $*" >> "{log}"
case "$1 $2" in
  "image inspect") exit {0 if image_present else 1} ;;
esac
if [[ " $* " == *" -i "* ]]; then
  sql="$(cat)"
  echo "sql: ${{sql//$'\n'/ }}" >> "{log}"
  case "$sql" in
    *querystore.backend*) echo elasticsearch ;;
    *core.version*) echo 2.9.0 ;;
    *chartsearchai_conversation*) echo "${{STUB_CONVERSATION_ROWS:-0}}" ;;
    *querystore_bootstrap_progress*) echo 0 ;;
  esac
  exit 0
fi
case "$1" in
  pull) exit 1 ;;
  create) echo baseline-container ;;
  cp) [[ "$2" == baseline-container:/baseline/manifest.json ]] && cat "{manifest_tar}" ;;
  inspect)
    case "$*" in
      *Config.Image*) echo harness-openmrs-backend:test ;;
      *Health.Status*) echo healthy ;;
      *) echo true ;;
    esac ;;
  exec)
    [[ "$*" == *sha256sum* ]] && printf '%s  %s\n' m /openmrs/data/chartsearchai/model.onnx v /openmrs/data/chartsearchai/vocab.txt ;;
esac
exit 0
""", encoding="utf-8")
    make = binaries / "make"
    make.write_text(f'#!/bin/bash\necho "make $*" >> "{log}"\n', encoding="utf-8")
    for stub in (docker, make):
        stub.chmod(0o755)
    return binaries


class _Elasticsearch(BaseHTTPRequestHandler):
    """Answers the calls a restore makes and logs each one beside the docker calls."""

    version = "8.13.4"
    log: Path

    def _answer(self) -> None:
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write(f"es {self.command} {self.path}\n")
        path = self.path.split("?")[0]
        if path == "/openmrs/ws/rest/v1/module":
            body: object = {"results": [{"uuid": "m", "name": "M", "version": "1", "started": True}]}
        elif path == "/openmrs/ws/rest/v1/querystore/indexingstatus":
            body = {"complete": True, "types": []}
        elif path == "/openmrs/ws/rest/v1/querystore/drift":
            body = {"types": [{"resourceType": "obs", "coreCount": 3, "indexedCount": 3}]}
        elif path == "/":
            body = {"version": {"number": self.version}}
        elif path.startswith("/_cat/indices"):
            body = [{"index": name} for name in INDICES]
        elif path.endswith("/_restore"):
            body = {"snapshot": {"shards": {"failed": 0}}}
        elif path.endswith("/_count"):
            body = {"count": INDICES[path.split("/")[1]]}
        else:
            body = {"acknowledged": True}
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = do_PUT = do_POST = do_DELETE = _answer

    def log_message(self, *_args: object) -> None:
        pass


@pytest.fixture
def elasticsearch(tmp_path):
    log = tmp_path / "calls.log"
    handler = type("Handler", (_Elasticsearch,), {"log": log})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield handler, f"http://127.0.0.1:{server.server_address[1]}", log
    server.shutdown()


def _calls(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _run_tool(tmp_path: Path, command: str, binaries: Path, es_url: str = "http://127.0.0.1:9",
              **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), command, "--pin", str(tmp_path / "hiv-baseline.json"),
         "--local-state", str(tmp_path / "state")],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", "QUERYSTORE_ES_URL": es_url,
             "HIV_BASELINE_IMAGE": "", **env},
        capture_output=True, text=True, timeout=60,
    )


def test_without_a_published_baseline_the_check_names_the_rebuild_and_touches_nothing(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)

    result = _run_tool(tmp_path, "check", binaries)

    assert result.returncode == 3
    assert "REBUILD_BASELINE=1" in result.stderr
    assert _calls(log) == []


def test_restore_refuses_an_image_that_is_not_a_baseline_before_any_side_effect(tmp_path, elasticsearch):
    _handler, es_url, log = elasticsearch
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest(schema_version="other")))

    result = _run_tool(tmp_path, "restore", binaries, es_url, HIV_BASELINE_IMAGE="example/baseline:test")

    assert result.returncode == 3
    assert not [call for call in _calls(log) if call.startswith(("docker stop", "docker exec", "es DELETE"))]


@pytest.mark.parametrize("built, running", [("8.15.0", "8.13.4"), ("7.17.0", "8.13.4")])
def test_restore_refuses_an_index_this_elasticsearch_cannot_load_before_any_side_effect(
        tmp_path, elasticsearch, built, running):
    handler, es_url, log = elasticsearch
    handler.version = running
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest(elasticsearch_version=built)))

    result = _run_tool(tmp_path, "restore", binaries, es_url, HIV_BASELINE_IMAGE="example/baseline:test")

    assert result.returncode == 3
    assert built in result.stderr
    assert not [call for call in _calls(log) if call.startswith(("docker stop", "docker exec", "es DELETE"))]


def test_restore_stops_openmrs_before_replacing_the_database_and_index(tmp_path, elasticsearch):
    _handler, es_url, log = elasticsearch
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest()))

    result = _run_tool(tmp_path, "restore", binaries, es_url, HIV_BASELINE_IMAGE="example/baseline:test")

    assert result.returncode == 0, result.stderr
    calls = _calls(log)
    stop = calls.index("docker stop harness-openmrs-backend")
    database = next(i for i, call in enumerate(calls) if call.startswith("docker exec -i harness-openmrs-db"))
    index = calls.index("es DELETE /querystore_obs")
    restore = next(i for i, call in enumerate(calls) if call.startswith("es POST /_snapshot/"))
    assert stop < database and stop < index < restore
    receipt = json.loads((tmp_path / "state" / "corpus-provenance.json").read_text(encoding="utf-8"))
    assert receipt["dump_sha256"] == "d" * 64
    assert receipt["baseline_image"] == "example/baseline:test"


def test_restore_of_an_unavailable_image_changes_nothing(tmp_path, elasticsearch):
    _handler, es_url, log = elasticsearch
    binaries = _stub_bin(tmp_path, log, None, image_present=False)

    result = _run_tool(tmp_path, "restore", binaries, es_url, HIV_BASELINE_IMAGE="example/missing:1")

    assert result.returncode == 3
    assert [call.split()[1] for call in _calls(log)] == ["image", "pull"]


def _run_setup(tmp_path: Path, binaries: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/bin/bash", str(SETUP), *args],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", **env},
        capture_output=True, text=True, timeout=60,
    )


def test_setup_with_an_unavailable_baseline_stops_before_building_anything(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None, image_present=False)

    result = _run_setup(tmp_path, binaries, HIV_BASELINE_IMAGE="example/missing:1")

    assert result.returncode != 0
    assert "REBUILD_BASELINE=1" in result.stderr
    assert not [call for call in _calls(log) if call.startswith(("make", "docker compose", "docker stop"))]


def test_rebuild_without_the_hiv_dump_stops_before_building_anything(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)

    result = _run_setup(tmp_path, binaries, f"DUMP={tmp_path / 'missing.sql.gz'}", REBUILD_BASELINE="1")

    assert result.returncode != 0
    assert "HIV baseline dump not found" in result.stderr
    assert _calls(log) == []


def test_setup_stops_openmrs_and_its_gateway_before_restoring_then_starts_the_stack(tmp_path):
    """The gateway's health check passes through to OpenMRS, so it must not stay up while OpenMRS is down."""
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)
    for name in ("python3", "curl"):
        stub = binaries / name
        stub.write_text(f'#!/bin/bash\necho "{name} $*" >> "{log}"\n', encoding="utf-8")
        stub.chmod(0o755)

    result = _run_setup(tmp_path, binaries, HIV_BASELINE_IMAGE="example/baseline:test")

    assert result.returncode == 0, result.stderr
    calls = _calls(log)
    stop = calls.index("docker compose -f compose/openmrs-2.8-refapp.yml stop proxy gateway backend")
    restore = calls.index("python3 scripts/hiv-baseline.py restore")
    start = calls.index("make local-stack-up")
    verify = calls.index("python3 scripts/hiv-baseline.py verify")
    assert stop < restore < start < verify


def _querystore_checkout(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "querystore"
    repo.mkdir()
    (repo / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    for command in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "fixture"]):
        subprocess.run(["git", *command], cwd=repo, check=True, env=env)
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()
    return repo, tree


def test_export_checks_for_conversations_only_after_openmrs_stops_and_never_snapshots_them(
        tmp_path, elasticsearch):
    """A conversation written before OpenMRS stops must not reach a published baseline."""
    _handler, es_url, log = elasticsearch
    binaries = _stub_bin(tmp_path, log, None)
    repo, tree = _querystore_checkout(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    (state / "deployed-querystore-omod.json").write_text(
        json.dumps({"source_tree_clean": True, "source_tree": tree}), encoding="utf-8")
    (state / "corpus-provenance.json").write_text(json.dumps({"dump_sha256": "d" * 64}), encoding="utf-8")
    compose = tmp_path / "compose.yml"
    compose.write_text("image: harness-openmrs-backend:test\nOPENMRS_BACKEND_IMAGE: example@sha256:abc\n",
                       encoding="utf-8")
    port = es_url.rsplit(":", 1)[1]

    result = subprocess.run(
        [sys.executable, str(TOOL), "export", "--querystore-repo", str(repo), "--compose", str(compose),
         "--local-state", str(state), "--output", str(tmp_path / "baseline")],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", "QUERYSTORE_ES_URL": es_url,
             "HARNESS_PROXY_HTTP_PORT": port, "STUB_CONVERSATION_ROWS": "2"},
        capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 1
    assert "conversation" in result.stderr
    calls = _calls(log)
    stop = calls.index("docker stop harness-openmrs-backend")
    usage = next(i for i, call in enumerate(calls) if "chartsearchai_conversation" in call)
    assert stop < usage < calls.index("docker start harness-openmrs-backend")
    assert not [call for call in calls if call.startswith("es PUT /_snapshot")]
    assert not (tmp_path / "baseline").exists()
