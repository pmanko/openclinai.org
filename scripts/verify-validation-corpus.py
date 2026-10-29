#!/usr/bin/env python3
"""Fail when a comparison set's live ledgers do not match its chart fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = ROOT / "targets" / "validation-harness"
sys.path.insert(0, str(HARNESS_ROOT))

from harness.validate.corpus_alignment import (  # noqa: E402
    alignment_issues,
    expected_ledgers,
)

sys.path.insert(0, str(ROOT / "scripts"))
from hub_ledger import HUB_CONTAINER, hub_ledgers  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True)
    parser.add_argument("--container", default=HUB_CONTAINER, help="the running Hub container")
    parser.add_argument(
        "--data-root", type=Path, default=HARNESS_ROOT / "datasets/validation"
    )
    args = parser.parse_args()

    expected = expected_ledgers(args.data_root, args.set)
    live = {
        patient: {"chart_snapshot": ledger["chart_snapshot"], "mappings": ledger["mappings"]}
        for patient, ledger in hub_ledgers(sorted(expected), args.container).items()
    }
    issues = alignment_issues(expected, live)
    if issues:
        print("ERROR: live validation corpus does not match committed chart fixtures:")
        for issue in issues:
            print(f"  - {issue}")
        print("Restore/reindex the intended corpus before running an evaluation.")
        return 1
    for patient, ledger in sorted(expected.items()):
        print(f"    {patient}: {len(ledger['mappings'])} exact fixture/live records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
