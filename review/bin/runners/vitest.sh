#!/usr/bin/env bash
# Test ids: a test file path, or path#test name (names become one -t pattern).
dir=$1 log=$2; shift 2
files=() names=()
for id in "$@"; do
  files+=("${id%%#*}")
  [[ $id == *#* ]] && names+=("${id#*#}")
done
pattern=""
if [ ${#names[@]} -gt 0 ]; then pattern=$(IFS='|'; echo "${names[*]}"); fi
json="$log.json"; rm -f "$json"
(cd "$dir" && TZ=UTC node_modules/.bin/vitest run --reporter=default --reporter=json \
  --outputFile.json="$json" "${files[@]}" ${pattern:+-t "$pattern"}) > "$log" 2>&1
[ -f "$json" ] || { echo "RAN 0"; exit 2; }
node -e '
const r = require(process.argv[1]);
let ran = 0, failed = 0, broken = 0;
for (const f of r.testResults) {
  if (f.status === "failed" && !f.assertionResults.some(a => a.status === "failed")) broken++;
  for (const a of f.assertionResults) {
    if (a.status === "passed" || a.status === "failed") ran++;
    if (a.status === "failed") { failed++;
      console.log("FAILED " + a.fullName + ": " + (a.failureMessages[0] || "").split("\n")[0]); }
  }
}
console.log("RAN " + ran);
process.exit(failed ? 1 : broken ? 2 : ran ? 0 : 3);' "$json"
