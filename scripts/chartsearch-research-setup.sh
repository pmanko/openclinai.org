#!/usr/bin/env bash
# Fresh HIV research setup; reuse the umbrella's native tools.
#
# The QueryStore index comes from the prepared index package beside the HIV dump
# when one is present and matches this checkout; REBUILD_INDEX=1 rebuilds it from
# the HIV data instead (several hours). Both paths end with QueryStore on
# Elasticsearch and a complete index.
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
INDEX_PACKAGE="${QUERYSTORE_INDEX_PACKAGE:-$(dirname "${DUMP}")/$(basename "${DUMP}" | sed -E 's/\.sql(\.gz)?$//').querystore-index.tar.gz}"
REBUILD_INDEX="${REBUILD_INDEX:-0}"

if [[ ! -f "${DUMP}" ]]; then
  echo "ERROR: HIV baseline dump not found at ${DUMP}." >&2
  echo "       Download the HIV baseline package described in environments/README.md." >&2
  exit 1
fi
if [[ "${REBUILD_INDEX}" != "1" ]]; then
  if [[ ! -f "${INDEX_PACKAGE}" ]]; then
    echo "ERROR: no prepared QueryStore index at ${INDEX_PACKAGE}." >&2
    echo "       Download it beside the HIV dump (environments/README.md), or rebuild" >&2
    echo "       the index from the HIV data with REBUILD_INDEX=1 (several hours)." >&2
    exit 1
  fi
  if ! python3 scripts/querystore-index-package.py check --dump "${DUMP}" --package "${INDEX_PACKAGE}"; then
    echo "       Download the prepared index for this checkout, or rebuild with REBUILD_INDEX=1." >&2
    exit 1
  fi
fi

echo "This imports the HIV baseline into the local OpenMRS database."
make openmrs-source-pair-build med-agent-hub-build
docker compose -f compose/openmrs-2.8-refapp.yml build backend
make local-stack-up
make chartsearch-esm-build
docker exec harness-openmrs-backend sh -c \
  'rm -rf /openmrs/data/.openmrs-lib-cache/chartsearchai /openmrs/data/.openmrs-lib-cache/querystore'
make seed "$@" TARGET="${OMRS_DB_NAME:-openmrs}"
make querystore-configure
if [[ "${REBUILD_INDEX}" == "1" ]]; then
  ALLOW_QUERYSTORE_INDEX_RESET=1 make querystore-recreate-index
else
  python3 scripts/querystore-index-package.py restore --dump "${DUMP}" --package "${INDEX_PACKAGE}"
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
