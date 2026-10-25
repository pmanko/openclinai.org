# Cutover to gh-stack stacks on the OpenMRS repositories (21 October 2026)

Evidence for the cutover item of [openmrs-contribution.md](../openmrs-contribution.md).
The three fork-based PR sets (QueryStore #85 to #91, ChartSearchAI #583 to #590 with
fork #35, frontend #55 to #59) are replaced by one stack per OpenMRS repository, each
layer a branch named for what it does, one squashed commit per layer, each PR targeting
the layer below. The old fork branches and closed PRs stay as the record of the first
three review rounds.

## What was done

1. Each old PR's commits were squashed onto the layer below with `git rebase --onto`
   and `git reset --soft`, then committed with a message written for the layer
   (`work/review/stack-msgs/<repo>/`). Layer order follows the dependency order, which
   put the three small QueryStore fixes (#89, #91, #90) below the REST slice they used
   to sit on top of.
2. The full suite ran at every layer before the first push
   (`work/review/stack-suites.sh`, summaries in `work/review/{qs,csai,esm}-stack-suites.txt`):
   QueryStore 504 to 635 tests, backend 3646 to 3872, frontend 515 to 724, all green.
3. `gh stack init` adopted each stack and `gh stack submit --remote upstream` pushed the
   branches and opened the PRs with hand-written descriptions:
   QueryStore #92 to #98, backend #615 to #623, frontend #72 to #76.
4. The old PRs were closed with one line naming the replacement
   (85→95, 86→96, 87→97, 88→98, 89→92, 90→94, 91→93; 583→615 … 590→622, fork 35→623;
   55→72 … 59→76).
5. The umbrella's push hook now refuses only a remote's default branch and a
   non-fast-forward over a head the local branch never saw; the earlier refusal of every
   OpenMRS remote is gone because the stacks live there.

## What the replay lost, and the check that caught it

Reordering layers replayed history. Old #85 contained a commit that moved a fix out to
#89; replayed above the new position of #89's content it deleted that content again:
the unit-vector test fix and the query-cache separator escape. The pre-push probe caught
the first (the integration test fed a zero vector), and a scratch merge of every old head
onto `main` diffed against the new stack top caught the second (`'\u0000'` had become a
raw NUL). Both were restored in `patient-record-rest` before the first push.

The same scratch-merge diff was run for all three stacks before pushing. Frontend:
identical. Backend: only the intended differences (the paired-build pin, one dropped H2
test, one resolved conflict). QueryStore: only the separator, restored. The check is now
a working rule in the contribution spec: after any restack that replays history, diff the
new top against the old heads merged onto `main`.

## Fresh-reviewer round

`make review PR=<n> REPO=<repo> AGENT=codex EFFORT=medium` ran a Codex reviewer on every
layer of the three stacks at its first pushed head (findings in
`work/review/<repo>-<pr>/round-1.md`, prompts and reviewer transcripts beside them).
Each fix landed in the owning layer with a fail-first test and the push hook's revert and
mutation probes; the layers above were rebased and resubmitted.

| PR | Finding | Disposition |
| --- | --- | --- |
| frontend #72 | no test for deltas after `answer_done` | test added, b97ee88 |
| frontend #74 | a citation group wrapped across a line loses its links | fixed, 628fec8 |
| frontend #75 | every profile unavailable never retries; a failed provider request hides the selector for the mount | both fixed, af4beaa |
| frontend #76 | New chat response discarded when the opening panel closes; pending guard per panel while requests are shared; Copy drops tables | all fixed, a4e76e2 |
| QueryStore #93 | version conflict on delete is not retried; a partial search reads as completion | fixed, 509ae63 |
| QueryStore #93 | a document reassigned to another patient at the same version | declined in the commit body: the index key carries the patient, a same-version rewrite cannot move it |
| QueryStore #94 | the entity captured for the worker can change before serialization | fixed: serialized on the committing thread, 8ea48c7 |
| QueryStore #94 | equal audit timestamps do not prove equal content | declined in the commit body: the stored version is the audit timestamp by design (Decision 12); a changed record carries a new one |
| QueryStore #95 | the fingerprint collapses `1` and `"1"` | fixed with a scalar kind tag, 0aa42bd |
| QueryStore #95 | which tests pin allergy and diagnosis dates | tests added, 0aa42bd |
| QueryStore #95 | `COMPLETED` can hide skipped records | open item for the owner in the contribution spec |
| QueryStore #96 | a one-character namespaced code is rejected; an identifier prefix takes the exact tier | both fixed, fd97a9b |
| QueryStore #97 | standalone "recent" is not a recency cue; the panel test passes on unchanged input | both fixed, 84b1676 |
| QueryStore #98 | the simulated backend ignores the requested limit, so dropping the deeper fetch passes | test fixed, 4d49961 |
| backend #616 | the startup idle timer unloads the server right after a first call longer than the interval | fixed: the callback re-checks inactivity under the lock, d8f5da3ee |
| backend #617 | a dose with no frequency reads as a checked daily ceiling; a damaged allergen entry never limits the check | both fixed, 604de3906 (Greptile raised the same two) |
| backend #618 (Greptile) | a stale turn copy reopens a settled turn; concurrent opens split history; the fallback audit loses bundled measurements; an audit purge failure skips the chat purge | all fixed, 2a7a2fd42 |
| backend #619 | the prewarm sweep stops at one truncated chart as if the index were unfinished | fixed: the exception carries its reason, 137af6661 |
| backend #619 | optional records are not rebuilt with the injected size reserved | declined: the composed-path tests in `LlmInferenceServiceModuleBudgetContextTest` drive the rebuild; the probe wired the counter into the builder only |
| backend #620 (Greptile) | a client gone at answer_done loses the retained answer | fixed, 20c27ba75 |
| backend #620 (Greptile) | the stored payload lacks references and statements | handled by #622's `withTurnMetadata` before storage |
| backend #621 (Greptile) | a cancelled turn whose stream ends cleanly loses its answer; profile discovery can block forever past the headers | both fixed, 18529e8fc |
| backend #622 (Greptile) | a failed checked-answer save is handled as a disconnect and the client gets nothing; an older turn registering late cancels a newer one | both fixed, a540ea99b |
| backend #622 (Codex question) | the discovery handlers are tested only through their payload helper | handler test added, 0f0734b87 |
| backend #623 (Codex, Greptile) | the bundled provider does not pass the account snapshot into inference, though the description says "the model" | open item for the owner in the contribution spec |
| backend #623 (Codex) | a test added on #622 did not compile against this layer's signature | fixed inside the layer's commit |
| backend #616, #619, #620, #621, #622, #623 (Greptile) | tests use fakes against the repository's "real pipeline" rule | owner's call; reply drafts hold the composed-path coverage each layer has |
| QueryStore #92, backend #615 | no findings | |

GitHub's Greptile bot also commented on the new PRs. Its findings on frontend #75 and
#76 duplicated Codex's; on #74 it found wide tables spilling out of the bubble, fixed in
374daf6; on #72, #73 and #75 it reported the chat, model and provider routes missing from
the published backend, which backend #622 adds. Reply drafts for every bot thread are in
`work/review/greptile-replies.md`, to be posted on the owner's approval. The backend
layers #619 to #623 are still under review at the time of this record.

## State at the end of the record

Stack tops after the fixes: see the umbrella gitlinks (`targets/querystore`,
`targets/chartsearchai`, `targets/chartsearchai-esm`), which point at the tops. The
backend's paired build is pinned to the QueryStore top; the required build compiles
against QueryStore's published `main` and fails from `context-budget` (#619) up until
#95 to #97 merge, as the contribution spec records.

Not done here: the local boot check of the three tops (fresh setup, restart with data,
module upgrade from the previous heads' database), the gate threshold decision, and the
maintainer's review of the new PRs.
