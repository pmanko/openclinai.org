# Provider parity measurements (16–17 October 2026)

Measurements for the [provider parity](../provider-parity.md) thread on the
owner's Mac (64 GB), Gemma 4 12B Q8 through the shared llama.cpp router
(`ctx-size` 24576, one slot). Each run asks the same five questions on the
sample HIV chart as `eval-nurse` at Outpatient Clinic, through
`POST /ws/rest/v1/chartsearchai/chat/stream`: the built-in provider
(`provider=bundled`) and the Hub's `single-12b-checked` profile. Per-call prompt
size, tokens read and read time come from the router log
(`scripts/time-chart-questions.py`). A handful of questions on one machine:
enough to see direction, not a benchmark.

ChartSearchAI keeps one conversation per patient, user and provider, so in the
baseline and configuration runs each question also carried the earlier
questions as history (up to four turns). Repeated experiment runs later carried
up to twelve, including an earlier wrong answer the model then copied. From the
Hub-change run on, each question starts a fresh conversation.

Machine load matters more than expected. With 21 unrelated OpenELIS and Catalyst
containers running, the router read prompts at 150–210 tokens per second; with
only the HIV stack it read 450–600, until a browser page took a full core and
reading fell back to about 150 during the last question.

## Baseline

Umbrella `claude/provider-parity` at the PR #16 specs, Hub `3269502`,
ChartSearchAI `ca136063`, `chartsearchai.chartMode=fullChart`, router without
`swa-full`.

| Question | Built-in | Hub first answer | Hub complete | Hub calls | Tokens read / sent | Hub read time |
| --- | --- | --- | --- | --- | --- | --- |
| Latest weight | 7 s | 6 s | 102 s | 7 | 34,720 / 100,345 | 67 s |
| Current medications | 46 s | 39 s | 157 s | 6 | 74,800 / 74,836 | 139 s |
| Latest CD4 and viral load | 8 s | 37 s | 153 s | 6 | 67,407 / 67,443 | 131 s |
| Drug allergies | 6 s | 44 s | 128 s | 3 | 56,359 / 56,377 | 120 s |
| HIV care summary | 90 s | 107 s | 552 s | 7 | 69,833 / 86,414 | 395 s |

- The built-in provider's whole chart (12,200 tokens) was already in the router's
  cache from an interrupted first run, so its times are mostly writing. Its cold
  first answer in that interrupted run, under the heavier load, took 89 s.
- The Hub's first two calls of the weight question were also cached from that
  run. Otherwise the router reused almost nothing: every review, In-Depth and
  In-Depth review call re-read 16,000–19,000 tokens.
- The two providers agreed on weight (71 kg), CD4 (341, no viral load) and
  allergies (none recorded). For medications the built-in provider also listed
  efavirenz; the Hub named nevirapine, lamivudine and stavudine. The Hub's
  In-Depth section ended in `indepth_error` on the weight and allergy questions.
- Hub time outside model calls (selection, token counting, QueryStore) was
  20–35 s per answer.

## Configuration only

`chartsearchai.chartMode=queryScoped` (default `topK` 12) and `swa-full` on the
router's Gemma 4 12B preset; Hub unchanged. The router had just restarted, and
the router read at about 170 tokens per second throughout, a third of the
baseline's rate, so compare tokens read rather than seconds.

| Question | Built-in | Hub first answer | Hub complete | Hub calls | Tokens read / sent | Hub read time |
| --- | --- | --- | --- | --- | --- | --- |
| Latest weight | 34 s | 8 s | 344 s | 7 | 50,185 / 100,345 | 282 s |
| Current medications | 73 s | 126 s | 515 s | 6 | 74,361 / 74,836 | 479 s |
| Latest CD4 and viral load | 15 s | 108 s | 401 s | 6 | 67,050 / 67,443 | 356 s |
| Drug allergies | 17 s | 104 s | 317 s | 3 | 56,347 / 56,377 | 301 s |
| HIV care summary | 58 s | 148 s | 588 s | 7 | 68,733 / 86,414 | 428 s |

- Query-scoped mode cut the built-in provider's prompt from the 12,200-token
  whole chart to 3,000–4,700 tokens per question, of which it read 360–2,900.
  It gave the same answers to the four factual questions as in full-chart mode.
- `swa-full` changed nothing for the Hub: its stages still share no prompt start,
  so it read 317,000 tokens over the five answers against 303,000 at baseline.
  It does let the router reuse an identical prompt start, as the last call of
  the weight question shows (16,434 tokens sent, 55 read).
- Why the Hub prompts are large: the selected records are only about 1,200
  tokens. The rest is the Hub's chart-wide temporal facts block, about 14,800
  tokens, the same for every question on this chart, which every stage sent
  after its own instructions. The Hub's `compact` temporal render would cut it
  to about 11,600.

## Hub reads the records once

Hub `1f506b4` ([Hub #36](https://github.com/pmanko/med-agent-hub/pull/36)):
every stage sends the same context message first (the temporal facts, then the
selected records) and its instructions after it, and later stages keep the
answer's records when they fit. Configuration as above; each question in a fresh
conversation, both providers.

| Question | Built-in | Hub first answer | Hub complete | Hub calls | Tokens read / sent | Hub read time |
| --- | --- | --- | --- | --- | --- | --- |
| Latest weight | 11 s | 7 s | 16 s | 4 | 2,705 / 50,429 | 7 s |
| Current medications | 34 s | 13 s | 29 s | 6 | 5,205 / 74,712 | 14 s |
| Latest CD4 and viral load | 7 s | 39 s | 56 s | 6 | 18,976 / 67,380 | 40 s |
| Drug allergies | 7 s | 12 s | 20 s | 3 | 4,642 / 56,283 | 12 s |
| HIV care summary | 27 s | 12 s | 36 s | 6 | 3,896 / 68,499 | 10 s |

- Over the five answers the Hub read 35,000 tokens, against 303,000 at baseline.
  After the first answer on the chart, each answer re-read 1,400–3,400 tokens of
  its first prompt and 400–800 for every later stage.
- The CD4 answer re-read its whole first prompt although the temporal facts
  matched the previous answer's; why the router missed that prefix is not
  established.
- The Hub's checked answers were correct on all five: 71 kg on 2026-01-26; the
  three current antiretrovirals; CD4 341 on 2025-11-24 and no viral load; no
  allergies recorded; a summary of the regimen and stage. In-Depth was shown on
  three of five, as at baseline.
- Each Hub answer now finishes within 2–3 times the built-in provider's time,
  inside the thread's two-minute aim on this machine.

## Hub sends less for narrow questions

Hub `4ff82ef` ([Hub #36](https://github.com/pmanko/med-agent-hub/pull/36)) fixes a
bug that kept the Hub from using QueryStore's question-scoped slice: rebuilding
records after drug-reference injection dropped each record's slice tier and
rank, so with drug safety on (every product profile) the selector fell back to
its own 32-record recent core plus word overlap. With the fix, selection is
relevance-led: 33–96 records, 1,000–2,800 tokens, no recent core.

| Question | Built-in | Hub first answer | Hub complete | Hub calls | Tokens read / sent | Hub read time |
| --- | --- | --- | --- | --- | --- | --- |
| Latest weight | 9 s | 112 s | 133 s | 4 | 18,326 / 50,420 | 112 s |
| Current medications | 38 s | 164 s | 204 s | 6 | 21,014 / 74,195 | 131 s |
| Latest CD4 and viral load | 7 s | 114 s | 150 s | 6 | 19,202 / 68,266 | 117 s |
| Drug allergies | 15 s | 112 s | 129 s | 3 | 19,707 / 54,606 | 115 s |
| HIV care summary | 51 s | 30 s | 83 s | 6 | 4,598 / 67,174 | 28 s |

- The records were never the large part. What each answer's first prompt still
  carries is the temporal facts block (14,800 tokens), which is the same for
  every question on the chart.
- In this run the router reused that block across questions only once in five,
  against three times in four in the previous run, with the same prompts and
  similar match ratios in its log; why is not established. Within an answer,
  reuse held: later stages read 400–800 tokens each. The router also read at
  140–170 tokens per second here, against about 400 in the previous run.
- Cutting the temporal facts to the selected records would leave 8,600–11,200
  tokens, because the date ledger, appointment and visit summaries are
  chart-wide by design (temporal facts may cite records the selection left
  out). The `compact` render would leave 11,600. Neither was adopted.
- Checked answers were correct on all five; In-Depth was shown on one of five.
- ChartSearchAI's 40-cell question set could not be run: none of its 30 gold
  patients exist in the HIV database.

## Fast checked profile

Hub `49e4201` adds `single-12b-fast`: every Answer check (gates, review,
reference resolution, grounding) and no In-Depth, as an explicit choice beside
the default `single-12b-checked`.

| Question | Hub fast first answer | Hub fast complete | Calls | Tokens read / sent |
| --- | --- | --- | --- | --- |
| Latest weight | 107 s | 123 s | 3 | 17,564 / 33,688 |
| Current medications | 162 s | 179 s | 3 | 19,179 / 37,454 |
| Latest CD4 and viral load | 113 s | 129 s | 3 | 17,876 / 34,282 |
| Drug allergies | 123 s | 134 s | 2 | 18,961 / 36,410 |
| HIV care summary | 31 s | 52 s | 3 | 2,832 / 33,612 |

- Answers matched the checked profile's on all five, and no In-Depth events
  were sent.
- The time is almost all the first prompt: the router again re-read the
  temporal facts on four of five questions, at about 160 tokens per second. On
  the one question where it reused them, the fast answer finished in 52 s.
- So the remaining gap to the built-in provider on this machine is the
  router's cross-question reuse of the 14,800-token temporal facts, plus
  machine load. Turning on llama-server's verbose logging for one run would
  show why it re-reads a prefix it reports as 80% shared.
