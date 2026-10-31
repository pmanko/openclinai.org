#!/usr/bin/env bash
# Run one review role in a fresh session of the named agent.
#   role.sh <claude|codex|gemini|human> <reviewer|fixer|reply|judge> <workdir> <prompt-file> <out-file>
# The answer (the agent's final message) is written to <out-file>. For a person the
# script prints what to do and exits 3; re-run `make review` once <out-file> exists.
# Beside the answer, <out-file>.card.json records the session: agent and version, model,
# reasoning effort, sampling, start and finish. A judge pass carries it as its judge card.
set -u
agent=$1 role=$2 workdir=$3 prompt=$4 out=$5
# The model and effort are set here, never inherited from a personal config: a review is a
# mid-tier model at medium effort unless REVIEW_MODEL / REVIEW_REASONING say otherwise.
# Claude has its own default model; the Codex default is not one of its models.
case $agent in
  claude) model=${REVIEW_MODEL:-claude-sonnet-5-5} ;;
  *)      model=${REVIEW_MODEL:-gpt-6.1-sol} ;;
esac
reasoning=${REVIEW_REASONING:-medium}
tools="Bash Read Grep Glob WebFetch"
[ "$role" = fixer ] && tools="$tools Edit Write"
started=$(date -u +%FT%TZ)
case $agent in
  claude) version=$(claude --version 2>/dev/null | head -1)
          (cd "$workdir" && claude -p --model "$model" --effort "$reasoning" --allowedTools "$tools" < "$prompt") > "$out" ;;
  codex)  version=$(codex --version 2>/dev/null | head -1 | sed 's/^codex-cli //')
          codex exec -C "$workdir" -s workspace-write -m "$model" -c "model_reasoning_effort=\"$reasoning\"" \
            -o "$out" - < "$prompt" > "$out.log" 2>&1 ;;
  gemini) version=$(gemini --version 2>/dev/null | head -1)
          (cd "$workdir" && gemini --approval-mode yolo -p "Follow the instructions given on stdin." < "$prompt") > "$out" ;;
  human)
    if [ ! -s "$out" ]; then
      echo "$role: read $prompt, work in $workdir, write your answer to $out, then re-run."
      exit 3
    fi
    model=${REVIEW_MODEL:-human} reasoning="" version="" ;;
  *) echo "unknown agent $agent" >&2; exit 2 ;;
esac
rc=$?
# The CLIs expose no sampling controls, so the provider's default is what ran.
printf '{"agent": "%s", "agent_version": "%s", "model": "%s", "reasoning_effort": "%s", "sampling": "provider default", "role": "%s", "started_at": "%s", "finished_at": "%s"}\n' \
  "$agent" "${version:-}" "$model" "$reasoning" "$role" "$started" "$(date -u +%FT%TZ)" > "$out.card.json"
exit $rc
