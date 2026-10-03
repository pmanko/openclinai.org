#!/usr/bin/env python3
"""Verify a dump against its provenance sidecar before publishing or restoring."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "targets" / "validation-harness"))
sys.path.insert(0, str(ROOT))

from harness.validate.dump_provenance import verify_dump  # noqa: E402
from scripts.environment import ConfigError, resolve  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument(
        "--require-portable",
        action="store_true",
        help="reject full backups that retain consumer-module state",
    )
    args = parser.parse_args()
    provenance_path = args.provenance or Path(f"{args.dump}.provenance.json")
    provenance, issues = verify_dump(
        args.dump, provenance_path, require_portable=args.require_portable
    )
    instance = os.environ.get("OPENCLINAI_ENVIRONMENT")
    if instance and args.require_portable:
        try:
            baseline = resolve(ROOT, instance)["preset"]["baseline"]
            if (provenance.get("output_sha256") != baseline["sha256"]
                    or provenance.get("output_bytes") != baseline["bytes"]):
                issues.append("research seed must match the selected preset's verified HIV archive")
        except ConfigError as exc:
            issues.append(str(exc))
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1
    print(f"    verified dump sha256 {provenance['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
