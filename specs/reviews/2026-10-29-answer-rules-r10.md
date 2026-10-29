# Answer rules R10: judged run on 15 fresh patients

**Date:** 29 October 2026 · **Spec:** [answer-rules.md](../answer-rules.md) R10 · **Run:**
`effa8855` (Hub b49bb60: the rules as of answer-rules 0d9777c), 15 HIV-baseline patients drawn at
random (seed 20261029) from the 2,907 whose charts can exercise the rules, excluding every patient
used before, including the 15 of the [unjudged pass](2026-10-28-answer-rules-heldout-pass.md); the
same 8 single-turn questions per patient (5 aimed at the fault patterns, 3 of kinds the rules were
not written for); reference date 2026-06-20; the default `single-12b-bare` and the built-in
ChartSearchAI on the same 12B engine; 120 cells per arm, judged blind by one gpt-6-astra high pass
and one Claude Opus 5.5 high pass. Data root `work/rules/fresh/data` (`make review DATA_ROOT=`).

## Judged scores

| Arm | Opus accuracy | gpt accuracy | Opus harm | gpt harm |
| --- | ---: | ---: | ---: | ---: |
| Built-in | 7.93 | 8.26 | 5 | 9 |
| Bare (writer and the deterministic checks, with the rules) | 8.52 | 9.00 | 2 | 3 |

By question (Opus, gpt):

| Question | Built-in | Bare | Rules that acted |
| --- | --- | --- | --- |
| Medications ordered in the past 6 months | 5.80, 5.73 | 8.80, 9.20 | window (edits) |
| Anything changed in the last 3 months | 5.07, 6.27 | 7.00, 8.20 | window (edits), relative time (marks) |
| Drugs and what each is for | 6.73, 7.67 | 7.73, 8.47 | drug citation (edits) |
| What the patient is treated for | 8.00, 8.13 | 7.87, 8.40 | |
| Weight over the past year | 9.53, 9.60 | 9.60, 9.47 | series, stale value (edits) |
| Latest CD4 | 10.00, 10.00 | 9.87, 9.93 | |
| Last visit summary | 8.47, 8.67 | 7.40, 8.33 | |
| Allergies | 9.87, 10.00 | 9.87, 10.00 | |

The two arms differ in more than the rules (the Hub's prompt and context too), so the gap is not
all the rules'. On the orders question the Hub arms without the rules scored the same 5 as the
built-in in runs D3 and D4, on other patients; with the rules the Hub scores 8.8 to 9.2, and the
judges' notes on those cells say the older orders are "correctly excluded". The window questions
are where the arms part most.

## The rules' findings against the judges

Marks (fail findings), a mark counting as a hit when the judge faulted the point (wrong fact,
wrong citation, unsupported) or the cell:

| Rule | Marks | A judge faulted it | Both judges faulted it |
| --- | ---: | ---: | ---: |
| Drug citation (In-Depth) | 4 | 2 | 2 |
| Relative time (Answer) | 2 | 2 | 2 |
| Relative time (In-Depth) | 2 | 1 | 1 |
| Demographics citation (In-Depth) | 1 | 1 | 0 |
| All | 9 | 6 | 5 |

The two drug-citation misses cite Hepatitis B and measles orders for a general sentence about the
other childhood vaccines: the citation does not support the sentence, and the judges called the
sentence guidance rather than a patient fact. Nine marks are far from LG1's 50; the marks stay
hidden until a rule has them.

Edits (info findings): 46 on 38 cells (window 24, stale value 12, drug citation 5, series 5,
among them several on one cell). The edited cells score 8.16 (Opus) and 8.58 (gpt) against 8.68
and 9.20 for the others; they are the window and drug questions, the hardest of the eight. Read
cell by cell, the judges' notes on the edited cells credit the edits ("correctly excludes the
four orders before 2025-12-20", "correctly states nothing is charted after 2026-03-20") and fault
what the rules do not touch: a wrong drug indication or class, a contradiction the writer adds
after the rule's lead (marked by the relative-time rule), and omissions. Two rule defects showed:

- In a sentence that also cites records inside the window, an item citing only older records
  stayed while the note said older records were left out (3 of the 4 such cells faulted). Fixed
  after the run (Hub answer-rules 051b191): the rule names such an item with its dates unless the
  answer frames it as earlier, and the note counts only what it removed.
- The lead "the chart has no records of these kinds within the window" was read as "no records"
  where the chart had a programme record in the window. Naming the window's other records was
  tried in a replay and dropped: on the orders question it lists visits and payment records.

## Patterns the judges raised that no rule covers

- A missed return visit: a return date in the past with no later encounter (several "changes"
  and "last visit" cells). The temporal facts carry return-visit dates and encounters, so a
  general rule is possible.
- A drug's indication or class (isoniazid called antiretroviral, co-trimoxazole called HIV
  treatment, prophylaxis recorded as stopped): needs a classification source or the chart's plan
  records read as current, not a hand list.
- A trend word against two readings ("pulse decreased" for 70 to 88).

## Reading

On patients the rules were not written from, the window edit removes the fault the judges marked
hardest in every earlier run (accuracy 5 on the orders question), and no edit was faulted for
what it did. The marks are right more often than not but rare (9 in 120 answers). The rules'
judged evidence is one run of 15 patients; the window and series rules have the most of it.
