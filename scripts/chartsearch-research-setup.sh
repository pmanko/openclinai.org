#!/usr/bin/env bash
# Fresh HIV research setup and reset; reuse the umbrella's native tools.
#
# By default this resets the stack to the published HIV baseline (environments/
# chartsearch-research/hiv-baseline.json), or to BASELINE=<image>: the OpenMRS
# database and QueryStore's embedded Elasticsearch index, in minutes.
# REBUILD_BASELINE=1 builds the state from the HIV dump instead (several hours of
# embedding); `make hiv-baseline-export hiv-baseline-publish` saves a state.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

set -a
. ./.env.chartsearch.example
[ ! -f .env.chartsearch ] || . ./.env.chartsearch
set +a
HUB_BUILD_REVISION="$(git -C targets/med-agent-hub rev-parse HEAD)"
export HUB_BUILD_REVISION

DUMP="artifacts/demo-data/refapp_28_demo.sql.gz"
for arg in "$@"; do
  case "${arg}" in
    DUMP=?*) DUMP="${arg#DUMP=}" ;;
  esac
done
REBUILD_BASELINE="${REBUILD_BASELINE:-0}"
COMPOSE_FILE="compose/openmrs-2.8-refapp.yml"

if [[ "${REBUILD_BASELINE}" == "1" ]]; then
  if [[ ! -f "${DUMP}" ]]; then
    echo "ERROR: HIV baseline dump not found at ${DUMP}." >&2
    echo "       Download the HIV baseline package described in environments/README.md." >&2
    exit 1
  fi
elif ! python3 scripts/hiv-baseline.py check; then
  echo "       Select a baseline with BASELINE=<image>, or rebuild from the HIV dump with REBUILD_BASELINE=1." >&2
  exit 1
fi

echo "This replaces the local OpenMRS database and QueryStore index."
make openmrs-source-pair-build med-agent-hub-build
docker compose -f "${COMPOSE_FILE}" build backend

if [[ "${REBUILD_BASELINE}" == "1" ]]; then
  make local-stack-up
  make chartsearch-esm-build
  docker exec harness-openmrs-backend sh -c \
    'rm -rf /openmrs/data/.openmrs-lib-cache/chartsearchai /openmrs/data/.openmrs-lib-cache/querystore'
  make seed "$@" TARGET="${OMRS_DB_NAME:-openmrs}"
  make querystore-configure
  ALLOW_QUERYSTORE_INDEX_RESET=1 make querystore-recreate-index
else
  # Load the baseline before OpenMRS first starts, so it never boots on stale data.
  # The gateway's health check passes through to OpenMRS; stop it and the proxy
  # too, so startup brings them back in order instead of failing on a gateway
  # that turned unhealthy while OpenMRS was down for the restore.
  docker compose -f "${COMPOSE_FILE}" stop proxy gateway backend
  ./scripts/stack-up.sh --wait db elasticsearch
  python3 scripts/hiv-baseline.py restore
  docker compose -f "${COMPOSE_FILE}" run --rm --no-deps --entrypoint sh backend -c \
    'rm -rf /openmrs/data/.openmrs-lib-cache/chartsearchai /openmrs/data/.openmrs-lib-cache/querystore'
  make local-stack-up
  make chartsearch-esm-build
  python3 scripts/hiv-baseline.py verify
fi

. ./scripts/openmrs-settings-lib.sh
set_openmrs_property chartsearchai.llm.engine remote
set_openmrs_property chartsearchai.llm.remote.endpointUrl \
  "${MED_AGENT_LLM_BASE_URL%/}/v1/chat/completions"
set_openmrs_property chartsearchai.llm.remote.modelName gemma-4-12b
CHARTSEARCH_PROVIDERS_DEFAULT=hub make chartsearch-configure
python3 scripts/provision-evaluation-users.py

echo "OpenMRS: http://localhost:${HARNESS_PROXY_HTTP_PORT}/openmrs/spa"
echo "Administrator: ${CHARTSEARCH_ADMIN_USER} (configured demo password)."
echo "The seven eval-* accounts use Admin123 unless EVALUATION_PASSWORD is set."
