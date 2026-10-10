# Decision-layer experiment

**Spec ID:** `DECISION-LAYER-2026-10` · **Status:** proposed, awaiting owner review ·
**Owners:** harness (protocol and evidence), Med Agent Hub (any runtime knob),
umbrella (coordination and publication)

**Question.** Can a typed decision model make the Hub's closed yes/no decisions and
screen harness answer evaluations at least as well as the current generative check,
faster, and with calibrated probabilities, on synthetic data? TypeSafe's Jev is the
hosted reference; Laya is the self-hostable arm that could actually ship.

Rationale, Jev primer and the mapping of Hub decision points to decision-model
primitives are in the [10 October review](reviews/2026-10-10-revamp-audit-and-jev-experiment.md),
sections 4 to 6. This spec holds only the target path, gates, rules and status.
Tick a box only with a link to the evidence (PR, run directory or dated review).

## Rules

- Synthetic OpenMRS HIV demo data only. No real patient data leaves the workstation.
- No change to product profiles, provider or mode selection, or deterministic gates
  before Phase 2 is reviewed.
- Every run records the provider route, model version (pin `jev-1.13`), request and
  response digests and timestamps in its manifest.
- A decision-model verdict is a separately attributed actor. It never replaces a
  deterministic result and is never the promoted judge, because it carries no rationale.
- Each phase ends with a dated review in `specs/reviews/`. This spec gets the ticked
  box and the link, nothing else.

## Target path

### Phase 0: offline replay (harness, no live product)

Inputs already on disk: the `hub-profile-candidate` and `small-model-answer-paths`
run packets with Hub traces, and the
[7 October context evaluation](reviews/2026-10-07-context-evaluation.md) captures
with their frozen [gold](reviews/2026-10-07-context-evaluation/gold.json).

- [ ] P0.1 Access: Jev route chosen (OpenRouter or direct) and key kept in an ignored
      env file; Laya weights fetched to the router host.
- [ ] P0.2 Harness script `scripts/decision-replay.py` extracts every (source text,
      statement) grounding pair, every In-Depth claim with its cited sources, and the
      `stage_timing` steps from the packets into a dated run directory with manifest
      and provenance.
- [ ] P0.3 Jev and Laya answer the grounding yes/no for every pair using the Hub's
      criteria from [`_ENTAILMENT_SYSTEM_PROMPT`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/team.py).
- [ ] P0.4 About 120 pairs sampled across cells, adjudicated blind as supported,
      unsupported or unclear, with reviewer id and time per
      [`adjudicate.adjudication_record`](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/harness/validate/adjudicate.py).
- [ ] P0.5 Relevance yes/no for every record and topic of the five context-evaluation
      patients, scored against the frozen gold; report whether patient 39's three
      dropped renal records are admitted.
- [ ] P0.6 Metrics computed: kappa versus human for Gemma, Jev and Laya; recall of
      `unsupported`; Brier score and expected calibration error with at least ten
      observations per bin; Jev agreement conditional on Gemma being right or wrong;
      Gemma's `unchecked` rate versus decision-model coverage; latency per batch versus
      the `ground_verdicts` stage timing; cost per turn.
- [ ] P0.7 Dated review written.
- [ ] **G1** Jev or Laya reaches a kappa within 0.05 of Gemma's, recall of
      `unsupported` at least Gemma's, and its errors are not a subset of Gemma's.
      Fail: close the experiment at Phase 0 with the review.

### Phase 1: second judge actor (harness, evaluation of answers)

- [ ] P1.1 Rubric mapping fixed and recorded: Score over the five anchored bands of
      the [Scout rubric](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/.claude/skills/clinical-answer-scoring/rubric.md)
      for ordinal axes, mapped to band midpoints; Choice for categorical axes; yes/no
      for harm.
- [ ] P1.2 Chart snapshots checked against the 32K-token context; oversized cells
      excluded and listed.
- [ ] P1.3 Jev rows built from `judge-cells.jsonl` for the checked 12B candidate run
      and the method-scaffolding run, finalized with
      [`judge-finalize.py`](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/scripts/judge-finalize.py)
      `--actor jev-1.13 --actor-type llm-judge`, never `--promote`.
- [ ] P1.4 Agreement and prediction-powered inference against the Claude judge and
      existing human adjudications; error correlation between the two actors reported.
- [ ] P1.5 Dated review written.
- [ ] **G2** Categorical-axis agreement with humans at least the Claude judge's and no
      missed known-harm cell. Pass: Jev becomes a screening actor that feeds
      adjudication sampling. Fail: Jev stays out of evaluation.

### Phase 2: shadow mode in the Hub (conditional on G1)

- [ ] P2.1 Change record drafted from the harness
      [PCCP template](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/pccp-change-record-template.md);
      Hub owner review.
- [ ] P2.2 One `visibility: evaluation` profile in
      [`levels.yaml`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/levels.yaml)
      with a `grounding_backend` knob: both verdicts and probabilities recorded in
      `groundingChecks[].method` and the trace; the shipped verdict unchanged; not
      advertised by `GET /v1/models`.
- [ ] P2.3 `small-model-answer-paths` rerun through the harness; disagreement rate,
      `unchecked` rate and stage latency compared.
- [ ] P2.4 Dated review written.
- [ ] **G3** Every shadow disagreement explained case by case and the stage latency
      change measured. Decide whether any Phase 3 item is worth its contract cost.

### Phase 3: Hub decision-making (conditional on G3, design review before code)

- [ ] P3.1 In-Depth claim drops by per-claim yes/no instead of the one-shot JSON
      verdict; claims dropped compared with adjudicated labels.
- [ ] P3.2 Review gate: a yes/no contradiction pre-check decides whether the rewrite
      validator runs. Deterministic gates stay unconditional. Needs a new honest label
      and a change to the [provider contract](../docs/openmrs-provider-interface.md)
      through the umbrella before any product use.
- [ ] P3.3 Team orchestrator routing by Choice, only if team profiles return to the
      product path.

## Not in scope

- Provider, mode or profile selection by any model.
- Replacing deterministic temporal, date or drug-safety gates.
- Sending non-synthetic patient data to a remote decision model.
- A decision model in a default product profile before a domain calibration audit
  and a change record exist.

## Decisions

- [ ] D1 Approve Phases 0 and 1 as a harness experiment on synthetic data (owner).
- [ ] D2 Jev access route and adjudicator tier for the 120 pairs (owner).
- [ ] D3 Include Laya as the self-hostable arm (recommended: yes).
- [ ] D4 Confirm the Phase 2 knob lives in a Hub PR with its change record (Hub owner).

## Budget

Phases 0 and 1: three to five working days including two to three hours of blind
adjudication. Jev requests at the reported price cost well under one dollar per
thousand decisions; Laya runs on the existing router host.
