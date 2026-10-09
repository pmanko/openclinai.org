# ChartSearchAI Research Setup

This prepares a fresh local OpenMRS instance with the HIV dataset, ChartSearchAI
and [seven evaluation accounts](chartsearch-research/accounts.json). The
validation harness runs experiments afterward; it does not install this stack.

## First Setup

Start from the recursive umbrella checkout described in the [README](../README.md#workspace-checkout).
Use `main` and initialize its pinned submodules. Gateway, frontend and backend
use the same OpenMRS distribution tag; our source-built ChartSearchAI and
QueryStore modules replace the distribution's snapshots.

Prerequisites: running Docker with Compose, Java 21/Maven, Python 3.11+, Node.js 18+,
Yarn 4 and `llama-server` on your PATH. Check `mvn -version` and
`python3 --version`; on macOS, the system Python may be older than the Python
you installed, and Maven uses the Java selected by `JAVA_HOME`.

Download
[`gemma-4-12b-it-Q8_0.gguf`](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/fc034cfff751157913579611efad8462ac1be606/gemma-4-12b-it-Q8_0.gguf)
from the pinned model revision and save it as
`~/.cache/llama-router-models/gemma-4-12b.gguf`, or set `LLAMA_MODEL_DIR` in
an ignored `.env.chartsearch` file. This is the Q8 artifact used by the default
router preset, not a Q4 or other quantization renamed to the same filename.
Its published SHA-256 is
`f20e7ff1be28c283eeeb18fc895733791c56a5851d5cd3fe9691b7f7d12afa72`.
The existing router uses this directory.

Download the [HIV baseline package](https://drive.google.com/file/d/1FxuaYxOfthzMHVL4bUPleLj_P7n_EN-X/view)
and place both files in `artifacts/demo-data/`:

- `refapp_28_demo.sql.gz`
- `refapp_28_demo.sql.gz.provenance.json`

Run from the umbrella root:

```sh
make chartsearch-research-setup
```

**This replaces the local OpenMRS database with the HIV baseline.** It builds
the pinned modules and frontend, starts the existing stack and model router,
imports the HIV data, recreates QueryStore's search index from that baseline,
configures both ChartSearchAI providers, and creates the
accounts. No stock patients are generated. There is no upgrade or backup flow.

ChartSearchAI defaults to Hub's checked Gemma 4 12B profile; its bundled provider
uses the same local Gemma 4 12B router. E4B remains available as an explicit
comparison when installed, along with other available Hub profiles in the picker.

## Access

Open [OpenMRS](http://localhost:8088/openmrs/spa). Select Outpatient Clinic
when asked for a login location.

| Username | Role | Demo password |
| --- | --- | --- |
| `admin` | Administrator | `Admin123` |
| `eval-clinical-officer` | Clinical officer | `Admin123` |
| `eval-nurse` | Nurse | `Admin123` |
| `eval-pharmacy` | Pharmaceutical technologist | `Admin123` |
| `eval-counsellor` | Adherence counsellor | `Admin123` |
| `eval-records` | Health records officer | `Admin123` |
| `eval-doctor` | Doctor | `Admin123` |
| `eval-peer` | Peer educator | `Admin123` |

These public passwords are for this local synthetic-data environment only.
`EVALUATION_PASSWORD` can override the research-account password. Existing
Doctor/Nurse roles are not changed. Account labels do not prove role-aware model
instructions or production permission isolation; those are separate work.

After login, open the [sample patient chart](http://localhost:8088/openmrs/spa/patient/dd75c020-1691-11df-97a5-7038c432aabf/chart/Patient%20Summary)
and launch ChartSearchAI. Non-clinician accounts may not have access to the
unrelated service-queue home page; use patient search or this chart link.

For every later startup, run this one command from the umbrella root:

```sh
make local-stack-up
```

It loads the defaults and optional `.env.chartsearch` overrides, starts Docker
Desktop when available, and starts the model router, OpenMRS and Hub. Local chart
access uses the existing demo administrator login; no generated credential file
is needed. `LLAMA_MODEL_DIR` is read automatically from your overrides.

For a standalone Hub using inline chart context only, explicitly export
`QUERYSTORE_BASE_URL`, `QUERYSTORE_USERNAME` and `QUERYSTORE_PASSWORD` as empty
before `make med-agent-hub-up`. That focused launcher preserves explicit empty
overrides; without overrides it uses the local demo login.

Stop with `make local-stack-down`. Startup retains the loaded data; repeat
`make chartsearch-research-setup` only when you want to reload the HIV baseline.

These are the only full-environment setup and start/stop commands. Fresh setup
uses the same startup path. Focused component build/configuration commands remain
available for development; model warmup, relay probes and evaluations are explicit
diagnostics, not part of startup.

## Setup Acceptance

Check only that OpenMRS opens, ChartSearchAI is available on a patient chart,
and known HIV patient records are loaded. Account logins are checked while
provisioning. Model-quality evaluations, reports and videos are not setup gates.

## Troubleshooting

- If a build fails, check the prerequisites above. Components are built from the
  pinned local checkouts; no upstream PR merge is required.
- If startup fails, read the error printed by `make local-stack-up`. Use
  `make logs` for container logs or `make med-agent-hub-logs` for Hub logs.
  Router logs are in `artifacts/llama-router/router.log` by default.
- If port 8088 is occupied, identify the owner with
  `docker ps --filter publish=8088`. Docker Desktop's `welcome-to-docker`
  container can use this port; stop it if you do not need it. Then repeat the
  setup or startup command. Startup recreates our proxy if an earlier failed
  bind left it without a published port; it does not stop unrelated containers.
- If the model is missing, check the model filename and directory above. Optional
  settings belong in `.env.chartsearch`; no generated credential file is needed.
- Do not rerun first setup to fix an ordinary startup failure: it replaces the
  database. Restart with `make local-stack-down` then `make local-stack-up`.
