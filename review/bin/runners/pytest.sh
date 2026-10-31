#!/usr/bin/env bash
# Use a prepared component environment. Never install partial dependencies implicitly.
set -u
dir=$1 log=$2; shift 2
ids=(); for id in "$@"; do ids+=("${id/\#/::}"); done
cd "$dir" || exit 2
if [ -n "${REVIEW_PYTHON:-}" ]; then py=$REVIEW_PYTHON
elif [ -x .venv/bin/python ]; then py="$PWD/.venv/bin/python"
else py=python3; fi
report="$log.xml"
rm -f "$report"
"$py" -m pytest -q -rfE -p no:cacheprovider --junitxml="$report" "${ids[@]}" > "$log" 2>&1
rc=$?
"$py" - "$report" "$rc" <<'PY'
import sys, xml.etree.ElementTree as ET
try:
    root = ET.parse(sys.argv[1]).getroot()
except (OSError, ET.ParseError):
    print('RAN 0'); sys.exit(2)
ran = failed = errors = 0
for case in root.iter('testcase'):
    if case.find('skipped') is not None: continue
    if case.find('error') is not None:
        errors += 1; continue
    ran += 1
    failure = case.find('failure')
    if failure is not None:
        failed += 1
        print('FAILED ' + case.get('classname', '') + '::' + case.get('name', '') + ': ' + failure.get('message', '').split('\n')[0])
print('RAN ' + str(ran))
rc = int(sys.argv[2])
sys.exit(2 if errors or rc not in (0,1) else 3 if not ran else 1 if failed else 0 if rc == 0 else 2)
PY
