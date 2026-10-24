# Round 9: the maintainer's 24 October comments and the stale pin (24 October 2026)

Evidence for [review-process.md](../review-process.md). On 24 October Daniel left five
comments: one on QueryStore #96 and four on backend #617, four of them blocking. Three Codex
findings on Hub #36 and #37 were still open, and the backend's paired build pinned a
QueryStore commit that no longer exists. Reply drafts: `work/review/round9-replies.tsv`.

## Changes

| PR | Comment | Commit | Test |
| --- | --- | --- | --- |
| QueryStore #96 | Bound the single-quote loops of `QUOTED_PHRASE` | efaf6ca | `ContextSliceTest#aLongSpanAfterAnOpeningSingleQuoteDoesNotOverflowTheStack`, on a 1 MB thread stack, both quote styles |
| Backend #617 | "100 mg per kg" read as a total | a98eae2a0 | `DrugSafetyStatusTest#aDoseInMilligramsPerKilogramSpelledOutIsNotAssessed` |
| Backend #617 | "1,500 mg" read by its last group | 2a584b5ef | `#aDoseWithAThousandsSeparatorIsNotAssessed`, `#aCeilingRecitedAsAMaximumOfAnAmountIsNotAStatedDose` |
| Backend #617 | A volume of a suspension read as the strength | 85e91349c, b817736ea | `#aDoseGivenAsAVolumeOfAStatedConcentrationIsNotAssessed`, `#aVolumeWithoutAConcentrationOrAsACeilingIsNotADose` |
| Backend #617 | README: `unavailable` carries one or more codes | 34ed00efe | none (documentation) |
| Backend #619 | Paired build pinned the vanished 28f2082 | pin moved to 118c608, #98's new tip | CI |
| Hub #36 | Fast profile streamed a pending In-Depth after grounding | c8b0de7 | `test_a_profile_without_in_depth_streams_no_pending_in_depth[reviewed]` |
| Hub #37 | An endpoint override discarded an error on another assertion | 25f61f0 | `test_answer_review_keeps_an_error_on_an_assertion_beside_a_confirmed_endpoint` |
| Hub #37 | "and" after a change verb merged two items into a range | dfa3026 | `test_citation_clusters_keep_an_item_after_a_change_verb_apart_when_no_second_endpoint_follows` |

Every new test failed before its fix. A mutation probe of each changed pattern or branch
made a named test fail.

## Suites

| Head | Result |
| --- | --- |
| QueryStore retrieval-diversity 118c608 (#98) | 631 api and 65 omod tests pass, 2 skipped |
| Backend safety-check-status (#617) before the reviewer fixes | 3,453 api and 297 omod tests pass |
| Backend account-context ccb95a525 (#623) | 3,612 api and 362 omod tests pass |
| Hub label-checks dfa3026 (#37) | 724 tests pass |

`LocalLlmServerAuthTest#aPortHeldByAListenerThatAcceptsNothingFailsTheStart` failed in one
full run of the #623 top, and failed two of three single runs on an unchanged tree.
Nothing in this round touches it. It is a timing-dependent test on this machine.

## Local reviewer decisions

Codex at medium effort, on the new commits of #96 (`work/review/querystore-96/round-1.md`)
and #617 (`work/review/chartsearchai-617/round-1.md`).

| PR | Finding | Decision |
| --- | --- | --- |
| #617 | Blocking: a concentration with "millilitres" hid the volume dose | Fixed, b817736ea |
| #617 | The ceiling test did not check the warnings | Fixed, 8ecf71ba5; read as a dose, the recited ceiling raises a 16,000 mg/day overdose warning |
| #617 | A comment omits `validateWithStatus` among the callers naming a scope | Fixed, d90304700 |
| #617 | Accept "maximum daily dose 4,000 mg" and longer ceiling phrasings | Kept: these report `limited`, the safe direction; a wider cue could hide a stated dose |
| #617 | Another quantity ("protein 20 g", "10 ml of water") limits the check | Kept: `limited`, the safe direction |
| #617 | A concentration with a frequency and no volume is read as a 500 mg dose | Deferred to the next dose-parsing change; not in the maintainer's comments |
| #617 | The range look-behind caps spacing at ten | Kept: Java look-behind must be bounded, and eleven spaces gives `limited` |
| #617 | Run two status checks concurrently | Deferred: this round adds only static patterns, so it does not change what two calls share |
| #96 | Document the 200-character single-quote cutoff and test its boundary | Deferred: the comment says the loops are bounded; the exact length is not a contract |
| #96 | Seven questions on older parts of #96 | Carried to the next #96 change; none is about this round's commit |
