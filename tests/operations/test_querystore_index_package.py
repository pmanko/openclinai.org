"""Behavior of the prepared QueryStore index package and the setup that consumes it.

Docker and make are stubs that record every invocation, so these tests show what the
tools refuse to do: a package built from other inputs, or a missing package, never
reaches a container, the database or a build.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts" / "querystore-index-package.py"
SETUP = ROOT / "scripts" / "chartsearch-research-setup.sh"
PIN = "example/backend@sha256:" + "a" * 64


def _recording_bin(tmp_path: Path, *names: str) -> tuple[Path, Path]:
    binaries = tmp_path / "bin"
    binaries.mkdir()
    log = tmp_path / "calls.log"
    for name in names:
        stub = binaries / name
        stub.write_text(f'#!/bin/bash\necho "{name} $*" >> "{log}"\n', encoding="utf-8")
        stub.chmod(0o755)
    return binaries, log


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


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    dump = tmp_path / "data" / "refapp_28_demo.sql.gz"
    dump.parent.mkdir()
    dump.write_bytes(gzip.compress(b"SELECT 1;\n"))
    Path(f"{dump}.provenance.json").write_text(json.dumps({"output_sha256": "d" * 64}), encoding="utf-8")
    compose = tmp_path / "compose.yml"
    compose.write_text(f"services:\n  backend:\n    build:\n      args:\n        OPENMRS_BACKEND_IMAGE: {PIN}\n",
                       encoding="utf-8")
    repo, tree = _querystore_checkout(tmp_path)
    inputs = {"dump_sha256": "d" * 64, "querystore_source_tree": tree, "backend_image": PIN}
    return dump, compose, repo, inputs


def _package(path: Path, inputs: dict[str, str]) -> Path:
    manifest = json.dumps({"schema_version": "querystore_index_package.v1", "inputs": inputs,
                           "indices": {"querystore_obs": 1}}).encode()
    with tarfile.open(path, "w:gz") as archive:
        entry = tarfile.TarInfo("manifest.json")
        entry.size = len(manifest)
        archive.addfile(entry, io.BytesIO(manifest))
    return path


def _run_tool(command: str, dump: Path, compose: Path, repo: Path, binaries: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), command, "--dump", str(dump), "--compose", str(compose),
         "--querystore-repo", str(repo)],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}"},
        capture_output=True, text=True, timeout=30,
    )


def test_a_package_built_from_the_same_inputs_passes_the_check(tmp_path):
    binaries, log = _recording_bin(tmp_path, "docker")
    dump, compose, repo, inputs = _inputs(tmp_path)
    _package(dump.with_name("refapp_28_demo.querystore-index.tar.gz"), inputs)

    result = _run_tool("check", dump, compose, repo, binaries)

    assert result.returncode == 0, result.stderr
    assert not log.exists()


@pytest.mark.parametrize("field", ["dump_sha256", "querystore_source_tree", "backend_image"])
def test_restore_refuses_a_package_from_other_inputs_before_any_side_effect(tmp_path, field):
    binaries, log = _recording_bin(tmp_path, "docker")
    dump, compose, repo, inputs = _inputs(tmp_path)
    _package(dump.with_name("refapp_28_demo.querystore-index.tar.gz"), {**inputs, field: "other"})

    result = _run_tool("restore", dump, compose, repo, binaries)

    assert result.returncode == 3
    assert field in result.stderr
    assert not log.exists()


def test_restore_refuses_an_uncommitted_querystore_checkout(tmp_path):
    binaries, log = _recording_bin(tmp_path, "docker")
    dump, compose, repo, inputs = _inputs(tmp_path)
    _package(dump.with_name("refapp_28_demo.querystore-index.tar.gz"), inputs)
    (repo / "pom.xml").write_text("<project>changed</project>\n", encoding="utf-8")

    result = _run_tool("restore", dump, compose, repo, binaries)

    assert result.returncode == 3
    assert not log.exists()


def _run_setup(tmp_path: Path, dump: Path, **env: str) -> tuple[subprocess.CompletedProcess, Path]:
    binaries, log = _recording_bin(tmp_path, "make", "docker")
    result = subprocess.run(
        ["/bin/bash", str(SETUP), f"DUMP={dump}"],
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", **env},
        capture_output=True, text=True, timeout=60,
    )
    return result, log


def test_setup_without_a_prepared_index_stops_before_building_anything(tmp_path):
    dump = tmp_path / "refapp_28_demo.sql.gz"
    dump.write_bytes(gzip.compress(b"SELECT 1;\n"))

    result, log = _run_setup(tmp_path, dump)

    assert result.returncode != 0
    assert "REBUILD_INDEX=1" in result.stderr
    assert not log.exists()


def test_setup_with_a_mismatched_prepared_index_stops_before_building_anything(tmp_path):
    dump = tmp_path / "refapp_28_demo.sql.gz"
    dump.write_bytes(gzip.compress(b"SELECT 1;\n"))
    Path(f"{dump}.provenance.json").write_text(json.dumps({"output_sha256": "d" * 64}), encoding="utf-8")
    _package(tmp_path / "refapp_28_demo.querystore-index.tar.gz",
             {"dump_sha256": "e" * 64, "querystore_source_tree": "x", "backend_image": "y"})

    result, log = _run_setup(tmp_path, dump)

    assert result.returncode != 0
    assert "dump_sha256" in result.stderr
    assert not log.exists()
