# Decision-layer experiment

**Spec ID:** `DECISION-LAYER-2026-10` · **Status:** proposed, awaiting owner review;
research updated 16 October 2026 ·
**Owners:** harness (protocol and evidence), Med Agent Hub (any runtime knob),
umbrella (coordination and publication)

**Question.** Can a typed decision model make the Hub's closed yes/no decisions and
screen harness answer evaluations at least as well as the current generative check,
faster, and with calibrated probabilities, on synthetic data? TypeSafe's Jev is the
hosted reference. Laya is the self-hostable arm, trained on our labels; its base
checkpoint is near chance zero-shot. For context admission the arm that could ship is
a local cross-encoder reranker.

Rationale, Jev primer and the mapping of Hub decision points to decision-model
primitives are in the [10 October review](reviews/2026-10-10-revamp-audit-and-jev-experiment.md),
sections 4 to 6. The mechanism, the Laya finding, the access situation and a
decision-by-decision reading of a checked Hub turn are in the
[16 October research update](reviews/2026-10-16-decision-layer-research-update.md).
This spec holds only the target path, gates, rules and status. Tick a box only with a
link to the evidence (PR, run directory or dated review).

## Rules

- Synthetic OpenMRS HIV demo data only. No real patient data leaves the workstation.
- No change to product profiles, provider or mode selection, or deterministic gates
  before Phase 2 is reviewed.
- Every run records the provider route, model version (pin `jev-1.13`), request and
  response digests and timestamps in its manifest. OpenRouter's `typesafe/jev-router`
  is a different product and never a route.
- A decision-model verdict is a separately attributed actor. It never replaces a
  deterministic result and is never the promoted judge, because it carries no rationale.
- Rule-made labels are recorded as such. The context-evaluation gold was produced by
  `build_gold_rc2.py`. Records any arm disputes are pooled and adjudicated without arm
  identities; the corrected gold is frozen with its hash before any arm's metrics are
  computed, and metrics are reported against both the original and the corrected gold.
- Each phase ends with a dated review in `specs/reviews/`. This spec gets the ticked
  box and the link, nothing else.

## Target path

### Phase 0: offline replay (harness, no live product)

Phase 0a needs only files committed to this repository and runs first. Phase 0b needs
the `hub-profile-candidate` and `small-model-answer-paths` run packets, which live in
the harness run directories on the owner's workstation. Every Jev route is refused by
the cloud coding environment's network policy, so Phase 0 runs on the workstation or
after `openrouter.ai` is allowed there (D5).

#### Phase 0a: context admission

Input: the [7 October context evaluation](reviews/2026-10-07-context-evaluation.md)
frozen [gold](reviews/2026-10-07-context-evaluation/gold.json): five patients, eight
topics, 980 records, 7,840 record–topic pairs, 91 on-topic.

- [ ] P0.1 Access: Jev route chosen (OpenRouter `typesafe/jev-1.13`, TypeSafe direct,
      or Vercel's gateway where per-request zero retention is wanted) and key kept in an
      ignored env file; reranker and Laya weights fetched to the workstation and
      recorded by name and hash.
- [ ] P0.5 Relevance yes/no for every record and topic of the five patients from three
      arms: Jev; an untrained off-the-shelf local cross-encoder reranker; Laya
      fine-tuned on four patients' pairs and tested on the fifth, rotating. The Hub's
      current selection (QueryStore slice tiers plus the local ranker) replayed over
      the same ledgers is the baseline. Each arm scored as recall of on-topic records
      and precision per patient and topic, with a calibration curve; disputed records
      adjudicated blind and the corrected gold frozen per the rules before scoring;
      report whether patient 39's three dropped renal records are admitted.
- [ ] **G0** Relevance result recorded against the frozen corrected gold. P3.4 may use
      an arm only if its recall of on-topic records is at least the current
      selection's at no lower precision, per patient and topic; if no arm qualifies,
      P3.4 closes. Among qualifying arms a local one that matches Jev is preferred
      because it can ship.

#### Phase 0b: grounding replay

- [ ] P0.2 Harness script `scripts/decision-replay.py` extracts every (source text,
      statement) grounding pair, every In-Depth claim with its cited sources, and the
      `stage_timing` steps from the packets into a dated run directory with manifest
      and provenance. The stage timings also show the review stage's share of turn
      latency, which P3.2 depends on.
- [ ] P0.3 Jev answers the grounding yes/no for every pair, with a probability, using
      the Hub's criteria from [`_ENTAILMENT_SYSTEM_PROMPT`](https://github.com/pmanko/med-agent-hub/blob/32695025f5ef77e0096aeef2d9b5907776234a82/server/team.py).
- [ ] P0.4 About 120 pairs sampled across cells, adjudicated blind as supported,
      unsupported or unclear, with reviewer id and time per
      [`adjudicate.adjudication_record`](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/harness/validate/adjudicate.py).
- [ ] P0.6 Metrics computed: kappa versus human for Gemma and Jev; recall of
      `unsupported`; Brier score and expected calibration error with at least ten
      observations per bin; Jev agreement conditional on Gemma being right or wrong;
      Gemma's `unchecked` rate versus Jev coverage; latency per batch versus the
      `ground_verdicts` stage timing; cost per turn. Jev's binary verdict is the
      prespecified 0.5 threshold on its probability. The probability bands that best
      reproduce the adjudicators' three labels are fit on a calibration split of the
      adjudicated pairs and reported on the held-out split; G1 does not use them.
- [ ] P0.7 Dated review written covering Phases 0a and 0b.
- [ ] **G1** At the prespecified 0.5 threshold, Jev reaches a kappa within 0.05 of
      Gemma's, recall of `unsupported` at least Gemma's, and its errors are not a
      subset of Gemma's. Fail: Phase 2 and P3.1 to P3.3 close with the review.
      Phase 1 and P3.4 do not depend on G1.

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
      [`levels.yaml`](https://github.com/pmanko/med-agent-hub/blob/32695025f5ef77e0096aeef2d9b5907776234a82/server/levels.yaml)
      with a `grounding_backend` knob: both verdicts and probabilities recorded in
      `groundingChecks[].method` and the trace; the shipped verdict unchanged; the P0.6
      probability bands recorded as a proposed threshold policy, not applied; not
      advertised by `GET /v1/models`.
- [ ] P2.3 `small-model-answer-paths` rerun through the harness; disagreement rate,
      `unchecked` rate and stage latency compared.
- [ ] P2.4 Dated review written.
- [ ] **G3** Every shadow disagreement explained case by case and the stage latency
      change measured. Decide whether any Phase 3 item is worth its contract cost.

### Phase 3: Hub decision-making (design review before code)

P3.1 to P3.3 are conditional on G3; P3.4 on G0.

- [ ] P3.1 In-Depth claim drops by per-claim yes/no instead of the one-shot JSON
      verdict; claims dropped compared with adjudicated labels.
- [ ] P3.2 Review gate: a fast check decides whether the slow repair runs. The decision
      model answers the contradiction yes/no and localises per sentence; the generative
      reviewer repairs and writes the clinician-facing note only when the check fails.
      Deterministic gates stay unconditional. Needs a new honest label and a change to
      the [provider contract](../docs/openmrs-provider-interface.md) through the
      umbrella before any product use; built only if the P0.2 stage timings show the
      review stage's latency share justifies it.
- [ ] P3.3 Team orchestrator routing by Choice, only if team profiles return to the
      product path.
- [ ] P3.4 Context admission: per-record relevance probability as the budget drop
      order and a recall net over the Hub's zero-relevance bucket, engine-side beside
      the local selector in [`context_sources.py`](https://github.com/pmanko/med-agent-hub/blob/32695025f5ef77e0096aeef2d9b5907776234a82/server/context_sources.py);
      arm chosen by G0; QueryStore's selection contract unchanged.

## Not in scope

- Provider, mode or profile selection by any model.
- Replacing deterministic temporal, date or drug-safety gates.
- Question interpretation or record selection inside QueryStore; its context slice
  stays mechanical (ADR Decision 17).
- Sending non-synthetic patient data to a remote decision model.
- A decision model in a default product profile before a domain calibration audit
  and a change record exist.

## Decisions

- [ ] D1 Approve Phases 0 and 1 as a harness experiment on synthetic data (owner).
- [ ] D2 Jev access route and adjudicator tier for the 120 pairs (owner).
- [ ] D3 Include Laya as a trained arm on the relevance pairs only (recommended: yes;
      the zero-shot arm is dropped, see the 16 October update).
- [ ] D4 Confirm the Phase 2 knob lives in a Hub PR with its change record (Hub owner).
- [ ] D5 Where Phase 0 runs: the owner's workstation, or the cloud coding environment
      after `openrouter.ai` is allowed and the key is set (owner).

## Budget

Phases 0 and 1: three to five working days including two to three hours of blind
adjudication, plus about one day for Laya fine-tuning following its model card's
notebook. Jev requests at the reported price cost well under one dollar per thousand
decisions; the reranker and Laya run on the workstation.
