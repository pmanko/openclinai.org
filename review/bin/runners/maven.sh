#!/usr/bin/env bash
# Test ids: Class or Class#method. REVIEW_MAVEN_ARGS defaults to offline (-o).
set -u
dir=$1 log=$2; shift 2
tests=$(IFS=,; echo "$*")
python3 - "$dir" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
for report in root.glob('**/target/surefire-reports/TEST-*.xml'):
    if report.resolve().is_relative_to(root): report.unlink()
PY
(cd "$dir" && mvn ${REVIEW_MAVEN_ARGS--o} -B test -Dtest="$tests" \
  -Dsurefire.failIfNoSpecifiedTests=false -DfailIfNoTests=false) > "$log" 2>&1
rc=$?
python3 - "$dir" "$rc" <<'PY'
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
ran = failed = errors = 0
try:
    for report in Path(sys.argv[1]).glob('**/target/surefire-reports/TEST-*.xml'):
        for case in ET.parse(report).getroot().iter('testcase'):
            if case.find('skipped') is not None: continue
            if case.find('error') is not None:
                errors += 1; continue
            ran += 1
            failure = case.find('failure')
            if failure is not None:
                failed += 1
                print('FAILED ' + case.get('classname', '') + '#' + case.get('name', '') + ': ' + failure.get('message', '').split('\n')[0])
except (OSError, ET.ParseError):
    errors += 1
print('RAN ' + str(ran))
rc = int(sys.argv[2])
sys.exit(2 if errors else 3 if not ran and rc == 0 else 2 if not ran else 1 if failed and rc else 0 if not failed and rc == 0 else 2)
PY
