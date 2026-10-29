# Answer rules: unjudged pass on 15 held-out patients

**Date:** 28 October 2026 · **Spec:** [answer-rules.md](../answer-rules.md) (R10, first half) ·
**Run:** `b1b904e4` (Hub answer-rules 29b4fee, default profile `single-12b-bare`), 15 HIV-baseline
patients drawn at random (seed 20261028) from the 2,922 whose charts can exercise the rules,
excluding every patient a scenario or fixture already used; 8 single-turn questions each, 5 aimed at
the fault patterns and 3 of kinds the rules were not written for; 120 turns, reference date
2026-06-20, no judging. Charts captured through the Hub's QueryStore export (32 to 211 records; the
earlier capture path had cut every chart at 100). Working files: `work/rules/heldout/`.

## What the rules did, and a hand check of every finding

| Rule | As run (29b4fee) | Hand check | After the fixes below (replayed on the same answers) |
| --- | --- | --- | --- |
| Window (edit) | 21 | 5 correct partial edits; 16 answers emptied (every record the answer cited predated the window, "changes in the last 3 months" on charts that end in February) | 5 partial edits; 14 answers kept behind "the chart has no records of these kinds dated within the last 3 months; the records below are older"; 1 answer that already said so left alone |
| Drug citation (mark) | 8 | 4 false ("Hib" and "DTP" read as naming no order), 4 correct | 2, both correct (a record of another drug inside a cited group) |
| Demographics citation (mark) | 3 | 3 correct (the demographics record cited for "no allergies documented") | 3 |
| Relative time (mark) | 1 | correct | 4, all correct (3 of them "in the past 6 months" or "within the last three months" on records the window lead now shows are older) |
| Stale latest value (edit) | 11 | 11 correct (gaps of 4.5 to 6 months, measured by each series' own rhythm) | 11 |
| Series readings (edit) | 2 | 2 correct | 2 |

## Fixes (Hub answer-rules 0d9777c)

- Window: when nothing the answer cites falls inside the window, the rule checks the chart for
  records of the same kinds inside it (up to the reference date). If there are some, the answer is
  marked for missing them; if there are none, the answer keeps its records behind a sentence saying
  they are older. Records dated after the reference date are outside the window.
- Drug citation: a drug name of several words also matches its initials; "vaccine" and
  "vaccination" no longer name a drug.

## Reading

After the fixes no false mark or wrong edit was found by hand on these 120 answers. The fixes were
made after reading them, so this patient set is now development data too; the judged measurement
draws 15 new patients the same way (answer-rules R10).
