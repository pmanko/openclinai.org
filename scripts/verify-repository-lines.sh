#!/usr/bin/env bash
set -euo pipefail

ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
allow_workspace_branch=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-workspace-branch)
      allow_workspace_branch=1
      ;;
    *)
      printf 'Usage: %s [--allow-workspace-branch]\n' \
        "${0##*/}" >&2
      exit 2
      ;;
  esac
  shift
done

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

require_clean_remote_commit() {
  local repo="$1"
  local label="$2"

  [[ -e "$repo/.git" ]] || fail "$label is not an initialized Git worktree"
  [[ -z "$(git -C "$repo" status --porcelain --untracked-files=all)" ]] \
    || fail "$label source tree is dirty"
  git -C "$repo" branch -r --contains HEAD | grep -q 'origin/' \
    || fail "$label HEAD is not available from its origin remote"
}

require_parent_pin() {
  local repo="$1"
  local label="$2"
  local path="$3"
  local head
  local pin

  head="$(git -C "$repo" rev-parse HEAD)"
  pin="$(git -C "$ROOT" rev-parse "HEAD:$path")"
  [[ "$head" == "$pin" ]] \
    || fail "$label checkout $head does not match the umbrella pin $pin"
}

require_main_commit() {
  local repo="$1"
  local label="$2"
  local path="${3:-}"

  git -C "$repo" show-ref --verify --quiet refs/remotes/origin/main \
    || fail "$label is missing origin/main; fetch its remote"
  git -C "$repo" merge-base --is-ancestor HEAD origin/main \
    || fail "$label HEAD has not been merged into origin/main"
  if [[ -n "$path" ]]; then
    require_parent_pin "$repo" "$label" "$path"
  fi
}

require_clean_remote_commit "$ROOT" "OpenClinAI workspace"
if [[ "$allow_workspace_branch" == 0 ]]; then
  require_main_commit "$ROOT" "OpenClinAI workspace"
fi

for spec in \
  "targets/chartsearchai|ChartSearchAI" \
  "targets/chartsearchai-esm|ChartSearchAI ESM" \
  "targets/querystore|QueryStore"; do
  path="${spec%%|*}"
  label="${spec#*|}"
  require_clean_remote_commit "$ROOT/$path" "$label"
  require_parent_pin "$ROOT/$path" "$label" "$path"
done

require_clean_remote_commit "$ROOT/targets/med-agent-hub" "med-agent-hub"
require_main_commit \
  "$ROOT/targets/med-agent-hub" "med-agent-hub" "targets/med-agent-hub"

for spec in \
  "targets/catalyst|Catalyst" \
  "targets/validation-harness|validation harness"; do
  path="${spec%%|*}"
  label="${spec#*|}"
  require_clean_remote_commit "$ROOT/$path" "$label"
  require_parent_pin "$ROOT/$path" "$label" "$path"
done

printf 'Repository lines match the approved ownership policy.\n'
