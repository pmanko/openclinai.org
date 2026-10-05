#!/usr/bin/env bash
# Fresh HIV research setup; reuse the umbrella's native tools.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

set -a
. ./.env.chartsearch.example
[ ! -f .env.chartsearch ] || . ./.env.chartsearch
set +a

echo "This imports the HIV baseline into the local OpenMRS database."
make openmrs-source-pair-build chartsearch-esm-build
./scripts/llama-router-up.sh --daemon
make up
make seed "$@"
make querystore-configure
make querystore-reindex

python3 scripts/provision-querystore-service-account.py \
  --base-url "http://localhost:${HARNESS_PROXY_HTTP_PORT}/openmrs" \
  --internal-base-url http://backend:8080/openmrs \
  --admin-user "${CHARTSEARCH_ADMIN_USER}" \
  --admin-password "${CHARTSEARCH_ADMIN_PASSWORD}" \
  --output artifacts/chartsearchai-local/querystore-service.env
set -a
. artifacts/chartsearchai-local/querystore-service.env
set +a
make med-agent-hub-up

. ./scripts/openmrs-settings-lib.sh
set_openmrs_property chartsearchai.llm.engine remote
set_openmrs_property chartsearchai.llm.remote.endpointUrl \
  "${MED_AGENT_LLM_BASE_URL%/}/v1/chat/completions"
set_openmrs_property chartsearchai.llm.remote.modelName gemma-e4b
CHARTSEARCH_PROVIDERS_DEFAULT=hub make chartsearch-configure
python3 scripts/provision-evaluation-users.py

echo "OpenMRS: http://localhost:${HARNESS_PROXY_HTTP_PORT}/openmrs/spa"
echo "Administrator: ${CHARTSEARCH_ADMIN_USER} (configured demo password)."
echo "The seven eval-* accounts use Admin123 unless EVALUATION_PASSWORD is set."
