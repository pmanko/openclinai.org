"""Behavior of the HIV baseline tool and the setup that resets to a baseline.

Docker, make and the OpenMRS and Elasticsearch HTTP APIs are stubs that record
every call into one log, so these tests show what the tools refuse to do and in
what order they act.
"""
from __future__ import annotations

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
        "dataset": {"sha256": "d" * 64},
        "embedding": {"model_sha256": "m", "vocab_sha256": "v"},
        "indices": INDICES,
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
  "buildx build")
    while [[ $# -gt 0 ]]; do
      [[ "$1" == --metadata-file ]] && echo '{{"containerimage.digest": "sha256:feed"}}' > "$2"
      shift
    done
    exit 0 ;;
esac
case "$1" in
  pull) exit 1 ;;
  create) echo baseline-container ;;
  cp) [[ "$2" == baseline-container:/baseline/manifest.json ]] && cat "{manifest_tar}" ;;
  inspect) [[ "$*" == *Health.Status* ]] && echo healthy || echo true ;;
esac
exit 0
""", encoding="utf-8")
    make = binaries / "make"
    make.write_text(f'#!/bin/bash\necho "make $* ${{OMRS_CONFIG_CREATE_TABLES:+create_tables=$OMRS_CONFIG_CREATE_TABLES}}" >> "{log}"\n',
                    encoding="utf-8")
    for stub in (docker, make):
        stub.chmod(0o755)
    return binaries


class _Services(BaseHTTPRequestHandler):
    """OpenMRS and Elasticsearch endpoints the tool calls, logged beside the docker calls."""

    index_complete = True
    log: Path

    def _answer(self) -> None:
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write(f"http {self.command} {self.path}\n")
        path = self.path.split("?")[0]
        if path == "/openmrs/ws/rest/v1/querystore/indexingstatus":
            body: object = {"complete": self.index_complete}
        elif path == "/":
            body = {"version": {"number": "8.13.4"}}
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
def services(tmp_path):
    log = tmp_path / "calls.log"
    handler = type("Handler", (_Services,), {"log": log})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield handler, server.server_address[1], log
    server.shutdown()


def _calls(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _run_tool(tmp_path: Path, binaries: Path, *args: str, port: int = 9, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args, "--pin", str(tmp_path / "hiv-baseline.json"),
         "--local-state", str(tmp_path / "state"), "--output", str(tmp_path / "export")],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", "BASELINE": "",
             "QUERYSTORE_ES_URL": f"http://127.0.0.1:{port}", "HARNESS_PROXY_HTTP_PORT": str(port), **env},
        capture_output=True, text=True, timeout=60,
    )


def test_without_a_default_baseline_the_check_names_the_alternatives_and_touches_nothing(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)

    result = _run_tool(tmp_path, binaries, "check")

    assert result.returncode == 3
    assert "REBUILD_BASELINE=1" in result.stderr and "BASELINE=<image>" in result.stderr
    assert _calls(log) == []


def test_restore_refuses_an_image_that_is_not_a_baseline_before_any_side_effect(tmp_path, services):
    _handler, port, log = services
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest(schema_version="other")))

    result = _run_tool(tmp_path, binaries, "restore", port=port, BASELINE="example/baseline:test")

    assert result.returncode == 3
    assert not [call for call in _calls(log) if call.startswith(("docker stop", "docker exec", "http DELETE"))]


def test_restore_of_an_unavailable_image_changes_nothing(tmp_path, services):
    _handler, port, log = services
    binaries = _stub_bin(tmp_path, log, None, image_present=False)

    result = _run_tool(tmp_path, binaries, "restore", port=port, BASELINE="example/missing:1")

    assert result.returncode == 3
    assert [call.split()[1] for call in _calls(log)] == ["image", "pull"]


def test_restore_stops_openmrs_before_replacing_the_database_and_index(tmp_path, services):
    _handler, port, log = services
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest()))

    result = _run_tool(tmp_path, binaries, "restore", port=port, BASELINE="example/baseline:test")

    assert result.returncode == 0, result.stderr
    calls = _calls(log)
    stop = calls.index("docker stop harness-openmrs-backend")
    database = next(i for i, call in enumerate(calls) if call.startswith("docker exec -i harness-openmrs-db"))
    index = calls.index("http DELETE /querystore_obs")
    restore = next(i for i, call in enumerate(calls) if call.startswith("http POST /_snapshot/"))
    assert stop < database and stop < index < restore
    receipt = json.loads((tmp_path / "state" / "corpus-provenance.json").read_text(encoding="utf-8"))
    assert receipt["baseline_image"] == "example/baseline:test"


def test_export_of_an_incomplete_index_stops_nothing_and_writes_nothing(tmp_path, services):
    handler, port, log = services
    handler.index_complete = False
    binaries = _stub_bin(tmp_path, log, None)

    result = _run_tool(tmp_path, binaries, "export", port=port)

    assert result.returncode == 1
    assert "not complete" in result.stderr
    assert not [call for call in _calls(log) if call.startswith(("docker stop", "http PUT /_snapshot"))]
    assert not (tmp_path / "export").exists()


@pytest.mark.parametrize("name", [None, "with-conversations"])
def test_publish_pins_only_the_default_baseline(tmp_path, name):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)
    (tmp_path / "export").mkdir()
    (tmp_path / "export" / "manifest.json").write_text(
        json.dumps(_manifest(created_at="2026-10-14T04:48:23+00:00")), encoding="utf-8")

    result = _run_tool(tmp_path, binaries, "publish", *(["--name", name] if name else []))

    assert result.returncode == 0, result.stderr
    pushed = next(call for call in _calls(log) if call.startswith("docker buildx build"))
    assert "--push" in pushed
    pin = tmp_path / "hiv-baseline.json"
    if name:
        assert f"ghcr.io/pmanko/openclinai-hiv-baseline:{name}" in pushed
        assert not pin.exists()
    else:
        assert json.loads(pin.read_text(encoding="utf-8"))["image"] == \
            "ghcr.io/pmanko/openclinai-hiv-baseline@sha256:feed"


def _run_setup(binaries: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/bin/bash", str(SETUP), *args],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", **env},
        capture_output=True, text=True, timeout=60,
    )


def test_setup_with_an_unavailable_baseline_stops_before_building_anything(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None, image_present=False)

    result = _run_setup(binaries, BASELINE="example/missing:1")

    assert result.returncode != 0
    assert "REBUILD_BASELINE=1" in result.stderr
    assert not [call for call in _calls(log) if call.startswith(("make", "docker compose", "docker stop"))]


def test_rebuild_without_the_hiv_dump_stops_before_building_anything(tmp_path):
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, None)

    result = _run_setup(binaries, f"DUMP={tmp_path / 'missing.sql.gz'}", REBUILD_BASELINE="1")

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

    result = _run_setup(binaries, BASELINE="example/baseline:test")

    assert result.returncode == 0, result.stderr
    calls = _calls(log)
    stop = calls.index("docker compose -f compose/openmrs-2.8-refapp.yml stop proxy gateway backend")
    restore = calls.index("python3 scripts/hiv-baseline.py restore")
    # The restored database is loaded before OpenMRS first starts, so a new data volume must not create tables.
    start = calls.index("make local-stack-up create_tables=false")
    restart = calls.index("docker restart harness-openmrs-backend")
    verify = calls.index("python3 scripts/hiv-baseline.py verify")
    recorded = calls.index("python3 scripts/hiv-baseline.py record-deployed")
    assert stop < restore < start < restart < verify < recorded


def test_record_deployed_copies_each_module_build_record(tmp_path):
    state = tmp_path / "state"
    builds = state / "module-provenance"
    builds.mkdir(parents=True)
    for module, commit in (("chartsearchai", "c" * 40), ("querystore", "a" * 40)):
        (builds / f"{module}-1.0.0-SNAPSHOT.omod.provenance.json").write_text(
            json.dumps({"source_commit": commit}), encoding="utf-8")
    log = tmp_path / "calls.log"

    result = _run_tool(tmp_path, _stub_bin(tmp_path, log, None), "record-deployed")

    assert result.returncode == 0, result.stderr
    for module, commit in (("chartsearchai", "c" * 40), ("querystore", "a" * 40)):
        assert json.loads((state / f"deployed-{module}-omod.json").read_text()) == {"source_commit": commit}
    assert _calls(log) == []


def test_record_deployed_without_a_build_record_fails_and_writes_nothing(tmp_path):
    log = tmp_path / "calls.log"

    result = _run_tool(tmp_path, _stub_bin(tmp_path, log, None), "record-deployed")

    assert result.returncode == 1
    assert "build the modules first" in result.stderr
    assert not list((tmp_path / "state").glob("deployed-*")) if (tmp_path / "state").exists() else True


@pytest.mark.parametrize("image, pulled", [
    ("ghcr.io/pmanko/openclinai-hiv-baseline:named", True),
    ("ghcr.io/pmanko/openclinai-hiv-baseline@sha256:" + "a" * 64, False),
])
def test_a_cached_tag_is_pulled_again_but_a_cached_digest_is_not(tmp_path, image, pulled):
    """A named baseline can be republished under the same tag; a digest cannot change."""
    log = tmp_path / "calls.log"
    binaries = _stub_bin(tmp_path, log, _manifest_archive(tmp_path, _manifest()))

    result = _run_tool(tmp_path, binaries, "check", BASELINE=image)

    assert result.returncode == 0, result.stderr
    assert (f"docker pull {image}" in _calls(log)) is pulled
