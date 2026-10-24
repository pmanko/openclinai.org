# Why the maintainer's 23 October round was not caught locally (23 October 2026)

Evidence for [review-process.md](../review-process.md). On 23 October Daniel left 23 review
comments on the three stacks (QueryStore #93 to #98: 12, backend #618 to #625: 6, frontend
#72 to #76: 5) and asked for #617's merge conflict to be resolved. This record says why
our local review and pre-push probes did not surface them first, and the process changes
that follow. Full comment text: `work/review/round8-new-comments.md`.

## What the local tooling had seen

The last reviewer runs were on 21 October (QueryStore 19:19 to 20:04, frontend 20:13 to
21:18, backend 21:27 to 22:33), on heads that already held most of the code these comments
are about. The round 7 push on 22 October ran the pre-push probes only. One commit,
60b9a4f2c (#625's test rewrite), was pushed without any reviewer pass.

## Why each was missed

| Reason | Count | Comments |
| --- | --- | --- |
| Our reviewer raised it, and we did not act | 3 | #619 acting on `withheldTypes` and #96 the full-chart REST page carrying it (both questions in `work/review/querystore-96/round-1.md`); #98 the limit overflow (listed "not taken on, for the owner" in [the QueryStore remediation record](2026-10-21-querystore-remediation.md)) |
| A test gap that deleting a line shows | 7 | #97 interpretation off unless asked; #95 the bootstrap seam; #93 the sweep's second pass; #620 the module-composed answer's status and the caching router's cancel; #72 no capabilities passed; #74 the `source` indexing |
| A commit no reviewer read | 2 | #625 arming the idle timer at server start; a timer firing during a call |
| An OpenMRS fact outside the diff | 4 | Orders have no `dateChanged`, so stopping one keeps its version (#94, #95); framework 5.5 to 10 write an unloaded empty session on a failed refetch (#73); core counts RECURRENCE and RELAPSE as active since TRUNK-6170 (#96) |
| A layer unsafe merged on its own | 1 | #95 asks Elasticsearch for more than 10,000 candidates; the cap arrives only in #98 |
| Documentation, description and diff hygiene | 5 | #98's description again lost two items from #88's; #618's README contradicts its audit-log section; #93 an ADR note; #97 a comment naming one consumer; #76 a formatter-only hunk |
| Behaviour older than the PR | 1 | #76 a failed turn does not settle its pending checks |

#617's conflict is not a review miss: 27 drug-safety commits landed on main on 21 to 23
October and conflict with the layer in one 18-line hunk of `DrugSafetyValidator.java`.

The brief already asks for the removal pass, the edge states and the consumer
([reviewer.md](../../review/briefs/reviewer.md) steps 5 to 7). At `EFFORT=medium` the reviewer
settles on a few findings per PR, so it removes lines for some tests, not every changed
line. The probes run only the mutations a commit names, so they cannot find one nobody
thought of. And reviewer questions stay in `round-1.md` files that no step turns into a
fix, a reply or a decision.

## Process changes

1. **Every reviewer question gets a decision before the push.** Fix, reply or defer, written
   in the round's record. Nothing is left "for the owner" without the owner seeing it.
2. **Review every head that is pushed.** Run the reviewer again after each restack, test-only
   commits included, not only at a stack's first pushed head.
3. **Delete lines mechanically, not by a model's judgment.** Mutation testing limited to each
   layer's changed lines (PIT for the Maven repositories, Stryker for the frontend), so the
   seven test gaps above are found without reviewer effort.
4. **Two more brief items.** "Would this layer be safe merged alone?" And a file of
   OpenMRS traps the maintainer has taught us (orders and `dateChanged`, the session refetch,
   condition statuses, Elasticsearch's 10,000-candidate limit, deployments that raise
   `webservices.rest.maxResultsAbsolute`), read on every run.

None of these is built yet; this round's remediation comes first.

## Local review of this round's heads

Run once on 23 October with the Codex reviewer at medium effort, on every layer this round
changed (QueryStore #93 to #98, backend #617 to #620 and #625, frontend #72 to #74 and #76),
each against the layer below; outputs under `work/review/<repo>-<pr>/round-1.md`. Every
finding got a decision before the push, per process change 1.

| Finding | Decision |
| --- | --- |
| QueryStore #93: a duplicate delete returns before the other delete's refresh | Not changed: the maintainer judged it non-blocking, and the ADR now records it |
| QueryStore #94: a same-second edit is skipped by the top-up | Not changed: kept by design with the maintainer, recorded in the ADR |
| QueryStore #94 question: the ADR's skip paragraph does not mention orders | Fixed: the sentence had been lost from the order commit and is now in |
| QueryStore #95: four completeness cases (top-up, restart, concurrent reindex, failed embedding) | Not changed: the open #95 completeness question the owner kept for further QueryStore work |
| Backend #617: a dose in mg/kg is read as a total and reported checked | Fixed: such a dose is now not assessed |
| Backend #620: the remote readiness probe waits for the whole body | Fixed: it answers on the headers |
| Backend #625: a waiting idle callback uses its own captured timeout | Fixed: it uses the last arming's, and does nothing when unloading was turned off |
| Backend #619 questions on the new withheld-types notice: stated twice after the drug-reference rebuild, left out of the budget, dropped on an empty chart | Fixed |
| Frontend #76 question: the failed-turn test held no citation at Checking, so its cleanup was untested | Fixed |
| The other questions: test gaps and wording on code older than this round, the inherited integration-coverage asks, and merge previews against the remote bases | Deferred: recorded here; none is a defect in this round's changes |
