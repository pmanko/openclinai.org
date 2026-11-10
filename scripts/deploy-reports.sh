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

SLUG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug)
      SLUG="${2:?usage: deploy-reports.sh [--slug <slug>]}"
      shift 2
      ;;
    *)
      echo "error: unknown argument: $1 (usage: deploy-reports.sh [--slug <slug>])" >&2
      exit 1
      ;;
  esac
done
SLUG="${SLUG:-${DEPLOY_SLUG:-}}"

if [[ -n "${SLUG}" && ! -f "${REPORTS_ROOT}/${SLUG}/index.html" ]]; then
  echo "error: staged report ${REPORTS_ROOT}/${SLUG}/index.html does not exist." >&2
  exit 1
fi

BRANCH="$(git -C "${REPORTS_ROOT}" symbolic-ref --short HEAD 2>/dev/null || echo "detached")"
if [[ -z "${SLUG}" && "${BRANCH}" != "main" && "${BRANCH}" != "master" && "${ALLOW_BRANCH_FULL_DEPLOY:-0}" != "1" ]]; then
  echo "error: refusing full-archive rsync --delete from non-main branch '${BRANCH}'." >&2
  echo "Use 'scripts/deploy-reports.sh --slug <slug>' (or 'scripts/publish-report.sh') for additive per-slug publishing on feature branches, or deploy from main." >&2
  exit 1
fi

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

# Prevent a diverged worktree from wiping reports that are already live on the host
# or committed in a sibling worktree when running rsync --delete.
if [[ "${ALLOW_REPORT_REMOVAL:-0}" != "1" ]]; then
  REMOTE_MANIFEST="$(gcp_ssh "cat ${GCP_REMOTE_REPO}/artifacts/reports/reports-index.json 2>/dev/null || true")"
  python3 - "${MANIFEST}" "${ROOT}" "${REMOTE_MANIFEST}" <<'PY'
import json, pathlib, subprocess, sys

manifest_path = pathlib.Path(sys.argv[1]).resolve()
root_path = pathlib.Path(sys.argv[2]).resolve()
remote_raw = sys.argv[3].strip()

def extract_slugs(data: dict) -> list[str]:
    out = []
    for r in data.get("runs", []) if isinstance(data, dict) else []:
        if isinstance(r, dict) and r.get("slug"):
            out.append(str(r["slug"]))
        for e in (r.get("earlier") or []) if isinstance(r, dict) else []:
            if isinstance(e, dict) and e.get("slug"):
                out.append(str(e["slug"]))
    return out

local_slugs = set(extract_slugs(json.loads(manifest_path.read_text(encoding="utf-8"))))

if remote_raw:
    try:
        remote_slugs = extract_slugs(json.loads(remote_raw))
    except Exception:
        remote_slugs = []
    missing_remote = [s for s in remote_slugs if s not in local_slugs]
    if missing_remote:
        sys.stderr.write(
            f"error: refusing to deploy because local {manifest_path} is missing report(s) currently live on the host: "
            + ", ".join(missing_remote)
            + "\nSync those report packets into this worktree first (or set ALLOW_REPORT_REMOVAL=1 to intentionally remove them).\n"
        )
        sys.exit(1)

# Only inspect sibling worktrees when deploying the repository's own reports/ folder
if manifest_path == (root_path / "reports" / "reports-index.json").resolve():
    try:
        wt_out = subprocess.check_output(
            ["git", "-C", str(root_path), "worktree", "list", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in wt_out.splitlines():
            if not line.startswith("worktree "):
                continue
            wt_dir = pathlib.Path(line.split(" ", 1)[1].strip())
            sib_manifest = wt_dir / "reports" / "reports-index.json"
            if sib_manifest.is_file() and sib_manifest.resolve() != manifest_path:
                try:
                    sib_slugs = extract_slugs(json.loads(sib_manifest.read_text(encoding="utf-8")))
                except Exception:
                    continue
                missing_sib = [s for s in sib_slugs if s not in local_slugs and (wt_dir / "reports" / s / "index.html").is_file()]
                if missing_sib:
                    sys.stderr.write(
                        f"error: refusing to deploy because sibling worktree {wt_dir} has staged report(s) missing here: "
                        + ", ".join(missing_sib)
                        + "\nSync reports/ across worktrees before deploying (or set ALLOW_REPORT_REMOVAL=1).\n"
                    )
                    sys.exit(1)
        branches = subprocess.check_output(
            ["git", "-C", str(root_path), "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            text=True, stderr=subprocess.DEVNULL
        ).splitlines()
        for br in branches:
            br = br.strip()
            if not br:
                continue
            try:
                br_raw = subprocess.check_output(
                    ["git", "-C", str(root_path), "show", f"{br}:reports/reports-index.json"],
                    text=True, stderr=subprocess.DEVNULL
                )
                br_slugs = extract_slugs(json.loads(br_raw))
            except Exception:
                continue
            missing_br = [s for s in br_slugs if s not in local_slugs]
            if missing_br:
                sys.stderr.write(
                    f"error: refusing to deploy because local branch '{br}' has published report(s) missing here: "
                    + ", ".join(missing_br)
                    + "\nMerge or sync those report packets onto main before deploying (or set ALLOW_REPORT_REMOVAL=1).\n"
                )
                sys.exit(1)
    except SystemExit:
        raise
    except Exception:
        pass
PY
fi

if [[ -n "${SLUG}" ]]; then
  gcp_ssh "mkdir -p ${GCP_REMOTE_REPO}/artifacts/reports/${SLUG}"
  rsync -az --delete --exclude='*.mp4' --exclude='*.webm' --exclude='.DS_Store' \
    -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
    "${REPORTS_ROOT}/${SLUG}/" \
    "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/${SLUG}/"
  CATALOG_ITEMS=("${REPORTS_ROOT}/index.html" "${REPORTS_ROOT}/reports-index.json")
  [[ -f "${REPORTS_ROOT}/sitemap.xml" ]] && CATALOG_ITEMS+=("${REPORTS_ROOT}/sitemap.xml")
  [[ -d "${REPORTS_ROOT}/assets" ]] && CATALOG_ITEMS+=("${REPORTS_ROOT}/assets")
  rsync -az --exclude='.DS_Store' \
    -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
    "${CATALOG_ITEMS[@]}" \
    "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/"
else
  rsync -az --delete --exclude='*.mp4' --exclude='*.webm' --exclude='.DS_Store' \
    -e "ssh -i ${GCP_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
    "${REPORTS_ROOT}/" \
    "${GCP_SSH_USER}@${IP}:${GCP_REMOTE_REPO}/artifacts/reports/"
fi
gcp_ssh "chmod -R a+rX ${GCP_REMOTE_REPO}/artifacts/reports"

SITE="${CADDY_SITE_REPORTS:-reports.openclinai.org}"
curl -fsS --retry 5 --retry-delay 2 --max-time 30 "https://${SITE}/" | cmp - "${REPORTS_ROOT}/index.html"
if [[ -n "${SLUG}" ]]; then
  echo "==> deployed report ${SLUG} additively to https://${SITE}/${SLUG}/ from commit $(git -C "${REPORTS_ROOT}" rev-parse --short HEAD)"
else
  echo "==> deployed https://${SITE}/ from commit $(git -C "${REPORTS_ROOT}" rev-parse --short HEAD)"
fi
