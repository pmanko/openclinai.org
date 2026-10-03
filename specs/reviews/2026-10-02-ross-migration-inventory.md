# Ross Environment Migration: Source Inspection

Inspected 2 October 2026. This is evidence for the
[reusable-environments roadmap](../reusable-environments-roadmap.md), not a second
setup procedure or a claim of recipient readiness. No services, data, accounts,
provider settings or product branches were changed during this inspection.

## Sources Inspected

| Source | Exact inspected revision | Finding |
| --- | --- | --- |
| Umbrella | `82dd3bff2c833ebf23a50d0c67b9757a06dbc4d5` | Clean main before creating the remediation branch; six component checkouts match their pins and are clean |
| [Original setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148) | `2b3b1fd0a112b3a3710cda45211212ae7d90c96f` | Open; contains setup/account/data-preservation work to port selectively, not merge into the independent harness |
| [Account-context PR #33](https://github.com/pmanko/openmrs-module-chartsearchai/pull/33) | `9416ffacce13264aa67ce5d5addc7b4245e9834b` | Open; introduces AccountContext and provider request/transport changes on older contracts |
| Selected ChartSearchAI | `8622f1b5c8995ac5361dd634705434ba65fe2fae` | Current TurnRequest/provider sources and REST controller have no AccountContext/accountContext implementation; context work must be reconciled, not assumed present |

PR status was read from GitHub; old setup source was fetched without checking out
its branch. Current component pins remain unchanged. This inspection does not
authorize rewriting either old PR or merging an OpenMRS contribution.

## Port Decisions

Paths in the first column refer to the original setup PR unless marked current.

| Source | Treatment | Reason and next proof |
| --- | --- | --- |
| `docs/environment-setup.md` | Rewrite as the generic umbrella operator guide | Useful preserve-first install/update distinction and recipient checks; old commands and harness ownership are no longer correct |
| `.claude/skills/harness-environment/SKILL.md` | Replace with a thin umbrella assistant entry point | One maintained human guide must drive both workflows; test from a fresh assistant session |
| `datasets/validation/evaluation-roles.json` | Port the seven account definitions into the research preset's account input | All seven roles are required; remove unused study-tier metadata, preserve occupational labels, explicit read privileges and existing-role requirements |
| `harness/evaluation_users.py`, `harness/common/openmrs.py`, `scripts/provision-evaluation-users.py` | Adapt the required account provisioning to umbrella operations | Reuse generated credentials, ownership checks, no existing-role rewrite and real login checks; test unrelated users, role inheritance and both providers |
| `harness/environment_setup.py` | Reuse preservation checks, not the fixed-stack implementation wholesale | Current container-name/checkout ownership assumptions cannot adopt the new layout or isolate two installations |
| `harness/evaluation_setup.py` and data/reset tests | Inspect and adapt backup/restore guarantees when lifecycle is implemented | Preserve-first update is distinct from initialize/reset; actual historical-schema and restored-backup proof remains required |
| `harness/environment_assets.py`, `datasets/sources/evaluation-baseline.json` | Reuse checksum/asset checks; save baseline identity once in the preset | Explicit acquisition only; no download/reseed during ordinary start/update |
| `scripts/update-evaluation-checkout.py` | Adapt its refusal checks to umbrella main and exact direct pins | Resolve target once; preserve preview revisions, dirty work and ignored-file collisions; no independent component branch updates |
| Current `compose/openmrs-2.8-refapp.yml` and lifecycle scripts | Adapt native operations, do not duplicate configuration | Fixed `harness-*` names and common artifact mounts prevent honest instance isolation today |
| Current `scripts/chartsearchai-local.sh` | Separate core preparation from provider setup and change config reading | `load_config_value` sources `.env` as shell; saved provider choices and private inputs must survive normal update |
| Current `Makefile:validate-run` | Remove preparation from selected-target experiment invocation | It currently starts Hub; an experiment must not restart/reconfigure the operator's manual environment |
| Current Playwright config/demo | Reuse journey, selected target and optional recording | Already has base URL/video/pacing and chat expansion; current demo is E4B-specific, not proof of two-provider role-context behavior |
| Old embedding/router/seed patches | Compare individually with current native scripts before carrying anything over | Avoid restoring already fixed or obsolete code; no bulk merge of old infrastructure |
| Old plans, harness ownership notes and old preview commands | Do not copy as current guidance | The umbrella roadmap and native product authorities govern this work |

## Verified Baseline Input

The available local `refapp_28_demo.sql.gz` matches the original setup manifest:

- SHA-256: `f76619b40b45f0261467ceaeb2708b97795d115d99a7b2c2a7c73b38d9a8512a`.
- Size: 44,057,876 bytes.
- The adjacent `.provenance.json` exists; its content and restore behavior are not
  verified by the checksum/size checks above.
- The old guide links the [private project baseline package](https://drive.google.com/file/d/1FxuaYxOfthzMHVL4bUPleLj_P7n_EN-X/view).
  Recipient access and package contents must be checked before handoff. The Drive
  page is not a direct SQL download endpoint.

This local package is enough to begin disposable implementation tests; no new
asset-hosting service is needed. Do not commit the SQL, provenance contents,
private settings, credentials or backups.

## Runtime and Migration Boundaries

A read-only Docker listing found a healthy OpenMRS stack under Compose project
`chartsearch-pr-split`, using the fixed `harness-*` container names. Other Catalyst,
OpenELIS and unrelated stacks are also running. This is an author-side observation,
not Ross's installation inventory and not evidence that the new umbrella owns
those services. None were restarted or claimed.

The current ChartSearchAI changelog already describes same-version redeployment
and applied-changeset hazards. The reported preserved-database failure therefore
requires an actual historical-schema regression and inspection of the installed
module/schema state, not a speculative edit or reset. No schema defect is claimed
fixed by this inspection.

Still required before changing Ross's installation:

- Exact owning checkout, Compose project, data volumes/bind mounts and private
  settings; do not collect secrets into a shared report.
- Actual schema and applied migration state, with a tested compatible upgrade.
- Full backup and demonstrated restoration; source rollback alone is insufficient.
- Explicit storage mapping and migration approval.

Before calling the handoff ready, also verify all seven account logins, actual
role/location transport through both providers, a completed question/follow-up,
inspectable evidence, In-Depth completion/failure, reload, a small independent run
and portable report. Recipient walkthrough and final quality/security/scope review
remain separate acceptance requirements.
