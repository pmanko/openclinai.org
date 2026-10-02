#!/usr/bin/env bash
# Connection helpers for publishing static files to an existing VM. Sourced, not executed.
#
# All values are env-overridable so operators can target a different project,
# zone, machine size, or VM name without editing this file. Defaults assume
# the clinical-ai-harness project in us-central1.

# shellcheck disable=SC2034   # consumed by sourcing scripts

GCP_PROJECT="${GCP_PROJECT:-clinical-ai-harness}"
GCP_ZONE="${GCP_ZONE:-us-central1-a}"
GCP_REGION="${GCP_REGION:-${GCP_ZONE%-*}}"
GCP_VM_NAME="${GCP_VM_NAME:-harness-chartsearch}"
# Remote path layout on the VM (under the SSH user's home).
GCP_REMOTE_REPO="${GCP_REMOTE_REPO:-openclinai.org}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Local SSH user is what gcloud compute ssh creates on the VM by default
# (project-level SSH keys, no OS Login). Override if your project enables OSL.
GCP_SSH_USER="${GCP_SSH_USER:-${USER}}"
GCP_SSH_KEY="${GCP_SSH_KEY:-${HOME}/.ssh/google_compute_engine}"

gcp_vm_exists() {
  gcloud compute instances describe "${GCP_VM_NAME}" \
    --zone="${GCP_ZONE}" --project="${GCP_PROJECT}" \
    --format='value(name)' >/dev/null 2>&1
}

gcp_vm_status() {
  gcloud compute instances describe "${GCP_VM_NAME}" \
    --zone="${GCP_ZONE}" --project="${GCP_PROJECT}" \
    --format='value(status)' 2>/dev/null || echo "MISSING"
}

gcp_vm_ip() {
  gcloud compute instances describe "${GCP_VM_NAME}" \
    --zone="${GCP_ZONE}" --project="${GCP_PROJECT}" \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null
}

gcp_ssh() {
  # Direct ssh using the gcloud-managed key. Falls back to `gcloud compute ssh`
  # if the key file isn't there yet (first-run bootstrap path).
  local ip
  ip="$(gcp_vm_ip)"
  if [ -z "${ip}" ]; then
    echo "error: VM ${GCP_VM_NAME} has no external IP (is it running?)" >&2
    return 1
  fi
  if [ -f "${GCP_SSH_KEY}" ]; then
    ssh -i "${GCP_SSH_KEY}" \
        -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile="${HOME}/.ssh/known_hosts" \
        -o ConnectTimeout=10 \
        "${GCP_SSH_USER}@${ip}" "$@"
  else
    gcloud compute ssh "${GCP_VM_NAME}" \
      --zone="${GCP_ZONE}" --project="${GCP_PROJECT}" \
      --quiet --command="$*"
  fi
}

gcp_ssh_keygen_once() {
  # Force gcloud to mint / register the SSH key pair if it isn't there yet.
  if [ ! -f "${GCP_SSH_KEY}" ]; then
    echo "==> bootstrapping SSH key via gcloud compute ssh"
    gcloud compute ssh "${GCP_VM_NAME}" \
      --zone="${GCP_ZONE}" --project="${GCP_PROJECT}" \
      --quiet --command='true'
  fi
}
