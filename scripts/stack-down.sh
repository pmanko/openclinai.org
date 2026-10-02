#!/usr/bin/env bash
# scripts/stack-down.sh
# Bring down the umbrella compose stack.
#
# Usage:
#   ./scripts/stack-down.sh             # stop containers; KEEP volumes (data persists)
#   ./scripts/stack-down.sh --volumes   # stop AND nuke volumes (fresh on next up)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
# Compose interpolates build arguments even during teardown; no build occurs here.
export HUB_BUILD_REVISION="${HUB_BUILD_REVISION:-teardown}"
COMPOSE_FILE="${COMPOSE_FILE:-compose/openmrs-2.8-refapp.yml}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-}"
EXTRA=()
for arg in "$@"; do
  case "$arg" in
    --volumes|-v) EXTRA+=(-v) ;;
    *) echo "unknown arg: $arg" >&2; exit 1 ;;
  esac
done
COMPOSE=(docker compose)
if [[ -n "${COMPOSE_ENV_FILE}" ]]; then
  COMPOSE+=(--env-file "${COMPOSE_ENV_FILE}")
fi
COMPOSE+=(-f "${COMPOSE_FILE}")
# The alternate-value form expands to zero arguments for an empty array under
# macOS Bash 3.2 + `set -u`; plain "${EXTRA[@]}" raises "unbound variable".
"${COMPOSE[@]}" down "${EXTRA[@]+"${EXTRA[@]}"}"
