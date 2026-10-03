# ChartSearchAI Research Setup

OpenClinAI owns application setup. The validation harness runs experiments
against the prepared application.

The shared [research recipe](chartsearch-research/preset.json) identifies the
verified HIV archive and existing configuration. Its [account definitions](chartsearch-research/accounts.json)
list the seven evaluation accounts: clinical officer, nurse, pharmaceutical
technologist, adherence counsellor, health records officer, doctor and peer
educator. These are saved inputs for the existing setup tools.

## Current State

The HIV-only startup change and saved account definitions are present. The
complete setup command, account provisioning and final startup smoke checks
are unfinished. This branch is not yet a tested handoff for Ross.

Native commands already available in the umbrella include:

| Command | Purpose |
| --- | --- |
| `make openmrs-source-pair-build` | Build and stage QueryStore and ChartSearchAI |
| `make chartsearch-esm-build` | Build and stage the frontend |
| `make up` | Start the configured OpenMRS services |
| `make seed DUMP=<verified-archive-path>` | Explicitly import the existing HIV archive using native verification |
| `make chartsearch-configure` | Apply ChartSearchAI configuration |
| `make querystore-configure` | Apply QueryStore configuration |
| `make status` | Show service status |

This table is a tool reference, not the finished fresh-setup procedure. The
[roadmap](../specs/reusable-environments-roadmap.md) connects these operations
in the required order and adds existing account provisioning.

Use the native `.env.chartsearch.example` defaults and ignored
`.env.chartsearch` overrides for local settings. The baseline accepts the
standard OpenMRS demo login, `admin` / `Admin123`.
Keep private settings out of Git and shared output.

## Ready for Research

Use only simple smoke checks: OpenMRS opens, ChartSearchAI is available on it,
and known HIV patient records can be sampled. The scenario adds the seven
evaluation accounts. Stock-generated patients must not be added.

The handoff will give the tested setup command and revision, application URL,
account access and provider selection. Role-context improvements, model
comparisons, reports and videos are subsequent work. Other scenarios can save
their own account/settings inputs and reuse the same native tools.
