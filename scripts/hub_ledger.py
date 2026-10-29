"""Patients' QueryStore ledgers as the running Hub reads and renders them.

Runs the Hub's QueryStore export (``server.querystore_export``) inside the Hub container, which
holds the QueryStore configuration, so the umbrella's fixture capture and corpus check use the
Hub's own client and serializer instead of a copy of them.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

HUB_CONTAINER = os.environ.get("MED_AGENT_HUB_CONTAINER", "harness-med-agent-hub")


def hub_ledgers(patients: list[str], container: str = HUB_CONTAINER) -> dict[str, dict[str, Any]]:
    """``{patient uuid: {chart_snapshot, mappings, records, total, snapshot_id, hub_revision}}``."""
    if not patients:
        return {}
    command = ["docker", "exec", container, "python", "-m", "server.querystore_export"]
    for patient in patients:
        command += ["--patient", patient]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"Hub QueryStore export failed in {container}: {proc.stderr.strip()}")
    ledgers = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return {ledger["patient"]: ledger for ledger in ledgers}
