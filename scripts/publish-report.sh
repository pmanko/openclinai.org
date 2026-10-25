#!/usr/bin/env bash
# Publish one reviewed report packet: stage it into the committed archive,
# rebuild the catalog, commit reports/, then deploy the whole committed archive.
# Usage: publish-report.sh <chartsearchai|catalyst> <run_dir> <slug> [title] [summary] [takeaway]
# PUBLISH_DRY_RUN=1 stages and rebuilds under REPORTS_ROOT without committing or deploying.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAMILY="${1:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
RUN_DIR="${2:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
SLUG="${3:?usage: publish-report.sh <family> <run_dir> <slug> [title] [summary] [takeaway]}"
TITLE="${4:-}"
SUMMARY="${5:-}"
TAKEAWAY="${6:-}"
export REPORTS_ROOT="${REPORTS_ROOT:-${ROOT}/reports}"
MANIFEST="${REPORTS_ROOT}/reports-index.json"
DRY_RUN="${PUBLISH_DRY_RUN:-0}"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "error: ${MANIFEST} is missing; the archive is the committed reports/ folder with its catalog." >&2
  exit 1
fi

# Refuse partial archives before staging or changing the catalog. The selected
# slug is supplied by the incoming packet; the build rechecks it after staging.
(cd "${ROOT}" && python3 scripts/build-reports-index.py \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}" \
  --check-archive --pending-slug "${SLUG}")

# report.html, optional dashboard/comparison pages and evidence are supplied by
# the report producer. Publication never renders or installs the harness.
(cd "${ROOT}" && python3 scripts/stage-report.py \
  "${FAMILY}" "${RUN_DIR}" "${SLUG}" "${TITLE}" "${SUMMARY}" "${TAKEAWAY}" \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}")
(cd "${ROOT}" && python3 scripts/build-reports-index.py \
  --reports-root "${REPORTS_ROOT}" --manifest "${MANIFEST}" --root "${ROOT}")

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "==> dry-run staged only under ${REPORTS_ROOT}"
  exit 0
fi

# The archive is tracked: the staged report and catalog are committed before
# anything reaches the host, so the host never holds what the repository lacks.
git -C "${REPORTS_ROOT}" add -- .
if git -C "${REPORTS_ROOT}" diff --cached --quiet -- .; then
  echo "==> ${SLUG} is already committed as staged"
else
  git -C "${REPORTS_ROOT}" commit -q -m "Publish report ${SLUG}" -- .
  echo "==> committed reports/${SLUG} and the catalog as $(git -C "${REPORTS_ROOT}" rev-parse --short HEAD)"
fi

"${ROOT}/scripts/deploy-reports.sh"
SITE="${CADDY_SITE_REPORTS:-reports.openclinai.org}"
echo "==> published: https://${SITE}/${SLUG}/"
