#!/usr/bin/env bash
# Launch the llama.cpp Router Mode server behind med-agent-hub profiles
# (GGUF + OpenAI-compatible API on :8077). Product clients never call it directly.
#
# Why HF_HOME is redirected to an empty dir: build 9430's router auto-publishes
# EVERY model in the HF cache as an extra preset on top of scripts/llama-router.ini
# (with default/untuned settings — no DRY, no seed), and there is no flag to disable
# it. All INI sections use local model= paths (stable symlinks under
# LLAMA_MODEL_DIR -> the real GGUF files), so pointing HF_HOME at an empty dir costs
# nothing at runtime and makes /v1/models == exactly the INI's sections.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EMPTY_HF="${HOME}/.cache/llama-router-emptyhf"
ROUTER_PORT="${LLAMA_ROUTER_PORT:-8077}"
MODEL_DIR="${LLAMA_MODEL_DIR:-${HOME}/.cache/llama-router-models}"
MODELS_FILE="${LLAMA_MODELS_MANIFEST:-${ROOT}/scripts/llama-router.models.tsv}"
RUNTIME_DIR="${LLAMA_ROUTER_RUNTIME_DIR:-${ROOT}/artifacts/llama-router}"
RUNTIME_MODELS="${RUNTIME_DIR}/models"
READY_TIMEOUT_SECONDS="${LLAMA_ROUTER_READY_TIMEOUT_SECONDS:-60}"
DAEMON=0
MODE="run"
TARGET_ALIAS=""

sha256_file() {
  local path="$1" real_path meta_file cur_meta cached_meta cached_sha computed_sha
  real_path="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${path}")"
  cur_meta="$(python3 -c 'import os,sys; st=os.stat(sys.argv[1]); print(f"{st.st_size}:{st.st_mtime_ns}")' "${real_path}")"
  meta_file="${real_path}.sha256meta"
  if [ -f "${meta_file}" ]; then
    IFS='|' read -r cached_meta cached_sha <"${meta_file}" || true
    if [ "${cached_meta}" = "${cur_meta}" ] && [ "${#cached_sha}" -eq 64 ]; then
      printf '%s\n' "${cached_sha}"
      return 0
    fi
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    computed_sha="$(sha256sum "${real_path}" | awk '{print $1}')"
  else
    computed_sha="$(shasum -a 256 "${real_path}" | awk '{print $1}')"
  fi
  printf '%s|%s\n' "${cur_meta}" "${computed_sha}" >"${meta_file}" 2>/dev/null || true
  printf '%s\n' "${computed_sha}"
}

model_record() {
  local alias="$1"
  awk -F '\t' -v wanted="${alias}" '
    $0 !~ /^#/ && NF >= 4 && $1 == wanted { print; found = 1; exit }
    END { if (!found) exit 1 }
  ' "${MODELS_FILE}"
}

verify_model() {
  local alias="$1" require_present="${2:-1}" record filename expected_sha actual path
  record="$(model_record "${alias}")" || {
    echo "ERROR: unsupported llama-router model alias: ${alias}" >&2
    return 2
  }
  IFS=$'\t' read -r _ filename expected_sha _ <<<"${record}"
  path="${MODEL_DIR}/${alias}.gguf"
  if [ ! -f "${path}" ] && [ -f "${MODEL_DIR}/${filename}" ]; then
    path="${MODEL_DIR}/${filename}"
  fi
  if [ ! -f "${path}" ]; then
    if [ "${require_present}" = "1" ]; then
      echo "ERROR: pinned model is missing: ${MODEL_DIR}/${alias}.gguf (${filename})" >&2
      return 1
    fi
    return 0
  fi
  actual="$(sha256_file "${path}")"
  if [ "${actual}" != "${expected_sha}" ]; then
    echo "ERROR: model checksum mismatch for ${alias}: ${path}" >&2
    echo "  expected ${expected_sha}" >&2
    echo "  actual   ${actual}" >&2
    return 1
  fi
  echo "verified ${alias}: ${path} (${actual})"
}

verify_models() {
  local require_present="${1:-1}" alias
  while IFS=$'\t' read -r alias _; do
    case "${alias}" in
      ''|'#'*) continue ;;
    esac
    verify_model "${alias}" "${require_present}"
  done <"${MODELS_FILE}"
}

fetch_model() {
  local alias="$1" record filename expected_sha source_url path partial actual
  record="$(model_record "${alias}")" || {
    echo "ERROR: unsupported llama-router model alias: ${alias}" >&2
    return 2
  }
  IFS=$'\t' read -r _ filename expected_sha source_url <<<"${record}"
  mkdir -p "${MODEL_DIR}"
  path="${MODEL_DIR}/${alias}.gguf"
  if [ -f "${path}" ]; then
    verify_model "${alias}" 1
    return
  fi
  partial="${path}.partial"
  echo "fetching ${alias} (${filename}) from pinned revision"
  if [ -f "${partial}" ]; then
    curl --fail --location --continue-at - --output "${partial}" "${source_url}"
  else
    curl --fail --location --output "${partial}" "${source_url}"
  fi
  actual="$(sha256_file "${partial}")"
  if [ "${actual}" != "${expected_sha}" ]; then
    rm -f "${partial}"
    echo "ERROR: downloaded model checksum mismatch for ${alias}" >&2
    echo "  expected ${expected_sha}" >&2
    echo "  actual   ${actual}" >&2
    return 1
  fi
  mv "${partial}" "${path}"
  echo "installed ${alias}: ${path} (${actual})"
}

fetch_all_models() {
  local alias
  while IFS=$'\t' read -r alias _; do
    case "${alias}" in
      ''|'#'*) continue ;;
    esac
    fetch_model "${alias}"
  done <"${MODELS_FILE}"
}

ensure_profile_models() {
  local levels_file="${1:-${ROOT}/targets/med-agent-hub/server/levels.yaml}"
  if [ ! -f "${levels_file}" ]; then
    echo "ERROR: levels.yaml not found at ${levels_file}" >&2
    return 1
  fi
  local aliases alias
  aliases="$(python3 - "${levels_file}" "${MODELS_FILE}" <<'PY'
import sys, yaml
from pathlib import Path

levels_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
pinned = set()
for line in manifest_path.read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#"):
        continue
    parts = line.split("\t")
    if parts:
        pinned.add(parts[0].strip())

doc = yaml.safe_load(levels_path.read_text(encoding="utf-8")) or {}
wanted = []
seen = set()
for _, spec in (doc.get("profiles") or {}).items():
    for _, model_id in ((spec or {}).get("models") or {}).items():
        m = str(model_id or "").strip()
        if m in pinned and m not in seen:
            seen.add(m)
            wanted.append(m)
for m in wanted:
    print(m)
PY
)"
  for alias in ${aliases}; do
    fetch_model "${alias}"
  done
}

add_model() {
  local alias="$1" hf_repo="$2" hf_file="${3:-}"
  if model_record "${alias}" >/dev/null 2>&1; then
    echo "Model alias ${alias} is already pinned in ${MODELS_FILE}; fetching..."
    fetch_model "${alias}"
    return 0
  fi
  local resolved
  resolved="$(python3 - "${alias}" "${hf_repo}" "${hf_file}" "${ROOT}/scripts/llama-router.ini" "${MODELS_FILE}" <<'PY'
import configparser, json, sys, urllib.request
from pathlib import Path

alias, repo, requested_file, ini_path, tsv_path = sys.argv[1:6]
info = json.loads(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}", timeout=15).read())
commit_sha = info["sha"]
tree = json.loads(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}/tree/main", timeout=15).read())
ggufs = [x for x in tree if x.get("path", "").endswith(".gguf")]
if not ggufs:
    raise SystemExit(f"ERROR: no .gguf files found in {repo}")
match = None
if requested_file:
    for item in ggufs:
        if item["path"] == requested_file:
            match = item
            break
else:
    for item in ggufs:
        if "q4_k_m" in item["path"].lower():
            match = item
            break
    if match is None:
        match = ggufs[0]
if match is None:
    raise SystemExit(f"ERROR: file {requested_file!r} not found in {repo}")

fname = match["path"]
sha256 = (match.get("lfs") or {}).get("oid")
if not sha256 or len(sha256) != 64:
    raise SystemExit(f"ERROR: LFS sha256 missing for {repo}/{fname}")
source_url = f"https://huggingface.co/{repo}/resolve/{commit_sha}/{fname}"

with open(tsv_path, "a", encoding="utf-8") as fh:
    fh.write(f"{alias}\t{fname}\t{sha256}\t{source_url}\n")

ini_file = Path(ini_path)
presets = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
presets.read(ini_file)
if not presets.has_section(alias):
    with open(ini_file, "a", encoding="utf-8") as fh:
        fh.write(f"\n[{alias}]\nmodel = artifacts/llama-router/models/{alias}.gguf\n")
print(f"pinned {alias} -> {source_url} ({sha256})")
PY
)"
  echo "${resolved}"
  fetch_model "${alias}"
}

if [ "${1:-}" = "--daemon" ] && [ "$#" -eq 1 ]; then
  DAEMON=1
elif [ "${1:-}" = "--verify" ] && [ "$#" -le 2 ]; then
  MODE="verify"
  TARGET_ALIAS="${2:-}"
elif [ "${1:-}" = "--fetch" ] && [ "$#" -le 2 ]; then
  MODE="fetch"
  TARGET_ALIAS="${2:-all}"
elif [ "${1:-}" = "--ensure-profiles" ] && [ "$#" -le 2 ]; then
  MODE="ensure-profiles"
  TARGET_ALIAS="${2:-}"
elif [ "${1:-}" = "--add" ] && [ "$#" -ge 3 ] && [ "$#" -le 4 ]; then
  MODE="add"
  ADD_ALIAS="$2"
  ADD_REPO="$3"
  ADD_FILE="${4:-}"
elif [ "$#" -gt 0 ]; then
  echo "usage: $0 [--daemon | --verify [ALIAS] | --fetch [ALIAS|all] | --ensure-profiles [LEVELS_YAML] | --add ALIAS HF_REPO [HF_FILE]]" >&2
  exit 2
fi

if [ "${MODE}" = "fetch" ]; then
  if [ "${TARGET_ALIAS}" = "all" ] || [ -z "${TARGET_ALIAS}" ]; then
    fetch_all_models
  else
    fetch_model "${TARGET_ALIAS}"
  fi
  exit 0
fi

if [ "${MODE}" = "ensure-profiles" ]; then
  if [ -n "${TARGET_ALIAS}" ]; then
    ensure_profile_models "${TARGET_ALIAS}"
  else
    ensure_profile_models
  fi
  exit 0
fi

if [ "${MODE}" = "add" ]; then
  add_model "${ADD_ALIAS}" "${ADD_REPO}" "${ADD_FILE}"
  exit 0
fi

if [ ! -d "${MODEL_DIR}" ]; then
  echo "ERROR: LLAMA_MODEL_DIR does not exist: ${MODEL_DIR}" >&2
  echo "Place GGUF files there using the filenames in scripts/llama-router.ini," >&2
  echo "or set LLAMA_MODEL_DIR to an existing model directory." >&2
  exit 1
fi

if [ "${MODE}" = "verify" ]; then
  if [ -n "${TARGET_ALIAS}" ]; then
    verify_model "${TARGET_ALIAS}" 1
  else
    verify_models 1
  fi
  exit 0
fi

if [ "${LLAMA_SKIP_MODEL_VERIFY:-0}" != "1" ]; then
  verify_models "${LLAMA_VERIFY_MODELS:-0}" >/dev/null
fi

mkdir -p "${EMPTY_HF}" "${RUNTIME_DIR}"
if [ -e "${RUNTIME_MODELS}" ] && [ ! -L "${RUNTIME_MODELS}" ]; then
  echo "ERROR: ${RUNTIME_MODELS} exists and is not a symlink." >&2
  exit 1
fi
ln -sfn "${MODEL_DIR}" "${RUNTIME_MODELS}"
cd "${ROOT}"

if [ "${DAEMON}" = "1" ]; then
  if curl -fsS --max-time 3 http://127.0.0.1:8077/v1/models >/dev/null 2>&1; then
    echo "llama.cpp router already reachable on :8077"
    exit 0
  fi

  command -v llama-server >/dev/null 2>&1 || {
    echo "ERROR: llama-server is not on PATH" >&2
    exit 1
  }
  mkdir -p "${RUNTIME_DIR}"

  PLATFORM="$(uname -s)"
  if [ "${PLATFORM}" = "Darwin" ]; then
    LABEL="org.openclinai.llama-router"
    command -v launchctl >/dev/null 2>&1 || {
      echo "ERROR: launchctl is required for managed macOS startup" >&2
      exit 1
    }
    launchctl remove "${LABEL}" >/dev/null 2>&1 || true
    launchctl submit \
      -l "${LABEL}" \
      -o "${RUNTIME_DIR}/router.stdout.log" \
      -e "${RUNTIME_DIR}/router.log" \
      -- /usr/bin/env \
      HOME="${HOME}" \
      PATH="${PATH}" \
      LLAMA_MODEL_DIR="${MODEL_DIR}" \
      LLAMA_ROUTER_RUNTIME_DIR="${RUNTIME_DIR}" \
      LLAMA_ROUTER_MODELS_MAX="${LLAMA_ROUTER_MODELS_MAX:-4}" \
      "${ROOT}/scripts/llama-router-up.sh"
  else
    nohup env \
      LLAMA_MODEL_DIR="${MODEL_DIR}" \
      LLAMA_ROUTER_RUNTIME_DIR="${RUNTIME_DIR}" \
      LLAMA_ROUTER_MODELS_MAX="${LLAMA_ROUTER_MODELS_MAX:-4}" \
      "${ROOT}/scripts/llama-router-up.sh" \
      >"${RUNTIME_DIR}/router.log" 2>&1 &
    echo "$!" >"${RUNTIME_DIR}/router.pid"
  fi

  for _ in $(seq 1 "${READY_TIMEOUT_SECONDS}"); do
    if curl -fsS --max-time 3 http://127.0.0.1:8077/v1/models >/dev/null 2>&1; then
      if [ "${PLATFORM}" = "Darwin" ]; then
        ROUTER_PID="$(launchctl print "gui/$(id -u)/${LABEL}" 2>/dev/null \
          | awk '/pid =/ {print $3; exit}' || true)"
        [ -z "${ROUTER_PID}" ] || printf '%s\n' "${ROUTER_PID}" >"${RUNTIME_DIR}/router.pid"
      fi
      echo "llama.cpp router ready on :8077"
      exit 0
    fi
    sleep 1
  done

  if [ "${PLATFORM}" = "Darwin" ]; then
    launchctl remove "${LABEL}" >/dev/null 2>&1 || true
  elif [ -f "${RUNTIME_DIR}/router.pid" ]; then
    ROUTER_PID="$(cat "${RUNTIME_DIR}/router.pid")"
    case "${ROUTER_PID}" in
      ''|*[!0-9]*) ;;
      *) kill "${ROUTER_PID}" >/dev/null 2>&1 || true ;;
    esac
  fi
  rm -f "${RUNTIME_DIR}/router.pid"
  echo "ERROR: llama.cpp router was not ready after ${READY_TIMEOUT_SECONDS}s" >&2
  tail -n 40 "${RUNTIME_DIR}/router.log" >&2 2>/dev/null || true
  exit 1
fi

# LLAMA_ROUTER_MODELS_MAX caps how many model instances stay co-resident, and it MUST be
# set per-workload — the tiers have wildly different footprints on this 64G host (Metal
# working-set limit ~48G), and one router can only be tuned for one of them at a time:
#
#   LOW / MED (interactive) — DEFAULT 4. Each turn cycles 4 distinct role-models
#     (orchestrator · expert · synthesizer · validator), all small/mid: LOW ~20G of weights,
#     MED ~34G — both fit co-resident, so 4 keeps every role-switch AND the next turn warm
#     (zero reloads). Anything LESS thrashes: with 4 distinct models cycled in order,
#     max=1/2/3 evicts the very model needed next, so every call reloads from disk (max=1
#     is why even the LOW team was painfully slow).
#
#   HIGH (benchmark) — set LLAMA_ROUTER_MODELS_MAX=1. Its 3 big GGUFs (19G/17G/29G) can't
#     co-reside: any two (~46-48G weights + KV) blow past the ~48G Metal limit and the
#     router thrashes (spawn -> child OOM-dies -> 500). One at a time loads each alone.
#
# Note: on a 64G host you cannot serve LOW/MED co-resident AND HIGH loaded at once
# (LOW+MED weights ~41G + one HIGH model ~29G > 64G) — pick the workload, restart to switch.
exec env HF_HOME="${EMPTY_HF}" llama-server \
  --models-preset "${ROOT}/scripts/llama-router.ini" \
  --models-max "${LLAMA_ROUTER_MODELS_MAX:-4}" --port "${ROUTER_PORT}" --host 0.0.0.0
