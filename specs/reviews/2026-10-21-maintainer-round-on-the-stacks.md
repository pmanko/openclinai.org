# Maintainer round on the new stacks: inventory and why the harness missed it (21 October 2026)

Daniel reviewed the QueryStore stack (#93 to #98) and the frontend stack (#72 to #76)
between 11:25 and 13:37 on 21 October, after the cutover push and while the Codex round
ran. The backend stack (#615 to #623) has no maintainer review yet. Thirty-two threads
in all: twenty on QueryStore, twelve on the frontend. Full text is in
`work/review/daniel-round4-threads.md`; nothing is answered or fixed yet except one local,
unpushed commit on #93 (02925c4) made before this inventory was asked for.

## Verdicts

Every thread is valid as stated; none rests on a misreading. "Blocking" is Daniel's own
word on the thread. The last column is why our review tooling did not surface it, by the
categories under the table.

### QueryStore

| PR | Site | Finding | Blocking | Miss |
| --- | --- | --- | --- | --- |
| #93 | `ElasticsearchBackendStore` bulkDelete | mget reports a missing index per item, so each id comes back a retryable failure where `delete()` treats it as success | no | E |
| #93 | ADR open item | the "accounting under concurrent writes" item still describes `_delete_by_query`, which this layer removed | no | B |
| #93 | integration test javadoc | the retry fix inserted two tests between a javadoc and the test it describes | no | B |
| #94 | `BootstrapServiceImpl.resyncType` | an interrupted resync is resumed by the next `bootstrap()` with the skip on, because `walkAfresh` is not persisted; the row ends COMPLETED with records unrewritten | yes | E |
| #94 | `AfterCommitDispatcher.dispatchPrepared` | no test that `prepare` waits for the commit; run at registration the suite still passes | no | D |
| #94 | ADR Decision 12 | the same-second limit sentence went with the rounding sentences he asked to drop on #90, though it still applies | no | A |
| #94 | `AfterCommitDispatcher.dispatch` | the fix rewrote `dispatch` without changing what it does | no | B |
| #95 | `TypeBootstrapper.runForPatient` | the per-patient walk does not skip stored records, so a patient whose projection always fails is re-embedded on every read, 304s included | yes | E |
| #95 | `QueryStoreRestController` | `?patient=&q=...` runs a cross-patient search and returns 200; a blank patient must be a 400 | yes | E |
| #96 | `QueryStoreServiceImpl` effective types | types the caller cannot read stay in `effectiveTypes`; he wants them out and named in `withheldTypes` (asked on #86) | no | A |
| #96 | `PatientRecordView.sliceId` | a second canonical form that has drifted from `PatientChartFingerprint` since the scalar-kind fix | no | B |
| #96 | `continuesIdentifier` | applied to quoted phrases it drops matches they made before the boundary fix | no | B |
| #96 | `ConceptNameUtil` codes cap | the cap costs common concepts their SNOMED codes; only exact matching reads them (asked on #86) | no | A |
| #96 | panel completion | no test with a member as the similarity hit, the only production path (asked on #86); dropping the member check passes | no | A, D |
| #97 | `ContextQuestionInterpreter` idioms | `at last` blanks "Viral load at last test?", which ChartSearchAI's router reads as temporal | yes | C |
| #97 | medications cues | missing `regimens?` and "she is taking", which ChartSearchAI's Decision 180 added to its router | yes | C |
| #97 | `getContextSlice` | no test that the caller's `temporal` survives interpretation; both interpret tests send it false | no | D |
| #97 | `QueryStoreService` javadoc | says preprocessing is gated on `interpretQuestion`; the similarity leg preprocesses regardless | no | C |
| #98 | diversification javadoc | "a trend question keeps its series" overclaims; identical values share one slot | no | B |
| #98 | similarity picks | a hit the chart does not hold (past the ES cap) takes a slot it cannot fill | no | E |

### Frontend

| PR | Site | Finding | Blocking | Miss |
| --- | --- | --- | --- | --- |
| #72 | `chat-stream.test.ts` | the `indepth_error` test asked for on #55 is still missing; removing the callback passes | no | A, D |
| #72 | fixture comment | the copied conformance cases do not name their source file (asked on #55) | no | A |
| #73 | `chat-session.store.ts` | reset should reuse the store's defaults and replace state; a merged partial lets a later field leak across users (asked on #56) | no | A |
| #74 | markdown walk | a marker inside a raw HTML block gets no chip, rating or caveat | no | A |
| #74 | emphasis | `UGT1A1*28` still renders as emphasis (asked on #57), with one change needed for the joined-group source | no | A |
| #74 | links | model-supplied links are rendered live with their URL hidden; he would render them as text | no | A |
| #74 | `citation-chip` comment | one cosmetic line-break change makes moved code read as rewritten | no | B |
| #75 | `hub-profile-discovery` | a dropped pick never re-reads `/models`, so a recovered profile cannot come back without reopening | no | E |
| #75 | `model-picker` | the `selection-unavailable` status branch is unreachable after the all-unavailable fix | no | B |
| #76 | README | two links point at closed backend #590 instead of #622 | no | B |
| #76 | `ai-chat-content.scss` | `.newChatLabel` is unused | no | B |
| #76 | `useChartSearchAi` (reply) | the other panel still loses its question: `isStartingSession` is per hook instance, so its composer stays enabled during a New chat | no | B |

## Why the harness missed them

- **A. Carried-over asks, ten threads.** Rounds two and three left non-blocking asks on the
  fork PRs (#55, #56, #57, #86, #90). The third-round record fixed the blocking findings
  and listed the rest as later work; the cutover squashed each layer from the fork
  branches without a checklist of those asks, so none of them moved into the new stack.
  The reviewer brief does not read the previous PR's threads, and `make review` fetches
  threads only from the PR it is pointed at. This is a process gap, not a reviewer gap:
  the register of open asks lived in a dated record and a memory file, not with the code.
- **B. Leftovers from our own fix commits, eleven threads.** Displaced javadoc, a
  no-op rewrite, a second canonical form that drifted after the fingerprint fix, a
  boundary rule over-applied after the identifier fix, a branch made unreachable by the
  retry fix, links to a closed PR, an unused class, a guard that locks the request but
  not the other panel's composer. The Codex round ran once per PR at its first pushed
  head (`ROUNDS=1`); no reviewer, human or model, read the layers again after the fixes
  landed and the stacks were cascaded. Daniel reads the whole PR each time.
- **C. Cross-repository consistency, four threads.** The reviewer brief scopes a review
  to one repository. Daniel reads the consumer: ChartSearchAI's `QueryScopeRouter` and
  its Decision 180 define what "temporal" and "medications" mean to the only caller that
  will send `interpret=true`, and the QueryStore interpreter had drifted from both.
- **D. Coverage gaps a line-removal pass finds, four threads.** Daniel's method is to
  remove a line and run the suite; where it stays green he asks for the test. The Codex
  reviewer does this ad hoc (it found the #98 limit case this way) and at `EFFORT=medium`
  stops after two or three findings. The pre-push probes verify only the mutations we
  name in the commit, so they cannot find a missing one.
- **E. Operational-state reasoning, six threads.** Restart and resume (`walkAfresh` not
  persisted), the cold-touch read path re-entering the walk, a blank query parameter, a
  missing index on a fresh install, a hit past the Elasticsearch cap, a dropped pick after
  recovery. The reviewer brief asks for the upgrade and restart cases, but the reviewer
  reads the diff rather than the state machine around it.

## What the reviewer runs actually did

Measured from the Codex transcripts under `work/review/<repo>-<pr>/` (reasoning is not
logged by Codex; only the commands it ran and its final answer are).

| Run | Wall time | Builds run | Reported |
| --- | --- | --- | --- |
| QueryStore #93 to #98 | 6 to 10 min each | 4 to 5 Maven runs each, 30 to 194 s of build time | 0 to 3 blocking, 0 or 1 question |
| Frontend #72 to #76 | 2 to 10 min each | up to 34 vitest runs | 0 to 3 blocking, 0 or 1 question |

- **It read the files Daniel's findings are in.** The transcripts show it opened
  `QueryStoreRestController` (the blank `patient`), `BootstrapServiceImpl` (`walkAfresh`),
  `TypeBootstrapper.runForPatient`, `PatientRecordView.sliceId`, `ConceptNameUtil`'s cap,
  the interpreter's idiom list, `model-picker`'s status branches and `isStartingSession`.
  It reported none of them. Each run converged on one to three findings it could
  reproduce, spent its time on those reproductions, and stopped; nothing in the brief or
  the driver makes it exhaust the file it has open. Daniel's pass is the opposite shape:
  breadth first, twenty items on one stack, most of them one sentence with a suggestion.
- **It never reasoned about four sites at all.** `dispatchPrepared` timing, `withheldTypes`,
  `continuesIdentifier`, `regimen`, `QueryScopeRouter`, `scheduleRetry` and the store's
  reset do not occur in the transcripts outside file dumps.
- **The brief filters out most of what Daniel writes.** A finding is blocking only with a
  failure mode and a run; "style and taste are not findings"; "checked-and-fine gets no
  words"; only `high` effort says to return uncertain findings as questions. Twenty-seven
  of Daniel's thirty-two threads are non-blocking by his own word: javadoc, a test he
  wrote, an ADR sentence, dead code, a design preference. Our medium-effort reviewer is
  told, in effect, not to report that class.
- **It had no prior threads.** `threads.json` held zero threads for every QueryStore PR
  (Daniel reviewed after the run) and one to three bot threads for the frontend PRs.
  `review/bin/threads.py` collects the PR's own threads only; the rounds-two-and-three
  asks on the fork PRs were in no input. The tasks that tracked those asks (#9 to #11)
  were deleted during the cutover on the assumption the new stack subsumed them.
- **It had one repository.** The probe worktree is the PR's repository; the consumer's
  router and ADR were not reachable, and the brief does not name them.
- **It ran once.** `ROUNDS` defaults to 1 and each stack was reviewed once at its first
  pushed head; no run looked at the fixed layers or at the cascaded commits.

## What follows from this

- Carry the open asks with the code: a checklist file per stack layer (or the PR
  description's own list) that `make review` reads and the cutover procedure copies,
  so a squash cannot drop them.
- Run the reviewer again on a layer after its fixes land and after every cascade
  (`ROUNDS=2`, or a second `make review` on the new head), and give it the previous
  round's threads as input.
- Give the QueryStore reviewer the consumer's router and ADR decisions in its brief, and
  the ChartSearchAI reviewer the QueryStore contract, when a layer touches the boundary.
- Add a line-removal pass to the reviewer brief for every new test: name the production
  line each test fails without.
- For the state-machine layers (bootstrap, sync, cold touch, REST parameters), brief the
  reviewer with the explicit restart, resume, empty-input and cap cases to walk.

None of these are applied yet; they are the owner's call, as is the order of fixes.
The QueryStore stack merges first, so its five blocking threads (#94 resume, #95 walk
and blank patient, #97 two cues) come before anything else.
