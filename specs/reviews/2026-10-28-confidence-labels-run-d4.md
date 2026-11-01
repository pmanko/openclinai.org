# Confidence labels: run D4 on the fixed checks, and the scorer closed

**Date:** 28 October 2026 · **Spec:** [confidence-labels.md](../confidence-labels.md) (L1.2, L3.5,
L6, L8) · **Run:** D4 `2a053c09` (Hub a34e7fa: the [run D3](2026-10-28-confidence-labels-run-d3.md)
fixes, the shadow scorer on), 17 scenarios, 35 turns per arm, reference date 2026-06-20,
judged blind by one gpt-6-astra high pass and one Claude Opus 5.5 high pass (headline: the
median), the judge reading no check verdict and scoring every In-Depth point.

## Judged scores

| Arm | Accuracy | Completeness | Relevance | Harm | Opus accuracy | gpt accuracy | Median turn |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Built-in | 7.94 | 6.94 | 7.74 | 1 | 7.71 | 8.18 | 16 s |
| Hub answer-only (12B, separate citation check) | 8.47 | 7.71 | 8.38 | 0 | 8.12 | 8.82 | 43 s |
| Bare (deterministic checks only) | 8.62 | 7.85 | 8.35 | 0 | 8.35 | 8.88 | 27 s |
| Verify (9B verification questions, 12B citation fallback, temperature 0) | 8.68 | 7.88 | 8.41 | 0 | 8.35 | 9.00 | 54 s |

The same order and spread as D3: the Hub arms sit within noise of each other, half a point
above the built-in. In five judged runs no check has moved a score.

## The checks against the judge (`judges/check-precision.json`)

Answer level, 68 judged cells, 30 judged faults: one mark in total, verify's contradicted
citation on am-orders-6mo, which both judges faulted (precision 1 of 1, recall 0.03). The D3
fixes removed every deterministic mark that misfired there: no window warning, no single-point
fail, no rewritten refusal.

In-Depth, 165 judged points, 38 judged wrong:

| Check | Marked | Hits | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| Date check | 2 | 0 | 0.00 | 0.00 |
| Citation support | 0 | 0 | n/a | 0.00 |
| Model review (verify) | 3 | 2 | 0.67 | 0.05 |
| Any mark | 5 | 2 | 0.40 | 0.05 |

The two date marks are one misfire repeated in both arms: the value binding read the 3 of
"cells/mm3" and of "a weight loss of 3 kg" as recorded values. Fixed on Hub d3-checks 34000a9
(`test_value_binding_skips_unit_digits_and_change_amounts`).

Verify's review, D3 and D4 together: 6 In-Depth marks, 4 right (0.67), and 1 of 1 answer mark
right. That is the best precision any model check has shown, at about one mark per eleven
turns; 50 marks (the proposed LG1 sample) would take about 550 verify turns, sixteen runs.

## The scorer (L6), scored offline

The shadow scorer only sees facts a prompted check listed; D4's verify arm folds its In-Depth
verdicts and listed facts for 99 Answer facts only. The decision used the facts the 12B check
listed in run C instead: `work/labels/scorer-offline.py` sent each (cited record, fact) pair
to the DeBERTa NLI cross-encoder and took, per In-Depth point, the highest contradiction and
lowest support probability over its facts. 177 points (470 facts), 117 judged, 19 wrong:

| Signal | Marked | Hits | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| Prompted citation check | 1 | 1 | 1.00 | 0.05 |
| Scorer contradiction >= 0.5 | 26 | 9 | 0.35 | 0.47 |
| Scorer contradiction >= 0.8 | 22 | 5 | 0.23 | 0.26 |
| Scorer contradiction >= 0.95 | 12 | 3 | 0.25 | 0.16 |
| Scorer support <= 0.3 | 65 | 14 | 0.22 | 0.74 |

AUROC 0.63 (contradiction), 0.65 (1 - support), the same as the whole-point replay of 28
October (0.56 to 0.66). Precision falls as the threshold rises: its confident contradictions
are facts the record does not state, not facts it states differently. No threshold comes near
0.8. Decision (owner, 28 October): L6 closes; the scorer service, its Make target, the compose
and env settings and the Hub's shadow policy are removed (Hub d3-checks 72d7dc8, umbrella).

## L8 refit (A2, C, D3, D4)

1123 judged points, 227 wrong: held-out AUROC 0.695, no band at 0.8 precision held out
(train: p >= 0.68 flags 14 points at 0.86). Log-odds: model review +1.67, date check +0.25,
citation check -0.05, uncited point -1.53. The checks' signal has not grown with the data; the
only consistent feature is the model review.

## What the five runs say together

- The answers are wrong in ways no check looks for. About one In-Depth point in five and
  about two answer cells in five are faulted, mostly for wrong or missing facts, omitted
  records and incomplete series; the checks see under a tenth of them.
- The deterministic checks are right when their rules fit and need a test for each misfire
  the runs find (three fixed from D3, one from D4).
- Model checks at this size either mark too often and wrongly (same-model review, the 9B
  citation verdicts, agreement) or rarely and rightly (the verification review).
- Checking costs time without changing what the judge sees: bare is the fastest Hub arm
  (27 s) and scores with the best.

## Proposed to the owner

1. Default profile (checked-answers A7): bare, deterministic checks only, with the
   verification review available as a hidden, measured arm (dashboard and report only) until
   it reaches the LG1 sample.
2. LG1 as written (0.8 on 50 marks over two runs); the verification review keeps running
   hidden in each round to accumulate marks. LG2 stays closed: no calibrated band exists.
3. Effort moves from checking to the answers' faults: completeness of series and windows,
   the records an answer omits, citation choice. Run B (the 31B writer) tests whether a bigger
   writer moves the judged faults that no check catches.

## Decisions (owner, 28 October)

- The default profile is `single-12b-bare` (Hub d3-checks 46a4dcd, PR #50).
- LG1 as written: a check marks what the clinician sees at 0.8 precision on 50 marks across two
  judged runs; the verification review stays a hidden arm until it has them.
- Work moves to deterministic rules for the judged fault patterns ([answer-rules.md](../answer-rules.md)).
