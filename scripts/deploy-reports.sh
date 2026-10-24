#!/usr/bin/env bash
# Deploy the committed report archive to the reports host.
#
# The site is the committed reports/ folder, nothing more and nothing less. This
# refuses uncommitted changes under reports/, rebuilds the catalog to prove the
# committed index matches the manifest, then mirrors the whole folder with
# --delete. Demo videos are git-ignored (.gitignore) and are neither uploaded nor
# deleted; they live only on the host and in the checkouts that recorded them.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_ROOT="${REPORTS_ROOT:-${ROOT}/reports}"
MANIFEST="${REPORTS_ROOT}/reports-index.json"

uncommitted() { git -C "${REPORTS_ROOT}" status --porcelain --untracked-files=all -- . ; }

if [[ -n "$(uncommitted)" ]]; then
  echo "error: ${REPORTS_ROOT} has uncommitted changes; the site is the committed archive, so commit them first:" >&2
  uncommitted >&2
  exit 1
fi

(cd "${ROOT}" && python3 scripts/build-reports-index.py \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}" >/dev/null)
if [[ -n "$(uncommitted)" ]]; then
  echo "error: the committed catalog is stale against ${MANIFEST}; commit the rebuilt files first:" >&2
  uncommitted >&2
  exit 1
fi

# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"
if ! gcp_vm_exists || [[ "$(gcp_vm_status)" != "RUNNING" ]]; then
  echo "error: VM ${GCP_VM_NAME} is not RUNNING; nothing deployed. Re-run scripts/deploy-reports.sh when it is up." >&2
  exit 1
fi

IP="$(gcp_vm_ip)"
gcp_ssh_keygen_once
gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/artifacts/reports"
rsync -az --delete --exclude='*.mp4' --exclude='*.webm' --exclude='.DS_Store' \
  -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
  "${REPORTS_ROOT}/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/"
gcp_ssh "chmod -R a+rX ${GCP_REMOTE_REPO}/artifacts/reports"

SITE="${CADDY_SITE_REPORTS:-reports.openclinai.org}"
curl -fsS --retry 5 --retry-delay 2 --max-time 30 "https://${SITE}/" | cmp - "${REPORTS_ROOT}/index.html"
echo "==> deployed https://${SITE}/ from commit $(git -C "${REPORTS_ROOT}" rev-parse --short HEAD)"
