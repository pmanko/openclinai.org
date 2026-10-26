#!/usr/bin/env bash
# Umbrella entry point for the pinned Catalyst query-to-table MVP.
#
# Catalyst and med-agent-hub are sibling target submodules. Other local
# bootstrap dependencies remain disposable checkouts, never nested submodules.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CATALYST_DIR="${ROOT_DIR}/targets/catalyst"
HUB_DIR="${ROOT_DIR}/targets/med-agent-hub"
DEFAULT_MVP_COMPOSE_OVERRIDE_FILE="${ROOT_DIR}/compose/catalyst-mvp-isolated.override.yml"

MVP_COMPOSE_OVERRIDE_FILE="${MVP_COMPOSE_OVERRIDE_FILE:-${DEFAULT_MVP_COMPOSE_OVERRIDE_FILE}}"
if [[ ! -f "${MVP_COMPOSE_OVERRIDE_FILE}" ]]; then
  echo "ERROR: Catalyst MVP compose override does not exist: ${MVP_COMPOSE_OVERRIDE_FILE}" >&2
  exit 1
fi
MVP_COMPOSE_OVERRIDE_FILE="$(
  cd "$(dirname "${MVP_COMPOSE_OVERRIDE_FILE}")"
  printf '%s/%s\n' "$(pwd -P)" "$(basename "${MVP_COMPOSE_OVERRIDE_FILE}")"
)"
export MVP_COMPOSE_OVERRIDE_FILE

# The tracked override intentionally moves the OpenELIS TLS endpoints away
# from the default stack. Keep the URLs used by seed/health aligned with those
# published ports while still allowing callers to supply explicit values.
if [[ "${MVP_COMPOSE_OVERRIDE_FILE}" == "${DEFAULT_MVP_COMPOSE_OVERRIDE_FILE}" ]]; then
  export GATEWAY_PORT="${GATEWAY_PORT:-18000}"
  export CATALYST_UI_PORT="${CATALYST_UI_PORT:-13000}"
  export ANALYTICS_DB_PORT="${ANALYTICS_DB_PORT:-15443}"
  export DATA_PIPES_PORT="${DATA_PIPES_PORT:-18090}"
  export OPENELIS_HTTPS_PORT="${OPENELIS_HTTPS_PORT:-28443}"
  export HAPI_HTTPS_PORT="${HAPI_HTTPS_PORT:-28444}"
  export SUPERSET_PORT="${SUPERSET_PORT:-18088}"
fi

# CATALYST_HUB=shared runs Catalyst on the ChartSearchAI stack's Med Agent Hub
# (`make med-agent-hub-up`, container harness-med-agent-hub on 18081) instead of
# its own, so one Hub serves both products. Give every command the same value:
# the health gate inspects whichever Hub the gateway uses.
CATALYST_HUB="${CATALYST_HUB:-own}"
case "${CATALYST_HUB}" in
  own)
    if [[ "${MVP_COMPOSE_OVERRIDE_FILE}" == "${DEFAULT_MVP_COMPOSE_OVERRIDE_FILE}" ]]; then
      export MED_AGENT_HUB_PORT="${MED_AGENT_HUB_PORT:-18082}"
    fi
    ;;
  shared)
    shared_hub_container="${SHARED_HUB_CONTAINER:-harness-med-agent-hub}"
    export MVP_HUB=external
    export MVP_HUB_CONTAINER="${shared_hub_container}"
    export MVP_GATEWAY_HUB_URL="http://${shared_hub_container}:8080"
    export MED_AGENT_HUB_PORT="${SHARED_HUB_PORT:-18081}"
    export MVP_COMPOSE_OVERRIDE_FILE="${MVP_COMPOSE_OVERRIDE_FILE}:${ROOT_DIR}/compose/catalyst-mvp-shared-hub.override.yml"
    ;;
  *)
    echo "ERROR: CATALYST_HUB must be own or shared (got: ${CATALYST_HUB})." >&2
    exit 2
    ;;
esac

usage() {
  cat <<'EOF'
Usage: scripts/catalyst-mvp.sh {up|ui-update|source-update|seed|warm|health|boot|restart|down|reset|superset-status|superset-import}

  up       Start the Catalyst services against the external model router without changing persisted data.
  ui-update  Rebuild and replace only the UI; leave its dependencies and retained state running.
  source-update  Apply source/network settings to Gateway and Superset only, without rebuilding or seeding.
  seed     Explicitly reload the pinned synthetic OpenELIS fixture and FHIR mart.
  warm     Prime each configured source's schema prefix without seeding, user-query execution, or clinical-row retrieval.
  health   Run the full MVP health and provenance gate.
  boot     First-time initialization: run up, seed, health, and warm in sequence.
  restart  Stop then start services, health-check, and warm sources while retaining all named volumes; does not seed.
  down     Stop the disposable MVP services while retaining all named volumes.
  reset    Remove the disposable MVP state and volumes.
  superset-status  Show the published-bundle import state for this isolated stack.
  superset-import  Import the current published Catalyst bundle into this isolated Superset.
EOF
}

command_name="${1:-}"
if [[ $# -ne 1 ]] || [[ ! "${command_name}" =~ ^(up|ui-update|source-update|seed|warm|health|boot|restart|down|reset|superset-status|superset-import)$ ]]; then
  usage >&2
  exit 2
fi

# Runtime bind mounts must outlive temporary review/build checkouts. Cleanup
# and inspection remain available so an old temporary stack can be retired.
if [[ "${command_name}" =~ ^(up|ui-update|source-update|boot|restart|seed|warm|superset-import)$ ]]; then
  case "${ROOT_DIR}/" in
    /tmp/*|/private/tmp/*|/var/tmp/*|/private/var/tmp/*|"${TMPDIR:-/tmp/}"*)
      echo "ERROR: start Catalyst from a persistent checkout, not ${ROOT_DIR}." >&2
      echo "Keep the workspace checkout under your code directory." >&2
      exit 1
      ;;
  esac
fi

require_pinned_clean_target() {
  local label="$1"
  local relative_path="$2"
  local target_dir="${ROOT_DIR}/${relative_path}"
  local expected actual target_top

  target_top="$(git -C "${target_dir}" rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ "${target_top}" != "${target_dir}" ]]; then
    echo "ERROR: ${label} is not initialized at ${target_dir}." >&2
    echo "Run: git submodule update --init ${relative_path}" >&2
    exit 1
  fi
  expected="$(git -C "${ROOT_DIR}" rev-parse "HEAD:${relative_path}")"
  actual="$(git -C "${target_dir}" rev-parse HEAD)"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "ERROR: ${label} is at ${actual}; the umbrella pins ${expected}." >&2
    echo "Run: git submodule update --init ${relative_path}" >&2
    exit 1
  fi
  if [[ -n "$(git -C "${target_dir}" status --porcelain)" ]]; then
    echo "ERROR: ${label} has uncommitted changes at ${target_dir}." >&2
    exit 1
  fi
}

require_pinned_clean_target "Catalyst" "targets/catalyst"

if [[ -n "$(git -C "${CATALYST_DIR}" ls-tree HEAD .gitmodules)" ]]; then
  echo "ERROR: the pinned Catalyst revision declares nested Git submodules." >&2
  echo "Use a Catalyst revision with runtime bootstrap dependencies instead." >&2
  exit 1
fi

require_pinned_clean_target "med-agent-hub" "targets/med-agent-hub"

# The umbrella owns both product pins and builds the exact sibling Hub checkout.
# Catalyst's separately pinned fallback is only for standalone Catalyst runs.
export MED_AGENT_HUB_CONTEXT="${HUB_DIR}"

if [[ "${CATALYST_HUB}" == "shared" ]] && [[ "${command_name}" =~ ^(up|boot|restart|health|warm)$ ]]; then
  hub_health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "${MVP_HUB_CONTAINER}" 2>/dev/null || true)"
  if [[ "${hub_health}" != "healthy" ]]; then
    echo "ERROR: the shared Hub ${MVP_HUB_CONTAINER} is not running and healthy." >&2
    echo "Start it first: make med-agent-hub-up (or make local-stack-up)." >&2
    exit 1
  fi
fi

run_catalyst() {
  local script_name="$1"
  shift
  "${CATALYST_DIR}/scripts/${script_name}" "$@"
}

case "${command_name}" in
  up) run_catalyst mvp-up.sh ;;
  ui-update) CATALYST_DIR="${CATALYST_DIR}" "${ROOT_DIR}/scripts/catalyst-ui-update.sh" ;;
  source-update) CATALYST_DIR="${CATALYST_DIR}" "${ROOT_DIR}/scripts/catalyst-source-update.sh" ;;
  seed) run_catalyst mvp-seed.sh ;;
  warm) run_catalyst mvp-warm.sh ;;
  health) run_catalyst mvp-health.sh ;;
  boot)
    run_catalyst mvp-up.sh
    run_catalyst mvp-seed.sh
    run_catalyst mvp-health.sh
    run_catalyst mvp-warm.sh
    ;;
  restart)
    run_catalyst mvp-down.sh
    run_catalyst mvp-up.sh
    run_catalyst mvp-health.sh
    run_catalyst mvp-warm.sh
    ;;
  down) run_catalyst mvp-down.sh ;;
  reset) run_catalyst mvp-reset.sh ;;
  superset-status) run_catalyst mvp-superset.sh status ;;
  superset-import) run_catalyst mvp-superset.sh import ;;
esac
