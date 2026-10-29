#!/usr/bin/env python3
"""Refresh judge fixtures from the running Hub's QueryStore export (the ledger it answers from)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
HARNESS_ROOT = ROOT / "targets" / "validation-harness"
sys.path.insert(0, str(ROOT / "scripts"))

from hub_ledger import HUB_CONTAINER, hub_ledgers  # noqa: E402


def updated_fixture(
    fixture: dict[str, Any],
    ledger: dict[str, Any],
    *,
    captured_at: str,
) -> dict[str, Any]:
    """Return a refreshed fixture while preserving its curated identity fields."""
    updated = deepcopy(fixture)
    mappings = ledger["mappings"]
    valid_uuids = sorted(
        {mapping["resourceUuid"] for mapping in mappings if mapping.get("resourceUuid")}
    )
    updated["chart_snapshot"] = ledger["chart_snapshot"]
    updated["mappings"] = mappings
    updated["valid_uuids"] = valid_uuids
    updated["n_records"] = len(mappings)
    updated["n_valid_uuids"] = len(valid_uuids)
    updated["provenance"] = {
        "source": "Querystore patientrecord read and rendered by med-agent-hub server.querystore_export",
        "captured_at": captured_at,
        "med_agent_hub_commit": ledger.get("hub_revision") or "",
        "querystore_snapshot_id": ledger.get("snapshot_id") or "",
        "resource_types": dict(
            sorted(Counter(mapping["resourceType"] for mapping in mappings).items())
        ),
        "note": (
            "Closed-context scoring fixture captured through the Hub's own QueryStore client "
            "and chart serializer, the evidence ledger the Hub answers from."
        ),
    }
    return updated


def _fixture_paths(path: str | None, all_fixtures: bool) -> list[Path]:
    if all_fixtures:
        return sorted((HARNESS_ROOT / "datasets" / "validation" / "charts").glob("*.json"))
    assert path is not None
    candidate = Path(path)
    return [candidate if candidate.is_absolute() else ROOT / candidate]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument("--fixture", help="fixture JSON to refresh in place")
    selected.add_argument("--all", action="store_true", help="refresh every committed chart fixture")
    parser.add_argument("--container", default=HUB_CONTAINER, help="the running Hub container")
    args = parser.parse_args(argv)

    captured_at = datetime.now(timezone.utc).isoformat()
    prepared: list[tuple[Path, dict[str, Any]]] = []
    try:
        fixtures = [
            (path, json.loads(path.read_text(encoding="utf-8")))
            for path in _fixture_paths(args.fixture, args.all)
        ]
        patients = []
        for path, fixture in fixtures:
            patient_uuid = str((fixture.get("patient") or {}).get("uuid") or "").strip()
            if not patient_uuid:
                raise ValueError(f"{path} has no patient.uuid")
            patients.append(patient_uuid)
        ledgers = hub_ledgers(patients, args.container)
        for (path, fixture), patient_uuid in zip(fixtures, patients):
            ledger = ledgers.get(patient_uuid)
            if not ledger or not ledger.get("mappings"):
                raise ValueError(f"no live records for {patient_uuid}")
            prepared.append((path, updated_fixture(fixture, ledger, captured_at=captured_at)))
    except Exception as exc:
        print(f"ERROR: fixture capture aborted before writing: {exc}", file=sys.stderr)
        return 1

    staged: list[tuple[Path, Path, dict[str, Any]]] = []
    try:
        for fixture_path, refreshed in prepared:
            temp_path = fixture_path.with_name(f".{fixture_path.name}.tmp")
            temp_path.write_text(
                json.dumps(refreshed, indent=2) + "\n", encoding="utf-8"
            )
            staged.append((fixture_path, temp_path, refreshed))
        for fixture_path, temp_path, refreshed in staged:
            os.replace(temp_path, fixture_path)
            print(
                f"refreshed {fixture_path.relative_to(ROOT)}: "
                f"{refreshed['n_records']} records"
            )
    finally:
        for _, temp_path, _ in staged:
            temp_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
