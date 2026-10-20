# Track A review revalidation, 19 October 2026

The ChartSearchAI maintainer re-reviewed the 18 October heads on 19 October,
between 09:37 and 20:23 UTC, and left 32 comments on eleven of the sixteen PRs. This
record checks every open thread against the code at those heads and records why
the October remediation left so much open. The plan that follows from it is the
[contribution spec's target path](../openmrs-contribution.md#target-path).

## Heads and state checked

The heads are those in the
[18 October record](2026-10-18-track-a-upstream-sync.md#evening-fixes-and-third-restack)
for the backend and frontend and in its
[QueryStore split](2026-10-18-track-a-upstream-sync.md#querystore-split) section.
None moved on 19 October. Thread state was read through the GitHub GraphQL API at
the end of the day, with no comment newer than 20:23 UTC.

| PR | Open threads before 19 Oct | New on 19 Oct | Replies drafted | Required checks |
| --- | --- | --- | --- | --- |
| Backend #583 | 2 | 1 | 0 | pass |
| Backend #584 | 1 | 2 | 0 | pass |
| Backend #585 | 3 | 1 | 0 | pass; the non-required QueryStore HEAD job failed |
| Backend #586 | 1 | 5 | 1 | pass |
| Backend #587 | 5 | 0 | 3 | ordinary builds fail on missing QueryStore symbols; paired builds pass |
| Backend #588 | 2 | 0 | 2 | as #587 |
| Backend #589 | 3 | 0 | 3 | as #587 |
| Backend #590 | 2 | 3 | 2 | as #587 |
| Frontend #55 | 5 | 0 | 0 | pass |
| Frontend #56 | 3 | 0 | 0 | pass |
| Frontend #57 | 5 | 1 | 0 | pass |
| Frontend #58 | 2 | 0 | 0 | pass |
| Frontend #59 | 10 | 1 | 0 | pass |
| QueryStore #85 | 0 | 4 | 0 | pass |
| QueryStore #86 | 0 | 6 | 0 | pass |
| QueryStore #87 | 0 | 5, plus a review-level request | 0 | pass |

That is 73 open threads. The maintainer resolved none; all 63 resolved threads were
resolved by us in the 7 October round. No reply has been posted since 7 October.
`git merge-tree` against current upstream `main` is clean for all eleven backend
and QueryStore heads. Backend upstream took 30 more direct commits (ADR Decisions
335 to 364, all drug-safety answers) since the stack base `70baf6b0`; QueryStore
upstream took one tooling commit; the frontend upstream did not move.

## Threads open before 19 October

Of the 44, 39 are fixed on the heads and need only a reply. Three were reopened by
the maintainer's follow-ups on 19 October: #585's `no_applicable_check`, #587's
bootstrap precondition and #59's backend-version line. Two were never closed out:
#587's Decision 28 evidence and its temporary paired-source job. Only 11 of the 44
have a drafted reply, all backend threads from the first fix round.

## New findings checked against the code

Every claim was checked at the stated head. All of them hold. Item 1 was
reproduced through `validateWithStatus` with two active orders and no allergy or
condition. Item 2's old checksum was recomputed under Liquibase 4.32.0. The
regexes in items 7 and 17 and the sort in item 8 were run.

| # | PR | Finding | Blocking | Fix belongs in |
| --- | --- | --- | --- | --- |
| 1 | #585 | The interaction screening flag uses a gate copied from before ADR Decision 183, so "Does zorblatine interact with any of her medications?" reports `checked` beside "No interaction check was run". The maintainer's patch was applied in a scratch worktree, and the safety-status, citation-wiring and REST-contract suites stayed green. | yes | #585 |
| 2 | #586 | Changeset `chartsearchai-010` was edited in place, so a database that ran the earlier 010 (`9:4072678082e4f5a4fecbde940616d4dd`) fails validation and the module does not start. | yes | #586 |
| 3 | #586, #590 | A Hub error after an unchecked `answer_done`, or a client dropping during bundled deltas, files an empty answer although the client received one. | yes | `finishTurn` in #586, fed by #590 |
| 4 | #587 | Every restart sets each QueryStore type back to RUNNING and re-embeds everything past its cursor, so answers return 503 for minutes. Skipping unchanged versions alone still leaves the page-scan window. | yes | QueryStore #85, plus a README line in #587 |
| 5 | QS #85 | Per-type, per-record and write failures are swallowed below `ensureIndexed`, so a failed cold touch reports `projectionComplete: true`. | yes | QS #85 |
| 6 | QS #85 | The endpoint requires only Get Patients, so it serves every type's text, and cross-patient search, to a user core would refuse (Decision 14 point 4). | yes | QS #85 service read path |
| 7 | QS #86 | The identifier pattern takes any word after "code is", so "the" becomes an exact signal. | yes | QS #86 |
| 8 | QS #87 | A concept's similarity slot goes to its best-ranked record, so "latest creatinine" can report an older value; numeric series are capped to one value per concept. | yes; the cap was asked as a question | the split-out retrieval PR |
| 9 | QS #87 | Four retrieval changes were in neither #68 nor Decision 18: the concept-diversified similarity tier, the threefold hybrid pools, the answer-concept merge and the form-prompt description filter. | requested | a new QueryStore PR |
| 10 | #588 | `IncompleteChartException` falls into the generic failure, so chat shows "Chart search failed" instead of `incomplete_chart`. | no | #588 |
| 11 | #583, #584, #585, #588 | New `##` README sections are missing from the table of contents. | no | each layer |
| 12 | #584 | The token-count refusals have no test; `isAvailable` duplicates the active-engine rule. | no | #584 |
| 13 | #585 | Neither `dose_not_assessable` branch is pinned by a test. | no | #585 |
| 14 | #586 | Zero token counts are filed as 0 rather than null; ADR Decision 105 and the audit bullet are stale; the only Mockito test in the repository passes with the lock removed. | no | #586 |
| 15 | #590 | The README does not name `safetyStatus`, `safetyCheck` or the early `done` carrying `unavailable`. | no | #590 |
| 16 | Frontend #57, #59 | A moved comment kept wording that upstream #65 removed; the README names a snapshot version; error codes are defined twice. | no | #57, #59 |
| 17 | QS #85, #86, #87 | ADR banners describe a split that has not landed; an unrelated separator change; the quote pattern pairs with apostrophes; `rank` and `chartTruncated` docs; a mapping-code test that injects its own data; seven unneeded stub overrides; Decisions 6 and 17 advisories; a misplaced javadoc. | no | the PR named in each thread |

## Why the remediation left these open

Of the 32 comments, 7 concern code or omissions from our own 17 and 18 October
fixes: 010 edited in place, autostart turned on every start, the half-fixed
`no_applicable_check`, removed tests that left the new refusals untested, and three
frontend leftovers from the move and rebase. Ten concern code from 1 to 6 October
that the maintainer had not raised before. The 15 QueryStore comments are the first
review of the split opened on 18 October.

- Fixes answered each comment's literal ask and were not checked for the same
  pattern nearby. The `no_applicable_check` fix covered the arm the maintainer
  named and not the screening arm with the same gate.
- Fixes were not reviewed for their effects on existing installations. The 18 October
  record noted that databases from earlier heads "need fresh setup" and the baseline
  was rebuilt, instead of treating the in-place edit as a module upgrade defect.
  The autostart change was proven by a fresh rebuild, never by a restart with data.
- Three observations from the 18 October audit were recorded as "not changed"
  rather than raised as open work: an incomplete chart reported as a generic
  failure, no test running changeset 010, and an interrupted bundled turn's audit.
  The maintainer raised all three.
- The 18 October thread check was made by agents told what the fixes were, and the
  QueryStore split went up without a review pass of its own.
- Replies were held for owner approval, correctly, but drafts stopped after the first
  fix round, so the maintainer re-reviewed 44 threads with no account of what had
  changed. Three of his follow-ups landed on threads a reply would have explained.

The contribution model now requires a drafted reply with each fix, an independent
review of each layer's diff before publishing, and deferred findings listed as open
items.
