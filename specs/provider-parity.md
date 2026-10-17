# Provider parity and local inference efficiency

**Thread:** make Hub answers about as fast as ChartSearchAI's built-in provider on
the same machine · **Status:** causes identified, nothing changed yet ·
**Owners:** Med Agent Hub (prompts, selection, profiles), umbrella (router preset,
setup settings, measurement)

The external provider should not be much slower than the product it extends.
On Ross's Mac the built-in provider answered in 42 s and the Hub's checked 12B
profile took about 20 minutes; here the Hub takes 5–8 minutes. The
[16 October findings](reviews/2026-10-16-provider-parity-findings.md) say why:
every Hub stage re-reads a 16,500-token prompt, the stages share no prompt
start, the router cannot reuse Gemma's prompt without `swa-full`, and the
default model and ChartSearchAI's default context mode both changed in October.

## Direction

Aim for a checked Gemma 4 12B answer in about 2 minutes here and about 5 on
Ross's Mac, roughly what the built-in provider manages, without obviously worse
answers. This is exploratory: numbers from a handful of fixed questions are
enough to see whether a change helps.

Checked Gemma 4 12B stays the default; smaller and hosted models are explicit
comparisons in the picker.

## Steps

- [x] Baseline: ask the same five questions of both providers and note, per model
      call, the prompt size, read time and how much the router reused
      ([17 October](reviews/2026-10-17-provider-parity-measurements.md#baseline)).
- [x] Configuration only: `swa-full` for the local Gemma 4 12B preset, and the
      query-scoped context mode ChartSearchAI measured as faster and more
      accurate in July (`chartsearchai.chartMode=queryScoped`, with the module's
      default `chartsearchai.querystore.topK` of 12). Re-run the five questions
      ([17 October](reviews/2026-10-17-provider-parity-measurements.md#configuration-only)).
- [x] Hub reads the records once per answer: one selection per answer, the same
      records block first in every stage, instructions after it, so the router's
      cache does the rest. Re-run
      ([17 October](reviews/2026-10-17-provider-parity-measurements.md#hub-reads-the-records-once)).
- [ ] Hub sends less for narrow questions: a smaller recent core and relevance-led
      admission; each profile's window sized to its model. Re-run, and spot-check
      answers on ChartSearchAI's 40-cell question set.
- [x] A "fast checked" profile without In-Depth for live sessions, as an explicit
      choice ([17 October](reviews/2026-10-17-provider-parity-measurements.md#fast-checked-profile)).
- [ ] An OpenRouter comparison profile with the same context budget, with one
      recorded answer, its time and its cost.
- [ ] Ross re-measures on his Mac.

## Notes

- Gate G13 of the OpenMRS parity contract (Hub prompt reuse) lives here now. Its
  July deferral assumed query-scoped context was the default, which ended with
  ChartSearchAI #603 in October.
- A startup warm only pre-pays the first answer, and ChartSearchAI's per-chart
  warmup is a no-op when the built-in provider uses the shared router. Neither
  is a substitute for the Hub reading the records once.
