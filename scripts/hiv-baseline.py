#!/usr/bin/env python3
"""Reset to, export and publish HIV research baselines.

A baseline is a saved state of the local stack for evaluation and testing: the
OpenMRS database and QueryStore's embedded Elasticsearch index, packaged as a
container image on GitHub Container Registry. The default baseline is pinned by
digest in environments/chartsearch-research/hiv-baseline.json; BASELINE=<image>
selects any other.

  check    is the selected baseline available? (pulls it)
  restore  load the baseline into the stack with OpenMRS stopped
  verify   after startup: modules started and the index matches the baseline
  export   capture the running stack as the local image openclinai-hiv-baseline:local
  publish  push the exported baseline; without --name it becomes the pinned default

Exit status 3 means the baseline is not available; nothing was changed.
"""
from __future__ import annotations

import argparse
import io
import json
import os
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
SCHEMA = "openclinai_hiv_baseline.v1"
UNAVAILABLE = 3
REGISTRY = "ghcr.io/pmanko/openclinai-hiv-baseline"
LOCAL_IMAGE = "openclinai-hiv-baseline:local"
PIN_FILE = ROOT / "environments" / "chartsearch-research" / "hiv-baseline.json"
EXPORT_DIR = ROOT / "artifacts" / "hiv-baseline"
LOCAL_STATE = ROOT / "artifacts" / "chartsearchai-local"
SOURCE_URL = "https://github.com/pmanko/openclinai.org"
REPOSITORY = "openclinai-baseline"
SNAPSHOT = "querystore"
SNAPSHOT_PARENT = "/usr/share/elasticsearch/snapshots"
SNAPSHOT_DIR = f"{SNAPSHOT_PARENT}/es-snapshot"
DATABASE_FILE = "openmrs.sql.gz"
EMBEDDING_FILES = {
    "model_sha256": "/openmrs/data/chartsearchai/model.onnx",
    "vocab_sha256": "/openmrs/data/chartsearchai/vocab.txt",
}
NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Unavailable(Exception):
    """The selected baseline cannot be found or read."""


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


def docker(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"docker {' '.join(args[:3])} failed: {result.stderr.strip()}")
    return result.stdout


def docker_stream(source: list[str], target: list[str]) -> None:
    """Pipe one docker command's output into another without staging it on the host."""
    producer = subprocess.Popen(["docker", *source], stdout=subprocess.PIPE)
    consumer = subprocess.Popen(["docker", *target], stdin=producer.stdout,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert producer.stdout is not None
    producer.stdout.close()
    _, error = consumer.communicate()
    if producer.wait() != 0 or consumer.returncode != 0:
        raise RuntimeError(f"docker {' '.join(source[:2])} | docker {' '.join(target[:2])} failed: "
                           f"{error.decode(errors='replace').strip()}")


def selected_image(settings: dict[str, str], pin_file: Path) -> str:
    if settings.get("BASELINE"):
        return settings["BASELINE"]
    if not pin_file.is_file():
        raise Unavailable("no default HIV baseline is published; build one from the HIV dump with "
                          "REBUILD_BASELINE=1 or select one with BASELINE=<image>")
    return json.loads(pin_file.read_text(encoding="utf-8"))["image"]


class Baseline:
    """A baseline image's files, read through a created (never started) container."""

    def __init__(self, image: str):
        self.image = image
        self.container = ""

    def __enter__(self) -> "Baseline":
        if subprocess.run(["docker", "image", "inspect", self.image], capture_output=True).returncode != 0:
            say(f"==> pulling {self.image}")
            if subprocess.run(["docker", "pull", self.image]).returncode != 0:
                raise Unavailable(f"cannot pull {self.image}")
        self.container = docker("create", self.image, "/baseline").strip()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.container:
            subprocess.run(["docker", "rm", self.container], capture_output=True)

    def manifest(self) -> dict:
        archive = subprocess.run(["docker", "cp", f"{self.container}:/baseline/manifest.json", "-"],
                                 capture_output=True)
        if archive.returncode != 0:
            raise Unavailable(f"{self.image} has no /baseline/manifest.json")
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            member = tar.extractfile("manifest.json")
            manifest = json.load(member) if member else {}
        if manifest.get("schema_version") != SCHEMA:
            raise Unavailable(f"{self.image} is not a {SCHEMA} baseline")
        return manifest

    def copy_to(self, path: str, container: str, parent: str) -> None:
        docker_stream(["cp", f"{self.container}:/baseline/{path}", "-"], ["cp", "-", f"{container}:{parent}"])


class Stack:
    """The local containers and HTTP endpoints."""

    def __init__(self, settings: dict[str, str]):
        self.backend = settings.get("OPENMRS_BACKEND", "harness-openmrs-backend")
        self.proxy = settings.get("OPENMRS_PROXY", "harness-proxy")
        self.db = settings.get("DB_CONTAINER", "harness-openmrs-db")
        self.es = settings.get("QUERYSTORE_ES_CONTAINER", "harness-querystore-es")
        self.db_name = settings.get("OMRS_DB_NAME", "openmrs")
        self.db_user = settings.get("OMRS_DB_USER", "openmrs")
        self.es_url = settings.get(
            "QUERYSTORE_ES_URL", f"http://localhost:{settings.get('QUERYSTORE_ES_PORT', '9200')}"
        ).rstrip("/")
        self.openmrs = f"http://localhost:{settings.get('HARNESS_PROXY_HTTP_PORT', '8088')}/openmrs"
        user = settings.get("CHARTSEARCH_ADMIN_USER")
        password = settings.get("CHARTSEARCH_ADMIN_PASSWORD")
        if not user or not password:
            raise SystemExit("ERROR: CHARTSEARCH_ADMIN_USER and CHARTSEARCH_ADMIN_PASSWORD must be set")
        self.auth = "Basic " + b64encode(f"{user}:{password}".encode()).decode()

    def db_client(self, program: str, *args: str, stdin: str | None = None) -> str:
        """Run a MariaDB client in the database container with that container's own root login."""
        return docker(
            "exec", "-i", self.db, "sh", "-c",
            f'exec {program} --user=root --password="$MYSQL_ROOT_PASSWORD" "$@"', program, *args,
            stdin=stdin,
        )

    def request(self, method: str, url: str, body: object = None, *, auth: bool = False,
                timeout: float = 120) -> dict | list:
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

    def es_call(self, method: str, path: str, body: object = None, timeout: float = 120) -> dict | list:
        return self.request(method, f"{self.es_url}/{path.lstrip('/')}", body, timeout=timeout)

    def rest(self, path: str, method: str = "GET", timeout: float = 120) -> dict:
        return self.request(method, f"{self.openmrs}/ws/rest/v1/{path}", auth=True, timeout=timeout)

    def embedding(self) -> dict[str, str]:
        output = docker("exec", self.backend, "sha256sum", *EMBEDDING_FILES.values())
        sums = {path.strip(): digest for digest, path in (line.split(None, 1) for line in output.splitlines())}
        return {key: sums.get(path, "") for key, path in EMBEDDING_FILES.items()}

    def require_modules_started(self) -> None:
        rows = self.rest("module?v=custom:(name,started,startupErrorMessage)").get("results", [])
        failed = [f"  {row.get('name')}: {row.get('startupErrorMessage') or '(no error message)'}"
                  for row in rows if not row.get("started")]
        if failed:
            raise RuntimeError("these OpenMRS modules did not start:\n" + "\n".join(failed))

    def index_complete(self) -> bool:
        try:
            return self.rest("querystore/indexingstatus", timeout=30).get("complete") is True
        except (OSError, RuntimeError):
            return False

    def counts(self) -> dict[str, int]:
        self.es_call("POST", "querystore_*/_refresh")
        rows = self.es_call("GET", "_cat/indices/querystore_*?format=json&h=index&expand_wildcards=all")
        return {row["index"]: int(self.es_call("GET", f"{row['index']}/_count")["count"])
                for row in sorted(rows, key=lambda row: row["index"])}

    def documents_written(self) -> int:
        """Documents written to QueryStore's indices since their shards opened (restore or ES start)."""
        stats = self.es_call("GET", "querystore_*/_stats/indexing")
        return sum(int(index["primaries"]["indexing"]["index_total"])
                   for index in stats.get("indices", {}).values())

    @staticmethod
    def running(name: str) -> bool:
        result = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", name],
                                capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def wait_backend_healthy(self, timeout: int = 1800) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", self.backend],
                                    capture_output=True, text=True).stdout.strip()
            if status == "healthy":
                return
            time.sleep(5)
        raise RuntimeError(f"{self.backend} did not become healthy within {timeout}s")

    def reset_snapshot_dir(self) -> None:
        docker("exec", "-u", "0", self.es, "sh", "-c",
               f"rm -rf '{SNAPSHOT_DIR}' && mkdir -p '{SNAPSHOT_PARENT}' && chown 1000:0 '{SNAPSHOT_PARENT}'")

    def remove_snapshot_repository(self) -> None:
        try:
            self.es_call("DELETE", f"_snapshot/{REPOSITORY}")
        except RuntimeError:
            pass
        docker("exec", "-u", "0", self.es, "rm", "-rf", SNAPSHOT_DIR)


def cmd_check(args: argparse.Namespace) -> int:
    with Baseline(selected_image(load_settings(), args.pin)) as baseline:
        manifest = baseline.manifest()
    say(f"HIV baseline {baseline.image}: {sum(manifest['indices'].values())} indexed documents")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    with Baseline(selected_image(settings, args.pin)) as baseline:
        manifest = baseline.manifest()
        if stack.running(stack.backend):
            docker("stop", stack.backend)

        say(f"==> loading the OpenMRS database from {baseline.image}")
        stack.db_client("mariadb", stdin=(
            f"DROP DATABASE IF EXISTS `{stack.db_name}`;\n"
            f"CREATE DATABASE `{stack.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\n"
            f"GRANT ALL PRIVILEGES ON `{stack.db_name}`.* TO '{stack.db_user}'@'%';\nFLUSH PRIVILEGES;\n"))
        baseline.copy_to(DATABASE_FILE, stack.db, "/tmp")
        docker("exec", stack.db, "sh", "-c",
               f'gunzip -c /tmp/{DATABASE_FILE} | mariadb --user=root --password="$MYSQL_ROOT_PASSWORD" '
               f'--default-character-set=utf8mb4 "{stack.db_name}"; status=$?; '
               f'rm -f /tmp/{DATABASE_FILE}; exit $status')

        say("==> restoring QueryStore's index with the Elasticsearch snapshot API")
        for index in stack.counts():
            stack.es_call("DELETE", index)
        stack.reset_snapshot_dir()
        baseline.copy_to("es-snapshot", stack.es, SNAPSHOT_PARENT)
        docker("exec", "-u", "0", stack.es, "chown", "-R", "1000:0", SNAPSHOT_DIR)
        stack.es_call("PUT", f"_snapshot/{REPOSITORY}?verify=false",
                      {"type": "fs", "settings": {"location": SNAPSHOT_DIR, "readonly": True}})
        restored = stack.es_call(
            "POST", f"_snapshot/{REPOSITORY}/{SNAPSHOT}/_restore?wait_for_completion=true",
            {"indices": "querystore_*", "include_global_state": False, "include_aliases": True},
            timeout=7200,
        )
        if restored.get("snapshot", {}).get("shards", {}).get("failed", 1) != 0:
            raise RuntimeError(f"snapshot restore reported failed shards: {restored}")
        stack.remove_snapshot_repository()

    record_restore(args.local_state, manifest, stack.db_name, baseline.image)
    say(f"    restored the database and {sum(manifest['indices'].values())} indexed documents")
    return 0


def record_restore(state: Path, manifest: dict, database: str, image: str) -> None:
    """Record which baseline the running stack holds, as seeding from the HIV dump does."""
    state.mkdir(parents=True, exist_ok=True)
    built = state / "module-provenance" / "querystore-1.0.0-SNAPSHOT.omod.provenance.json"
    if built.is_file():
        (state / "deployed-querystore-omod.json").write_text(built.read_text(encoding="utf-8"), encoding="utf-8")
    dataset = manifest.get("dataset") or {}
    receipt = {
        "schema_version": "validation_corpus.v1",
        "target_database": database,
        "dump_sha256": dataset.get("sha256"),
        "dump_bytes": dataset.get("bytes"),
        "source_schema": dataset.get("source_schema"),
        "baseline_image": image,
        "restored_at": datetime.now(timezone.utc).isoformat(),
    }
    (state / "corpus-provenance.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def cmd_verify(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    with Baseline(selected_image(settings, args.pin)) as baseline:
        manifest = baseline.manifest()
    stack.wait_backend_healthy()
    stack.require_modules_started()
    if stack.embedding() != manifest["embedding"]:
        raise RuntimeError("OpenMRS loads a different embedding model than the baseline was built with; "
                           "rebuild the baseline with REBUILD_BASELINE=1")
    stack.rest("searchindexupdate", method="POST", timeout=1800)
    deadline = time.monotonic() + 600
    while not stack.index_complete():
        if time.monotonic() > deadline:
            raise RuntimeError("QueryStore did not report the restored index complete within 10 minutes")
        time.sleep(10)
    counts = stack.counts()
    if counts != manifest["indices"]:
        raise RuntimeError(f"QueryStore document counts {counts} differ from the baseline {manifest['indices']}")
    written = stack.documents_written()
    say(f"{sum(counts.values())} documents match the baseline; "
        + (f"QueryStore wrote {written} documents after the restore" if written else "nothing was re-embedded"))
    return 0


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def cmd_export(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    if not stack.index_complete():
        raise RuntimeError("QueryStore's index is not complete; wait for indexing to finish")
    receipt_path = args.local_state / "corpus-provenance.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else {}
    manifest = {
        "schema_version": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {"sha256": receipt.get("dump_sha256"), "bytes": receipt.get("dump_bytes"),
                    "source_schema": receipt.get("source_schema")},
        "embedding": stack.embedding(),
        "elasticsearch_version": stack.es_call("GET", "/")["version"]["number"],
        "built_from": {
            "umbrella_commit": git(ROOT, "rev-parse", "HEAD"),
            "querystore_source_tree": git(ROOT / "targets" / "querystore", "rev-parse", "HEAD^{tree}"),
        },
    }

    work = args.output.with_name(args.output.name + ".partial")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    say(f"==> stopping {stack.backend} so the database and index are captured together")
    docker("stop", stack.backend)
    try:
        manifest["indices"] = stack.counts()
        stack.reset_snapshot_dir()
        stack.es_call("PUT", f"_snapshot/{REPOSITORY}", {"type": "fs", "settings": {"location": SNAPSHOT_DIR}})
        say("==> snapshotting QueryStore's index with the Elasticsearch snapshot API")
        created = stack.es_call("PUT", f"_snapshot/{REPOSITORY}/{SNAPSHOT}?wait_for_completion=true",
                                {"indices": "querystore_*", "include_global_state": False}, timeout=7200)
        if created.get("snapshot", {}).get("state") != "SUCCESS":
            raise RuntimeError(f"snapshot did not succeed: {created}")
        docker("cp", f"{stack.es}:{SNAPSHOT_DIR}", str(work / "es-snapshot"))
        stack.remove_snapshot_repository()
        say("==> dumping the OpenMRS database")
        with (work / DATABASE_FILE).open("wb") as output:
            dump = subprocess.run(
                ["docker", "exec", stack.db, "bash", "-c",
                 'set -o pipefail; mariadb-dump --user=root --password="$MYSQL_ROOT_PASSWORD" '
                 '--single-transaction --routines --triggers --default-character-set=utf8mb4 '
                 f'"{stack.db_name}" | gzip -6'],
                stdout=output, stderr=subprocess.PIPE,
            )
        if dump.returncode != 0:
            raise RuntimeError(f"database dump failed: {dump.stderr.decode(errors='replace').strip()}")
    finally:
        docker("start", stack.backend)
        stack.wait_backend_healthy()
        docker("start", stack.proxy)

    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (work / "Dockerfile").write_text(
        "FROM scratch\n"
        f'LABEL org.opencontainers.image.source="{SOURCE_URL}"\n'
        'LABEL org.opencontainers.image.description="OpenClinAI HIV research baseline: '
        'OpenMRS database and QueryStore Elasticsearch snapshot"\n'
        "COPY es-snapshot /baseline/es-snapshot\n"
        f"COPY {DATABASE_FILE} manifest.json /baseline/\n",
        encoding="utf-8",
    )
    shutil.rmtree(args.output, ignore_errors=True)
    os.replace(work, args.output)
    if subprocess.run(["docker", "build", "-q", "-t", LOCAL_IMAGE, str(args.output)]).returncode != 0:
        raise RuntimeError(f"could not build {LOCAL_IMAGE}")
    size = sum(path.stat().st_size for path in args.output.rglob("*") if path.is_file())
    say(f"exported {LOCAL_IMAGE} ({size / 1e9:.2f} GB, {sum(manifest['indices'].values())} indexed documents)")
    say(f"Reset to it with BASELINE={LOCAL_IMAGE} make chartsearch-research-setup; "
        "publish it with make hiv-baseline-publish [NAME=<name>].")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    manifest_path = args.output / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"no exported baseline in {args.output}; run make hiv-baseline-export first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tag = args.name or f"hiv-{manifest['created_at'][:19].replace('-', '').replace(':', '').replace('T', '-')}"
    with tempfile.TemporaryDirectory(prefix="hiv-baseline-") as scratch:
        metadata = Path(scratch) / "metadata.json"
        say(f"==> pushing {REGISTRY}:{tag} for linux/amd64 and linux/arm64")
        pushed = subprocess.run([
            "docker", "buildx", "build", "--platform", "linux/amd64,linux/arm64", "--provenance=false",
            "--push", "--metadata-file", str(metadata), "-t", f"{REGISTRY}:{tag}", str(args.output),
        ])
        if pushed.returncode != 0:
            raise RuntimeError(f"could not push {REGISTRY}:{tag}; log in with docker login ghcr.io first")
        digest = json.loads(metadata.read_text(encoding="utf-8"))["containerimage.digest"]
    image = f"{REGISTRY}@{digest}"
    say(f"published {image} ({REGISTRY}:{tag})")
    if args.name:
        say(f"Reset to it with BASELINE={REGISTRY}:{tag} make chartsearch-research-setup")
    else:
        args.pin.write_text(json.dumps({"image": image, "tag": tag}, indent=2) + "\n", encoding="utf-8")
        say(f"pinned as the default in {args.pin}; commit it")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("check", "restore", "verify", "export", "publish"))
    parser.add_argument("--name", help="publish: push as this tag without changing the default")
    parser.add_argument("--pin", type=Path, default=PIN_FILE, help="file pinning the default baseline")
    parser.add_argument("--output", type=Path, default=EXPORT_DIR, help="exported baseline directory")
    parser.add_argument("--local-state", type=Path, default=LOCAL_STATE,
                        help="receipts describing what the running stack holds")
    args = parser.parse_args()
    command = {"check": cmd_check, "restore": cmd_restore, "verify": cmd_verify,
               "export": cmd_export, "publish": cmd_publish}[args.command]
    try:
        return command(args)
    except Unavailable as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return UNAVAILABLE
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
