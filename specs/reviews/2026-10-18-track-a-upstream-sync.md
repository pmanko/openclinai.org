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
| Backend | `74bad089` | #583 `codex/provider-contract` | `7ac2eec8` |
| | | #584 `codex/local-token-counting` | `ed3ef1a4` |
| | | #585 `codex/safety-check-status` | `4f44d6ce` |
| | | #586 `codex/conversation-storage` | `2097455a` |
| | | #587 `codex/context-budget` | `787cb31c` |
| | | #588 `codex/bundled-provider` | `dd7ce027` |
| | | #589 `codex/hub-provider` | `5b271b96` |
| | | #590 `codex/conversation-endpoints` | `64ad8c7b` |
| | | fork #35 `codex/account-context` | `cdba10d2` |

On 18 October every backend and frontend PR head on GitHub matched the table, and
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

## Review fixes still open

An audit of #586–#590 against the reviewer's requests found these addressed:
retention purge of unfinished turns by `coalesce(completedAt, startedAt)`, audit
search mode and reference slice from the source answer, checked answers kept for
interrupted turns, the Hub endpoint property in `config.xml`, mode rejection before
any conversation change, and no model file path in `unavailable` reasons. Open:

- **#586:** no test runs Liquibase changeset `chartsearchai-010`; the conversation
  `title` column is declared but never mapped or used; an interrupted bundled
  turn's audit records search mode as unknown.
- **#586 decisions:** answers are withheld until QueryStore's deployment-wide
  bootstrap completes, even for a patient just projected lazily. The module's
  safety cue patterns largely copy QueryStore's question-interpretation cues, and
  `QueryPreprocessor` keeps recency patterns reached only from tests.
- **#587/#588:** the post-injection prompt check exists (#588), but the selector
  reserves no room for injected references, so overflow is refused rather than
  trimmed; the fixed recency anchor of 15 and the no-counter behavior are
  undocumented.
- **#589:** a response that arrives after a cancelled header wait is not closed;
  Hub HTTP failures are not logged by status class; one warn log and the profile
  listing can still carry remote response text.
- **#590:** no tests for `/chat/stream`'s pre-stream 400, 404 and 429 responses or
  `/chat/new` with an unavailable provider; an incomplete chart in chat reports a
  generic provider failure; the new endpoints are missing from ADR Decision 11,
  `ONBOARDING.md` and the README privilege table.
- Temporary PR-process text (the PR #68 note and the paired-build job) is still in
  the backend README and workflow.

Upstream `main` moved to `981e1f44` during this work (ADR Decisions 304–307). They
change `DrugReferenceInjector`, one context test and `docs/adr.md`, all of which the
stack also changes; restack once before requesting re-review.
