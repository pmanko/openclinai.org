# QueryStore #88 retrieval diversity: context evaluation, 20 October 2026

This is a dated evaluation record for QueryStore [#88](https://github.com/openmrs/openmrs-module-querystore/pull/88)
against its base [#87](https://github.com/openmrs/openmrs-module-querystore/pull/87), run with the
[7 October method](2026-10-07-context-evaluation.md) on the 20 October HIV baseline. It is evidence, not
a requirement or an acceptance decision. It also records the reindex defect found while preparing the
run and the fix that corrected it.

## Result

| Measure (same cohort, questions, gold and model as 7 October) | #87 | #88 |
|---|---|---|
| Present cells scored (of 40 scope cells) | 18 | 18 |
| Mean F1 over present cells | 0.705 | 0.761 |
| Absent cells answered correctly | 22/22 | 22/22 |
| Off-topic citations (drift) | 0 | 0 |
| Temporal cases passing all three checks | 14/15 | 14/15 |
| Temporal cases needing source-ambiguity review | 1 | 1 |
| Captures returned 200 | 55/55 | 55/55 |

Three cells differ. Two kidney cells that #87 answered without any record now cite the newest creatinine
order or result: patient 39 kidney goes from 0 to 1 of 3 on-topic records cited (F1 0.50), patient 3666
kidney from 0 to its single on-topic record (F1 1.00). One medications cell regresses: patient 5587's
three isoniazid orders were all cited by #87, #88 cites only the newest (recall 0.33). That is the
designed behaviour of the diversified similarity tier, which groups repeats of one concept and keeps the
newest, and it is the trade-off a reviewer should weigh. Precision over present cells is 1.00 in every
scored cell of both arms except the two cells with no citation at all; neither arm cites an off-topic or
unknown record.

The one temporal review case is the same in both arms and in October: patient 5587 has three weights at
the same newest timestamp (56, 54 and 55 kg on 2026-06-01); both arms answer 55 kg and cite that real
record without explaining the conflict. Two answers in each arm render a date with a typo
(`2026-06-1`, `2026-0127`); the scorer records them as malformed date tokens and they do not change a
verdict.

Latency is not comparable between the arms in this run. The model server's own throughput, read from
the router log, fell from a median of 19 generated tokens per second during the #87 captures to between
5 and 10 during the #88 captures, with prompt sizes in the same range in both windows (medians between
500 and 1,100 tokens). Elasticsearch's share of one timed question was 65 ms over 40 queries. The per-cell
seconds in `scores.json` are therefore recorded but not a measure of #88.

## What was run

- Baseline: `make chartsearch-research-setup`, hiv-20261019-025659, restored on 20 October without
  recomputing the Elasticsearch index. Settings as in October: query-scoped chart mode, grounding and drug
  reference off, remote gemma-4-12b through the router, topK 12. The rate limit was raised to 1000 for
  the captures and restored to 10 afterwards.
- Cohort: the five October patients with identical record counts (320/121/168/157/214) and all 7,840
  gold record references present. The record universe was frozen in `provenance.json`
  (`recordUniverse`) and each arm's re-projection was checked against it before capture.
- Arms: #87 at 1bd12c1 (clean tree, omod sha256 f6a05775...) and #88 at 56360db merged with the reindex
  fix below (fork branch `codex/eval-88-rewrite-fix`, d61c14d, clean tree, omod sha256 d6b80192...).
  Each arm re-projected the five patients with `POST /querystore/reindex {"patient"}` and captured the
  55 questions through `POST /chartsearchai/search` in the October question-first order.
- Scoring: `targets/chartsearchai/eval/drift-metric/metric_score.py` over each arm's capture directory
  with an empty adjudication file and the October `gold.json`; the temporal checks of October
  (value or visit date matches, a newest source is cited, explicit dates match) against October's frozen
  `temporalTruth`. One correction to the October truth: it kept one encounter per patient for the
  last-visit question, but patient 5587 has three encounters tied at the newest timestamp, so the tie set
  was read from the database and is recorded as `lastVisitTies`; without it the #87 arm's citation of a
  tied encounter would have been a false fail.

Evidence in [2026-10-20-querystore-88-retrieval-diversity/](2026-10-20-querystore-88-retrieval-diversity/):
`captures.json` (both arms' unmodified responses by capture name), `scores.json` (per-cell scope scores,
temporal checks, timings and module provenance per arm) and `provenance.json` (manifests, record universe,
settings, tie set and the run notes).

## The reindex defect found on the way

Preparing the #87 arm, every first `POST /querystore/reindex {"patient"}` returned 200 with
`documentsIndexed: 0`, deleted the patient's documents and left the chart empty, while a repeat about a
minute later succeeded. The cause is Elasticsearch's delete tombstone: the store writes with
`version_type=external_gte` and the record's timestamp as the version, but deleted without a version,
which leaves a tombstone one above the document's version for `index.gc_deletes` (60 s). The reindex
deletes and rewrites the same records at the same timestamp, so every rewrite within a minute was a
version conflict that the store counted as a stale write skipped. One live reindex of patient 39 raised
the Elasticsearch failed-write counter by 320 per shard copy and wrote nothing. The patient-merge sweep
and a void followed by an unvoid lose their rewrites the same way. Both pieces of code are in upstream
main.

The fix is QueryStore [#91](https://github.com/openmrs/openmrs-module-querystore/pull/91): every delete
runs at the document's own version, so an equal-or-newer rewrite applies and a strictly older write still
does not resurrect the record. Three integration tests against a real Elasticsearch failed with 0
documents before the change and pass after it; the older-write guard passes before and after. After
deploying it, two consecutive reindexes of patient 39 both wrote all 320 documents with no failed writes,
and the #88 arm's five re-projections each succeeded on their single attempt.

## Baseline published from this QueryStore

After the evaluation, every obs was re-projected under #88's serializer (`POST /querystore/reindex
{"scope":"type","resourceType":"obs"}`, 427,890 documents, 21:32 to 23:10 UTC, index complete, drift
zero for encounters and visits), and the stack was exported and published as the new default baseline
`hiv-20261020-231108` (514,682 indexed documents, built from umbrella commit 9e05629 with QueryStore
d61c14d). The database carries the evaluation's 116 audit-log rows from this day and no conversations.

## Limits

- One capture per cell on the same small substitute cohort as October; the three changed cells are
  single observations.
- The #88 arm ran on a merge of #88 with #91, not on #88 alone, because the reindex cannot be trusted
  without the fix. The merge touches only the Elasticsearch delete paths.
- Latency could not be attributed to the arms because the host's model throughput changed between the
  two windows; a paired timing run under equal conditions is still owed if latency matters for the
  decision.
- October's base scored a mean F1 of 0.891 on the same gold; this baseline's #87 arm scores 0.705 with the
  same abstention and drift results. The difference is between the October stack and the 20 October
  baseline, not between the two arms, and is not examined here.
