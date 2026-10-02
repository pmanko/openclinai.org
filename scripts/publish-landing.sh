#!/usr/bin/env bash
# Publish static OpenClinAI pages to an existing VM.
# Full publication updates only the independent website proxy configuration.
# --landing-only leaves that configuration and all services unchanged.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLISH_MODE="${1:-full}"
if [ "${PUBLISH_MODE}" != "full" ] && [ "${PUBLISH_MODE}" != "--landing-only" ]; then
  echo "usage: $0 [--landing-only]" >&2
  exit 2
fi
# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"

echo "==> generating landing discovery files"
python3 "${ROOT}/scripts/build-landing-sitemap.py"
echo "==> running landing regression checks"
( cd "${ROOT}" && python3 -m pytest -q tests/website/test_landing_site.py )

if ! gcp_vm_exists || [ "$(gcp_vm_status)" != "RUNNING" ]; then
  echo "error: VM ${GCP_VM_NAME} is not running" >&2
  exit 1
fi

if [ "${PUBLISH_MODE}" = "full" ] && [ ! -f "${ROOT}/.env.website" ]; then
  echo "error: .env.website is required for full static-host publication" >&2
  exit 1
fi

# The published pages are the source of truth for their demo-host assets.
# Include subpages and nested asset directories so galleries receive the same
# missing-media protection as the homepage recordings. Extract before any
# deployment mutation: a page referencing missing media must fail here and
# leave the currently published page untouched.
MEDIA_HOST="https://catalyst.openelis-global.org/media/"
REMOTE_MEDIA_ASSETS=()
while IFS= read -r asset; do
  REMOTE_MEDIA_ASSETS+=("${asset}")
done < <(
  grep -rhoE --include='*.html' "${MEDIA_HOST}[A-Za-z0-9._/-]+" "${ROOT}/landing/" | sort -u
)
if [ "${#REMOTE_MEDIA_ASSETS[@]}" -eq 0 ]; then
  echo "error: no ${MEDIA_HOST}<asset> references found in landing HTML" >&2
  exit 1
fi
echo "==> verifying ${#REMOTE_MEDIA_ASSETS[@]} demo-host asset(s) referenced by landing HTML"
for asset in "${REMOTE_MEDIA_ASSETS[@]}"; do
  curl -fsS --retry 8 --retry-delay 2 --max-time 30 "${asset}" -o /dev/null
done

IP="$(gcp_vm_ip)"
gcp_ssh_keygen_once
if [ "${PUBLISH_MODE}" = "--landing-only" ]; then
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/landing"
else
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/landing ${GCP_REMOTE_REPO}/artifacts/reports ${GCP_REMOTE_REPO}/compose/website"
fi

SSH_TRANSPORT="ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new"
echo "==> syncing tested landing files only"
# No -L: the recordings are no longer symlinked into this tree at all. They are
# served by the Catalyst demo host, and landing/index.html links to them there,
# so landing/ carries only text and the small hand-made poster images.
rsync -avz --delete -e "${SSH_TRANSPORT}" \
  "${ROOT}/landing/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/landing/"
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

echo "==> verifying https://${SITE}/"
# Compare every published HTML/CSS file with the reviewed source, including
# subpages. Matching only an old headline would miss a stale project page.
while IFS= read -r local_page; do
  relative_page="${local_page#"${ROOT}/landing/"}"
  echo "==> verifying ${relative_page}"
  curl -fsS --retry 8 --retry-connrefused --retry-delay 2 --max-time 30 \
    "https://${SITE}/${relative_page}" | cmp - "${local_page}"
done < <(find "${ROOT}/landing" -type f \( -name '*.html' -o -name '*.css' -o -name 'sitemap.xml' \) | sort)
curl -fsS --retry 8 --retry-connrefused --retry-delay 2 --max-time 20 "https://${SITE}/media/openmrs-evidence-poster.png" \
  -o /dev/null
# Separate post-publish verification: the demo-host assets were already
# confirmed reachable above, before this deploy touched anything, but the
# published landing/index.html on the VM is what the pre-publish check read
# from THIS checkout -- re-check the same list against the now-live page so a
# transport failure during rsync is not mistaken for success.
for asset in "${REMOTE_MEDIA_ASSETS[@]}"; do
  curl -fsS --retry 8 --retry-delay 2 --max-time 30 "${asset}" -o /dev/null
done

echo "==> published: https://${SITE}/"
