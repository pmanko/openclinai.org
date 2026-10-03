# Ross Setup: Source Inspection and Scope Audit

Inspected 2 October 2026. This is evidence for the
[reusable-environments roadmap](../reusable-environments-roadmap.md), not a second
setup procedure or a claim of recipient readiness. No services, data, accounts,
provider settings or product branches were changed during this inspection.

## Scope Audit, 3 October 2026

Reviewed the full environment roadmap, its parent-roadmap entries, operator guide
and linked preparation evidence against the user's requests. The user asked for
fresh setup and reusable, ordered scenario additions, not migration of an old
database. The older report explicitly states that a fresh baseline avoids the
schema collision and that Ross had no data to retain. The assistant nevertheless
added historical-upgrade acceptance to the roadmap; that was not a user requirement.

| Finding | Disposition in the current roadmap |
| --- | --- |
| Old-installation adoption, schema inventory, full-backup restoration and historical upgrade required before handoff | Removed. Reuse setup code and the verified HIV archive, not the previous database. No migration signoff is pending. |
| Repair of `chartsearchai-009` treated as the next delivery step | Removed from this delivery. The reproduced historical defect remains dated evidence, not a setup blocker or an authorized product change. |
| A fresh assistant session made an extra acceptance gate | Simplified to tested, self-contained commands and one generic guide usable by humans or assistants. The actual recipient walkthrough remains. |
| Update requirements could grow into a custom branch/update framework | Bound to existing Git, workspace and native commands, with clear selected revisions and no destructive automatic source changes. |
| Repeated proof of existing harness independence/reporting could expand setup work | Reuse existing tests/evidence where unchanged; require one real small clinical run/report against the new setup. |
| Account setup not expressed as ordered reusable additions | Added baseline/application/scenario layers, declared affected records, conflict checks, safe repetition and receipt provenance. No generic plugin or migration engine. |
| Credential/setup complexity | Retained the already-restored `admin` / `Admin123` default. No new administrator bootstrap or password-policy approval; private overrides remain private. |

Retained because they serve the requested handoff: the HIV-only baseline, all
seven accounts, real account/location context in both providers, browser evidence,
follow-up/reload and supported In-Depth states, a small evaluation/report, generic
instructions, and final code-qa/security/scope review. Ordinary repeat startup
must not reload data or duplicate accounts. Catalyst reuse remains later work.
None of these remaining requirements authorizes model tuning, production
permission redesign or an automatic role-to-prompt policy.

**Implementation finding to address when connecting lifecycle:** the current
`scripts/environment.py:check_ownership` rejects selected volumes without an owning
container, and `scripts/stack-down.sh` normally removes containers while retaining
volumes. A blanket orphan-volume rejection cannot become the public restart path.
Verify ordinary stop/start of the newly created environment using native ownership
metadata; do not turn it into another backup or recovery workflow. Runtime code is
unchanged by this documentation audit.

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

## Reuse Decisions

Paths in the first column refer to the original setup PR unless marked current.

| Source | Treatment | Reason and next proof |
| --- | --- | --- |
| `docs/environment-setup.md` | Rewrite as the generic umbrella operator guide | Retain useful fresh-setup commands and recipient checks; old commands and harness ownership are no longer correct |
| `.claude/skills/harness-environment/SKILL.md` | Replace with a thin umbrella assistant entry point | Link one maintained human guide, without a separate installation procedure or mandatory new-agent exercise |
| `datasets/validation/evaluation-roles.json` | Port the seven account definitions into the research preset's account input | All seven roles are required; remove unused study-tier metadata, preserve occupational labels, explicit read privileges and existing-role requirements |
| `harness/evaluation_users.py`, `harness/common/openmrs.py`, `scripts/provision-evaluation-users.py` | Adapt the required account provisioning to umbrella operations | Reuse generated credentials, ownership checks, no existing-role rewrite and real login checks; test unrelated users, role inheritance and both providers |
| `harness/environment_setup.py` | Reuse necessary target selection and repeat-start checks, not the fixed-stack implementation wholesale | Operate on the selected new installation and leave unrelated resources alone; do not implement adoption |
| `harness/evaluation_setup.py` and data/reset tests | Reuse verified baseline import and explicit reset behavior only | Fresh setup uses the reviewed archive; old-database backup/restore and historical upgrade guarantees are outside this delivery |
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

## Runtime Boundaries

A read-only Docker listing found a healthy OpenMRS stack under Compose project
`chartsearch-pr-split`, using the fixed `harness-*` container names. Other Catalyst,
OpenELIS and unrelated stacks are also running. This is an author-side observation,
not Ross's installation inventory and not evidence that the new umbrella owns
those services. None were restarted or claimed.

The reported historical schema collision is not a fresh-setup requirement.
No old database, existing-installation inventory, backup restoration or storage
adoption is needed. The current roadmap calls for a new selected environment with
the verified baseline and declared additions. This does not authorize deleting
or modifying any unrelated installation.

Before calling the handoff ready, also verify all seven account logins, actual
role/location transport through both providers, a completed question/follow-up,
inspectable evidence, In-Depth completion/failure, reload, a small independent run
and portable report. Recipient walkthrough and final quality/security/scope review
remain separate acceptance requirements.
