# Checked answers: stages, checks and labels

Owner: umbrella (this spec, the arm matrix, the runs and their records). Implementers: the Hub
(`targets/med-agent-hub`: engine, profiles, prompts, the answer envelope), the harness (arms,
the judge fields the comparison reads), the ChartSearchAI frontend (what the clinician sees).
Judging of the runs follows [judging.md](judging.md). Speed of a checked answer stays with
[provider-parity.md](provider-parity.md).

## Goal

A checked answer is a draft written by one model, checked by deterministic rules and by a
second model, and shown to the clinician with labels that say exactly which check questioned
what. Every choice in that pipeline (which steps run, which model takes each, what each is
asked, what happens with its verdict) is a line in a profile, so a variant is a profile and a
harness arm, never a branch in the engine. The default profile is the simplest one the
evidence supports, and every added step has a judged run showing what it buys.

## Decisions (owner, 27 October 2026)

- With checkers of the sizes this host runs (12B to 35B), a model's critique is shown as a
  label and never used to regenerate the answer. The only edits come from deterministic checks
  with a chart-derived patch (the date gate). An apply or redo mode is reserved as a policy
  value and built only after a judged run shows a checker is right often enough to earn it.
- The reviewer is a different model from the writer in every new profile. Same-model review
  (the current default) stays only as the control.
- Citation grounding stays as its own narrow check (statement against cited record, yes or
  no) and becomes a profile choice: separate, folded into the review, or off. The baseline
  keeps it separate.
- The reviewer's prompt stops asking for a rewrite the engine discards.
- No team profile for now. The ten-stage single profile already has six model calls; the
  team's gather stage adds two or more, unmeasured. Team profiles return when a harder task
  set exists (multi-step or longitudinal questions) and the single baseline has been judged.
- The In-Depth gate judges each claim on the claim's own words, never on the question's.
- Labels the clinician sees are consolidated after the first judged run of the baseline, not
  before, so the run says which labels are worth showing.

## The pipeline today

Stage sets and profiles live in the Hub's `server/levels.yaml`; the engine runs the stages in
order. A stage is a step; a role is the model that takes it. The checked profile
(`single-12b-checked`, the product default):

| Stage | What it does | Model call |
| --- | --- | --- |
| context | builds the chart context for the question | none |
| answer | the writer drafts the answer with `[N]` citations | 1, writer |
| gate | deterministic date, window and trend checks; patches from dated records | none |
| resolve_refs | maps citation numbers to chart records | none |
| review | the reviewer reads the draft against the chart and reports errors | 2, reviewer |
| gate | the same checks on the reviewed answer | none |
| final_resolve_refs | re-maps citations | none |
| ground_verdicts | one entailment call: does each cited record support its sentence | 3, grounder |
| indepth | the writer drafts Background claims; the reviewer validates them | 4 writer, 5 reviewer |
| indepth_gate | the deterministic checks per claim, then one entailment call for the claims' citations | 6, grounder |

Findings behind the decisions (26 and 27 October reads of the three full runs and the code):

- The reviewer is prompted for `errors` and a `corrected_answer`; since Hub PR #37 (25 October)
  the engine labels only, so the rewrite is paid for and discarded. Every `edited` status in
  the runs came from the date gate.
- The grounder never changes the answer: an unsupported citation marks the answer
  `needs_review` and the citation unsupported. The answer-only profile also runs it, so no arm
  has measured leaving it out.
- 31 of 35 In-Depths are marked for checking in every run, but the date check accounts for few
  of them. In the 26 October run the citation checks marked 66 of 89 claims: 33 because the
  grounder found the cited record did not support the claim, 33 because the claim cites nothing
  and is labelled general guidance. The date check questioned 9 claims in 6 In-Depths.
- The In-Depth gate called the answer gate per claim with the question attached, so a question
  asking how weight changed failed a claim that stated one CD4 value. Replayed claim by claim,
  3 of the 9 questioned claims came from the question.
- Under both judges the checked profile's answer scores are within a point of answer-only
  while costing about 20 s more per turn
  ([26 October record](reviews/2026-10-26-l5-full-default.md)).

## What the research says

- Small models cannot self-correct; verification by the same model is no better than its
  generation, and a larger or different verifier widens the gap
  ([Mind the Gap, ICLR 2025](https://arxiv.org/pdf/2412.02674);
  [SCORE, 2024](https://arxiv.org/pdf/2404.17140)). Hence a different reviewer, and the
  bigger-pair arm.
- Feedback quality, not rewriting, is the bottleneck; raw critique from an untrained critic
  rarely improves an answer and can degrade it
  ([CTRL, 2025](https://arxiv.org/pdf/2502.03492);
  [LLMRefine](https://arxiv.org/pdf/2311.09336);
  [TACL 2024](https://aclanthology.org/2024.tacl-1.78.pdf)). Hence label, never regenerate.
- Narrow claim-against-document grounding is where small models match large ones
  ([MiniCheck](https://arxiv.org/abs/2404.10774);
  [Paladin-mini, 2025](https://arxiv.org/html/2506.20384v1)), and critics anchored to an
  external signal are far more reliable than free judgement. Hence the grounder stays narrow
  and the deterministic gate is the one check allowed to edit.
- Evaluators favour their own generations
  ([Panickssery, NeurIPS 2024](https://arxiv.org/pdf/2404.13076);
  [follow-up, 2025](https://arxiv.org/html/2504.03846v2)). Hence cross-family review and
  cross-family judging.
- Several weak verifiers combined beat any one
  ([Weaver, 2025](https://arxiv.org/html/2506.18203v3)). A later option for how the gate, the
  grounder and the reviewer are combined.

## Target path

Each box is ticked with a link to its evidence: the merged PR with its tests for code, a
dated review under `reviews/` for a run.

- [ ] A1 In-Depth gate on the claim's words. `gate_indepth_claims` evaluates each claim with no
  question attached, so the trend test, the window test and the series selection see the
  claim only; the Answer gate keeps the question. Tests: a non-trend claim over a
  single-point series under a "trend" question raises nothing; a claim asserting a trend over
  one point still fails; the flagged claims of the 26 October run as goldens with the expected
  flag set. Evidence: the Hub PR and the date check's questioned-claim count on a 17-scenario
  answers-only run after the fix (replayed on the 26 October claims: 6, down from 9).
- [ ] A2 Review policy. Every profile carries a `review` policy block:
  `action: label` (the only accepted value; `apply` and `redo` reserved and refused) and
  `grounding: separate | folded | off`, covering the Answer and the In-Depth claims. `separate`
  is the entailment call; `folded` adds a per-citation support verdict to the reviewer's JSON
  and skips the call; `off` runs neither and marks citations unchecked rather than leaving them
  "checking". In-Depth citations are checked for what the claim attributes to each record, not
  for the interpretation joined to it, and an uncited claim is tagged general guidance without
  marking the In-Depth for checking (owner, 27 October). The label-mode prompt returns
  `answer_ok` and `errors` (each with `wrong` and `chart`) and no corrected answer.
  Tests: every product and eval profile loads with its policies validated; `off` yields
  unchecked citations; `folded` writes grounding statuses from the review reply; no profile id
  appears in engine code. Evidence: the Hub PR.
- [ ] A3 Models. Pinned downloads (revision and hash in the model manifest) for Gemma 4 31B
  Q4_K_M, Qwen3.6-35B-A3B Q4_K_M (thinking budget 0 when checking) and Qwen3.8-27B
  UD-Q4_K_XL (thinking off, card sampling); router sections (`qwen3.8-27b` new) and
  `model_registry.json` entries; the residency check for each arm's pair. Evidence: the
  umbrella PR and `make llama-router-models` output.
- [ ] A4 Profiles and arms. Hub product profiles sorted after the default, so the app and the
  harness run them alike; same stages, policies and context as the default: `single-12b-xcheck` (Gemma 4 12B writes, Qwen3.6-35B-A3B reviews and
  grounds), `single-31b-xcheck` (Gemma 4 31B writes, Qwen3.8-27B reviews and grounds),
  `single-12b-checked-folded` and `single-12b-checked-noground` (the default pair with the
  grounding policy changed). Harness arms for each in `backends.json`. Evidence: the Hub and
  harness PRs with their profile-loading tests.
- [ ] A5 Runs. After A1 and A2 are deployed. Run A, 33 GB resident: bundled, Hub answer-only,
  baseline, folded, noground, `single-12b-xcheck`. Run B, 36 GB resident: `single-31b-xcheck`
  with the baseline repeated as the in-run control. Judged blind per scenario by gpt-6-astra
  high, three passes, plus one Claude Opus 5.5 high pass on run A ([judging.md](judging.md)
  C2 to C5). Evidence: a dated review with, per arm, the judged scores and harm, the latency,
  the reviewer's flags against the judges' accuracy (flag precision and missed errors), the
  grounder's verdicts against the judges' citation groundedness, and what `off` loses.
- [ ] A6 Labels. One status per answer, one note that names the checks that questioned it
  (date check, second model review, citation support), citation marks, and the In-Depth as the
  product renders it; the same on the harness report and dashboard. Scoped from A5's evidence.
  Evidence: the Hub envelope PR, the frontend PR, the harness PR, and the next judged run.
- [ ] A7 Default. The product default profile is the arm A5 supports; `single-12b-checked`
  stays only if nothing beats it. Evidence: the Hub PR moving `default: true` and the record
  it cites.
- [ ] A8 Team profiles. Revisited when a task set exists that a single writer cannot serve;
  the entry criterion is written here before any team run. No action now.

## Run plan

| Arm | Profile | Writer (answer, In-Depth) | Reviewer, grounder | Resident |
| --- | --- | --- | --- | --- |
| bundled | ChartSearchAI built-in | Gemma 4 12B | module's own checks | 13 GB |
| answer-only | `single-12b-answer` | Gemma 4 12B | none (grounder only) | 13 GB |
| baseline | `single-12b-checked` | Gemma 4 12B | Gemma 4 12B | 13 GB |
| folded | `single-12b-checked-folded` | Gemma 4 12B | Gemma 4 12B, grounding in the review | 13 GB |
| noground | `single-12b-checked-noground` | Gemma 4 12B | Gemma 4 12B, no grounding | 13 GB |
| arm 3 | `single-12b-xcheck` | Gemma 4 12B | Qwen3.6-35B-A3B | 33 GB |
| arm 4 | `single-31b-xcheck` | Gemma 4 31B | Qwen3.8-27B | 36 GB |

Run A holds the first six (about 3.5 hours at 55 s per checked turn, 35 turns per arm); run B
holds arm 4 and the baseline. The two runs are compared like for like through the judge cards.
Arm 3 against the first three isolates what self-review and then cross-family review add to
the same draft; arm 4 against arm 3 asks whether a bigger pair does better; folded and noground
against the baseline price the grounder.

## Order of work

A1, then A2 (separate Hub PRs, each rebuilt and pinned with `make chartsearch-smoke`), A3 and
A4 together, A5, then A6 and A7 from its evidence.
