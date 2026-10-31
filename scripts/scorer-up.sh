#!/usr/bin/env bash
# Start the local entailment scorer the Hub reads in shadow (confidence-labels L6).
# A venv under artifacts/scorer holds torch and transformers; the model (SCORER_MODEL) comes
# from the Hugging Face cache. The Hub reaches it as http://host.docker.internal:8090.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "${ROOT}"
VENV="${ROOT}/artifacts/scorer/.venv"
PORT="${SCORER_PORT:-8090}"
if [ ! -x "${VENV}/bin/python" ]; then
  uv venv "${VENV}" >/dev/null
  uv pip install --python "${VENV}/bin/python" torch transformers sentencepiece >/dev/null
fi
if curl -fsS -m 3 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "scorer already up on :${PORT}"; exit 0
fi
mkdir -p artifacts/scorer
nohup "${VENV}/bin/python" scripts/scorer-service.py > artifacts/scorer/scorer.log 2>&1 &
echo $! > artifacts/scorer/scorer.pid
for _ in $(seq 1 120); do
  curl -fsS -m 3 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && { echo "scorer ready on :${PORT}"; exit 0; }
  sleep 2
done
echo "ERROR: scorer was not ready after 240s; see artifacts/scorer/scorer.log" >&2; exit 1
