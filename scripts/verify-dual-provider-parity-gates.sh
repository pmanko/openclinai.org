#!/usr/bin/env bash
set -euo pipefail

# Umbrella entrypoint for current dual-provider product acceptance and evidence.
# Workspace topology and publication checks have their own umbrella tooling.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${PARITY_GATE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/verify_dual_provider_parity_gates.py" --root "$ROOT" "$@"
