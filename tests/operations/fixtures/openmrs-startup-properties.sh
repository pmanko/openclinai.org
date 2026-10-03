#!/bin/bash
# Run inside the umbrella backend image, network-isolated as uid 1001.
# Exercise native property conversion only, not Java or inference readiness.
set -eu
for state in fresh existing; do
  export OMRS_HOME="/tmp/native-$state"
  mkdir -p "$OMRS_HOME/data/chartsearchai"
  touch "$OMRS_HOME/data/chartsearchai/model.onnx" "$OMRS_HOME/data/chartsearchai/vocab.txt"
  if [ "$state" = existing ]; then
    printf '%s\n' 'other.setting=kept' 'referencedemodata.createDemoPatients=true' > "$OMRS_HOME/data/openmrs-runtime.properties"
  fi
  printf '%s\n' '#!/bin/bash' 'exec /bin/bash /openmrs/startup-init.sh' > "$OMRS_HOME/startup.sh"
  chmod +x "$OMRS_HOME/startup.sh"
  /usr/local/bin/backend-init.sh > /dev/null
  if [ "$state" = fresh ]; then
    grep -qx 'property.referencedemodata.createDemoPatients=false' "$OMRS_HOME/openmrs-server.properties"
  else
    grep -qx 'referencedemodata.createDemoPatients=false' "$OMRS_HOME/data/openmrs-runtime.properties"
    grep -qx 'other.setting=kept' "$OMRS_HOME/data/openmrs-runtime.properties"
    if grep -qx 'referencedemodata.createDemoPatients=true' "$OMRS_HOME/data/openmrs-runtime.properties"; then
      echo 'Generator remained enabled in existing runtime properties.' >&2
      exit 1
    fi
  fi
  echo "Native $state startup: generator disabled; unrelated settings preserved."
done
