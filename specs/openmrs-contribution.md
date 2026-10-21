# OpenMRS contribution delivery

**Stream:** Track A · **Status:** three stacks on the OpenMRS repositories since
21 October, one PR per layer targeting the layer below; the maintainer's third
round is answered; a fresh-reviewer round (Codex) is being fixed layer by layer ·
**Owner:** umbrella for cross-project acceptance; each OpenMRS PR owns its behavior

Deliver the extracted ChartSearchAI backend and frontend contributions and the
QueryStore changes to upstream review and merge, with our integration requirements
kept in this umbrella. Dated evidence: the
[21 October cutover record](reviews/2026-10-21-stack-cutover.md), the
[20 October third-round remediation](reviews/2026-10-20-round3-remediation.md) and
the [7 October context evaluation](reviews/2026-10-07-context-evaluation.md).

## Contribution model

The extraction is complete. Preserve its code, tests, documentation and review
history while maintainers review and merge the existing contributions. Do not
reopen decomposition or add new features as prerequisites.

One stack per repository, managed with the `github/gh-stack` extension. The
branches live in the OpenMRS repositories, named for what the layer does, and each
PR targets the layer below it, so its Files changed view and its checks are that
layer's alone. Each layer is one squashed commit carrying the layer's narrative;
a review fix is a further commit on its layer. Never push any repository's `main`;
the umbrella's pre-push hook refuses it.

- **QueryStore:** `main → query-cache-separator (#92) → es-delete-at-version (#93)
  → bootstrap-skip-unchanged (#94) → patient-record-rest (#95) → context-slice (#96)
  → question-interpretation (#97) → retrieval-diversity (#98)`
- **Backend:** `main → provider-contract (#615) → local-token-counting (#616) →
  safety-check-status (#617) → conversation-storage (#618) → context-budget (#619)
  → bundled-provider (#620) → hub-provider (#621) → conversation-endpoints (#622)
  → account-context (#623)`
- **Frontend:** `main → chat-stream-client (#72) → chat-session-history (#73) →
  answer-presentation (#74) → provider-selection (#75) → conversation-lifecycle (#76)`

Working rules:

- `gh stack init <branches>` adopts the branches, `gh stack rebase` cascades them
  (fast-forward the local `main` to upstream first; the fork's `main` is never
  moved), `gh stack submit --remote upstream` pushes and creates or updates the PRs.
  Upstream `main` takes direct commits daily, so restack right before each review
  round.
- A restack that replays history can silently undo a change moved between layers;
  after one, diff the new top against the old heads merged onto `main` (the cutover
  record shows the check) before pushing.
- Fix a finding in the layer that owns the behaviour; the layers above follow in
  the same cascade. The full suite runs on every layer before a push; the push
  hook probes each new commit.
- PR descriptions say what the layer does and nothing else; a superseded PR is
  closed with one line naming its replacement. The fork's `codex/*` branches and
  the closed fork PRs stay as the record of the first three review rounds.
- The backend's required build compiles against QueryStore's published `main`, so
  `context-budget` and above fail it until QueryStore #95 to #97 merge and publish;
  the paired job builds the QueryStore stack top first and is the check that counts
  until then.

Every review round runs under the [review process](review-process.md): the commit
and push hooks with their revert and mutation probes, a fresh-session review with
`make review` (`AGENT=codex` so the reviewer is not the model that wrote the fix,
`STACK=1` for a stack), and replies drafted by its reply brief. These stacks add:

- Fix the finding's pattern, not only the line named: check sibling code paths
  with the same shape.
- The review covers upgrading from the previous head's database and a restart with
  existing data.
- Post replies right after the round's push, only on the owner's approval, as one
  set per round, one or two sentences each.
- A finding we notice and do not fix becomes an open item in this spec for the
  owner to decide, not a note in a dated record.

## Extraction register

| Existing work | PR | Base |
| --- | --- | --- |
| B1 shared provider contract | [Backend #615](https://github.com/openmrs/openmrs-module-chartsearchai/pull/615) | main |
| B4 exact token counting | [Backend #616](https://github.com/openmrs/openmrs-module-chartsearchai/pull/616) | #615 |
| B3 safety-check execution status | [Backend #617](https://github.com/openmrs/openmrs-module-chartsearchai/pull/617) | #616 |
| B5 conversation persistence | [Backend #618](https://github.com/openmrs/openmrs-module-chartsearchai/pull/618) | #617 |
| B4 QueryStore context and budgets | [Backend #619](https://github.com/openmrs/openmrs-module-chartsearchai/pull/619) | #618 |
| B3 bundled inference and cancellation | [Backend #620](https://github.com/openmrs/openmrs-module-chartsearchai/pull/620) | #619 |
| B2 Hub discovery and transport | [Backend #621](https://github.com/openmrs/openmrs-module-chartsearchai/pull/621) | #620 |
| B5 conversation endpoints and history | [Backend #622](https://github.com/openmrs/openmrs-module-chartsearchai/pull/622) | #621 |
| B6 account context | [Backend #623](https://github.com/openmrs/openmrs-module-chartsearchai/pull/623) | #622 |
| F1 staged stream transport | [Frontend #72](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/72) | main |
| F1 history client and session state | [Frontend #73](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/73) | #72 |
| F3 Markdown, tables and citations | [Frontend #74](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/74) | #73 |
| F2 provider/profile selection | [Frontend #75](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/75) | #74 |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #76](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/76) | #75 |
| Q4 query-cache key separator spelling | [QueryStore #92](https://github.com/openmrs/openmrs-module-querystore/pull/92) | main |
| Q5 Elasticsearch deletes at the document's version | [QueryStore #93](https://github.com/openmrs/openmrs-module-querystore/pull/93) | #92 |
| Q6 bootstrap top-up skips stored versions | [QueryStore #94](https://github.com/openmrs/openmrs-module-querystore/pull/94) | #93 |
| Q1 patient records over REST, completeness and dates | [QueryStore #95](https://github.com/openmrs/openmrs-module-querystore/pull/95) | #94 |
| Q2 tiered context slice (ADR 17) | [QueryStore #96](https://github.com/openmrs/openmrs-module-querystore/pull/96) | #95 |
| Q3 question interpretation and preprocessing (ADR 18) | [QueryStore #97](https://github.com/openmrs/openmrs-module-querystore/pull/97) | #96 |
| Q7 similarity diversity and deeper hybrid pools | [QueryStore #98](https://github.com/openmrs/openmrs-module-querystore/pull/98) | #97 |

The umbrella gitlinks record the three stack tops; the cutover record lists them.

## Target path

Earlier stages (the 7 October remediation, the 18 October upstream sync, the
19 October revalidation and the 20 October third round) are closed out in their
dated records and no longer listed here.

- [x] Cut over to one gh-stack stack per repository on the OpenMRS repositories,
      one squashed commit per layer, suites green on every layer, old PRs closed
      with pointers ([record](reviews/2026-10-21-stack-cutover.md)).
- [ ] Fix the fresh-reviewer (Codex) round in the owning layers: frontend done,
      QueryStore #93 to #96 done, #97 and #98 and the backend layers in progress
      ([record](reviews/2026-10-21-stack-cutover.md#fresh-reviewer-round)).
- [ ] Owner decision: QueryStore #95's completeness signal (a COMPLETED type can
      hide skipped records; flipping the flag on any skipped record would withhold
      every answer for a type with one poison record).
- [ ] Dispose of the context-composition evidence on #619: the 20 October cohort
      re-run is in Decision 28; the temporal probe has not been re-run on the new
      composition.
- [ ] Local boot check of the stack tops: fresh setup, restart with data, and a
      module upgrade from a database set up on the previous heads.
- [ ] Maintainer review of the new PRs; replies per the reply brief, posted on the
      owner's approval.
- [ ] Merge order once approved: QueryStore #92 to #97 first (a published snapshot
      makes the backend's required build pass), then backend #615 to #623, frontend
      #72 to #76; after each merge, `gh stack rebase` reduces the next PR to its own
      layer. The umbrella then pins the merged `main` heads; the baseline is rebuilt
      only if the schema changed.

### Standing items

- [ ] Signoff 2: accept the dual-provider product and authorize controlled comparison.
- [ ] Signoff 3: accept release, companion merges, curated publication and PR cleanup.
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

Owner decisions. The first seven were made on 19 October and gate the
[path to mergeable](#path-to-mergeable); the last is standing:

- [x] **Changeset 010 (#586), 19 October:** 010 accepts its old checksum through
      `validCheckSum`, and an 011 drops the title column where an earlier 010
      created it. Not chosen: restoring the original 010.
- [x] **Delivered answer on error or disconnect (#586, #590), 19 October:**
      `finishTurn` takes the last delivered envelope with the error result and keeps
      it on the audit row only; the saved turn stays empty, so unchecked text never
      reaches later prompts.
- [x] **Answers after a restart (QueryStore #85), 19 October:** skip records whose
      stored version matches, as its own PR. The reply proposes that a type
      completed before counts as complete while it tops up; that changes only if
      the maintainer agrees.
- [x] **QueryStore privileges (#85), 19 October:** filter records by each type's
      core read privilege in the service read path; cross-patient search stays
      behind the same filter, as Decision 14 allows.
- [x] **QueryStore #87 scope, 19 October:** the four retrieval changes move to a new
      PR with their fixes and an evaluation; #87 keeps the interpreter and
      Decision 18.
- [x] **Decision 28 evidence (#587), 19 October:** run both gates as written; where
      one cannot run, record why and the substitute measured, as #318 did. Original
      scores kept; no tuning to individual cells.
- [x] **Resolving threads, 19 October:** we resolve threads whose fix is mechanical
      and verifiable from the reply; design and blocking threads stay open for the
      maintainer.
- [ ] **OpenMRS caches:** preserve existing bundled caching. The old harness plan's
      blanket cache prohibition conflicts with bundled preservation; Hub restrictions
      remain Hub-owned. A broader product-policy change requires explicit review.

[backend]: https://github.com/pmanko/openmrs-module-chartsearchai/blob/76e70dafd6fabcde7673fc8fe5cb765d640d6093/README.md#provider-integration-contract
[frontend]: https://github.com/pmanko/openmrs-esm-chartsearchai/blob/3f92411fbaeab83db697473fd0ee62e64b8671ce/README.md
[querystore]: https://github.com/pmanko/openmrs-module-querystore/blob/844dcd0ccad275831ecfaca6fe6cf4e4d8acaa2c/docs/rest-api.md
[hub]: https://github.com/pmanko/med-agent-hub/blob/main/README.md
[conformance]: https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md
