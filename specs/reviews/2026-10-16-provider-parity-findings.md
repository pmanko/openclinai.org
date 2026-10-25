# Provider parity: why Hub answers are slow (16 October 2026)

Findings behind the [provider parity](../provider-parity.md) thread, from reading
the pinned sources, the router log on the owner's Mac and the old harness notes.
Observations on two machines, not a controlled benchmark.

## The gap

| Provider | Owner's Mac (16 Oct) | Ross's Mac (15 Oct) |
| --- | --- | --- |
| ChartSearchAI built-in, Gemma 4 12B through the shared router | not measured | 42 s |
| Hub `single-12b-checked` | 282 s and 467 s | about 20 min |

Both Hub turns asked for the sample patient's most recent weight
([record](2026-10-16-account-context.md)).

## What a Hub answer does today

- The Hub's selector admitted about 16,500 tokens for that question: its
  32-record "recent clinical core" plus matching records.
- The nurse's turn made seven model calls (answer, review, grounding, In-Depth,
  two In-Depth reviews and a retry). The router read each large prompt in full
  at 150–210 tokens per second, 80–110 s per call.
- The router does reuse a prompt it has seen: repeats processed 5–1,000 tokens
  instead of 16,500. The stage prompts simply do not share a start: review and
  grounding put their instruction first, and In-Depth re-selects its records.
- No Hub code has ever asked the router to reuse a prefix. The Hub README's
  "Deferred full-chart prefix reuse" section records the idea (gate G13), deferred
  in July because query-scoped context was the default then.
- Gemma 4 uses sliding-window attention. Without `--swa-full`, llama-server can
  reuse such a model's prompt only back to a saved checkpoint
  ([llama.cpp #13194](https://github.com/ggml-org/llama.cpp/pull/13194)). The
  router preset has never set it.

## What changed since July

| When | Change | Effect |
| --- | --- | --- |
| July | ChartSearchAI made query-scoped context the default (ADR Decision 28): first answers 12–27 s against 73–74 s full chart on a CPU host, with better citation scores | Built-in provider fast |
| 15 July | Harness context-cache plan recorded Hub times: E4B 71 s, 12B 165 s | Last Hub baseline |
| 4 Oct | Hub PR #33 and the umbrella made checked 12B the default | Roughly doubles Hub time against E4B |
| 6 Oct | ChartSearchAI #603 returned the default to full chart | Fresh installs get the slower built-in mode; our setup sets no mode |
| 9 Oct | Umbrella PR #9 stopped running the Hub warm script at startup | First Hub answer no longer pre-paid; the script remains |

ChartSearchAI's per-chart warmup is a no-op when `chartsearchai.llm.engine` is
`remote`, which the research setup sets so the built-in provider shares the
router.

## Not established

- Why today's Hub turns (282–467 s) are slower than July's 165 s: extra In-Depth
  review passes, the newer router build, machine load or prompt size. The
  baseline step settles this.
- The built-in provider's time on the owner's Mac.
