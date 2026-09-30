# OpenClinAI Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`

This roadmap coordinates the OpenClinAI workspace, validation harness and product
delivery. [Architecture](architecture.md) defines component responsibilities and
interfaces. Product repositories own their application requirements and detailed
implementation registers.

## 1. Current Priorities

1. Establish direct umbrella submodules for the validation harness, Med Agent Hub,
   Catalyst, ChartSearchAI backend/frontend and QueryStore. Remove the harness's
   product gitlinks and the `openmrs_chatbot` target.
2. Remove checkout, pin, build, deployment and release management from the harness.
   Implement only the capabilities needed by the umbrella. Make the harness an
   independent, modular runner for configured validation experiments.
3. Align code, configuration, commands, tests and documentation with those owners.
   Consolidate current requirements and delete obsolete implementations and specs.
4. Continue OpenMRS contribution review and Catalyst delivery through their product
   contracts, independently of the workspace restructuring.

Only material needed by this architecture belongs in the umbrella. Content removed
from the harness is not automatically transferred here. Product behavior remains
product-owned; unnecessary tooling, retired plans and duplicate structures are
deleted rather than imported.

Changes to paths, commands, imports, configuration and package boundaries are
expected. Backward compatibility with the previous workspace is not a requirement.
Any compatibility mechanism needs an explicit current use case. Consumers are
updated directly; Git history holds previous code and specifications.

## 2. Implementation Status

| Area | Current state | Remaining work |
| --- | --- | --- |
| Umbrella repository | [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org) is published; workspace checks and CI exist | Direct component layout and operational tooling |
| Component checkouts | `targets/validation-harness` is initialized; product submodules are still nested beneath it | Move product gitlinks to the umbrella and remove the excluded target |
| Validation harness | Experiment functionality exists alongside workspace-management dependencies | Independent configuration, adapters and execution without Git, pins or product source checkouts |
| Specifications | Umbrella direction and architecture are defined; component specs still mix responsibilities | Consolidate current requirements into their owners and delete obsolete content |
| Product delivery | OpenMRS review and Catalyst delivery have existing contracts and task registers | Component verification, publication and deployed acceptance remain separate from workspace checks |

The current nested checkout layout is not the intended design. The phases below
cover its replacement. Implementation, local verification, CI, publication and
deployed acceptance are recorded separately; a workspace check is not product or
clinical acceptance.

## 3. Track B: Workspace and Validation Architecture

| Phase | Deliverable | Acceptance criteria | Status |
| --- | --- | --- | --- |
| U0 Ownership and dependencies | Assign affected capabilities to umbrella, validation or product ownership; identify required interfaces and consumers | Each changed capability has one owner and a testable destination; only requirements of the new setup justify additions | Ownership defined; consumer analysis incomplete |
| U1 Component and management ownership | Direct umbrella gitlinks; required checkout/build/release tooling outside the harness; removal of nested product gitlinks and `openmrs_chatbot` | One canonical gitlink per component; fresh umbrella checkout resolves recorded revisions; no product pin or checkout-management responsibility remains in the harness | Not implemented |
| U2 Independent validation | Modular experiment execution, target adapters, evidence collection, evaluation and reporting | Experiments run against configured targets without Git, submodules, product source trees, product pins or an umbrella installation; offline reports consume captured artifacts only | Not implemented |
| U3 Environment and delivery tooling | Umbrella environment, build, deployment and release orchestration using product-native entry points | Umbrella operations resolve component configuration and invoke product commands without validation scoring or experiment execution; build/run provenance reflects actual inputs | Not implemented |
| U4 Documentation and interfaces | Current specs, instructions, commands, configuration, CI and website consumers aligned with ownership | Consumers resolve directly to current owners; obsolete specs, copied history and unnecessary compatibility entry points are removed | Umbrella documentation updated; component changes pending |
| U5 Completion | Remove remaining obsolete code, dependencies and duplicate responsibilities; verify the assembled system | Independent harness checks and umbrella integration checks pass; current requirements have one maintained owner; component and deployed acceptance are explicit | Not implemented |

### Dependencies

- U0 analysis is limited to the capabilities and consumers affected by each change;
  it is not an exhaustive repository inventory prerequisite.
- U1 and U2 are implemented together where removing a gitlink requires changing a
  validation adapter. Harness-owned management is removed, not made configurable.
- U3 proceeds with the affected ownership changes. Required functionality may be
  moved, rewritten or replaced; copying existing scripts is not itself a deliverable.
- U4 accompanies each implementation change. References and tests are updated with
  their interfaces rather than deferred to a final documentation pass.
- OpenMRS publication decisions and individual spec cleanups do not gate the
  umbrella/harness separation.

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
umbrella gitlink. The umbrella selects versions; the harness records relevant
identity without selecting or enforcing those versions.

**Contract coverage:** Tests exercise current requirements. Tests that only enforce
removed paths, interfaces or responsibilities are removed or replaced alongside
those requirements. Structural changes do not silently redefine product safety,
clinical policy, scoring or sampling semantics.

## 4. Specification Ownership

Paths in this table are relative to the validation harness. These are cleanup and
ownership assignments, not instructions to copy whole documents into the umbrella.

| Source material | Validation responsibility | Other ownership or disposition |
| --- | --- | --- |
| `specs/001-harness-control-plane-foundation/` | Experiment readiness, fixture/endpoint identity and run provenance | Component catalog, pins, checkouts, builds and shared environment management belong to the umbrella |
| `specs/002-openmrs-demo-data-2-8-remap/` | Reviewed validation corpus, mappings, fixtures, clinical-meaning checks and provenance | Reusable migration/terminology utilities require a data-tooling owner; shared deployment belongs outside the harness |
| `specs/004-real-adapter-entrypoints/`, `specs/005-med-agent-hub-bridge/`, `specs/007-llm-config-overrides/` | Any still-current validation protocols missing from maintained validation specs | Consolidate current requirements with their product or umbrella owners; delete obsolete plans and files with no current responsibility |
| `specs/006-validation-harness-mvp/`, metadata and evaluation contracts | Scenarios, adapters, evidence, evaluation, review and reporting | Reconcile transport descriptions with current product contracts; do not make the harness own provider behavior |
| `specs/008-catalyst-query-workbench/` | Validation scenarios, experiment protocols, evidence and reporting | Catalyst owns application requirements; the umbrella owns cross-project delivery coordination |
| `specs/catalyst-program-roadmap.md`, `specs/openelis-reporting-catalyst-integration.md` | Evaluation methodology and test protocols | Current delivery priorities belong to the umbrella; application behavior belongs to Catalyst/OpenELIS |
| `specs/artifacts/planning/openmrs-dual-provider-*` | Conformance experiments and their evidence | Joint delivery, review and release coordination belong to the umbrella; concrete API behavior remains product-owned |
| `specs/roadmap.canvas.tsx`, program lanes/status and public website material | Validation-specific results and reports | Bring only current program information and required public surfaces into the umbrella; delete obsolete plans rather than migrating them |

Each retained requirement keeps its identity and one maintained owner. Update
SpecKit pointers, instructions, links, imports, navigation, generated catalogs and
tests with the affected content. A dependency on an obsolete spec is a consumer
to fix, not a reason to retain that spec. Historical reports remain evidence, not
sources of current requirements.

## 5. Track A: OpenMRS Contribution Delivery

This track coordinates QueryStore, ChartSearchAI and its OpenMRS frontend.
Application behavior is defined by the
[dual-provider conformance contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md)
and [QueryStore ADR](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/adr.md).
The [delivery status register](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap-status.md)
records implementation and acceptance evidence at the selected harness revision.
The component repositories maintain subsequent development and release status;
coordination content is assigned to the umbrella under section 4.

### Milestones

| ID | Deliverable | Acceptance |
| --- | --- | --- |
| M0 | Current source/base/PR inventory and dependency map | Candidate revisions, compilation dependencies and outstanding review findings are identified |
| M1 | QueryStore Q0 review resolution | Exact-source tests and required integration evidence support the published contribution |
| M2 | Reviewable backend/frontend decomposition | Every source delta has a destination; the cumulative sequence builds; the publication model is agreed |
| M3 | Backend delivery | B1–B5 satisfy product contracts and affected integration checks |
| M4 | Frontend delivery | F1–F3 satisfy lifecycle, provider and evidence/browser acceptance against the tested backend |
| M5 | Integrated release acceptance | Assembled product behavior and deployed evidence satisfy the existing release signoffs |

Publication requires current source/review status and applicable verification
evidence. Merge/deployment order is QueryStore, ChartSearchAI backend, then frontend.
Paired pre-merge testing can establish compatibility before upstream merge.

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

These are proposed contribution boundaries, subject to compilation dependencies.
Product requirements remain in the component contracts, not in duplicate umbrella
specifications.

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

The proposed backend order is B1 → B4 → B3 → B2 → B5; frontend order is F1 → F2 → F3.
An inseparable compilation dependency changes the boundary rather than requiring
production stubs or disabled tests. Current product requirements include explicit
provider choice, no silent fallback, traceable evidence, cancellation and reload
survival. They do not require retaining the previous umbrella/harness layout.

### Publication

The current OpenMRS contribution policy uses tested `pmanko:harness-integration`
heads. Publishing separate replacement PR heads requires agreement on the
publication model and corresponding verification changes. Until that decision,
review boundaries can organize the existing PRs without replacing them.

Replacement of QueryStore #68, ChartSearchAI #157 or frontend #23 requires accounted
source deltas and replacement links. Publication verification is an umbrella
responsibility, not a prerequisite for running validation experiments.

## 6. Catalyst Delivery

The [four-pathway delivery roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/openelis-reporting-catalyst-integration.md)
and [Feature 008 register](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/008-catalyst-query-workbench/tasks.md)
record delivery scope and acceptance at the selected component revision. Catalyst
owns the SQL workbench,
Datasets, Widgets, Dashboards and publication. Med Agent Hub owns configured model
roles; native reporting remains OpenELIS-owned.

The workspace refactor relocates coordination and validation content without
introducing a model benchmark, new product capability or a prerequisite on
umbrella packaging. Any disputed application requirement is resolved against its
owning product contract.

## 7. Outstanding Decisions

- **Data tooling:** Assign a maintained owner for reusable migration and terminology
  utilities outside the validation harness.
- **OpenMRS publication:** Select review chapters on existing integration PRs or
  independently published replacement slices with the required policy changes.
- **Public delivery:** Decide repository visibility/organization and website hosting
  changes separately from the internal component layout.

Umbrella ownership of product pins and operations, harness independence, and the
direct component layout are defined architecture—not outstanding decisions.
