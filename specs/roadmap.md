# OpenClinAI Roadmap

**Roadmap ID:** `PR-DECOMPOSITION-2026-09`

This roadmap coordinates the OpenClinAI workspace, validation harness and product
delivery. [Architecture](architecture.md) defines component responsibilities and
interfaces. Product repositories own their application requirements and detailed
implementation registers.

## 1. Current Priorities

1. Break the existing ChartSearchAI backend and frontend integration work into the
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
| Product delivery | Eight backend and five frontend extractions are published. Applicable hosted checks pass on all recorded heads; no review threads are unresolved. Confirmed findings are fixed. Backend #590 retains the documented local macOS socket-test failure despite passing hosted source-pair checks. Both linear stacks are published and their current hosted builds pass. Combined functional validation passes, and all thirteen contributions are ready for review | Maintainer review and ordered merging; retain integration branches unchanged |

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
[dual-provider conformance contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md)
and [QueryStore ADR](https://github.com/pmanko/openmrs-module-querystore/blob/55bf9971eb293b2155fb72de1e7cadfd6fab3bdd/docs/adr.md).
The [delivery status register](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap-status.md)
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
Each project follows the linear order above; the two projects can proceed in
parallel. Ancestor changes belong in the base, not in the displayed contribution diff.
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
| M2 | One linear PR stack per project | The existing PRs follow the exact Contribution Model order, each targets its immediate predecessor (first targets main), shows only its own changes and passes applicable checks; no prerequisite assembly branches remain in the review path |
| M3 | Backend delivery | Existing B1–B5 work is accounted for in upstream or extracted PRs, with its product checks |
| M4 | Frontend delivery | Existing F1–F3 work is accounted for in upstream or extracted PRs, with its lifecycle, provider and evidence/browser checks |
| M5 | Integrated release acceptance | Assembled product behavior and deployed evidence satisfy the existing release signoffs |

M5 is separate release work, not a prerequisite for publishing the extracted PRs.
The split does not require new test suites, acceptance infrastructure or a new demo.
Combined functional validation of the complete split is required before declaring
the decomposition complete; it is distinct from deployment and release signoff.
Run that validation once against the completed stack as part of this implementation.
If it fails, fix the failures and rerun the affected checks. Record the exact
revisions, results and browser evidence with the run. Temporary PR branches,
dependency arrangements and CI status belong in that evidence; do not add
permanent tests or workflow gates to enforce this temporary stack state.
Permanent tests verify lasting product or workspace functionality.

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
[QueryStore API contract](https://github.com/pmanko/openmrs-module-querystore/blob/55bf9971eb293b2155fb72de1e7cadfd6fab3bdd/docs/rest-api.md)
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

These are code dependencies, not alternative PR arrangements. Some slices have
no direct code dependency on their immediate predecessor, but all contributions
follow the linear review order in Contribution Model to keep review and merging
simple. The full context consumer still needs the QueryStore additions, and
endpoint wiring requires its providers and persistence.
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

| Existing work | Published PR | Immediate base | Current head |
| --- | --- | --- | --- |
| B1 shared provider contract | [Backend #583](https://github.com/openmrs/openmrs-module-chartsearchai/pull/583) | main | `b89211ce` |
| B4 exact token counting | [Backend #584](https://github.com/openmrs/openmrs-module-chartsearchai/pull/584) | #583 | `c245fa53` |
| B3 safety-check execution status | [Backend #585](https://github.com/openmrs/openmrs-module-chartsearchai/pull/585) | #584 | `ddfb4202` |
| B5 conversation persistence | [Backend #586](https://github.com/openmrs/openmrs-module-chartsearchai/pull/586) | #585 | `7d9056c3` |
| B4 QueryStore context and budgets | [Backend #587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587) | #586 | `b1cf5d56` |
| B3 bundled inference and cancellation | [Backend #588](https://github.com/openmrs/openmrs-module-chartsearchai/pull/588) | #587 | `18e03f6e` |
| B2 Hub discovery and transport | [Backend #589](https://github.com/openmrs/openmrs-module-chartsearchai/pull/589) | #588 | `b69ea2bb` |
| B5 conversation endpoints and history | [Backend #590](https://github.com/openmrs/openmrs-module-chartsearchai/pull/590) | #589 | `8622f1b5` |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55) | main | `fdf262ce` |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56) | #55 | `f6f5cc24` |
| F3 Markdown, tables and citations | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57) | #56 | `39b5217f` |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58) | #57 | `150c236a` |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59) | #58 | `be4f8bd6` |

All thirteen PRs have passing applicable hosted builds on these heads and no
unresolved review threads. Some superseded runs were cancelled during push/base
updates; the final runs completed successfully. Component verification and the
release/deployment signoff remain separate from review readiness.

Carry relevant README changes with each contribution. Shared files are split by
behavior; preserve newer upstream versions. From #587 onward, pull-request builds
install QueryStore `55bf9971eb293b2155fb72de1e7cadfd6fab3bdd` from source and run
the full ChartSearchAI reactor on Java 11, 17 and 21. Dependency-build selection
no longer depends on a PR branch name. Main publication and scheduled
QueryStore-main compatibility checks retain their existing paths. The umbrella
owns assembled-system pins and acceptance.

The obsolete local-embedding plan is removed with #587; current retrieval belongs
to QueryStore. Test mock, TypeScript configuration and lockfile changes travel only with the extraction
that needs them.

The file inventory covers all 97 backend and 39 frontend files changed between the
common ancestors and the source integration revisions above. Each is assigned to
the published or remaining groups, shared support, or the excluded paired workflow.
Shared files are accounted for by behavior: #588 carries engine cancellation and
the architecture/answer-wiring tests; #58/#59 carry frontend discovery and feedback.
The source-path comparison finds all 56 added backend and 14 added frontend files
in the published assembled work, including Hub #589 and endpoint #590. Stream
tests moved to `src/api/chat-stream.test.ts`; constructor, tokenizer authentication,
clinical-read and serializer adaptations retain newer upstream contracts. This
path/line comparison is extraction evidence, not functional acceptance; the
separate behavioral verification is recorded below.
All extraction groups are published, recorded review findings are fixed, and
combined functional validation passes. All thirteen PRs are ready for review.

### Current Execution: Review-Ready Stacks

The first acceptance step is complete: both published PR chains match the exact
Contribution Model order. `gh stack init`, `rebase` and `submit` adopted and
updated all existing PRs without replacements. Each actual GitHub base names the
immediate predecessor and points to its exact current head; each contribution diff
stays within its original scope. Existing review discussions, fixes and draft
states were preserved through restacking. After combined validation passed,
`gh stack submit --auto --open --remote origin` marked backend #588/#589/#590 and
frontend #59 ready for review without changing their heads. PR descriptions give
the linear review order and acceptance evidence.

Both final Git trees were identical immediately after restacking. A necessary
follow-up in #587 removed inherited branch-name-dependent CI selection and updated
the declared QueryStore source revision. This changed only the backend workflow
and its README explanation; backend application code and tests remain identical.
The final frontend tree remains identical in full. The one-time ancestry, diff,
tree and hosted-check evidence is recorded under
`artifacts/pr-split-acceptance/linear-stack-*.json` and
`artifacts/pr-split-acceptance/linear-restack-tree-proof.json`; these are run records,
not permanent branch-state tests.

The recorded backend/frontend findings below are fixed, applicable hosted builds
pass on all current heads, and their review threads are resolved. QueryStore Q0
fixes at `55bf9971` pass hosted Java 8/11/17/21 builds, the native reactor (527 API
tests, 57 web tests, two existing skips) and all 22 MySQL integration checks.
Its maintainer threads retain commit-linked responses and remain formally open.

Combined functional validation passes using backend `8622f1b5`, frontend
`be4f8bd6`, QueryStore `55bf9971` and Hub `6120c313`. Native module and frontend
builds completed; both modules report started without errors. The identity probe
verifies staged/mounted module hashes, served frontend assets and the Hub image
revision. The native backfill completed for all twelve registered types; the
selected synthetic chart reports 365 records, complete and not truncated.

Actual QueryStore HTTP checks accept registered context types, reject unknown
explicit types and reject context-only parameters outside context mode. Following
the exact next-page link preserves the chart snapshot and returns disjoint page
records. That check exposed the standard gateway dropping the external port from
absolute links; the umbrella's QueryStore route now goes directly to the same
backend, preserving the external Host. Caddy validation and the HTTP rerun pass.

The existing real-model staged Answer/check/In-Depth, two-turn date continuity and
In-Depth preemption checks pass. Existing display fixtures pass for tables and
flagged/rejected output through reload. Actual UI feedback persisted on its
numeric audit row. Those harness checks and fixture corrections are published at
`9b5b87e`; its full suite passes (1,111 tests, 36 skips, 3 deselected), with hosted
checks passing. Valid evidence for unchanged code is retained.

The final runtime checks additionally establish:

- Bundled streaming off delivers a complete cited answer. Enabling streaming
  retains the same provider and conversation; a follow-up resolves the prior
  measurement's date and both answers persist.
- Stop during actual incremental output retains visible partial answer/reasoning
  and re-enables the composer. The server records cancellation; durable storage
  of that unfinished draft is not claimed.
- Missing optional checks and In-Depth do not leave bundled progress waiting;
  disabled safety checks are labeled unavailable. Hub, which does not advertise
  token streaming, still delivers completed answers on its selected profile.
  Missing model reasoning does not prevent its answer.
- Hub streaming off and on preserve explicit provider/profile selection,
  checked/original answers, evidence and terminal In-Depth withholding. The
  affected Hub read path passes with the reviewed QueryStore revision, and the
  completed two-turn history restores after reload.
- Scrolling to earlier content during a Hub follow-up stays at that position
  through answer review and In-Depth completion.

One-time evidence is under `artifacts/pr-split-acceptance/`, including
`runtime-identity-current.json`, `querystore-q0-http-current.json`,
`manual-runtime-observations.md`, the bundled/Hub history JSON files and browser
screenshots/recordings. Model output still includes recorded quality failures:
Hub In-Depth can be withheld and a cancelled bundled draft contained inconsistent
dates. No prompt tuning or model-quality acceptance is implied. The bundled
provider used its configured remote engine; bundled local-engine execution and
optional QueryStore Elasticsearch/ONNX suites are not claimed.

All thirteen component heads have passing applicable hosted checks and zero
unresolved review threads. QueryStore maintainer threads retain their documented
responses and remain formally open. The umbrella exact-source build at `c5f7b55`
passes; the later proxy/documentation change has its own verification record.
The next contribution step is maintainer review and merging in the approved
linear order, updating dependents with `gh stack`. Release signoff (M5), production
deployment and the other umbrella roadmap tracks remain separate unfinished work.

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

The following records the original fixes and their local validation. Those commits
were carried through restacking; current heads, bases and hosted status are owned
by the extraction register above. Older local test totals are not reruns of the
expanded intermediate stack branches.

Frontend #57's three review findings are fixed at `59943fb` and all threads are
resolved after its hosted build passed: model-generated
[remote images](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510429)
are omitted,
[numeric links](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510442)
resolve through the chart-citation contract, and
[tables](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57#discussion_r4159510448)
accept attribution, severity and significance safeguards. Five added cases failed
before the fixes; six added cases and all 490 tests pass.

Frontend #58's
[available nondefault profile finding](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58#discussion_r4159641463)
is fixed at `b3d8a7c`: the picker remains usable for explicit selection while no
profile is selected. No fallback is chosen silently. Its reproduced regression,
all 500 tests and hosted build pass; the thread is resolved.

Frontend draft #59 carries both prerequisite fixes and resolves its six recorded
source findings at `4181b0d`:

- Live reasoning configuration gates active callbacks and clears cached/buffered
  notes when disabled, for streaming enabled and disabled.
- Effect setup restores the mounted flag so StrictMode replay permits history and
  New chat completion.
- Current-request identity gates session callbacks after preemption and New chat;
  old events cannot replace the new conversation or remove its visible history.
- Clinical warnings retain red styling; other-medication notices remain neutral.
- Unresolved citations do not navigate in the answer, citation details or evidence cards.
- Retained reasoning is disclosed after the answer, collapsed unless the reader has
  chosen to expand it; stopped/failed content remains inspectable.

#59 also propagates citation safeguards through its actual structured-table path.
Fourteen regression cases failed before these fixes and pass afterward; all 635
local tests, lint, type checks, translation extraction, production build and
whitespace checks pass. Existing bundle-size warnings remain. Hosted build passed
at this updated head; release was skipped. These local results do not establish browser/video
proof, complete graceful degradation across real models or combined acceptance.

Backend draft #588's recorded findings are fixed at `e2ae0874`:

- Model-budget checks follow the module-composed-answer return on both paths,
  before any model inference or preliminary reasoning pass. Both regressions
  failed first through actual QueryStore backfill/retrieval and safety composition.
- Inherited budget and remote-overflow assertions exercise the actual search and
  HTTP engine paths, preserving rejection and input-material checks. Only the model
  counter is a boundary recorder; these tests do not measure a real model's limits.
- Citation-wiring comments describe the status-carrying entry point and bundled
  conversation path accurately.

All 113 focused checks, full API verification and web-module verification/packaging
pass locally. Hosted paired-source Java 11/17/21 checks, selftests and lint also
pass on this updated head. Combined acceptance remains pending. Streaming-off and unsupported real-model behavior still require the
provider/endpoint/frontend acceptance specified above.

Backend draft #589's terminal-status findings are fixed at `8f3ccea2`.
A normal terminal response settles unfinished review and In-Depth stages without
claiming success and preserves the supported answer, original draft and partial
detail. EOF without a terminal Hub event still produces an incomplete-stream error;
interrupted optional stages publish their failed outcomes first. Three regressions
exercise the configured OpenMRS provider through its real HTTP transport, including
absent optional capabilities. They use protocol fixtures and do not establish
real-model quality. All 62 focused checks, full API verification and web-module
checks pass locally. Hosted Java 11/17/21, QueryStore-main, selftests and lint
also pass on this latest head; snapshot publication and the dependency scan were
skipped. Combined runtime acceptance remains pending.

Backend draft #590's failure/history and request-path fixes are published at `1f9166c2`.
Actual request-handler regressions reproduced stored turns lacking a terminal
result after response failures. The controller now settles started turns before
abandoning the response and avoids duplicate persistence. Interrupted In-Depth
outcomes are stored with already checked answers; incomplete turns remain inspectable
but are not replayed as completed context. The composed request/HTTP-provider/Hibernate
path verifies provider rejection, restored answer/draft/status/audit identity and
unauthenticated request rejection using synthetic fixtures and a local HTTP peer.
All 35 focused checks and 321 web tests plus packaging pass against the
prerequisite revisions used for that run. Full API verification ran 2,949 tests
with zero errors,
59 skips and the previously recorded macOS failure in
`LocalLlmServerAuthTest.aPortHeldByAListenerThatAcceptsNothingFailsTheStart`.
Hosted paired-source Java 11/17/21 checks, selftests and lint passed on this latest
head; ordinary artifact, QueryStore-main and dependency-scan jobs were skipped.
These checks do not establish live routing, browser/video evidence or combined model acceptance.

Renewed backend checks passed: 25 provider-contract, 92 local-token/engine and
64 safety-status tests. Renewed source review found no additional actionable
defects in these four PRs. Frontend #55's three inherited stream defects are fixed;
six new regression cases failed before the fixes and pass afterward. Its build
retains the existing bundle-size warning. The backend repository's automated
review is disabled for fork PRs, so passing builds and this review do not establish
maintainer approval. Release/deployment jobs are skipped; none of these publications
constitutes deployment or integrated acceptance.

### Publication

Publish each topic branch to the project fork and preserve its existing PR.
Follow the exact linear order in Contribution Model: only the first PR in each
project targets `main`; every other PR targets its immediate predecessor.
GitHub requires that base branch in the destination repository: publish an exact
copy of the predecessor PR's current head there under its `codex/` topic ref,
using the verified repository write access. Keep each destination base aligned
with its corresponding PR head. These are copies of individual PR branches,
not extra branches that assemble multiple prerequisites.

Update PR descriptions to state their focused behavior, validation and immediate
predecessor. Remove assembly branches from the PR review path as the existing
PRs are retargeted. After a predecessor merges, rebase and retarget the remaining
stack in order, preserving its changes and checking the resulting diffs. Do not
change the reference integration branches or merge into upstream `main` as part
of restacking.

Assembled-system verification records the selected source revisions and invokes
existing functional checks. Permanent workspace checks verify source consistency
and reproducible builds; they must not require a particular contribution branch,
PR base, PR number or current publication state. The integration branches remain
reference sources. The umbrella owns assembled-system gitlinks and build provenance.

The split does not authorize closing the existing integration PRs. Their disposition
can be decided once the smaller contributions cover the intended capabilities.
Branch retention is independent of PR closure. QueryStore #68 review remains its
own delivery work; do not expand the ChartSearchAI split to it automatically.

## 6. Catalyst Delivery

The [four-pathway delivery roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/openelis-reporting-catalyst-integration.md)
and [Feature 008 register](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/008-catalyst-query-workbench/tasks.md)
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
