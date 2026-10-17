# Provider parity and local inference efficiency

**Thread:** Hub answers at least as fast as ChartSearchAI's built-in provider, on
the same machine, model and router · **Status:** causes identified, nothing fixed;
no measured baseline yet · **Owners:** Med Agent Hub (prompt layout, selection,
profiles), umbrella (router preset, setup settings, measurement, publication)

The external provider must not perform worse than the product it extends. On
Ross's Mac the built-in provider answered in 42 s and the Hub's checked 12B
profile in about 20 minutes; here the Hub takes 5–8 minutes. The
[16 October findings](reviews/2026-10-16-provider-parity-findings.md) record why:
every Hub stage re-reads a 16,500-token prompt, the stages share no prompt
start, the router cannot reuse Gemma's prompt without `swa-full`, and the
defaults for the model and ChartSearchAI's context mode both changed in October.

## Goal

A checked Gemma 4 12B answer on the sample chart in at most 2 minutes on the
owner's Mac and 5 on Ross's, and in every case no slower than the built-in
provider with the same model and router, with quality on ChartSearchAI's 40-cell
gate no worse than today. Measured on a fixed question set.

## Rules

- Checked Gemma 4 12B stays the default; smaller models and hosted models are
  explicit comparisons in the picker.
- Budgets are ceilings. Nothing truncates silently; mandatory evidence that does
  not fit fails as `insufficient_context`.
- Reuse is proven by the server's own reused and processed token counts in the
  trace, never by warmup claims. Startup warmups stay diagnostics.
- Every change is re-measured on the fixed question set before it is ticked, and
  a selection change also passes ADR Decision 28's two gates: the 40-cell
  evaluation and the temporal probe.
- No chart text in logs or committed artifacts; identifiers and counts only.

## Target path

- [ ] P0 Baseline: a fixed 5-question set on the sample chart, run as `eval-nurse`
      against both providers, reporting per model call the prompt tokens, prompt
      read time, generation time and reused tokens from the router log and Hub
      trace; today's numbers recorded in a dated review.
- [ ] P1 Configuration only: `swa-full` for the local Gemma 4 12B preset; research
      setup selects `chartsearchai.chartMode=queryScoped` and
      `chartsearchai.querystore.topK=30`, ADR Decision 28's measured settings;
      P0 re-run.
- [ ] P2 The Hub reads the records once per answer: one selection per answer, the
      same records block first in every stage with the stage instruction after
      it, and the server's reused and processed counts in the trace. Later stages
      process only their own suffix; the 40-cell gate is unchanged.
- [ ] P3 Selection sized to the question and the model: a smaller recent core,
      relevance-driven admission, and each profile's window sized to its model.
- [ ] P4 An explicit "fast checked" profile without In-Depth for live sessions;
      the default keeps In-Depth.
- [ ] P5 An OpenRouter comparison profile with the same 24,576-token budget and
      local tokenizer counting, explicit in the picker, with one recorded answer,
      its cost and its time.
- [ ] G-parity On one machine, question set, model and router, Hub checked
      answers take no longer than the built-in provider and score no lower on
      the 40-cell gate; Ross re-measures on his Mac.

## Decisions

- Gate G13 of the OpenMRS parity contract (Hub prompt reuse and measured backend
  timing) is owned here. Its 24 July deferral assumed query-scoped context was
  the operating default, which ChartSearchAI #603 ended on 6 October.
- The acceptance rules of the harness's
  [15 July context-cache research plan](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/chart-context-cache-research-plan-2026-07-15.md)
  apply to P2 and P3: correctness with cache on and off, freshness, isolation,
  citation integrity and measured prompt reuse.
- Re-adding a startup warm is not a path to parity: it pre-pays one answer, and
  ChartSearchAI's per-chart warmup is a no-op under the shared router.
