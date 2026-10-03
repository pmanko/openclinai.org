#!/bin/sh
# Umbrella OpenMRS initialization. Both ChartSearchAI providers remain supported;
# model provisioning is separate. Clinical data comes only from the verified HIV
# archive, never the distribution's automatic demo-patient generator.
#
# When started as root (no separate init container chowns the volume), heal
# pre-uid-1001 root-owned contents and drop to the openmrs user. The OpenMRS
# process always runs as uid 1001.
set -eu
OMRS_HOME="${OMRS_HOME:-/openmrs}"
if [ "$(id -u)" = "0" ]; then
  chown -R 1001:1001 "$OMRS_HOME/data" 2>/dev/null || true
  exec runuser -u openmrs -- "$0" "$@"
fi

# Native startup merges this file into runtime properties (or installation
# properties on first boot). OMRS_EXTRA_* cannot preserve this case-sensitive key.
cd "$OMRS_HOME"
touch openmrs-extra.properties
awk '
  BEGIN { print "referencedemodata.createDemoPatients=false" }
  $0 !~ /^[[:space:]]*referencedemodata[.]createDemoPatients[[:space:]]*[:=]/ { print }
' openmrs-extra.properties > openmrs-extra.properties.next
mv openmrs-extra.properties.next openmrs-extra.properties

MODEL_DIR="$OMRS_HOME/data/chartsearchai"
mkdir -p "$MODEL_DIR"

# Embedding model (all-MiniLM-L6-v2, ~86MB). querystore.embedding.modelFilePath
# points at chartsearchai/model.onnx relative to the app data directory. The path
# name is retained for data-volume compatibility; ChartSearchAI does not load it.
ONNX_FILE="$MODEL_DIR/model.onnx"
VOCAB_FILE="$MODEL_DIR/vocab.txt"
HF_EMBED="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main"

if [ ! -f "$ONNX_FILE" ]; then
  echo "Downloading all-MiniLM-L6-v2 ONNX model (~86MB)..."
  curl -fsSL -o "$ONNX_FILE" "$HF_EMBED/onnx/model.onnx"
  echo "Embedding model downloaded."
fi

if [ ! -f "$VOCAB_FILE" ]; then
  echo "Downloading all-MiniLM-L6-v2 vocab..."
  curl -fsSL -o "$VOCAB_FILE" "$HF_EMBED/vocab.txt"
  echo "Vocab downloaded."
fi

exec "$OMRS_HOME/startup.sh"
