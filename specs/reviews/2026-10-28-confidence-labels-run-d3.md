# Confidence labels: run D3, the bare, verify and agree arms against the judge

**Date:** 28 October 2026 · **Spec:** [confidence-labels.md](../confidence-labels.md) (L1.2, L3.5,
L7.2, L8) · **Run:** D3 `b7bccdd2` (Hub 35ef26b: #47 with the folded citation fallback), 17
scenarios, 35 turns per arm, reference date 2026-06-20, judged blind by one gpt-6-astra high
pass and one Claude Opus 5.5 high pass (headline: the median of the two), the judge reading no
check verdict and scoring every In-Depth point ([judging.md](../judging.md)). Runs D `2840496f`
(Hub #46, stopped at 86 turns) and D2 `d7c7919e` (Hub #47, stopped at 114 turns, unjudged) are
its two aborted predecessors; D2 stopped because the 9B reviewer returned no citation verdicts
in most verify turns and left the answers `unavailable` (Hub 35ef26b falls back to the separate
check when that happens).

## Judged scores

| Arm | Accuracy | Completeness | Relevance | Harm | Opus accuracy | gpt accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Built-in | 8.00 | 7.09 | 7.76 | 1 | 7.59 | 8.41 |
| Default (12B, same-model review, separate check) | 8.50 | 7.74 | 8.56 | 0 | 8.18 | 8.82 |
| Bare (deterministic checks only) | 8.71 | 7.85 | 8.65 | 0 | 8.47 | 8.94 |
| Verify (9B verification questions, citations folded) | 8.74 | 7.79 | 8.65 | 0 | 8.47 | 9.00 |
| Agree (second writer Qwen3.6-35B, claim agreement) | 8.50 | 7.74 | 8.53 | 0 | 8.18 | 8.82 |

As in every earlier run, the checks do not move the scores: bare, verify and agree sit within
noise of each other and of the default (17 cells an arm). Opus scores every arm about 0.4
below gpt-6-astra, in the same order.

## What the labels did (35 turns an arm)

| Arm | Answer status | Marks | Median turn |
| --- | --- | --- | ---: |
| Bare | 29 checked, 6 edited | deterministic: 2 single-point trend, 1 date binding, 1 window warn; In-Depth 0 of 94 points | 30 s |
| Verify | 26 checked, 4 edited, 5 needs review | 7 contradicted citations on 3 turns, 4 review flags on 2 turns, 3 of 35 In-Depths flagged; 64 In-Depth citation passes, 30 uncited | 69 s (answer 11, review 28, In-Depth 13) |
| Agree | 21 checked, 11 needs review, 3 edited | 18 claims differ on 11 turns, 23 unverified; agreement agreed 17, partly 5, differs 11, unchecked 1; In-Depth 0 of 87 | 47 s (second writer 18) |
| Default | 28 checked, 6 edited, 1 unavailable | 89 citations supported, 4 not addressed, 2 unchecked | 48 s |

The verify arm's folded citation verdicts were empty in 11 of 35 turns (4 of the first 5); the
fallback ran the separate check with the 9B in those turns at 6 to 56 s each. Verify turns in
D2 took 108 s a turn with the Hub 2x slower under memory pressure; in D3 the 12B answer stage
alone ranged from 11 s to 175 s on the same arm.

## The checks against the judge (`judges/check-precision.json`)

Answer level, 85 judged cells, 32 judged faults:

| Check | Marked | Hits | Precision | Recall | What the marks were |
| --- | ---: | ---: | ---: | ---: | --- |
| Date check | 4 | 0 | 0.00 | 0.00 | the `window_scope` warn on am-weight-trend in every Hub arm (both judges 9 and 10: endpoints correct) |
| Date check, answer patched | 4 | 4 | 1.00 | 0.12 | convo-diagnosis-evidence t5: the cell is faulted for turns 1 and 2; the patch rewrote an already correct "no trend from one point" refusal |
| Citation support | 1 | 0 | 0.00 | 0.00 | ek-growth, verify: the 9B contradicted a height trend both judges call correct |
| Model review | 1 | 1 | 1.00 | 0.03 | am-orders-6mo, verify: [5] does not hold the drug order (both judges 5) |
| Status: needs review | 7 | 3 | 0.43 | 0.09 | verify 2 marked 1 hit; agree 5 marked 2 hits |

In-Depth, 224 judged points, 48 judged wrong (26 wrong fact, 15 wrong citation, 7 unsupported):

| Check | Marked | Hits | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| Citation support | 0 | 0 | n/a | 0.00 |
| Date check | 0 | 0 | n/a | 0.00 |
| Model review (verify) | 3 | 2 | 0.67 | 0.04 |
| Any mark | 3 | 2 | 0.67 | 0.04 |

Reading: the remediated checks mark almost nothing (3 In-Depth marks across three arms, 7
answer cells), so precision is measured on a handful of items and recall is near zero. One in
five judged In-Depth points is wrong and no check sees them: the judges' faults are wrong facts
and missed records, not contradictions a citation check can prove.

## Findings per arm

- **Verify.** The verification-question review's flags were right where they were judged (1 of
  1 answer, 2 of 3 In-Depth points; the three non-final adherence flags quote the chart and read
  as right). Too few marks for LG1. The 9B as a citation checker is unusable: all 7 contradicted
  citations were false, three of them on enumeration fragments (", lamivudine", ", and stavudine
  .") that `_citation_clusters` makes into their own claims and the 12B grounds without
  trouble. The arm's review runs at temperature 0.7 (`knobs.review`), against principle 7.
- **Agree.** 0.40 precision on 5 final cells (hits: the orders table and the diagnosis
  conversation, both judged 5 and 6; misses: two "last visit" answers where the writers differ
  in wording, judged 9 and 10, and ek-growth at 7 and 8). 11 of 35 answers needs review is more
  noise than the default's reviewer produced in run C. Cheap (18 s), and agreement did not lift
  the scores.
- **Bare.** The deterministic checks are the only ones that fired in every arm, and two of
  their three kinds misfired: `window_scope` warns on a correct one-year answer whose chart
  window is shorter, and `single_point_trend` fails an answer that already says no trend can be
  drawn, binding a second measurement (white blood cells, [189]) the answer never names, then
  patches it to an equivalent sentence. The `date_value_binding` fail (4.0 bound to a weight
  date) is a real catch on a non-final turn.

## L8 refit (A2, C and D3)

`work/labels/calibrate.py` on 958 judged points (189 wrong), scenarios split in half:

| | Train (572) | Held out (386) |
| --- | ---: | ---: |
| AUROC | 0.715 | 0.725 |
| Brier | 0.152 | 0.127 |
| Expected calibration error | 0.007 | 0.074 |
| Lowest 0.8-precision cut | p >= 0.70: 14 points, precision 0.86, recall 0.09 | none reachable |

Log-odds: model review +1.58, date check +0.58, citation check -0.03, uncited point -1.43,
remediated Hub -0.72, intercept -0.57. The held-out AUROC is unchanged from the A2 and C fit
(0.757 on fewer points); the checks remain a weak classifier and no band reaches 0.8 precision
held out. The scorer's fact-level labels (L6) were not recorded in D3 (Hub #48 is not pinned),
so the fact-level decision waits for the next run with the shadow on.

## Decisions proposed to the owner

1. Verify's citation fallback uses the 12B grounding model, not the 9B: the profile gets
   `grounding: gemma-4-12b` (the engine already prefers it) and `knobs.review` goes to
   temperature 0. The 9B keeps the verification questions, whose marks were right.
2. The agree arm does not clear LG1 at 0.40 and is retired from the matrix unless the owner
   wants a wording-tolerant matcher tried first; the second-writer code stays behind its profile.
3. `window_scope` becomes an info note, and `single_point_trend` skips an answer that states no
   trend and binds only to measurements the answer names (Hub, next round).
4. LG1 and LG2 stay open with the owner; nothing in D3 reaches 50 marks on any check, so the
   bar is not yet testable on the verification review. The next judged run carries the shadow
   scorer so L6's fact-level set exists.
