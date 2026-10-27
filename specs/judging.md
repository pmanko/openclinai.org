# Judging: who scored a run, how many times, and how the scores combine

Owner: umbrella (this spec), harness (scoring, report, dashboard), umbrella `review/`
(running the judge, publication, the catalog). Research and recon behind it: the owner's
26 October plan (`work/judging-plan-2026-10-26.md`, working file) and the harness's
[evaluation methodology brief](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/artifacts/planning/eval-methodology-brief.md).

## Goal

Every judged score on a report, dashboard or catalog page names the judge that produced it
(model, reasoning effort, agent and version, pass, brief), a run can be judged several times
by one judge or by judges of different families, the pages show the consensus and the
disagreement with chance-corrected agreement, and a comparison between runs is made only
between like judges.

## Decisions (owner, 26 October 2026)

- One pass by default; before every judging run the owner is asked which judge, effort and
  how many passes.
- Across passes: median per 0-10 axis, majority per categorical axis; a harm tie counts as
  harmful.
- A panel of judge families is on request, not the default.
- Arm identities are blinded to the judge and sessions are split per scenario.
- Re-judging the 22 October baseline with gpt-6-astra is on hold.

## Target path

- [ ] C1 Judge card. Every pass writes `judges/<actor>/manifest.json`; `judges/canonical.json`
  names the pass the headline came from; the report, the dashboard, the run summary and the
  catalog say "Judged by ...", or that no judge was recorded. Harness
  [#200](https://github.com/pmanko/clinical-ai-validation-harness/pull/200); umbrella: this
  branch (`review/bin/role.sh` writes the session card, `review.py` adds the brief hash and
  pass, publication carries it to the catalog). The two published L5 runs get their cards
  from the local session logs and are republished.
- [ ] C2 Repeated passes. `make review FULL=1 ... JUDGE_PASSES=N` runs N fresh sessions as
  actors p1..pN; the canonical rows are the per-cell median and majority (harness
  `judge-aggregate.py`); Krippendorff's alpha per axis across passes, with the 0.667 and 0.8
  thresholds stated, and the highest-spread cells listed on the page (harness
  `agreement.py`, `judges/consensus.json`). Built on harness #200 and umbrella #28; evidence is
  the first published three-pass run.
- [ ] C3 Panel. `--judge agent:model:effort`, repeatable; per-judge arm scores side by side,
  inter-judge alpha, the disagreement cells as the priority sample for human adjudication; a
  judge from an arm's own model family is refused or flagged.
- [ ] C4 Isolation. One bundle per scenario with arm identities replaced by letters, one
  session per bundle, the letters mapped back at finalize.
- [ ] C5 Drill-down and like-for-like comparison. Every pass's scores and note per cell (the
  report's heatmap note and the dashboard's cell panel); the run summary says whether the
  baseline was judged the same way (model, effort, brief, aggregation), and
  `make review REJUDGE=<run> ...` scores a run's frozen cells again with the current judge.
  Built on harness #200 and umbrella #28; evidence is the first run compared like for like.
- [ ] C6 Human calibration stays as built (`validate-adjudicate`, PPI); C3's disagreement
  cells feed its sample.

Verification of each checkpoint is its behavior tests in the harness and the umbrella, and a
dated review under `reviews/` for the first run that uses it.
