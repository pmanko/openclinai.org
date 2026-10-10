import configparser
import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = ROOT / "compose" / "catalyst-model-router.yml"
PRESET_PATH = ROOT / "scripts" / "catalyst-model-router.ini"
MODELS_PATH = ROOT / "scripts" / "catalyst-model-router.models.tsv"
SCRIPT_PATH = ROOT / "scripts" / "catalyst-model-router.sh"


def model_records() -> dict[str, dict[str, str]]:
    records = {}
    for line in MODELS_PATH.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        alias, filename, sha256, source = line.split("\t")
        records[alias] = {
            "filename": filename,
            "sha256": sha256,
            "source": source,
        }
    return records


def test_router_compose_is_digest_pinned_loopback_only_and_read_only():
    """Invariant: the router image is immutable, its port is loopback-only and model mounts are read-only."""
    service = yaml.safe_load(COMPOSE_PATH.read_text())["services"]["model-router"]
    assert re.search(r"@sha256:[a-f0-9]{64}\}?$", service["image"])
    assert all(str(port).startswith("127.0.0.1:") for port in service["ports"])
    assert all(volume.endswith(":ro") for volume in service["volumes"])


def test_router_presets_and_verified_sources_describe_the_same_models():
    presets = configparser.ConfigParser(interpolation=None)
    presets.read(PRESET_PATH)
    records = model_records()

    assert set(presets.sections()) - {"*"} == set(records)
    for alias, record in records.items():
        assert presets[alias]["model"] == f"/models/{record['filename']}"
        assert re.fullmatch(r"[a-f0-9]{64}", record["sha256"])
        assert re.fullmatch(
            r"https://huggingface\.co/[^/]+/[^/]+/resolve/[a-f0-9]{40}/[^/]+\.gguf",
            record["source"],
        )


@pytest.mark.parametrize("image", ["router:latest", "router:v1", "sha256:abc", "repo@sha256:abc"])
def test_router_rejects_mutable_or_incomplete_image_override(image):
    import os
    import subprocess

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "config"],
        env={**os.environ, "CATALYST_ROUTER_IMAGE": image},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "must be an immutable image ID or registry digest" in result.stderr


@pytest.mark.parametrize("already_loaded", [True, False])
def test_warm_model_handles_loaded_and_unloaded_states(already_loaded):
    import json
    import os
    import subprocess
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    requests = []
    loaded = already_loaded

    class Router(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(("GET", self.path))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"data": [{"id": "gemma-e4b", "status": {"value": "loaded" if loaded else "unloaded"}}]}).encode())

        def do_POST(self):
            nonlocal loaded
            requests.append(("POST", self.path))
            if loaded:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":{"message":"model is already running"}}')
            else:
                loaded = True
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"success":true}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Router)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "warm", "gemma-e4b"],
            env={**os.environ, "CATALYST_ROUTER_PORT": str(server.server_port)},
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert ("GET", "/models") in requests
        assert requests.count(("POST", "/models/load")) == (0 if already_loaded else 1)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("image", ["sha256:" + "a" * 64, "registry.example/router@sha256:" + "b" * 64])
def test_router_passes_verified_image_override_to_compose(tmp_path, image):
    import os
    import subprocess

    docker = tmp_path / "docker"
    docker.write_text('#!/bin/sh\nprintf "%s\\n" "$CATALYST_ROUTER_IMAGE" "$@"\n')
    docker.chmod(0o755)
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "config"],
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
             "CATALYST_ROUTER_IMAGE": image,
             "CATALYST_ROUTER_PUBLIC_NETWORK": "public",
             "CATALYST_ROUTER_APPLICATION_NETWORK": "application"},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [image, "compose", "-f", str(COMPOSE_PATH), "config"]


def test_router_up_with_unverified_models_never_starts_the_container(tmp_path):
    import os
    import subprocess

    calls = tmp_path / "docker-calls.txt"
    docker = tmp_path / "bin" / "docker"
    docker.parent.mkdir()
    docker.write_text(f'#!/bin/sh\necho "$*" >> "{calls}"\n')
    docker.chmod(0o755)
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "up"],
        env={**os.environ, "PATH": f"{docker.parent}{os.pathsep}{os.environ['PATH']}",
             "CATALYST_ROUTER_MODEL_DIR": str(tmp_path / "no-models"),
             "CATALYST_ROUTER_PUBLIC_NETWORK": "public",
             "CATALYST_ROUTER_APPLICATION_NETWORK": "application"},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert not calls.exists() or "up" not in calls.read_text().split()
