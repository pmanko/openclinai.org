#!/usr/bin/env bash
# Start the harness's live validate dashboard on loopback if it is not already serving.
# It follows the newest run under artifacts/validate, so one server watches every run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${DASH_PORT:-8099}"
RUNTIME_DIR="${ROOT}/artifacts/validate-dashboard"

if curl -fsS --max-time 3 "http://localhost:${PORT}/api/status" >/dev/null 2>&1; then
  echo "    live dashboard: http://localhost:${PORT}"
  exit 0
fi

mkdir -p "${RUNTIME_DIR}"
DASH_PORT="${PORT}" nohup "${UV:-uv}" --directory "${ROOT}/targets/validation-harness" \
  run python scripts/validate-dashboard.py >"${RUNTIME_DIR}/dashboard.log" 2>&1 </dev/null &
echo "$!" >"${RUNTIME_DIR}/dashboard.pid"

for _ in $(seq 1 30); do
  if curl -fsS --max-time 3 "http://localhost:${PORT}/api/status" >/dev/null 2>&1; then
    echo "    live dashboard: http://localhost:${PORT}"
    exit 0
  fi
  sleep 1
done
echo "ERROR: the validate dashboard did not answer on :${PORT}; see ${RUNTIME_DIR}/dashboard.log" >&2
exit 1
