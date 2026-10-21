# Review layers L2 to L5 built (20 October 2026)

Evidence for the second to fifth items of [review-process.md](../review-process.md).
Harness changes are in
[clinical-ai-validation-harness#199](https://github.com/pmanko/clinical-ai-validation-harness/pull/199),
pinned in the umbrella at its branch head until it merges.

## L2 review

`make review PR=85 REPO=querystore EFFORT=low AGENT=claude` ran one fresh `claude -p`
reviewer on QueryStore #85 at a437269. It returned one blocking finding, ranked paging
that serves records twice or never, with a reproduction it ran (`RankFusion.rrf` sliced
the way the controller does, and `searchByPatient` for a caller without one type
privilege). That is one of the maintainer's two blocking findings on #85; the other, the
bootstrap loop guard, was not found at low effort. `tests/review/test_review_driver.py`
covers the round record and the downgrade of a blocking finding without a failure mode and
evidence. `ROUNDS` above 1 and `STACK=1` have not run live.

## L3 scenarios

`make review PR=88 REPO=querystore SCENARIOS=review-smoke NO_REVIEW=1` built QueryStore #88
at 56360db, deployed it, matched the loaded api jar's sha256 to the build, replayed
`review-smoke` (run fc5aded6), checked it and put the as-found omod back. Three of four
checks failed on resource-type names: the module emits `obs` and `drug_order`, not FHIR
names. With the checks corrected, the same run's results pass all four.

## L4 measurement

`make review MEASURE=context-cohort GOLD=gold/context-cohort-2026-10.json` ran the
40-cell October cohort on the stack as deployed (QueryStore d61c14d, the #88 merge with
the reindex fix) through the bundled 12B parity arm: harness run
f5dcd8ef-c504-451f-b2a0-02771d07c6e4.

| Measure | Value |
| --- | ---: |
| Present cells scored | 18 |
| Mean citation F1 | 0.761 |
| Absent cells abstaining correctly | 22 of 22 |
| Off-topic citations | 0 |
| Unknown citations | 0 |

The one-off #88 evaluation of the earlier session ([record](2026-10-20-querystore-88-retrieval-diversity.md))
scored the same stack at 0.761 with its own runner and the module's scorer, so the harness
path reproduces it. The run step brought the parity taps up and restored the module's three
`chartsearchai.llm.*` properties and the Hub's engine afterwards. No gate is signed yet; the
owner sets the threshold.
