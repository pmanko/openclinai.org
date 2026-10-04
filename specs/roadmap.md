# OpenClinAI Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`

This roadmap coordinates the OpenClinAI workspace, validation harness and product
delivery. [Architecture](architecture.md) defines component responsibilities and
interfaces. Product repositories own their application requirements and implementation
direction.

## 1. Current Priorities

1. Prioritize Ross's fresh research setup and instructions through the
   [HIV OpenMRS setup roadmap](reusable-environments-roadmap.md).
   Reuse the verified HIV baseline and native tooling, then apply reproducible,
   ordered scenario additions including all seven evaluation accounts. Carry over
   useful setup code, not an old database. Deliver the verified ChartSearchAI
   preview and copyable instructions before Catalyst alignment or broader cleanup.
   Setup proof is OpenMRS booting, ChartSearchAI available on it and a sample of
   the intended HIV records. Use checked Gemma 4 12B as the default for research
   testing; smaller models such as E4B are explicit comparisons. Remove custom
   Docker ownership/storage auditing and unrelated backup/restore work. Role-context
   enhancements, broader functionality tests, evaluations and videos follow
   separately; they are not setup blockers. Leave unrelated installations alone.
   Report/demo publication and changes to someone else's running environment
   require their own approval.
2. Use the consolidated documentation and focused website patch. Application
   requirements belong to their maintained product authorities; cross-project
   integration specifications and delivery belong to this umbrella; experiment
   protocols and evidence belong to the harness. Keep our coordination material out of
   OpenMRS-owned repositories and forks; their native module docs remain unchanged.
   Retain only requirements supported by current code or explicit current direction.
   Delete obsolete sections, consolidate duplicates and preserve IDs only for
   retained requirements. Update consumers directly; do not relocate an old backlog.
   Audit repository documentation and the published website separately, review
   technical and non-technical visitor journeys, and submit concrete content/UX
   remediation for owner review. The [2 October audit](reviews/2026-10-02-documentation-audit.md)
   records findings, proposed dispositions and verification evidence; it does not
   replace the product authorities or this roadmap.
   Ownership consolidation, consumer checks and the technical/non-technical site
   audit are complete and merged. The documentation site is published through the
   umbrella's GitHub Pages workflow. The separate public landing deployment and
   broader audit proposals are not implied by that publication; this documentation
   work changes no product runtime behavior.
   Merged companions: [Catalyst #140](https://github.com/DIGI-UW/catalyst-ai/pull/140),
   [Hub #32](https://github.com/pmanko/med-agent-hub/pull/32) and
   [harness #198](https://github.com/pmanko/clinical-ai-validation-harness/pull/198).
   OpenMRS module documentation and feature PRs are unchanged. Umbrella
   [#3](https://github.com/pmanko/openclinai.org/pull/3) contains the integration
   reference, roadmap and website patch; the closeout records merged component pins.
3. Complete maintainer review and ordered merging of the ChartSearchAI split.
   Break the existing ChartSearchAI backend and frontend integration work into the
   smallest practical reviewable PRs. Extract the existing implementation, tests
   and documentation together into one linear PR stack per project, rooted
   in each project's current `main`. The published contributions now follow the
   exact order defined under Contribution Model. Extraction, recorded review fixes
   and combined functional validation are complete; maintainer review and merging
   remain.
   Carry recorded findings and their fixes with their owning PRs. The complete
   set must reproduce the integration branches' functionality while preserving
   newer upstream behavior and apply the approved frontend integration decisions
   below. Unrelated new features and replacement implementations are outside this
   task.
4. The component-ownership slice is merged:
   [harness #197](https://github.com/pmanko/clinical-ai-validation-harness/pull/197)
   and [umbrella #2](https://github.com/pmanko/openclinai.org/pull/2).
   The umbrella implementation and documentation PRs are merged, followed by the
   harness review corrections and documentation cleanup. Retain separate
   product-build and deployed-acceptance evidence; this refactor does not complete
   Ross's fresh environment handoff or authorize OpenMRS upstream merges.
5. Continue QueryStore review and [Catalyst delivery](roadmap.md#6-catalyst-delivery) through their product contracts.
   Verify product-native builds and shared environments against recorded revisions;
   record deployed acceptance separately from source verification.

The immediate environment priority is Ross's reproducible fresh setup and usable handoff.
Broader documentation proposals and the existing contribution tracks continue separately.
The completed split remains under its existing contribution rules; this priority
change does not reopen its functional acceptance or authorize upstream merges.
Environment sequence, review points and acceptance live in the linked roadmap.

## 2. Implementation Status

| Area | Current state | Remaining work |
| --- | --- | --- |
| Umbrella repository | [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org) owns product operations, component pins and website sources; PRs #2 and #3 are merged | Verify reusable environments against actual installations under the separate roadmap |
| Component checkouts | Exactly six direct components have recorded revisions; harness product gitlinks and `openmrs_chatbot` are absent; companion changes are merged | Preserve recorded versions during environment setup and updates |
| Validation harness | PRs #197 and #198 are merged; runners use configured targets and supplied/observed provenance; required fields/types are checked without treating caller claims as verified revisions | Verify actual product interfaces separately; fixture isolation is not product acceptance |
| Website | Sources and publication tooling are umbrella-owned; GitHub Pages is configured for Actions and build/deploy pass; browser inspection confirms the documentation loads | Public landing deployment and product/demo publication remain separate |
| Specifications | Product behavior, shared delivery and validation protocols have maintained owners; duplicate plans and obsolete lane instructions are removed; companion documentation is merged | Follow the maintained owners; broader content proposals retain their own review |
| Research setup | [Setup guide](../environments/README.md) and `make chartsearch-research-setup` prepare the fresh HIV baseline, ChartSearchAI and seven accounts using existing tools. Local startup, account logins and the patient-chart browser smoke passed on 3 October 2026 | PR review and Ross's fresh install. Account-context enhancements and broader evaluation remain follow-up, not setup gates. |
| Product delivery | Eight backend and five frontend extractions are published. Backend and QueryStore include upstream through 3 October; the frontend already included its latest upstream. The synced source pair passes local Maven builds and tests. Hosted checks must be refreshed for the new heads | Maintainer review and ordered merging; retain backend/frontend integration references unchanged |

The phases below cover the component layout and validation interfaces defined in
the architecture. Progress distinguishes implementation, local verification, CI,
publication and deployed acceptance.

## 3. Track B: Workspace and Validation Architecture

| Phase | Deliverable | Acceptance criteria | Status |
| --- | --- | --- | --- |
| U0 Ownership and dependencies | Map capabilities, interfaces and consumers to component owners | Each capability has an owner, defined inputs/outputs and verification criteria | Ownership consolidation and its documentation companions are merged |
| U1 Component and management ownership | Direct umbrella gitlinks and workspace-management tooling; removal of nested product gitlinks and `openmrs_chatbot` | One canonical gitlink per component; fresh umbrella checkout resolves recorded revisions; umbrella tooling manages component selection and checkouts | Implemented and merged; fresh recursive checkout and offline workspace verification are recorded |
| U2 Independent validation | Modular experiment execution, target adapters, evidence collection, evaluation and reporting | Experiments run against configured targets without Git, submodules, product source trees, product pins or an umbrella installation; offline reports consume captured artifacts only | Implemented and merged; local and hosted harness suites pass; portable reports and isolation tested with doubles; actual product acceptance remains separate |
| U3 Environment and delivery tooling | Umbrella environment, build, deployment and release orchestration; OpenClinAI website build and publication tooling | Configured workspace operations invoke product-native commands; website build/publication runs from umbrella-owned sources, configuration and workflows; build/run provenance records actual inputs | Ownership move is merged; operational tests and documentation Pages build/deploy pass. Reusable environment implementation and broader deployed acceptance follow their separate roadmap |
| U4 Documentation and interfaces | Current specs, instructions, commands, configuration, CI and website consumers aligned with ownership | Consumers resolve directly to current owners; obsolete specs, copied history and unnecessary compatibility entry points are removed | Retained requirements, consumers and cleanup are merged; documentation is published; broader public-content proposals still require their own review |
| U5 Completion | Remove remaining obsolete code, dependencies and duplicate responsibilities; verify the assembled system | Independent harness checks and umbrella integration checks pass; current requirements have one maintained owner; component and deployed acceptance are explicit | Repository split and documentation closeout are merged and verified; not a claim of Ross handoff, upstream merging or new clinical/product acceptance |

### Refactor Closeout Evidence

Recorded 2 October 2026. These revisions replace the pre-merge companion pins:

| Component | Merged changes | Recorded revision |
| --- | --- | --- |
| Validation harness | [#197](https://github.com/pmanko/clinical-ai-validation-harness/pull/197), [#198](https://github.com/pmanko/clinical-ai-validation-harness/pull/198) | `5f180650aab46e607e5f21595faa4d0dc1620d4c` |
| Med Agent Hub | [#32](https://github.com/pmanko/med-agent-hub/pull/32) | `96d0489660c161acdf28f6ace621a29654e48c49` |
| Catalyst | [#140](https://github.com/DIGI-UW/catalyst-ai/pull/140) | `94742f1af6d634f03b47b9e97f3512829ba265b1` |

The OpenMRS component pins are unchanged. All four companion PRs passed their
applicable hosted checks before merging. The final harness tree is identical to
the checked documentation PR head. Local verification: 1,136 harness tests passed,
36 skipped and 3 deselected; 97% changed-line coverage; 58 focused checks passed
on the documentation branch; Markdown consistency passed. Umbrella verification:
24 unit tests, 230 operational tests, 125 website/publication tests and 54 site
tests passed. The operational suite deselected one opt-in test. These are source,
runner and tooling checks, not new live clinical evaluation.

GitHub Pages was enabled in workflow mode without a custom-domain or DNS change.
The [documentation publication run](https://github.com/pmanko/openclinai.org/actions/runs/37078640482)
passed build, rendered-link/asset checks and deployment from `30133f3db9c574dd918349ce2822fec54abba06a`.
The [published documentation](https://pmanko.github.io/openclinai.org/) and its
architecture page were inspected in the browser. Subsequent main updates publish
through the same workflow. This is not a claim that the separate `openclinai.org`
landing deployment or a product environment was updated.

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
| `specs/catalyst-program-roadmap.md` | Evaluation methodology and test protocols | Current delivery priorities belong to the umbrella; application behavior belongs to Catalyst/OpenELIS |
| Four-pathway reporting coordination | Experiments and dated evidence remain in the harness | [Catalyst delivery](roadmap.md#6-catalyst-delivery) now owns order and cross-project acceptance; the competing harness roadmap is removed and FP product requirements link directly to Catalyst |
| `specs/artifacts/planning/openmrs-dual-provider-*` | Conformance experiments and their evidence | Our integration requirements/reference, joint delivery and release coordination belong to this umbrella; existing native OpenMRS API documentation stays unchanged |
| Program lanes/status | Validation-specific results and dated evidence | Current coordination belongs to this roadmap; obsolete lane hierarchy and competing plans are removed; dated evidence links use immutable source versions |
| Website sources and tests | Experiment artifacts and report generation | `landing/`, `site/`, public catalogs and `tests/website/` are implemented in this repository |
| Website/report publication | Validation output artifacts supplied for publication | Umbrella `scripts/`, `.github/workflows/pages.yml` and `compose/website/` own static publication; product deployment is separate |

Each requirement retains its identifier under one maintained owner. Update SpecKit
pointers, instructions, links, imports, navigation, generated catalogs and tests to
reference that owner. Remove obsolete specification content and its references.

## 5. Track A: OpenMRS contribution delivery

### Contribution Model

The extraction is complete. Preserve its code, tests, documentation and review
history while maintainers review and merge the existing contributions. Do not
reopen decomposition or add new features as prerequisites.

Use one linear stack per project in this exact review and merge order:

- **Backend:** `main → #583 → #584 → #585 → #586 → #587 → #588 → #589 → #590`
- **Frontend:** `main → #55 → #56 → #57 → #58 → #59`

The first PR targets the destination project's current `main`. Every subsequent
PR targets the immediately preceding PR's branch and contains that predecessor's
current head, so its diff shows only its own contribution. Do not use separate
prerequisite assembly branches or branching dependency graphs. Keep the existing
PR numbers, scopes, review discussions and confirmed fixes while restacking.
Do not wait for upstream merges to prepare, test or publish the rest of the stack.

Manage both stacks with the installed `github/gh-stack` extension (`gh stack`).
Adopt the existing branches in bottom-to-top order with `gh stack init --base`,
using a verified trunk at the destination project's `main`; inspect the result
with `gh stack view`. Use `gh stack rebase` for cascading rebases and
`gh stack submit` to update existing PR heads and bases, followed by
`gh stack sync` for subsequent synchronization. GitHub currently rejects native
Stack objects for these fork PRs; retain local `gh stack` tracking and the actual
linear PR bases rather than replacing PRs to obtain that object. Inspect the
installed command help and verify fork/upstream remote selection and existing-PR matching before
any remote update. Preserve current draft states; do not use `--open` until the
readiness requirements pass. Verify both the local stack and actual GitHub bases
after publication. Do not substitute manually maintained assembly branches or
create replacement PRs when adopting the existing contributions.

Keep the original `harness-integration` branches unchanged as references.
Maintain newer upstream behavior and confirmed fixes. Each PR must remain
understandable and pass its applicable checks against its declared base. After a
predecessor merges, rebase and retarget dependents in order with `gh stack`.
Preserve PR numbers, discussions and changes. Existing integration PR closure is
a separate decision, not implied by the split.

The completed stack received combined functional validation once. If a relevant
change or failure requires another check, rerun the affected existing checks and
record revisions/results. Permanent tests cover lasting behavior, not PR branches,
bases, numbers or transient publication state. Local progress and exact-source
builds must not depend on upstream merging or publishing first.

### Extraction register

| Existing work | Published PR | Immediate base | Current head |
| --- | --- | --- | --- |
| B1 shared provider contract | [Backend #583](https://github.com/openmrs/openmrs-module-chartsearchai/pull/583) | main | `9dbf83de` |
| B4 exact token counting | [Backend #584](https://github.com/openmrs/openmrs-module-chartsearchai/pull/584) | #583 | `9da939f8` |
| B3 safety-check execution status | [Backend #585](https://github.com/openmrs/openmrs-module-chartsearchai/pull/585) | #584 | `a9a68d3a` |
| B5 conversation persistence | [Backend #586](https://github.com/openmrs/openmrs-module-chartsearchai/pull/586) | #585 | `13380038` |
| B4 QueryStore context and budgets | [Backend #587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587) | #586 | `50a36f0f` |
| B3 bundled inference and cancellation | [Backend #588](https://github.com/openmrs/openmrs-module-chartsearchai/pull/588) | #587 | `2b11d37d` |
| B2 Hub discovery and transport | [Backend #589](https://github.com/openmrs/openmrs-module-chartsearchai/pull/589) | #588 | `b84bcfb3` |
| B5 conversation endpoints and history | [Backend #590](https://github.com/openmrs/openmrs-module-chartsearchai/pull/590) | #589 | `d638318c` |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55) | main | `fdf262ce` |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56) | #55 | `f6f5cc24` |
| F3 Markdown, tables and citations | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57) | #56 | `39b5217f` |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58) | #57 | `150c236a` |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59) | #58 | `e60cea9c` |

### Current execution: review-ready stacks

Recorded 3 October: the existing backend stack is rebased onto upstream
`315d10db`, preserving our provider work and upstream's citation-aware safety
checks. QueryStore includes upstream `e12a1de2` at `286993cc`, including its
calendar-date birthdate fix. Frontend `e60cea9c` already contains upstream
`d0bf8b5b` and is unchanged. Backend paired-build CI now installs this same
QueryStore revision.

Local `mvn -q -B clean install` passed for QueryStore (587 tests, two skips),
followed by `mvn -q -B clean package` for the assembled backend (3,277 tests,
59 skips); both had zero failures or errors. The prior macOS socket failure did
not reproduce. The fork heads and destination comparison branches are synced;
each dependent PR's base commit matches its predecessor's current head. QueryStore
and the first backend PR have successful hosted checks. Fresh checks for the
dependent backend PRs remain outstanding after GitHub skipped scheduling while
their old comparison branches conflicted. Local success does not stand in for
those checks or maintainer approval. The split's earlier
functional evidence remains in the [acceptance checkpoint](https://github.com/pmanko/openclinai.org/blob/6e048c2ac3d45987922270e6f2e59e5ff444d239/specs/roadmap.md#current-execution-review-ready-stacks).

### QueryStore review (M1 / Q0)

Q0 resolves [QueryStore review #68](https://github.com/openmrs/openmrs-module-querystore/pull/68),
covering preprocessing documentation, dispatcher link handling, explicit chart-read
construction and parameter/resource-type validation. The
[QueryStore API contract](https://github.com/pmanko/openmrs-module-querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/rest-api.md)
and product review own the detailed behavior and any required contract updates.

Delivery requires exact-source reactor and MySQL integration evidence, applicable
HTTP-path verification and evidence-linked review dispositions. Skipped tests and
additional Elasticsearch checks are recorded separately.

### Release and owner signoffs (M5)

The completed split is source/review readiness, not a deployed release or clinical
acceptance. Signoff 1 approved the original baseline procedure. Signoff 2 accepts
the dual-provider product and authorizes controlled comparison; Signoff 3 accepts
release, companion merges, curated publication and PR cleanup. Signoffs 2 and 3
remain open. Reconcile their existing evidence against affected current revisions;
do not rerun unaffected checks because documentation moved.

Our [integration requirements and interface reference](../docs/openmrs-provider-interface.md)
belong to this umbrella. Native product behavior remains documented by [ChartSearchAI][backend], [the frontend][frontend],
[QueryStore][querystore] and [Hub][hub]. The [harness protocol][conformance] owns
fixtures and experiment evidence. Equivalent approved medication content, CIEL
mappings, exposure resolution and CDS Hooks remain a separate clinical-review
track; a shared safety-status interface does not prove equivalent clinical coverage.

### Release acceptance

IDs below retain the namespace `OPENMRS-DUAL-PROVIDER-PARITY-2026-07-20`.
This table routes acceptance to its owner; it is not another application spec.
Historical G01/G02 roadmap-hash and branch-backup procedures are not standing
checks. Workspace source consistency remains governed by the umbrella architecture.

| ID | Acceptance evidence and owner |
| --- | --- |
| G03 | Harness fixture families are consumed by actual owner tests, with stable case IDs and passing relevant behavior checks. |
| G04 | Backend: bundled answers with Hub absent; Hub answers without bundled model files; no silent provider substitution. |
| G05 | Backend/frontend: truthful availability, conditional picker, explicit selection and a fresh conversation on provider switch. |
| G06 | Backend: preserve supported local/remote engines, modes, streaming, grounding, safety, caching and warmup; report unexercised runtime variants separately. |
| G07 | QueryStore: authorized full/ranked service behavior and correct dates/version metadata across resource fixtures. |
| G08 | QueryStore/Hub: chart changes alter snapshots, conditional reuse works and mixed/incomplete acquisitions are rejected. |
| G09 | Hub: startup and inline/alternate sources work without QueryStore. |
| G10 | QueryStore owns selection invariants; engines preserve protected tiers, stable identity and trace reasons. Harness parity evidence measures actual selected records. |
| G11 | Engines: budgets are ceilings, with explicit protected-context and full-chart overflow rather than silent truncation. |
| G12 | Hub: cache isolation, revalidation and no stale-on-error behavior; backend retains its own supported cache contract. |
| G13 | Deferred Hub full-chart prefix reuse and measured backend timing. The 24 July decision makes this optional for Signoff 2 while query-scoped is the operating default. Activate only when that deployment need is selected. |
| G14 | Providers: every Checked answer has deterministic temporal/substance evidence; shared fixture expectations agree across adapters. |
| G15 | Providers: changed answers are checked again, current citations resolve deterministically and grounding evaluates final text; no prior-turn citation leakage. |
| G16 | Providers/frontend: honest checked/limited/unavailable status and visible coverage/provenance; unreviewed Hub seed rules cannot look clinically approved. |
| G17 | Backend/frontend: shared lifecycle, complete answer/review/evidence/warning/optional-stage state and faithful reload. |
| G18 | Backend/providers/frontend: disconnect and preemption settle one assistant turn, release supported downstream work and retain inspectable output. |
| G19 | Browser/demo: model errors remain visible; no false Checked labels, hidden rejected output, broken evidence or silent downgrade. |
| G20 | Owners review current README, instructions, specifications, examples and contribution descriptions for coherent responsibility and behavior. Prose-token tests are not this review. |
| G21 | Relevant product checks, CI, real-interface smoke and independent review have no unresolved blocker. Record source and deployment identity; temporary PR arrangements are evidence, not permanent tests. |
| G22 | Harness run evidence identifies supplied/observed provider, mode, snapshot, selected records, gate results, cache state, model/prompt and stage timings; missing provenance stays explicit. |

Use existing owner tests and assembled acceptance tooling. Static file presence,
regex matches or fixture copies alone do not prove runtime behavior. Live claims
need artifacts supporting the asserted values and their actual configuration.
Hash-bound evidence verifies those values, not a self-reported `passed` field.
A failed or skipped required check remains incomplete; an approved deferral is
identified separately. The one-time split acceptance is already recorded in the
roadmap and is not replaced by recurring branch-state tests.

### Controlled comparison after product acceptance

Hold model, prompt, sampling, chart, question and reference date fixed while
varying a declared provider, context mode, checking stage or cache condition.
Design and review the matrix before collection. Run deterministic audits before
judging, preserve separate judgments, and report per-cell quality and latency
without requiring identical answers or one aggregate winner. The harness collects
and reports; the umbrella publishes reviewed artifacts. Product setup and release
remain outside experiment execution.


## 6. Catalyst delivery

Catalyst owns application behavior in its [specification][product], [Dashboard
Builder design][binding] and [reporting integration design][design]. The harness
owns the comparison protocol and static reference/reader evidence. The umbrella
owns shared environments, rollout and publication; use the [operations guide](../docs/catalyst-demo-operations.md).

The current delivery covers four complementary journeys:

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
not a backlog to replay. Remaining delivery is acceptance of the complete local
and server journeys, publication verification and owner review. Native OpenELIS
reporting retains its own specification and review process. Shared production
identity/access is a separate milestone.

The retained task IDs route to their existing owners:

| ID | Maintained owner and deliverable |
| --- | --- |
| FP-001 | This roadmap: reconcile cross-project scope, requirement ownership and consumers; remove competing sequences without losing unique requirements. Local consolidation is verified; owner review/publication remain. |
| FP-002 | [Catalyst integration design][design]: approved CSV/import and PostgreSQL source interactions, recovery, retained drafts and visual review. |
| FP-003 | This roadmap, with [native reporting owner][native]: real saved-report rerun and CSV → Superset table/summary chart; inspect repeated results, dates and values, and begin same-instance FHIR coverage review. |
| FP-004 | [Catalyst PostgreSQL source][postgres]: ordinary connection, complete readable schema, exact execution, types/bounds and editor; retain Spark behavior. |
| FP-005 | [Catalyst publication/import][publication]: actual backing source and dialect, immutable saved versions, deterministic bundles, retry and receipts. |
| FP-006 | [Catalyst imported Dataset][imports]: file review, immutable durable imports, failures/retry, retained artifacts and origin-specific provenance. |
| FP-007 | [Catalyst Widget][widgets]: shared reviewed grouping/aggregation and meaningful raw-row charts; immutable versions and publication. |
| FP-008 | This roadmap, with native FHIR and pipeline owners: actual reporting-instance FHIR output reaches Spark, Catalyst and Superset with record provenance and honest coverage/freshness. |
| FP-009 | This roadmap: four complete local journeys, rendered-value checks, retained state and desktop/narrow light/dark review against approved designs. Record findings and owner feedback. |
| FP-010 | This roadmap: compatible reviewed deployment, four server journeys, verified published videos/page and explicit owner acceptance. |

Verify source identity and record meaning through actual queries/imports, saved
Dataset/Widget/Dashboard state and rendered Superset values. All four paths use
one OpenELIS source per environment; the FHIR path uses its actual output and
states coverage/freshness limitations. Counts alone do not prove correctness.
The separate OpenMRS/OpenELIS reference deployment needs both sources' complete
journeys. Product contracts own detailed behavior and failure cases; this roadmap
does not copy their checklists.

One real ingestion-to-render proof establishes a source when integrated. Reuse
retained data and rerun affected checks for relevant changes/failures. Final
release uses compatible reviewed revisions; development can proceed before
upstream merges. Preserve existing data, configuration and unrelated deployments.

Public demonstrations should make each starting point, workflow, actual outcome
and limitations easy to understand. Use readable recordings of real interactions,
identify the recording environment and actual model roles, and verify final media
and links before publication. Local video proof, server checks, publication and
owner acceptance remain separate facts. Detailed earlier recording scripts and
measurements remain in [dated evidence][catalyst-history], not current product specs.

After current acceptance, the product's implementation direction is responsiveness
and session navigation, then A (multi-artifact design/shared controls), B
(Metabase) and C (Evidence). Model comparison and broader conversation work remain
separately scheduled. Designs for follow-ons are reviewed when those efforts start.

## 7. Outstanding decisions

- **Documentation/publication:** the focused patch and documentation companions
  are merged, and the documentation site is published. Broader audit proposals,
  public-navigation changes and the separate landing deployment retain owner review.
- **Catalyst source discovery:** review current-data versus snapshot-history
  presentation at the FHIR Data Pipes source boundary. Preserve saved SQL and
  snapshots; do not add a FHIR-specific filter to Catalyst.
- **OpenMRS caches:** preserve existing bundled caching. The old harness plan's
  blanket cache prohibition conflicts with bundled preservation; Hub restrictions
  remain Hub-owned. A broader product-policy change requires explicit review.
- **Data tooling:** assign a maintained owner for reusable migration/terminology
  utilities outside the validation runner.
- **Public hosting:** decide repository organization/visibility or hosting changes
  separately from this documentation cleanup.

[backend]: https://github.com/pmanko/openmrs-module-chartsearchai/blob/d638318cdf0c1156144a8538108de8e65771f630/README.md#provider-integration-contract
[frontend]: https://github.com/pmanko/openmrs-esm-chartsearchai/blob/e60cea9cf5be41410c2401fe3261cdb712d1b0ee/README.md
[querystore]: https://github.com/pmanko/openmrs-module-querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/rest-api.md
[hub]: https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/README.md
[conformance]: https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md
[product]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md
[binding]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/dashboard-builder-mvp-design.md
[design]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specs/openelis-reporting-integration/spec.md
[postgres]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#postgresql-source
[publication]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#publication-and-import
[imports]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#imported-dataset
[widgets]: https://github.com/DIGI-UW/catalyst-ai/blob/94742f1af6d634f03b47b9e97f3512829ba265b1/docs/specification.md#widget
[native]: https://github.com/DIGI-UW/OpenELIS-Global-2/blob/codex/reporting-ui/specs/479-reporting-mvp/plan.md
[catalyst-history]: reviews/2026-10-02-documentation-audit.md#evidence-and-coverage
