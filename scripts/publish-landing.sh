#!/usr/bin/env bash
# Publish static OpenClinAI pages to an existing VM.
# - Production modes (default full or --landing-only) require a clean website
#   tree on `main` at or ahead of `origin/main` and fast-forward against the
#   remote `.landing-deploy-receipt.json` (override only with --force).
# - Preview mode (--preview <slug>) syncs to an isolated preview directory served
#   at https://<slug>-preview.<site>/ without touching production hosts or proxy.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  echo "usage: $0 [--landing-only] [--force] | --preview <slug>" >&2
  exit 2
}

PUBLISH_MODE="full"
FORCE=0
PREVIEW_SLUG=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    full)
      if [ "${PUBLISH_MODE}" != "full" ]; then
        usage
      fi
      shift
      ;;
    --landing-only)
      if [ "${PUBLISH_MODE}" = "preview" ]; then
        usage
      fi
      PUBLISH_MODE="--landing-only"
      shift
      ;;
    --force)
      if [ "${PUBLISH_MODE}" = "preview" ]; then
        usage
      fi
      FORCE=1
      shift
      ;;
    --preview)
      if [ "${PUBLISH_MODE}" != "full" ] || [ "${FORCE}" -eq 1 ] || [ "$#" -lt 2 ]; then
        usage
      fi
      PUBLISH_MODE="preview"
      PREVIEW_SLUG="$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

if [ "${PUBLISH_MODE}" = "preview" ]; then
  if [[ ! "${PREVIEW_SLUG}" =~ ^[a-z0-9]([a-z0-9-]{0,38}[a-z0-9])?$ ]]; then
    echo "error: invalid preview slug '${PREVIEW_SLUG}' (use lowercase letters, digits, and internal hyphens, 1-40 chars)" >&2
    exit 2
  fi
fi

# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"

echo "==> generating landing discovery files"
python3 "${ROOT}/scripts/build-landing-sitemap.py"
echo "==> running landing regression checks"
( cd "${ROOT}" && python3 -m pytest -q tests/website/test_landing_site.py )

if [ "${PUBLISH_MODE}" = "full" ] && [ ! -f "${ROOT}/.env.website" ]; then
  echo "error: .env.website is required for full static-host publication" >&2
  exit 1
fi

if [ "${PUBLISH_MODE}" != "preview" ]; then
  WATCHED_PATHS=("landing")
  if [ -d "${ROOT}/wahs/demo" ]; then
    WATCHED_PATHS+=("wahs/demo")
  fi
  if [ "${PUBLISH_MODE}" = "full" ]; then
    WATCHED_PATHS+=("compose/website")
  fi

  DIRTY_STATUS="$(git -C "${ROOT}" status --porcelain --untracked-files=all -- "${WATCHED_PATHS[@]}")"
  if [ -n "${DIRTY_STATUS}" ]; then
    echo "error: uncommitted changes in published website paths; commit first or use --preview <slug>:" >&2
    printf '%s\n' "${DIRTY_STATUS}" >&2
    exit 1
  fi

  HEAD_SHA="$(git -C "${ROOT}" rev-parse --verify HEAD)"
  HEAD_BRANCH="$(git -C "${ROOT}" symbolic-ref --quiet --short HEAD || echo detached)"

  if [ "${FORCE}" -ne 1 ]; then
    if [ "${HEAD_BRANCH}" != "main" ]; then
      echo "error: refusing production publish from branch '${HEAD_BRANCH}' (expected 'main')." >&2
      echo "       Publish an isolated preview instead: $0 --preview <slug>" >&2
      echo "       Or pass --force only with explicit approval to deploy an unmerged branch to production." >&2
      exit 1
    fi
    if git -C "${ROOT}" remote get-url origin >/dev/null 2>&1; then
      git -C "${ROOT}" fetch --quiet origin main
      if ! git -C "${ROOT}" merge-base --is-ancestor refs/remotes/origin/main "${HEAD_SHA}"; then
        echo "error: local HEAD (${HEAD_SHA:0:7}) is behind origin/main; pull or rebase before publishing." >&2
        exit 1
      fi
    fi
  fi
fi

if ! gcp_vm_exists || [ "$(gcp_vm_status)" != "RUNNING" ]; then
  echo "error: VM ${GCP_VM_NAME} is not running" >&2
  exit 1
fi

IP="$(gcp_vm_ip)"
gcp_ssh_keygen_once
SSH_TRANSPORT="ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new"

verify_live_host() {
  local target_host="$1"
  echo "==> verifying https://${target_host}/"
  # Compare every published HTML/CSS/sitemap file with the reviewed source,
  # including subpages. Matching only a headline would miss a stale project page.
  while IFS= read -r local_page; do
    relative_page="${local_page#"${ROOT}/landing/"}"
    echo "==> verifying ${relative_page}"
    curl -fsS --retry 8 --retry-connrefused --retry-delay 2 --max-time 30 \
      "https://${target_host}/${relative_page}" | cmp - "${local_page}"
  done < <(find "${ROOT}/landing" -type f \( -name '*.html' -o -name '*.css' -o -name 'sitemap.xml' \) | sort)
  curl -fsS --retry 8 --retry-connrefused --retry-delay 2 --max-time 20 \
    "https://${target_host}/media/openmrs-evidence-poster.png" -o /dev/null
}

if [ "${PUBLISH_MODE}" = "preview" ]; then
  if [ -f "${ROOT}/.env.website" ]; then
    SITE="$(awk -F= '/^CADDY_SITE=/{print $2}' "${ROOT}/.env.website" | tail -1)"
  else
    SITE=""
  fi
  SITE="${SITE:-${CADDY_SITE:-openclinai.org}}"
  PREVIEW_HOST="${PREVIEW_SLUG}-preview.${SITE}"
  DEMO_PREVIEW_HOST="${PREVIEW_SLUG}-demo-preview.${SITE}"
  REMOTE_PREVIEW_DIR="${GCP_REMOTE_REPO}/artifacts/previews/${PREVIEW_HOST}"

  gcp_ssh "mkdir -p ${REMOTE_PREVIEW_DIR}"
  echo "==> syncing isolated branch preview to ${PREVIEW_HOST}"
  rsync -avz --delete -e "${SSH_TRANSPORT}" \
    "${ROOT}/landing/" \
    "${GCP_SSH_USER}@${IP}:${REMOTE_PREVIEW_DIR}/"
  if [ -d "${ROOT}/wahs/demo" ]; then
    REMOTE_DEMO_PREVIEW_DIR="${GCP_REMOTE_REPO}/artifacts/previews/${DEMO_PREVIEW_HOST}"
    gcp_ssh "mkdir -p ${REMOTE_DEMO_PREVIEW_DIR}"
    rsync -avz --delete -e "${SSH_TRANSPORT}" \
      "${ROOT}/wahs/demo/" \
      "${GCP_SSH_USER}@${IP}:${REMOTE_DEMO_PREVIEW_DIR}/"
  fi

  verify_live_host "${PREVIEW_HOST}"
  echo "==> published preview: https://${PREVIEW_HOST}/"
  if [ -d "${ROOT}/wahs/demo" ]; then
    echo "==> published demo preview: https://${DEMO_PREVIEW_HOST}/"
  fi
  exit 0
fi

REMOTE_LOCK="/tmp/openclinai-publish-landing.lock"
if ! gcp_ssh "find ${REMOTE_LOCK} -maxdepth 0 -mmin +15 -exec rm -rf {} + 2>/dev/null || true; mkdir ${REMOTE_LOCK}"; then
  echo "error: another production landing deployment is currently in progress (${REMOTE_LOCK})" >&2
  exit 1
fi
release_remote_lock() {
  gcp_ssh "rmdir ${REMOTE_LOCK} 2>/dev/null || true" >/dev/null 2>&1 || true
}
trap release_remote_lock EXIT

RECEIPT_PATH="${GCP_REMOTE_REPO}/.landing-deploy-receipt.json"
REMOTE_RECEIPT="$(gcp_ssh "cat ${RECEIPT_PATH} 2>/dev/null || true")"
REMOTE_COMMIT="$(printf '%s\n' "${REMOTE_RECEIPT}" | sed -n 's/.*"commit":[[:space:]]*"\([0-9a-fA-F]\{7,40\}\).*/\1/p' | head -1)"
REMOTE_BRANCH="$(printf '%s\n' "${REMOTE_RECEIPT}" | sed -n 's/.*"branch":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
REMOTE_TIME="$(printf '%s\n' "${REMOTE_RECEIPT}" | sed -n 's/.*"deployed_at":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"

if [ -n "${REMOTE_COMMIT}" ] && [ "${FORCE}" -ne 1 ]; then
  if ! git -C "${ROOT}" cat-file -e "${REMOTE_COMMIT}^{commit}" 2>/dev/null || \
     ! git -C "${ROOT}" merge-base --is-ancestor "${REMOTE_COMMIT}" "${HEAD_SHA}"; then
    echo "error: live site is at commit ${REMOTE_COMMIT:0:7} (branch '${REMOTE_BRANCH:-unknown}', ${REMOTE_TIME:-unknown})," >&2
    echo "       which is NOT an ancestor of local HEAD (${HEAD_SHA:0:7})." >&2
    echo "       Pull/rebase onto the deployed commit, use --preview <slug>, or pass --force with explicit approval." >&2
    exit 1
  fi
fi

if [ "${PUBLISH_MODE}" = "--landing-only" ]; then
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/landing"
else
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/landing ${GCP_REMOTE_REPO}/artifacts/reports ${GCP_REMOTE_REPO}/artifacts/previews ${GCP_REMOTE_REPO}/compose/website"
fi

echo "==> syncing tested landing files only"
# Recordings live in the openclinai-media bucket, so landing/ carries only text
# and small hand-made images; nothing here is a symlink to follow.
rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${ROOT}/landing/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/landing/"
if [ -d "${ROOT}/wahs/demo" ]; then
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/wahs/demo"
  rsync -avz --delete -e "${SSH_TRANSPORT}" \
    "${ROOT}/wahs/demo/" \
    "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/wahs/demo/"
fi

SAFE_BRANCH="$(printf '%s' "${HEAD_BRANCH}" | tr -cd 'A-Za-z0-9._/-')"
SAFE_ACTOR="$(printf '%s' "${USER:-unknown}" | tr -cd 'A-Za-z0-9._-')"
DEPLOYED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
gcp_ssh "printf '{\n  \"commit\": \"%s\",\n  \"branch\": \"%s\",\n  \"mode\": \"%s\",\n  \"deployed_at\": \"%s\",\n  \"deployed_by\": \"%s\"\n}\n' '${HEAD_SHA}' '${SAFE_BRANCH}' '${PUBLISH_MODE}' '${DEPLOYED_AT}' '${SAFE_ACTOR}' > ${RECEIPT_PATH}.tmp && mv ${RECEIPT_PATH}.tmp ${RECEIPT_PATH}"

if [ "${PUBLISH_MODE}" = "--landing-only" ]; then
  echo "==> landing-only mode; proxy configuration and services unchanged"
else
  CONFIG_CHANGES="$(rsync -azc --itemize-changes -e "${SSH_TRANSPORT}" \
    "${ROOT}/compose/website/Caddyfile" \
    "${ROOT}/compose/website/services.yml" \
    "${ROOT}/.env.website" \
    "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/compose/website/")"

  RECREATE=""
  if [ -n "${CONFIG_CHANGES}" ]; then
    echo "==> proxy config changed; recreating only the proxy"
    printf '%s\n' "${CONFIG_CHANGES}"
    RECREATE="--force-recreate "
  else
    echo "==> proxy config unchanged; ensuring the proxy is running"
  fi
  gcp_ssh "cd ${GCP_REMOTE_REPO} && chmod 600 compose/website/.env.website && docker compose --project-name openclinai-website --env-file compose/website/.env.website -f compose/website/services.yml up -d --no-deps ${RECREATE}proxy"
fi

if [ "${PUBLISH_MODE}" = "--landing-only" ]; then
  SITE="${CADDY_SITE:-openclinai.org}"
else
  SITE="$(awk -F= '/^CADDY_SITE=/{print $2}' "${ROOT}/.env.website" | tail -1)"
  SITE="${SITE:-openclinai.org}"
fi

verify_live_host "${SITE}"

echo "==> published: https://${SITE}/"
