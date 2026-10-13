#!/usr/bin/env python3
"""Export or restore the prepared QueryStore index for the HIV baseline.

QueryStore embeds every HIV record into Elasticsearch, which takes hours. A
prepared index package lets a fresh setup restore that work in minutes. The
package holds an Elasticsearch snapshot of every querystore_* index (made with
the snapshot API), QueryStore's bootstrap completion records, and a manifest of
the inputs the index was built from. Restore refuses a package whose inputs
differ from this checkout, so a restored index always matches the database,
module, distribution and embedding model it serves.

  export   maintainer: package the running, fully indexed local stack
  check    no side effects: does a package match this checkout and dump?
  restore  fresh setup: load a matching package into the running stack

Exit status 3 means the package does not match; nothing was changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "querystore_index_package.v1"
MISMATCH = 3
REPOSITORY = "openclinai-baseline"
SNAPSHOT = "querystore"
SNAPSHOT_DIR = f"/usr/share/elasticsearch/snapshots/{REPOSITORY}"
PROGRESS_TABLE = "querystore_bootstrap_progress"
PROGRESS_FILE = "querystore_bootstrap_progress.sql"
DEFAULT_DUMP = ROOT / "artifacts" / "demo-data" / "refapp_28_demo.sql.gz"
MODULE_PROVENANCE = (
    ROOT / "artifacts" / "chartsearchai-local" / "module-provenance"
    / "querystore-1.0.0-SNAPSHOT.omod.provenance.json"
)
DEPLOYED_PROVENANCE = ROOT / "artifacts" / "chartsearchai-local" / "deployed-querystore-omod.json"
CORPUS_RECEIPT = ROOT / "artifacts" / "chartsearchai-local" / "corpus-provenance.json"
EMBEDDING_FILES = {
    "embedding_model_sha256": "/openmrs/data/chartsearchai/model.onnx",
    "embedding_vocab_sha256": "/openmrs/data/chartsearchai/vocab.txt",
}
NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Mismatch(Exception):
    """The package was built from different inputs than this checkout."""


def say(message: str) -> None:
    print(message, flush=True)


def load_settings() -> dict[str, str]:
    """Defaults from the env files the setup uses; the process environment wins."""
    values: dict[str, str] = {}
    for name in (".env.chartsearch.example", ".env.chartsearch"):
        path = ROOT / name
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    values[key.strip()] = value.strip()
    values.update(os.environ)
    return values


def package_for(dump: Path) -> Path:
    name = re.sub(r"\.sql(\.gz)?$", "", dump.name)
    return dump.with_name(f"{name}.querystore-index.tar.gz")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def checkout_inputs(dump: Path, querystore: Path, compose: Path) -> dict[str, str]:
    """Inputs known before any container runs: the dump, the QueryStore source and the pinned distribution."""
    sidecar = Path(f"{dump}.provenance.json")
    if not sidecar.is_file():
        raise Mismatch(f"missing dump provenance {sidecar}")
    dump_sha = json.loads(sidecar.read_text(encoding="utf-8")).get("output_sha256")
    if git(querystore, "status", "--porcelain", "--untracked-files=all"):
        raise Mismatch(f"{querystore} has uncommitted changes; a prepared index needs the pinned source")
    pin = re.search(r"OPENMRS_BACKEND_IMAGE:\s*(\S+)", compose.read_text(encoding="utf-8"))
    if not pin:
        raise Mismatch(f"no OPENMRS_BACKEND_IMAGE pin in {compose}")
    return {
        "dump_sha256": str(dump_sha),
        "querystore_source_tree": git(querystore, "rev-parse", "HEAD^{tree}"),
        "backend_image": pin.group(1),
    }


def compare(expected: dict[str, str], actual: dict[str, str]) -> None:
    differences = [
        f"  {key}: package {expected.get(key)!r}, this setup {value!r}"
        for key, value in actual.items()
        if expected.get(key) != value
    ]
    if differences:
        raise Mismatch("the prepared index was built from different inputs:\n" + "\n".join(differences))


class Stack:
    """The running local containers and HTTP endpoints."""

    def __init__(self, settings: dict[str, str]):
        self.backend = settings.get("OPENMRS_BACKEND", "harness-openmrs-backend")
        self.proxy = settings.get("OPENMRS_PROXY", "harness-proxy")
        self.db = settings.get("DB_CONTAINER", "harness-openmrs-db")
        self.es = settings.get("QUERYSTORE_ES_CONTAINER", "harness-querystore-es")
        self.db_name = settings.get("OMRS_DB_NAME", "openmrs")
        self.es_url = settings.get(
            "QUERYSTORE_ES_URL", f"http://localhost:{settings.get('QUERYSTORE_ES_PORT', '9200')}"
        ).rstrip("/")
        self.openmrs = f"http://localhost:{settings.get('HARNESS_PROXY_HTTP_PORT', '8088')}/openmrs"
        user = settings.get("CHARTSEARCH_ADMIN_USER")
        password = settings.get("CHARTSEARCH_ADMIN_PASSWORD")
        if not user or not password:
            raise SystemExit("ERROR: CHARTSEARCH_ADMIN_USER and CHARTSEARCH_ADMIN_PASSWORD must be set")
        self.auth = "Basic " + b64encode(f"{user}:{password}".encode()).decode()

    # -- processes -------------------------------------------------------
    @staticmethod
    def docker(*args: str, stdin: str | None = None) -> str:
        result = subprocess.run(
            ["docker", *args], input=stdin, capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker {' '.join(args[:3])} failed: {result.stderr.strip()}")
        return result.stdout

    def db_client(self, program: str, *args: str, stdin: str | None = None) -> str:
        """Run a MariaDB client in the database container with that container's own root login."""
        return self.docker(
            "exec", "-i", self.db, "sh", "-c",
            f'exec {program} --user=root --password="$MYSQL_ROOT_PASSWORD" "$@"', program, *args,
            stdin=stdin,
        )

    def sql(self, statements: str) -> str:
        return self.db_client("mariadb", "--batch", "--skip-column-names", self.db_name, stdin=statements)

    # -- HTTP --------------------------------------------------------------
    def request(self, method: str, url: str, body: object = None, *, auth: bool = False,
                timeout: float = 120) -> dict:
        data = None if body is None else json.dumps(body).encode()
        headers = {"Content-Type": "application/json"} if data else {}
        if auth:
            headers["Authorization"] = self.auth
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with NO_PROXY.open(req, timeout=timeout) as response:
                text = response.read().decode()
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"{method} {url} -> HTTP {error.code}: {error.read().decode()[:500]}") from None
        return json.loads(text) if text.strip() else {}

    def es_call(self, method: str, path: str, body: object = None, timeout: float = 120) -> dict:
        return self.request(method, f"{self.es_url}/{path.lstrip('/')}", body, timeout=timeout)

    def rest(self, path: str, timeout: float = 120) -> dict:
        return self.request("GET", f"{self.openmrs}/ws/rest/v1/{path}", auth=True, timeout=timeout)

    # -- state ---------------------------------------------------------------
    def runtime_inputs(self) -> dict[str, str]:
        files = list(EMBEDDING_FILES.values())
        sums = {
            path: digest
            for digest, path in (
                line.split(None, 1) for line in self.docker("exec", self.backend, "sha256sum", *files).splitlines()
            )
        }
        inputs = {key: sums.get(path, "") for key, path in EMBEDDING_FILES.items()}
        inputs["elasticsearch_version"] = self.es_call("GET", "/")["version"]["number"]
        return inputs

    def querystore_indices(self) -> list[str]:
        rows = self.es_call("GET", "_cat/indices/querystore_*?format=json&h=index&expand_wildcards=all")
        return sorted(row["index"] for row in rows) if isinstance(rows, list) else []

    def counts(self) -> dict[str, int]:
        self.es_call("POST", "querystore_*/_refresh")
        return {index: int(self.es_call("GET", f"{index}/_count")["count"]) for index in self.querystore_indices()}

    def wait_backend_healthy(self, timeout: int = 1800) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", self.backend],
                capture_output=True, text=True,
            ).stdout.strip()
            if status == "healthy":
                return
            time.sleep(5)
        raise RuntimeError(f"{self.backend} did not become healthy within {timeout}s")

    def start_backend(self) -> None:
        say(f"==> starting {self.backend}")
        self.docker("start", self.backend)
        self.wait_backend_healthy()
        self.docker("start", self.proxy)

    def wait_index_complete(self, timeout: int = 1800) -> dict:
        """Wait for QueryStore to report every type COMPLETED, then apply the drift rule."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status = self.rest("querystore/indexingstatus", timeout=30)
            except (OSError, RuntimeError):
                status = {}
            failed = [row for row in status.get("types") or [] if row.get("status") == "FAILED"]
            if failed:
                raise RuntimeError(f"QueryStore indexing failed: {failed}")
            if status.get("complete") is True:
                drift = self.rest("querystore/drift", timeout=120)
                check = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "check-querystore-drift.py")],
                    input=json.dumps(drift), capture_output=True, text=True,
                )
                print(check.stdout, end="")
                if check.returncode != 0:
                    raise RuntimeError("QueryStore drift check failed:\n" + check.stderr)
                return status
            time.sleep(10)
        raise RuntimeError(f"QueryStore did not report a complete index within {timeout}s")

    def prepare_snapshot_dir(self) -> None:
        self.docker("exec", "-u", "0", self.es, "sh", "-c",
                    f"rm -rf '{SNAPSHOT_DIR}' && mkdir -p '{SNAPSHOT_DIR}' && chown -R 1000:0 '{SNAPSHOT_DIR}'")

    def remove_snapshot_repository(self) -> None:
        try:
            self.es_call("DELETE", f"_snapshot/{REPOSITORY}")
        except RuntimeError:
            pass
        self.docker("exec", "-u", "0", self.es, "rm", "-rf", SNAPSHOT_DIR)


def safe_extract(package: Path, destination: Path) -> None:
    with tarfile.open(package, "r:gz") as archive:
        if hasattr(tarfile, "data_filter"):
            archive.extractall(destination, filter="data")
            return
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if not (member.isfile() or member.isdir()) or not target.is_relative_to(destination.resolve()):
                raise RuntimeError(f"unsafe path in package: {member.name}")
        archive.extractall(destination)


def read_manifest(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA:
        raise Mismatch(f"unsupported package schema {manifest.get('schema_version')!r}")
    return manifest


def manifest_of(package: Path) -> dict:
    with tarfile.open(package, "r:gz") as archive:
        member = archive.extractfile("manifest.json")
        if member is None:
            raise Mismatch("package has no manifest.json")
        manifest = json.load(member)
    if manifest.get("schema_version") != SCHEMA:
        raise Mismatch(f"unsupported package schema {manifest.get('schema_version')!r}")
    return manifest


def cmd_check(args: argparse.Namespace) -> int:
    if not args.package.is_file():
        raise Mismatch(f"no prepared index at {args.package}")
    manifest = manifest_of(args.package)
    compare(manifest["inputs"], checkout_inputs(args.dump, args.querystore_repo, args.compose))
    say(f"prepared index {args.package.name} matches this checkout and dump")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    if not args.package.is_file():
        raise Mismatch(f"no prepared index at {args.package}")
    compare(manifest_of(args.package)["inputs"], checkout_inputs(args.dump, args.querystore_repo, args.compose))
    stack = Stack(load_settings())
    with tempfile.TemporaryDirectory(prefix="querystore-index-") as scratch:
        work = Path(scratch)
        say(f"==> unpacking {args.package.name}")
        safe_extract(args.package, work)
        manifest = read_manifest(work)
        compare(manifest["inputs"], stack.runtime_inputs())
        if not stack.sql(f"SHOW TABLES LIKE '{PROGRESS_TABLE}';").strip():
            raise RuntimeError("QueryStore is not installed in this database; check the module startup errors")

        say(f"==> stopping {stack.backend} so nothing writes to the index during restore")
        stack.docker("stop", stack.backend)
        try:
            for index in stack.querystore_indices():
                stack.es_call("DELETE", index)
                say(f"    deleted {index}")
            stack.prepare_snapshot_dir()
            stack.docker("cp", f"{work / 'snapshot'}/.", f"{stack.es}:{SNAPSHOT_DIR}")
            stack.docker("exec", "-u", "0", stack.es, "chown", "-R", "1000:0", SNAPSHOT_DIR)
            stack.es_call("PUT", f"_snapshot/{REPOSITORY}?verify=false",
                          {"type": "fs", "settings": {"location": SNAPSHOT_DIR, "readonly": True}})
            say("==> restoring querystore_* indices with the Elasticsearch snapshot API")
            restored = stack.es_call(
                "POST", f"_snapshot/{REPOSITORY}/{SNAPSHOT}/_restore?wait_for_completion=true",
                {"indices": "querystore_*", "include_global_state": False, "include_aliases": True},
                timeout=7200,
            )
            shards = restored.get("snapshot", {}).get("shards", {})
            if shards.get("failed", 1) != 0:
                raise RuntimeError(f"snapshot restore reported failed shards: {restored}")
            counts = stack.counts()
            if counts != manifest["indices"]:
                raise RuntimeError(f"restored document counts {counts} differ from the package {manifest['indices']}")
            stack.remove_snapshot_repository()
            say(f"    restored {sum(counts.values())} documents in {len(counts)} indices")

            say("==> restoring QueryStore completion records and selecting the Elasticsearch backend")
            records = (work / PROGRESS_FILE).read_text(encoding="utf-8")
            stack.sql(
                "START TRANSACTION;\n"
                f"DELETE FROM {PROGRESS_TABLE};\n{records}\n"
                "INSERT INTO global_property (property, property_value, uuid) VALUES "
                "('querystore.backend', 'elasticsearch', UUID()), "
                "('querystore.bootstrap.autostart', 'true', UUID()) "
                "ON DUPLICATE KEY UPDATE property_value = VALUES(property_value);\n"
                "COMMIT;\n"
            )
        finally:
            stack.start_backend()

    if MODULE_PROVENANCE.is_file():
        DEPLOYED_PROVENANCE.write_text(MODULE_PROVENANCE.read_text(encoding="utf-8"), encoding="utf-8")
    say("==> waiting for QueryStore to confirm the restored index")
    stack.wait_index_complete()
    say("prepared QueryStore index restored; nothing was re-embedded")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    stack = Stack(load_settings())
    inputs = checkout_inputs(args.dump, args.querystore_repo, args.compose)
    if not DEPLOYED_PROVENANCE.is_file():
        raise RuntimeError(f"missing {DEPLOYED_PROVENANCE}; rebuild or restore the index with the setup first")
    deployed = json.loads(DEPLOYED_PROVENANCE.read_text(encoding="utf-8"))
    if not deployed.get("source_tree_clean") or deployed.get("source_tree") != inputs["querystore_source_tree"]:
        raise RuntimeError("the running index was not built from this checkout's QueryStore; "
                           "rebuild it with `make chartsearch-research-setup REBUILD_INDEX=1` first")
    receipt = json.loads(CORPUS_RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("dump_sha256") != inputs["dump_sha256"]:
        raise RuntimeError("the running database was not seeded from this dump; run the setup first")
    running = stack.docker("inspect", "-f", "{{.Config.Image}}", stack.backend).strip()
    built = re.search(r"image:\s*(harness-openmrs-backend:\S+)", args.compose.read_text(encoding="utf-8"))
    if not built or running != built.group(1):
        raise RuntimeError(f"{stack.backend} runs {running}, not the pinned backend image; rerun the setup first")
    backend = stack.sql("SELECT property_value FROM global_property WHERE property = 'querystore.backend';").strip()
    if backend != "elasticsearch":
        raise RuntimeError(f"QueryStore uses the {backend or 'default'} backend, not Elasticsearch")
    say("==> checking that the running index is complete")
    stack.wait_index_complete(timeout=60)
    inputs.update(stack.runtime_inputs())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="querystore-index-") as scratch:
        work = Path(scratch)
        say(f"==> stopping {stack.backend} so the index and completion records agree")
        stack.docker("stop", stack.backend)
        try:
            counts = stack.counts()
            stack.prepare_snapshot_dir()
            stack.es_call("PUT", f"_snapshot/{REPOSITORY}", {"type": "fs", "settings": {"location": SNAPSHOT_DIR}})
            say("==> snapshotting querystore_* indices with the Elasticsearch snapshot API")
            created = stack.es_call(
                "PUT", f"_snapshot/{REPOSITORY}/{SNAPSHOT}?wait_for_completion=true",
                {"indices": "querystore_*", "include_global_state": False},
                timeout=7200,
            )
            if created.get("snapshot", {}).get("state") != "SUCCESS":
                raise RuntimeError(f"snapshot did not succeed: {created}")
            stack.docker("cp", f"{stack.es}:{SNAPSHOT_DIR}", str(work / "snapshot"))
            records = stack.db_client(
                "mariadb-dump", "--no-create-info", "--skip-comments", "--skip-dump-date", "--skip-add-locks",
                stack.db_name, PROGRESS_TABLE,
            )
            (work / PROGRESS_FILE).write_text(records, encoding="utf-8")
            stack.remove_snapshot_repository()
        finally:
            stack.start_backend()

        manifest = {
            "schema_version": SCHEMA,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "inputs": inputs,
            "indices": counts,
            "snapshot": {"repository": REPOSITORY, "name": SNAPSHOT},
        }
        (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        partial = args.output.with_name(args.output.name + ".partial")
        with tarfile.open(partial, "w:gz", compresslevel=6) as archive:
            for name in ("manifest.json", PROGRESS_FILE, "snapshot"):
                archive.add(work / name, arcname=name)
        os.replace(partial, args.output)

    size = args.output.stat().st_size
    say(f"prepared index: {args.output} ({size / 1e9:.2f} GB, sha256 {sha256_file(args.output)})")
    say(f"{sum(counts.values())} documents in {len(counts)} indices")
    say("Publish it beside the HIV baseline package so fresh setups restore it.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("export", "check", "restore"))
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP, help="HIV dump the index belongs to")
    parser.add_argument("--package", type=Path, help="package to check or restore (default: beside the dump)")
    parser.add_argument("--output", type=Path, help="package to write on export (default: beside the dump)")
    parser.add_argument("--querystore-repo", type=Path, default=ROOT / "targets" / "querystore")
    parser.add_argument("--compose", type=Path, default=ROOT / "compose" / "openmrs-2.8-refapp.yml")
    args = parser.parse_args()
    args.dump = args.dump.resolve()
    args.package = (args.package or package_for(args.dump)).resolve()
    args.output = (args.output or package_for(args.dump)).resolve()
    command = {"export": cmd_export, "check": cmd_check, "restore": cmd_restore}[args.command]
    try:
        return command(args)
    except Mismatch as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return MISMATCH
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
