# OpenClinAI Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`

This roadmap coordinates the OpenClinAI workspace, validation harness and product
delivery. [Architecture](architecture.md) defines component responsibilities and
interfaces. Product repositories own their application requirements and detailed
implementation registers.

## 1. Current Priorities

1. Break the existing ChartSearchAI backend and frontend integration work into the
   smallest practical reviewable PRs. Extract the existing implementation, tests
   and documentation together into independent or stacked topic branches rooted
   in each project's current `main`. Finish the full split before the review-fix
   pass; record findings as they arrive and carry them with their owning PRs. The complete
   set must reproduce the integration branches' functionality while preserving
   newer upstream behavior and apply the approved frontend integration decisions
   below. Unrelated new features and replacement implementations are outside this
   task.
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

The active ChartSearchAI task is this PR split. Other priorities enter that task
only when they directly block a specific contribution.

## 2. Implementation Status

| Area | Current state | Remaining work |
| --- | --- | --- |
| Umbrella repository | [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org) has the component-ownership implementation published in PR #2, including product operations and website sources | Review and merge the assembled changes |
| Component checkouts | Fresh recursive GitHub clone resolves exactly six direct components at their recorded revisions; harness product gitlinks and `openmrs_chatbot` are absent | Review and merge the component changes |
| Validation harness | Clinical and Catalyst runners use configured targets and supplied/observed provenance; source-free wheel isolation, portable reports and the full local harness suite pass | Review the published component change and verify actual product interfaces separately |
| Website | `landing/`, `site/`, static hosting configuration, build/publication tools and workflows are umbrella-owned; local website tests and build have run | Hosted CI and explicit deployment acceptance |
| Specifications | Harness governance and validation foundations are reconciled; retained 004 criteria are in Feature 006; obsolete 004/005/007 files are removed | Consolidate mixed Feature 008, program-delivery and OpenMRS coordination specifications |
| Product delivery | Six backend and five frontend extractions are published. Applicable hosted checks pass for #583–#588 and #55–#59; lifecycle/presentation draft #59 also has passing local checks. Rendering #57, selectors #58, bundled-provider #588 and lifecycle/presentation #59 have findings recorded below; earlier stream findings are fixed and resolved | Publish the remaining Hub adapter and backend endpoints, then address collected findings and verify combined functionality; retain integration branches unchanged |

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

The deliverable is a set of reviewable PRs containing the work already implemented
on the backend and frontend `harness-integration` branches. Reuse that code and
carry its existing tests and documentation with each extracted change. Do not
reimplement a capability from its description or add unrelated new features,
redesigns or fixes as prerequisites for the split. The approved frontend
integration decisions below explicitly authorize the necessary adaptation for
toggleable streaming and unsupported model capabilities.

Create independent topic branches from the destination project's current `main`.
Build dependent changes on their prerequisite topic branches and target the
preceding branch so each PR shows only its own contribution. Do not wait for
upstream merges to prepare, test or publish the rest of the split.
Make the adjustments necessary to separate the existing changes, resolve conflicts,
fix confirmed review defects and preserve newer upstream functionality. Keep closely
dependent changes together when splitting them would require scaffolding or a
rewrite. Use existing commits where suitable or extract their relevant changes;
preserving commit history is optional, and rewriting working code is not a goal.

Use the [existing contribution catalogue](https://openclinai.org/docs/openmrs-upstream/)
as the starting inventory, checked against the integration branches and current
upstream code. Its dated review and test status is not current acceptance evidence.
Track each existing capability as already covered by upstream, assigned to a small
PR, or still awaiting extraction. Keep the corresponding tests and documentation
with the behavior rather than making a separate test or documentation project.

Keep the existing `harness-integration` branches unchanged: do not rewrite, delete
or rebase them. Preserve newer upstream code when extracting changes; a raw tree
diff against an older integration branch is not a patch to apply wholesale.

Each PR must be understandable, buildable and testable against its declared base.
Independent changes may proceed in parallel. A stack makes dependencies explicit;
ancestor changes belong in the base, not in the displayed contribution diff.
After a prerequisite merges, update and retarget its dependents without losing
their changes. Run the relevant existing checks for each extracted piece and add
focused regression coverage for confirmed defects.

Completion means that both projects' full integration functionality is accounted
for by the complete PR set and retained upstream behavior. Review every PR, address
each actionable finding, require passing applicable CI on its current revision,
and run the existing integration acceptance checks against the assembled stack
heads and exact QueryStore dependency. Explain mechanical omissions such as
integration-only build jobs; do not omit product capabilities. An unextracted
capability is unfinished work. A few green foundation PRs or a completed file
inventory do not satisfy this goal.

### Milestones

| ID | Deliverable | Acceptance |
| --- | --- | --- |
| M0 | Inventory and grouping of existing integration work | Main and integration revisions are identified; existing code, tests and documentation are mapped to upstream coverage or proposed PRs, with necessary dependencies |
| M1 | QueryStore Q0 review resolution | Exact-source tests and required integration evidence support the published contribution |
| M2 | Small independent or stacked backend/frontend PRs | Each PR extracts one coherent portion of the existing work, shows only its own changes against its declared base and passes its applicable checks; coverage and remaining extraction work are explicit |
| M3 | Backend delivery | Existing B1–B5 work is accounted for in upstream or extracted PRs, with its product checks |
| M4 | Frontend delivery | Existing F1–F3 work is accounted for in upstream or extracted PRs, with its lifecycle, provider and evidence/browser checks |
| M5 | Integrated release acceptance | Assembled product behavior and deployed evidence satisfy the existing release signoffs |

M5 is separate release work, not a prerequisite for publishing the extracted PRs.
The split does not require new test suites, acceptance infrastructure or a new demo.
Combined functional validation of the complete split is required before declaring
the decomposition complete; it is distinct from deployment and release signoff.

Execute this work in three steps: publish the complete backend/frontend split,
address the collected review findings across that set, then verify the combined
functionality. Open review findings do not block later extractions. Fix only
compilation or dependency problems needed to make an extraction coherent during
the split; defer review remediation to the second step. Do not merge or call the
work ready until findings are addressed and applicable checks and combined
functional validation pass.

Publication requires accurate source/review status and applicable verification
evidence, including outstanding findings. Declare QueryStore/backend/frontend dependencies explicitly and test
their exact source revisions together without requiring upstream publication.
Paired tests provide integration evidence but do not replace each PR's checks
against its declared base.

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

These groups describe the existing implementation to split; they are not new
implementation assignments or fixed PR sizes. Choose boundaries that make the
existing changes easy to review with the least adaptation. Combine inseparable
changes rather than adding code to force an artificial split.

| Slice | Responsibility | Integration dependency |
| --- | --- | --- |
| B1 Contract | Provider descriptors, request/result and event types, answer envelope, lifecycle and cancellation contract | No concrete provider implementation required |
| B4 Context consumer | QueryStore-backed chart context and token/budget accounting; retrieval policy remains in QueryStore | Token counting can stand alone; chart-context consumer needs the reviewed QueryStore API |
| B3 Bundled provider | Bundled inference implementation, registry and routing/engine integration | B1/B4; bundled installation remains independent of Hub |
| B2 Hub adapter | Configured Hub discovery, request/stream transport, cancellation and failure handling | B1 for the adapter; no bundled-provider prerequisite or silent fallback |
| B5 OpenMRS integration | Authorization, conversation persistence, schema changes, REST/SSE and startup wiring | Persistence uses B1; endpoint/provider wiring uses B1–B4 |
| F1 Transport and state | Client transport, lifecycle, durable session state and reload behavior | Backend contracts; B5 for real-path acceptance |
| F2 Provider selection | Explicit provider selection and configuration-aware availability | F1 and backend provider discovery |
| F3 Answer and evidence UI | Clinical output, references, original/rejected drafts, validation/safety disclosure and optional In-Depth | F1 types/state and real backend payloads; no inherent provider-picker prerequisite |

The backend contract unlocks independent Hub-adapter and conversation-persistence
work. Token counting does not need that contract; the full context consumer does
need the QueryStore additions. Endpoint wiring follows its actual providers and
persistence. Frontend transport, state, provider selection and presentation follow
their actual imports and backend interfaces, not a mandatory single sequence.
Each PR must compile and satisfy the relevant product contracts on its declared base.
Integrated acceptance covers explicit provider choice, no silent fallback,
traceable evidence, cancellation and reload survival.

### Extraction Register

The source comparison uses backend integration `2b020dd268fa526c7fa0e168a0a1a8bbc1e6761c`
and frontend integration `77f61c8a1f9afcf7eb03208caac3dd7ae8ea35a2`. The first PRs
use upstream main `d183c5bfc1820ba8fb274a11595db5eab0dd313b` and
`d0bf8b5b14ef23273e70428e8deb7457ad47b616`, respectively. Compare integration changes
from their common ancestors (`7446d9a` backend, `9668ae0` frontend), then fit those
changes to current main. Newer upstream safety and citation behavior must remain.

| Existing work | Publication or remaining extraction |
| --- | --- |
| B1 provider contracts, lifecycle validation, cancellation/preemption and prior-turn input | [Backend #583](https://github.com/openmrs/openmrs-module-chartsearchai/pull/583), `b89211ce`; full Maven verification passed locally and hosted Java 11/17/21 builds passed. No adapter or endpoint activation in this PR |
| B4 exact token counting | [Backend #584](https://github.com/openmrs/openmrs-module-chartsearchai/pull/584), `370f4c32`; full local Maven verification and hosted Java 11/17/21 and QueryStore-main builds passed. Existing counting requests adapted to upstream authentication |
| B4 chart context and budgets | [Backend #587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587), `508546e5`, stacked on #584: QueryStore context consumer, protected-evidence budgets and existing tests/fixture. Review fixed acceptance of incomplete source projections; both regression cases failed before the fix. All 110 focused checks and 285 web-module tests plus packaging pass against QueryStore `8b79db97`; full API run has only the previously reproduced upstream macOS socket-test failure (59 skips). Hosted paired-source Java 11/17/21, selftest and lint checks passed at this revision; no review threads outstanding. Ordinary artifact builds are replaced by the declared source-pair checks for this branch; combined runtime acceptance is unverified |
| B3 safety-check execution status | [Backend #585](https://github.com/openmrs/openmrs-module-chartsearchai/pull/585), `c1f43ce9`; 64 focused tests, full local Maven verification and hosted Java 11/17/21 and QueryStore-main builds passed. Carries validator status/issues and patient-context completeness while preserving upstream order-read and attribution logic |
| B3 bundled provider, cancellation and safety status on answers | [Backend draft #588](https://github.com/openmrs/openmrs-module-chartsearchai/pull/588), `389ae7a3`, on the exact #583/#585/#587 prerequisite assembly `1cf826b5`: bundled adapter, registry, router/engine cancellation, final prompt-budget preflight and `ChartAnswer` safety wiring, including module-composed answers. Preserves newer upstream prompt arguments and answer fields; existing validator/constructor fixtures are adapted without changing clinical assertions. Full API verification has 2,903 tests with zero failures/errors and 59 skips; all 285 web-module tests and packaging pass. Hosted source-pair Java 11/17/21, selftest and lint checks against QueryStore `8b79db97` passed at this revision. Review findings are recorded below; combined endpoint/frontend behavior and approved capability/toggle acceptance remain unverified |
| B2 Hub connection | Extracted and staged on `codex/hub-provider`, based on #583: profile discovery, adapter/transport/request/event classes, configuration and existing tests. Review fixes close terminal streams and reuse upstream remote-response byte limits. 75 focused checks and all 285 web-module tests pass; full local API run has one previously reproduced upstream macOS socket-test failure (59 skips). Commit/publication is pending a commit-guard false positive on the runtime-property name constant; hosted CI has not run |
| B5 conversation storage | [Backend #586](https://github.com/openmrs/openmrs-module-chartsearchai/pull/586), `5ddfd912`, stacked on #583: service/DAO/models, audit attribution and purge handling, mappings/migrations and module registration. All 16 source/schema/test changes match the integration additions/removals. Ten focused tests and all 285 web-module tests plus packaging pass. Full local API run has only the previously reproduced upstream macOS socket-test failure (59 skips). Hosted Java 11/17/21, QueryStore-main, selftest and lint checks passed at this revision; no review threads outstanding. Combined runtime and MySQL migration acceptance remain unverified |
| B5 endpoints and wiring | Prepared locally against the exact #588/#586 and staged Hub assembly: controller discovery, new conversation, history and provider-neutral stream; REST/history/persistence tests; test dependencies/resources; component documentation and paired-source branch checks. All 49 focused checks and 316 web-module tests plus packaging pass against QueryStore `8b79db97`. Full API verification ran 2,944 tests with one previously reproduced upstream macOS socket-test failure and 59 skips; the web module was verified separately after the reactor stopped. Newer upstream answer fields and clinical assertions are retained; existing upstream `XmlPayloads.marshal` already provides the required behavior. Publication waits for the held Hub prerequisite commit; no endpoint PR or hosted checks yet. Combined runtime and approved capability/toggle acceptance remain unverified |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55), `fdf262ce`; all 468 tests, lint, type checks, local build and hosted build passed. CRLF separators, final-event model normalization and terminal reader cleanup are fixed with regression coverage; all three review threads are resolved. Existing search transport and visible panel are unchanged |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56), `f6f5cc24`, stacked on #55: history/new-session requests, conversation identifiers and provider/profile state, with logout isolation. Preserves upstream reasoning-display preferences and correctly represents empty history with a null session. All 476 local tests, lint, type checks, translation verification and production build pass; existing bundle-size warning remains. Hosted build and automated review check passed at this revision; no review threads outstanding. This slice does not activate history in the visible panel |
| F1 conversation lifecycle and visible history | [Frontend draft #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59), `7cf9503a`, on the exact #58/#57 prerequisite assembly `9ca6703a`: history hydration, New chat, lifecycle phases, cancellation/preemption, mounted selectors and chat/search-panel wiring. Carries the existing removal of patient-open warmup and restored-provider test. Conflicts are resolved under the approved decisions below; newer upstream answer-limit fields, reasoning controls and reader scrolling are retained. All 615 local tests, lint, type checks, translation extraction and production build pass; the existing bundle-size warning remains. Hosted build passed at this revision; release was skipped. Review findings are recorded below; browser/video and combined runtime acceptance remain unverified |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58), `08eec6ca`, stacked on #56: discovery client calls/types, provider/model pickers, configuration, styles and tests. All 499 local tests, lint, type checks, translation extraction and production build pass; hosted build and automated review check passed at this revision. One open finding is recorded below. Controls are not mounted until the lifecycle extraction. Carry its existing real-hook restored-provider test with that extraction |
| F3 formatted answers and citation renderers | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57), `1102317b`, stacked directly on #55: existing Markdown/table renderers, dependencies and tests; completed answers now use Markdown while retaining newer upstream citation safeguards. Six reproduced rendering failures are fixed, including disappearing clinical disclosures under repeated React rendering. All 484 tests, lint, type checks, translation extraction and production build pass locally; bundle-size warnings remain. Hosted build passed; automated review produced three open findings recorded below. Structured table activation and combined browser/runtime acceptance remain unverified |
| F3 staged answer/evidence presentation | Included with the tightly coupled lifecycle in [frontend draft #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59): separate answer/review/In-Depth sections, original/withheld drafts, evidence cards and grounding, feedback, styles, translations and existing tests. Reuses #57 renderers while retaining newer upstream attribution, severity and significance disclosures. Streaming off suppresses incremental display on the same conversation transport; backend token generation is not yet disabled. Local checks pass as recorded above; real-model capability behavior and combined acceptance remain unverified |

Carry relevant README changes with each contribution. Shared files are split by
behavior; do not replace their newer upstream versions. Ordinary topic PRs use
the normal product checks. Context PR #587 and its bundled-provider descendant #588
consume an API still under review in QueryStore #68, so they adapt the existing
paired-source Java 11/17/21 job for those branches, replacing checks against artifacts that lack the required API. It
installs the exact QueryStore source without a shared Maven cache and runs the full
ChartSearchAI reactor. Remove that temporary substitution and rerun ordinary checks
after the dependency merges/publishes, before merging either contribution. Any descendants consuming
that API must declare and verify the same source dependency rather than wait to be
extracted. The umbrella retains ownership of assembled-system pins and acceptance.
The obsolete local-embedding plan is removed with #587; current retrieval belongs
to QueryStore. Test mock, TypeScript configuration and lockfile changes travel only with the extraction
that needs them.

The file inventory covers all 97 backend and 39 frontend files changed between the
common ancestors and the source integration revisions above. Each is assigned to
the published or remaining groups, shared support, or the excluded paired workflow.
Shared-file extraction is not completion of the whole file: `LocalLlmEngine` and
its tests still contain cancellation changes, while frontend `chartsearchai.ts`
and its tests still contain discovery and feedback changes. Carry the
architecture and answer-wiring tests with the corresponding backend answer changes.
This completes file grouping; each remaining extraction still needs adaptation,
review and verification against current main. Integration acceptance is separate.

### Next Extractions

The four foundations, conversation storage, context budgets, frontend
history/session state and answer-rendering extractions remain open. The next publication steps follow the existing imports and contracts:

1. Publish the prepared Hub adapter on backend #583. Conversation storage (#586)
   is published separately on #583 with passing hosted checks. Both use its
   provider types; neither needs the other or the bundled adapter. Hub profile
   discovery stays with its adapter.
2. Context-budget PR #587 is stacked on #584 with passing hosted source-pair
   verification against the required QueryStore revision. It supplies
   `PatientChartRead`, `ContextSlice` and `TokenCounter` consumers for the next slice.
3. Bundled-provider behavior, cancellation and safety answer wiring are published
   as draft #588 on the exact #583/#585/#587 assembly. Connect providers and storage
   to the REST endpoints next. Preserve current main's additional answer-limit
   fields through the existing canonical answer serializer; the bundled envelope
   retains its source `ChartAnswer` for that endpoint adaptation. The endpoint slice
   is now prepared and locally verified with #586 and the staged Hub changes;
   publish it on their exact prerequisite assembly after the Hub commit hold is
   resolved. Keep prerequisites out of the endpoint PR's review diff. Carry the
   same declared QueryStore source dependency into its hosted checks.
4. Provider/profile selectors are published as frontend #58 on #56. Frontend draft
   #59 connects those selectors/history with #57 renderers for conversation lifecycle,
   visible history and staged presentation. Its exact prerequisite assembly is published
   as `codex/conversation-prerequisites`; `turn-phase` and the selector's existing
   real-hook restored-provider test travel with this consumer. Its hosted build
   passed; collected review remediation remains pending. Coordinate the streaming preference
   and optional capabilities with the backend endpoints before combined acceptance.
5. Once every integration capability is represented in the published set, address
   outstanding findings, recheck affected descendants and validate the assembled
   functionality against both integration branches. Do not wait for upstream merges.

### Approved Frontend Integration Decisions

These decisions govern resolution of the frontend lifecycle and presentation
conflicts. They are approved implementation direction, not evidence that the
behavior is implemented or validated. Carry the resulting behavior and its
documentation into the owning frontend/backend contributions; this roadmap owns
the cross-project coordination and acceptance tracking.

| Area | Approved behavior | Owning extraction |
| --- | --- | --- |
| Reasoning and previews | Honor `showReasoning`. When enabled, retain actual model reasoning behind a collapsed disclosure after the answer; when disabled, neither display nor retain it. Temporary previews remain distinct from the final answer. Missing reasoning is a supported case | F1 lifecycle and F3 presentation |
| Stop and cancellation | Keep answer or enabled reasoning content already shown when the user stops a turn. Mark unfinished checks, review and In-Depth as interrupted; do not imply they completed | F1 lifecycle, B3 cancellation and B5 endpoints |
| Scrolling | Follow new content only while the reader is at the latest content. Answer, review or In-Depth completion must not pull the reader away from earlier content | F1 chat panel |
| Safety disclosure | Combine the integration's execution status and rule/source details with newer upstream compact advisories, dates and caveats. Preserve upstream clinical limitations without duplicate warnings | B3 answer wiring and F3 presentation |
| Evidence and citations | Keep evidence cards and grounding results together with newer upstream attribution, severity and significance disclosures. Apply the same citation safeguards in Markdown, tables and evidence cards | F3 renderers and staged presentation |
| Feedback | Keep the internal numeric audit identifier and serialize it under the backend's existing `questionId` request field. Verify the actual feedback request against the controller contract | F3 feedback and B5 endpoints |
| Streaming choice | Preserve and honor the existing `useStreaming` toggle in the conversation flow. Enabled permits incremental output when supported; disabled presents a complete response without incremental output. Both choices retain the selected provider/profile and conversation/history behavior, cancellation and truthful check/review status | F1 transport/lifecycle, B2/B3 providers and B5 endpoints |
| Unsupported capabilities | A model or provider lacking an optional capability must still deliver its supported answer. Missing token streaming uses completed-answer delivery from the same selected provider; missing reasoning, structured blocks, review or In-Depth must not break plain-answer display or leave progress waiting indefinitely. Offer only supported actions; identify unavailable checks or elaboration where their absence matters | B1 descriptors, B2/B3 providers and F1/F2/F3 consumers |

Use the existing provider capability contract and the selected model/profile's
actual support rather than assuming every model supports every feature. Do not
silently switch providers or models to obtain a missing capability. Unsupported,
not run, interrupted and failed checks remain distinguishable from passed checks;
absence of a safety or grounding result is not proof that an answer is safe or
grounded. Required answer capability or provider unavailability still needs a
clear unavailable/error state and explicit user choice.

Streaming support needs frontend and backend coordination: the source integration
has a conversation streaming endpoint but no equivalent non-streaming conversation
endpoint. Do not route streaming-off requests through the old search flow if that
loses provider selection, conversation identity or history. Choose the smallest
product-native adaptation that fulfills the approved behavior; the transport
details remain an implementation decision, not a reason to ignore the toggle.

Resolve the mechanical merges under these decisions while completing the split.
Retain the full-split, review-fix, combined-validation sequence above. Verification
must exercise streaming enabled and disabled, supported and unsupported optional
capabilities, and absent optional payloads for bundled inference and Hub using the
existing tests and acceptance paths. Check that a usable answer remains visible,
progress terminates honestly, provider/profile and history are retained, Stop
preserves visible content, scrolling respects the reader and feedback uses the
backend request contract. Extend focused coverage only where these approved
adaptations require it; no new acceptance framework or unrelated feature work is
authorized. Record local, hosted and combined acceptance separately.

### Findings for the Review-Fix Pass

Frontend #57 has three open findings at `1102317b`: answer Markdown can
[load remote images](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510429),
[turn a citation number into an external link](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510442),
and structured tables
[omit citation warnings and clinical disclosures](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510448).
These remain assigned to #57 for remediation after the full split. A passing
automated review check does not mean there are no findings. Collect subsequent
findings with their PR and disposition; review readiness remains unverified.

Frontend #58 has one open finding at `08eec6ca`:
[available profiles are hidden when none is an available default](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58#discussion_r4159641463).
Retain manual selection of available profiles without silently choosing a fallback.
Its passing build and automated review check do not resolve this finding.

Frontend draft #59 has these source-review findings at `7cf9503a`, assigned to its
review-fix pass. They are identified from source; focused reproductions are still
needed before remediation:

- `useChartSearchAi.ts:245,657,670`: disabling reasoning clears cached notes, but
  an active turn's callbacks retain the submission-time setting and can store notes
  again. Honor the disabled setting throughout the turn, including completed-answer
  delivery when streaming is off.
- `useChartSearchAi.ts:238`: effect cleanup marks the hook unmounted without restoring
  that flag on setup. React StrictMode effect replay can drop history/New chat results.
- `useChartSearchAi.ts:495,542,688`: late session callbacks are not guarded by current
  request identity, even where late message updates are rejected. An old callback
  can replace a newer conversation identifier or clear its visible history.
- `ai-response-panel.component.tsx:1263` and `ai-response-panel.scss:624`: warning
  markup never applies the new status modifiers; ordinary warnings lose upstream
  red styling. Preserve the approved distinction between clinical warnings and
  neutral notices.
- `ai-response-panel.component.tsx:337,1122`: unresolved evidence can still receive
  a chart navigation link from the shared helper. Reconcile this across evidence
  cards and citation rendering; a missing source must not appear navigable as resolved.

#59 inherits the outstanding #57/#58 findings as well. Its passing local suites
do not establish complete graceful-degradation behavior or review readiness.

Backend draft #588 has these source-review findings at `389ae7a3`, assigned to its
review-fix pass:

- `LlmInferenceService.java:140,663`: the new model-budget check precedes the
  upstream module-composed-answer return. An oversized prompt can therefore reject
  an answer needing no model call. Preserve that deterministic path; the passing
  suite does not cover it with an available token counter.
- `LlmInferenceServiceTest.java:45` and `RemoteLlmEngineTest.java:37`: inherited
  integration tests call helpers directly. Carry their assertions into the actual
  production paths, consistent with the component's test instructions.
- `LlmInferenceServiceCitationWiringTest.java:71,154`: overload and primary-path
  comments are stale. Align them with the status-carrying entry point and the
  conversation endpoint once extracted.

Do not infer readiness from #588's passing local suites. Approved streaming-off
and unsupported-capability behavior remains work for the provider/endpoint/frontend
consumers and combined acceptance, as required above.

The prepared B5 endpoint slice has a source-review finding at
`ChartSearchAiRestController.java:1500,1543,1548`: a turn is stored before provider
execution, but an exceptional completion or disconnect can reach the catch without
persisting a terminal result. The wire error alone does not settle stored history.
Reproduce the actual controller-to-storage path during its review-fix pass and
preserve any answer already shown while recording the failure or interruption.
Several carried REST tests also call package-private helpers; passing them does
not establish the request authorization and HTTP contract. The existing real
controller-to-Hibernate tests verify audit identity and bundled-mode rejection;
broader request-path and failure acceptance remains pending.

Renewed backend checks passed: 25 provider-contract, 92 local-token/engine and
64 safety-status tests. Renewed source review found no additional actionable
defects in these four PRs. Frontend #55's three inherited stream defects are fixed;
six new regression cases failed before the fixes and pass afterward. Its build
retains the existing bundle-size warning. The backend repository's automated
review is disabled for fork PRs, so passing builds and this review do not establish
maintainer approval. Release/deployment jobs are skipped; none of these publications
constitutes deployment or integrated acceptance.

### Publication

Publish each topic branch to the project fork. Independent PRs target the
corresponding project's `main`; dependent PRs target the preceding topic branch.
GitHub requires that base branch in the destination repository: publish an exact
copy of the prerequisite revision there under a dedicated `codex/` topic ref,
using the verified repository write access. Keep that base aligned with its
prerequisite PR and record the relationship. PR descriptions state the focused
behavior, tests, dependencies and merge order. Do not present the stacked diff as
an independent change against main.

The backend `codex/provider-contract` base is published upstream at `b89211ced6f5da1df866ea72d361dcce154f0238`,
exactly matching #583. The backend `codex/local-token-counting` base is published
upstream at `370f4c329242242a86f1fdf167855f617fd94426`, exactly matching #584.
The backend `codex/bundled-prerequisites` base is published identically in upstream
and the fork at `1cf826b5`, assembling exact #583 `b89211ce`, #585 `c1f43ce9`
and #587 `508546e5` (including #584); #588 targets this base and contains only its
bundled-provider additions and required adaptations. Retarget after those
prerequisites merge and recheck the resulting contribution.
The frontend `codex/chat-stream-client` base is published upstream at
`fdf262cedcc8719c1621775179591f381c022a79`, exactly matching frontend #55.
The frontend `codex/chat-session-history` base is published upstream at
`f6f5cc24e6fd7b8e6149afbab1a0f30ef7e3a594`, exactly matching #56; #58 targets it.
The frontend `codex/conversation-prerequisites` base is published identically in
upstream and the fork at `9ca6703a98a90c3ee2d82e4cac8c93d69b893627`, assembling
exact #58 `08eec6ca` (including #56/#55) and #57 `1102317b`; #59 targets this
base and contains only its lifecycle/presentation additions and required adaptations.
Retarget and recheck after those prerequisites merge.
No integration branch or main branch was changed to create these bases.

If an extracted contribution needs umbrella verification, update the affected
`scripts/openmrs-source-pair-test.sh`, `scripts/verify-repository-lines.sh` or CI
consumer to verify selected PR revisions and dependency versions rather than
require every contribution head to equal `harness-integration`. General tooling
cleanup is not a prerequisite for publishing the split.
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
