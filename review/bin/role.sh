#!/usr/bin/env bash
# Run one review role in a fresh session of the named agent.
#   role.sh <claude|codex|gemini|human> <reviewer|fixer|reply> <workdir> <prompt-file> <out-file>
# The answer (the agent's final message) is written to <out-file>. For a person the
# script prints what to do and exits 3; re-run `make review` once <out-file> exists.
set -u
agent=$1 role=$2 workdir=$3 prompt=$4 out=$5
# The model and effort are set here, never inherited from a personal config: a review is a
# mid-tier model at medium effort unless REVIEW_MODEL / REVIEW_REASONING say otherwise.
model=${REVIEW_MODEL:-gpt-6.1-sol} reasoning=${REVIEW_REASONING:-medium}
tools="Bash Read Grep Glob WebFetch"
[ "$role" = fixer ] && tools="$tools Edit Write"
case $agent in
  claude) (cd "$workdir" && claude -p --allowedTools "$tools" < "$prompt") > "$out" ;;
  codex)  codex exec -C "$workdir" --add-dir "$(dirname "$out")" -s workspace-write -m "$model" -c "model_reasoning_effort=\"$reasoning\"" \
            -o "$out" - < "$prompt" > "$out.log" 2>&1 ;;
  gemini) (cd "$workdir" && gemini --approval-mode yolo -p "Follow the instructions given on stdin." < "$prompt") > "$out" ;;
  human)
    if [ ! -s "$out" ]; then
      echo "$role: read $prompt, work in $workdir, write your answer to $out, then re-run."
      exit 3
    fi ;;
  *) echo "unknown agent $agent" >&2; exit 2 ;;
esac
