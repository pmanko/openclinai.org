# Decision-layer experiment

**Spec ID:** `DECISION-LAYER-2026-10` · **Status:** proposed, awaiting owner review;
updated 27 October 2026 for the label-only pipeline in [checked-answers.md](checked-answers.md) ·
**Owners:** harness (protocol and evidence), Med Agent Hub (any runtime knob),
umbrella (coordination and publication)

**Question.** Can a typed decision model make the Hub's closed yes/no grounding and
review-verification decisions that set answer and In-Depth labels, and screen harness
answer evaluations, at least as well as the current generative check, faster, and with
calibrated probabilities, on synthetic data? TypeSafe's Jev is the hosted ceiling
reference. Self-hostable arms are a local entailment cross-encoder (`MiniCheck` /
DeBERTa / ModernBERT-NLI class) for zero-shot grounding and review-flag verification, a
local cross-encoder reranker for context admission, and Laya trained on our relevance
labels (its base checkpoint is near chance zero-shot).

Rationale, Jev primer and the initial mapping of Hub decision points to decision-model
primitives are in the [10 October review](reviews/2026-10-10-revamp-audit-and-jev-experiment.md),
sections 4 to 6. The mechanism, the Laya finding, the access situation and a
decision-by-decision reading of a checked Hub turn are in the
[16 October research update](reviews/2026-10-16-decision-layer-research-update.md).
Since [checked-answers.md](checked-answers.md) (27 October), the Hub never rewrites
answers or drops In-Depth claims; only deterministic temporal checks edit text, while
the reviewer and grounder set the answer, citation and In-Depth labels under
`policies.review`. This spec holds only the target path, gates, rules and status. Tick a
box only with a link to the evidence (PR, run directory or dated review).

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

Phase 0a needs only files committed to this repository and runs first. Phase 0b replays
the captured 17-scenario `full-default` L5 run traces ([26 October](reviews/2026-10-26-l5-full-default.md)
and [checked-answers.md](checked-answers.md) Run A) from `targets/validation-harness/artifacts/validate/`
and `artifacts/hub-trace/trace.jsonl`. Every Jev route is refused by the cloud coding
environment's network policy, so Jev calls in Phase 0 run on the workstation or after
`openrouter.ai` is allowed there (D5).

#### Phase 0a: context admission

Input: the [7 October context evaluation](reviews/2026-10-07-context-evaluation.md)
frozen [gold](reviews/2026-10-07-context-evaluation/gold.json): five patients, eight
topics, 980 records, 7,840 record–topic pairs, 91 on-topic.

- [ ] P0.1 Access: Jev route chosen (OpenRouter `typesafe/jev-1.13`, TypeSafe direct,
      or Vercel's gateway where per-request zero retention is wanted) and key kept in an
      ignored env file; local entailment cross-encoder, reranker and Laya weights
      fetched to the workstation and recorded by name and hash.
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

#### Phase 0b: grounding and review-label replay

- [ ] P0.2 Harness script `scripts/decision-replay.py` extracts from the `full-default`
      L5 traces every Answer `(source text, statement)` grounding pair, every In-Depth
      claim with its cited sources and review `flag` verdicts, every Answer reviewer
      `errors[]` `(wrong, chart)` pair from `_validate_answer_label`, and the
      `stage_timing` steps into a dated run directory with manifest and provenance. The
      stage timings also show the review stage's share of turn latency, which P3.2
      depends on.
- [ ] P0.3 Jev and a local zero-shot entailment cross-encoder answer the Noul yes/no for
      each extracted item, with a probability: Answer citation pairs under
      [`_ENTAILMENT_SYSTEM_PROMPT`](https://github.com/pmanko/med-agent-hub/blob/main/server/team.py),
      In-Depth citation pairs under `_ATTRIBUTION_SYSTEM_PROMPT` (record attribution)
      and a separate clinical-consistency Noul, and reviewer `errors[]` pairs under a
      contradiction-verification Noul ("does `chart` contradict `wrong`?").
- [ ] P0.4 About 120 pairs sampled across Answer grounding, In-Depth attribution and
      reviewer-error cells, adjudicated blind as supported, unsupported or unclear, with
      reviewer id and time per
      [`adjudicate.adjudication_record`](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/harness/validate/adjudicate.py),
      joined with the three-pass blinded judge panel (`gpt-6-astra` and
      `claude-opus-5-5`, [judging.md](judging.md)) on `citation_groundedness`,
      `accuracy` and `harm`.
- [ ] P0.6 Metrics computed for the LLM grounder (`separate` and `folded`), Jev and the
      local entailment cross-encoder: kappa versus human adjudication and the judge
      panel's `citation_groundedness`; recall of `unsupported`; false-positive rate on
      In-Depth marks and Answer `errors[]` (how many false yellow/red `needs_review`
      labels are suppressed without missing a judged error or harm cell); Brier score
      and expected calibration error with at least ten observations per bin; conditional
      agreement on cells where the LLM checker is wrong versus right; `unchecked` rate
      versus decision-model coverage; latency per batch versus `ground_verdicts` and
      `review` stage timings; cost per turn. Binary verdicts use the prespecified 0.5
      threshold on probability. Three-band thresholds (`verified` green, `uncertain`
      yellow, `unsupported` red) are fit on a calibration split of the adjudicated pairs
      and reported on the held-out split; G1 does not use them.
- [ ] P0.7 Dated review written covering Phases 0a and 0b.
- [ ] **G1** At the prespecified 0.5 threshold, Jev or the local entailment
      cross-encoder reaches a kappa within 0.05 of the LLM grounder's, recall of
      `unsupported` at least the LLM grounder's, and errors that are not a subset of the
      LLM grounder's. Among qualifying arms the local model is preferred for Hub
      integration. Fail: Phase 2 and P3.1 to P3.3 close with the review. Phase 1 and
      P3.4 do not depend on G1.

### Phase 1: second judge actor (harness, evaluation of answers)

- [ ] P1.1 Rubric mapping fixed and recorded: Score over the five anchored bands of
      the [Scout rubric](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/.claude/skills/clinical-answer-scoring/rubric.md)
      for ordinal axes (Answer and Background), mapped to band midpoints; Choice for
      categorical axes; yes/no for `harm` and `background_no_new_harm`.
- [ ] P1.2 Chart snapshots checked against the 32K-token context; oversized cells
      excluded and listed.
- [ ] P1.3 Jev rows built from `judge-cells.jsonl` for the [26 October L5 run](reviews/2026-10-26-l5-full-default.md)
      and [checked-answers.md](checked-answers.md) Run A, finalized with
      [`judge-finalize.py`](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/scripts/judge-finalize.py)
      `--actor jev-1.13 --actor-type llm-judge`, never `--promote`.
- [ ] P1.4 Agreement and prediction-powered inference against the [judging.md](judging.md)
      panel (`gpt-6-astra` and `claude-opus-5-5`) and existing human adjudications;
      error correlation between actors reported.
- [ ] P1.5 Dated review written.
- [ ] **G2** Categorical-axis agreement with humans and the canonical judge panel at
      least single-pass LLM judge agreement, and no missed known-harm cell. Pass: Jev
      becomes a screening actor that feeds [judging.md](judging.md) C6 adjudication
      sampling. Fail: Jev stays out of evaluation.

### Phase 2: shadow mode in the Hub (conditional on G1)

- [ ] P2.1 Change record drafted from the harness
      [PCCP template](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/pccp-change-record-template.md);
      Hub owner review.
- [ ] P2.2 Extend `policies.review` in
      [`levels_loader.py`](https://github.com/pmanko/med-agent-hub/blob/main/server/levels_loader.py)
      and one `visibility: evaluation` profile in
      [`levels.yaml`](https://github.com/pmanko/med-agent-hub/blob/main/server/levels.yaml)
      so `ground_verdicts`, `review` and `indepth_gate` run the qualifying decision
      model in shadow alongside the configured checker: both verdicts and probabilities
      recorded in `groundingChecks[].method`, `groundingChecks[].probability` and the
      trace steps (`answer_review`, `indepth_validator`); the shipped envelope labels
      unchanged; the P0.6 three-band thresholds recorded as a proposed policy, not
      applied; not advertised by `GET /v1/models`.
- [ ] P2.3 The 17-scenario `full-default` L5 suite rerun through the harness;
      disagreement rate, `unchecked` rate, false-positive `needs_review` rate and stage
      latency compared.
- [ ] P2.4 Dated review written.
- [ ] **G3** Every shadow disagreement explained case by case and the stage latency
      change measured. Decide which Phase 3 items feed into [checked-answers.md](checked-answers.md)
      A6 label consolidation.

### Phase 3: Hub decision-making (design review before code)

P3.1 to P3.3 are conditional on G3; P3.4 on G0.

- [ ] P3.1 Three-band citation and In-Depth attribution labels (`policies.review.grounding: decision`):
      replace the binary generative entailment call in `_ground_references` and
      `indepth_gate` with the qualifying decision model's calibrated three-band policy
      (`verified` green, `uncertain` yellow caution, `unsupported` red `needs_review`),
      decoupling In-Depth record attribution (`_ATTRIBUTION_SYSTEM_PROMPT`) from
      clinical interpretation marks; compared against A5/A6 judged labels.
- [ ] P3.2 Review-flag verification and optional pre-gate (`policies.review`):
      (a) verify candidate `errors[]` from `_validate_answer_label` and `flag[]` from
      `_validate_indepth_verdict` with a Noul contradiction check, overruling
      unverified reviewer flags in `overruled_by_decision_check` before they set
      `answerValidation.status = "needs_review"` or `confidence.answer.level = "yellow"`
       while keeping the generative reviewer's `wrong` and `chart` note when confirmed;
      (b) if P0.2 stage timings justify it, add a sentence-level Noul pre-gate that
      invokes the generative reviewer only when a sentence is flagged (requires an
      honest label and a [provider contract](../docs/openmrs-provider-interface.md)
      update through the umbrella before product use). Deterministic gates stay
      unconditional.
- [ ] P3.3 Team orchestrator routing by Choice, only if team profiles return to the
      product path ([checked-answers.md](checked-answers.md) A8).
- [ ] P3.4 Context admission: per-record relevance probability as the budget drop
      order and a recall net over the Hub's zero-relevance bucket, engine-side beside
      the local selector in [`context_sources.py`](https://github.com/pmanko/med-agent-hub/blob/main/server/context_sources.py);
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
- [ ] D3 Include a local zero-shot entailment cross-encoder in Phase 0b alongside Jev,
      and Laya as a trained arm on the Phase 0a relevance pairs only (recommended: yes;
      zero-shot Laya is dropped, see the 16 October update).
- [ ] D4 Confirm the Phase 2 shadow policy lives under `policies.review` in a Hub PR
      with its change record (Hub owner).
- [ ] D5 Where Phase 0 runs: the owner's workstation, or the cloud coding environment
      after `openrouter.ai` is allowed and the key is set (owner).

## Budget

Phases 0 and 1: three to five working days including two to three hours of blind
adjudication, plus about one day for Laya fine-tuning following its model card's
notebook. Jev requests at the reported price cost well under one dollar per thousand
decisions; the reranker and Laya run on the workstation.
