#!/usr/bin/env bash
# Deploy the WA Health Summary cloud stack, server-enforced Google whitelist gate,
# and workspace landing portal onto the OpenClinAI Google Cloud VM (`harness-chartsearch`).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"

WAHS_ENGINE_SRC="${WAHS_ENGINE_SRC:-/Users/pmanko/code/worktrees/wahs-engine-s6-12-profiles}"
SHL_IPS_SRC="${SHL_IPS_SRC:-/Users/pmanko/code/worktrees/shl-ips-s6-fullstack-fixes}"
WAHS_MOBILE_SRC="${WAHS_MOBILE_SRC:-/Users/pmanko/code/worktrees/wahs-mobile-s6-fullstack}"
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
gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/wahs/cloud-gate ${GCP_REMOTE_REPO}/compose/website/gate.d ${GCP_REMOTE_REPO}/compose/website/sites.d ${REMOTE_BASE}/src/wahs-engine ${REMOTE_BASE}/src/shl-ips ${REMOTE_BASE}/src/wahs-mobile-frontend ${REMOTE_BASE}/bundles ${REMOTE_BASE}/config/keycloak/themes"

echo "==> syncing cloud-gate, compose configuration, bundles, themes, and app sources"
rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${ROOT}/wahs/cloud-gate/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/wahs/cloud-gate/"

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
    "WAHS_DEFAULT_MODEL": "wahs-26b-kb",
    "WAHS_LLM_TIMEOUT_SECONDS": "180",
    "WAHS_CONTEXT_WINDOW": "32768",
    "WAHS_CHART_BUDGET_CEILING": "16384",
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

gcp_ssh "docker network create openclinai-edge >/dev/null 2>&1 || true"

echo "==> building and starting wahs-cloud backend, frontends, and auth-gate"
gcp_ssh "cd ${REMOTE_BASE} && docker compose --project-name wahs-cloud --env-file .env up -d --build"

echo "==> seeding 12 WAHS demo patients and FHIR/Keycloak records"
gcp_ssh "cd ${REMOTE_BASE} && docker compose --project-name wahs-cloud --env-file .env run --rm wahs-seeder"

echo "==> enabling Caddy edge routes on openclinai-website proxy"
gcp_ssh "cd ${GCP_REMOTE_REPO} && docker compose --project-name openclinai-website --env-file compose/website/.env.website -f compose/website/services.yml up -d --no-deps --force-recreate proxy"

echo "==> verifying public endpoints & whitelist enforcement"
for protected in \
  "https://wahealth.openclinai.org/" \
  "https://wahs-web.openclinai.org/" \
  "https://wahs-mobile.openclinai.org/"
do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --retry 10 --retry-connrefused --retry-delay 2 --max-time 20 "${protected}")"
  echo "  unauthenticated GET ${protected} -> HTTP ${code}"
  if [ "${code}" != "302" ] && [ "${code}" != "401" ]; then
    echo "error: expected 302/401 on unauthenticated ${protected}, got ${code}" >&2
    exit 1
  fi
done

api_code="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Accept: application/json' --max-time 20 https://wahs-mobile.openclinai.org/api/chat)"
echo "  unauthenticated JSON GET /api/chat -> HTTP ${api_code}"
if [ "${api_code}" != "401" ]; then
  echo "error: expected 401 on unauthenticated /api/chat, got ${api_code}" >&2
  exit 1
fi

gate_code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 20 https://openclinai.org/wahs/gate/)"
echo "  gate login page GET https://openclinai.org/wahs/gate/ -> HTTP ${gate_code}"

for pub in \
  "https://openclinai.org/" \
  "https://reports.openclinai.org/" \
  "https://wahs-demo.openclinai.org/"
do
  pub_code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 20 "${pub}")"
  echo "  public site GET ${pub} -> HTTP ${pub_code}"
done

echo "==> WAHS cloud stack deployed and gated cleanly."
