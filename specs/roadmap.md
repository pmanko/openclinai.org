# OpenClinAI Refactor and PR Delivery Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`
**Revision:** 6, 2026-09-30
**Status:** Private GitHub umbrella established with an isolated recursive component checkout; first spec-cleanup slice prepared; runtime refactor and product publication remain pending.
**Goal:** Make the existing QueryStore, ChartSearchAI and ESM contributions
reviewable while separating umbrella coordination from validation and product implementation,
without losing tested behavior, upstream changes, provenance or product ownership.

**Coordination home:** `openclinai.org/specs/roadmap.md`. This document owns
umbrella direction, current priorities, cross-project decisions and refactor
sequencing. The owner requested that coordination move out of the validation
harness so each component can be refactored under its own responsibilities.
Product requirements remain in their owning repositories.

### Current Focus

1. Finish umbrella bootstrap checks/publication and prepare matching
   `spec/005-current-contract-cleanup` branches in the umbrella and its isolated
   harness checkout. The first implementation slice is Feature 005 and its direct
   consumers, not a runtime extraction or wholesale status-artifact move.
2. Resolve the concrete canvas direction question in the
   [cleanup inventory](spec-cleanup-inventory.md), reconcile current consumers,
   then delete obsolete spec content. Full U0 completion is not a prerequisite
   for this documentation slice. Preserve the independent dirty sibling checkout.
3. Continue Track A's PR-boundary review and Track B's U0 dependency map separately.
   Establish fresh component baselines before runtime changes or product
   publication. Neither audit is complete; keep QueryStore remediation and
   Catalyst delivery independent of umbrella packaging.

### Document Roles

| Document | Role | Update rule |
| --- | --- | --- |
| This roadmap | Single grounding document for umbrella priorities, decisions and phase sequence | Maintain current focus and phase evidence here |
| [Architecture](architecture.md) | Supporting ownership/design rationale and possible target structure | Amend design when decisions change; no duplicate task/status register |
| [First-slice inventory](spec-cleanup-inventory.md) | Current cleanup findings, consumers and unresolved direction question | Reconcile or remove findings as implementation resolves them; no copied old-spec bodies |
| Component specifications/task registers linked below | Product behavior and implementation/release acceptance | Update the owning repository; do not restate their full plans here |
| Harness `artifacts/review-2026-09-30/` | Ignored raw inspection/backups and blocked-test evidence | Not a roadmap or proof of a new test pass |

The umbrella's isolated checkout is `targets/validation-harness`, pinned to
published harness main `a27d7e51b7268653420e8f91306c9aaa4ab5a8ee`. Its six nested
product gitlinks are preserved exactly; no local-only product commits or dirty
sibling files were imported. Cross-repository links use the recorded components'
GitHub commit permalinks, validated locally against Git objects. The uncommitted
sibling sitrep remains local evidence, not a published contract or broken link.

Track A's candidate/source findings below still concern the independent sibling
integration work, not a runtime acceptance of this clean checkout. Product tests
have not been rerun by umbrella bootstrap. Public website source/publication
remain in the harness's `landing/` and `site/` flows; nothing was deployed.

### Workspace Bootstrap and First Slice

| Field | Current state |
| --- | --- |
| Repository | `https://github.com/pmanko/openclinai.org`, private; default branch `main` |
| Implementation checkout | `targets/validation-harness`, isolated from the dirty sibling; existing nested product paths preserved |
| Revision authority | Umbrella harness gitlink and harness product gitlinks; no duplicate revision catalog |
| Local umbrella verification | 16 standard-library unit tests and offline workspace link/pin/cleanliness checks passed; component/runtime checks not run |
| Hosted verification | Workspace workflow configured; hosted result must be recorded after push |
| Publication | GitHub repository created; bootstrap commit/push is the remaining setup step |
| First branch pair | `spec/005-current-contract-cleanup` in umbrella and harness, created after bootstrap publication |
| First slice | Reconcile Feature 005's direct canvas/status/catalog consumers and delete obsolete spec content; no runtime/product-pin changes |
| Blocking direction question | Remove canvas gateway/MCP work as obsolete, or identify an explicitly approved current requirement/owner; do not infer direction from an old feature card |

Component instructions remain authoritative. Publish reviewed component commits in
that repository before updating the umbrella gitlink; a local branch alone does
not change the canonical pin. Product publication/PR replacement, website migration
and deployment are not authorized by bootstrap. Broader U0 still needs its accepted
capability/dependency map before runtime U1 work.

### Incorporated Tracks

| Track | Scope and sequence owner | Current state |
| --- | --- | --- |
| A: OpenMRS PR delivery | M0-M5 and Q/B/F slices in sections 3-9 | Planning/source review; fresh verification blocked; extraction/publication decisions pending |
| B: OpenClinAI umbrella refactor | U0-U5 in section 10 | Private GitHub workspace and isolated recursive checkout established; first doc slice prepared; full dependency audit and runtime implementation pending |
| Existing Catalyst delivery | Existing four-pathway roadmap and Feature 008 register, linked below | Delivery scope/order unchanged; mixed coordination/validation documents await controlled split |

On 30 September 2026 the owner first incorporated the umbrella refactor track,
then requested a separate `openclinai.org` project and actual transfer of umbrella
coordination. The legacy roadmap ID remains for history; this is now the only
maintained copy. [Architecture](architecture.md) retains supporting detail.
The owner has authorized publication of the umbrella to `pmanko/openclinai.org`
(private initially). This does not approve product changes, replacement upstream
PRs, product publication, domain changes or a harness repository rename.

## 1. Authority and Non-Negotiable Boundaries

Read the relevant component authorities before changing its behavior; this
coordination document does not supersede their constitution or product contracts:

1. [Constitution](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/.specify/memory/constitution.md).
2. [Dual-provider roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap.md), its
   [status and approved amendments](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap-status.md),
   [upstream inventory](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-upstream-inventory.md) and
   [conformance contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md).
3. QueryStore's [ADR](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/adr.md) for retrieval,
   projection, dates, context selection and its REST API.
4. Applicable target instructions and their production-path tests.

### Validation-Only Harness Boundary and Spec Disposition

A harness specification defines how a system is exercised, measured and reviewed,
and which evidence supports the result. Product specifications define what the
system must do; umbrella planning defines cross-project scope and delivery order.
Validation tests cite product contracts rather than becoming their second owner.

**Spec maintenance rule:** Maintained specs describe current state or current
implementation direction, clearly distinguishing implemented behavior from planned
work. Replace or delete obsolete requirements, plans and status claims. Do not keep
superseded banners, historical spec copies, old-plan appendices or redirect stubs.
Git history owns past specifications. Move still-current requirements to exactly
one maintained owner and update references directly; delete a source document when
it has no remaining current responsibility. Run evidence is distinct from spec
history and must not be rewritten to imply fresh verification.

The table below is an initial responsibility allocation from source inspection,
not a claim that the legacy files have already moved. Source paths are relative
to `clinical-ai-validation-harness`. Split mixed documents by their requirements,
not by their current folder or feature number.

| Existing material | Validation-harness scope to retain | Destination for other responsibilities |
| --- | --- | --- |
| `specs/006-validation-harness-mvp/` | Scenarios, execution adapters, frozen run artifacts, deterministic checks, evaluation/human review and report contracts | Reconcile its historical transport wording against current product contracts; it does not own provider behavior |
| `specs/artifacts/planning/metadata-schema.md`, evaluation methodology, evidence/review/PCCP records | Validation provenance, record-level evidence, methodology and review governance, preserving approved semantics and historical limitations | General program scheduling or live product guardrail implementation belongs to the umbrella/product owner |
| `specs/001-harness-control-plane-foundation/` | Validation-target readiness, endpoint/fixture identity, run preflight and evidence/override provenance | General component catalog, checkout/release policy and shared development/demo/deployment orchestration belong to umbrella tooling; split the mixed spec |
| `specs/002-openmrs-demo-data-2-8-remap/` | Reproducible validation corpus, reviewed mappings/fixtures, fixture preparation, clinical-meaning checks and provenance; retain completed-run history | General-purpose data migration/terminology utilities need an explicit data-tooling owner; shared demo/deployment operation belongs outside the validation component |
| `specs/004-real-adapter-entrypoints/` | Still-current adapter/test protocols, reconciled against current APIs and maintained validation specs | Consolidate current product requirements and coordination into their owners; delete obsolete PoC, rollout and status text. Remove source files once no current responsibility remains |
| `specs/005-med-agent-hub-bridge/`, `specs/007-llm-config-overrides/` | Any still-current validation requirements missing from maintained validation specs | Reconcile against current product contracts, transfer only missing current requirements, then delete obsolete plans and empty source documents; no banners or archives |
| `specs/008-catalyst-query-workbench/` | Test scenarios, integration-validation protocols, evidence capture and reporting for the Catalyst path | Catalyst product behavior/design belongs in Catalyst; cross-project assembly, release sequence, implementation coordination and delivery status belong in the umbrella. The current spec/plan/tasks mix these and must be split |
| `specs/catalyst-program-roadmap.md` | Evaluation/comparison methodology, reader/evidence protocol and its existing constraints | Product phases, broader conversation scope and delivery-priority decisions belong to Catalyst/umbrella; preserve policy while separating ownership |
| `specs/openelis-reporting-catalyst-integration.md` | Referenced real-path test protocols/results, not the entire delivery roadmap | Cross-project pathway order, integration delivery and owner checkpoints belong in the umbrella; native reporting implementation stays in OpenELIS |
| `specs/artifacts/planning/openmrs-dual-provider-*` | Validation drivers, conformance test evidence and consumption of the agreed contracts | Joint provider-contract coordination, upstream inventory, PR/merge sequencing and signoff status belong in the umbrella; concrete API behavior stays product-owned |
| `specs/roadmap.canvas.tsx`, `specs/artifacts/lanes/`, `specs/artifacts/project-status/` | Harness-specific validation progress only | Program-wide views, lane coordination and status belong in the umbrella; migrate their renderers/imports together rather than copying another maintained register |
| Public website/navigation plans and general demo/release instructions | Validation report generation and evidence-specific publication contracts | Umbrella website, shared public navigation and general deployment ownership move with their source/build/publication consumers |

A validation-specific test environment or deterministic fixture loader can remain
in the harness. Operating the shared demonstration/production environment or
owning product feature design is a different responsibility. Retrieval-quality
instrumentation already owned by QueryStore remains with QueryStore; the harness
may invoke it and capture evidence without reimplementing retrieval policy.

**Migration gate:** Before each cleanup/move/split, classify content as current
state, current implementation direction, obsolete, or unresolved. Map current
requirements to their owning destinations and preserve their IDs and relevant
evidence references. Resolve uncertainty against current contracts or an explicit
owner decision; do not silently discard a possibly current requirement. Delete
obsolete spec content, relying on Git history rather than retaining another copy.
Update instructions, SpecKit pointers, links, code/test imports and site consumers
together so they resolve directly to the maintained owner. Confirm removed content
is recoverable in Git before deletion; uncommitted unique content needs an explicit
disposition first. Legacy locations below are transitional, not permanent ownership
endorsements. No scoring, sampling or clinical policy changes are part of this work.

**First cleanup slice:** [Spec cleanup inventory](spec-cleanup-inventory.md) maps
Feature 005's direct consumers and current contract coverage at the clean pinned
source. Canvas gateway/MCP direction remains unresolved. Broader status-artifact
mapping and 004/007 reconciliation remain follow-ups. No harness content has been
moved, reconciled or deleted, and no migration acceptance is claimed.

Preserve bundled inference as the fresh-install default, configured hub inference
as a separate provider, explicit provider choice and no silent fallback. QueryStore
owns retrieval and shared slice selection; ChartSearchAI remains its consumer.
Hub must remain usable without QueryStore. Clinical evidence, temporal checks,
safety disclosure, original/rejected output, cancellation and reload survival
must not disappear during extraction.

Catalyst delivery continues against its current
[four-pathway roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/openelis-reporting-catalyst-integration.md)
and [Feature 008 register](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/008-catalyst-query-workbench/tasks.md)
until their mixed ownership is split as specified above. Moving coordination must
preserve existing delivery scope/order and must not add a benchmark or model change.

## 2. Publication Decision Before Extraction

The approved 2026-08-05 harness policy publishes the tested fork
`pmanko:harness-integration` head directly and pins that exact remote commit.
Private extraction branches are permitted; separate upstream publication heads
are not presently authorized. The existing verifier enforces this distinction.

Keep OpenMRS QueryStore #68, ChartSearchAI #157 and ESM #23 open during planning.
Do not declare #157/#23 abandoned or assume that one large replacement stack
will automatically satisfy the existing publication gates.

**Recommended transition, pending approval:** preserve immutable integration
backup refs and the working source pair; prepare ordered extraction branches
from recorded current upstream bases; publish one independently buildable slice
at a time. Amend the publication policy and matching verifiers/tests in a
separate reviewed harness change before publishing those heads. Record the
replacement PR links and accounted-for residual before closing any original PR.
No force-push, reset, rebase of the preserved integration line or cleanup deletion
is part of this roadmap.

If this transition is not approved, use the same slice boundaries as review
chapters on the existing integration PRs instead. That improves reviewability
without silently changing the branch policy.

## 3. Track A: OpenMRS Milestones and Exit Criteria

| ID | Work and exit criteria | Current state |
| --- | --- | --- |
| M0 | Record exact checkout/base/remote SHAs, dirty-file ownership, immutable backup plan and verification commands. Unresolved publication/environment choices are explicit. | Local inventory recorded; fresh checks blocked; remote refresh limited. |
| M1 | Revalidate QueryStore remediation, publish the approved integration head, match review threads to code/tests, and obtain upstream disposition. | `7a7cccb` clean locally; unpushed in the inspected remote; no fresh test pass. |
| M2 | Approve publication transition; account for every source delta in a slice manifest; prove compilation dependencies before cutting PRs. | Proposal only; no extraction performed. |
| M3 | Backend slices pass their narrow regression cycles, exact-head reactor/CI checks and applicable real-path acceptance. | Not started. |
| M4 | ESM slices preserve the existing shell and pass lifecycle, provider and evidence/browser acceptance against the tested backend. | Not started. |
| M5 | Reconcile preserved integration behavior with merged slices, prove the exact assembled release, and obtain owner signoffs before PR cleanup. | Open. |

M1 review and local paired-source validation do not require an upstream merge.
The existing paired CI supports pre-merge review using an immutable public
QueryStore checkout. Actual merge/deploy order remains QueryStore, ChartSearchAI,
then ESM. Do not confuse a local Maven install, a hosted paired build and
publication of the upstream QueryStore SNAPSHOT.

## 4. QueryStore Remediation Slice Q0

**Source:** local `7a7cccb1a0001bc390cc49c845ee051778085062`, parent `8b79db9`.
**Scope:** preprocessing comment, runtime REST prefix, explicit
`PatientChartRead` constructor arguments, context-only parameter guards and
resource-type syntax validation. Keep this on existing upstream PR #68.

Acceptance:

- Link URIs use the runtime REST prefix and preserve query/patient/context
  parameters and pagination. Verify the configured webapp context, not only the
  string `/openmrs` in an isolated helper.
- `types`, `temporal` and `interpret` outside `mode=context` return 400;
  invalid type syntax returns 400 and valid contributed names remain supported.
  Syntax validation is not an allowlist of installed types.
- No two-argument constructor or accidental completeness default remains.
  Caps, missing indexes, failed reads, failed cold projection and incomplete
  bootstrap remain explicitly disclosed.
- The reactor and MySQL integration checks pass at the exact reviewed source.
  Record skipped suites separately. Elasticsearch fault tests are not a claim
  of a fresh live Elasticsearch integration pass.
- For HTTP acceptance, exercise dispatcher binding/security and follow a returned
  link in the real configured OpenMRS deployment. Direct controller tests alone
  do not establish deployed routing.
- Every review thread has an evidence-linked reply or an explicit unresolved
  disposition. An outdated marker is not permission to auto-resolve a thread.

## 5. Proposed Backend Slices

These are extraction boundaries, not implementation assignments. At M2 produce
a path/hunk manifest: each delta is assigned once, its prerequisite is explicit,
and existing upstream behavior is retained. Shared-file hunks must be separated
deliberately; cherry-picking whole commits without that inventory is insufficient.

**Proposed order:** B1 -> B4 -> B3 -> B2 -> B5. B4 follows QueryStore upstream
merge/artifact availability for normal upstream builds; paired local review can
precede it. Keep an inseparable compilation unit together and return a boundary
change for review rather than hiding it behind stubs or broken intermediate PRs.

| Slice | Scope and prerequisite | Behavioral acceptance and existing regression anchors |
| --- | --- | --- |
| B1 Contract | `api/provider` contract types: `ClinicalAnswerProvider`, descriptors, modes/capabilities, turn events/request/result, `AnswerEnvelope`, lifecycle/cancellation types; include required `PriorClinicalTurn` value type. Do not activate a new public route or move the existing `ChartAnswer`/clinical safety model into a new framework. | Required event ordering, one terminal outcome, immutable envelope and unknown payload preservation are asserted. Use `AnswerEnvelopeTest`, `TurnLifecycleConformanceTest`, `TurnCancellationTest` and the versioned conformance fixture. Compile without concrete provider adapters. |
| B4 Context consumer | `QueryStoreChartBuilder`, budget/token accounting and associated caller changes. Requires B1 and the reviewed QueryStore API. Slice selection/interpretation implementations remain in QueryStore, not copied into ChartSearchAI. | Full/query-scoped reads preserve selected records, ordering, snapshot/completeness flags, mandatory evidence and explicit overflow. Run `QueryStoreChartBuilderTest`, `QueryStoreChartBuilderScopedTest`, `QueryStoreChartBuilderBudgetTest` and `CountingQueryStoreStubTest` against installed exact QueryStore source. |
| B3 Bundled preservation | `BundledClinicalAnswerProvider`, registry, router/engine seams and necessary bundled lifecycle changes. Requires B1/B4. Registry belongs here because its fresh-install default references the bundled provider. | Existing local and remote engines, modes, grounding and safety still work without Hub. No model dependency is removed merely to shrink the PR. Use `BundledClinicalAnswerProviderTest`, `ProviderRegistryConformanceTest`, engine tests and applicable existing safety/grounding tests; inspect real bundled operation with Hub absent. |
| B2 Hub adapter | `HubClinicalAnswerProvider`, HTTP stream transport, hub call/wire types and profile discovery/configuration. Requires B1/B3 in this proposed sequence. No retrieval implementation or new Hub subsystem. | Hub path works without bundled model files, preserves nested provider payloads, normalizes failures, closes transport resources, rejects post-terminal events and handles cancellation without fallback. Use `HubClinicalAnswerProviderTest`, `HttpHubStreamTransportTest`, `HubProfileServiceTest` and `TemporalGateRelayConformanceTest`; retain real configured-Hub proof separately from fixture tests. |
| B5 OpenMRS activation and persistence | Conversation services/DAO/models, Hibernate/Liquibase changes, routing activation, authorization, REST/SSE, audit/history and startup wiring. Requires B1-B4. Persistence and terminal publication remain one coherent change. | Fresh install and existing conversations retain access controls, stable identity and one final assistant row; disconnect/preemption, reload and failure paths stay truthful. Use `ConversationServicePersistenceTest`, `ConversationTurnAllocationTest`, `ProviderRestContractTest`, `ProviderStreamPersistenceTest`, `ChatHistoryEndpointTest`, `ResolveConversationTest`, `ArchitectureGuardTest` and the real relay probe. |

The clinical provider SPI is `ClinicalAnswerProvider`, not the existing engine
implementation `LlmProvider`. Backend endpoint ownership is
`ChartSearchAiRestController`; `PatientRecordEndpointTest` belongs to QueryStore.
Tests named here are present in the inspected source, not claims that the
future extracted subset already compiles or passes.

## 6. Proposed ESM Slices

Do not rebuild existing workspace scaffolding or ship empty placeholder screens.
Preserve the established Carbon/OpenMRS layout, translations and accessibility.
Use the existing API client/hook/store rather than introducing React Query.

**Proposed order:** F1 -> F2 -> F3. These three slices replace the earlier draft's
four speculative frontend slices; F3 owns its former citation-rendering scope.
Backend B5 supplies the real API contract for integration acceptance.

| Slice | Scope | Acceptance |
| --- | --- | --- |
| F1 Transport, lifecycle and durable state | `src/api`, `src/hooks/useChartSearchAi.ts`, `turn-phase.ts`, canonical fixture and `chat-session.store`. | Both providers use the same lifecycle; preliminary/final/evidence events retain their distinct meaning; terminal failures and session expiry are explicit; preemption cannot overwrite another turn; refresh retains identity and transcript. Run API, hook, store and fixture tests; then verify streaming/reload against B5. |
| F2 Provider selection | Provider picker and existing workspace configuration/wiring, including translations. | Bundled-only configuration needs no Hub profile fetch; picker appears only for multiple enabled providers; unavailable selections remain visible with a reason; switching starts a new conversation; existing conversations are not silently reassigned. Run picker/workspace tests and inspect the real browser states. |
| F3 Answer and evidence presentation | Existing response/markdown/citation/safety components and chat presentation, including translations/styles. | Final checked/limited/unavailable states, original/rejected output, validation summaries, evidence provenance and optional In-Depth survive reload. Reference-group citations do not invent a grounding verdict. Inspect keyboard/focus, error, light/dark and narrow layouts with real backend payloads; component snapshots alone cannot close acceptance. |

Keep translation/lockfile/toolchain changes with the slice that needs them.
Account for all remaining ESM hunks at M2; do not treat a residual UI or dependency
change as automatically irrelevant because it does not fit these headings.

## 7. Repeatable Validation Cycle

Each Q/B/F slice or U-phase change follows this cycle; failures return to its
responsible scope:

1. **Freeze inputs:** record source tip, exact upstream base, prerequisite SHAs,
   assigned paths/hunks and expected observable behavior. Distinguish cached
   remote refs from a newly fetched head.
2. **Prove regressions:** run the named production-path guards. For new behavior
   or a repair, retain red-before/green-after evidence without weakening tests.
3. **Implement/extract minimally:** preserve unrelated upstream deltas; do not
   create replacement retrieval, safety or model orchestration implementations.
4. **Narrow checks:** run the smallest affected tests, compiler/type/lint checks
   and applicable schema/fixture checks. Retain commands, outputs and skips.
5. **Final slice gate:** run the exact-head reactor or ESM verification set once,
   then applicable real-path acceptance. Preserve raw record/event/browser
   evidence and build/artifact provenance; mocks are labelled scaffolding.
6. **Review pause:** present the full diff, findings, environment limitations and
   behavioral evidence. Owner/maintainer acceptance, push and merge remain
   explicit actions. Do not infer them from a green check or mergeability.
7. **Revalidate after change:** any relevant source/base/dependency change
   invalidates its affected evidence. Rerun the narrow affected checks; repeat
   the final gate at the final head, not every unchanged historical suite.
8. **Assemble:** reconcile the merged slices against the preserved integration
   delta, then validate the real two-provider journey and record owner signoffs
   in the existing dual-provider status register.

### Command Entry Points

These are execution recipes, not assertions that they ran in this review.
Run from the harness root unless a target directory is shown.

```bash
make querystore-test
make querystore-test-integration
make openmrs-source-pair-test
scripts/verify-repository-lines.sh --allow-harness-branch
```

`querystore-test-integration` runs MySQL only. A separately needed live ES check
uses `scripts/test-querystore.sh elasticsearch-integration`; it must not be
silently inferred from the MySQL result. An offline local retry may append `-o`
to `scripts/test-querystore.sh unit` or `mysql-integration`; unavailable cached
dependencies/images are a blocker, not a passing or skipped acceptance gate.

For ChartSearchAI run its existing test wrapper after installing the exact
QueryStore source. For ESM run `yarn test`, `yarn lint`, `yarn typescript` and
`yarn build` in `targets/chartsearchai-esm`. Production probes/browser journeys
require a deliberately selected existing runtime and authorization; do not
restart, seed or substitute a simulation to make this review appear complete.

The current source-pair wrapper requires exact integration heads and parent
gitlinks. Do not bypass it or casually repoint the dirty working directory.
An approved extraction-publication transition must update those expectations
explicitly. Network-backed publication verification is separate:
`scripts/verify-repository-lines.sh --allow-harness-branch --check-publication-prs`.
After merge, strict `scripts/verify-repository-lines.sh` must pass before release.

### Evidence and Acceptance Record

For each Q/B/F slice or U-phase change record: repository/PR, source/base/dependency SHA, scope,
commands and exit statuses, test skips, retained log/XML paths, runtime/artifact
identity, fixture/record/event evidence, browser proof when applicable,
unresolved findings, reviewer/owner decision and next action. Keep secrets and
raw clinical evidence out of Git; durable Markdown links to private/ignored
artifacts without treating their existence as proof of a pass.

Track implementation, local checks, public CI, merge, deployment and owner
acceptance separately. Update the existing project-status sources only with
verified dated facts; do not create a competing product task register.

## 8. Immediate Continuation and Owner Decisions

1. Preserve/assign the dirty report-index changes, Hub profile edit, submodule
   mismatches and duplicate Compose file before choosing a sync/release checkout.
2. Enable the narrow verification commands or record that they remain blocked.
   Revalidate Q0 before presenting it as newly ready to publish.
3. Approve pushing QueryStore `harness-integration` and posting evidence-linked
   replies separately; keep upstream thread resolution with its review process.
4. Align the next tested QueryStore gitlink and ChartSearchAI paired-CI ref in one
   compatible reviewed change. Both named `cfced36` in the inspected harness checkout.
5. Approve or reject the publication transition in section 2 before M2 extraction.
   Review the completed hunk manifest and compilation boundaries at that pause.
6. Complete release evidence and Signoff 2/3 in the existing roadmap/status.
   No source test result alone closes these signoffs or authorizes PR deletion.
7. Begin the U0 ownership/dependency review alongside Track A's Stage A if
   authorized. Return its concrete boundaries and checks for owner review before
   U1 code changes; no packaging or rename gate may block Q0 remediation.

## 9. Roadmap Validity Review and Controlled Execution

**Status:** Proposed procedure, persisted 2026-09-30; not executed or approved
by being written down. The earlier pointer check establishes that links and
named tests exist, not that extraction boundaries are correct or buildable.

The Q/B/F extraction procedure here governs Track A. Track B uses the U0-U5 gates
in section 10 and the same evidence/review cycle in section 7; do not force its
architecture audit through an OpenMRS publication-policy gate.

### Stage A: Challenge the Roadmap Before Changing Code

- Refresh exact source/base/PR facts with authorized read-only remote access;
  otherwise label them cached. Preserve the current dirty checkout and account
  for local-only commits. Treat unrelated model/profile and report-index work
  as separate lanes, not prerequisites to review the OpenMRS decomposition.
- Trace each proposed slice to an existing product requirement, ADR or approved
  roadmap gate. Identify omissions, conflicting ownership, unapproved scope,
  hidden prerequisites and acceptance that only checks implementation details.
- Map every changed path/hunk from the recorded integration tip versus its
  recorded upstream base to Q0, B1-B5, F1-F3, or an explicitly reviewed residual.
  Record prerequisite types, callers, Spring wiring, schema changes, fixtures,
  translations and build configuration. Do not silently drop a residual.
- Challenge the proposed order: ask whether the preceding merged state still
  compiles, starts and preserves bundled behavior; whether a test relies on a
  later adapter; and whether shared-file hunks can actually be separated.
  An existing test name or attractive PR title is not evidence of independence.
- Record findings and their dispositions in this roadmap. Fix confirmed plan
  defects before requesting approval; keep hypotheses visibly unproven.

**Exit A:** Complete requirement-to-slice and source-delta mappings, explicit
compile/runtime prerequisites, no unresolved blocking plan contradiction, and
an owner decision on the publication model. Maintainer agreement on intended
PR scope is sought before replacing existing upstream PRs. B1 -> B4 -> B3 ->
B2 -> B5 remains a proposal until the dependency review supports it.

### Stage B: Establish an Executable Baseline and Prove Boundaries

- Enable only the required verification commands and determine the existing
  compatible JDK, dependency cache and test-container availability. Stop at an
  authorization/dependency blocker; do not retry denied commands through aliases
  or download/install a workaround without permission.
- Use an isolated, explicitly pinned review worktree/source set rather than
  resetting or switching the owner's dirty working directory. Retain the
  planning documents in a scoped harness documentation branch; do not stage
  unrelated report-index edits, Compose files or submodule changes with them.
- Revalidate QueryStore Q0 at its exact source and retain fresh reactor/MySQL
  logs and XML. Prove ChartSearchAI compatibility against that same installed
  QueryStore source; distinguish a local paired build from the strict pinned
  source-pair/publication gates, which need an aligned reviewed source set.
- After the publication decision, mechanically prepare the proposed intermediate
  subsets from the frozen hunk manifest in isolated scratch branches. Compile
  and test each cumulative subset before publishing any replacement PR.
  Scratch extraction is feasibility evidence, not an upstream merge or deploy.
- If a boundary requires a later slice to compile or start, move the inseparable
  change to its proper slice and return the revised plan for review. Do not add
  production stubs, disable assertions or remove existing behavior to obtain a
  green intermediate build.

**Exit B:** Fresh exact-source baseline evidence and a buildable cumulative
sequence, with relevant production-path regression guards passing. Any changed
boundary is reflected in the manifest and acceptance before implementation or
publication proceeds. Blocked/unrun checks remain explicit, not presumed passes.

### Stage C: Execute One Accepted Slice at a Time

Execute Q0 publication/review disposition, then the accepted backend sequence,
then the accepted ESM sequence. Actual merge/deploy order remains QueryStore,
ChartSearchAI, ESM; paired pre-merge review need not wait for upstream merge.

Each slice uses section 7: freeze inputs, preserve red/green evidence for new
repairs, make the minimal extraction/change, run narrow checks, review the full
diff, run the final exact-head gate and applicable real-path proof, then request
publication/merge approval. Retain blocker dispositions and revalidate affected
evidence whenever the source, base or prerequisite changes.

**Exit C:** Every accepted slice has separately recorded implementation, test,
CI, merge and applicable runtime evidence. Reconcile the assembled result with
the preserved integration baseline before requesting existing Signoff 2/3.
Original PR closure requires replacement links and accounted-for residuals;
no documentation update or green build closes that approval by itself.

### Durable Record and First Decision

Keep this procedure, slice manifest and current review dispositions in this
roadmap. The sibling's dated sitrep is local evidence, not a published spec.
Record implementation/release acceptance in the existing dual-provider status
register, not a parallel product task list. Raw logs/XML/browser evidence stay
in ignored artifact storage, linked from durable records without secrets.

The next authorized unit of work should be **Stage A plus permission/baseline
preflight**, not an immediate push or wholesale PR replacement. Approval to
review/persist the plan is separate from authorization for remote access,
branch publication, PR comments/closure and deployment.

## 10. Track B: OpenClinAI Umbrella Refactor

### Direction and Ownership

The `pmanko/openclinai.org` repository owns umbrella coordination and the scoped
submodule-based workspace. `targets/validation-harness` is an isolated checkout
of published harness main; it retains the six nested product gitlinks as their
single revision authority. Products and the harness retain their repositories
and governance. Operational tooling and website code remain in the harness
until an agreed ownership/consumer map justifies each move. Promoting products to
direct umbrella submodules requires a coordinated path migration, not duplicate
independent pins. This workspace is not a new monolithic runtime application.

Use [architecture detail](architecture.md) for the responsibility map, observed
seams, possible target structure and dependency rules. Product specifications
remain authoritative. OpenClinAI is the public brand; `openclinai.org` is the
selected local coordination project. A harness repository rename is not required.
Remote identity is `pmanko/openclinai.org`, private initially. Organization transfer
or public visibility, public website migration, import/distribution names, CLI
aliases and Hindsight routing remain follow-up decisions.

### Phase Register and Acceptance

| Phase | Planned scope | Exit gate | State |
| --- | --- | --- | --- |
| U0 Ownership/dependencies | Inventory modules, commands, imports, configuration, generated/public surfaces and source ownership. Assign workspace tooling, validation, data preparation, deployment, web and product responsibilities. Classify the component registry and shared provenance primitives. | A versioned capability-to-owner/destination map, concrete dependency boundaries, compatibility inventory and per-change validation plan are reviewed. Every in-scope capability has one owner; product requirements and original clinical/evaluation semantics are preserved. Naming choices and unresolved findings are explicit. | Initial spec allocation recorded; full ownership/dependency audit pending |
| U1 Behavior-preserving seams | Within the current layout, separate CLI dispatch/configuration and execution, evidence/rendering and lifecycle concerns. Reconcile one existing component catalog rather than add competing registries. Avoid importing product internals where public contracts suffice. | Existing deterministic production-path fixtures and serialized contract values are preserved. Offline rendering uses frozen artifacts without Docker, a model, live clinical queries or rejudging. Existing CLI commands/imports/configuration aliases still work; focused affected checks pass. | Blocked on accepted U0 boundaries and checks |
| U2 Package/dependency isolation | Make workspace, validation and data-tooling dependencies installable separately only after U1 proves their seams. Retain minimal shared checkout/identity/provenance code based on actual common use. | Workspace operations do not need SQLMesh/scoring dependencies; evidence rendering does not need data-import dependencies. Validate each intended dependency subset and compatibility entry point. No grading, sampling, model/profile or clinical-context semantics change. | Depends on U1 |
| U3 Deployment/publishing organization | Organize existing reference-stack configuration and lifecycle/publication wrappers with one owning path per capability. Do not replace the working lifecycle model or add an orchestration service. | Commands preserve ports, mounted data, exact pin/build provenance and explicit seed/reset behavior. Affected real-path journeys and existing publication/receipt checks pass without loss of retained state. Build-time and long-lived runtime paths are distinguished. | Depends on U1/U2 and accepted operational migration |
| U4 Deliberate naming migration | After explicit rename approval, update repository/display identity, remotes, Pages/base URLs, source links, CLI aliases, configuration paths and Hindsight routing together. Preserve historical provenance and useful old entry points. | Compatibility/redirect tests and publication identity checks pass; historical manifests/reports retain their original identifiers and values; workspace memory uses the intentionally selected bank. Public-domain changes need a separate explicit decision. | Local coordination name selected; remaining identity/publication decisions pending after stable U3 |
| U5 Closeout | Reconcile migrated capabilities and accepted destinations. Remove only explicitly approved obsolete compatibility code after consumers and remaining references are accounted for. | No unowned capability or unresolved blocking regression; retained old entry points have an approved disposition. Component CI, merge, deployment and owner acceptance remain separately recorded. | Depends on U1-U4 outcomes |

### Track Dependencies and Delivery Priority

- U0 is design/inventory work and may run alongside Track A's Stage A. Neither
  requires a repository rename or public replacement PR. Fresh remote facts and
  executable checks still require the appropriate access authorization.
- QueryStore Q0 and the OpenMRS source-pair repair continue independently of U1-U5.
  The umbrella refactor is not an upstream merge prerequisite or a new release
  signoff for the existing products.
- Catalyst delivery continues through its existing register during migration.
  Transfer its coordination to the umbrella and retain validation-only protocols
  in the harness without losing tasks or acceptance evidence. Do not turn this
  move into a model-accuracy optimization backlog or pause the delivery goal.
- U1/U2 changes should stay within owned umbrella modules. If a proposed change
  reaches an active product contract, classify it with that product's owner and
  its existing tests before implementation; do not hide it in a packaging PR.
- U3 must coordinate actual operational path changes with the current release
  owner. Preserve `targets/`, existing wrappers, environment variable names,
  ports and storage bindings until their migration is reviewed. Do not move a
  directory underneath a running bind mount or silently rebuild/reseed a stack.
- U4 follows behavior/dependency isolation, not the other way around. Keep
  immutable source/build/run identity and the existing fork branch policies;
  gitlinks remain canonical pins, not a new duplicate lockfile.

### Validation Cycle and Owner Pauses

Apply section 7 separately to each coherent umbrella change: freeze the affected
inputs/contracts, retain deterministic before/after evidence, make the minimal
change, run the agreed narrow checks, review the complete diff, and run its final
exact-head gate plus applicable real-path proof. Do not invent performance tests
or rewrite historical reports to validate a packaging refactor.

At U0 review, present the actual dependency graph, destinations, compatibility
risks, proposed first implementation PR and its named checks. Pause before code
changes where a boundary is unsettled. Review U1/U2 isolation evidence before
operational movement; approve the U3 operational plan before changing live paths;
approve exact naming/compatibility choices before U4. A gate is blocked until its
evidence exists; this phase table does not mark work complete.

Implementation, local checks, hosted CI, merge, deployment and acceptance are
separate status fields, just as for Track A. Preserve clinical/evaluation policy,
model settings, source credentials, retained data and historical artifacts. No
new warehouse, connector framework, event bus, identity/SSO service or universal
clinical domain model is authorized by this track.

### Durable Records and Next Step

Record U0's capability/destination map and review dispositions in this roadmap;
retain detailed ownership/design rationale in `architecture.md`.
Migrate program-wide status with its consumers when that slice is ready; retain
validation-specific status in the harness. Until then the current records are
transitional evidence, not a reason to retain umbrella ownership in the harness.
The sibling sitrep remains local evidence, not a live mutable status source or a
published dependency.

The next implementation deliverable is Feature 005 spec cleanup and direct-consumer
reconciliation after the canvas direction decision. Complete the U0 dependency map
and review a scoped U1 proposal before runtime refactoring. Umbrella publication and
branch preparation do not claim product release, deployment or U0/U1 acceptance.
