# Hub confidence regression: diagnosis, 22 October 2026

This is a dated diagnosis of the drop in the Med-Agent Hub's answer and In-Depth confidence between
the July 13 Hub 12B checked-profile run and the October L5 full evaluations. It is evidence and a
proposal for the next round, not an acceptance decision. Per-scenario data is in
[2026-10-22-hub-confidence-regression/scenarios.json](2026-10-22-hub-confidence-regression/scenarios.json).

## Summary

On the 12 single-turn scenarios shared by the three runs, the Hub's settled confidence was:

| Run | Hub | Answer red | In-Depth red | In-Depth delivered |
|---|---|---|---|---|
| 13 Jul ([published](https://reports.openclinai.org/hub-profile-12b-checked-candidate-2026-07-13/dashboard.html), run 8e1291c4) | about 7869c62 | 0 (11 green, 1 yellow) | 2 | 6 of 12 |
| 20 Oct L5 (run 2cfd655d) | 49e4201 | 3 | 7 | 6 of 12 |
| 21 Oct L5 (run e936a4ab, in progress; all 12 captured) | 49e4201 | 4 | 7 | 5 of 12 |

October values are the Hub trace's own confidence for each turn. The regression is real for answer confidence and for In-Depth confidence. It is not new in this
round: 20 Oct and 21 Oct match, and both differ from July. The main findings:

1. **Most of the In-Depth "regression" is a change in what red means, not less In-Depth.** July and
   20 Oct delivered In-Depth content on the same number of scenarios (6 of 12). July labelled an
   empty In-Depth (gate `needs_review`, no claims kept) green on 5 cells. Since Hub 5368b02 (25 Jul),
   any `needs_review` In-Depth is withheld and marked red with "In-Depth was withheld because evidence
   checks rejected every claim", including turns where the model wrote no claims at all (9 of 22
   withheld turns on 20 Oct, mostly abstention and conversation turns, where adding nothing is correct).
2. **The Hub's In-Depth was redesigned to fail closed.** 5368b02 changed the In-Depth prompt from "2 to
   4 claims" of WHO and guideline context ("the most valuable part of the response") to "1 to 3"
   chart-only claims, at most one for a point lookup, guideline text only with a KnowledgeReference
   record, and an empty list whenever a claim is not fully supported. The same change made the In-Depth
   citation check reject a claim whose citation is unsupported or could not be checked within the
   grounding limits. With usually one claim, any single rejection withholds the whole In-Depth.
3. **Answer reds come from two new or changed checks, one of them often wrong.** A blocking answer
   `citation_grounding` check (5368b02) turns cells red; on am-orders-6mo it caught a real
   misattribution (an Efavirenz order [34] cited for trimethoprim and sulfamethoxazole), on ek-growth
   it looks like a source-set scoping false positive. On date-zabella-weight-endpoints the answer was
   correct and identical to July's (74 kg on 2025-10-13 [350] is the earliest weight in the window),
   but the LLM answer review flagged it as wrong, and its retry then flagged a typo date ("2016-01-26")
   in its own rewrite, so the turn ended red. July's review passed the same answer.
4. **The Hub now sees a much narrower chart.** July's Hub ranked the whole QueryStore ledger and
   filled its budget (174 to 276 records). Since 5368b02 the Hub consumes QueryStore's question-scoped
   context slice and drops every record outside it as `zero_relevance`, even with about 3,000 tokens
   unused (43 to 100 records). This is confirmed but not shown to cause the reds: for the three weight
   questions every weight observation was still included.
5. **The signal is noisy.** Between 20 Oct and 21 Oct (same Hub, same context sizes), In-Depth
   confidence flipped on 8 of 19 turns, 4 of them with byte-identical answers, and 9 of 19 answers
   differed at temperature 0. Twelve scenarios cannot size the regression precisely.

## Measurement gaps

- **Harness capture (fixed).** The harness kept only the `answer_done` envelope and stored the whole
  `indepth_done`/`indepth_error` payload as the In-Depth, but ChartSearchAI streams those events with
  the full settled envelope, the real In-Depth nested under `inDepth`. Captures therefore showed the
  In-Depth equal to the answer (34 of 35 Hub turns on 20 Oct, all on 21 Oct), answer validation stuck
  at `checking`, and no In-Depth confidence. The capture function dates from 24 September, which fits
  the June and July captures being right (gemma-quant-curve's In-Depth is present on about half the
  turns and never equals the answer). Fixed in validation-harness e52b2ed on `review-checks`, "Keep the
  settled turn envelope ChartSearchAI streams after answer_done", tested by
  `evals/validate/test_client.py::test_chat_keeps_the_settled_envelope_the_later_events_carry`.
  Existing captures are recoverable: the settled envelope is at `response.inDepth` and the real
  In-Depth at `response.inDepth.inDepth`.
- **The 20 Oct L5 report.** Its Hub answer scores are mostly sound: the judged answer is the
  `answer_done` answer, which matched the settled answer on 34 of 35 turns (am-weight-trend was
  rewritten by the temporal gate after `answer_done`). Its In-Depth and validation content is not:
  the judge and the dashboard saw the answer repeated as In-Depth, validation as `checking`, and no
  In-Depth confidence. Its harm flag on the Hub arm (ek-growth) concerns the answer and stands.
- **Trace retention.** The run directory's `trace.jsonl` is empty for 20 Oct; the Hub's own trace
  (`artifacts/hub-trace/trace.jsonl`, from 2 October) holds both October runs and joins to results by
  question and time, not by request id (ChartSearchAI issues its own). The July run directory is not
  on this machine; only its frozen dashboard is.
- **Report fields.** The dashboard and report show no In-Depth gate status, no withheld cause and no
  distinction between "nothing to add" and "rejected", so a reader cannot tell a correct abstention
  from a failure.

## Root cause by hypothesis

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| 1 | The request path changed (Hub retrieval vs ChartSearchAI context) | Confirmed, Hub-side | In both July and October the Hub reads QueryStore itself; ChartSearchAI supplies no chart. Since 5368b02 the Hub also fetches QueryStore's context slice (`mode=context`, `interpret=true`, ADR Decision 17) and `_ranked_records`/`select_context` exclude every non-slice record as `zero_relevance`, and the recent-record heuristic is switched off while a slice is active (`server/context_sources.py`) |
| 2 | QueryStore retrieval (#96 slice, #97 interpretation, #88/#98 diversity) starves trend and history claims | Ruled out for the October difference and the weight cells; unresolved for July to October | 20 Oct (QueryStore d61c14d, which already has the diversified similarity tier) and 21 Oct (#98) give the same context sizes per scenario. All 11, 11 and 7 weight observations were included for the three weight questions (Elasticsearch lookup of included and excluded ids). Whether the slice contract itself costs answers needs experiment E1 |
| 3 | Hub changes since July | Confirmed, primary | 5368b02 (25 Jul): In-Depth prompt narrowed, fail-closed In-Depth citation checks, `needs_review` mapped to withheld and red, blocking answer `citation_grounding`, slice-only selection. c290367 (17 Oct): review and In-Depth stages reuse the answer's records and the records move ahead of the instructions; July selected context per stage |
| 4 | Context budget or window truncation | Ruled out as truncation; structural constraint found | Inputs stay under the 20,480-token limit (24,576 window minus 4,096 output). July's trace shows about 15,500 fixed tokens (instructions, temporal facts) and about 27 tokens per record, so only about 5,000 tokens are left for records: about 180 records, while a 320-record chart needs about 8,800 |
| 5 | Engine, parity tap or sampling knobs | Unresolved, low | Same gemma-4-12b, temperature 0, 24,576 context in all runs; the router now sets `swa-full` for prompt reuse; the tap is a passthrough. The run-to-run variance (finding 5) is unexplained and may come from prompt caching or batch effects |
| 6 | ChartSearchAI does not handle the Hub's advanced features | Ruled out as the cause; the measurement gap was the harness | The backend relays the settled envelope (seen in the captures). The ESM merges every later envelope (`applyTurnEnvelope`: confidence, answerValidation, nested inDepth) and renders `confidence.in_depth`, `needs_review` and `edited`. The capture gap was in the harness and is fixed |

## Product gaps in handling the Hub's advanced features

- **Hub:** "no In-Depth to add" and "In-Depth rejected" share one red state and one misleading note.
  An unchecked citation (grounding limits) is treated as a rejection. A single rejected claim withholds
  the whole In-Depth, and the Hub re-synthesises only after a validator drop: none of the 10 October turns whose
  In-Depth failed a citation check had an `indepth_resynth` step. The answer review can override a correct answer, and
  a review rewrite can introduce a date that is not in the chart.
- **Harness and reports:** fixed capture (above). Still missing: In-Depth gate status, withheld cause
  and delivered/empty/withheld counts on the dashboard, report and judge cells.
- **ChartSearchAI:** no defect found in relaying or rendering. Its panel shows whatever red the Hub
  sends, so the Hub's semantics decide what a clinician sees. One observation to verify, outside this
  regression: the Hub reads QueryStore with its own configured account (`QUERYSTORE_USERNAME` is set in
  the container), so QueryStore's per-user withholding from #96 may not apply on the Hub path.

## Proposed remediation for the next round

Ordered by impact on what a clinician sees. None of these is implemented.

| # | Change | Owner | Size | Verify |
|---|---|---|---|---|
| 1 | Give an empty In-Depth (no claims written) its own neutral state and note, distinct from "withheld after rejection" | med-agent-hub `server/engine.py` (In-Depth gate and confidence) | S | Unit test per state; rerun the 12 scenarios: no red In-Depth on cells whose synth wrote no claims |
| 2 | Treat an unchecked citation (grounding limits) as yellow, or raise the limit, instead of rejecting the claim | med-agent-hub `server/engine.py` | S | Test with a stubbed unchecked verdict; am-last-visit In-Depth delivered |
| 3 | Re-synthesise the In-Depth once with the citation-check feedback before withholding, as the validator path already does | med-agent-hub `server/engine.py`/`team.py` | M | Trace shows `indepth_resynth` after a citation failure; delivered In-Depth rate on the 12 scenarios |
| 4 | Answer review: check earliest, latest and endpoint statements against the temporal facts ledger before the LLM review can flag them, and reject a rewrite whose dates are not in the chart | med-agent-hub `server/team.py`, temporal gate | M | date-zabella-weight-endpoints stays green; test with the recorded review output |
| 5 | Check the answer `citation_grounding` source-set scoping for claims that span several citation groups (ek-growth) | med-agent-hub grounding | M | Replay the ek-growth claim; keep the am-orders-6mo misattribution caught |
| 6 | Report fields: In-Depth gate status, withheld cause, delivered/empty/withheld counts in the dashboard, report, judge cells and the L5 summary; re-render the 20 Oct and current runs from the recoverable envelope | validation-harness (report, dashboard, judge-prep); umbrella `review/bin/review.py` | M | The 20 Oct report shows the real In-Depth and validation |
| 7 | Measure variance before sizing the regression: three repeats of the 12 scenarios per arm, and report the per-cell flip rate | umbrella L5 (`make review FULL=1` with a repeat count) | S | Flip rate recorded in a dated review |
| 8 | Decide the context policy with data: fill unused budget after slice records, and consider a larger 12B window so whole charts fit | med-agent-hub `context_sources.py`; umbrella `scripts/llama-router.ini` and Hub `levels.yaml` | S to M | Experiments E1 and E2 |
| 9 | Decide what In-Depth is for: chart-only context (current) or the guideline context July produced; the current prompt removes most of what July's In-Depth offered | Product decision; med-agent-hub prompt | S | Agreed definition, then the 12 scenarios |
| 10 | Verify and, if confirmed, scope the Hub's QueryStore reads to the requesting user | med-agent-hub `querystore_client.py`, ChartSearchAI account context | M | A user without Get Allergies sees no allergy record through the Hub |

## Decisions, 22 October

- Items 1 and 2 are in med-agent-hub 96cb4de: an In-Depth whose synthesis wrote no claims is
  complete and empty (`validation.status` "no_claims"), and a reviewed claim whose citation could
  not be checked ships with a yellow caution.
- Items 3, 4 and 9 are taken together as one principle: validators label, they do not hide or
  regenerate. In med-agent-hub 99a7a0d the answer reviewer's verdict leaves the answer as written
  with a yellow note, and an error it reports on an earliest or latest statement the dated series
  confirm is set aside (the weight-endpoints case). The In-Depth is written and reviewed once;
  every claim is shown, and a claim a check questions carries a note naming the check, red for a
  date or grounding contradiction or a citation outside the chart, yellow for a review flag, an
  unchecked citation or uncited general guidance. The In-Depth prompt again asks for knowledge-base
  and guideline context applied to the patient. The deterministic date gate keeps its patch.
- Item 5: the replay showed citation grounding split "from 65.5 cm [253], [214] to 67.0 cm [20],
  [71]" at the second citation, so the two 65.5 cm records were asked alone to support an upward
  trend. med-agent-hub 169dd8f checks a range or change cited at both ends against both ends.
- Item 10 is deferred and flagged as a future security and parity fix: the Hub reads QueryStore
  with its own account, so QueryStore's per-user withholding does not apply on the Hub path.
- QueryStore's top-up behaviour (answers withheld, or a chart read before the top-up has
  re-walked the records written while down) is out of scope for the L5 rerun and needs its own
  analysis.
- Items 6, 7 and 8 and the controlled experiments stay follow-ups.

## Proposed controlled experiments (not run)

The L5 run was still in progress (55 of 70 rows), so none of these ran.

- **E1, slice vs full ledger:** the 12 scenarios on Hub 49e4201 with the slice-only selection and with
  the July behaviour (ranked fill to budget), same QueryStore and engine. Answers whether the narrow
  context costs answers or In-Depth.
- **E2, window size:** the same with the 12B context at 32,768 so the full chart fits; compare
  delivered In-Depth and answer reds.
- **E3, Hub bisect:** the 12 scenarios on 7869c62, 5368b02, c290367^ and 49e4201 against the same
  stack, to attribute the change per Hub commit.
- **E4, determinism:** one question sent twice in a row to the Hub with prompt caching on and off, to
  explain the temperature-0 variance.
- **E5, re-judge:** re-run judge-prep and the judge on the 20 Oct run with the recovered In-Depth, to
  see the In-Depth scores the report never had.

## How this was measured

The July values come from the frozen dashboard's embedded status and detail data; the October values
from the Hub trace joined to the harness results by question and time. Context counts, include and
exclude reasons and fixed token counts are the Hub's own context step. Weight coverage used a
read-only Elasticsearch `_mget` on `querystore_obs`. Nothing was changed on the stack. Scripts are in
the umbrella's `work/review/hub-regression/`.
