"""Native preparation routing; these doubles do not prove application readiness."""

import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("existing", ("", "other.setting=kept\nreferencedemodata.createDemoPatients=true\n"))
def test_backend_disables_stock_generation_before_native_startup_on_every_boot(tmp_path, existing):
    home = tmp_path / "openmrs"
    model = home / "data/chartsearchai"
    model.mkdir(parents=True)
    for filename in ("model.onnx", "vocab.txt"):
        (model / filename).write_text("already installed\n")
    extra = home / "openmrs-extra.properties"
    extra.write_text(existing)
    captured = home / "captured.properties"
    executable(home / "startup.sh", 'cp "$OMRS_HOME/openmrs-extra.properties" "$OMRS_HOME/captured.properties"\n')
    fake = tmp_path / "bin"
    fake.mkdir()
    executable(fake / "id", "printf '1001\\n'\n")
    executable(fake / "curl", "exit 19\n")
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}", "OMRS_HOME": str(home)}
    for _ in range(2):
        result = subprocess.run(["sh", str(ROOT / "compose/backend-init.sh")], env=env,
                                capture_output=True, text=True, check=False, timeout=10)
        assert result.returncode == 0, result.stderr
        lines = captured.read_text().splitlines()
        assert lines.count("referencedemodata.createDemoPatients=false") == 1
        assert "referencedemodata.createDemoPatients=true" not in lines
        if existing:
            assert "other.setting=kept" in lines


def executable(path, body):
    path.write_text("#!/usr/bin/env bash\nset -eu\n" + body)
    path.chmod(0o755)


def core_fixture(tmp_path):
    root = tmp_path / "workspace"
    (root / "scripts").mkdir(parents=True)
    (root / "compose").mkdir()
    shutil.copy2(ROOT / "scripts/chartsearchai-local.sh", root / "scripts/chartsearchai-local.sh")
    (root / "compose/openmrs-2.8-refapp.yml").write_text("services: {}\n")
    artifacts = root / "artifacts/environments/study"
    manifests = artifacts / "chartsearchai-local/module-provenance"
    manifests.mkdir(parents=True)
    for name in ("chartsearchai", "querystore"):
        text = f"{name}-source-identity\n"
        (manifests / f"{name}-1.0.0-SNAPSHOT.omod.provenance.json").write_text(text)
        (manifests.parent / f"deployed-{name}-omod.json").write_text(text)
    (artifacts / "openmrs/spa-custom").mkdir(parents=True)
    sentinel = root / "unexpected-shell-execution"
    (root / ".env.chartsearch").write_text(f"HUB_TIMEZONE=$(touch {sentinel})\n")
    fake = tmp_path / "bin"
    fake.mkdir()
    log = tmp_path / "native-calls.log"
    executable(fake / "git", "printf '%040d\\n' 1\n")
    executable(fake / "python3", 'printf "python3 %s\\n" "$*" >> "$CALL_LOG"\n')
    executable(fake / "docker", '''printf "docker %s\\n" "$*" >> "$CALL_LOG"
case "$*" in
  *"ps -q backend"*) printf 'owned-backend-id\\n' ;;
  "inspect -f "*) printf 'healthy\\n' ;;
esac
''')
    executable(fake / "curl", '''printf "curl %s\\n" "$*" >> "$CALL_LOG"
case "$*" in *"/__proxy_health"*) exit 0 ;; *) exit 1 ;; esac
''')
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}", "CALL_LOG": str(log),
           "OPENCLINAI_ENVIRONMENT": "study", "COMPOSE_PROJECT_NAME": "openclinai-study",
           "COMPOSE_ENV_FILE": os.devnull, "STACK_ARTIFACTS_DIR": str(artifacts),
           "ARTIFACTS_DIR": str(artifacts), "CHARTSEARCH_LOCAL_BUILD": "never",
           "HARNESS_PROXY_HTTP_PORT": "18108"}
    env.pop("HUB_TIMEZONE", None)
    return root, artifacts, sentinel, log, env


@pytest.mark.parametrize("check_only", (False, True))
def test_core_preparation_uses_selected_resources_without_clinical_mutations(tmp_path, check_only):
    root, artifacts, sentinel, log, env = core_fixture(tmp_path)
    before = {str(p): p.read_bytes() for p in artifacts.rglob("*") if p.is_file()}
    result = subprocess.run(["bash", str(root / "scripts/chartsearchai-local.sh"), "--prepare-core"]
                            + (["--check"] if check_only else []), cwd=root, env=env,
                            capture_output=True, text=True, check=False, timeout=15)
    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()
    calls = log.read_text().splitlines()
    assert not any(term in call for call in calls for term in (
        "8077", "provision-", "configure.sh", "seed-local", "warm-hub", "probe-chartsearchai", "med-agent-hub-up"))
    assert any(f"--artifact {artifacts}/openmrs/" in call for call in calls)
    compose_calls = [call for call in calls if call.startswith("docker compose")]
    assert compose_calls
    assert all("--env-file /dev/null" in call for call in compose_calls)
    if check_only:
        assert not any(" up " in call or " restart " in call or " exec " in call for call in calls)
    else:
        assert any("up -d --build db elasticsearch backend frontend gateway proxy" in call for call in calls)
        assert any("ps -q backend" in call for call in calls)
        assert not any("harness-openmrs" in call for call in calls)
        assert "provider settings" in result.stdout
    assert {str(p): p.read_bytes() for p in artifacts.rglob("*") if p.is_file()} == before


def test_changed_module_cache_refresh_targets_compose_backend_service(tmp_path):
    root, artifacts, _, log, env = core_fixture(tmp_path)
    deployed = artifacts / "chartsearchai-local/deployed-chartsearchai-omod.json"
    deployed.write_text("older identity\n")
    result = subprocess.run(["bash", str(root / "scripts/chartsearchai-local.sh"), "--prepare-core"],
                            cwd=root, env=env, capture_output=True, text=True, check=False, timeout=15)
    assert result.returncode == 0, result.stderr
    calls = log.read_text().splitlines()
    assert any("exec -T backend sh -c rm -rf /openmrs/data/.openmrs-lib-cache/chartsearchai" in call for call in calls)
    assert any("restart backend" in call for call in calls)
    assert not any("harness-openmrs-backend" in call for call in calls)
    assert deployed.read_text() == "chartsearchai-source-identity\n"


def test_native_make_build_targets_stage_only_selected_artifact_directory(tmp_path):
    artifacts = tmp_path / "selected artifacts"
    result = subprocess.run(["make", "--dry-run", "chartsearch-build", "chartsearch-esm-build",
                             f"ARTIFACTS_DIR={artifacts}"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    assert f'"{artifacts}/openmrs/modules"' in result.stdout
    assert f'"{artifacts}/openmrs/chartsearchai-esm.provenance.json"' in result.stdout
    assert "mkdir -p artifacts/openmrs/modules" not in result.stdout


@pytest.mark.parametrize("script,filename", (("chartsearch-importmap-gen.sh", "importmap.json"),
                                            ("chartsearch-registry-gen.sh", "routes.registry.json")))
def test_frontend_metadata_helpers_use_compose_service_and_selected_destination(tmp_path, script, filename):
    fake = tmp_path / "bin"
    fake.mkdir()
    log = tmp_path / "native-calls.log"
    artifacts = tmp_path / "selected artifacts"
    routes = artifacts / "openmrs/spa-custom/openmrs-esm-chartsearchai-app-multiturn/routes.json"
    routes.parent.mkdir(parents=True)
    routes.write_text('{"routes": []}\n')
    executable(fake / "docker", '''printf '%s\\n' "$*" >> "$CALL_LOG"
case "$*" in *"exec -T frontend cat "*) printf '{"imports": {}}\\n' ;; *) exit 1 ;; esac
''')
    executable(fake / "jq", "printf '{}\\n'\n")
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}", "CALL_LOG": str(log),
           "COMPOSE_PROJECT_NAME": "openclinai-study", "COMPOSE_ENV_FILE": os.devnull,
           "ARTIFACTS_DIR": str(artifacts), "HUB_BUILD_REVISION": "a" * 40, "CLOUD": "0"}
    result = subprocess.run(["bash", str(ROOT / "scripts" / script)], cwd=ROOT, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert (artifacts / "openmrs/spa-custom" / filename).is_file()
    calls = log.read_text().splitlines()
    assert len(calls) == 1
    assert "compose --env-file /dev/null" in calls[0]
    assert f"exec -T frontend cat /usr/share/nginx/html/{filename}" in calls[0]
    assert "harness-openmrs" not in calls[0]


@pytest.mark.parametrize("invalid_target,stop_fails,missing_password", (
    (True, False, False), (False, True, False), (False, False, True)))
def test_demo_seed_refuses_unsafe_identifiers_and_failed_backend_stop_before_database_changes(
        tmp_path, invalid_target, stop_fails, missing_password):
    root = tmp_path / "workspace"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/seed-local.sh", root / "scripts/seed-local.sh")
    dump = tmp_path / "demo.sql"
    dump.write_text("placeholder\n")
    fake = tmp_path / "bin"
    fake.mkdir()
    log = tmp_path / "native-calls.log"
    executable(fake / "python3", "exit 0\n")
    executable(fake / "sleep", "exit 0\n")
    executable(fake / "curl", '''case "$*" in *"module?"*) printf '{"results": []}\\n' ;; *) printf '200' ;; esac
''')
    executable(fake / "docker", '''printf '%s\\n' "$*" >> "$CALL_LOG"
if [ "$1" = stop ] && [ "$STOP_FAILS" = 1 ]; then exit 1; fi
''')
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}", "CALL_LOG": str(log),
           "STOP_FAILS": str(int(stop_fails)), "DB_CONTAINER": "owned-db-id",
           "CHARTSEARCH_ADMIN_PASSWORD": "" if missing_password else secrets.token_urlsafe(24),
           "OPENMRS_BACKEND": "owned-backend-id", "ARTIFACTS_DIR": str(root / "owned-artifacts")}
    target = "openmrs`; DROP DATABASE other; --" if invalid_target else "openmrs"
    result = subprocess.run(["bash", str(root / "scripts/seed-local.sh"), "--dump", str(dump),
                             "--target", target], cwd=root, env=env, capture_output=True, text=True,
                            check=False, timeout=10)
    assert result.returncode != 0
    calls = log.read_text().splitlines() if log.exists() else []
    assert not any("mariadb" in call or "start " in call for call in calls)
    if invalid_target or missing_password:
        assert calls == []
        if missing_password:
            assert "configure CHARTSEARCH_ADMIN_PASSWORD in private settings" in result.stderr
    else:
        assert calls == ["exec owned-db-id sh -c true", "stop owned-backend-id"]


@pytest.mark.parametrize("api_ready,modules_present,clinical_changed", (
    (True, True, False), (False, True, False), (True, False, False), (True, True, True),
    ("denied", True, False)))
def test_demo_seed_uses_selected_credentials_receipt_and_never_restarts_on_timeout(
        tmp_path, api_ready, modules_present, clinical_changed):
    root = tmp_path / "workspace"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/seed-local.sh", root / "scripts/seed-local.sh")
    dump = tmp_path / "demo.sql"
    dump.write_text("placeholder\n")
    fake = tmp_path / "bin"
    fake.mkdir()
    log = tmp_path / "native-calls.log"
    executable(fake / "python3", '''if [ "${1:-}" = - ]; then
  printf 'receipt %s\\n' "$4" >> "$CALL_LOG"
elif [ "${1:-}" = -c ]; then
  exec "$REAL_PYTHON" "$@"
else printf 'verified\\n' >> "$CALL_LOG"; fi
''')
    executable(fake / "sleep", "exit 0\n")
    executable(fake / "curl", '''args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [ "${args[$i]}" = -u ]; then
    [ "${args[$((i+1))]}" = "$CHARTSEARCH_ADMIN_USER:$CHARTSEARCH_ADMIN_PASSWORD" ] || exit 9
  fi
done
case "$*" in
  *"module?"*)
    if [ "$MODULES_PRESENT" = 1 ]; then
      printf '{"results": [{"uuid":"chartsearchai", "name":"ChartSearchAI", "started":true}, {"uuid":"querystore", "name":"QueryStore", "started":true}]}\\n'
    else printf '{"results": []}\\n'; fi ;;
  *) if [ "$API_READY" = 1 ]; then printf '200';
     elif [ "$API_READY" = denied ]; then printf '401'; else printf '503'; fi ;;
esac
''')
    executable(fake / "docker", '''printf "%s\\n" "$*" >> "$CALL_LOG"
case "$*" in *"mariadb-dump"*)
  if [ -f "$HASH_MARKER" ] && [ "$CLINICAL_CHANGED" = 1 ]; then printf 'generated record\\n';
  else printf 'original record\\n'; fi
  touch "$HASH_MARKER" ;;
esac
''')
    artifacts = root / "selected-artifacts"
    test_password = secrets.token_urlsafe(24)
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}", "CALL_LOG": str(log),
           "DB_CONTAINER": "owned-db-id", "OPENMRS_BACKEND": "owned-backend-id",
           "CHARTSEARCH_ADMIN_USER": "study-admin", "CHARTSEARCH_ADMIN_PASSWORD": test_password,
           "API_READY": str(int(api_ready)) if isinstance(api_ready, bool) else api_ready,
           "MODULES_PRESENT": str(int(modules_present)),
           "CLINICAL_CHANGED": str(int(clinical_changed)), "HASH_MARKER": str(tmp_path / "hash-marker"),
           "REAL_PYTHON": sys.executable, "ARTIFACTS_DIR": str(artifacts)}
    result = subprocess.run(["bash", str(root / "scripts/seed-local.sh"), "--dump", str(dump),
                             "--no-reindex"], cwd=root, env=env, capture_output=True, text=True,
                            check=False, timeout=15)
    calls = log.read_text().splitlines()
    assert calls[0] == "verified"
    assert calls.count("stop owned-backend-id") == 1
    assert calls.count("start owned-backend-id") == 1
    assert not any("restart" in call for call in calls)
    if api_ready is True and modules_present and not clinical_changed:
        assert result.returncode == 0, result.stderr
        assert calls[-1] == f"receipt {artifacts}/chartsearchai-local/corpus-provenance.json"
    else:
        assert result.returncode != 0
        if api_ready == "denied":
            assert "rejected the configured administrator credentials or access" in result.stderr
        elif not api_ready:
            assert "No automatic restart or reset" in result.stderr
        elif not modules_present:
            assert "chartsearchai: required module is missing" in result.stderr
        else:
            assert "clinical rows changed during startup" in result.stderr
        assert not any(call.startswith("receipt") for call in calls)
