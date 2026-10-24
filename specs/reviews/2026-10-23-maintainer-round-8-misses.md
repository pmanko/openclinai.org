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
