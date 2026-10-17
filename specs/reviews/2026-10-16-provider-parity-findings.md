# Provider parity: why Hub answers are slow (16 October 2026)

Findings behind the [provider parity](../provider-parity.md) thread, from this
session's read of the pinned sources, the router log on the owner's Mac and the
old harness records. Numbers below are observations on two machines, not a
controlled benchmark; the thread's first item produces that.

## Measured gap

| Provider, profile | Owner's Mac (16 Oct, after reset) | Ross's Mac (15 Oct) |
| --- | --- | --- |
| ChartSearchAI built-in, Gemma 4 12B through the shared router | not measured | 42 s |
| Hub `single-12b-checked` | 282 s and 467 s | about 20 min |

Both Hub turns ([account-context record](2026-10-16-account-context.md)) asked
"What is this patient's most recent weight?" on the sample chart.

## What each Hub answer does today

- The Hub's selector admitted about 16,500 tokens for that question: its
  32-record "recent clinical core" plus matching records (Hub trace,
  `context_selection` steps, `input_tokens` 16,435–17,041 per stage).
- The nurse's turn made seven model calls: answer, review, grounding, In-Depth,
  two In-Depth reviews and a retry. Each large call was read in full by the router
  at 150–210 prompt tokens per second, 80–110 s per call
  (`artifacts/llama-router/router.log`, `prompt eval time` lines for tasks 0, 73,
  164, 246, 491 and 647).
- The router does reuse identical prompts: repeats of the same prompt processed
  5–1,030 tokens instead of 16,500 (tasks 328, 403, 562, 729, 899). The stage
  prompts simply do not share a start.

## Why the stages cannot reuse each other's prompt

- No Hub commit has ever asked llama-server to reuse a prefix: the chat payload
  carries model, messages, temperature, max_tokens, tools, response_format and
  penalties only (`server/team.py`, `_chat`); `cache_prompt`, `id_slot` and
  `n_keep` appear only in README text (Hub `50e65fa`, `96d0489`, PR #32).
- The review and grounding prompts have put their instruction before the records
  since Hub `c3215ee` (8 June). The answer and In-Depth prompts share a layout,
  but Hub `5368b02` (25 July, PR #13) gave each stage its own re-selected record
  view, and two other calls run between them.
- Gate G13, Hub prompt reuse, was deferred on 24 July because query-scoped
  context was the operating default (old harness
  `openmrs-dual-provider-parity-roadmap-status.md`). The Hub README's "Deferred
  full-chart prefix reuse" section records the design it would need.
- Gemma 4 uses sliding-window attention layers. Without `--swa-full`, llama-server
  can reuse such a model's prompt only back to a saved checkpoint
  ([llama.cpp #13194](https://github.com/ggml-org/llama.cpp/pull/13194),
  [#15293](https://github.com/ggml-org/llama.cpp/pull/15293),
  [#24587](https://github.com/ggml-org/llama.cpp/issues/24587)). The router
  preset has never set it; its history since June shows only the dry, batch and
  penalty settings changing (harness `9d67fbb`, `8cd18f6`; umbrella `d1073e7`).

## What changed since July

| When | Change | Effect |
| --- | --- | --- |
| July | ChartSearchAI ADR Decision 28 made query-scoped context the default: on a CPU host, first answers 12–27 s against 73–74 s full chart; mean F1 0.800 against 0.733 | Built-in provider fast and more accurate |
| 15 July | Harness context-cache research plan recorded Hub end-to-end times: E4B 71 s, 12B 165 s; input limit 20,480 tokens | Last recorded Hub baseline |
| 4 Oct | Hub `05a40fb` (PR #33) and umbrella `ff09aa2` made `single-12b-checked` the default | Roughly doubles Hub time against E4B |
| 6 Oct | ChartSearchAI `6aa25193` (#603) returned the default to full chart, "against this decision's own measurements" | Fresh installs get the slower built-in mode; our setup sets no mode |
| 7 Oct | The umbrella context evaluation ran query-scoped with `topK` 12 | Measured configuration differs from the shipped default |
| 9 Oct | Umbrella PR #9 removed the launcher that ran `scripts/warm-hub-profile.py` at startup | First Hub answer no longer pre-paid; the script remains a diagnostic |

ChartSearchAI's own per-chart warmup (`chartsearchai.warmupEnabled`) is a no-op
when `chartsearchai.llm.engine` is `remote` (module README), which the research
setup sets so the built-in provider shares the router. Its disk cache is
local-engine only.

## Not established

- Whether the Hub's July 165 s and today's 282–467 s differ because of the extra
  In-Depth review passes, the router build (`0.4.0`, build 10809, installed
  6 September), machine load, or prompt size. The fixed-set baseline settles this.
- The built-in provider's time on the owner's Mac.
