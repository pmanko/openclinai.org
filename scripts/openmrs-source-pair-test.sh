#!/usr/bin/env bash
set -euo pipefail

ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MVN_BIN="${MVN_BIN:-mvn}"

verify_pinned_source() {
  local repo="$1"
  local label="$2"
  local gitlink_path="$3"
  local head
  local gitlink

  head="$(git -C "${repo}" rev-parse HEAD)"
  gitlink="$(git -C "${ROOT}" rev-parse "HEAD:${gitlink_path}")"
  if [[ "${head}" != "${gitlink}" ]]; then
    echo "${label}: HEAD ${head} does not match parent gitlink ${gitlink}" >&2
    return 1
  fi
  if [[ -n "$(git -C "${repo}" status --porcelain --untracked-files=all)" ]]; then
    echo "${label}: source tree is dirty" >&2
    return 1
  fi

  echo "${label}: ${head}"
}

verify_pinned_source "${ROOT}/targets/querystore" "Querystore" "targets/querystore"
verify_pinned_source "${ROOT}/targets/chartsearchai" "ChartSearchAI" "targets/chartsearchai"
verify_pinned_source "${ROOT}/targets/chartsearchai-esm" "ChartSearchAI ESM" "targets/chartsearchai-esm"

echo "==> installing the pinned Querystore source"
(
  cd "${ROOT}/targets/querystore"
  "${MVN_BIN}" -q -B clean install
)

echo "==> building the pinned ChartSearchAI source against that Querystore artifact"
(
  cd "${ROOT}/targets/chartsearchai"
  "${MVN_BIN}" -q -B clean package
)

echo "OpenMRS source-pair build passed."
