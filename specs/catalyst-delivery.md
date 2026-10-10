# Catalyst delivery

**Stream:** Catalyst reporting journeys · **Status:** four journeys demonstrated;
local and server acceptance, publication verification and owner review open ·
**Owner:** umbrella for shared environments, rollout order and publication

Catalyst owns application behavior in its [specification][product], [Dashboard
Builder design][binding] and [reporting integration design][design]. The harness
owns the comparison protocol and static reference/reader evidence. The umbrella
owns shared environments, rollout and publication through the
[operations guide](../docs/catalyst-demo-operations.md). Dated evidence: the
[2 October documentation audit](reviews/2026-10-02-documentation-audit.md#evidence-and-coverage)
and the published demonstrations it cites.

## Journeys

| Path | Complete journey | Use |
| --- | --- | --- |
| 1 | OpenELIS report builder → CSV → native Superset upload → table/chart/dashboard | Visualize a deliberately configured report without Catalyst or AI. |
| 2 | OpenELIS CSV → Catalyst upload and review → imported Dataset → Widgets/Dashboard → Superset | Build on an existing report without SQL interaction. |
| 3 | OpenELIS PostgreSQL → Catalyst question/refinement → explicit execution → Dataset/Widgets/Dashboard → Superset | Explore the native database independently of the report builder. |
| 4 | The same OpenELIS instance's FHIR output → FHIR Data Pipes → Parquet/Spark → Catalyst → Superset | Explore FHIR-derived analytics with its actual coverage and freshness. |

Manual SQL correction is a valid completion path for connected-data workflows.
Retain generated and edited versions and show recovery honestly. Fix failures in
reviewing, executing, saving or publishing; model mistakes do not automatically
create a tuning or benchmarking project.

Existing implementation and September demonstrations are evidence to reconcile,
not a backlog to replay. Native OpenELIS reporting retains its own specification
and review process. Shared production identity/access is a separate milestone.

## Requirement register

Retained task IDs route to their existing owners:

| ID | Maintained owner and deliverable |
| --- | --- |
| FP-001 | This spec: reconcile cross-project scope, requirement ownership and consumers; remove competing sequences without losing unique requirements. |
| FP-002 | [Catalyst integration design][design]: approved CSV/import and PostgreSQL source interactions, recovery, retained drafts and visual review. |
| FP-003 | This spec, with the [native reporting owner][native]: real saved-report rerun and CSV → Superset table/summary chart; inspect repeated results, dates and values, and begin same-instance FHIR coverage review. |
| FP-004 | [Catalyst PostgreSQL source][postgres]: ordinary connection, complete readable schema, exact execution, types/bounds and editor; retain Spark behavior. |
| FP-005 | [Catalyst publication/import][publication]: actual backing source and dialect, immutable saved versions, deterministic bundles, retry and receipts. |
| FP-006 | [Catalyst imported Dataset][imports]: file review, immutable durable imports, failures/retry, retained artifacts and origin-specific provenance. |
| FP-007 | [Catalyst Widget][widgets]: shared reviewed grouping/aggregation and meaningful raw-row charts; immutable versions and publication. |
| FP-008 | This spec, with native FHIR and pipeline owners: actual reporting-instance FHIR output reaches Spark, Catalyst and Superset with record provenance and honest coverage/freshness. |
| FP-009 | This spec: four complete local journeys, rendered-value checks, retained state and desktop/narrow light/dark review against approved designs. Record findings and owner feedback. |
| FP-010 | This spec: compatible reviewed deployment, four server journeys, verified published videos/page and explicit owner acceptance. |

Product-owned rows (FP-002, FP-004 to FP-007) are tracked in Catalyst's
specification; this spec does not tick them.

## Target path

- [x] FP-001 local consolidation of scope and ownership verified
      ([audit](reviews/2026-10-02-documentation-audit.md#consolidation-prepared-locally)).
- [ ] FP-001 owner review and publication of the reconciled scope.
- [ ] FP-003 real saved-report rerun and CSV → Superset table/summary chart with
      repeated results, dates and values inspected; same-instance FHIR coverage
      review begun.
- [ ] FP-008 reporting-instance FHIR output reaches Spark, Catalyst and Superset
      with record provenance and honest coverage/freshness.
- [ ] FP-009 four complete local journeys accepted: rendered-value checks, retained
      state, desktop/narrow light/dark review; findings and owner feedback recorded.
- [ ] FP-010 compatible reviewed deployment, four server journeys, verified
      published videos/page, explicit owner acceptance.
- [ ] Public Catalyst status reconciled to one dated summary (documentation audit D07).

## Acceptance rules

Verify source identity and record meaning through actual queries/imports, saved
Dataset/Widget/Dashboard state and rendered Superset values. All four paths use one
OpenELIS source per environment; the FHIR path uses its actual output and states
coverage/freshness limitations. Counts alone do not prove correctness. The separate
OpenMRS/OpenELIS reference deployment needs both sources' complete journeys.
Product contracts own detailed behavior and failure cases; this spec does not copy
their checklists.

One real ingestion-to-render proof establishes a source when integrated. Reuse
retained data and rerun affected checks for relevant changes or failures. Final
release uses compatible reviewed revisions; development can proceed before upstream
merges. Preserve existing data, configuration and unrelated deployments.

Public demonstrations make each starting point, workflow, actual outcome and
limitations easy to understand. Use readable recordings of real interactions,
identify the recording environment and actual model roles, and verify final media
and links before publication. Local video proof, server checks, publication and
owner acceptance remain separate facts. Earlier recording scripts and measurements
remain in [dated evidence][catalyst-history], not here.

## After acceptance

The product's implementation direction is responsiveness and session navigation,
then A (multi-artifact design and shared controls), B (Metabase) and C (Evidence).
Model comparison and broader conversation work are separately scheduled. Designs
for follow-ons are reviewed when those efforts start.

## Decisions

- [ ] **Source discovery:** review current-data versus snapshot-history presentation
      at the FHIR Data Pipes source boundary. Preserve saved SQL and snapshots; do
      not add a FHIR-specific filter to Catalyst.

[product]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md
[binding]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/dashboard-builder-mvp-design.md
[design]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specs/openelis-reporting-integration/spec.md
[postgres]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#postgresql-source
[publication]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#publication-and-import
[imports]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#imported-dataset
[widgets]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#widget
[native]: https://github.com/DIGI-UW/OpenELIS-Global-2/blob/codex/reporting-ui/specs/479-reporting-mvp/plan.md
[catalyst-history]: reviews/2026-10-02-documentation-audit.md#evidence-and-coverage
