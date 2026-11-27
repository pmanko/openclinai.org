#!/usr/bin/env bash
# Deploy the WA Health Summary cloud stack, server-enforced Google whitelist gate,
# and workspace landing portal onto the OpenClinAI Google Cloud VM (`harness-chartsearch`).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"

WAHS_ENGINE_SRC="${WAHS_ENGINE_SRC:-/Users/pmanko/code/wahs-engine}"
SHL_IPS_SRC="${SHL_IPS_SRC:-/Users/pmanko/code/shl-ips}"
WAHS_MOBILE_SRC="${WAHS_MOBILE_SRC:-/Users/pmanko/code/wahs-mobile-frontend}"
WAHS_BUNDLES_DIR="${WAHS_BUNDLES_DIR:-/Users/pmanko/code/hq/wahs/bundles}"
WAHS_KEYCLOAK_THEMES_DIR="${WAHS_KEYCLOAK_THEMES_DIR:-/Users/pmanko/code/hq/wahs/wahs-environments/base/config/keycloak/themes}"
LOCAL_WAHS_ENV="${LOCAL_WAHS_ENV:-/Users/pmanko/code/hq/wahs/.env}"

for req_dir in \
  "${WAHS_ENGINE_SRC}" \
  "${SHL_IPS_SRC}" \
  "${WAHS_MOBILE_SRC}" \
  "${WAHS_BUNDLES_DIR}" \
  "${WAHS_KEYCLOAK_THEMES_DIR}"
do
  if [ ! -d "${req_dir}" ]; then
    echo "error: required source directory missing: ${req_dir}" >&2
    exit 1
  fi
done

if ! gcp_vm_exists || [ "$(gcp_vm_status)" != "RUNNING" ]; then
  echo "error: VM ${GCP_VM_NAME} is not running" >&2
  exit 1
fi

IP="$(gcp_vm_ip)"
gcp_ssh_keygen_once
SSH_TRANSPORT="ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new"

REMOTE_BASE="${GCP_REMOTE_REPO}/compose/wahs-cloud"
echo "==> preparing remote workspace under ${REMOTE_BASE} on ${IP}"
gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/wahs/cloud-gate ${GCP_REMOTE_REPO}/wahs/demo ${GCP_REMOTE_REPO}/compose/website/gate.d ${GCP_REMOTE_REPO}/compose/website/sites.d ${GCP_REMOTE_REPO}/compose/website/demo.d ${REMOTE_BASE}/src/wahs-engine ${REMOTE_BASE}/src/shl-ips ${REMOTE_BASE}/src/wahs-mobile-frontend ${REMOTE_BASE}/bundles ${REMOTE_BASE}/config/keycloak/themes"

echo "==> syncing cloud-gate, sandbox UI, compose configuration, bundles, themes, and app sources"
rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${ROOT}/wahs/cloud-gate/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/wahs/cloud-gate/"

rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${ROOT}/wahs/demo/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/wahs/demo/"

rsync -avz --delete \
  --exclude '.env' \
  --exclude 'src/' \
  --exclude 'bundles/' \
  --exclude 'config/keycloak/themes/' \
  -e "${SSH_TRANSPORT}" \
  "${ROOT}/compose/wahs-cloud/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/"

rsync -avz --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  -e "${SSH_TRANSPORT}" \
  "${WAHS_ENGINE_SRC}/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/src/wahs-engine/"

rsync -avz --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'build' \
  --exclude '.svelte-kit' \
  --exclude 'test-results' \
  --exclude 'playwright-report' \
  -e "${SSH_TRANSPORT}" \
  "${SHL_IPS_SRC}/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/src/shl-ips/"

rsync -avz --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'test-results' \
  --exclude 'playwright-report' \
  -e "${SSH_TRANSPORT}" \
  "${WAHS_MOBILE_SRC}/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/src/wahs-mobile-frontend/"

rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${WAHS_BUNDLES_DIR}/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/bundles/"

rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${WAHS_KEYCLOAK_THEMES_DIR}/" \
  "${GCP_SSH_USER}@${IP}:${REMOTE_BASE}/config/keycloak/themes/"

echo "==> provisioning remote compose/wahs-cloud/.env without echoing secrets"
python3 - <<'PY' | gcp_ssh "cat > /tmp/.wahs_env_in && chmod 600 /tmp/.wahs_env_in"
import os
from pathlib import Path

local_env = Path(os.environ.get("LOCAL_WAHS_ENV", "/Users/pmanko/code/hq/wahs/.env"))
key = ""
if local_env.is_file():
    for line in local_env.read_text(encoding="utf-8").splitlines():
        if line.startswith("LLM_API_KEY="):
            key = line.split("=", 1)[1].strip().strip("'\"")
            break
print(key)
PY

gcp_ssh "python3 -" <<'REMOTE_PY'
import base64
import os
import secrets
import stat
from pathlib import Path

env_path = Path(os.path.expanduser("~/openclinai.org/compose/wahs-cloud/.env"))
in_path = Path("/tmp/.wahs_env_in")
incoming = in_path.read_text(encoding="utf-8").strip() if in_path.exists() else ""
in_path.unlink(missing_ok=True)

existing = {}
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        existing[k.strip()] = v.strip()

llm_key = incoming or existing.get("LLM_API_KEY", "")
if not llm_key:
    raise SystemExit("error: LLM_API_KEY is missing locally and remotely")


def ensure_secret(key: str, gen) -> str:
    val = existing.get(key, "")
    return val if val else gen()


values = {
    "POSTGRES_PASSWORD": ensure_secret("POSTGRES_PASSWORD", lambda: secrets.token_hex(24)),
    "KEYCLOAK_ADMIN_PASSWORD": ensure_secret("KEYCLOAK_ADMIN_PASSWORD", lambda: secrets.token_hex(24)),
    "KEYCLOAK_WAHS_LOGS_CLIENT_SECRET": ensure_secret("KEYCLOAK_WAHS_LOGS_CLIENT_SECRET", lambda: secrets.token_hex(24)),
    "WAHS_GATE_COOKIE_SECRET": ensure_secret("WAHS_GATE_COOKIE_SECRET", lambda: secrets.token_hex(32)),
    "SHL_PASSCODE_ENCRYPTION_KEY": ensure_secret(
        "SHL_PASSCODE_ENCRYPTION_KEY",
        lambda: base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("="),
    ),
    "LLM_BASE_URL": "https://llm.co.dev.cirg.uw.edu/v1",
    "LLM_API_KEY": llm_key,
    "WAHS_PROVIDER_FLAVOR": "litellm",
    "WAHS_DEFAULT_MODEL": "wahs-26b",
    "WAHS_DEFAULT_PROFILE": "core-enriched",
    "WAHS_PREFERRED_CHART_TOKENS": "16384",
    "WAHS_DEFAULT_TARGET_BUDGET_TOKENS": "16384",
    "WAHS_LLM_TIMEOUT_SECONDS": "180",
    "WAHS_CONTEXT_WINDOW": "65536",
    "WAHS_OLLAMA_NUM_CTX": "65536",
    "WAHS_CACHE_TTL_SECONDS": "1800",
}

lines = [f"{k}={v}" for k, v in values.items()]
env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
print("Wrote ~/openclinai.org/compose/wahs-cloud/.env cleanly (mode 600).")
REMOTE_PY

echo "==> syncing website Caddy drop-in host templates and joining openclinai-edge"
rsync -az -e "${SSH_TRANSPORT}" \
  "${ROOT}/compose/website/Caddyfile" \
  "${ROOT}/compose/website/services.yml" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/compose/website/"

rsync -az -e "${SSH_TRANSPORT}" \
  "${ROOT}/compose/wahs-cloud/caddy/wahs-gate.caddy" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/compose/website/gate.d/wahs-gate.caddy"

rsync -az -e "${SSH_TRANSPORT}" \
  "${ROOT}/compose/wahs-cloud/caddy/wahs-cloud.caddy" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/compose/website/sites.d/wahs-cloud.caddy"

rsync -az -e "${SSH_TRANSPORT}" \
  "${ROOT}/compose/wahs-cloud/caddy/wahs-demo-api.caddy" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/compose/website/demo.d/wahs-demo-api.caddy"

gcp_ssh "docker network create openclinai-edge >/dev/null 2>&1 || true"

echo "==> pruning stale Docker BuildKit cache before sequential image builds"
gcp_ssh "docker builder prune -af >/dev/null 2>&1 || true; docker image prune -f >/dev/null 2>&1 || true"

echo "==> building wahs-cloud images sequentially to avoid ext4/memory spikes on shared VM"
for svc in wahs-auth-gate wahs-engine wahs-mobile-frontend wahs-shl-ips; do
  echo "  -> building ${svc}"
  gcp_ssh "cd ${REMOTE_BASE} && COMPOSE_PARALLEL_LIMIT=1 docker compose --project-name wahs-cloud --env-file .env build ${svc}"
done

echo "==> starting wahs-cloud backend, frontends, and auth-gate"
gcp_ssh "cd ${REMOTE_BASE} && docker compose --project-name wahs-cloud --env-file .env up -d --no-build"
gcp_ssh "docker builder prune -af >/dev/null 2>&1 || true; docker image prune -f >/dev/null 2>&1 || true"

echo "==> checking cloud HAPI seed state (seed only if < 12 patients or FORCE_WAHS_SEED=1)"
remote_patient_count="$(gcp_ssh "docker exec wahs-cloud-engine python -c \"import json, urllib.request; print(json.loads(urllib.request.urlopen('http://fhir-internal:8080/fhir/Patient?_summary=count', timeout=5).read()).get('total', 0))\" 2>/dev/null || echo 0")"
if [ "${FORCE_WAHS_SEED:-0}" = "1" ] || [ "${remote_patient_count:-0}" -lt 12 ]; then
  echo "==> seeding 12 WAHS demo patients and FHIR/Keycloak records (found ${remote_patient_count})"
  gcp_ssh "cd ${REMOTE_BASE} && docker compose --project-name wahs-cloud --env-file .env run --rm wahs-seeder"
else
  echo "==> cloud HAPI already seeded (${remote_patient_count} patients); skipping wahs-seeder"
fi

echo "==> enabling Caddy edge routes on openclinai-website proxy"
gcp_ssh "cd ${GCP_REMOTE_REPO} && docker compose --project-name openclinai-website --env-file compose/website/.env.website -f compose/website/services.yml up -d --no-deps --force-recreate proxy"

echo "==> verifying public endpoints & whitelist enforcement"
wait_http_status() {
  local target_url="$1"
  local extra_header="${2:-}"
  local attempt=0
  local code="000"
  while [ "${attempt}" -lt 20 ]; do
    if [ -n "${extra_header}" ]; then
      code="$(curl -sS -o /dev/null -w '%{http_code}' -H "${extra_header}" --max-time 20 "${target_url}" 2>/dev/null || true)"
    else
      code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "${target_url}" 2>/dev/null || true)"
    fi
    code="${code:-000}"
    if [ "${code}" != "000" ] && [ "${code}" != "502" ] && [ "${code}" != "503" ]; then
      printf '%s\n' "${code}"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  printf '%s\n' "${code}"
}

for protected in \
  "https://wahealth.openclinai.org/" \
  "https://wahs-web.openclinai.org/" \
  "https://wahs-mobile.openclinai.org/"
do
  code="$(wait_http_status "${protected}")"
  echo "  unauthenticated GET ${protected} -> HTTP ${code}"
  if [ "${code}" != "302" ] && [ "${code}" != "401" ]; then
    echo "error: expected 302/401 on unauthenticated ${protected}, got ${code}" >&2
    exit 1
  fi
done

api_code="$(wait_http_status "https://wahs-mobile.openclinai.org/api/chat" "Accept: application/json")"
echo "  unauthenticated JSON GET /api/chat -> HTTP ${api_code}"
if [ "${api_code}" != "401" ]; then
  echo "error: expected 401 on unauthenticated /api/chat, got ${api_code}" >&2
  exit 1
fi

gate_code="$(wait_http_status "https://openclinai.org/wahs/gate/")"
echo "  gate login page GET https://openclinai.org/wahs/gate/ -> HTTP ${gate_code}"
if [ "${gate_code}" != "200" ]; then
  echo "error: expected 200 on https://openclinai.org/wahs/gate/, got ${gate_code}" >&2
  exit 1
fi

for pub in \
  "https://openclinai.org/" \
  "https://reports.openclinai.org/" \
  "https://wahs-demo.openclinai.org/"
do
  pub_code="$(wait_http_status "${pub}")"
  echo "  public site GET ${pub} -> HTTP ${pub_code}"
  if [ "${pub_code}" != "200" ]; then
    echo "error: expected 200 on ${pub}, got ${pub_code}" >&2
    exit 1
  fi
done

echo "==> verifying sandbox engine split-auth contract & live 64k streaming smoke"
demo_bundles_code="$(wait_http_status "https://wahs-demo.openclinai.org/api/engine/v1/wahs/demo-bundles")"
echo "  public GET wahs-demo /api/engine/v1/wahs/demo-bundles -> HTTP ${demo_bundles_code}"
if [ "${demo_bundles_code}" != "200" ]; then
  echo "error: expected 200 on public demo-bundles endpoint, got ${demo_bundles_code}" >&2
  exit 1
fi

demo_chat_unauth="$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"model":"wahs-26b","messages":[{"role":"user","content":"ping"}],"wahs":{"bundle_id":"margaret-chen-polypharmacy"}}' \
  --max-time 20 "https://wahs-demo.openclinai.org/api/engine/v1/chat/completions" 2>/dev/null || echo 000)"
echo "  unauthenticated POST wahs-demo /api/engine/v1/chat/completions -> HTTP ${demo_chat_unauth}"
if [ "${demo_chat_unauth}" != "401" ]; then
  echo "error: expected 401 on unauthenticated sandbox chat/completions, got ${demo_chat_unauth}" >&2
  exit 1
fi

gcp_ssh "docker exec wahs-cloud-sandbox-engine python -c \"
import json, urllib.request

# 1. Verify mounted demo bundles + preview system_prompt
b_resp = json.loads(urllib.request.urlopen('http://127.0.0.1:8080/v1/wahs/demo-bundles', timeout=10).read())
assert b_resp.get('count', 0) >= 10, f'expected >=10 demo bundles, got {b_resp.get(\\\"count\\\")}'

p_req = urllib.request.Request(
    'http://127.0.0.1:8080/v1/wahs/context/preview',
    data=json.dumps({
        'model': 'wahs-26b',
        'messages': [{'role': 'user', 'content': 'What active medications are on my record?'}],
        'wahs': {'bundle_id': 'margaret-chen-polypharmacy', 'target_budget_tokens': 16384, 'profile': 'core-enriched'},
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
)
p_data = json.loads(urllib.request.urlopen(p_req, timeout=30).read())
assert '=== CONDENSED CLINICAL RECORD' in (p_data.get('system_prompt') or ''), 'missing system_prompt in preview'
assert p_data['x_wahs']['condensation']['context_window'] == 65536, 'expected 64k context_window'

# 2. Live streaming smoke turn against UW GPU wahs-26b @ 64k
s_req = urllib.request.Request(
    'http://127.0.0.1:8080/v1/chat/completions',
    data=json.dumps({
        'model': 'wahs-26b',
        'stream': True,
        'max_tokens': 160,
        'messages': [{'role': 'user', 'content': 'List two active medications on my record with citations.'}],
        'wahs': {'bundle_id': 'margaret-chen-polypharmacy', 'target_budget_tokens': 16384, 'profile': 'core-enriched'},
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
)
saw_ctx = False
saw_done = False
content_parts = []
num_ctx = None
with urllib.request.urlopen(s_req, timeout=90) as resp:
    for raw_line in resp:
        line = raw_line.decode('utf-8', errors='replace').strip()
        if not line.startswith('data:'):
            continue
        payload = line[5:].strip()
        if payload == '[DONE]':
            saw_done = True
            break
        obj = json.loads(payload)
        if obj.get('error'):
            raise AssertionError(f'SSE error chunk: {obj}')
        xw = obj.get('x_wahs') or {}
        if xw.get('event') == 'context_ready':
            saw_ctx = True
        cond = xw.get('condensation') or {}
        if cond.get('upstream_num_ctx') is not None:
            num_ctx = cond['upstream_num_ctx']
        for ch in obj.get('choices') or []:
            delta = (ch.get('delta') or {}).get('content')
            if delta:
                content_parts.append(delta)
text = ''.join(content_parts).strip()
assert saw_ctx, 'missing context_ready SSE frame'
assert saw_done, 'missing [DONE] SSE sentinel'
assert len(text) > 15, f'empty/short streamed reply: {text!r}'
assert num_ctx == 65536, f'expected upstream_num_ctx=65536, got {num_ctx}'
print(f'LIVE STREAM SMOKE OK: num_ctx={num_ctx} chars={len(text)} sample={text[:100]!r}')
\""

echo "==> WAHS cloud stack deployed, gated, and live-stream verified cleanly."
