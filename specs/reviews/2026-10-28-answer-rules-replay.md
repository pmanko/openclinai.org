# Answer rules: replay on the judged answers of runs D3 and D4

**Date:** 28 October 2026 · **Spec:** [answer-rules.md](../answer-rules.md) (R1 to R9) · **Code:**
Hub `answer-rules` 173c6b5 · **Method:** `work/rules/replay.py` runs the rules on the answers and
In-Depth points the Hub arms shipped in runs D3 `b7bccdd2` and D4 `2a053c09`, for the scenarios of
the two patients with Hub fixture charts (aloice-mukangu, zabella-halambe; ellcky-minayo has no
fixture), and joins each finding to both judges' verdicts. This is the development set: the rules
were written from these runs' faults, so the replay shows they do what they were written for and
how often they misfire on the same answers, not how they generalise (that is R10's run).

## Marks (fail findings) against the judges

| Rule | Marks | A judge faulted it | Both judges faulted it |
| --- | ---: | ---: | ---: |
| Drug citation (In-Depth) | 19 | 19 | 17 |
| Diagnosis presence (Answer) | 14 | 14 | 14 |
| Drug class (In-Depth) | 10 | 10 | 10 |
| Demographics citation (In-Depth) | 10 | 10 | 5 |
| Demographics citation (Answer) | 7 | 7 | 7 |
| Relative time (In-Depth) | 4 | 4 | 0 |
| Advanced HIV disease (In-Depth) | 2 | 2 | 2 |
| All | 66 | 66 | 55 |

Answer marks count a cell as faulted when the judge's accuracy is below 7 or its citation
groundedness is partly or unsupported. Relative time is the weakest rule (each mark faulted by one
judge only); two earlier misfires found in this replay were fixed before the count (a span quoting
the record's own question, "adherence in the past week [11]", and a span with no number,
"previous months").

## Edits (info findings)

| Rule | Edits | Cells |
| --- | ---: | --- |
| Window | 14 | the two "past 6 months" orders scenarios in every arm, each judged accuracy 5 for the older orders the edit now leaves out |
| Drug citation (Answer) | 7 | am-orders-6mo: [34] (efavirenz) dropped from the trimethoprim and sulfamethoxazole group the judges named |
| Series readings | 14 | am-weight-trend, convo-vitals-monitoring t3 |
| Stale latest value | 63 | answers about weight, CD4, blood pressure and oxygen saturation, last measured 5 to 8 months before the reference date |

Whether the edits raise the judged scores is R10's question; the window edit removes the exact
records both judges named in every faulted orders cell.
