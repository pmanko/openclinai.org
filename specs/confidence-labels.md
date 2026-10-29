# Confidence labels: findings, not grades

**Spec ID:** `CONFIDENCE-LABELS-2026-10` · **Status:** proposed 27 October 2026 from the
dashboard review of runs 5ac27952 and 8dacd7b1; the owner has read the proposals and agrees
with most; decisions below are open until marked · **Owners:** umbrella (this spec, gates,
runs), Hub (label semantics, checkers, prompts, sampling), harness (measurement), ChartSearchAI
frontend (what the clinician sees)

This stream remediates how a checked answer earns its labels. It takes over
[checked-answers.md](checked-answers.md) A6 (label consolidation) and sets the bar every
check must clear before it may change what a clinician sees. The arms and runs stay in
checked-answers.md; judging stays in [judging.md](judging.md); the decision-layer
experiment stays in [decision-layer-experiment.md](decision-layer-experiment.md) and is
not changed by this spec (see "Interface with the decision-layer experiment").

## Findings (27 October 2026)

Runs 5ac27952 (the Hub before the In-Depth fixes) and 8dacd7b1 (after them, with a DRY-off
arm), 17 scenarios, 35 turns per arm.

- Nothing shown today is a measured confidence. Each check yields one yes/no from one
  sample of a small model; a section turns red when any check fires; no check's precision
  has been measured.
- The architecture multiplies false alarms. Up to three checks per In-Depth point and about
  three points per In-Depth give about nine chances to mark a section; at a 5% false alarm
  rate per check, about 37% of correct In-Depths go red. The judged Answer accuracy is about
  8.8 of 10, so most points are right and a checker that is 90% right on both kinds still
  produces red that is half false. In run 8dacd7b1, 35% of the default arm's In-Depth
  points are marked (32 of 92) and 22 of 32 In-Depths need review.
- The citation prompt pushed checkers to "no": "answer NO unless fully certain from the
  source text alone". Qwen3.6 took it literally and rejected every one of 8 probe claims,
  including the 4 correct ones; that is why arm 3 marked 45 of about 51 cited In-Depth
  claims. A facts-first prompt (list the patient facts, mark each found or not) scores 10 of
  10 on gemma-4-12b, qwen3.6-35b and qwen3.5-9b.
- The checker's one-word verdict contradicts its own fact list: 18 of the default arm's 28
  In-Depth citation failures, and 7 of Qwen's 35, say "not supported" after finding every
  fact.
- Incomplete citing is scored as a wrong fact: "from 52 kg to 41 kg [21]" fails because [21]
  holds only the 41 kg.
- The Answer citation check still runs the old strict prompt; on the Qwen arm 13 of 35
  answers are `needs_review`, and in run 5ac27952 the judge rated 6 of its 9 flagged cells
  fully supported.
- Same-model review catches little: the 12B Answer citation check flagged 2 cells the judge
  also faulted and missed 2; the folded variant caught 0 of 4; the Qwen reviewer's flags
  were mostly wrong under the old prompt. Cross-family review is still the right design
  ([verification across families beats self-verification, 37 models, 9 benchmarks](https://arxiv.org/abs/2512.02304)).
- The judge saw the checks' verdicts until 27 October (source grounding status, check
  results, marks after each point), so earlier agreement between judge and checks is partly
  circular. Fixed on harness `e92b752`; the judge now also gives a verdict per In-Depth
  point.
- DRY (multiplier 0.8, allowed length 8, penalty range the whole 24k context) garbles copied
  dates: 14 of 204 answers in run 5ac27952 had dates like `2026-01_26`; a controlled
  blood-pressure list derailed with DRY on and was clean with it off. In run 8dacd7b1 the
  DRY-off arm had 0 garbled turns against 4 for the default, 29 of 35 answers identical to
  the default, and 57 s per turn against 72 s. The date check flags a garbled date but never
  repairs it.

## Principles (proposed)

1. Show findings, not grades. A contradiction a check can prove is named with the chart's
   value ("2026-01-15 is not a date in the chart"; "[21] does not state 52 kg"). A doubt a
   model cannot quote is neutral ("not verified"), never red.
2. Three labels per claim: supported, contradicted, not addressed. Only contradicted marks
   a section. Not addressed means the cited record does not hold that fact (incomplete
   citing) and is shown neutrally. This is the scheme of VeriFact, RAGAS and the NLI
   literature ([VeriFact](https://arxiv.org/pdf/2501.16672),
   [LiveRAG NLI](https://arxiv.org/pdf/2507.04942)).
3. The verdict is derived from listed facts, never asked as one word.
4. A section's status is a count and a list (which claims, which checks, what the chart
   says), never "any no means red".
5. A check runs hidden until it is measured. It may change what the clinician sees only
   after its precision against the judge and human adjudication clears the bar in LG1.
6. No High/Medium/Low until a probability is calibrated on labelled claims; verbalised
   confidence from small models is not used
   ([overconfidence in small models](https://www.alphaxiv.org/abs/2604.01457)).
7. Checks that decide (verdicts, JSON, tables, date lists) run at temperature 0 with DRY off.
8. The judge never sees a check's verdict.

## Rules

- Nothing here changes the shipped clinician envelope before LG1 is measured on a judged
  run; new label semantics ship behind the profile's `policies.review` until then.
- Every check has a name the dashboard, the report and the envelope share (date check,
  model review, citation support, record check, agreement).
- A profile is the only place a check is switched on, off or made visible; no engine branch.
- Labelled claims (judge per-point verdicts, human adjudications) are frozen with the run
  before any check's precision is computed, and thresholds fit on a calibration split are
  reported on a held-out split.
- Each phase ends with a dated review in `reviews/`; this spec gets the ticked box and the
  link.

## Target path

### L1 Measurement (harness)

- [ ] L1.1 A harness script scores every check in a judged run against the judge rows: per
  check (date check, model review, citation support, record check, and the section
  statuses), precision of its marks (marked items the judge also faulted), recall of judged
  errors, and the same split by arm. Answer checks score against `citation_groundedness`,
  `accuracy` and `harm`; In-Depth checks against the per-point verdicts the brief asks for
  since 27 October (correct, wrong_fact, wrong_citation, unsupported, guidance). Human
  adjudications (judging.md C6) join as a second reference where they exist. Output: a table
  per run under `judges/check-precision.json`, shown on the report and the dashboard.
- [x] L1.2 Runs 8dacd7b1 and e01674f6 scored, the result recorded with the DRY finding and a
  first calibrated score: [28 October review](reviews/2026-10-28-confidence-labels-runs-a2-c.md);
  run b7bccdd2 (bare, verify, agree) scored and the fit repeated on 958 points:
  [run D3 record](reviews/2026-10-28-confidence-labels-run-d3.md).
- [ ] **LG1** Bar for visibility (owner decision): a check may mark what the clinician sees
  when its precision is at least 0.8 on at least 50 marked items across two judged runs, and
  its marks are not a subset of a cheaper check's. A check below the bar runs hidden and is
  shown only on the dashboard and report. Proposed values; the owner sets them. Status after
  D4: only the deterministic checks mark often enough to measure; the verification review is
  at 0.67 on 6 marks ([record](reviews/2026-10-28-confidence-labels-run-d4.md)).

### L2 Label semantics (Hub envelope, harness, frontend)

- [ ] L2.1 Per-claim labels: every Answer citation group and In-Depth point carries
  `support: supported | contradicted | not_addressed | unchecked` with `facts[]` (fact,
  found, source index) and, for contradicted, the chart's value. `groundingStatus` keeps
  its current values for compatibility and is derived from `support`.
- [ ] L2.2 Section status derived from the labels: `needs_review` only for contradicted
  claims (date check, record check, citation support) or a review flag that clears LG1;
  `not_addressed` and unverified review doubts produce a neutral note; the In-Depth status
  carries the marked count and the list; one marked point among several never reads as a
  low-confidence section.
- [ ] L2.3 `confidence.answer` and `confidence.in_depth` levels are withdrawn from the
  shipped envelope until L9 calibrates them; the fields stay with `level: null` and the
  note names the findings. The frontend shows findings, not the chip, in that state.
- [ ] L2.4 Marks name what the chart has (done for the date check and citation support on
  Hub #44); the review's flags carry the quoted chart record or are shown as unverified.
- [ ] L2.5 The Hub records what a clean check found (`review_status: clean`, citation
  `pass` entries), so the dashboard can say "passed" rather than "no flag recorded".
  Evidence: the Hub envelope PR, the harness presentation PR, the frontend PR.

### L3 Checkers: prompts and mechanics (Hub)

- [ ] L3.1 The Answer citation check uses the facts-first attribution prompt (as the
  In-Depth check does since Hub #44): list the patient facts, mark each found or not with
  the source span; a claim citing several records is supported by them together.
- [ ] L3.2 The verdict is derived from the fact list in code; the model's one-word verdict
  is recorded for the trace and never used.
- [ ] L3.3 Three-way output: a fact the cited record does not hold is `not_addressed` unless
  the record states a different value, which is `contradicted`.
- [ ] L3.4 Batches of at most four pairs per call; balanced few-shot examples (supported,
  contradicted, not addressed) in the prompt; temperature 0; DRY off; the label's
  log-probability recorded as a score where the router exposes it.
- [x] L3.5 The reviewer asks and answers verification questions (Chain-of-Verification:
  questions drawn from the answer, each answered from the chart alone, then compared) and
  reports only contradictions it can quote
  ([CoVe](https://arxiv.org/pdf/2309.11495)); its flags are per sentence with `wrong` and
  `chart`, as the label prompt already returns. Built as the `verify` arm (Hub #46); after run
  D's first turns showed four chart reads and 107 s a turn, the citation verdicts are folded
  into the verification review and the verifier is Qwen3.5-9B (Hub #47). Measured in run D3
  ([record](reviews/2026-10-28-confidence-labels-run-d3.md)): its flags were right where
  judged (1 of 1 answer, 2 of 3 In-Depth points) but too few for LG1; the 9B's own citation
  verdicts were empty in 11 of 35 turns and wrong in all 7 contradictions it did give, so the
  fallback citation check uses the 12B grounding model and the review runs at temperature 0
  (Hub d3-checks). Run D4 on that profile ([record](reviews/2026-10-28-confidence-labels-run-d4.md)): D3 and D4 together give the review 6
  In-Depth marks at 0.67 and 1 of 1 answer mark, about one mark per eleven turns.
- [ ] L3.6 Prompt probes become tests: the ten probe pairs under `work/hub-labels/` move to
  Hub fixtures with the expected label per pair, run against a stub model in CI and against
  the live checkers before a run.

### L4 Deterministic repairs and checks (Hub)

- [ ] L4.1 Underscore date repair: a token that becomes a chart date when `_` is read as
  `-`, with the value beside it matching that date's record, is repaired and the repair is
  noted; unrepairable garbled dates stay flagged.
- [ ] L4.2 Table cells that cite several records are checked by exact date and value against
  those records before any model call (today a two-record cell goes to the model and fails
  on the date).
- [ ] L4.3 The record check (a cited index outside the chart) and the date check keep their
  red marks; they are the proven-contradiction class and clear LG1 by construction once L1.2
  confirms it.

### L5 Sampling policy (Hub profiles, router)

- [ ] L5.1 DRY off for every stage that copies or decides: review, grounding, In-Depth
  review, tables and date lists (the `review` role already allows `dry: 0`; the grounding
  and In-Depth review calls get the knob).
- [x] L5.2 DRY off is the writer's default: no loss on any judged axis, no garbled dates,
  15 s a turn faster ([28 October review](reviews/2026-10-28-confidence-labels-runs-a2-c.md));
  Hub #46 (`SYNTH_DRY_MULTIPLIER` 0) and the router's `[*]` section.

### L6 Local entailment scorer (closed 28 October 2026)

- [x] L6 Measured and closed. Whole points first ([replay](reviews/2026-10-28-entailment-scorer-replay.md):
  four MIT and Apache scorers, AUROC 0.56 to 0.66 on 461 points), then the atomic (record,
  fact) pairs the facts-first check lists, scored offline on run C's 470 facts ([run D4
  record](reviews/2026-10-28-confidence-labels-run-d4.md)): AUROC 0.63, precision at most 0.35 at any threshold, falling as the
  threshold rises. No scorer reaches the 0.8 bar, so none replaces or backs the prompted check;
  the service, its settings and the Hub's shadow policy are removed (owner, 28 October).

### L7 Agreement arm (research)

- [x] L7.1 Built as the `agree` profile (Hub #46); measured in run D3. The `agree` profile: two writers from different families answer independently;
  claims are split and matched; the first writer's answer is shown as written (never a
  merged text), agreed claims read as supported and disagreements as "the models differ"
  with the other reading. A candidate replacement for the model review, not an addition. Agreement is a confidence signal, not proof: two
  models can misread the same chart the same way
  ([semantic entropy](https://oatml.cs.ox.ac.uk/blog/2024/06/19/detecting_hallucinations_2024.html),
  [cross-model disagreement](https://arxiv.org/pdf/2603.25450)). Cost about one extra
  answer per turn; semantic entropy (5 to 10 samples) is out of reach on this host.
- [x] L7.2 Judged in run D3 and scored under L1 as one more check: 0.40 precision on 5 marked
  cells (the misses are wording differences on "last visit" answers judged 9 and 10), 11 of 35
  answers sent to review, no score lift at 18 s a turn
  ([record](reviews/2026-10-28-confidence-labels-run-d3.md)). Retired from the matrix (owner,
  28 October); the profile and code stay for a wording-tolerant matcher if one is tried.

### L8 Calibration and the confidence label (harness, Hub)

- [ ] L8.1 With two judged runs of per-point verdicts (about 700 labelled points each), fit
  three-band thresholds (supported, uncertain, contradicted) on the checks' combined probability
  (the logistic fit of `work/labels/calibrate.py`) on a calibration split and report precision and coverage on the held-out split
  ([conformal factuality](https://www.themoonlight.io/review/language-models-with-conformal-factuality-guarantees)).
- [ ] **LG2** A confidence label returns to the clinician's view only when its bands hold
  on the held-out split (proposed: at least 0.9 precision for "supported", at most 0.1 of
  true contradictions in "supported") and the label states what it measures.

### L9 Clinician view (frontend, checked-answers A6)

- [ ] L9.1 ChartSearchAI renders findings: one status per section, the named checks and
  the chart's value per contradiction, neutral notes for not-addressed and unverified,
  no High/Medium/Low chip while `level` is null. Replaces checked-answers A6's label list.
  Evidence: the frontend PR and the next judged run's dashboard.

## Pruning (28 October 2026, from runs A2 and C and the ensemble research)

Every signal and arm earns its place by a measured precision and recall against the judge,
or it goes. The matrix below replaces the seven-arm matrix for the next run.

| Signal or arm | Evidence | Decision |
| --- | --- | --- |
| Date check, record check (deterministic) | Precision 0.75 to 1.0; recall under 0.1 | Keep; the proven-contradiction class, never a grade |
| Same-model review (the default's reviewer) | Answer scores within noise of answer-only in three runs; 0.5 precision on its marks | Retire; a model does not catch its own errors ([Mind the Gap](https://arxiv.org/pdf/2412.02674)) |
| Free-form cross-family review (arm 3's reviewer) | 0.5 precision, the main source of marks in run C | Replace: one run measures the verification-question form (L3.5) against claim agreement with a second writer (L7); the one that clears LG1 with the better recall stays, the other goes |
| Prompted citation check, separate | 0.38 (A2) to 0.6 (C, 5 marks); scores unchanged without it; almost no marks since the three-way labels | Kept as the verify arm's fallback and the answer-only arm's check; the scorer that might have replaced it failed (L6) |
| Local entailment scorer (shadow) | AUROC 0.63, precision at most 0.35 on run C's listed facts (D4 record) | Removed; L6 closed |
| Citation check folded into the review | Caught 0 of 4 judged citation faults (C); the 9B verifier returned no verdicts in 11 of 35 turns and 7 false contradictions (D3) | The fold stays on the verify arm with the 12B separate check as its fallback; the 9B never judges citations alone |
| No citation check (noground) | Scores equal to the default | Becomes the bare control (deterministic checks only), not a separate research arm |
| DRY on the writer | No score change, no garbled dates, 15 s a turn faster with it off | Off is the default; the DRY-off arm is retired |
| Two writers merged into one answer | Mixing models lowers quality and synthesis loses to selection ([Self-MoA](https://mlanthology.org/tmlr/2026/li2026tmlr-rethinking/), [selection bottleneck](https://www.alphaxiv.org/abs/2603.20324)) | Never built |
| Claim agreement between two independent writers | 0.40 precision on 5 marks in D3, 11 of 35 answers to review, no score lift ([record](reviews/2026-10-28-confidence-labels-run-d3.md)) | Retired from the matrix (owner, 28 October); the profile stays off the run list |
| Window scope warn, single-point trend on a refusal | Marked correct answers in every arm of D3 (judges 9 and 10) | Window scope is an info note; the single-point check passes an answer that states no trend and checks only the series the answer names (Hub d3-checks) |
| Confidence grade (High, Medium, Low) | Never measured; small models' self-confidence is near chance | Withdrawn; returns only as the calibrated score of L8 |
| Team profiles | Unmeasured, two extra calls | Stay deferred (checked-answers A8) |

Runs D3 (b7bccdd2) and D4 (2a053c09) measured bare, verify, agree and the built-in reference
([D3](reviews/2026-10-28-confidence-labels-run-d3.md), [D4](reviews/2026-10-28-confidence-labels-run-d4.md)). In five judged runs no check has moved a
judged score, and the judged faults (wrong or missing facts, omitted records, incomplete series)
are of kinds the checks do not look for. Proposed from D4: bare becomes the default's check set
(checked-answers A7); the verification review runs hidden in every round until it has the LG1
sample; work moves to the answers' faults and to run B. The labelled points of A2, C, D3 and D4
feed L8 (1123 points, held-out AUROC 0.695, no band at 0.8).

## Order of work

1. Done 27 and 28 October: L1.1 (harness #202), L2.1 to L2.5, L3.1 to L3.4, L4, L5.1 (Hub #45),
   the frontend findings view; runs A2 (8dacd7b1) and C (e01674f6) judged and scored.
2. L1.2: the A2 against C review, with edited answers scored against their original draft; the
   owner sets LG1 and LG2.
3. Done 28 October (Hub #46): L5.2 (DRY off by default, router too), L3.5 (verification-question
   reviewer), L7 (second writer and claim agreement), the bare, verify and agree profiles; the
   retired arms removed. L6 runs offline in the decision-layer replay first.
4. Done 28 October: run D (stopped at 86 turns for the verify arm's cost), D2 (stopped at 114
   turns when the 9B returned no citation verdicts; Hub 35ef26b falls back to the separate
   check) and D3 (b7bccdd2, judged by one gpt-6-astra pass and one Opus pass, blind) on Hub #47;
   the pruning table's open rows closed, L8 refit on A2, C and D3 (held-out AUROC 0.725, no
   0.8-precision band), the agree arm retired, the misfiring deterministic checks and the verify
   profile fixed (Hub d3-checks).
5. Done 28 October: run D4 (2a053c09) on the fixed checks; L6 scored offline and closed, the
   scorer removed; one more value-binding misfire fixed (Hub d3-checks 34000a9); L8 refit on
   four runs ([record](reviews/2026-10-28-confidence-labels-run-d4.md)).
6. Owner: LG1 and the default (checked-answers A7) from the D4 record's proposals; L9 and A6
   follow LG1 (the frontend findings view is built on the ESM fork's `findings-view`).
7. Run B (the 31B writer) on the settled checks, with bare and the verification review.

## Interface with the decision-layer experiment

[decision-layer-experiment.md](decision-layer-experiment.md) (Jev, Laya, the local
cross-encoder) is a separate thread and is not changed here. Shared surfaces, so neither
thread blocks the other:

- Inputs: that thread's Phase 0b replays the same captured traces and uses the same labelled
  pairs (judge per-point verdicts, adjudications, the Hub goldens) that L1 scores against.
  L1.1's output format (per-check precision and recall against the judge) is the metric set
  P0.6 reports for its arms, so one script serves both.
- Three-band labels: L2's supported / contradicted / not addressed is the label scheme P0.6
  fits its thresholds to; L8's calibration is the same fit. Our local scorer failed the bar
  (L6 closed, 28 October); if their G1 passes, the qualifying model joins a profile through
  LG1 like any other check.
- Rules in common: shadow first and a separately attributed actor (their P2.2, our LG1), the judge never sees a check (their rule that a decision verdict is never the
  promoted judge, our principle 8).
- Scope split: this thread owns what a label means and when it may show; that thread owns
  its models and gates G0 to G3. Phase 3 items graduate through LG1 like any other check.

## Not in scope

- Regenerating or rewriting answers from a checker's verdict (checked-answers.md decision).
- Replacing the deterministic date, record and drug-safety checks.
- Any confidence number shown before LG2.
- The decision-layer experiment's models, routes and gates.
