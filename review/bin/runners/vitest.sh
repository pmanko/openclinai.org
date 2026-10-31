#!/usr/bin/env bash
# Test ids: a test file path, or path#test name (names become one -t pattern).
dir=$1 log=$2; shift 2
case "$log" in /*) ;; *) log="$PWD/$log" ;; esac
runner_dir=$(cd -- "$(dirname -- "$0")" && pwd)
files=() names=()
for id in "$@"; do
  files+=("${id%%#*}")
  [[ $id == *#* ]] && names+=("${id#*#}")
done
pattern=""
if [ ${#names[@]} -gt 0 ]; then pattern=$(IFS='|'; echo "${names[*]}"); fi
json="$log.json"; execution="$log.execution.json"
rm -f "$json" "$execution" || { echo "RAN 0"; exit 2; }
(cd "$dir" && TZ=UTC REVIEW_VITEST_EVIDENCE="$execution" node_modules/.bin/vitest run \
  --reporter=default --reporter=json --reporter="$runner_dir/vitest-evidence.mjs" \
  --outputFile.json="$json" "${files[@]}" ${pattern:+-t "$pattern"}) > "$log" 2>&1
process_exit=$?
[ -f "$json" ] && [ -f "$execution" ] || { echo "RAN 0"; exit 2; }
node -e '
let r, execution;
try {
  r = require(process.argv[1]);
  execution = require(process.argv[2]);
} catch {
  console.log("RAN 0"); process.exit(2);
}
const code = Number(process.argv[3]);
if (!["passed", "failed"].includes(execution.reason) ||
    !Number.isInteger(execution.unhandled_errors) || execution.unhandled_errors !== 0 ||
    ![0, 1].includes(code) || (execution.reason === "failed" && code === 0) || !Array.isArray(r.testResults)) {
  console.log("RAN 0"); process.exit(2);
}
const path = require("node:path");
const directory = path.resolve(process.argv[4]);
const requested = process.argv.slice(5);
let ran = 0, failed = 0, broken = 0;
for (const f of r.testResults) {
  if (!f || !Array.isArray(f.assertionResults) ||
      f.assertionResults.some(a => !a || !["passed", "failed", "skipped", "pending", "todo"].includes(a.status))) {
    console.log("RAN 0"); process.exit(2);
  }
  if (f.status === "failed" && !f.assertionResults.some(a => a.status === "failed")) broken++;
  for (const a of f.assertionResults) {
    if (a.status === "passed" || a.status === "failed") ran++;
    if (a.status === "failed") { failed++;
      const selectors = requested.filter(id => {
        const split = id.indexOf("#");
        return split >= 0 && typeof f.name === "string" &&
          path.resolve(directory, id.slice(0, split)) === path.resolve(f.name) &&
          new RegExp(id.slice(split + 1)).test(a.fullName);
      });
      console.log("FAILED_ID " + JSON.stringify({file: f.name, name: a.title,
        full_name: a.fullName, selectors}));
      console.log("FAILED " + a.fullName + ": " + (a.failureMessages[0] || "").split("\n")[0]); }
  }
}
console.log("RAN " + ran);
process.exit(broken || (code !== 0 && !failed) || (code === 0 && failed) ? 2 : failed ? 1 : ran ? 0 : 3);' "$json" "$execution" "$process_exit" "$dir" "$@"
