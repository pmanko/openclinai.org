# Can the changed harness reproduce the maintainer's round? (21 October 2026)

Evidence for the "Measured" item of [review-process.md](../review-process.md). The
maintainer's 32 threads are inventoried in
`2026-10-21-maintainer-round-on-the-stacks.md` (remediation branch). The question here is
how many of them a fresh Codex reviewer finds under the changed brief, on the same PRs,
without having seen his comments.

## Setup

`make review PR=<n> REPO=<repo> AGENT=codex EFFORT=medium THREADS_UNTIL=2026-10-21T11:00:00Z`
on QueryStore #93 to #98 and frontend #72 to #76, run serially between 06:40 and 10:05.
The cut-off is before the maintainer's first comment (11:25), so `threads.json` held only
the bot threads already there; the replaced PRs' threads were attached (`previous`: #85 to
#91, #55 to #59), and the ChartSearchAI stack top was checked out beside each PR. Heads
reviewed were the current ones (two QueryStore layers carry a small later fix each; none
of the maintainer's findings was fixed). The first round's outputs, from the old brief,
are under `work/review/archive/codex-round1/`; this round's under `archive/codex-round2/`.

## Result

| Stack | Maintainer threads | Reproduced | Of his five blocking |
| --- | --- | --- | --- |
| QueryStore #93 to #98 | 20 | 15 | 2 (the #94 resume as blocking, the #95 walk as a question) |
| Frontend #72 to #76 | 12 | 10 | (none marked blocking) |
| Both | 32 | 25 | |

Under the old brief the same reviewer had reported one to three items per PR and none
of these 25 except the two it had raised itself (#94's snapshot, #96's fingerprint, which
were fixed before his round). Under the new brief it reports 5 to 20 items per PR and
runs 14 to 22 minutes instead of 6 to 10.

### Reproduced (25)

QueryStore: #93 index-not-found per item, ADR cascade item, displaced javadoc; #94
interrupted resync resumed with the skip, prepare-after-commit coverage, the `dispatch`
rewrite; #95 the per-patient walk re-embedding on every read; #96 withheld types,
`sliceId` drift, `continuesIdentifier` on quoted prose, the codes cap, the member-hit
test; #97 the caller's temporal flag, the preprocessing javadoc; #98 the stable-series
javadoc. Frontend: #72 the `indepth_error` test and the fixture's source; #73 the store
reset; #74 raw HTML and the `*` notation; #75 the dropped-pick retry and the unreachable
branch; #76 the second panel's lost question, the closed-PR links, the unused class.

All ten carried-over asks from rounds two and three are among them: the carried threads
did what they were added for.

### Missed (7) and why

| Thread | Why the reviewer missed it | Brief change |
| --- | --- | --- |
| #95 blank `patient` runs a cross-patient search | no probe of a blank parameter; the state list was optional and the budget went to the completeness findings | parameter cases on every effort level, one line per case in the answer |
| #97 `at last` idiom; #97 medication cues | the consumer checkout was there but the reviewer never opened the router: the step is phrased for a request contract, not a rule set kept on both sides | rule sets diffed entry by entry, consumer ADR decisions read |
| #94 the dropped ADR sentence | the #90 ask was carried and marked done; the rule covered unanswered asks only | a done ask is diffed against what was asked |
| #98 hits past the cap take a slot | the PR wrote the limitation into Decision 3 and the reviewer read it as design | a limitation the PR adds is a candidate finding |
| #74 model links rendered live | design preference, not reproducible | none |
| #74 comment line break in moved code | cosmetic | none |

The four brief changes are in the same commit as this record. A third run on #94, #95,
#97 and #98 under the changed brief follows; its result is appended below.

### Found beyond the maintainer's list

The reviewer also raised items he had not: on #93 and #94 the two it had reported before
(declined on record); on #95 three completeness findings; on #97 "patient-reported"
losing its first half when the subject is dropped; on #98 the `numCandidates` cap from
his old #88 thread, now with a reproduction; on #74 a Markdown footnote captured as a
chart citation; on #75 an unavailable provider never refreshed; on #76 a stopped bundled
answer losing its safety notice on reload and a pending New chat surviving a logout.
These are not scored here and go to the owner with the fixes.

## Third run on the missed cases

Pending.
