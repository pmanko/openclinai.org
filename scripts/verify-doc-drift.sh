#!/usr/bin/env bash
# Check explicit, current product documentation contracts, not historical plans
# or a repository-wide banned-word registry.
set -euo pipefail
ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

python3 - "$ROOT" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
required = {
    "targets/chartsearchai/README.md": (
        r"authorizes the patient request",
        r"bundled provider",
        r"med-agent-hub provider",
        r"no automatic fallback",
    ),
    "targets/chartsearchai-esm/README.md": (
        r"provider-neutral",
        r"bundled provider",
        r"med-agent-hub provider",
        r"does not choose provider endpoints",
        r"no automatic fallback",
    ),
    "targets/med-agent-hub/README.md": (
        r"client-facing clinical answer service",
        r"optional.*Querystore",
        r"temporal",
        r"insufficient_context",
    ),
    "targets/querystore/docs/rest-api.md": (
        r"GET `/ws/rest/v1/querystore/patientrecord`",
        r"external services such as med-agent-hub",
        r"clinicalDate",
        r"dateKind",
        r"snapshotId",
        r"ETag",
    ),
}
forbidden = (
    (r"\bchartSnapshot\b|\bchartMappingsJson\b|\brefresh-chart\b", "removed session chart snapshot path"),
    (r"\bindepth_token\b|\bonInDepthToken\b", "removed In-Depth token event/callback"),
    (r"only\s+med-agent-hub\s+(?:is|remains)\s+(?:the\s+)?(?:provider|inference)", "hub-only provider claim"),
    (r"bundled\s+(?:provider|inference|engine).{0,80}(?:removed|deleted|unsupported)", "removed bundled-provider claim"),
)
errors = []
for relative, patterns in required.items():
    path = root / relative
    if not path.is_file():
        errors.append(f"{relative}: missing product documentation")
        continue
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        if re.search(pattern, text, re.I | re.S) is None:
            errors.append(f"{relative}: missing contract /{pattern}/")
    for pattern, label in forbidden:
        if re.search(pattern, text, re.I):
            errors.append(f"{relative}: {label}")
if errors:
    print("FAIL: product documentation contracts")
    print("\n".join(errors))
    sys.exit(1)
print(f"PASS: checked {len(required)} current product documentation contracts")
PY
