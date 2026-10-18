# Track A upstream sync (17–18 October 2026)

All three [OpenMRS contribution](../openmrs-contribution.md) stacks were rebased on
current upstream, the reviewer's (dkayiwa) requested fixes were applied in their
owning layers where finished, and every head was published to the pmanko forks with
pinned leases. This record lists the published heads, what was checked and what
remains open.

## Published heads

| Project | Upstream base | PR | Head |
| --- | --- | --- | --- |
| QueryStore | `63b3cef` | split of #68: `codex/patient-record-rest` | `c30b660` |
| | | `codex/context-slice` (ADR 17) | `709511f` |
| | | `codex/question-interpretation` (ADR 18) | `844dcd0` |
| Frontend | `c2b6bf4b` | #55 `codex/chat-stream-client` | `14e9bb8a` |
| | | #56 `codex/chat-session-history` | `ac7f4384` |
| | | #57 `codex/answer-presentation` | `9ee0a596` |
| | | #58 `codex/provider-selection` | `4b3811c9` |
| | | #59 `codex/conversation-lifecycle` | `3f92411f` |
| Backend | `9baba552` | #583 `codex/provider-contract` | `f9cde450` |
| | | #584 `codex/local-token-counting` | `88eb01d1` |
| | | #585 `codex/safety-check-status` | `203251b0` |
| | | #586 `codex/conversation-storage` | `8782a101` |
| | | #587 `codex/context-budget` | `0c6ea150` |
| | | #588 `codex/bundled-provider` | `c65f6a21` |
| | | #589 `codex/hub-provider` | `69600dca` |
| | | #590 `codex/conversation-endpoints` | `f588d059` |
| | | fork #35 `codex/account-context` | `76e70daf` |

The backend heads are the review fixes described below, restacked onto upstream
`9baba552` (see the last section). On 18 October every backend and frontend PR head on
GitHub matched the table, and
each PR's base was its predecessor's branch (#583 and #55 on `main`; fork #35 on
`codex/conversation-endpoints`). QueryStore #68 still points at
`harness-integration` `286993cc`; the three split branches are pushed but have no
PRs yet. The umbrella QueryStore gitlink records `844dcd0`, the source the backend
stack was tested against.

## What changed in the backend restack

- #583 rejects `answer_validation`, `evidence_updated` and In-Depth events that
  arrive without a preceding `answer_done`, with a conformance test.
- #584 counts the exact inference messages on llama.cpp's
  `/v1/messages/count_tokens`, which the shipped b8850 serves. The real-model test
  is opt-in (`-Dchartsearchai.test.tokenCount.enabled=true`) and skips otherwise.
- #585 keeps upstream's allergy severity, spelling and non-drug-token handling
  alongside the stack's complete-drug-identity check.
- #587: upstream had grown new drug-safety predicates on `QueryScopeRouter` while
  #587 removes the unused retrieval routing (`Intent`, `matchedIntents`,
  `typedSlice`). The resolution keeps every upstream predicate and reads the
  medication, allergy, condition, program and visit cue patterns directly. Comments
  that still named `typedSlice` were updated. `docs/embedding-improvement-plan.md`
  is upstream's file: #587 deletes and restores it in the same PR, so its net diff
  leaves it unchanged.
- #588 and #590 conflicts were additive (upstream's `readAgainstTheChart` beside the
  stack's cancellation argument; both sides' controller imports).

## Checks

The backend ran `mvn -o test` (api and omod) on macOS against QueryStore
`844dcd0`, whose installed jar was byte-identical to a build of that checkout.
These are the rebase heads, before the review fixes below.

| Layer | api tests | omod tests |
| --- | --- | --- |
| #586 `2097455a` | 3,259 pass, 63 skipped | 294 pass |
| #587 `9788ee37` | 3,257 pass, 63 skipped | 297 pass |
| #588 `c6a79017` | 3,297 pass, 63 skipped | 298 pass |
| #589 `5b271b96` | 3,336 pass, 63 skipped | 299 pass |
| #590 `64ad8c7b` | 3,335 pass, 63 skipped, 1 excluded | 339 pass |
| #35 `cdba10d2` | 3,342 pass, 63 skipped, 1 excluded | 340 pass |

#587 and #588 were tested at the revisions shown; their published heads (`787cb31c`,
`dd7ce027`) differ only by restoring `docs/embedding-improvement-plan.md`.
`LocalLlmServerAuthTest.aPortHeldByAListenerThatAcceptsNothingFailsTheStart` failed
on #590 and #35 in the full run and once in three isolated reruns on #590. It is
upstream's test of upstream code that the stack does not change, and it is the
occupied-port fixture the
[7 October record](2026-10-07-track-a-remediation.md#verified-on-7-october) found
failing on macOS and passing on Linux. Those two layers were rerun with only that
test excluded.

The frontend passed 701 tests, lint, type checks, build and translation extraction
on #59; QueryStore passed `mvn clean install` on `844dcd0`. Both were reported by the
session that did that work and were not rerun here.

Upstream had created no workflow runs for the new #586–#590 heads when this record
was written. Fork #35 runs the same workflow on the stack tip `cdba10d2`
([run](https://github.com/pmanko/openmrs-module-chartsearchai/actions/runs/39108816912)):
the paired-source builds pass on Java 11, 17 and 21, as do the MariaDB demo seed,
the harness self-tests and the shell lint. The ordinary builds and the
QueryStore-HEAD build fail to compile on the missing `ContextSliceRequest` and
`ContextSliceRecord` symbols: the open dependency item, unchanged since 7 October.
The paired job builds against QueryStore `286993cc`, which lacks only
`SearchRequest.withLimit` among `844dcd0`'s new public API, and the stack does not
call it. No deployment or runtime smoke is claimed.

## Review fixes

The open threads on #586–#590 were answered with fixes in the owning layer, each
test written to fail first where the behavior was wrong:

- **#586:** `startTurn` refreshes a conversation the session already holds under the
  lock, so one closed by another request is rejected rather than reopened. The unused
  conversation `title` column is removed from changeset `chartsearchai-010`, and a test
  checks that every column the conversation tables declare is mapped.
- **#587:** on the Docker path `backend-init.sh` turns QueryStore autostart on
  whenever the embedder verifies; the README states that chart search needs a completed
  bootstrap and how to run one; the incomplete-chart message sends the clinician to an
  administrator. The allergy-cue comment states its safety reason.
- **#588:** six test doubles overrode a safety-check overload production no longer
  calls; they now stub `validateWithStatus`, which a throwing probe showed is reached.
  Where the module's reference records push a query-scoped prompt over the input
  budget, the slice is rebuilt with their size reserved, so only optional records give
  way. The context-size docs state the 4096-token answer reservation.
- **#589:** a Hub response arriving after a cancel is closed (the Java 11 case);
  rejected Hub requests log their HTTP status, and Hub or parser text stays at DEBUG.
- **#590:** the token-counting README section is back in the base's place; the five
  conversation endpoints are listed in ADR Decision 11, `ONBOARDING.md` and the README
  privilege table; tests cover `/chat/stream`'s pre-stream 400, 404 and 429 responses
  and `/chat/new` with an unavailable provider.

Full `mvn -o test` on each published head, with the macOS-only occupied-port test
excluded as above, 63 api tests skipped on every layer and no failures:

| Layer | api tests | omod tests |
| --- | --- | --- |
| #586 `c809bf8c` | 3,261 | 294 |
| #587 `7a5bf4f8` | 3,261 | 298 |
| #588 `a6282486` | 3,304 | 299 |
| #589 `8b68b2fd` | 3,347 | 300 |
| #590 `eeef4d84` | 3,347 | 342 |
| #35 `13f8bd0a` | 3,354 | 343 |

Only JDK 21 was available locally, where the JDK already cancels an interrupted
exchange, so the late-response close is exercised by CI's Java 11 job alone. Hosted
checks for these heads had not reported when this record was updated. Replies on the
review threads have not been posted.

Dropping the `title` column changes changeset `chartsearchai-010`, which databases set
up from the earlier heads already applied, so those databases and any baseline built
from them need fresh setup.

Still open: #587's Decision 28 finding (the kidney-cell retrieval loss belongs in
QueryStore's ranked-search preprocessing, with the new composition recorded in Decision
28), and #587's temporary paired-source job, which waits on a published QueryStore API.
The audit's remaining non-thread observations (no test running changeset 010 itself,
an interrupted bundled turn auditing its search mode as unknown, an incomplete chart in
chat reported as a generic provider failure, and the module's safety cues copying
QueryStore's interpretation cues) were not changed.

## Restack onto upstream `9baba552`

Upstream `main` took 19 direct commits during this work (ADR Decisions 304–322, all
drug-safety answers from findings); it carries no merge commits, so it moves about once
an hour on active days. The stack was then restacked with `gh stack rebase`, after
fast-forwarding only the local `main` (`gh stack` reads its trunk from the fork, whose
`main` was left unchanged), and pushed with `gh stack push`. The rebase raised no
conflicts, although `QueryScopeRouter`, `DrugReferenceInjector` and `docs/adr.md`
changed on both sides. The stack tip
`76e70daf` passed 3,380 api tests (63 skipped) and 343 omod tests with the occupied-port
test excluded; GitHub showed every PR on the heads above with its predecessor as base.

The full suite then ran on each lower layer at its restacked head, with the same
exclusion. Every layer passed with no failures or errors:

| Layer | Head | api tests (skipped) | omod tests |
| --- | --- | --- | --- |
| provider-contract | `f9cde450` | 3,244 (62) | 294 |
| local-token-counting | `88eb01d1` | 3,249 (63) | 294 |
| safety-check-status | `203251b0` | 3,265 (63) | 294 |
| conversation-storage | `8782a101` | 3,287 (63) | 294 |
| context-budget | `0c6ea150` | 3,287 (63) | 298 |
| bundled-provider | `c65f6a21` | 3,330 (63) | 299 |
| hub-provider | `69600dca` | 3,373 (63) | 300 |
| conversation-endpoints | `f588d059` | 3,373 (63) | 342 |
