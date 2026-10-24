# QueryStore #98 retrieval diversity: context evaluation, 21 October 2026

This is a dated evaluation record for QueryStore [#98](https://github.com/openmrs/openmrs-module-querystore/pull/98)
against its base [#97](https://github.com/openmrs/openmrs-module-querystore/pull/97) on the restacked local
tips, run with the [7 October method](2026-10-07-context-evaluation.md) on the default HIV baseline. It
answers the reviewer's request for scope and temporal results at this head. It is evidence, not a requirement
or an acceptance decision. The [20 October record](2026-10-20-querystore-88-retrieval-diversity.md) measured
the same change, then #88, against #87.

## Result

| Measure (same cohort, questions, gold and model as 7 October) | #97 | #98 |
|---|---|---|
| Present cells scored (of 40 scope cells) | 18 | 18 |
| Mean F1 over present cells | 0.819 | 0.801 |
| Absent cells answered correctly | 21/22 | 22/22 |
| Off-topic citations (drift) | 3 | 0 |
| Temporal cases passing all three checks | 14/15 | 14/15 |
| Temporal cases needing source-ambiguity review | 1 | 1 |
| Captures returned 200 | 55/55 | 55/55 |

Seven cells differ. #98 gains on four: patient 39's heart cell goes from no citation to its on-topic record
(F1 0 to 1.00) and its kidney cell from 1 to 2 on-topic records (F1 0.50 to 0.80); patient 36's medications
cell names efavirenz, which #97 left out (F1 0.40 to 0.50); and patient 5587's heart cell, where #97 cited
three off-topic records for an absent topic, abstains (the drift and abstention rows above).

Three medications cells lose recall: patient 39 from 18 cited on-topic records to 4 (F1 1.00 to 0.36),
patient 2606 from 15 to 6 (1.00 to 0.57) and patient 3666 from 24 to 5 (1.00 to 0.34). In all three the answer
names the same drugs in both arms; #98 cites the newest order of each drug where #97 cited every repeat order.
That is the designed behaviour of the diversified similarity tier, which groups repeats of one concept and
keeps the newest, and the gold counts each repeat order as an on-topic record. On 20 October the same trade-off
cost one medications cell; on this stack it costs three, because #97 now cites the full repeat series that #87
did not. Whether a citation per repeat order matters to a reader is the trade-off for the reviewer to weigh.

The temporal review case is the one recorded in October and on 20 October: patient 5587 has three weights at
the same newest timestamp, and both arms answer 55 kg citing that real record without explaining the tie.

Latency is comparable in this run: median 7.6 s per question in both arms, 465 s and 488 s in total.

## What was run

- Stack: `make chartsearch-research-setup` from the restacked local tips (QueryStore 057eae4, ChartSearchAI
  0edae2e8c, ESM 7f71ddb), baseline hiv-20261020-231108, restored without recomputing the index. Settings as
  found matched October: query-scoped chart mode, grounding and drug reference off, remote gemma-4-12b through
  the router, topK 12. The rate limit was raised to 1000 for the captures and restored to 10 afterwards.
- Arms: #98 at 057eae4 (the setup's build, clean tree, omod sha256 42afea2a...) and #97 at 0d6d2c0 (clean tree,
  omod sha256 6a77adf9...), each checked inside the recreated backend container. Each arm re-projected the five
  October patients with `POST /querystore/reindex {"patient"}`, checked every chart against the frozen record
  universe (320/121/168/157/214), and captured the 55 questions through `POST /chartsearchai/search` in the
  October order. Afterwards the #98 build was restored and the five patients re-projected with it.
- Scoring: `targets/chartsearchai/eval/drift-metric/metric_score.py` over each arm's captures with an empty
  adjudication file and the October `gold.json`, and the October temporal checks against its frozen
  `temporalTruth` with the 20 October `lastVisitTies`.

Evidence in [2026-10-21-querystore-98-retrieval-diversity/](2026-10-21-querystore-98-retrieval-diversity/):
`captures.json` (both arms' unmodified responses), `scores.json` (per-cell scope scores, temporal checks and
timings per arm) and `provenance.json` (manifests, record universe, settings, tie set and the run notes).
