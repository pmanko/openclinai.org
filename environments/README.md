# ChartSearchAI Research Setup

This prepares a fresh local OpenMRS instance with the HIV dataset, ChartSearchAI
and [seven evaluation accounts](chartsearch-research/accounts.json). The
validation harness runs experiments afterward; it does not install this stack.

## First Setup

Start from the recursive umbrella checkout described in the [README](../README.md#workspace-checkout).
While [PR #5](https://github.com/pmanko/openclinai.org/pull/5) is open, use
`codex/research-environment-handoff`.

Prerequisites: running Docker with Compose, Java/Maven, Python 3, Node.js 18+,
Yarn 4 and `llama-server` on your PATH. Put the
[Gemma E4B GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF)
in `~/.cache/llama-router-models/gemma-e4b.gguf`, or set `LLAMA_MODEL_DIR` in
an ignored `.env.chartsearch` file. The existing router uses this directory.

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
imports the HIV data, configures both ChartSearchAI providers, and creates the
accounts. No stock patients are generated. There is no upgrade or backup flow.

ChartSearchAI defaults to Hub; its bundled provider uses the same local Gemma
E4B router. Other available Hub profiles appear in the picker.

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

Use the existing `make down` to stop containers without deleting their data.
For later startup, run `bash scripts/llama-router-up.sh --daemon`, then
`COMPOSE_ENV_FILE=.env.chartsearch.example make up med-agent-hub-up`.
Use `.env.chartsearch` instead if you have private overrides. Do not repeat
the fresh setup unless you want to reload the baseline.

## Setup Acceptance

Check only that OpenMRS opens, ChartSearchAI is available on a patient chart,
and known HIV patient records are loaded. Account logins are checked while
provisioning. Model-quality evaluations, reports and videos are not setup gates.
