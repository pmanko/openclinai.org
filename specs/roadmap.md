# OpenClinAI Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`

This roadmap coordinates the OpenClinAI workspace, validation harness and product
delivery. [Architecture](architecture.md) defines component responsibilities and
interfaces. Product repositories own their application requirements and detailed
implementation registers.

## 1. Current Priorities

1. Extract small, reviewable ChartSearchAI backend and frontend PRs from each
   project's current `main`, using its `harness-integration` branch as a reference.
   Each PR contains one coherent change with its tests and documentation.
2. Review the published component-ownership slice:
   [harness #197](https://github.com/pmanko/clinical-ai-validation-harness/pull/197)
   and [umbrella #2](https://github.com/pmanko/openclinai.org/pull/2).
   Merge the harness first, then the umbrella; retain separate product-build and
   deployed-acceptance evidence.
3. Consolidate the remaining Catalyst and OpenMRS delivery specifications into their
   maintained owners, preserving current requirement identifiers and updating consumers.
4. Continue QueryStore review and Catalyst delivery through their product contracts.
   Verify product-native builds and shared environments against recorded revisions;
   record deployed acceptance separately from source verification.

## 2. Implementation Status

| Area | Current state | Remaining work |
| --- | --- | --- |
| Umbrella repository | [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org) has the component-ownership implementation published in PR #2, including product operations and website sources | Review and merge the assembled changes |
| Component checkouts | Fresh recursive GitHub clone resolves exactly six direct components at their recorded revisions; harness product gitlinks and `openmrs_chatbot` are absent | Review and merge the component changes |
| Validation harness | Clinical and Catalyst runners use configured targets and supplied/observed provenance; source-free wheel isolation, portable reports and the full local harness suite pass | Review the published component change and verify actual product interfaces separately |
| Website | `landing/`, `site/`, static hosting configuration, build/publication tools and workflows are umbrella-owned; local website tests and build have run | Hosted CI and explicit deployment acceptance |
| Specifications | Harness governance and validation foundations are reconciled; retained 004 criteria are in Feature 006; obsolete 004/005/007 files are removed | Consolidate mixed Feature 008, program-delivery and OpenMRS coordination specifications |
| Product delivery | ChartSearchAI backend #157 and frontend #23 contain the integration implementations; smaller main-based PRs are the selected delivery approach | Extract focused changes, verify each against current main and publish in dependency order; retain integration branches as references |

The phases below cover the component layout and validation interfaces defined in
the architecture. Progress distinguishes implementation, local verification, CI,
publication and deployed acceptance.

## 3. Track B: Workspace and Validation Architecture

| Phase | Deliverable | Acceptance criteria | Status |
| --- | --- | --- | --- |
| U0 Ownership and dependencies | Map capabilities, interfaces and consumers to component owners | Each capability has an owner, defined inputs/outputs and verification criteria | First-slice runtime, operations and publication consumers mapped; remaining specification ownership pending |
| U1 Component and management ownership | Direct umbrella gitlinks and workspace-management tooling; removal of nested product gitlinks and `openmrs_chatbot` | One canonical gitlink per component; fresh umbrella checkout resolves recorded revisions; umbrella tooling manages component selection and checkouts | Implemented and published for review; fresh recursive checkout, workspace checker and component cleanliness pass |
| U2 Independent validation | Modular experiment execution, target adapters, evidence collection, evaluation and reporting | Experiments run against configured targets without Git, submodules, product source trees, product pins or an umbrella installation; offline reports consume captured artifacts only | Local runtime, full regression and installed-wheel clinical/Catalyst isolation checks pass; portable reports tested with doubles; component review and real-interface acceptance pending |
| U3 Environment and delivery tooling | Umbrella environment, build, deployment and release orchestration; OpenClinAI website build and publication tooling | Configured workspace operations invoke product-native commands; website build/publication runs from umbrella-owned sources, configuration and workflows; build/run provenance records actual inputs | Required local operations and website delivery tooling moved; local checks/build pass; actual product builds and deployment pending |
| U4 Documentation and interfaces | Current specs, instructions, commands, configuration, CI and website consumers aligned with ownership | Consumers resolve directly to current owners; obsolete specs, copied history and unnecessary compatibility entry points are removed | Governance, foundational specs, commands, tests and website consumers aligned; mixed delivery-spec consolidation remains |
| U5 Completion | Remove remaining obsolete code, dependencies and duplicate responsibilities; verify the assembled system | Independent harness checks and umbrella integration checks pass; current requirements have one maintained owner; component and deployed acceptance are explicit | Not implemented |

### Dependencies

- U0 maps the capabilities and consumers affected by each implementation change.
- U1 and U2 share changes where component layout affects a validation adapter.
- U3 uses the component configuration and native entry points established in U1.
  Website source and publication ownership can be implemented independently of
  product checkout changes.
- U4 updates documentation, references and tests alongside their interfaces.
  With U1/U2, amend the harness constitution, agent instructions and SpecKit context
  to define experiment-runner scope and configurable targets; remove control-plane
  duties and the fixed product-path requirements.
- OpenMRS contribution publication proceeds as a separate delivery track.

### Verification

**Harness isolation:** Install and run configured experiments in an environment
without Git, product source checkouts or the umbrella. Confirm that execution does
not perform pin lookups, checkouts, builds, deployments or release-policy checks.
Test adapter configuration, output/trace capture, supplied or observed provenance,
missing-metadata handling and evaluation/report generation. Test doubles validate
runner mechanics; product acceptance uses actual product interfaces.

**Umbrella integration:** Verify component gitlinks, remote reachability, required
build/deployment entry points and the configured handoff to validation. Component
commits are published in their owning repositories before being referenced by an
umbrella gitlink. Verify that experiment manifests capture the target identity
supplied by the workspace or reported by the target.

**Website delivery:** Build and preview the selected public surfaces from this
repository. Check navigation, links, assets, media and narrow/desktop rendering.
Run publication checks through umbrella-owned tooling and record the source
revision, deployed output and live verification. The website build and deployment
pipeline operates independently of the validation runtime.

**Contract coverage:** Verify product safety and clinical behavior against product
contracts, and scoring and sampling against experiment definitions. Maintain test
coverage for each supported interface and remove tests for retired interfaces.

## 4. Specification Ownership

Paths in this table are relative to the validation harness. Each row identifies
the maintained destination for its requirements.

| Source material | Validation responsibility | Other ownership or disposition |
| --- | --- | --- |
| `specs/001-harness-control-plane-foundation/` | Experiment readiness, fixture/endpoint identity and run provenance | Component catalog, pins, checkouts, builds and shared environment management belong to the umbrella |
| `specs/002-openmrs-demo-data-2-8-remap/` | Reviewed validation corpus, mappings, fixtures, clinical-meaning checks and provenance | Reusable migration/terminology utilities require a data-tooling owner; shared deployment belongs outside the harness |
| Feature 006 smoke/evaluation criteria | Retains `SC-004.4` and namespaced `MAH-CONSOLIDATION-2026-07-09-v1:G09/G21` | Obsolete Feature 004/005/007 files and the redundant consolidation roadmap are deleted |
| `specs/006-validation-harness-mvp/`, metadata and evaluation contracts | Scenarios, adapters, evidence, evaluation, review and reporting | Link transport and provider behavior to their product contracts |
| `specs/008-catalyst-query-workbench/` | Validation scenarios, experiment protocols, evidence and reporting | Catalyst owns application requirements; the umbrella owns cross-project delivery coordination |
| `specs/catalyst-program-roadmap.md`, `specs/openelis-reporting-catalyst-integration.md` | Evaluation methodology and test protocols | Current delivery priorities belong to the umbrella; application behavior belongs to Catalyst/OpenELIS |
| `specs/artifacts/planning/openmrs-dual-provider-*` | Conformance experiments and their evidence | Joint delivery, review and release coordination belong to the umbrella; concrete API behavior remains product-owned |
| Program lanes/status | Validation-specific results and dated evidence | Current coordination belongs to this roadmap; obsolete public roadmap and architecture canvases are deleted |
| Website sources and tests | Experiment artifacts and report generation | `landing/`, `site/`, public catalogs and `tests/website/` are implemented in this repository |
| Website/report publication | Validation output artifacts supplied for publication | Umbrella `scripts/`, `.github/workflows/pages.yml` and `compose/website/` own static publication; product deployment is separate |

Each requirement retains its identifier under one maintained owner. Update SpecKit
pointers, instructions, links, imports, navigation, generated catalogs and tests to
reference that owner. Remove obsolete specification content and its references.

## 5. Track A: OpenMRS Contribution Delivery

This track coordinates QueryStore, ChartSearchAI and its OpenMRS frontend.
Application behavior is defined by the
[dual-provider conformance contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/9c1f65606f357662419aaa3417a4dde6d81c9948/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md)
and [QueryStore ADR](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/adr.md).
The [delivery status register](https://github.com/pmanko/clinical-ai-validation-harness/blob/9c1f65606f357662419aaa3417a4dde6d81c9948/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap-status.md)
records implementation and acceptance evidence at the selected harness revision.
The component repositories maintain subsequent development and release status;
coordination content is assigned to the umbrella under section 4.

### Contribution Model

Create fresh topic branches from the destination project's current `main` and
open small PRs targeting that `main`. Use the existing integration implementation
to identify and implement the intended capability, adapting it to current product
code and contracts. Fresh commits are expected; preserving commit history, merge
structure or the integration branch's exact diff is not an acceptance requirement.

The existing `harness-integration` branches remain available as reference. Do not
rewrite, delete or rebase them as part of this split. Track capability coverage and
remaining work, not a replay or disposition of every historical commit.

Each PR must be understandable, buildable and testable against its main base.
Independent changes may proceed in parallel. A dependent change follows its
prerequisite into `main`; do not include unmerged prerequisite changes merely to
make a later PR compile. Include relevant tests and documentation with the behavior.

### Milestones

| ID | Deliverable | Acceptance |
| --- | --- | --- |
| M0 | Current main/reference comparison and capability dependencies | Main and integration reference revisions are identified; intended changes, existing upstream behavior and necessary prerequisites are understood |
| M1 | QueryStore Q0 review resolution | Exact-source tests and required integration evidence support the published contribution |
| M2 | Small main-based backend/frontend PRs | Each PR implements one coherent change, targets current main and passes its applicable checks; capability coverage and remaining work are explicit |
| M3 | Backend delivery | B1–B5 satisfy product contracts and affected integration checks |
| M4 | Frontend delivery | F1–F3 satisfy lifecycle, provider and evidence/browser acceptance against the tested backend |
| M5 | Integrated release acceptance | Assembled product behavior and deployed evidence satisfy the existing release signoffs |

Publication requires current source/review status and applicable verification
evidence. Resolve dependencies in order: QueryStore APIs before backend consumers,
and backend APIs before frontend consumers that require them. Independent changes
need not wait for unrelated work. Paired tests provide integration evidence but do
not replace each PR's checks against its main base.

### QueryStore Review Slice Q0

Q0 resolves [QueryStore review #68](https://github.com/openmrs/openmrs-module-querystore/pull/68),
covering preprocessing documentation, dispatcher link handling, explicit chart-read
construction and parameter/resource-type validation. The
[QueryStore API contract](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/rest-api.md)
and product review own the detailed behavior and any required contract updates.

Delivery requires exact-source reactor and MySQL integration evidence, applicable
HTTP-path verification and evidence-linked review dispositions. Skipped tests and
additional Elasticsearch checks are recorded separately.

### Backend and Frontend Boundaries

These capability groups organize the work by responsibility and dependency.
They are not fixed PR sizes: subdivide or adjust boundaries to produce small,
coherent changes against current main.

| Slice | Responsibility | Integration dependency |
| --- | --- | --- |
| B1 Contract | Provider descriptors, request/result and event types, answer envelope, lifecycle and cancellation contract | No concrete provider implementation required |
| B4 Context consumer | QueryStore-backed chart context and token/budget accounting; retrieval policy remains in QueryStore | B1 and the reviewed QueryStore API |
| B3 Bundled provider | Bundled inference implementation, registry and routing/engine integration | B1/B4; bundled installation remains independent of Hub |
| B2 Hub adapter | Configured Hub discovery, request/stream transport, cancellation and failure handling | B1/B3; no silent provider fallback |
| B5 OpenMRS integration | Authorization, conversation persistence, schema changes, REST/SSE and startup wiring | B1–B4 |
| F1 Transport and state | Client transport, lifecycle, durable session state and reload behavior | Backend contracts; B5 for real-path acceptance |
| F2 Provider selection | Explicit provider selection and configuration-aware availability | F1 and backend provider discovery |
| F3 Answer and evidence UI | Clinical output, references, original/rejected drafts, validation/safety disclosure and optional In-Depth | F1/F2 and real backend payloads |

The proposed backend dependency order is B1 → B4 → B3 → B2 → B5; frontend order
is F1 → F2 → F3. Confirm these dependencies against current main before extraction.
Each PR must compile and satisfy the relevant product contracts on that base.
Integrated acceptance covers explicit provider choice, no silent fallback,
traceable evidence, cancellation and reload survival.

### Publication

Publish each topic branch to the project fork and open its PR against the
corresponding project's `main`. PR descriptions state the focused behavior,
applicable contract, tests and dependencies; they need not reproduce the
integration branch's development history.

Update `scripts/openmrs-source-pair-test.sh`, `scripts/verify-repository-lines.sh`
and their CI consumers to verify selected PR revisions and dependency versions
rather than require every contribution head to equal `harness-integration`.
The umbrella continues to own assembled-system gitlinks and reproducible source
verification. The integration branches remain reference sources, not publication
gates for the new PRs.

The split does not authorize closing the existing integration PRs. Their disposition
can be decided once the smaller contributions cover the intended capabilities.
Branch retention is independent of PR closure. QueryStore #68 review remains its
own delivery work; do not expand the ChartSearchAI split to it automatically.

## 6. Catalyst Delivery

The [four-pathway delivery roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/9c1f65606f357662419aaa3417a4dde6d81c9948/specs/openelis-reporting-catalyst-integration.md)
and [Feature 008 register](https://github.com/pmanko/clinical-ai-validation-harness/blob/9c1f65606f357662419aaa3417a4dde6d81c9948/specs/008-catalyst-query-workbench/tasks.md)
record delivery scope and acceptance at the selected component revision. Catalyst
owns the SQL workbench, Datasets, Widgets, Dashboards and publication. Med Agent Hub owns configured model
roles; native reporting remains OpenELIS-owned.

The umbrella tracks cross-project delivery; the harness maintains validation
protocols and evidence; Catalyst and Med Agent Hub maintain their application
contracts and implementation tasks.

## 7. Outstanding Decisions

- **Data tooling:** Assign a maintained owner for reusable migration and terminology
  utilities outside the validation harness.

- **Public delivery:** Decide repository visibility/organization and website hosting
  changes separately from the internal component layout.
