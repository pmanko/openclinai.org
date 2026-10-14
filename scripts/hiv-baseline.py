#!/usr/bin/env python3
"""Export, publish and restore the HIV research baseline.

The baseline is the finished state of a fresh HIV setup: the OpenMRS database
with every module installed and configured, and QueryStore's embedded
Elasticsearch index. Building it from the HIV dump takes hours, almost all of
it embedding; restoring it takes minutes. It is published as a container image
on GitHub Container Registry and pinned by digest in
environments/chartsearch-research/hiv-baseline.json.

The baseline is keyed to what determines its embeddings: the HIV dataset, the
embedding model and the Elasticsearch major version. A newer OpenMRS
distribution or module pin does not invalidate it: Liquibase migrates the
restored database forward at startup and QueryStore's drift check confirms the
index still covers the data.

  export   maintainer: capture the running, fully indexed stack as a local image
  publish  maintainer: push the exported baseline and pin its digest
  check    no side effects beyond pulling: is a usable baseline pinned?
  restore  fresh setup: load the baseline into the stack with OpenMRS stopped
  verify   fresh setup: after startup, prove modules, model and index match

Exit status 3 means the baseline cannot be used here; nothing was changed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
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
SCHEMA = "openclinai_hiv_baseline.v1"
UNUSABLE = 3
REGISTRY = "ghcr.io/pmanko/openclinai-hiv-baseline"
LOCAL_IMAGE = "openclinai-hiv-baseline:local"
PIN_FILE = ROOT / "environments" / "chartsearch-research" / "hiv-baseline.json"
EXPORT_DIR = ROOT / "artifacts" / "hiv-baseline"
SOURCE_URL = "https://github.com/pmanko/openclinai.org"
REPOSITORY = "openclinai-baseline"
SNAPSHOT = "querystore"
SNAPSHOT_PARENT = "/usr/share/elasticsearch/snapshots"
SNAPSHOT_DIR = f"{SNAPSHOT_PARENT}/es-snapshot"
DATABASE_FILE = "openmrs.sql.gz"
LOCAL_STATE = ROOT / "artifacts" / "chartsearchai-local"
MODULE_PROVENANCE = "module-provenance/querystore-1.0.0-SNAPSHOT.omod.provenance.json"
DEPLOYED_PROVENANCE = "deployed-querystore-omod.json"
CORPUS_RECEIPT = "corpus-provenance.json"
USAGE_TABLES = ("chartsearchai_conversation", "chartsearchai_conversation_turn", "chartsearchai_audit_log")
EMBEDDING_FILES = {
    "model_sha256": "/openmrs/data/chartsearchai/model.onnx",
    "vocab_sha256": "/openmrs/data/chartsearchai/vocab.txt",
}
NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Unusable(Exception):
    """The baseline cannot be used with this checkout or stack."""


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


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def baseline_image(settings: dict[str, str], pin_file: Path) -> str:
    """The pinned baseline, or an explicit HIV_BASELINE_IMAGE a maintainer is testing."""
    if settings.get("HIV_BASELINE_IMAGE"):
        return settings["HIV_BASELINE_IMAGE"]
    if not pin_file.is_file():
        raise Unusable("no HIV baseline has been published for this checkout; "
                       "build one from the HIV dump with REBUILD_BASELINE=1")
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
                raise Unusable(f"cannot pull {self.image}")
        self.container = docker("create", self.image, "/baseline").strip()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.container:
            subprocess.run(["docker", "rm", self.container], capture_output=True)

    def manifest(self) -> dict:
        archive = subprocess.run(["docker", "cp", f"{self.container}:/baseline/manifest.json", "-"],
                                 capture_output=True)
        if archive.returncode != 0:
            raise Unusable(f"{self.image} has no /baseline/manifest.json")
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            member = tar.extractfile("manifest.json")
            manifest = json.load(member) if member else {}
        if manifest.get("schema_version") != SCHEMA:
            raise Unusable(f"{self.image} is not a {SCHEMA} baseline "
                           f"(schema {manifest.get('schema_version')!r})")
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

    # -- database ------------------------------------------------------------
    def db_client(self, program: str, *args: str, stdin: str | None = None) -> str:
        """Run a MariaDB client in the database container with that container's own root login."""
        return docker(
            "exec", "-i", self.db, "sh", "-c",
            f'exec {program} --user=root --password="$MYSQL_ROOT_PASSWORD" "$@"', program, *args,
            stdin=stdin,
        )

    def sql(self, statements: str) -> str:
        return self.db_client("mariadb", "--batch", "--skip-column-names", self.db_name, stdin=statements)

    # -- HTTP ----------------------------------------------------------------
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

    # -- state ---------------------------------------------------------------
    def es_version(self) -> str:
        try:
            return self.es_call("GET", "/", timeout=10)["version"]["number"]
        except (OSError, RuntimeError) as error:
            raise RuntimeError(f"Elasticsearch is not reachable at {self.es_url}: {error}") from None

    def embedding(self) -> dict[str, str]:
        files = list(EMBEDDING_FILES.values())
        sums = {path.strip(): digest
                for digest, path in (line.split(None, 1)
                                     for line in docker("exec", self.backend, "sha256sum", *files).splitlines())}
        return {key: sums.get(path, "") for key, path in EMBEDDING_FILES.items()}

    def modules(self) -> dict[str, dict]:
        rows = self.rest("module?v=custom:(uuid,name,version,started,startupErrorMessage)").get("results", [])
        return {row["uuid"]: row for row in rows}

    def require_modules_started(self) -> dict[str, dict]:
        modules = self.modules()
        failed = [f"  {row.get('name')}: {row.get('startupErrorMessage') or '(no error message)'}"
                  for row in modules.values() if not row.get("started")]
        if failed:
            raise RuntimeError("these OpenMRS modules did not start:\n" + "\n".join(failed))
        return modules

    def querystore_indices(self) -> list[str]:
        rows = self.es_call("GET", "_cat/indices/querystore_*?format=json&h=index&expand_wildcards=all")
        return sorted(row["index"] for row in rows) if isinstance(rows, list) else []

    def counts(self) -> dict[str, int]:
        self.es_call("POST", "querystore_*/_refresh")
        return {index: int(self.es_call("GET", f"{index}/_count")["count"]) for index in self.querystore_indices()}

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
            status = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", self.backend],
                capture_output=True, text=True,
            ).stdout.strip()
            if status == "healthy":
                return
            time.sleep(5)
        raise RuntimeError(f"{self.backend} did not become healthy within {timeout}s")

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
        docker("exec", "-u", "0", self.es, "sh", "-c",
               f"rm -rf '{SNAPSHOT_DIR}' && mkdir -p '{SNAPSHOT_PARENT}' && chown 1000:0 '{SNAPSHOT_PARENT}'")

    def remove_snapshot_repository(self) -> None:
        try:
            self.es_call("DELETE", f"_snapshot/{REPOSITORY}")
        except RuntimeError:
            pass
        docker("exec", "-u", "0", self.es, "rm", "-rf", SNAPSHOT_DIR)


def require_compatible_elasticsearch(built: str, running: str) -> None:
    """Elasticsearch restores snapshots from its own major version, up to its own release."""
    if version_tuple(running)[:1] != version_tuple(built)[:1] or version_tuple(running) < version_tuple(built):
        raise Unusable(f"the baseline's index was made with Elasticsearch {built}; "
                       f"this stack runs {running}, which cannot restore it")


def report_build_differences(manifest: dict, querystore: Path, compose: Path) -> None:
    """Pins that changed since the baseline was built are expected; say what startup will do."""
    built = manifest.get("built_from", {})
    current = {"querystore_source_tree": git(querystore, "rev-parse", "HEAD^{tree}")}
    pin = re.search(r"OPENMRS_BACKEND_IMAGE:\s*(\S+)", compose.read_text(encoding="utf-8"))
    if pin:
        current["backend_image"] = pin.group(1)
    changed = [key for key, value in current.items() if built.get(key) and built[key] != value]
    if changed:
        say(f"    built from other pins ({', '.join(changed)}); OpenMRS migrates the database at startup "
            "and the drift check confirms the index")


def cmd_check(args: argparse.Namespace) -> int:
    with Baseline(baseline_image(load_settings(), args.pin)) as baseline:
        manifest = baseline.manifest()
    say(f"HIV baseline {baseline.image}: dataset {manifest['dataset']['sha256'][:12]}, "
        f"{sum(manifest['indices'].values())} indexed documents")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    with Baseline(baseline_image(settings, args.pin)) as baseline:
        manifest = baseline.manifest()
        require_compatible_elasticsearch(manifest["elasticsearch_version"], stack.es_version())
        if not stack.running(stack.db):
            raise RuntimeError(f"{stack.db} is not running; start the database first")
        report_build_differences(manifest, args.querystore_repo, args.compose)

        if stack.running(stack.backend):
            say(f"==> stopping {stack.backend} so nothing writes during the restore")
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

        say("==> restoring querystore_* indices with the Elasticsearch snapshot API")
        for index in stack.querystore_indices():
            stack.es_call("DELETE", index)
        stack.prepare_snapshot_dir()
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
        counts = stack.counts()
        if counts != manifest["indices"]:
            raise RuntimeError(f"restored document counts {counts} differ from the baseline {manifest['indices']}")
        stack.remove_snapshot_repository()

    built = args.local_state / MODULE_PROVENANCE
    if built.is_file():
        (args.local_state / DEPLOYED_PROVENANCE).write_text(built.read_text(encoding="utf-8"), encoding="utf-8")
    write_corpus_receipt(args.local_state / CORPUS_RECEIPT, manifest, stack.db_name, baseline.image)
    say(f"    restored the database and {sum(counts.values())} documents in {len(counts)} indices")
    return 0


def write_corpus_receipt(path: Path, manifest: dict, database: str, image: str) -> None:
    """Record the dataset the running stack holds, as seeding from the HIV dump does."""
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "validation_corpus.v1",
        "target_database": database,
        "dump_sha256": manifest["dataset"]["sha256"],
        "dump_bytes": manifest["dataset"].get("bytes"),
        "source_schema": manifest["dataset"].get("source_schema"),
        "baseline_image": image,
        "restored_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def cmd_verify(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    with Baseline(baseline_image(settings, args.pin)) as baseline:
        manifest = baseline.manifest()
    stack.wait_backend_healthy()
    say("==> checking that every OpenMRS module started")
    stack.require_modules_started()
    embedding = stack.embedding()
    if embedding != manifest["embedding"]:
        raise Unusable(f"the baseline was embedded with {manifest['embedding']}, but OpenMRS loads "
                       f"{embedding}; rebuild the baseline with REBUILD_BASELINE=1")
    say("==> rebuilding OpenMRS's patient search index for the restored database")
    stack.rest("searchindexupdate", method="POST", timeout=1800)
    say("==> waiting for QueryStore to confirm the restored index")
    stack.wait_index_complete()
    counts = stack.counts()
    if counts != manifest["indices"]:
        raise RuntimeError(f"QueryStore document counts {counts} differ from the baseline {manifest['indices']}")
    written = stack.documents_written()
    if written:
        say(f"QueryStore wrote {written} documents after the restore")
    else:
        say(f"{sum(counts.values())} documents match the baseline; nothing was re-embedded")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    settings = load_settings()
    stack = Stack(settings)
    tree = git(args.querystore_repo, "rev-parse", "HEAD^{tree}")
    if git(args.querystore_repo, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError(f"{args.querystore_repo} has uncommitted changes; a baseline needs the pinned source")
    deployed_path = args.local_state / DEPLOYED_PROVENANCE
    if not deployed_path.is_file():
        raise RuntimeError(f"missing {deployed_path}; build the baseline with REBUILD_BASELINE=1 first")
    deployed = json.loads(deployed_path.read_text(encoding="utf-8"))
    if not deployed.get("source_tree_clean") or deployed.get("source_tree") != tree:
        raise RuntimeError("the running index was not built from this checkout's QueryStore; "
                           "rebuild it with `make chartsearch-research-setup REBUILD_BASELINE=1` first")
    receipt_path = args.local_state / CORPUS_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"missing {receipt_path}; the database was not seeded from the HIV dump")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    pins = args.compose.read_text(encoding="utf-8")
    running = docker("inspect", "-f", "{{.Config.Image}}", stack.backend).strip()
    built = re.search(r"image:\s*(harness-openmrs-backend:\S+)", pins)
    if not built or running != built.group(1):
        raise RuntimeError(f"{stack.backend} runs {running}, not the pinned backend image; rerun the setup first")
    backend = stack.sql("SELECT property_value FROM global_property WHERE property = 'querystore.backend';").strip()
    if backend != "elasticsearch":
        raise RuntimeError(f"QueryStore uses the {backend or 'default'} backend, not Elasticsearch")
    modules = stack.require_modules_started()
    say("==> checking that the running index is complete")
    stack.wait_index_complete(timeout=60)
    core = stack.sql("SELECT property_value FROM global_property WHERE property = 'core.version';").strip()
    pin = re.search(r"OPENMRS_BACKEND_IMAGE:\s*(\S+)", pins)
    manifest = {
        "schema_version": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "sha256": receipt["dump_sha256"],
            "bytes": receipt.get("dump_bytes"),
            "source_schema": receipt.get("source_schema"),
        },
        "embedding": stack.embedding(),
        "elasticsearch_version": stack.es_version(),
        "built_from": {
            "umbrella_commit": git(ROOT, "rev-parse", "HEAD"),
            "querystore_source_tree": tree,
            "backend_image": pin.group(1) if pin else "",
            "core_version": core,
            "modules": {row["uuid"]: row.get("version") for row in modules.values()},
        },
    }

    work = args.output.with_name(args.output.name + ".partial")
    say(f"==> stopping {stack.backend} so nothing changes the database or index during the export")
    docker("stop", stack.backend)
    try:
        # Checked with OpenMRS stopped, so no later write can slip into the published baseline.
        used = stack.sql(" + ".join(f"(SELECT COUNT(*) FROM {table})" for table in USAGE_TABLES).join(
            ("SELECT ", ";"))).strip()
        if used != "0":
            raise RuntimeError(f"ChartSearchAI already holds {used} conversation or audit rows; export the "
                               "baseline straight after REBUILD_BASELINE=1 setup, before anyone uses the stack")
        unfinished = stack.sql("SELECT COUNT(*) FROM querystore_bootstrap_progress "
                               "WHERE status <> 'COMPLETED';").strip()
        if unfinished != "0":
            raise RuntimeError(f"{unfinished} QueryStore resource types are not COMPLETED")
        manifest["indices"] = stack.counts()
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
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
        say(f"==> starting {stack.backend}")
        docker("start", stack.backend)
        stack.wait_backend_healthy()
        docker("start", stack.proxy)

    manifest["database"] = {"file": DATABASE_FILE, "sha256": sha256_file(work / DATABASE_FILE),
                            "bytes": (work / DATABASE_FILE).stat().st_size}
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
    say(f"==> building {LOCAL_IMAGE}")
    if subprocess.run(["docker", "build", "-q", "-t", LOCAL_IMAGE, str(args.output)]).returncode != 0:
        raise RuntimeError(f"could not build {LOCAL_IMAGE}")
    size = sum(path.stat().st_size for path in args.output.rglob("*") if path.is_file())
    say(f"exported baseline: {args.output} ({size / 1e9:.2f} GB), image {LOCAL_IMAGE}")
    say(f"database {manifest['database']['bytes'] / 1e6:.1f} MB; "
        f"{sum(manifest['indices'].values())} documents in {len(manifest['indices'])} indices")
    say(f"Test it with HIV_BASELINE_IMAGE={LOCAL_IMAGE} make chartsearch-research-setup, "
        "then publish it with make hiv-baseline-publish.")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    manifest_path = args.output / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"no exported baseline in {args.output}; run make hiv-baseline-export first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tag = f"hiv-{manifest['dataset']['sha256'][:12]}-{manifest['created_at'][:10].replace('-', '')}"
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
    args.pin.write_text(json.dumps({"image": image, "tag": tag}, indent=2) + "\n", encoding="utf-8")
    say(f"published {image}")
    say(f"pinned in {args.pin}; commit it so fresh setups restore this baseline")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("export", "publish", "check", "restore", "verify"))
    parser.add_argument("--pin", type=Path, default=PIN_FILE, help="file pinning the published baseline")
    parser.add_argument("--querystore-repo", type=Path, default=ROOT / "targets" / "querystore")
    parser.add_argument("--compose", type=Path, default=ROOT / "compose" / "openmrs-2.8-refapp.yml")
    parser.add_argument("--output", type=Path, default=EXPORT_DIR, help="exported baseline directory")
    parser.add_argument("--local-state", type=Path, default=LOCAL_STATE,
                        help="receipts describing what the running stack holds")
    args = parser.parse_args()
    command = {"export": cmd_export, "publish": cmd_publish, "check": cmd_check,
               "restore": cmd_restore, "verify": cmd_verify}[args.command]
    try:
        return command(args)
    except Unusable as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return UNUSABLE
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
