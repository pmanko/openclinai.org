# Research Setup: Source Inventory and Scope Audit

Inspected 2-3 October 2026. The [setup roadmap](../reusable-environments-roadmap.md)
owns the current requirements; this document identifies existing material to reuse.

## Scope Audit, 3 October 2026

This PR sets up a fresh HIV OpenMRS environment. It does not adopt an old database,
build an environment manager or validate model quality.

| Area | Action |
| --- | --- |
| HIV archive and disabled stock patient generator | Keep |
| Seven evaluation account definitions | Keep and connect the existing provisioner |
| Existing build, import, startup and configuration tools | Reuse |
| Custom selector, status, storage/ownership audits and isolated build layer | Remove |
| Added setup tests, command assertions, exact-archive restriction and table hashing | Remove; use simple live smoke checks |
| Backup/restore and old-database repair additions | Remove |
| Role-context, functionality evaluation, reports and video | Separate subsequent work |

## Sources

- Umbrella baseline: `82dd3bff2c833ebf23a50d0c67b9757a06dbc4d5`.
- [Original setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148),
  inspected at `2b3b1fd0a112b3a3710cda45211212ae7d90c96f`: account definitions
  and provisioning in `harness/evaluation_users.py`,
  `harness/common/openmrs.py` and `scripts/provision-evaluation-users.py`.
  Port only that necessary behavior, not its old installer.
- Existing [HIV baseline package](https://drive.google.com/file/d/1FxuaYxOfthzMHVL4bUPleLj_P7n_EN-X/view):
  contains `refapp_28_demo.sql.gz` and its native provenance sidecar.
- [Account-context PR #33](https://github.com/pmanko/openmrs-module-chartsearchai/pull/33),
  inspected at `9416ffacce13264aa67ce5d5addc7b4245e9834b`: later product work.
  The selected ChartSearchAI `8622f1b5c8995ac5361dd634705434ba65fe2fae`
  does not transport that account context. Creating accounts does not prove it does.

These are inspected revisions, not assertions about current remote PR status.
No component source or pin changes are part of this scope cleanup.
Use the [operator guide](../../environments/README.md); earlier partial startup
observations are [recorded separately](2026-10-02-research-preparation-proof.md).
