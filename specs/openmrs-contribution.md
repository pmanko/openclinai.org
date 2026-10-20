# OpenMRS contribution delivery

**Stream:** Track A · **Status:** every PR targets `main` from the fork; the
maintainer re-reviewed all heads on 19 October and 73 threads are open, 39 of
them fixed and awaiting replies; no reply posted since 7 October · **Owner:**
umbrella for cross-project acceptance; each OpenMRS PR owns its behavior

Deliver the extracted ChartSearchAI backend and frontend contributions and the
QueryStore change to upstream review and merge, with our integration requirements
kept in this umbrella. Dated evidence: the
[7 October remediation record](reviews/2026-10-07-track-a-remediation.md), the
[7 October context evaluation](reviews/2026-10-07-context-evaluation.md), the
[18 October upstream sync](reviews/2026-10-18-track-a-upstream-sync.md) and the
[19 October review revalidation](reviews/2026-10-19-track-a-review-revalidation.md).

## Contribution model

The extraction is complete. Preserve its code, tests, documentation and review
history while maintainers review and merge the existing contributions. Do not
reopen decomposition or add new features as prerequisites.

Use one linear stack per project in this exact review and merge order:

- **Backend:** `main → #583 → #584 → #585 → #586 → #587 → #588 → #589 → #590`
- **Frontend:** `main → #55 → #56 → #57 → #58 → #59`
- **QueryStore:** `main → #85 → #86 → #87`

Every branch lives on the pmanko fork and every PR targets the destination
project's `main`; nothing of ours is pushed to the OpenMRS repositories. Each
branch contains its predecessor's current head, so a PR's "Files changed" view
includes the layers below it, and each PR description carries a link to the
compare view of its own layer against its predecessor's branch. The order is
stated in the descriptions. Keep the existing PR numbers, scopes, review
discussions and confirmed fixes while restacking. Do not wait for upstream merges
to prepare, test or publish the rest of the stack; after a predecessor merges, the
next PR's diff against `main` becomes exact by itself.

Manage both stacks with the installed `github/gh-stack` extension (`gh stack`):
`gh stack view` to inspect, `gh stack rebase` for the cascading rebase and
`gh stack push` to publish. `gh stack` reads its trunk from the fork, so
fast-forward only the local `main` to upstream before rebasing; do not move the
fork's `main`. Upstream `main` takes direct commits about hourly, so restack right
before each review round. Never substitute manually maintained assembly branches,
base-branch copies in the OpenMRS repositories, or replacement PRs.

Keep the original `harness-integration` branches unchanged as references. Maintain
newer upstream behavior and confirmed fixes. Each PR must remain understandable and
pass its applicable checks against its declared base; missing or skipped checks are
not passing evidence. Address review findings in the PR that owns the affected
behavior and publish the response with the fix and its verification. After a
predecessor merges, rebase and retarget dependents in order. Existing integration
PR closure is a separate decision, not implied by the split.

Every review round follows these rules:

- Fix the finding's pattern, not only the line named: check sibling code paths
  with the same shape.
- Before publishing a layer, an independent reviewer reads its diff against the
  threads it answers, without being told the fix is correct. The review covers
  upgrading from the previous head's database and a restart with existing data.
- Draft each thread reply in the same step as its fix. Replies are posted only on
  the owner's approval, as one set per round.
- A reply states what changed, the commit and how it was verified, and nothing
  else. It is no longer than the comment it answers. No thanks, restatement of the
  finding or narrative.
- A finding we notice and do not fix becomes an open item in this spec for the
  owner to decide, not a note in a dated record.

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
| B6 account context | [Fork #35](https://github.com/pmanko/openmrs-module-chartsearchai/pull/35), not yet upstream | #590 |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55) | main |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56) | #55 |
| F3 Markdown, tables and citations | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57) | #56 |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58) | #57 |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59) | #58 |
| Q1 QueryStore patient records over REST, completeness and dates | [QueryStore #85](https://github.com/openmrs/openmrs-module-querystore/pull/85) | main |
| Q2 QueryStore tiered context slice (ADR 17) | [QueryStore #86](https://github.com/openmrs/openmrs-module-querystore/pull/86) | main |
| Q3 QueryStore question interpretation and preprocessing (ADR 18) | [QueryStore #87](https://github.com/openmrs/openmrs-module-querystore/pull/87) | main |
| M1/Q0 original QueryStore integration PR, replaced by Q1–Q3 | [QueryStore #68](https://github.com/openmrs/openmrs-module-querystore/pull/68) | main |

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
- [x] Every stacked PR targets `main` and the base-branch copies in the OpenMRS
      repositories are gone
      ([record](reviews/2026-10-18-track-a-upstream-sync.md#base-branches-in-the-openmrs-repositories)).
- [x] Answer the QueryStore maintainer's request to split #68: #85, #86 and #87
      opened from the fork against `main` on 18 October, #68 answered
      ([record](reviews/2026-10-18-track-a-upstream-sync.md#querystore-split)).
- [x] Check every open thread against the heads after the maintainer's 19 October
      round: 73 open, all 29 new findings hold
      ([record](reviews/2026-10-19-track-a-review-revalidation.md)).

### Path to mergeable

A PR is mergeable when the maintainer has approved it, every thread is answered
and closed, its required checks pass and it applies cleanly to `main`. The
[revalidation record](reviews/2026-10-19-track-a-review-revalidation.md#new-findings-checked-against-the-code)
numbers the findings referred to below. Stages 2 to 4 touch separate repositories
and can run in parallel once the [decisions](#decisions) they depend on are made.

**Stage 1: answer what is already fixed.**

- [ ] Draft replies for the 44 threads open before 19 October: 39 fixed on the
      heads, 3 reopened by follow-ups (with the stage 2 and 3 fixes), 2 still open.
      Rewrite the 11 existing drafts to the reply rule above.

**Stage 2: backend, bottom layer up, each fix with its reply drafted.**

- [ ] #583: README table-of-contents entry (finding 11).
- [ ] #584: refusal tests, `isAvailable` through the active engine, table-of-contents
      entry (findings 11, 12).
- [ ] #585: screening-arm gate with the zorblatine case, one test per
      `dose_not_assessable` branch, table-of-contents entry (findings 1, 11, 13).
- [ ] #586: changeset 010 accepts its old checksum and 011 drops the column where
      it exists; `finishTurn` accepts the delivered answer; zero counts filed as
      null; ADR Decision 105 and the audit bullet updated; the Mockito test deleted
      (findings 2, 3, 14).
- [ ] #587: README line on restart behavior; the stale lab-expansion test comment.
- [ ] #588: `IncompleteChartException` reported as `incomplete_chart`;
      table-of-contents entry (findings 10, 11).
- [ ] #590: bundled deltas accumulated and the last Hub answer passed to
      `finishTurn`; `safetyStatus` and `safetyCheck` in the README (findings 3, 15).
- [ ] Restack onto upstream `main`; run the full suite on every layer, not only
      the tip; independent review of each layer's diff, including an upgrade from
      the previous head's database and a restart with data; push.

**Stage 3: frontend.**

- [ ] #57: carry `main`'s comment wording. #59: no version in the README, one
      definition of each error code (finding 16).
- [ ] Decide our own two residuals from the 18 October check: the wording when an
      explicitly picked profile becomes unavailable, and the safety box drawn for a
      bare `unavailable`.
- [ ] Test, independent review, push.

**Stage 4: QueryStore.**

- [ ] #85: a failed cold touch is reported incomplete; records filtered by each
      type's core read privilege; a completed type stays complete while it tops
      up; ADR banners deferred; the separator change moved to its own PR
      (findings 4, 5, 6, 17).
- [ ] #86: identifier and quote patterns; `rank` and `chartTruncated` docs; the
      mapping-code test; the seven stub overrides removed (findings 7, 17).
- [ ] #87: the four retrieval changes moved to a new PR with the latest-value
      ordering, the series decision, the Decision 6 and 17 updates, the javadoc
      placement and an evaluation; #87 keeps the interpreter and Decision 18
      (findings 8, 9, 17).
- [ ] Skip unchanged records during the bootstrap top-up, as its own PR.
- [ ] Restack, test, independent review, push.

**Stage 5: evidence and the next round.**

- [ ] Dispose of #587's context-composition finding with the two Decision 28
      gates, the 40-cell scope evaluation and the temporal probe, or a documented
      substitute: the renal retrieval regression, the metric-versus-prompt
      disagreement on negative-category citations, and the substitute cohort's
      limits. Keep the original scores; do not tune prompts to individual cells or
      silently redefine the gate. A retrieval correction belongs to QueryStore, must
      preserve clinical qualifiers, must be evaluated beyond one patient, and must
      not restore word stripping or add a case-specific ranking rule.
- [ ] Local boot check of the new heads: fresh setup, restart with data, and a
      module upgrade from a database set up on the 18 October heads.
- [ ] Post the round's replies on the owner's approval and request the next review.

**Stage 6: merge order once approved.**

- [ ] Backend #583 to #586 and frontend #55 to #58, whose checks pass today; after
      each merge, `gh stack rebase` reduces the next PR to its own layer.
- [ ] QueryStore #85, #86, #87 and the split-out PRs; QueryStore publishes a
      snapshot with the API.
- [ ] Ordinary dependency compatibility: ordinary builds of #587 to #590 pass
      against the published QueryStore API and the temporary paired-source job is
      removed; then #587 to #590.
- [ ] Frontend #59 after #590.
- [ ] Decide closure of #68 once #85 to #87 are accepted.
- [ ] The umbrella pins the merged `main` heads; the baseline is rebuilt only if
      the schema changed.

### Standing items

- [ ] Signoff 2: accept the dual-provider product and authorize controlled comparison.
- [ ] Signoff 3: accept release, companion merges, curated publication and PR cleanup.
- [ ] Decide closure of the old integration PRs (backend #157, frontend #23).
- [ ] Report the Core 2.9.0-SNAPSHOT module Liquibase resource-scope defect upstream
      (a TRUNK ticket with the reproduction and the proposed `DatabaseUpdater` patch
      from the [13 October record](reviews/2026-10-13-appointments-fresh-import-root-cause.md#fix-options)),
      then drop the local `optimized.startup=false` override once a fixed Core is
      in the pinned distribution.

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
| G13 | Hub prompt reuse and measured backend timing, now owned by the [provider parity](provider-parity.md) thread. The 24 July deferral assumed query-scoped was the operating default; ChartSearchAI #603 (6 October) made full chart the default again. |
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

Owner decisions for the [path to mergeable](#path-to-mergeable), with the
recommended option first:

- [ ] **Changeset 010 (#586):** add the maintainer's `validCheckSum` and an 011
      that drops the title column where an earlier 010 created it; or restore the
      original 010 and drop the column in 011.
- [ ] **Delivered answer on error or disconnect (#586, #590):** keep it on the
      audit row only, so unchecked text never reaches later prompts; or also on the
      saved turn.
- [ ] **Answers after a restart (QueryStore #85):** a type that has completed before
      counts as complete while it tops up, with the unchanged-record skip as its
      own PR; or the skip alone, which still blocks answers during the page scan.
- [ ] **QueryStore privileges (#85):** filter records by each type's core read
      privilege in the service read path and drop cross-patient search from the
      REST endpoint; or keep cross-patient search behind the same filter.
- [ ] **QueryStore #87 scope:** split the four retrieval changes into a new PR with
      their fixes and an evaluation; or keep them in #87 and add the evaluation
      there.
- [ ] **Decision 28 evidence (#587):** run the two mandated gates; or a documented
      substitute where they cannot run.
- [ ] **Resolving threads:** we resolve threads whose fix is mechanical and leave
      design threads for the maintainer; or leave every thread for the maintainer.
- [ ] **OpenMRS caches:** preserve existing bundled caching. The old harness plan's
      blanket cache prohibition conflicts with bundled preservation; Hub restrictions
      remain Hub-owned. A broader product-policy change requires explicit review.

[backend]: https://github.com/pmanko/openmrs-module-chartsearchai/blob/76e70dafd6fabcde7673fc8fe5cb765d640d6093/README.md#provider-integration-contract
[frontend]: https://github.com/pmanko/openmrs-esm-chartsearchai/blob/3f92411fbaeab83db697473fd0ee62e64b8671ce/README.md
[querystore]: https://github.com/pmanko/openmrs-module-querystore/blob/844dcd0ccad275831ecfaca6fe6cf4e4d8acaa2c/docs/rest-api.md
[hub]: https://github.com/pmanko/med-agent-hub/blob/main/README.md
[conformance]: https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md
