#!/usr/bin/env bash
# Family-aware report/evidence staging and optional cloud publication.
# Usage: publish-report.sh <chartsearchai|catalyst> <run_dir> <slug> [title] [summary] [takeaway]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAMILY="${1:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
RUN_DIR="${2:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
SLUG="${3:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
TITLE="${4:-}"
SUMMARY="${5:-}"
TAKEAWAY="${6:-}"
REPORTS_ROOT="${REPORTS_ROOT:-${ROOT}/artifacts/reports}"
DRY_RUN="${PUBLISH_DRY_RUN:-0}"

MANIFEST="${ROOT}/reports-index.json"
if [[ "${DRY_RUN}" == "1" && -f "${REPORTS_ROOT}/reports-index.json" ]]; then
  MANIFEST="${REPORTS_ROOT}/reports-index.json"
fi

# Refuse partial archives before staging, manifest updates, or any cloud access.
# The selected slug is supplied by the incoming packet; the build rechecks it
# after staging, along with every other available curated report.
(cd "${ROOT}" && python3 scripts/build-reports-index.py \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}" \
  --check-archive --pending-slug "${SLUG}")

mkdir -p "${REPORTS_ROOT}"
if [[ "${DRY_RUN}" == "1" && "${MANIFEST}" != "${REPORTS_ROOT}/reports-index.json" ]]; then
  cp "${MANIFEST}" "${REPORTS_ROOT}/reports-index.json"
  MANIFEST="${REPORTS_ROOT}/reports-index.json"
fi

(cd "${ROOT}" && python3 scripts/stage-report.py \
  "${FAMILY}" "${RUN_DIR}" "${SLUG}" "${TITLE}" "${SUMMARY}" "${TAKEAWAY}" \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}")

# report.html, optional dashboard/comparison pages and evidence are supplied by
# the report producer. Publication never renders or installs the harness.

(cd "${ROOT}" && python3 scripts/build-reports-index.py \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}")
if [[ "${MANIFEST}" != "${REPORTS_ROOT}/reports-index.json" ]]; then
  cp "${MANIFEST}" "${REPORTS_ROOT}/reports-index.json"
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "==> dry-run staged only under ${REPORTS_ROOT}"
  exit 0
fi

# shellcheck disable=SC1091
. "${ROOT}/scripts/cloud-lib.sh"
if ! gcp_vm_exists || [[ "$(gcp_vm_status)" != "RUNNING" ]]; then
  echo "warn: VM ${GCP_VM_NAME} not RUNNING — staged locally only." >&2
  exit 1
fi

IP="$(gcp_vm_ip)"
gcp_ssh_keygen_once
gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/artifacts/reports/${SLUG}"
rsync -avz --delete \
  -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
  "${REPORTS_ROOT}/${SLUG}/" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/${SLUG}/"
rsync -avz \
  -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
  "${REPORTS_ROOT}/index.html" "${REPORTS_ROOT}/reports-index.json" "${REPORTS_ROOT}/sitemap.xml" \
  "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/"
gcp_ssh "chmod -R a+rX ${GCP_REMOTE_REPO}/artifacts/reports"

SITE="${CADDY_SITE_REPORTS:-reports.openclinai.org}"

# The VM is a serving copy, not the archive: every publish also lands in the versioned bucket.
"${ROOT}/scripts/reports-backup.sh" || {
  BACKUP_STATUS=$?
  echo "error: report already published at https://${SITE}/${SLUG}/; mandatory backup failed (exit ${BACKUP_STATUS})." >&2
  exit "${BACKUP_STATUS}"
}
echo "==> published: https://${SITE}/${SLUG}/"
