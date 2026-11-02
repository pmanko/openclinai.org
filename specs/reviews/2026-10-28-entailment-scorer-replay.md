# Entailment scorer replay: MiniCheck and NLI cross-encoders against the Hub's prompted citation check

**Date:** 28 October 2026 · **Spec:** [confidence-labels.md](../confidence-labels.md) (L6, decision-layer P0.3) ·
**Runs:** A2 `8dacd7b1` (four-pass judge panel aggregate) and C `e01674f6` (one Opus pass), the same
runs as [the A2 and C check scoring](2026-10-28-confidence-labels-runs-a2-c.md). Offline replay on
CPU; no Hub or harness code changed. Scripts and outputs are in the git-ignored
`work/labels/scorer/` (`build_pairs.py`, `score_pairs.py`, `metrics.py`, `probe_format.py`,
`variant_facts.py`, `aggregate_facts.py`, `write_review.py`; pairs, scores and tables under `out/`;
step log `agent.log`).

## Question

Would a dedicated local entailment scorer (MiniCheck class or an NLI cross-encoder) beat the
Hub's prompted citation check at finding In-Depth points the judge faults, and if so at what
threshold should it enter a Hub profile in shadow (L6.1, L6.2)?

## Method

Pairs. For every In-Depth point that cites at least one record and has a canonical judge verdict,
one pair: source = the cited records' chart lines from `charts/<slug>.snapshot.txt` joined with
newlines, statement = the point text with `[N]` markers removed. The join to the verdict is on
(scenario, arm, turn, n) with n the 1-based position in `inDepth.validation.claims`, the same join
as `harness/validate/check_precision.py`. Label: contradicted when the verdict is `wrong_fact`,
`wrong_citation` or `unsupported`; supported for `correct` and `guidance`. Citation indices above
the chart's last record (366, 367) are guideline entries the Hub resolved from its own guidance
source, not chart records; their `references[].sourceText` is used as the source and the pair is
flagged, and the tables are repeated without those pairs.

The Hub's verdict for the same point comes from `citation_checks[]` (`fail`, `warn`, `pass`,
`not_addressed`); where A2 lists no entry (it records only the non-passing points) the
`groundingChecks[]` entries with `location: indepth` for the same text are aggregated. The
noground arm has no check, so its points read `none`. For precision and recall the Hub mark is
`fail`; for AUROC, Brier and ECE the Hub is scored fail = 1.0, pass = 0.0, everything else 0.5
(a three-level score, so its calibration numbers are indicative only).

Scorers, all on CPU with four threads, weights in the default Hugging Face cache:

| Scorer | Checkpoint | Licence | Input | Score used |
| --- | --- | --- | --- | --- |
| minicheck-deberta | `lytang/MiniCheck-DeBERTa-v3-Large` | MIT | `doc</s>claim`, max 2048 tokens, as in the MiniCheck reference `inference.py` | 1 - p(support) |
| minicheck-flan-t5 | `lytang/MiniCheck-Flan-T5-Large` | MIT | `predict: doc</s>claim`, logits of tokens 3 and 209 | 1 - p(support) |
| nli-mnli-fever | `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | MIT | (premise, hypothesis) pair, max 512 | 1 - p(entailment); p(contradiction) shown as a second row |
| nli-cross-encoder | `cross-encoder/nli-deberta-v3-base` | Apache-2.0 | (premise, hypothesis) pair, max 512 | 1 - p(entailment); p(contradiction) as a second row |

Bespoke-MiniCheck-7B (CC BY-NC 4.0) was not run: non-commercial and too large for CPU here. No
input was truncated (longest In-Depth input 307 tokens). A mark is a score at or above 0.5;
the second threshold is the lowest one whose precision for "contradicted" reaches 0.8 with at
least five marks. Calibration uses ten equal-width bins.

Answer-level pairs: every `groundingChecks[]` entry with `location` answer or block on the final
turn of each judged cell, source = its `source_indices` chart lines, statement = its claim. The
reference is the cell's `citation_groundedness` (supported vs partly or unsupported), one label
for every check in the cell, so those numbers are a weaker, cell-level comparison and are
reported apart.

## Pair counts

| Run | In-Depth points | cited | cited and judged (pairs) | contradicted | correct / guidance / wrong_fact / wrong_citation / unsupported | guideline-sourced citations | Hub verdicts fail / warn / pass / not addressed / none |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| A2 | 462 | 301 | 263 | 89 | 117 / 57 / 33 / 28 / 28 | 46 | 85 / 4 / 87 / 0 / 87 |
| C | 461 | 296 | 198 | 36 | 125 / 37 / 16 / 16 / 4 | 45 | 5 / 4 / 97 / 52 / 40 |

The 461 In-Depth pairs carry 125 contradicted labels (27 percent). Uncited points (161 in A2,
165 in C) and cited points without a verdict (38 and 98) are outside the set. Answer level:
472 pairs per run (944 in all, 255 in cells the judge called partly or unsupported).

## Headline: In-Depth points

**In-Depth points, both runs** (461 pairs, 125 contradicted)

| scorer | marked at 0.5 (Hub: fail) | precision at 0.5 | recall at 0.5 | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|
| minicheck-deberta | 414 | 0.30 | 1.00 | none | | |  | 0.59 | 0.565 | 0.591 |
| minicheck-flan-t5 | 383 | 0.32 | 0.97 | none | | |  | 0.66 | 0.506 | 0.533 |
| nli-cross-encoder | 405 | 0.29 | 0.94 | none | | |  | 0.56 | 0.617 | 0.628 |
| nli-cross-encoder (p_contra) | 14 | 0.43 | 0.05 | none | | |  | 0.58 | 0.274 | 0.276 |
| nli-mnli-fever | 370 | 0.30 | 0.89 | none | | |  | 0.59 | 0.525 | 0.535 |
| nli-mnli-fever (p_contra) | 15 | 0.53 | 0.06 | 0.654 | 5 | 1.00 | 0.04 | 0.57 | 0.248 | 0.247 |
| hub-check | 90 | 0.39 | 0.28 | none | | |  | 0.57 | 0.312 | 0.309 |
| hub-check, checked arms only (334 pairs, 90 contradicted) | 90 | 0.39 | 0.39 | none | | |  | 0.58 | 0.335 | 0.341 |

No scorer and no threshold reaches precision 0.8 (the only one that does, p(contradiction) of
nli-mnli-fever at 0.654, marks 5 pairs for recall 0.04). Every scorer marks almost every pair:
370 to 414 of the 461 pairs score at or above 0.5, including 220 to 242 of the 242 points the
judge called correct, and 311 to 394 score above 0.9. AUROC 0.56 to 0.66 against 0.57 for the Hub's
three-level verdict; the Hub's fail mark has precision 0.39 and recall 0.28 (0.39 on the arms
that ran the check).

**In-Depth points whose every citation resolves in the chart snapshot** (370 pairs, 108 contradicted)

| scorer | marked at 0.5 (Hub: fail) | precision at 0.5 | recall at 0.5 | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|
| minicheck-deberta | 370 | 0.29 | 1.00 | none | | |  | 0.49 | 0.647 | 0.668 |
| minicheck-flan-t5 | 351 | 0.30 | 0.96 | none | | |  | 0.59 | 0.590 | 0.610 |
| nli-cross-encoder | 362 | 0.28 | 0.93 | none | | |  | 0.45 | 0.703 | 0.713 |
| nli-cross-encoder (p_contra) | 14 | 0.43 | 0.06 | none | | |  | 0.50 | 0.297 | 0.299 |
| nli-mnli-fever | 334 | 0.28 | 0.87 | none | | |  | 0.54 | 0.607 | 0.635 |
| nli-mnli-fever (p_contra) | 9 | 0.56 | 0.05 | none | | |  | 0.51 | 0.269 | 0.276 |
| hub-check | 78 | 0.33 | 0.24 | none | | |  | 0.52 | 0.352 | 0.342 |
| hub-check, checked arms only (263 pairs, 76 contradicted) | 78 | 0.33 | 0.34 | none | | |  | 0.52 | 0.394 | 0.399 |

Without the guideline-sourced pairs every scorer's AUROC drops to 0.45 to 0.59: the scorers
separate guidance points cited to a WHO guideline paragraph (supported, often) from everything
else, and that is most of what the AUROC above was measuring.

### Why: the points are not atomic claims

Median p(support) by judge verdict, minicheck-deberta: correct 0.03, wrong_fact 0.02,
wrong_citation 0.02, unsupported 0.04, guidance 0.55. The scorers do not tell a correct point
from a wrong one; they tell "repeats a guideline paragraph" from "states a chart fact with a
clinical reading". A handcrafted probe (`probe_format.py`) shows the mechanism. Cells are
p(support) for: a bare fact ("The patient's CD4 count was 341 cells/uL on 2025-11-24.") / the
same fact with the inference the model actually wrote ("..., which indicates a need for
continued antiretroviral therapy to maintain immune function.") / a wrong value (72 cells/uL),
against record `[182] (2025-11-24) CD4 count: 341 cells/uL` rendered four ways:

| source form | minicheck-deberta | minicheck-flan-t5 | nli-mnli-fever | nli-cross-encoder |
|---|---|---|---|---|
| chart line as is | 0.62 / 0.01 / 0.03 | 0.85 / 0.02 / 0.02 | 0.56 / 0.00 / 0.00 | 0.01 / 0.00 / 0.00 |
| no [N] prefix | 0.71 / 0.01 / 0.03 | 0.77 / 0.02 / 0.02 | 0.43 / 0.00 / 0.00 | 0.01 / 0.00 / 0.00 |
| prose | 0.84 / 0.01 / 0.02 | 0.65 / 0.02 / 0.02 | 0.41 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| prose with record id | 0.85 / 0.01 / 0.03 | 0.86 / 0.02 / 0.02 | 0.78 / 0.00 / 0.00 | 0.01 / 0.00 / 0.00 |

The inference clause takes p(support) to 0.01 for every model, as entailment should: the chart
does not state the need for continued ART. The judge calls that point correct because the fact
is right and the reading is sound. The two definitions of "supported" differ, and nearly every
In-Depth point carries such a clause. The chart-line format is a smaller effect (0.62 to 0.85
for the bare fact with MiniCheck DeBERTa) and `cross-encoder/nli-deberta-v3-base` cannot entail
even the bare fact (0.007), so it is unusable for this data.

### By run and by arm

**In-Depth by run**

| by_run | n | contradicted | minicheck-deberta AUROC / P / R at 0.5 | minicheck-flan-t5 AUROC / P / R at 0.5 | nli-cross-encoder AUROC / P / R at 0.5 | nli-cross-encoder (p_contra) AUROC / P / R at 0.5 | nli-mnli-fever AUROC / P / R at 0.5 | nli-mnli-fever (p_contra) AUROC / P / R at 0.5 | hub-check AUROC / P / R at 0.5 |
|---|---|---|---|---|---|---|---|---|---|
| A2 | 263 | 89 | 0.58 / 0.37 / 1.00 | 0.64 / 0.38 / 0.95 | 0.55 / 0.36 / 0.97 | 0.58 / 0.50 / 0.03 | 0.57 / 0.37 / 0.90 | 0.56 / 0.71 / 0.06 | 0.52 / 0.38 / 0.36 |
| C | 198 | 36 | 0.61 / 0.21 / 1.00 | 0.69 / 0.22 / 1.00 | 0.58 / 0.18 / 0.86 | 0.57 / 0.38 / 0.08 | 0.61 / 0.20 / 0.86 | 0.59 / 0.38 / 0.08 | 0.59 / 0.60 / 0.08 |

**In-Depth by arm**

| by_arm | n | contradicted | minicheck-deberta AUROC / P / R at 0.5 | minicheck-flan-t5 AUROC / P / R at 0.5 | nli-cross-encoder AUROC / P / R at 0.5 | nli-cross-encoder (p_contra) AUROC / P / R at 0.5 | nli-mnli-fever AUROC / P / R at 0.5 | nli-mnli-fever (p_contra) AUROC / P / R at 0.5 | hub-check AUROC / P / R at 0.5 |
|---|---|---|---|---|---|---|---|---|---|
| hub-profile-single-12b-checked | 91 | 21 | 0.54 / 0.25 / 1.00 | 0.63 / 0.27 / 1.00 | 0.49 / 0.25 / 0.95 | 0.49 / 0.00 / 0.00 | 0.54 / 0.25 / 0.91 | 0.48 / 0.25 / 0.05 | 0.57 / 0.30 / 0.29 |
| hub-profile-single-12b-checked-folded | 90 | 25 | 0.62 / 0.31 / 1.00 | 0.69 / 0.33 / 0.96 | 0.61 / 0.29 / 0.92 | 0.57 / 0.50 / 0.08 | 0.64 / 0.32 / 0.88 | 0.56 / 0.75 / 0.12 | 0.51 / 0.50 / 0.16 |
| hub-profile-single-12b-checked-nodry | 91 | 20 | 0.54 / 0.24 / 1.00 | 0.62 / 0.26 / 1.00 | 0.50 / 0.23 / 0.90 | 0.51 / 0.00 / 0.00 | 0.50 / 0.22 / 0.85 | 0.47 / 0.00 / 0.00 | 0.56 / 0.28 / 0.35 |
| hub-profile-single-12b-checked-noground | 92 | 27 | 0.62 / 0.33 / 1.00 | 0.70 / 0.35 / 0.96 | 0.58 / 0.31 / 0.93 | 0.64 / 0.50 / 0.07 | 0.66 / 0.34 / 0.89 | 0.62 / 0.75 / 0.11 | 0.50 / n/a / 0.00 |
| hub-profile-single-12b-xcheck | 97 | 32 | 0.59 / 0.37 / 1.00 | 0.62 / 0.38 / 0.94 | 0.58 / 0.35 / 0.97 | 0.65 / 0.50 / 0.06 | 0.60 / 0.37 / 0.91 | 0.65 / 1.00 / 0.03 | 0.64 / 0.49 / 0.56 |

### Marks by judge verdict

**In-Depth marks by judge verdict** (marked = score at or above 0.5; Hub mark = fail)

| scorer | marked: correct | marked: wrong_fact | marked: wrong_citation | marked: unsupported | marked: guidance | unmarked: correct | unmarked: wrong_fact | unmarked: wrong_citation | unmarked: unsupported | unmarked: guidance |
|---|---|---|---|---|---|---|---|---|---|---|
| minicheck-deberta | 242 | 49 | 44 | 32 | 47 | 0 | 0 | 0 | 0 | 47 |
| minicheck-flan-t5 | 227 | 49 | 44 | 28 | 35 | 15 | 0 | 0 | 4 | 59 |
| nli-cross-encoder | 242 | 41 | 44 | 32 | 46 | 0 | 8 | 0 | 0 | 48 |
| nli-cross-encoder (p_contra) | 8 | 5 | 0 | 1 | 0 | 234 | 44 | 44 | 31 | 94 |
| nli-mnli-fever | 220 | 35 | 44 | 32 | 39 | 22 | 14 | 0 | 0 | 55 |
| nli-mnli-fever (p_contra) | 7 | 5 | 3 | 0 | 0 | 235 | 44 | 41 | 32 | 94 |
| hub-check | 38 | 12 | 15 | 8 | 17 | 204 | 37 | 29 | 24 | 77 |

### Calibration

**In-Depth calibration** (ten equal-width bins; n, mean score, observed contradicted rate)

| bin | minicheck-deberta | minicheck-flan-t5 | nli-cross-encoder | nli-mnli-fever | hub-check |
|---|---|---|---|---|---|
| 0.0-0.1 | 35, 0.07, 0.00 | 45, 0.03, 0.00 | 48, 0.01, 0.00 | 48, 0.02, 0.00 | 184, 0.00, 0.23 |
| 0.1-0.2 | 4, 0.13, 0.00 | 7, 0.16, 0.14 |  | 13, 0.18, 0.00 |  |
| 0.2-0.3 |  |  |  | 19, 0.23, 0.47 |  |
| 0.3-0.4 | 8, 0.38, 0.00 | 8, 0.37, 0.38 | 8, 0.38, 1.00 | 11, 0.37, 0.46 |  |
| 0.4-0.5 |  | 18, 0.44, 0.00 |  |  |  |
| 0.5-0.6 | 4, 0.52, 0.00 |  |  | 5, 0.56, 0.00 | 187, 0.50, 0.26 |
| 0.6-0.7 |  | 14, 0.65, 0.00 |  | 10, 0.67, 0.50 |  |
| 0.7-0.8 | 9, 0.79, 0.56 | 28, 0.77, 0.36 | 1, 0.77, 0.00 | 26, 0.74, 0.15 |  |
| 0.8-0.9 | 41, 0.86, 0.17 | 24, 0.87, 0.12 | 10, 0.82, 0.00 | 18, 0.87, 0.61 |  |
| 0.9-1.0 | 360, 0.96, 0.31 | 317, 0.96, 0.34 | 394, 0.99, 0.30 | 311, 0.98, 0.29 | 90, 1.00, 0.39 |

Brier 0.51 to 0.62 and ECE 0.53 to 0.63 for the scorers against 0.31 for the Hub: the scorers
are confidently wrong on the supported majority. A 0.9 to 1.0 score means contradicted 29 to 34
percent of the time, which is the base rate.

### Agreement

**Scorer agreement (In-Depth)**

| pair | agreement at 0.5 | kappa at 0.5 | Spearman |
|---|---|---|---|
| minicheck-deberta vs minicheck-flan-t5 | 0.92 | 0.64 | 0.64 |
| minicheck-deberta vs nli-cross-encoder | 0.95 | 0.75 | 0.52 |
| minicheck-deberta vs nli-mnli-fever | 0.91 | 0.63 | 0.51 |
| minicheck-flan-t5 vs nli-cross-encoder | 0.90 | 0.60 | 0.62 |
| minicheck-flan-t5 vs nli-mnli-fever | 0.85 | 0.52 | 0.58 |
| nli-cross-encoder vs nli-mnli-fever | 0.92 | 0.72 | 0.78 |
| minicheck-deberta vs hub-check (hub-checked pairs) | 0.37 | 0.08 | n/a |
| minicheck-flan-t5 vs hub-check (hub-checked pairs) | 0.42 | 0.11 | n/a |
| nli-cross-encoder vs hub-check (hub-checked pairs) | 0.39 | 0.09 | n/a |
| nli-mnli-fever vs hub-check (hub-checked pairs) | 0.43 | 0.13 | n/a |

The scorers agree with each other (kappa 0.52 to 0.75) and not with the Hub check (kappa 0.08
to 0.13): they measure a different thing.

### Where the Hub check and MiniCheck DeBERTa disagree

**Hub check marked fail, the ten pairs minicheck-deberta finds least contradicted (score below 0.5 = scorer says supported)**

| # | run / arm / scenario / turn / n | scorer | judge | statement | source | judge reason |
|---|---|---|---|---|---|---|
| 1 | A2 / checked-nodry / convo-diagnosis-evidence / t5 / n2 | 0.13 | guidance | Per WHO HIV guidelines, a CD4 count below 200 cells/mm3 indicates advanced HIV disease and necessitates opportunistic-infection prophylaxis. | [366] Role of the CD4 count: The CD4 count reflects immune status in HIV; lower counts mean higher risk of opportunistic infection. A CD4 below 200 cells/mm3 indicates advanced HIV disease and the need for opportunistic-infection prophylaxis. ART is started regardless of the CD4 count. (source: WHO Consolidated guidelines on HIV prevention, testing, treatment, service delivery and monitoring) | States a general CD4 threshold; [366] is not a chart record. |
| 2 | A2 / checked-nodry / convo-diagnosis-evidence / t2 / n1 | 0.85 | correct | Standard practice for HIV management involves the use of Antiretroviral Therapy (ART) to suppress viral load, which is consistent with this patient's current regimen of nevirapine, lamivudine, and stavudine. | [1] (2026-01-26) Drug order: Nevirapine. Action: NEW. Urgency: ROUTINE [2] (2026-01-26) Drug order: Lamivudine. Action: NEW. Urgency: ROUTINE [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE | The patient-specific regimen is supported by [1]-[3]. |
| 3 | A2 / xcheck / date-aloice-last-visit-exact / t1 / n3 | 0.89 | correct | The patient's pulse was elevated at 157 beats/min during this visit, which requires close monitoring alongside their reported fever and active TB status. | [18] (2026-01-07) Pulse: 157 beats/min [20] (2026-01-07) Temperature (C): 39.7 C [1] (2026-05-20) Program: Tuberculosis treatment program. Status: Active. Current state: GROUP TB | Record [18] documents pulse 157 beats/min at the visit, [20] documents fever, and [1] documents active tuberculosis program status; monitoring is general advice. |
| 4 | A2 / checked-nodry / convo-safety-escalation / t3 / n2 | 0.91 | correct | The patient's current regimen includes Nevirapine and Stavudine, which requires consistent use to ensure clinical efficacy. | [1] (2026-01-26) Drug order: Nevirapine. Action: NEW. Urgency: ROUTINE [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE | [1,3] support inclusion of nevirapine and stavudine in the latest recorded regimen. |
| 5 | A2 / checked / convo-safety-escalation / t3 / n2 | 0.91 | correct | The patient's current regimen includes Nevirapine and Stavudine, which requires consistent use to ensure clinical efficacy. | [1] (2026-01-26) Drug order: Nevirapine. Action: NEW. Urgency: ROUTINE [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE | [1,3] support inclusion of nevirapine and stavudine in the latest recorded regimen. |
| 6 | A2 / xcheck / convo-diagnosis-evidence / t4 / n2 | 0.91 | unsupported | Because the patient's CD4 count remains above 200 cells/mm³, they do not currently meet the criteria for opportunistic-infection prophylaxis based on immune status alone. | [366] Role of the CD4 count: The CD4 count reflects immune status in HIV; lower counts mean higher risk of opportunistic infection. A CD4 below 200 cells/mm3 indicates advanced HIV disease and the need for opportunistic-infection prophylaxis. ART is started regardless of the CD4 count. (source: WHO Consolidated guidelines on HIV prevention, testing, treatment, service delivery and monitoring) | Neither the historical count [182] nor [366] establishes current ineligibility for all opportunistic-infection prophylaxis. |
| 7 | A2 / xcheck / convo-safety-escalation / t1 / n1 | 0.91 | guidance | Per the 'treat-all' strategy, patients should remain on ART regardless of their current CD4 count or WHO clinical stage to maintain viral suppression and improve health outcomes. | [367] Treat-all: start ART regardless of CD4: WHO recommends antiretroviral therapy for everyone diagnosed with HIV, regardless of CD4 count or WHO clinical stage ('treat all'), and as early as possible after diagnosis. (source: WHO Consolidated guidelines on HIV prevention, testing, treatment, service delivery and monitoring) | General treatment guidance without a patient-specific fact; [367] is a supplied knowledge reference, not a chart record. |
| 8 | A2 / checked-nodry / convo-diagnosis-evidence / t3 / n2 | 0.92 | correct | The patient's classification of WHO stage 3 adult indicates a need for close monitoring and management of opportunistic infections. | [20] (2026-01-26) Current WHO HIV stage: WHO stage 3 adult | [20] explicitly supports stage 3. |
| 9 | A2 / checked / convo-diagnosis-evidence / t3 / n2 | 0.92 | correct | The patient's classification as WHO stage 3 adult indicates a need for close monitoring and management of opportunistic infections. | [20] (2026-01-26) Current WHO HIV stage: WHO stage 3 adult | [20] explicitly supports stage 3. |
| 10 | A2 / checked-nodry / convo-diagnosis-evidence / t4 / n3 | 0.92 | guidance | Monitoring of the CD4 count over time is standard practice to assess the effectiveness of antiretroviral therapy and guide clinical management. | [366] Role of the CD4 count: The CD4 count reflects immune status in HIV; lower counts mean higher risk of opportunistic infection. A CD4 below 200 cells/mm3 indicates advanced HIV disease and the need for opportunistic-infection prophylaxis. ART is started regardless of the CD4 count. (source: WHO Consolidated guidelines on HIV prevention, testing, treatment, service delivery and monitoring) | Discusses monitoring generally without claiming it occurred. |

**Hub check passed, the ten pairs minicheck-deberta finds most contradicted**

| # | run / arm / scenario / turn / n | scorer | judge | statement | source | judge reason |
|---|---|---|---|---|---|---|
| 1 | A2 / checked-folded / convo-medications-adherence / t3 / n3 | 0.99 | correct | The patient's CD4 count was recorded at 341 cells/uL on 2025-11-24, which indicates a need for continued antiretroviral therapy to maintain immune function. | [182] (2025-11-24) CD4 count: 341 cells/uL | Record [182] gives CD4 341 cells/uL on November 24, 2025. |
| 2 | C / checked-folded / convo-medications-adherence / t3 / n3 | 0.99 | correct | The patient's CD4 count was recorded at 341 cells/uL on 2025-11-24, which indicates a need for continued antiretroviral therapy to maintain immune function. | [182] (2025-11-24) CD4 count: 341 cells/uL | CD4 341 cells/uL on 2025-11-24 matches [182]. |
| 3 | C / checked / ek-growth / t1 / n3 | 0.99 | correct | Monitoring weight gain remains critical for children with HIV who are also experiencing failure to thrive or delayed milestones. | [131] (2026-01-12) Condition: Failure to thrive. Status: ACTIVE. Onset: 2026-01-12 [132] (2026-01-12) Condition: Delayed milestones. Status: ACTIVE. Onset: 2026-01-12 | FTT [131] and delayed milestones [132] are both active. |
| 4 | A2 / checked / single-upcoming-appointments / t1 / n1 | 0.99 | correct | Based on the patient's most recent encounter on 2026-01-26, a return visit was scheduled for 2026-02-23, which has already passed relative to today's date of 2026-06-20. | [22] (2026-01-26) Return visit date: 2026-02-23 | The latest encounter is 2026-01-26 [4], and [22] records a 2026-02-23 return date, before 2026-06-20. |
| 5 | C / checked / single-upcoming-appointments / t1 / n1 | 0.99 | correct | Based on the patient's most recent encounter on 2026-01-26, a return visit was scheduled for 2026-02-23, which has already passed relative to today's date of 2026-06-20. | [22] (2026-01-26) Return visit date: 2026-02-23 | [22] (2026-01-26) records return visit 2026-02-23, which precedes the reference date 2026-06-20. |
| 6 | A2 / checked-nodry / single-upcoming-appointments / t1 / n1 | 0.99 | correct | Based on the patient's most recent encounter on 2026-01-26, a return visit was scheduled for 2026-02-23, which has already passed relative to today's date of 2026-06-20. | [22] (2026-01-26) Return visit date: 2026-02-23 | The latest encounter is 2026-01-26 [4], and [22] records a 2026-02-23 return date, before 2026-06-20. |
| 7 | C / checked-nodry / single-upcoming-appointments / t1 / n1 | 0.99 | correct | Based on the patient's most recent encounter on 2026-01-26, a return visit was scheduled for 2026-02-23, which has already passed relative to today's date of 2026-06-20. | [22] (2026-01-26) Return visit date: 2026-02-23 | [22] (2026-01-26) records return visit 2026-02-23, which precedes the reference date 2026-06-20. |
| 8 | C / checked-folded / convo-abstention-honesty / t4 / n2 | 0.99 | correct | While the patient's current records show orders for Nevirapine, Stavudine, and Efavirenz, there is no documentation of a switch to dolutegravir. | [1] (2026-01-26) Drug order: Nevirapine. Action: NEW. Urgency: ROUTINE [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE [35] (2025-12-17) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE [72] (2025-12-15) Drug order: Efavirenz. Action: NEW. Urgency: ROUTINE [135] (2025-11-25) Drug order: Efavirenz. Action: NEW. Urgency: ROUTINE | Nevirapine [1], stavudine [3][35] and efavirenz [72][135] orders exist, and no dolutegravir appears. |
| 9 | A2 / checked-folded / convo-diagnosis-evidence / t1 / n2 | 0.99 | guidance | Stavudine requires monitoring for potential side effects such as peripheral neuropathy and lipoatrophy, which are the primary clinical concerns associated with its continued use. | [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE | Describes potential stavudine adverse effects and monitoring without asserting that she has them. |
| 10 | C / checked-folded / convo-diagnosis-evidence / t1 / n2 | 0.99 | correct | Stavudine requires monitoring for potential side effects such as peripheral neuropathy and lipoatrophy, which are the primary clinical concerns associated with its continued use. | [3] (2026-01-26) Drug order: Stavudine. Action: NEW. Urgency: ROUTINE | Stavudine order [3] is in the chart; toxicity monitoring is guidance. |

The first list is the Hub's fails that the scorer is least sure about: nine of ten are still
at 0.85 or above. The second list is the Hub's passes the scorer rejects hardest: all are
judged correct or guidance, and each adds a reading the chart line does not state.

## Variants (exploratory, after the headline)

Two follow-ups on the mechanism, not part of the planned comparison. Prose rendering of the
source ("Record 182, dated 2025-11-24: CD4 count: 341 cells/uL.") on all 461 points, and
scoring the Hub's own decomposed `facts[]` (run C only, 85 points carry them, 179 facts) with
the least supported fact as the point's score, over all facts and over value-bearing facts only
(text contains a digit).

**Whole-point statements: chart-line source vs prose-rendered source** (461 points)

| variant / scorer | n | contradicted | marked at 0.5 | precision | recall | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minicheck-deberta, chart lines | 461 | 125 | 414 | 0.30 | 1.00 | none | | |  | 0.59 | 0.565 | 0.591 |
| minicheck-deberta, prose source | 461 | 125 | 414 | 0.30 | 1.00 | none | | |  | 0.58 | 0.559 | 0.587 |
| minicheck-flan-t5, chart lines | 461 | 125 | 383 | 0.32 | 0.97 | none | | |  | 0.66 | 0.506 | 0.533 |
| minicheck-flan-t5, prose source | 461 | 125 | 389 | 0.32 | 0.99 | none | | |  | 0.64 | 0.514 | 0.538 |
| nli-mnli-fever, chart lines | 461 | 125 | 370 | 0.30 | 0.89 | none | | |  | 0.59 | 0.525 | 0.535 |
| nli-mnli-fever, prose source | 461 | 125 | 367 | 0.30 | 0.87 | none | | |  | 0.56 | 0.529 | 0.546 |

**Run C points with Hub facts, chart source** (85 points, 11 contradicted; per point the least supported fact)

| variant / scorer | n | contradicted | marked at 0.5 | precision | recall | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hub-check (fail marks) | 85 | 11 | 1 | 1.00 | 0.09 | none | | |  | 0.60 | 0.168 | 0.218 |
| minicheck-deberta, all facts | 85 | 11 | 56 | 0.18 | 0.91 | none | | |  | 0.65 | 0.500 | 0.553 |
| minicheck-deberta, value-bearing facts only | 47 | 6 | 28 | 0.21 | 1.00 | none | | |  | 0.73 | 0.399 | 0.498 |
| hub-check on the same value-bearing points | 47 | 6 | 1 | 1.00 | 0.17 | none | | |  | 0.57 | 0.170 | 0.234 |
| minicheck-flan-t5, all facts | 85 | 11 | 55 | 0.20 | 1.00 | none | | |  | 0.72 | 0.449 | 0.532 |
| minicheck-flan-t5, value-bearing facts only | 47 | 6 | 20 | 0.20 | 0.67 | none | | |  | 0.67 | 0.340 | 0.388 |
| nli-mnli-fever, all facts | 85 | 11 | 47 | 0.15 | 0.64 | none | | |  | 0.64 | 0.476 | 0.500 |
| nli-mnli-fever, value-bearing facts only | 47 | 6 | 15 | 0.20 | 0.50 | none | | |  | 0.72 | 0.282 | 0.294 |

Fact level, minicheck-deberta, facts_chart: Hub not_found: n=43, median p_support=0.02, share above 0.5=0.02; Hub found: n=134, median p_support=0.65, share above 0.5=0.63; Hub differs: n=2, median p_support=0.39, share above 0.5=0.50

**Run C points with Hub facts, prose source** (85 points, 11 contradicted; per point the least supported fact)

| variant / scorer | n | contradicted | marked at 0.5 | precision | recall | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hub-check (fail marks) | 85 | 11 | 1 | 1.00 | 0.09 | none | | |  | 0.60 | 0.168 | 0.218 |
| minicheck-deberta, all facts | 85 | 11 | 47 | 0.17 | 0.73 | none | | |  | 0.62 | 0.448 | 0.499 |
| minicheck-deberta, value-bearing facts only | 47 | 6 | 16 | 0.25 | 0.67 | none | | |  | 0.59 | 0.291 | 0.417 |
| hub-check on the same value-bearing points | 47 | 6 | 1 | 1.00 | 0.17 | none | | |  | 0.57 | 0.170 | 0.234 |
| minicheck-flan-t5, all facts | 85 | 11 | 59 | 0.19 | 1.00 | none | | |  | 0.72 | 0.465 | 0.526 |
| minicheck-flan-t5, value-bearing facts only | 47 | 6 | 27 | 0.15 | 0.67 | none | | |  | 0.64 | 0.349 | 0.438 |
| nli-mnli-fever, all facts | 85 | 11 | 49 | 0.14 | 0.64 | none | | |  | 0.67 | 0.495 | 0.511 |
| nli-mnli-fever, value-bearing facts only | 47 | 6 | 15 | 0.20 | 0.50 | none | | |  | 0.58 | 0.283 | 0.287 |

Fact level, minicheck-deberta, facts_prose: Hub not_found: n=43, median p_support=0.02, share above 0.5=0.02; Hub found: n=134, median p_support=0.88, share above 0.5=0.89; Hub differs: n=2, median p_support=0.42, share above 0.5=0.50

Prose rendering changes nothing at the point level. At the fact level it moves the scorer onto
the Hub's string match: for facts the Hub marked `found`, the share MiniCheck DeBERTa calls
supported rises from 0.63 (chart lines) to 0.89 (prose), and for `not_found` facts it stays at
0.02. The facts variant lifts AUROC to 0.65 to 0.73 on a set too small to lean on (85 points,
11 contradicted, 6 among the value-bearing subset) and precision stays at 0.2, because the
not-found facts are mostly guidance phrases ("monitoring for potential opportunistic
infections") that the judge does not fault.

## Answer and table cells

**Answer and table cells (cell-level judge label applied to every check in the cell)** (944 pairs, 255 contradicted)

| scorer | marked at 0.5 (Hub: fail) | precision at 0.5 | recall at 0.5 | threshold for precision 0.8 | marked | precision | recall | AUROC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|---|
| minicheck-deberta | 694 | 0.35 | 0.94 | none | | |  | 0.68 | 0.339 | 0.398 |
| minicheck-flan-t5 | 504 | 0.26 | 0.51 | 0.978 | 10 | 1.00 | 0.04 | 0.47 | 0.386 | 0.450 |
| nli-cross-encoder | 760 | 0.29 | 0.86 | 1.000 | 84 | 0.81 | 0.27 | 0.45 | 0.595 | 0.612 |
| nli-cross-encoder (p_contra) | 64 | 0.86 | 0.22 | 0.110 | 144 | 0.94 | 0.53 | 0.67 | 0.175 | 0.199 |
| nli-mnli-fever | 524 | 0.40 | 0.82 | none | | |  | 0.68 | 0.306 | 0.331 |
| nli-mnli-fever (p_contra) | 128 | 0.66 | 0.33 | none | | |  | 0.60 | 0.199 | 0.208 |
| hub-check | 13 | 0.46 | 0.02 | none | | |  | 0.48 | 0.279 | 0.287 |
| hub-check, checked arms only (944 pairs, 255 contradicted) | 13 | 0.46 | 0.02 | none | | |  | 0.48 | 0.279 | 0.287 |

**Answer-level marks by the cell's citation_groundedness** (marked = score at or above 0.5; Hub mark = fail)

| scorer | marked: supported | marked: partly | marked: unsupported | unmarked: supported | unmarked: partly | unmarked: unsupported |
|---|---|---|---|---|---|---|
| minicheck-deberta | 454 | 240 | 0 | 235 | 15 | 0 |
| minicheck-flan-t5 | 374 | 130 | 0 | 315 | 125 | 0 |
| nli-cross-encoder | 540 | 220 | 0 | 149 | 35 | 0 |
| nli-cross-encoder (p_contra) | 9 | 55 | 0 | 680 | 200 | 0 |
| nli-mnli-fever | 314 | 210 | 0 | 375 | 45 | 0 |
| nli-mnli-fever (p_contra) | 43 | 85 | 0 | 646 | 170 | 0 |
| hub-check | 7 | 6 | 0 | 682 | 249 | 0 |

Cell-level labels: a cell the judge called partly supported marks every check in it, so
precision here is bounded by the cell's share of faulty checks, and the Hub's 13 marks cannot be
compared with the scorers' hundreds. p(contradiction) of the cross-encoder reaches precision 0.94 at
recall 0.53 from a threshold of 0.11 on this set, and nli-mnli-fever's p(contradiction) 0.66
at 0.5, which says the two NLI models flag value conflicts in short table cells; it does not
transfer to In-Depth points (above).

## Runtime per pair on CPU

Each model alone, 100 In-Depth pairs, four threads, batch size one (the run had another model
serving on the GPU; the full-set timings were taken with two scorers in parallel and are 0.1 to
0.2 s higher, Flan-T5 much higher under contention):

| Scorer | Checkpoint | seconds per pair |
| --- | --- | ---: |
| minicheck-deberta | lytang/MiniCheck-DeBERTa-v3-Large | 0.23 |
| nli-cross-encoder | cross-encoder/nli-deberta-v3-base | 0.08 |
| nli-mnli-fever | MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli | 0.27 |
| minicheck-flan-t5 | lytang/MiniCheck-Flan-T5-Large | 0.23 |

Model load 2 to 4 s from cache (55 s on first download of the 1.7 GB DeBERTa-large weights).
An In-Depth section of 5 points costs about 1.2 s with MiniCheck DeBERTa on CPU.

## Recommendation

Do not put an entailment scorer into a Hub profile yet, in shadow or otherwise, on these pairs:
no scorer and no threshold beats the prompted check, none reaches precision 0.8, and the
failure is structural rather than a tuning matter. The In-Depth points are a chart fact plus a
clinical reading, and an entailment model rightly calls the reading "not in the chart" while
the judge rightly calls the point correct, so a (source, whole point) scorer measures the wrong
thing and would mark 80 to 90 percent of good points. The scorer only becomes a candidate once
the statement it receives is an atomic, checkable fact, which the Hub's own `facts[]`
decomposition is close to producing (run C) but on a set far too small here to set a threshold
(85 points, 11 faults). The next step for L6 is therefore not a profile but a larger labelled
set of (record, fact) pairs from run D and later runs, scored with MiniCheck DeBERTa (MIT,
0.23 s per pair on CPU, prose-rendered source) on the value-bearing facts, with a threshold
chosen there; if that set still does not reach precision 0.8 at recall above the Hub's 0.3 to
0.4, close L6 and keep the prompted check as the single citation signal. The
`cross-encoder/nli-deberta-v3-base` model is out regardless.
