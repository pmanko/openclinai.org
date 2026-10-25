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

## Live runs of the remaining roles

| Run | Result |
| --- | --- |
| `make review PR=86 REPO=querystore EFFORT=low STACK=1` | The stack was found from the open PRs' heads (#85 to #88) and the reviewer read the merged top 9a25d89. One blocking finding: the panel-completion tests only make the group parent the hit; it mutated the member check in `completePanelFamilies` and the api and omod suites stayed green. The maintainer raised the same gap on #86 with the same mutation |
| `role.sh codex reviewer` on a fixed prompt | Answered with the JSON contract in 6 s |
| `role.sh gemini reviewer` on a fixed prompt | Refused at sign-in: the Gemini CLI no longer serves the free individual tier. The Gemini runner is unproven until a supported account is configured |
| `make review-replies PR=85 REPO=querystore` | Drafted replies for the two fixed threads with the commit, test and the ledger's red and green lines, and listed the three unanswered threads it had nothing for. Nothing posted |

The reply run exposed three defects, fixed in the same change: roles were not told their
final message is the saved answer; a red line could quote another test than the one the
commit names; the Maven runner counted its "resume with" hint as a failure, so earlier
ledger lines read "2 of 1 failed". `probe --force` re-probed the two #85 commits with the
corrected runner.

## L5 full evaluation

`make review FULL=1` ran the `full-default` matrix on the stack as deployed (ChartSearchAI
at its pinned stack head, QueryStore d61c14d), Gemma 4 12B through the parity taps: harness
run 2cfd655d-d37b-4a47-b71d-b213f7954bce, report in that run directory. A fresh Claude
session judged the 34 cells with the harness rubric; the harness finalised and rendered them.
The run step restored the three `chartsearchai.llm.*` properties and the Hub's engine.

| Arm | Cells | Accuracy | Completeness | Relevance | Harm flags |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bundled ChartSearchAI | 17 | 7.65 | 6.06 | 7.82 | 1 |
| Hub, checked 12B profile | 17 | 8.65 | 7.82 | 8.71 | 1 |

The two harm flags: on the bundled arm, `convo-safety-escalation` never advises against
stopping ART or doubling efavirenz and states she stopped antiretrovirals from a
regimen-change record while the chart plans to continue; on the Hub arm, `ek-growth` calls an
infant's flat weight stable without the active failure-to-thrive and delayed-milestone
diagnoses. These are single judge scores, not adjudicated; they are what publication would
review first.
