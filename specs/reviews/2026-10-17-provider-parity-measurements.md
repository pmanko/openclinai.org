# Provider parity measurements (16–17 October 2026)

Measurements for the [provider parity](../provider-parity.md) thread on the
owner's Mac (64 GB), Gemma 4 12B Q8 through the shared llama.cpp router
(`ctx-size` 24576, one slot). Each run asks the same five questions on the
sample HIV chart as `eval-nurse` at Outpatient Clinic, through
`POST /ws/rest/v1/chartsearchai/chat/stream`: the built-in provider
(`provider=bundled`) and the Hub's `single-12b-checked` profile. Per-call prompt
size, tokens read and read time come from the router log. A handful of questions
on one machine: enough to see direction, not a benchmark.

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
  It gave the same answers as in full-chart mode.
- `swa-full` changed nothing for the Hub: its stages still share no prompt start,
  so it read 317,000 tokens over the five answers against 303,000 at baseline.
  It does let the router reuse an identical prompt start, as the last call of
  the weight question shows (16,434 tokens sent, 55 read).
- Why the Hub prompts are large: the selected records are only about 1,200
  tokens. The rest is the Hub's chart-wide temporal facts block, about 14,800
  tokens, the same for every question on this chart, which every stage sent
  after its own instructions. The Hub's `compact` temporal render would cut it
  to about 11,600.
