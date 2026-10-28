# Confidence labels: runs A2 and C, the checks against the judge, and a first calibrated score

**Date:** 28 October 2026 · **Spec:** [confidence-labels.md](../confidence-labels.md) (L1.2, L5.2, L8 prototype) ·
**Runs:** A2 `8dacd7b1` (Hub cd52e2d, the checks before the remediation, DRY-off arm added) and
C `e01674f6` (Hub cd92ae1, the remediated checks). Both: 17 scenarios, 35 turns per arm, the
run's reference date 2026-06-20, judged blind per scenario with the judge reading no check
verdict and scoring every In-Depth point ([judging.md](../judging.md)). Run D (bare, verify,
agree) is running on Hub 6151004 and gets its own record.

## Judged scores

A2 was judged by three gpt-6-astra high passes and one Claude Opus 5.5 high pass (headline: the
median and majority across the four). C was judged by one Opus pass; its gpt-6-astra passes
were refused by Codex (429) and dropped when the owner chose one judge run per round.

| Arm | A2 accuracy | A2 completeness | A2 relevance | A2 harm | C accuracy (Opus) | C completeness | C relevance | C harm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Built-in | 6.35 | 6.74 | 7.38 | 2 | 6.18 | 5.76 | 6.65 | 1 |
| Answer-only | 8.85 | 8.21 | 8.94 | 0 | 8.29 | 7.00 | 7.82 | 0 |
| Default | 9.00 | 8.29 | 8.85 | 0 | 8.41 | 7.00 | 7.65 | 0 |
| Folded | 8.91 | 8.09 | 8.76 | 0 | 8.65 | 7.18 | 7.82 | 0 |
| DRY off | 8.94 | 8.41 | 9.03 | 0 | 8.41 | 7.24 | 7.94 | 0 |
| Noground | 8.88 | 8.18 | 8.76 | 0 | 8.65 | 7.24 | 7.88 | 0 |
| Qwen3.6 checker | 8.38 | 7.94 | 8.50 | 1 | 8.65 | 7.24 | 7.88 | 0 |

Opus scores every arm lower than the gpt panel, so the two runs' numbers are not compared with
each other; within a run the checked arms sit within noise of answer-only on every axis, as in
the three earlier runs. The built-in arm is the only one apart.

## What the labels did

| Arm | A2 In-Depth points marked | C marked | A2 answers needs review | C needs review |
| --- | ---: | ---: | ---: | ---: |
| Default | 32 of 92 | 9 of 91 | 2 | 0 |
| DRY off | 33 of 94 | 3 of 91 | 3 | 0 |
| Folded | 7 of 93 | 6 of 93 | 0 | 0 |
| Noground | 8 of 93 | 8 of 93 | 0 | 0 |
| Qwen3.6 checker | 49 of 90 | 20 of 93 | 13 | 1 |

In C the default arm's citation check reports 33 points passed, 23 not addressed (the record
does not hold a stated fact; a neutral note) and 1 contradiction, where A2 had 28 failures.
The reviewer's unquoted doubts are notes. The Qwen checker's 45 In-Depth citation failures and
13 flagged answers in A2 fell to 2 and 1 in C.

## The checks against the judge (`judges/check-precision.json`, harness #202)

Answer level, per cell, against the union of the judge's faults (citation groundedness
unsupported or partly, accuracy below 7, harm, a temporal axis not ok):

| Check | A2 marked | A2 hits | A2 precision | A2 recall | C marked | C hits | C precision | C recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Date check | 6 | 0 | 0.00 | 0.00 | 6 | 0 | 0.00 | 0.00 |
| Date check, answer patched | 6 | 6 | 1.00 | 0.12 | 6 | 0 | 0.00 | 0.00 |
| Citation support | 15 | 8 | 0.53 | 0.16 | 2 | 0 | 0.00 | 0.00 |
| Model review | 0 | 0 | n/a | 0.00 | 0 | 0 | n/a | 0.00 |
| Status: needs review | 11 | 7 | 0.64 | 0.14 | 0 | 0 | n/a | 0.00 |

Judged answer faults: 49 of 102 cells in A2 (panel), 34 of 102 in C (Opus). A patched answer
is scored after the patch, so its row says whether the patch left a judged fault, not whether
the check was right: the panel faulted all six patched cells, Opus none of them. The six
unpatched date-check marks in both runs are the same cells in every Hub arm; they are to be
read case by case before run D's record.

In-Depth, per point, against the judge's per-point verdict (wrong_fact, wrong_citation,
unsupported):

| Check | A2 marked | A2 hits | A2 precision | A2 recall | C marked | C hits | C precision | C recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Citation support | 85 | 32 | 0.38 | 0.32 | 5 | 3 | 0.60 | 0.08 |
| Date check | 5 | 4 | 0.80 | 0.04 | 4 | 3 | 0.75 | 0.08 |
| Model review | 27 | 15 | 0.56 | 0.15 | 20 | 10 | 0.50 | 0.25 |
| Any mark | 102 | 40 | 0.39 | 0.40 | 26 | 10 | 0.38 | 0.25 |

Judged wrong points: 101 of 462 in A2, 40 of 461 in C.

Reading: the remediation cut the marked points by three quarters and left the judged scores
where they were. The precision of what remains did not move (about 0.4 for any mark), because
the model review is now the main source of marks and is right half the time; the citation
and date checks are at 0.6 to 0.8 on few marks. Recall is a quarter at best: most judged
errors are of kinds no check looks for (a wrong interpretation, a missed record, an
incomplete answer). Nothing but the deterministic checks is near the proposed LG1 bar.

## DRY (L5.2)

The DRY-off arm scored as the default on every A2 axis (8.94 against 9.00 accuracy, 8.41
against 8.29 completeness, 9.03 against 8.85 relevance), had 0 turns with a garbled date
against 4, wrote 29 of 35 answers identically, and took 57 s a turn against 72 s (the answer
stage 34.5 s against 42.0 s, the In-Depth 11.4 s against 15.3 s: scanning the 24k context for
repeats on every token costs time). Decision: DRY off is the writer's default (Hub #46,
`SYNTH_DRY_MULTIPLIER` 0) and the router's shared section (`scripts/llama-router.ini`).

## A first calibrated score (L8 prototype)

`work/labels/calibrate.py` fits a logistic regression on the 734 judged In-Depth points of
A2 and C (141 wrong) with five features: the date check, the citation check, the model review,
an uncited point, and which Hub wrote it; scenarios split in half, the odd half held out.

| | Train (431 points) | Held out (303 points) |
| --- | ---: | ---: |
| AUROC | 0.748 | 0.757 |
| Brier | 0.143 | 0.127 |
| Expected calibration error (10 bins) | 0.017 | 0.076 |
| Lowest cut with 0.8 precision | p >= 0.52: 14 points, precision 0.86, recall 0.13 | none reachable |

Log-odds: model review +1.63, date check +0.71, citation check +0.03, uncited point -1.30, the
remediated Hub -1.11, intercept -0.62. Single checks on the held-out half: citation 42 marked
at 0.36 precision, review 24 at 0.38, date 1 at 1.00.

Reading: the checks carry about as much signal as a weak classifier (AUROC 0.75) and, once
calibrated, say so: a marked point is wrong with probability 0.35 to 0.45, which is what the
page should show instead of red. No band reaches 0.8 precision on held-out data with these
features. The features run D adds (the verification-question review, agreement with a second
writer) and the offline scorer are the candidates for raising it; the fit is repeated on
A2, C and D.

## Other findings

- The judge saw the checks' verdicts until 27 October (source grounding status, check results,
  the marks after each point), so agreement in the 26 October run and run A is partly circular;
  from A2 on it saw none (harness e92b752).
- The judge brief asks for a verdict per In-Depth point since 27 October; that is what the
  per-point table and the calibration use.
- Claude Opus 5.5 wrote a trailing comma in one of 17 verdict blocks and the tool lost the
  pass; the parser now forgives it and a bad session is re-run (umbrella judging-card).
- Codex rate-limited the gpt-6-astra sessions (429) after about seven passes in a day; the
  judge loop now takes `JUDGE_PARALLEL` and `JUDGE_ATTEMPTS`, and the owner set one judge
  run per round.

## Decisions taken and open

- Taken (owner, 28 October): one judge run per round; the pruning in
  [confidence-labels.md](../confidence-labels.md#pruning-28-october-2026-from-runs-a2-and-c-and-the-ensemble-research);
  DRY off.
- Open: LG1 (the precision bar for a check to mark what the clinician sees; proposed 0.8 on
  50 marks across two runs) and LG2 (the bands for a returned confidence label).
