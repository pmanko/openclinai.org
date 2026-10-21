#!/usr/bin/env bash
# Test ids: a path or a node id (path::name; path#name is accepted). REVIEW_PYTHON
# picks the interpreter; otherwise the project's .venv, python3, or uv with pytest.
dir=$1 log=$2; shift 2
ids=(); for id in "$@"; do ids+=("${id/\#/::}"); done
cd "$dir" || exit 2
if [ -n "$REVIEW_PYTHON" ]; then py=("$REVIEW_PYTHON")
elif [ -x .venv/bin/python ]; then py=(.venv/bin/python)
elif python3 -c 'import pytest' 2>/dev/null; then py=(python3)
else py=(uv run --no-project --with pytest python); fi
"${py[@]}" -m pytest -q -rfE -p no:cacheprovider "${ids[@]}" > "$log" 2>&1
rc=$?
summary=$(tail -1 "$log")
ran=$(printf '%s' "$summary" | grep -oE '[0-9]+ (passed|failed|error)' | awk '{n += $1} END {print n + 0}')
echo "RAN $ran"
grep -E '^(FAILED|ERROR) ' "$log" | sed -E 's/^(FAILED|ERROR) /FAILED /' | head -20
case $rc in 0) exit 0 ;; 1) exit 1 ;; 4|5) exit 3 ;; *) exit 2 ;; esac
