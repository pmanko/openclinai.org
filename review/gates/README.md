# Model gates

A gate is written, signed off and committed before the run it governs; `make review
GATE=<name>` refuses a gate file that is uncommitted or changed. A threshold chosen after
seeing the number is not a gate.

1. Measure the baseline on the stack as deployed, through the same path the gate uses:
   `make review MEASURE=context-cohort GOLD=gold/context-cohort-2026-10.json`.
2. Write `<name>.md` with these lines, then the reason for the threshold in prose:

```
set: context-cohort
gold: gold/context-cohort-2026-10.json
metric: meanF1
direction: higher
baseline_run: <run id printed by step 1>
baseline: <the number step 1 printed>
threshold: <the number the head must reach>
date: <YYYY-MM-DD>
signed_off: <who agreed the threshold>
```

   `metric` is a key of the scorer's per-arm summary (`meanF1`, `abstention_accuracy`,
   `offtopic_citations`, `unknown_citations`); `backend:` names the arm when the set has
   more than one.
3. Commit it, then `make review PR=<n> REPO=<module> GATE=<name>`: the base (the layer
   below, or `GATE_BASE=<ref>`) and the head are each deployed, run and scored; the head's
   number against the threshold decides. The record is `work/review/<component>-<encoded-repository>-<pr>/gate-<name>.md`;
   cite it in a dated review under `specs/reviews/`.
