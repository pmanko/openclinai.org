#!/usr/bin/env bash
# Test ids: Class or Class#method. REVIEW_MAVEN_ARGS defaults to offline (-o).
dir=$1 log=$2; shift 2
tests=$(IFS=,; echo "$*")
(cd "$dir" && mvn ${REVIEW_MAVEN_ARGS--o} -B test -Dtest="$tests" \
  -Dsurefire.failIfNoSpecifiedTests=false -DfailIfNoTests=false) > "$log" 2>&1
rc=$?
ran=$(grep -E '^\[(INFO|WARNING|ERROR)\] Tests run: [0-9]+, Failures: [0-9]+, Errors: [0-9]+, Skipped: [0-9]+$' "$log" \
  | awk -F'[:,]' '{n += $2 - $8} END {print n + 0}')
echo "RAN $ran"
fails='^\[ERROR\]   [A-Z][A-Za-z0-9_$]*\.[A-Za-z0-9_$]+'
grep -E "$fails" "$log" | sed 's/^\[ERROR\]   /FAILED /' | head -20
if [ $rc -eq 0 ]; then [ "$ran" -gt 0 ] && exit 0 || exit 3; fi
grep -qE "$fails" "$log" && exit 1
exit 2
