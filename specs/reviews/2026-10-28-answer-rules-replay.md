# Answer rules: replay on the judged answers of runs D3 and D4

**Date:** 28 October 2026 · **Spec:** [answer-rules.md](../answer-rules.md) (R1 to R5, R7, R9) · **Code:**
Hub `answer-rules` 29b4fee · **Method:** `work/rules/replay.py` runs the rules on the answers and
In-Depth points the Hub arms shipped in runs D3 `b7bccdd2` and D4 `2a053c09`, for the scenarios of
the two patients with Hub fixture charts (aloice-mukangu, zabella-halambe; ellcky-minayo has no
fixture), and joins each finding to both judges' verdicts. This is the development set: the rules
were written from these runs' faults, so the replay shows they do what they were written for and
how often they misfire on the same answers, not how they generalise (that is R10's run).

## Marks (fail findings) against the judges

After the owner's rule that a check be general or parameterised from the chart, the drug class
and advanced HIV disease rules were removed (they rested on a hand list of antiretrovirals and a
disease-specific definition). The remaining rules:

| Rule | Marks | Distinct claims | A judge faulted it | Both judges faulted it |
| --- | ---: | ---: | ---: | ---: |
| Drug citation (In-Depth) | 19 | 5 | 19 | 17 |
| Diagnosis presence (Answer) | 14 | 2 | 14 | 14 |
| Demographics citation (In-Depth) | 10 | 2 | 10 | 5 |
| Demographics citation (Answer) | 7 | 1 | 7 | 7 |
| Relative time (In-Depth) | 4 | 1 | 4 | 0 |
| All | 54 | 11 | 54 | 43 |

The marks repeat a handful of claims across arms and runs (11 distinct), from 3 patients and 17
scenarios, and the rules were written from these answers, so the table says the rules do what
they were written for and do not misfire on these answers; it does not say they generalise.
Answer marks count a cell as faulted when the judge's accuracy is below 7 or its citation
groundedness is partly or unsupported. Two misfires found in this replay were fixed before the
count (a span quoting the record's own question, "adherence in the past week [11]", and a span
with no number, "previous months").

## Edits (info findings)

| Rule | Edits | Distinct cells |
| --- | ---: | ---: |
| Window | 14 | 2 (the "past 6 months" orders scenarios, judged accuracy 5 for the older orders the edit leaves out) |
| Drug citation (Answer) | 7 | 5 |
| Series readings | 14 | 2 |
| Stale latest value (chart rhythm) | 42 | 6 |

The held-out measurement is [answer-rules.md](../answer-rules.md) R10.
