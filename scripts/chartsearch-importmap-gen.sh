#!/usr/bin/env bash
# Generate the custom importmap.json that Caddy serves at
# /openmrs/spa/importmap.json. We fetch the current baked importmap from
# the running frontend container, then rewrite only the
# @openmrs/esm-chartsearchai-app entry to point at our locally-built
# bundle directory. Re-fetching the base each run keeps unrelated module
# version entries in sync with whatever `:nightly-chartsearch` is
# currently in use — no manual editing of importmap.json ever.
#
# Where the base is fetched from:
#   - the frontend service of the selected local Compose project
#   - cloud generation is not available in this command
#
# Output: artifacts/openmrs/spa-custom/importmap.json

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-${ROOT}/artifacts}"
case "${ARTIFACTS_DIR}" in /*) ;; *) ARTIFACTS_DIR="${ROOT}/${ARTIFACTS_DIR}" ;; esac
ARTIFACT_DIR="${ARTIFACTS_DIR}/openmrs/spa-custom"
COMPOSE=(docker compose)
if [ -n "${COMPOSE_ENV_FILE:-}" ]; then COMPOSE+=(--env-file "${COMPOSE_ENV_FILE}"); fi
COMPOSE+=(-f "${COMPOSE_FILE:-${ROOT}/compose/openmrs-2.8-refapp.yml}")
export HUB_BUILD_REVISION="${HUB_BUILD_REVISION:-$(git -C "${ROOT}/targets/med-agent-hub" rev-parse HEAD)}"
TARGET_NAME="openmrs-esm-chartsearchai-app-multiturn"
OUT="${ARTIFACT_DIR}/importmap.json"
ENTRY_VALUE="./${TARGET_NAME}/openmrs-esm-chartsearchai-app.js"

mkdir -p "${ARTIFACT_DIR}"

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required to rewrite the importmap entry" >&2
  exit 1
fi

if [ "${CLOUD:-0}" = "1" ]; then
  echo "ERROR: cloud importmap generation is pending umbrella U3 migration." >&2
  exit 1
else
  echo "==> fetching live importmap from local frontend container"
  if ! BASE_JSON="$("${COMPOSE[@]}" exec -T frontend cat /usr/share/nginx/html/importmap.json)"; then
    echo "error: cannot read importmap from the selected frontend service" >&2
    echo "  bring the local stack up first (make up)" >&2
    exit 1
  fi
fi

echo "${BASE_JSON}" | jq --arg value "${ENTRY_VALUE}" '.imports."@openmrs/esm-chartsearchai-app" = $value' > "${OUT}"

echo "    wrote ${OUT}"
echo "    chartsearchai entry → $(jq -r '.imports."@openmrs/esm-chartsearchai-app"' "${OUT}")"
echo "    total entries: $(jq '.imports | length' "${OUT}")"
