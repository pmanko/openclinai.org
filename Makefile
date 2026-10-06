UV ?= uv
HARNESS := targets/validation-harness
LLAMA_ROUTER_TIER ?= med
SET ?= demo
TIER ?= med
REFERENCE_DATE ?= 2026-06-20
RESUME ?=
TRACE_FILE ?= $(CURDIR)/artifacts/hub-trace/trace.jsonl
CORPUS_PROVENANCE ?= $(wildcard $(CURDIR)/artifacts/chartsearchai-local/corpus-provenance.json)
UV_PROJECT_ENVIRONMENT ?= $(CURDIR)/$(HARNESS)/.venv
export UV_PROJECT_ENVIRONMENT

.PHONY: up down local-stack-up local-stack-down reset status logs catalyst-mvp-up catalyst-mvp-external catalyst-mvp-seed catalyst-mvp-warm catalyst-mvp-health catalyst-mvp-restart catalyst-mvp-down catalyst-mvp-reset catalyst-superset-status catalyst-superset-import reset-transform sqlmesh-status loadtest-up loadtest-down dump-loaded chartsearch-build querystore-build openmrs-source-pair-build openmrs-source-pair-test repository-lines-check repository-lines-pr-check deployed-sources-check chartsearch-esm-build chartsearch-esm-dev llama-router-up llama-router-down llama-router-models llama-router-small-model-proof med-agent-hub-build med-agent-hub-up med-agent-hub-logs med-agent-hub-restart med-agent-hub-test chartsearch-test querystore-test querystore-test-integration chartsearch-configure querystore-configure querystore-reindex querystore-recreate-index chartsearch-backend chartsearchai-local dual-provider-up chartsearch-doctor seed validate-preflight validate-run load-test orphan-fk-check import-smoke completeness-check test

# --- compose lifecycle ---
up:
	./scripts/stack-up.sh --wait

down:
	./scripts/stack-down.sh

# Fast-resume path for a day-to-day dev machine: starts Docker Desktop,
# llama-router, and the already-built compose stack with no rebuilds — for
# first-time HIV research setup, use `make chartsearch-research-setup`.
local-stack-up:
	./scripts/local-stack-up.sh

local-stack-down:
	./scripts/local-stack-down.sh

reset:
	./scripts/stack-reset.sh

status:
	./scripts/stack-status.sh
	@echo ""
	@./scripts/sqlmesh-state-check.sh --quiet || true

logs:
	docker compose -f compose/openmrs-2.8-refapp.yml logs -f --tail=200

catalyst-mvp-up:
	./scripts/catalyst-mvp.sh up

catalyst-mvp-external:
	MVP_MODEL_BACKEND=external ./scripts/catalyst-mvp.sh boot

catalyst-mvp-seed:
	./scripts/catalyst-mvp.sh seed

catalyst-mvp-warm:
	./scripts/catalyst-mvp.sh warm

catalyst-mvp-health:
	./scripts/catalyst-mvp.sh health

catalyst-mvp-restart:
	./scripts/catalyst-mvp.sh restart

catalyst-mvp-down:
	./scripts/catalyst-mvp.sh down

catalyst-mvp-reset:
	./scripts/catalyst-mvp.sh reset

catalyst-superset-status:
	./scripts/catalyst-mvp.sh superset-status

catalyst-superset-import:
	./scripts/catalyst-mvp.sh superset-import

reset-transform:
	./scripts/reset-transform.sh $(if $(FORCE),--force) $(if $(PLAN),--plan)

# Inspect SQLMesh state health (environment count, snapshot count,
# orphan tables/views). Exit 0 if healthy; 1 if drift detected.
sqlmesh-status:
	./scripts/sqlmesh-state-check.sh

loadtest-up:
	./scripts/loadtest-up.sh $(if $(FORCE),--force)

loadtest-down:
	./scripts/loadtest-down.sh

dump-loaded:
	./scripts/dump-loaded.sh $(if $(SOURCE),--source $(SOURCE)) $(if $(OUT),--out $(OUT))

chartsearch-build: querystore-build
	cd targets/chartsearchai && mvn -DskipTests -B package
	mkdir -p artifacts/openmrs/modules artifacts/chartsearchai-local/module-provenance
	cp targets/chartsearchai/omod/target/chartsearchai-*.omod artifacts/openmrs/modules/
	./scripts/artifact-provenance.py write --repo targets/chartsearchai \
	  --artifact artifacts/openmrs/modules/chartsearchai-1.0.0-SNAPSHOT.omod \
	  --manifest artifacts/chartsearchai-local/module-provenance/chartsearchai-1.0.0-SNAPSHOT.omod.provenance.json
	@ls -la artifacts/openmrs/modules/chartsearchai-*.omod

# Build the pinned patient-record source module used by the hub's optional
# Querystore adapter. The local entrypoint invokes this only when missing/stale.
querystore-build:
	cd targets/querystore && mvn -DskipTests -B install
	mkdir -p artifacts/openmrs/modules artifacts/chartsearchai-local/module-provenance
	cp targets/querystore/omod/target/querystore-*.omod artifacts/openmrs/modules/
	./scripts/artifact-provenance.py write --repo targets/querystore \
	  --artifact artifacts/openmrs/modules/querystore-1.0.0-SNAPSHOT.omod \
	  --manifest artifacts/chartsearchai-local/module-provenance/querystore-1.0.0-SNAPSHOT.omod.provenance.json
	@ls -la artifacts/openmrs/modules/querystore-*.omod

# Build and stage the current development pair in dependency order. Unlike the
# strict test target below, this supports intentional dirty-tree local work.
openmrs-source-pair-build: chartsearch-build

# Prove the exact pinned integration pair from source. Querystore is installed
# first so ChartSearchAI cannot pass against an older cached snapshot API.
openmrs-source-pair-test:
	./scripts/openmrs-source-pair-test.sh

repository-lines-check:
	./scripts/verify-repository-lines.sh

repository-lines-pr-check:
	./scripts/verify-repository-lines.sh --allow-workspace-branch

# Verify that staged, mounted, and served OpenMRS artifacts plus the running hub
# image were all built from the source revisions currently pinned by this repo.
deployed-sources-check: repository-lines-check
	python3 scripts/probe-chartsearchai-relay.py --identity-only

chartsearch-esm-build:
	@./scripts/chartsearch-esm-build.sh
	@./scripts/artifact-provenance.py write --repo targets/chartsearchai-esm \
	  --artifact artifacts/openmrs/spa-custom \
	  --manifest artifacts/openmrs/chartsearchai-esm.provenance.json

# Day-to-day ESM dev loop. Spins up `openmrs develop` (Express + HMR) on
# port 8080 and proxies API to the local docker backend. Edits in
# targets/chartsearchai-esm/ hot-reload in the browser at
# http://localhost:8080/openmrs/spa. The dockerized :nightly-chartsearch
# frontend container stays up but is bypassed during dev — `openmrs
# develop` runs its own app-shell with an in-memory importmap pointing
# at the locally-bundled ESM (per OpenMRS o3-docs).
chartsearch-esm-dev:
	@if [ ! -d targets/chartsearchai-esm/node_modules ]; then \
	  echo "==> installing ESM deps"; \
	  (cd targets/chartsearchai-esm && yarn install); \
	fi
	@cd targets/chartsearchai-esm && yarn start --backend=http://localhost:8088 --spa-path=/openmrs/spa --api-url=/openmrs

LLAMA_ROUTER_TIER ?= med
llama-router-up:
	@case "$(LLAMA_ROUTER_TIER)" in \
	  low|med) MAX=4;; \
	  high) MAX=1;; \
	  *) echo "LLAMA_ROUTER_TIER must be low|med|high (got: $(LLAMA_ROUTER_TIER))"; exit 1;; \
	esac; \
	command -v llama-server >/dev/null 2>&1 || { \
	  echo "ERROR: 'llama-server' not on PATH — install llama.cpp (build 9430+) first."; exit 1; }; \
	echo "==> llama-router on :8077 (tier=$(LLAMA_ROUTER_TIER), models-max=$$MAX) — Ctrl-C to stop"; \
	LLAMA_ROUTER_MODELS_MAX=$$MAX ./scripts/llama-router-up.sh

llama-router-down:
	@./scripts/llama-router-down.sh

# Probe what the router is serving (the picker's llama-server section + the tiers
# med-agent-hub maps onto). Fails clearly when :8077 is down.
llama-router-models:
	@curl -fsS -m 5 http://localhost:8077/v1/models \
	  | python3 -c "import sys,json; d=json.load(sys.stdin); ms=d.get('data',[]); print('models on :8077:' if ms else 'no models loaded'); [print(f'  - {m[\"id\"]}') for m in ms]" \
	  || { echo "llama-router not reachable on :8077 — start it: make llama-router-up"; exit 1; }

# Explicit test/demo proof that the E2B writer and E4B checking model remain
# loaded together. This is deliberately separate from normal local startup.
llama-router-small-model-proof:
	@python3 scripts/verify-small-model-residency.py

# --- med-agent-hub ---
# Builds/runs the profile-driven inference service from targets/med-agent-hub.
# OpenMRS reaches it at http://med-agent-hub:8080 and direct local clients use
# the loopback-only host port :18081. Hub role models reach llama-router on
# the host (:8077); start that first with `make llama-router-up`. Point
# chartsearchai at the hub with `make chartsearch-configure` after setting the
# endpoint in .env.chartsearch.
med-agent-hub-build:
	HUB_BUILD_REVISION=$$(git -C targets/med-agent-hub rev-parse HEAD) \
	  docker compose -f compose/openmrs-2.8-refapp.yml build med-agent-hub

# Preflight: the container bind-mounts server/levels.yaml read-only; if it's
# missing (uninitialized submodule), the hub 500s on every request with a
# FileNotFoundError. Fail early with the fix instead of a confusing runtime 500.
# Soft-warn when the canonical llama-router (:8077) isn't reachable — the hub
# starts but every inference call fails until the router is up.
med-agent-hub-up:
	@if [ "$$(id -u)" = "0" ]; then \
	  echo "ERROR: med-agent-hub-up must run as a non-root host user." >&2; \
	  echo "  Root would map UID 0 into the container and defeat its non-root runtime." >&2; \
	  exit 1; \
	fi
	@if [ ! -f targets/med-agent-hub/server/levels.yaml ]; then \
	  echo "ERROR: targets/med-agent-hub/server/levels.yaml is missing."; \
	  echo "  The hub bind-mounts it read-only; without it the hub 500s on every request."; \
	  echo "  Fix: git submodule update --init targets/med-agent-hub"; \
	  exit 1; \
	fi
	@curl -fsS -m 3 http://localhost:8077/v1/models >/dev/null 2>&1 \
	  || echo "WARN: llama-router (:8077) not reachable — start it with 'make llama-router-up' or the hub's inference calls will fail."
	@override_source_set=$${QUERYSTORE_BASE_URL+x}; override_source=$${QUERYSTORE_BASE_URL-}; \
	  override_user_set=$${QUERYSTORE_USERNAME+x}; override_user=$${QUERYSTORE_USERNAME-}; \
	  override_password_set=$${QUERYSTORE_PASSWORD+x}; override_password=$${QUERYSTORE_PASSWORD-}; \
	  override_timezone_set=$${HUB_TIMEZONE+x}; override_timezone=$${HUB_TIMEZONE-}; \
	  override_anchor_set=$${HUB_ANCHOR+x}; override_anchor=$${HUB_ANCHOR-}; \
	  override_llm_set=$${MED_AGENT_LLM_BASE_URL+x}; override_llm=$${MED_AGENT_LLM_BASE_URL-}; \
	  set -a; . ./.env.chartsearch.example; \
	  [ ! -f .env.chartsearch ] || . ./.env.chartsearch; \
	  [ -z "$$override_source_set" ] || QUERYSTORE_BASE_URL="$$override_source"; \
	  [ -z "$$override_user_set" ] || QUERYSTORE_USERNAME="$$override_user"; \
	  [ -z "$$override_password_set" ] || QUERYSTORE_PASSWORD="$$override_password"; \
	  [ -z "$$override_timezone_set" ] || HUB_TIMEZONE="$$override_timezone"; \
	  [ -z "$$override_anchor_set" ] || HUB_ANCHOR="$$override_anchor"; \
	  [ -z "$$override_llm_set" ] || MED_AGENT_LLM_BASE_URL="$$override_llm"; \
	  QUERYSTORE_BASE_URL=$${QUERYSTORE_BASE_URL:-http://backend:8080/openmrs}; \
	  QUERYSTORE_USERNAME=$${QUERYSTORE_USERNAME:-$${CHARTSEARCH_ADMIN_USER:-admin}}; \
	  QUERYSTORE_PASSWORD=$${QUERYSTORE_PASSWORD:-$${CHARTSEARCH_ADMIN_PASSWORD:-Admin123}}; \
	  set +a; \
	  HUB_BUILD_REVISION=$$(git -C targets/med-agent-hub rev-parse HEAD) \
	  MED_AGENT_HUB_UID=$$(id -u) MED_AGENT_HUB_GID=$$(id -g) \
	  docker compose -f compose/openmrs-2.8-refapp.yml up -d --build med-agent-hub
	@ready=0; for i in $$(seq 1 60); do \
	  status=$$(docker inspect -f '{{.State.Health.Status}}' harness-med-agent-hub 2>/dev/null || echo missing); \
	  if [ "$$status" = healthy ]; then echo "    med-agent-hub healthy after $$i s"; ready=1; break; fi; \
	  sleep 1; \
	done; \
	if [ "$$ready" != 1 ]; then \
	  echo "ERROR: med-agent-hub did not become healthy within 60s" >&2; \
	  docker compose -f compose/openmrs-2.8-refapp.yml logs --tail=80 med-agent-hub >&2; \
	  exit 1; \
	fi
	@docker exec harness-med-agent-hub python -c "from pathlib import Path; p=Path('/app/trace/.write-probe'); p.write_text('ok'); p.unlink()"

med-agent-hub-logs:
	docker compose -f compose/openmrs-2.8-refapp.yml logs -f --tail=200 med-agent-hub

med-agent-hub-restart:
	docker compose -f compose/openmrs-2.8-refapp.yml restart med-agent-hub

# Run the bridge + KB unit tests in a throwaway python container. The runtime
# image is built from exported requirements (no dev deps), so tests run here
# against the source mount with the minimal import set + pytest. No host venv.
# Scoped to the bridge's suite; the legacy A2A tests belong to the multi-process
# topology the in-process team replaced (they import the unused a2a-sdk).
med-agent-hub-test:
	docker run --rm -v $(CURDIR)/targets/med-agent-hub:/app -w /app python:3.11-slim \
		sh -c "pip install --quiet --root-user-action=ignore fastapi httpx psutil python-dotenv pyyaml pytest && python -m pytest -q tests/test_bridge.py tests/test_kb.py"

chartsearch-test:
	@./scripts/test-chartsearchai.sh

querystore-test:
	@./scripts/test-querystore.sh unit

querystore-test-integration:
	@./scripts/test-querystore.sh mysql-integration

# Configure ChartSearchAI's fixed hub endpoint; the available default comes from hub discovery.
chartsearch-configure:
	@./scripts/chartsearch-configure.sh

# Configure the optional Querystore context source independently of the chat relay.
querystore-configure:
	@./scripts/querystore-configure.sh

querystore-reindex:
	@./scripts/querystore-reindex.sh

# Destructive only to the local Querystore read model, never to OpenMRS clinical tables.
# Explicit opt-in prevents an accidental invocation. Rebuilds the pinned module first.
querystore-recreate-index: querystore-build
	@ALLOW_QUERYSTORE_INDEX_RESET=$(ALLOW_QUERYSTORE_INDEX_RESET) ./scripts/querystore-recreate-index.sh

# Switch querystore's storage backend and re-test it. The backend is wired at
# module startup (QueryStoreActivator), so this sets the querystore.backend GP,
# brings up Elasticsearch when selected, recreates the backend, and re-runs
# configure. Select the shared environment's retrieval backend explicitly.
# Usage: make chartsearch-backend BACKEND=elasticsearch  (or lucene|mysql)
chartsearch-backend:
	@if [ -z "$(BACKEND)" ]; then echo "usage: make chartsearch-backend BACKEND=mysql|lucene|elasticsearch"; exit 1; fi
	@case "$(BACKEND)" in mysql|lucene|elasticsearch) ;; *) echo "BACKEND must be mysql|lucene|elasticsearch (got: $(BACKEND))"; exit 1;; esac
	@echo "==> querystore.backend -> $(BACKEND)"
	@set -a; [ -f .env.chartsearch ] && . ./.env.chartsearch; set +a; \
	  docker exec harness-openmrs-db mariadb -u"$${OMRS_DB_USER:-openmrs}" -p"$${OMRS_DB_PASSWORD:-openmrs}" "$${OMRS_DB_NAME:-openmrs}" \
	    -e "INSERT INTO global_property (property,property_value,uuid) VALUES ('querystore.backend','$(BACKEND)',UUID()) ON DUPLICATE KEY UPDATE property_value='$(BACKEND)'"
	@if [ "$(BACKEND)" = "elasticsearch" ]; then \
	  echo "==> elasticsearch backend: enabling querystore.bootstrap.autostart (self-index the whole corpus on boot)"; \
	  set -a; [ -f .env.chartsearch ] && . ./.env.chartsearch; set +a; \
	  docker exec harness-openmrs-db mariadb -u"$${OMRS_DB_USER:-openmrs}" -p"$${OMRS_DB_PASSWORD:-openmrs}" "$${OMRS_DB_NAME:-openmrs}" \
	    -e "INSERT INTO global_property (property,property_value,uuid) VALUES ('querystore.bootstrap.autostart','true',UUID()) ON DUPLICATE KEY UPDATE property_value='true'"; \
	  echo "==> starting elasticsearch service"; \
	  docker compose -f compose/openmrs-2.8-refapp.yml up -d elasticsearch; \
	fi
	@echo "==> recreating backend (re-wires querystore at startup)"
	@set -a; [ -f .env.chartsearch ] && . ./.env.chartsearch; set +a; \
	  docker compose -f compose/openmrs-2.8-refapp.yml up -d --force-recreate backend
	@observed=0; for i in $$(seq 1 60); do \
	  s=$$(docker inspect -f '{{.State.Health.Status}}' harness-openmrs-backend 2>/dev/null || echo starting); \
	  if [ "$$s" = "healthy" ]; then echo "    healthy after $$((i*5))s on $(BACKEND)"; observed=1; break; fi; \
	  sleep 5; \
	done; \
	if [ "$$observed" != "1" ]; then echo "ERROR: backend not healthy after 5 min" >&2; exit 1; fi
	@echo "==> configure Querystore assets and ChartSearchAI hub relay"
	@$(MAKE) querystore-configure chartsearch-configure
	@echo "==> querystore now on $(BACKEND); open a patient / run a search to (re)index into it"

chartsearchai-local:
	@./scripts/chartsearchai-local.sh

# Fresh HIV baseline, ChartSearchAI and saved research accounts.
.PHONY: chartsearch-research-setup
chartsearch-research-setup:
	@bash scripts/chartsearch-research-setup.sh $(if $(DUMP),"DUMP=$(DUMP)")

# One command: fresh reset -> working DUAL-provider stack (bundled + hub), restoring the cached
# Elasticsearch querystore index instead of re-embedding the static demo corpus. Build the cache
# once with `scripts/querystore-snapshot.sh snapshot <ver>`; thereafter every reset is minutes.
dual-provider-up:
	@./scripts/dual-provider-up.sh

chartsearch-doctor:
	@set -a; . ./.env.chartsearch.example; [ ! -f .env.chartsearch ] || . ./.env.chartsearch; set +a; \
	echo "Raw llama.cpp models:"; \
	curl -fsS -m 5 http://127.0.0.1:8077/v1/models \
	  | python3 -c "import sys,json; [print(f'  - {m[\"id\"]}') for m in json.load(sys.stdin).get('data',[])]"; \
	echo "Hub product profiles:"; \
	curl -fsS -m 5 "http://127.0.0.1:$${MED_AGENT_HUB_PORT:-18081}/v1/models" \
	  | python3 -c "import sys,json; [print(f'  - {m.get(\"label\", m[\"id\"])} ({m[\"id\"]}): available={m.get(\"available\")} default={m.get(\"default\")}') for m in json.load(sys.stdin).get('data',[]) if m.get('visibility') == 'product']"; \
	echo ""; \
	echo "Module status:"; \
	curl -fsS -u admin:Admin123 \
	  "http://localhost:$${HARNESS_PROXY_HTTP_PORT:-8088}/openmrs/ws/rest/v1/module/chartsearchai?v=custom:(uuid,started,version)" \
	  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  chartsearchai {d.get(\"version\",\"?\")} started={d.get(\"started\")}')" \
	  || echo "  module not found (backend may still be starting, or chartsearchai .omod not in artifacts/openmrs/modules/)"

seed:
	./scripts/seed-local.sh $(if $(FROM_SCHEMA),--from-schema $(FROM_SCHEMA)) $(if $(DUMP),--dump "$(DUMP)") $(if $(TARGET),--target "$(TARGET)")

validate-preflight:
	./scripts/validate-preflight.sh $(SET) $(TIER)

# The run's simulated "now": ONE value drives the hub temporal anchor (HUB_ANCHOR = the model's "now")
# AND the judge (--reference-date, recorded per row) so model == judge (P0b). Override per dataset/run.
REFERENCE_DATE ?= 2026-06-20
RESUME ?=
validate-run:
	HUB_ANCHOR=$(REFERENCE_DATE) $(MAKE) med-agent-hub-up
	$(UV) --directory $(HARNESS) run harness-cli validate run $(SET) --reference-date $(REFERENCE_DATE) \
		--trace-file "$(TRACE_FILE)" \
		$(if $(CORPUS_PROVENANCE),--corpus-provenance "$(CORPUS_PROVENANCE)",) \
		$(if $(RESUME),--resume "$(abspath $(RESUME))",)

# Data assets and Python tooling remain in the harness.
load-test:
	$(UV) --directory $(HARNESS) run python -m harness.load run --target $(or $(TARGET),openmrs_test)
orphan-fk-check:
	$(UV) --directory $(HARNESS) run python -m harness.transform.orphan_fk --target $(or $(TARGET),openmrs_test) $(if $(ALLOW_ORPHANS),--allow-orphans)
import-smoke:
	$(UV) --directory $(HARNESS) run python -m harness.import_smoke --target $(or $(TARGET),openmrs_test)
completeness-check:
	$(UV) --directory $(HARNESS) run python -m harness.transform.completeness

CIEL_VERSION ?= v2026-04-28
.PHONY: ciel-fetch ciel-baseline snapshot-baseline load-baseline catalyst-mvp-ui-update catalyst-mvp-source-update catalyst-router-build
ciel-fetch:
	$(UV) --directory $(HARNESS) run bash scripts/fetch-ciel-release.sh --version $(CIEL_VERSION)
ciel-baseline:
	./scripts/ciel-baseline-up.sh --version $(CIEL_VERSION)
snapshot-baseline:
	./scripts/snapshot-baseline.sh --version $(CIEL_VERSION)
load-baseline:
	./scripts/load-baseline.sh --version $(CIEL_VERSION)
catalyst-mvp-ui-update:
	./scripts/catalyst-mvp.sh ui-update
catalyst-mvp-source-update:
	./scripts/catalyst-mvp.sh source-update
catalyst-router-build:
	./scripts/build-catalyst-model-router.sh

test:
	python3 -m unittest discover -s tests -v
	$(UV) run --project $(HARNESS) --extra dev python -m pytest tests/operations
