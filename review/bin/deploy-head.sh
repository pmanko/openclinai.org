#!/usr/bin/env bash
# Build a backend module at a commit and deploy it to the local stack, proving the
# loaded bytes are the build's.
#   deploy-head.sh <querystore|chartsearchai> <commit>   build, deploy, check, keep as-found copy
#   deploy-head.sh <querystore|chartsearchai> --restore  put the as-found omod back
# The build runs in work/review/wt-deploy/<module> (offline Maven, tests skipped; the
# probes and suites cover tests). The module's lib cache is deleted before restart, and
# the api jar OpenMRS extracted is hashed against the one in the built omod.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
module=${1:?module} ref=${2:?commit or --restore}
case $module in querystore|chartsearchai) ;; *) echo "module must be querystore or chartsearchai" >&2; exit 2 ;; esac
container=${OPENMRS_CONTAINER:-harness-openmrs-backend}
modules=$ROOT/artifacts/openmrs/modules
keep=$ROOT/work/review/deploy
mkdir -p "$keep"

restart() {
  docker exec "$container" rm -rf "/openmrs/data/.openmrs-lib-cache/$module"
  docker restart "$container" > /dev/null
  echo "waiting for $container to report healthy"
  while :; do
    state=$(docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container")
    case $state in "running healthy") break ;; "running "*|"restarting"*) sleep 5 ;; *) echo "$container: $state" >&2; exit 1 ;; esac
  done
}

if [ "$ref" = --restore ]; then
  found=$(ls "$keep"/$module-*.omod.as-found 2>/dev/null | head -1)
  [ -n "$found" ] || { echo "no as-found $module omod to restore"; exit 0; }
  cp "$found" "$modules/$(basename "$found" .as-found)"
  rm "$found"
  restart
  echo "restored the as-found $module omod"
  exit 0
fi

src=$ROOT/targets/$module
wt=$ROOT/work/review/wt-deploy/$module
sha=$(git -C "$src" rev-parse "$ref^{commit}")
if [ ! -e "$wt/.git" ]; then git -C "$src" worktree prune; git -C "$src" worktree add -q --detach "$wt" "$sha"; fi
git -C "$wt" checkout -q --detach -f "$sha"
git -C "$wt" clean -fdq
echo "building $module at ${sha:0:7}"
(cd "$wt" && mvn -o -q -B -DskipTests package) > "$keep/$module-build.log" 2>&1 \
  || { echo "build failed: $keep/$module-build.log" >&2; exit 1; }
omod=$(ls "$wt"/omod/target/$module-*.omod)
name=$(basename "$omod")
[ -e "$keep/$name.as-found" ] || cp "$modules/$name" "$keep/$name.as-found"
cp "$omod" "$modules/$name"
restart
built=$(unzip -p "$omod" "lib/$module-api-*.jar" | shasum -a 256 | cut -d' ' -f1)
loaded=$(docker exec "$container" sh -c "sha256sum /openmrs/data/.openmrs-lib-cache/$module/lib/$module-api-*.jar" | cut -d' ' -f1)
if [ "$built" != "$loaded" ]; then
  echo "loaded $module api jar $loaded is not the build's $built" >&2; exit 1
fi
echo "deployed $module ${sha:0:7}: loaded api jar sha256 ${built:0:16} matches the build"
