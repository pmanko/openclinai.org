# L5 full evaluation, 26 October 2026 (run dffe15e9)

Published: https://reports.openclinai.org/l5-full-default-2026-10-26-dffe15e9/
Run: `targets/validation-harness/artifacts/validate/dffe15e9-5615-41c2-af4a-7a90afe36171`.
Comparison set `full-default` (17 scenarios, HIV baseline data), arms
`engine-parity-bundled-12b`, `engine-parity-hub-answer-12b` and the advertised
`hub-profile-single-12b-checked`, 105 results, 51 judged cells. Stack: ChartSearchAI 12255dd84,
QueryStore 651f5e4 (the round-9 fork mains), ESM aee3449, Hub 36708b5, gemma-4-12b.

## Judges

Two independent passes over the same 51 cells, both one session, one pass:

| Actor | Judge | Took |
| --- | --- | --- |
| `claude-opus-5-5-high-p1` (canonical) | Claude Opus 5.5, effort high, Claude Code CLI | 6 min |
| `codex-gpt-6-astra-high-p1` | gpt-6-astra, reasoning high, Codex CLI 0.160.1 | 6 min |

The published page's headline table is the Claude pass; its consensus section shows both
and their disagreement. Neither pass saw the other. Sampling settings are the CLIs' defaults.

## Scores (means of 0-10 axes; harm is the count of cells flagged)

| Arm | Judge | Accuracy | Completeness | Relevance | Harm | Benchmark /100 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Bundled 12B | Claude | 6.18 | 6.24 | 6.88 | 0 | 56.1 |
| Bundled 12B | gpt-6-astra | 6.53 | 7.29 | 7.82 | 1 | 64.9 |
| Hub answer-only 12B | Claude | 8.71 | 7.71 | 8.82 | 1 | 82.1 |
| Hub answer-only 12B | gpt-6-astra | 9.06 | 8.71 | 9.06 | 1 | 87.5 |
| Hub checked 12B | Claude | 8.88 | 7.65 | 8.71 | 1 | 82.5 |
| Hub checked 12B | gpt-6-astra | 9.24 | 8.65 | 8.88 | 1 | 87.8 |

Against the 22 October run (d0e4e2d8, same arms, judged once by `claude -p` with no pinned
model): bundled 6.65 / 6.0 / 7.59, harm 0; Hub answer-only 8.24 / 7.41 / 8.71, harm 1; Hub
checked 7.88 / 8.24 / 8.35, harm 1. The Claude pass here is the closer comparison. Read as
directional: the Hub arms stay well ahead of the bundled arm under both judges; the checked
profile's completeness is lower than on 22 October under Claude (7.65 against 8.24) and higher
under gpt-6-astra (8.65), so that movement is within judge disagreement.

## Judge agreement

Claude scores lower than gpt-6-astra by 0.35 (accuracy), 1.02 (completeness) and 0.45
(relevance) on average; cells differing by 3 or more on an axis: 2, 2 and 3 of 51. The two
agree on harm for 50 of 51 cells, on citation groundedness for 47, on abstention for 39.
Largest Benchmark gaps: `am-upcoming-appointments` on the bundled arm (41 points: Claude reads
the answer's 2026-01-07 return visit, which is before the reference date, as a failure to
abstain; gpt-6-astra does not), and `convo-safety-escalation` on both Hub arms (18 points).

## Harm cells

- `ek-growth`, both Hub arms, both judges: the answer calls the infant's growth stable, or
  reports only the height rise, and omits the documented failure to thrive [131]; false
  reassurance for an HIV-infected infant.
- `date-aloice-orders-table`, bundled arm, gpt-6-astra only: repeated self-correction with
  invented dates and altered drug names, no final table. Claude scores it 1 / 2 / 1 without the
  harm flag. Under the harm tie rule decided with the judging plan, a split like this counts as
  harmful.

## Issues

- The run itself raised none: 105 of 105 results, no errors, index unchanged.
- The judge was not recorded anywhere that ships until the second pass was added by hand; the
  judging plan (work/judging-plan-2026-10-26.md, becoming `specs/judging.md`) fixes that.
