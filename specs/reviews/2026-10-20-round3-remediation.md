# Third review round: blocking findings fixed under the review process (20 October 2026)

The maintainer's third round left twelve blocking findings across the three stacks. Each was
fixed in its owning PR with a test that fails first, under the hooks and probes of
[review-process.md](../review-process.md): every fix commit was refused at push unless its
named tests failed with the fix reverted, passed at the commit and failed under each named
mutation. The red and green lines are in the probe ledger under `work/review/ledger/`.
Nothing is posted yet; the reply drafts are in `work/review/<repo>-<pr>/replies.md`.

## Fixes

| PR | Finding | Commit | Test |
| --- | --- | --- | --- |
| QueryStore #85 | ranked pages repeat and skip records | 3913656 | `PatientRecordEndpointTest#rankedPages_areSlicesOfOneRankingWhateverDepthTheFusionWouldReorderAt` |
| QueryStore #85 | per-patient walk loops at the epoch cursor | 1221d44, 1c58775 | `TypeBootstrapperTest#runForPatient_stopsWhenAPageDoesNotAdvancePastTheCursor`, `#runForPatient_stopsWhenAStaleRowOnAPageBoundaryWouldCycleTheWalk` |
| QueryStore #90 | condition edits no longer reach the index | 1c00e37 | `ConditionEditProjectionTest` (real core `saveCondition`) |
| QueryStore #87, ChartSearchAI #587 | kidney cell | 2fb45fb; c45befbc2, ca226bd68 | `ContextQuestionInterpreterTest`, `ContextSliceTest#similarityLeg_leavesOutThePatientTheWholeChartIsAbout`; cohort re-run below |
| ChartSearchAI #586 | `finishTurn` refuses the fallback after a failed settlement | c76080082 | `ConversationServicePersistenceTest#aFallbackSettlementSucceedsAfterAFailedOneLeftTheCallersTurnMarked` |
| ChartSearchAI #588 (thread on #590) | grounding on: a departed client turns the turn into a blank error | b1fe94490 | `BundledClinicalAnswerProviderTest#aClientThatLeavesBeforeTheEvidenceEventStillLeavesTheGroundedAnswerStored` |
| ChartSearchAI #590 | XStream back-references in `/search` XML | 072a28997 | `ChartSearchAiChartOrderBridgeTest`, `ChartSearchAiCurrentMedicationOrdersTest` (no `reference=` in the marshalled payload) |
| ESM #55 | an out-of-order delta ends the turn | c1ffa4e | `chat-stream.test.ts` |
| ESM #58 | all profiles unavailable reads as a lost pick | de3b219 | `hub-profile-discovery.test.ts` |
| ESM #59 | stopped answer draws no safety box | 0188e33 | `useChartSearchAi.test.ts`, `ai-response-panel.test.tsx` |
| ESM #59 | reload shows an empty bubble for a turn stopped before its answer | 4707e94 | `useChartSearchAi.test.ts` |
| ESM #59 | closing one panel aborts the other's turn | c1bc84b | `useChartSearchAi.test.ts` |

## Where the fix differs from the suggestion

- **QueryStore #85 loop guard:** the suggested equality check was applied (1221d44), then a
  fresh reviewer run (`make review PR=85 EFFORT=medium`) showed a two-page cycle it misses: a
  half-loaded row ending a later page sends the walk back to page one at the epoch cursor.
  1c58775 requires each page to end strictly past its cursor in keyset order.
- **QueryStore #87:** general stopword stripping, as #586 did, would break Decision 18's
  qualifiers and the multilingual tests. Only "the/this/that patient" and "patient's" are
  removed; the measurement is in Decision 18 and in ChartSearchAI's Decision 28.
- **ESM #55:** dropping every out-of-order delta would break the shared conformance fixture's
  reject cases. Late reasoning and answer deltas are dropped; a preview out of order and any
  delta from a provider without `token_streaming` still end the turn.
- **ChartSearchAI #590:** the envelope gets a deep copy of the chip statements rather than a
  second serialization, because the module's guards allow one `putSafetyChips` call and one
  writer per wire key.

## Kidney cell re-run

QueryStore #88's head carrying the #87 fix (c2fce41) was deployed with `deploy-head.sh` (loaded
api jar hash matched the build) and the 40-cell October cohort re-run through the harness
(`make review MEASURE=context-cohort`), then the as-found omod restored.

| Measure | #88 before (run f5dcd8ef) | With the fix (run 2d959d32) |
| --- | ---: | ---: |
| Mean citation F1, 18 present cells | 0.761 | 0.825 |
| Absent cells abstaining | 22 of 22 | 22 of 22 |
| Off-topic citations | 0 | 0 |

Kidney cells: patient 39 one of three creatinine records cited before, two after; patients 36
and 2606 one of two in both; patient 3666 one of one in both. Patient 39's heart cell went from
0.0 to 1.0. Patient 3666's medications cell went from 24 of 24 to 5 of 24: both answers name
the same five drugs, and the second cites one order per drug instead of every repeat. One
capture per cell; the temporal probe was not re-run.

## Not done

- The non-blocking threads of the round, for the remediation PR on top of each stack.
- Rolling the umbrella gitlinks: the pinned checkouts stay on the heads the HIV baseline was
  built from until the round is approved.
- Posting replies: drafts only, on the owner's approval.
