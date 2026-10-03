#!/usr/bin/env bash
# Generate the custom routes.registry.json that Caddy serves at
# /openmrs/spa/routes.registry.json. The OpenMRS app-shell reads this on boot
# to discover which frontend modules and their extensions/workspaces exist.
# If chartsearchai isn't here, the importmap alias is unused — the app-shell
# never imports the bundle, so the patient-banner extension never mounts.
#
# We fetch the baked registry from the running frontend container, then merge
# in the chartsearchai routes.json under the @openmrs/esm-chartsearchai-app
# key. The bundled routes.json (under dist/) is the source of truth for that
# entry — keeping merge logic out of this script means routes-change-only
# updates don't need a script edit.
#
# Where the base is fetched from:
#   - the frontend service of the selected local Compose project
#   - cloud generation is not available in this command
#
# Output: artifacts/openmrs/spa-custom/routes.registry.json

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
OUT="${ARTIFACT_DIR}/routes.registry.json"
ENTRY_NAME="@openmrs/esm-chartsearchai-app"
ROUTES_JSON="${ARTIFACT_DIR}/${TARGET_NAME}/routes.json"

mkdir -p "${ARTIFACT_DIR}"

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required to merge the routes registry" >&2
  exit 1
fi

if [ ! -f "${ROUTES_JSON}" ]; then
  echo "error: ${ROUTES_JSON} not found — run chartsearch-esm-build first" >&2
  exit 1
fi

if [ "${CLOUD:-0}" = "1" ]; then
  echo "ERROR: cloud registry generation is pending umbrella U3 migration." >&2
  exit 1
else
  echo "==> fetching live routes.registry.json from local frontend container"
  if ! BASE_JSON="$("${COMPOSE[@]}" exec -T frontend cat /usr/share/nginx/html/routes.registry.json)"; then
    echo "error: cannot read routes registry from the selected frontend service" >&2
    exit 1
  fi
fi

# Merge in the chartsearchai entry — overwrite if already present (idempotent).
echo "${BASE_JSON}" \
  | jq --arg name "${ENTRY_NAME}" --slurpfile routes "${ROUTES_JSON}" \
      '.[$name] = $routes[0]' \
  > "${OUT}"

echo "    wrote ${OUT}"
echo "    chartsearchai entry present: $(jq -r "has(\"${ENTRY_NAME}\")" "${OUT}")"
echo "    total module entries: $(jq 'length' "${OUT}")"
