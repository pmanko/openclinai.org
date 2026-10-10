# OpenMRS contribution delivery

**Stream:** Track A · **Status:** stacks published and checked; review dispositions
open; upstream merge awaits maintainers · **Owner:** umbrella for cross-project
acceptance; each OpenMRS PR owns its behavior

Deliver the extracted ChartSearchAI backend and frontend contributions and the
QueryStore change to upstream review and merge, with our integration requirements
kept in this umbrella. Dated evidence: the
[7 October remediation record](reviews/2026-10-07-track-a-remediation.md) and the
[7 October context evaluation](reviews/2026-10-07-context-evaluation.md).

## Contribution model

The extraction is complete. Preserve its code, tests, documentation and review
history while maintainers review and merge the existing contributions. Do not
reopen decomposition or add new features as prerequisites.

Use one linear stack per project in this exact review and merge order:

- **Backend:** `main → #583 → #584 → #585 → #586 → #587 → #588 → #589 → #590`
- **Frontend:** `main → #55 → #56 → #57 → #58 → #59`

The first PR targets the destination project's current `main`. Every subsequent PR
targets the immediately preceding PR's branch and contains that predecessor's
current head, so its diff shows only its own contribution. No separate prerequisite
assembly branches or branching dependency graphs. Keep the existing PR numbers,
scopes, review discussions and confirmed fixes while restacking. Do not wait for
upstream merges to prepare, test or publish the rest of the stack.

Manage both stacks with the installed `github/gh-stack` extension (`gh stack`):
`gh stack init --base` bottom-to-top against a verified trunk, `gh stack view` to
inspect, `gh stack rebase` for cascading rebases, `gh stack submit` to update
existing heads and bases, then `gh stack sync`. GitHub rejects native Stack objects
for these fork PRs; retain local tracking and the actual linear PR bases rather
than replacing PRs. Verify fork/upstream remote selection and existing-PR matching
before any remote update. Preserve draft states; do not use `--open` until the
readiness requirements pass. Verify both the local stack and actual GitHub bases
after publication. Never substitute manually maintained assembly branches or create
replacement PRs.

Keep the original `harness-integration` branches unchanged as references. Maintain
newer upstream behavior and confirmed fixes. Each PR must remain understandable and
pass its applicable checks against its declared base; missing or skipped checks are
not passing evidence. Address review findings in the PR that owns the affected
behavior and publish the response with the fix and its verification. After a
predecessor merges, rebase and retarget dependents in order. Existing integration
PR closure is a separate decision, not implied by the split.

The completed stack received combined functional validation once. If a relevant
change or failure requires another check, rerun the affected existing checks and
record revisions and results. Permanent tests cover lasting behavior, never PR
branches, bases, numbers or transient publication state. Local progress and
exact-source builds must not depend on upstream merging or publishing first.

## Extraction register

| Existing work | Published PR | Immediate base |
| --- | --- | --- |
| B1 shared provider contract | [Backend #583](https://github.com/openmrs/openmrs-module-chartsearchai/pull/583) | main |
| B4 exact token counting | [Backend #584](https://github.com/openmrs/openmrs-module-chartsearchai/pull/584) | #583 |
| B3 safety-check execution status | [Backend #585](https://github.com/openmrs/openmrs-module-chartsearchai/pull/585) | #584 |
| B5 conversation persistence | [Backend #586](https://github.com/openmrs/openmrs-module-chartsearchai/pull/586) | #585 |
| B4 QueryStore context and budgets | [Backend #587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587) | #586 |
| B3 bundled inference and cancellation | [Backend #588](https://github.com/openmrs/openmrs-module-chartsearchai/pull/588) | #587 |
| B2 Hub discovery and transport | [Backend #589](https://github.com/openmrs/openmrs-module-chartsearchai/pull/589) | #588 |
| B5 conversation endpoints and history | [Backend #590](https://github.com/openmrs/openmrs-module-chartsearchai/pull/590) | #589 |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55) | main |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56) | #55 |
| F3 Markdown, tables and citations | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57) | #56 |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58) | #57 |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59) | #58 |
| M1/Q0 QueryStore preprocessing, dispatcher links, explicit chart reads, validation | [QueryStore #68](https://github.com/openmrs/openmrs-module-querystore/pull/68) | main |

The umbrella gitlinks record the heads under review; the dated record lists them.

## Target path

- [x] Rebase both stacks on current upstream in the declared order, publish them
      and verify actual GitHub bases and heads
      ([record](reviews/2026-10-07-track-a-remediation.md#verified-on-7-october)).
- [x] Fix review findings in their owning PRs with regression coverage; publish
      responses with fix and verification
      ([record](reviews/2026-10-07-track-a-remediation.md#verified-on-7-october)).
- [x] Restore per-PR checks on all heads, ordinary and paired-source
      ([record](reviews/2026-10-07-track-a-remediation.md#verified-on-7-october)).
- [x] Publish component heads, update umbrella pins and consumers, run assembled
      checks ([umbrella #8](https://github.com/pmanko/openclinai.org/pull/8)).
- [x] Reconcile all QueryStore #68 inline threads against implemented fixes
      ([record](reviews/2026-10-07-track-a-remediation.md#verified-on-7-october)).
- [ ] Answer the QueryStore maintainer's request to split #68 with a concrete
      disposition; zero unresolved inline threads does not settle it.
- [ ] Dispose of #587's context-composition finding: the renal retrieval regression,
      the metric-versus-prompt disagreement on negative-category citations, and the
      substitute cohort's limits. Keep the original scores; do not tune prompts to
      individual cells or silently redefine the gate. A retrieval correction belongs
      to QueryStore, must preserve clinical qualifiers, must be evaluated beyond one
      patient, and must not restore word stripping or add a case-specific ranking
      rule. Recheck affected behavior after any correction.
- [ ] Close #587's two remaining review threads: temporary dependency-job removal
      and the reviewer's retrieval-versus-safety classification.
- [ ] Obtain ordinary dependency compatibility: the QueryStore API reaches upstream
      and a published artifact, ordinary builds of #587–#590 pass against it, and the
      temporary paired-source CI is removed.
- [ ] Signoff 2: accept the dual-provider product and authorize controlled comparison.
- [ ] Signoff 3: accept release, companion merges, curated publication and PR cleanup.
- [ ] Decide closure of the old integration PRs (backend #157, frontend #23).
- [ ] Upstream merges, in stack order, by the OpenMRS maintainers.

Signoff 1 approved the original baseline procedure. Published extraction and its
earlier acceptance do not establish current review readiness, a deployed release or
clinical acceptance. Reconcile existing signoff evidence against affected current
revisions; do not rerun unaffected checks because documentation moved. Upstream
merging, deployment changes and release/clinical signoffs are not authorized by
remediation work.

## Contracts

Our [integration requirements and interface reference](../docs/openmrs-provider-interface.md)
belong to this umbrella. Native product behavior remains documented by
[ChartSearchAI][backend], [the frontend][frontend], [QueryStore][querystore] and
[Hub][hub]. The [harness protocol][conformance] owns fixtures and experiment
evidence. Equivalent approved medication content, CIEL mappings, exposure
resolution and CDS Hooks remain a separate clinical-review track; a shared
safety-status interface does not prove equivalent clinical coverage.

## Release acceptance

IDs retain the namespace `OPENMRS-DUAL-PROVIDER-PARITY-2026-07-20`. This table
routes acceptance to its owner; it is not another application spec. Historical
G01/G02 roadmap-hash and branch-backup procedures are not standing checks.
Workspace source consistency is governed by the umbrella architecture.

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

Each row is accepted by its owners' tests, the assembled OpenMRS source check and
real-interface evidence recorded in a dated review, then ticked by owner review.
Static file presence, regex matches or fixture copies do not prove runtime
behavior. Live claims need artifacts supporting the asserted values and their
actual configuration. A failed or skipped required check remains incomplete; an
approved deferral is identified separately. The one-time split acceptance is
recorded in the dated record and is not replaced by recurring branch-state tests.

**Controlled comparison after product acceptance.** Hold model, prompt, sampling,
chart, question and reference date fixed while varying a declared provider,
context mode, checking stage or cache condition. Design and review the matrix
before collection. Run deterministic audits before judging, preserve separate
judgments, and report per-cell quality and latency without requiring identical
answers or one aggregate winner. The harness collects and reports; the umbrella
publishes reviewed artifacts. Product setup and release remain outside experiment
execution.

## Decisions

- [ ] **OpenMRS caches:** preserve existing bundled caching. The old harness plan's
      blanket cache prohibition conflicts with bundled preservation; Hub restrictions
      remain Hub-owned. A broader product-policy change requires explicit review.

[backend]: https://github.com/pmanko/openmrs-module-chartsearchai/blob/20cb84ba97bb76ee97a8745016a6d9bb1546077b/README.md#provider-integration-contract
[frontend]: https://github.com/pmanko/openmrs-esm-chartsearchai/blob/475f6eb60ea14011f719c861b02d02daf2156390/README.md
[querystore]: https://github.com/pmanko/openmrs-module-querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/rest-api.md
[hub]: https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/README.md
[conformance]: https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md
