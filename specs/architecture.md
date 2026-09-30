# OpenClinAI Umbrella Refactor Proposal

**Status:** Supporting architecture for the published private umbrella workspace;
runtime refactoring and product publication remain pending.
**Date:** 2026-09-30
**Scope:** Clarify umbrella/component responsibilities and migrate incrementally
without changing clinical behavior, evaluation policy or active delivery scope.

**Roadmap home:** [OpenClinAI roadmap](roadmap.md) owns umbrella priorities,
U0-U5 ordering, dependencies, phase evidence and acceptance. This document moved
with the coordination plan on 30 September 2026; it supplies design rationale,
not a parallel execution register.

## 1. Recommendation and Naming

Establish `openclinai.org` as the separate umbrella coordination project. Keep the
Clinical AI Validation Harness as a distinct component alongside the existing
product repositories and their release ownership. Separate responsibilities
before deciding where operational tooling or website code should move.

OpenClinAI remains the public brand at `openclinai.org`. The local coordination
home now uses that name; this does not rename the harness, change a domain,
move the website or rewrite artifact identities. The umbrella repository is
`pmanko/openclinai.org`, private initially. Decisions
about runtime/package extraction and publication follow the roadmap's U0-U5 gates.

## 2. Observed Reasons to Refactor

The paths below are in `clinical-ai-validation-harness`, inspected on 30 September 2026.

- `harness/cli.py` mixes data remap/terminology commands and clinical/Catalyst
  validation commands. `harness/config.py` combines workspace configuration with
  Feature 002 path definitions.
- Root `pyproject.toml` has one `harness-cli` entry point and one distribution
  with database, SQLMesh, FHIR and general evidence dependencies together.
- `harness/targets.py` accepts only the four initial validation target IDs and
  specific `targets/`/`compose/` paths. `harness/targets.yaml` describes validation
  targets rather than all umbrella components; ESM and Hub are separate gitlinks
  but not first-class records in that validation registry.
- `harness/validate/runner.py` imports metrics, report generation and model-router
  policy alongside execution/evidence capture. These are explicit seams worth
  separating, not proof that their current behavior is wrong.
- Deployment scripts, data preparation, evidence/report publishing, public
  `landing/`, documentation/status `site/`, and governance already coexist here.
  Their differences should be made explicit, not erased through one generic API.
- Products are already separate git submodules. The immediate problem is umbrella
  responsibilities and coupling, not absence of repository separation.

These observations use the inspected checkout, which is behind cached main.
Refresh the inventory before assigning implementation changes. Existing delivery
constraints remain stronger than this draft recommendation.

## 3. Responsibility Map

| Owner | Owns | Must not become |
| --- | --- | --- |
| OpenClinAI workspace/platform tooling | Component discovery, checkout resolution, exact pins, dependency/build order, environment wiring, isolated lifecycle commands, artifact identity and reference-release composition | A second clinical application, patient datastore, model-quality grader or mandatory runtime service |
| Clinical AI Validation Harness | Explicitly authorized experiment execution through real product APIs, evidence capture, run provenance, domain-specific evaluation/human review, offline reports and validation-specific fixtures and test environments | Production conversation state, live clinical policy, product query execution or a prerequisite for running a product |
| General data tooling | Reusable data-migration and terminology utilities with an explicit owner; validation-specific mappings, corpus preparation and fixture loading remain with the harness | Authoritative clinical records, automatic reseeding or a replacement for native FHIR ingestion |
| ChartSearchAI and ESM | OpenMRS authorization/conversations, provider lifecycle and persistence, bundled inference and configured Hub adapter, evidence/clinical UI | A duplicate QueryStore index or compulsory Hub-only application |
| QueryStore | OpenMRS read projections, synchronization, retrieval, shared context slices, source dates/freshness/completeness and public read API | A generic model executor, application chat UI or umbrella metadata database |
| Med Agent Hub | Configured model profiles, prompts, role mappings/settings, model access and its existing declared clinical execution contracts | Catalyst schema discovery, SQL execution, Dataset/Dashboard state or automatic selection of a winning model |
| Catalyst | Source/dialect/schema context, writer/reviewer sequencing, advisory query validation, exact selected SQL execution, versioned Datasets/Widgets/Dashboards and native publication | FHIR ingestion, a preferred warehouse engine or a clinical-answer scoring system |
| Website/documentation/status surfaces | Public explanation, guides, dated progress, design/evidence discovery and links to owning contracts | Another source of product requirements, operational truth or regenerated historical judgments |

The harness's boundary is validation-specific, not general integration delivery.
Its fixtures, adapters, test environments, evidence and methodology stay there;
product feature specifications, cross-project release coordination and shared
website/deployment ownership do not. The roadmap's spec-disposition table records
which existing documents stay, move or require a content-level split. Maintained
specs describe current state or current implementation direction only. Obsolete
spec content is deleted, not retained behind banners or moved into an archive;
Git history supplies past versions. A split transfers only current requirements,
with one maintained owner and direct consumer references.

Model serving remains the configured external runtime. FHIR Data Pipes and
Superset retain ingestion and visualization responsibilities. Native OpenELIS
reporting remains independently useful without Catalyst or Hub.

For Catalyst, Hub owns configured named model roles; Catalyst owns application
orchestration. Do not generalize that boundary into deleting the Hub's existing
clinical pipeline or moving it into validation. Audit any proposed clinical
pipeline relocation against the dual-provider contract as a separate change.

## 4. Target Structure, Not a Day-One Move

The umbrella is a scoped submodule-based workspace. Its initial checkout layout
preserves component histories and the existing runtime paths:

```text
openclinai.org/
  specs/                        # maintained umbrella direction and decisions
  scripts/                      # umbrella checks; shared tooling migrates by slice
  tests/                        # umbrella-tooling checks
  targets/
    validation-harness/         # exact published harness gitlink
      targets/                  # product gitlinks remain authoritative here
  artifacts/                    # ignored local execution evidence
```

There is no duplicate top-level product pin set. Promote product checkouts to
direct umbrella submodules only with a reviewed migration of harness consumers,
build contexts, scripts and publication checks; do not point two gitlinks at the
same product independently. The sibling harness remains untouched for its local
work. Shared workspace/deployment capabilities migrate here by their owning
requirements; validation capabilities remain in the harness.

Move files and create installable workspace packages only when the dependency
inventory proves their boundaries. Keep existing scripts, `harness` imports,
`harness-cli` and environment variable names working through migration. Do not
create empty package/deployment/website trees or a new shared framework.

## 5. Dependency Rules

- Products own their production APIs and contract schemas. The workspace pins and
  consumes them; validation invokes them through thin adapters. Product runtime
  code must not depend on the validation runner or umbrella website.
- Deployment commands may assemble products without importing scoring/report
  modules. An offline report command must not start Docker, contact a model,
  query a clinical source or rerun a judgment to reconstruct presentation.
- Evidence rendering reads frozen run artifacts. Explicit publishing handles
  network/filesystem side effects separately. Preserve the existing shared
  report publisher rather than creating one publisher per product.
- Keep reusable checkout/identity/provenance primitives small and based on actual
  shared use. Do not introduce a universal clinical object model across patient
  chat and analytical SQL results.
- Model/profile definitions stay with Hub; application context and conversation
  stay with the relevant product. Experimental configuration remains explicitly
  separate from production defaults and carries its own provenance.
- Extend/reconcile the existing registry into a component catalog, with optional
  validation surfaces and component-specific release policy. Do not maintain
  separate drifting component catalogs. Gitlinks remain the canonical pins;
  `.gitmodules` supplies URLs/branch hints, not a second version lockfile.
- Preserve upstream-owned fork policy for ChartSearchAI, ESM and QueryStore;
  workspace/Hub release policy does not override those projects' governance.

## 6. Migration and Acceptance Ownership

The [integrated roadmap's umbrella track](roadmap.md#10-track-b-openclinai-umbrella-refactor)
owns the U0-U5 phase register and exit criteria. Review ownership/dependencies
first; establish behavior-preserving seams before package isolation; organize
operational paths before a deliberately approved naming migration; then reconcile
and close out remaining compatibility code.

Use small reviewed changes, not a big-bang move. Retain before/after evidence at
exact revisions. Add regression tests for changed behavior without weakening
existing assertions. Dependency isolation and packaging must not change grading
rubrics, scoring, sampling, model settings, clinical-context policy or historical
result values. Phase state and owner decisions are recorded in the roadmap.

No cloud resource, identity/SSO system, generic connector layer, event bus,
service discovery server or shared clinical warehouse is required by this design.
Propose an additional subsystem only after documenting a concrete unmet need.

## 7. Relationship to Current Work and Durable Records

This document supports the umbrella track and its validation-only harness
boundary. The roadmap owns the legacy-spec disposition and migration gates.
Keep QueryStore/OpenMRS and Catalyst delivery moving while relocating coordination;
retain their current requirements and relevant evidence references, delete obsolete
spec content, and update consumer references as each mixed document is split.

- [First-slice inventory](spec-cleanup-inventory.md) identifies current cleanup
  consumers and the canvas direction decision. The sibling sitrep remains local
  evidence and is not a published source link.
- [Integrated refactor roadmap](roadmap.md) retains its validity,
  publication and source-pair gates; this draft does not approve their transition.
- [Dual-provider roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap.md) and its
  [status/amendments](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap-status.md) own OpenMRS
  behavior and existing signoffs.
- [Four-pathway roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/openelis-reporting-catalyst-integration.md) and
  [Feature 008 tasks](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/008-catalyst-query-workbench/tasks.md) retain Catalyst
  delivery order, scope and acceptance.
- [Public website contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/landing/README.md) owns public hierarchy;
  [Catalyst-Hub contract](https://github.com/DIGI-UW/openelis-catalyst/blob/6ba00082519f9fb2d864895b292352d8987ce51c/docs/med-agent-hub.md) owns
  that current application boundary.

Keep this supporting architecture record in `openclinai.org/specs/`; execution
sequence and phase status belong to `roadmap.md`. Any governance change must
update the owning component's instructions/contracts through its reviewed change
process. The coordination transfer does not modify Feature 008 or create a new
specification per component, and establishes no runtime or deployment acceptance.
