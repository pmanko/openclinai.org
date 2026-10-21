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
