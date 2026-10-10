# Revamp audit and decision-model experiment proposal

Observed 10 October 2026 from a fresh clone of umbrella `a53061f` with the Hub and
harness submodules initialized. This is dated review evidence and a proposal, not a
specification or an acceptance decision. The [roadmap](../roadmap.md) owns execution;
product repositories own application behavior; the harness owns experiments.

Three questions are answered here:

1. How well is the umbrella revamp (`PR-DECOMPOSITION-2026-09`) going?
2. What is Jev, TypeSafe AI's decision model, and how does it relate to our work?
3. Which targeted experiment would tell us whether a decision model belongs in Med
   Agent Hub's decision points and in the harness's answer evaluation?

## 1. Audit method and limits

Inspected: `AGENTS.md`, README, roadmap, architecture, both dated reviews, the
provider-interface reference, the guardrails research note, `environments/README.md`,
the Makefile and the three workflows, `reports-index.json`, all nine umbrella PRs,
hosted check results on `main` and on PR #9, the Hub at pin `05a40fb` (README,
`levels.yaml`, `engine.py`, `team.py`, prompts, tests) and the harness at pin
`5f18065` (README, Feature 006, judge scripts, `adjudicate.py`, datasets).

Run here: `python3 -m unittest discover -s tests -v` (24 tests pass);
`python3 scripts/check_workspace.py` (fails only because four OpenMRS and Catalyst
submodules were left uninitialized in this clone, which is the checker working as
designed); the Hub suite `pytest tests` with pip-installed dependencies (716 pass in
24 s on Python 3.13). The harness suite was not rerun (its 1,136-test result is
recorded in the roadmap closeout).

Not verified: the live `openclinai.org` landing site and report catalog, any model
run, deployed environments, the OpenMRS upstream PRs (outside this session's
repository scope), and TypeSafe's primary documentation (the sandbox network policy
denied `docs.typesafe.ai`, `openrouter.ai` and similar hosts). Jev facts below come
from web-search summaries of secondary sources and arXiv preprints and are marked
as vendor-reported where that is all there is.

## 2. Verdict: the revamp is structurally complete and operationally honest; delivery is now gated by three external items

The repository was bootstrapped on 30 September. Ten days later it has 94 commits,
nine PRs (eight merged, #9 open with green checks), zero issues and one author.
Hosted CI (`Workspace`, `operations`, Pages) is green on the latest `main`.

| Track | Roadmap claim | What the evidence supports | Assessment |
| --- | --- | --- | --- |
| B: U0–U5 workspace and validation architecture | All phases merged and verified | Six direct gitlinks, no nested product pins, umbrella-owned Makefile/compose/website, harness independence enforced by `tests/test_operation_ownership.py`; closeout counts recorded 2 October | Done. The structural goal of the revamp is met. |
| B: documentation and interfaces (U4) | Consumers resolve to current owners | Architecture, provider reference, component contracts and Hub README are consistent with each other; D01–D10 from the 2 October audit are addressed or explicitly deferred; documentation Pages publish on every merge | Done, with drift already reappearing in the roadmap (finding A2). |
| A: OpenMRS contribution delivery | Stacks rebased, findings remediated, awaiting review | Thirteen PRs restacked; QueryStore #68 reconciled but the maintainer's split request is unanswered; #587–#590 cannot build against the published QueryStore API until #68 lands; #587's context evaluation is a mixed result | At risk. Progress is real, but completion depends on OpenMRS maintainers and on a product decision about #587. |
| Local HIV research environment | Setup verified 3 October; Ross's fresh install pending | PR #9 consolidates launchers and recovers proxy startup, but the fresh-import Appointments startup failure is unresolved and fresh-install completion is unverified | Blocked on a root cause the PR itself describes as evidence, not proof. |
| Catalyst delivery | Four journeys; acceptance and publication remain | FP-001–FP-010 have owners; no Catalyst commit since the 2 October pin | Waiting on owner acceptance; no new evidence this week. |
| Website and publication | Docs published; landing deployment separate | `pmanko.github.io/openclinai.org` deploys from `main`; the separate `openclinai.org` landing deployment still awaits owner review, so the public findings D05–D07 may still be live | Partially done; the public site is the most visible unfinished item. |
| Evidence culture | Reports describe runs, not acceptance | Nineteen catalog entries with explicit limits; the 7 October context evaluation is a model of controlled comparison (frozen gold, hashed artifacts, isolated instance, targeted repeat) | Strong. This is the project's main asset. |

In short: the hard part of the revamp, moving ownership into the right repositories
without breaking the products, is finished and tested. The remaining work is
delivery through other people (OpenMRS maintainers, Ross, Catalyst owners) plus a
few hygiene items below.

## 3. Findings

Priority 1 means a correctness or ownership problem; priority 2 means drift or
friction that will cost time later.

| ID | Priority | Evidence | Impact and suggested disposition |
| --- | --- | --- | --- |
| A1 | 1 | `.gitmodules` records `branch = main` for the Hub, but the pinned Hub commit `05a40fb` (4 October, "Use checked Gemma 4 12B as the clinical default") is reachable only from Hub PR [#33](https://github.com/pmanko/med-agent-hub/pull/33) (`codex/default-gemma-12b`); Hub `main` is still `96d0489`. The roadmap closeout table records `96d0489`. | The umbrella default profile depends on an unmerged component PR. Either merge Hub #33 and keep the pin, or record the PR dependency in the roadmap status table. `AGENTS.md` asks for component changes to be published in their own repository before pinning; "published as an open PR" should be stated as such. |
| A2 | 2 | Roadmap §5 "Current execution" holds a dated sitrep (7 October test counts, hashes, thread tallies); §2 says "PRs #2 and #3 are merged" although #4–#8 have merged; the roadmap is 330 lines. | The maintained roadmap is becoming the status diary that `AGENTS.md` and the 2 October audit warned against. Move the dated remediation record to `specs/reviews/2026-10-07-track-a-remediation.md`, keep one current-state row per track in §2, and link the evidence. |
| A3 | 1 | PR #9 is green but states that fresh-install completion is unverified and that the Appointments `DatabaseUpdater` ordering failure reproduces on current upstream and release 2.8.10. | Ross's fresh installation remains the roadmap's priority 5 and is not unblocked. Decide whether to pin the official distribution's Core instead of the 2.9.0-SNAPSHOT overlay for the research baseline, or open an upstream issue with the captured log; record the decision in §7. |
| A4 | 2 | GitGuardian flagged `scripts/seed-local.sh` line 112 on PR #9. The line is a curl health probe with the public demo login `admin:Admin123`, which `environments/README.md` documents for the synthetic local environment. | Not a leaked secret. Read the login from the existing defaults file instead of inlining it, so the scanner stays quiet and the password has one owner. |
| A5 | 2 | The 2 October audit's W04 report-catalog provenance mismatch ("Lever sweep (dev)" narrative versus displayed rows) is no longer tracked in roadmap §7, and the `reports-index.json` entry is unchanged. | Either confirm it was investigated and record the disposition, or restore it to outstanding decisions. Untracked public-evidence issues erode the evidence culture that is otherwise the project's strength. |
| A6 | 2 | The 7 October context evaluation reports mean citation F1 falling from 0.891 to 0.735 while off-topic citations fall from 14 to 0, with a confirmed renal retrieval loss and a metric-versus-prompt disagreement on negative-category citations. | This is a product decision, not an evaluation gap. #587 needs an explicit disposition on (a) whether the raw-question ranked read is accepted with the retrieval loss, (b) whether QueryStore owns a qualifier-preserving fix, and (c) whether the gold or the prompt rule changes. Section 6 proposes an experiment that bears directly on (a). |
| A7 | 2 | Single author; every merged branch is agent-generated (`codex/*`); zero issues; decisions live only in roadmap prose. | Fine for velocity, fragile for continuity. Keep the dated reviews, and consider opening GitHub issues for the three external dependencies so collaborators can see state without reading the roadmap. |
| A8 | 2 | The harness still carries SpecKit scaffolding (`.specify/`, ten `speckit-*` skills), `.cursor/` rules, 25 planning documents and a May development artifact directory. | Not a blocker; the independence contract is tested. Schedule a separate cleanup once Track A settles, following the harness's own `AGENTS.md`. |

Positive observations worth keeping: the operational test suite asserts ownership
boundaries rather than prose; the provider-interface reference was checked against
registry, transport and frontend code; the Hub trace package already records every
decision the experiment below needs (`steps`, `stage_timing`, `final_references[]`
with `sourceText` and `groundingChecks`); and the harness already supports a second
judge actor (`judge-finalize.py --actor`), weighted kappa against human adjudication
and prediction-powered inference. The experiment proposal reuses all of this.

## 4. Jev primer

### What it is

Jev is the first "System One" model from TypeSafe AI, in early access since 15
September 2026. It does not generate prose. A request supplies a `state` (text to
judge) and a map of named typed `questions`; the response answers every question in
parallel with probabilities. Three primitives are documented:

| Primitive | Input | Output |
| --- | --- | --- |
| Choice | Named options with descriptions | Chosen label, a probability per option, confidence |
| Score | An ordered rubric of up to ten levels | Probability-weighted numeric score, per-level distribution, confidence |
| Noul (yes/no) | Instruction plus optional criteria defining true and false | A probability from 0 to 1 |

Reported operating envelope (vendor-reported unless noted): text-only input; a 32K
token context (one source says 64K); 70–500 ms end-to-end latency; $0.042 per
million input tokens with output free; model routes `jev-latest` and `jev-1.13`;
access through TypeSafe's API (sign-up status has changed more than once since
launch), OpenRouter (`typesafe/jev-1.13`, beta), Vercel AI Gateway
(`typesafe-ai/jev`) and Cloudflare Workers AI; official Python and TypeScript SDKs;
LiteLLM pass-through, Spring AI and Langfuse integrations. Training is described as
"Reinforcement Learning for Calibrated Decisions" with no published details.
TypeSafe's own four-workflow benchmark puts Jev at 67.8%, level with one frontier
model and behind two others; it reports an expected calibration error of 0.246 on
its own set. The claim of "0% structured-output errors" is a schema guarantee, not
a correctness guarantee.

### Independent evidence

- Rao and Callison-Burch, [JEV vs. LLMs as Rubric Judges](https://arxiv.org/abs/2609.29769):
  Jev is 16–325 times cheaper and 28–350 times faster than three flash-tier LLM
  judges; its accuracy differs significantly in at most 8 of 27 paired comparisons,
  ahead mostly on binary checklist criteria and behind on ordinal ones. On Jev's
  most confident errors about 96% of LLM verdicts repeat the same wrong answer, so
  judge cascades gain at most 2.7 points even with oracle thresholds. The title says
  it: cheaper, faster, and wrong in the same places.
- [JEV-as-a-Judge: Accept When Confident, Escalate When Unsure](https://arxiv.org/abs/2609.26550):
  within three points of a frontier judge wherever the verdict can be read off the
  text, at 0.36% of the fee and 0.15 s median latency; behind where the verdict must
  be derived (math, code, logic).
- [Calibrated Decisions at Scale](https://arxiv.org/pdf/2609.24052) (police crash
  narratives, 27-question schema, 2,416 blinded human judgments): F1 0.908 against
  humans; recalibration on the same labels cut calibration error 3.3 times;
  "calibration varies by model rather than by paradigm, so each model must be
  audited".
- [JEV and Laya as System One decision layers](https://arxiv.org/html/2609.28940v1):
  Jev ECE 0.246 versus Laya 0.081 after temperature scaling, measured on different
  sets; Jev far ahead on a 77-way choice task (0.870 versus 0.425).
- Healthcare coverage is limited to one practitioner blog proposing narrow uses
  (does this passage support this claim; does this letter contain an explicit
  request) and stating that none has clinical validation.

### Deployment and data constraints

Jev is cloud-only and US-hosted; no weights or self-hosted package exist. Zero data
retention is an enterprise arrangement (the Cloudflare route lists it as available);
no HIPAA business associate agreement is published; SOC 2 Type II is claimed by
third parties only. For OpenClinAI, whose [design is local-first](../background/why-local-first-clinical-ai.md),
Jev can be an experiment and evaluation instrument on synthetic data. It cannot be a
production dependency of the Hub without a governance decision this proposal does
not make.

Laya (Convai Innovations) is the self-hostable counterpart: a 421M-parameter model
with the same three primitives, Apache 2.0 weights, PyTorch and ONNX runtimes, about
33 ms per question on a T4 (vendor-reported), trained against the Brier score, and
weaker than Jev on high-cardinality choice. Its documentation recommends calibrating
on the deployment domain. Any decision layer that could ship in the Hub would be
Laya-shaped; Jev is the ceiling reference.

## 5. How a decision model relates to our architecture

Our [guardrails research note](../artifacts/planning/guardrails-methodology-research.md)
already states the two cautions Jev's marketing invites: "well-formed is not
correct" and "verification needs independent evidence". A decision model guarantees
shape and returns a probability; whether that probability is calibrated on our
charts and whether its errors are independent of our writer's errors are empirical
questions. The arXiv results predict correlated errors; our experiment measures that
in our domain rather than assuming either way.

The Hub's hosted clinical workflow is a staged pipeline:
`context, answer, gate, resolve_refs, review, gate, final_resolve_refs,
ground_verdicts, indepth, indepth_gate`. The decisions inside it that are currently
made by a generative model constrained to a JSON schema are the natural Jev or Laya
candidates. Decisions made deterministically are not.

| Hub decision point (pinned `05a40fb`) | Today | Decision-model shape | Fit |
| --- | --- | --- | --- |
| `ground_verdicts` → `_entailment_verdicts` in `server/team.py`: for each citation cluster, "does SOURCE support STATEMENT", batched YES/NO via the `grounding` role (Gemma 4 12B) with a JSON schema; fails open to `unchecked`; `unsupported` drives `needs_review` | One extra full generation pass on the single-slot router per turn; same model family as the writer | Noul per (source, statement) pair; all pairs of a turn in parallel | Best first target: closed criterion, high volume, labels cheap to adjudicate, already traced with `sourceText` and `groundingChecks` |
| `indepth_gate` → `_validate_indepth_verdict`: per-claim drop decisions over numbered In-Depth claims | One JSON call returning claim numbers to drop | Noul per claim ("is this claim fully supported by its cited sources?") | Good: In-Depth is already labeled review-only, so a wrong drop is low-harm |
| `review` → `_validate_answer_rewrite`: `answer_ok`, localized `errors`, `corrected_answer`, then recheck and re-gate | Generative; the correction is prose | Only the decision half (Noul: "does any clinical value or date in the DRAFT contradict the CHART?") | Partial: a decision model cannot write `corrected_answer` or the chart-fact rationale; it could only decide whether to spend the rewrite call |
| `gather` (team profiles): orchestrator tool-call loop deciding whether to consult `medical_expert` | Gemma E4B tool calling | Choice: `lookup_only` versus `needs_interpretation` | Low priority: team profiles are not the product default, and published runs found the orchestrator hurts both writers |
| Context admission for non-QueryStore sources: the deterministic selector admits exact matches, a clinical core and normalized-overlap records | Deterministic | Noul per record ("is this record relevant to the question topic?") as a recall safety net over the complete ledger | Directly relevant to the #587 renal retrieval loss; QueryStore owns ranking, so this is an experiment, not a product path |
| Provider, mode and profile selection; deterministic temporal, date and drug-safety gates | Explicit configuration and deterministic code | None | Out of scope by contract: providers are never silently substituted and Checked answers require deterministic results |

For answer evaluation, the harness's Scout rubric maps onto the primitives almost
one-to-one, which is why it is the second experiment arm:

| Rubric axis (FR-006.5) | Jev primitive | Note |
| --- | --- | --- |
| `accuracy`, `completeness`, `relevance` (0–10) and `background_support`, `background_added_value` | Score over the rubric's five anchored bands (0, 1–3, 4–6, 7–8, 9–10), mapped to band midpoints | Jev Score supports at most ten levels; the arXiv results predict this is where it is weakest |
| `abstention_outcome` (4 values), `citation_groundedness` (4), `temporal_date_accuracy` (3), `temporal_window` (2), `temporal_trend` (2) | Choice | Closed criteria; predicted strength |
| `harm`, `background_no_new_harm` | Noul | Safety-relevant recall is the metric that matters |
| `note` (1–3 sentence rationale citing chart records) | Not producible | A Jev actor row carries no rationale, so it can never be the promoted judge; it stays a separately attributed actor under FR-006.4 |

## 6. Proposed experiment: `DECISION-LAYER-2026-10`

One experiment, four phases, each with a stop rule. Phases 0 and 1 change no
product code and can start now. Phases 2 and 3 are conditional and need owner
review. Data is the synthetic OpenMRS HIV demo dataset only; run manifests record
the remote provider, model version and the fact that retention terms are those of
the chosen route. Jev requests cost well under one dollar per thousand decisions at
the reported price; Laya runs on the existing router host.

### Phase 0: offline replay against captured evidence (no live services)

Inputs already on disk:

- Harness run packets for `hub-profile-candidate` (12 scenarios, `single-12b-checked`)
  and `small-model-answer-paths` (the same 12 scenarios across six backends). Each
  cell's trace carries `final_references[]` with `sourceText`, usage fragments and
  the Hub's `groundingChecks` verdicts, the `answer_review` steps with `answer_ok`
  and `errors`, `in_depth_claims` with the In-Depth gate, and `stage_timing` steps.
- The 7 October context evaluation: 55 captured questions in each of two arms and a
  frozen `gold.json` classifying every chart record as on-topic or not for each of
  eight topics across five patients.

Procedure (a harness experiment script under `scripts/`, writing a dated run
directory with the usual manifest and provenance; nothing under `server/` changes):

1. Extract every (source text, statement) grounding pair and every In-Depth claim with
   its cited sources from the packets. Ask Jev and Laya the Noul question the Hub
   asks Gemma, with the same strict criteria as `_ENTAILMENT_SYSTEM_PROMPT`.
2. Have the owner tier adjudicate about 120 pairs sampled across cells, blind to all
   model verdicts, using `supported`, `unsupported`, `unclear`. Record the reviewer
   and time as `adjudicate.adjudication_record` does.
3. For the context evaluation, ask the per-record relevance Noul for every record of
   the five patients against each topic, and score against `gold.json`. No human
   labels are needed; the gold is frozen. Report whether the three renal records
   that #587 dropped for patient 39 would have been admitted.

Metrics, computed with the existing `adjudicate.weighted_kappa` (binary labels use
`max_score=1`): kappa versus human for Gemma, Jev and Laya; recall of `unsupported`
(the safety-relevant class); Brier score and expected calibration error of the
decision-model probabilities with at least ten observations per bin; conditional
agreement of Jev with Gemma on the cells where Gemma is wrong versus right (the
error-correlation test from the arXiv paper); Gemma's fail-open `unchecked` rate
versus decision-model coverage; wall-clock latency per batch versus the
`ground_verdicts` stage timing; cost per turn.

Gate G1, stated before collection: proceed only if Jev or Laya reaches a kappa
within 0.05 of Gemma's on grounding pairs with recall of `unsupported` at least
equal to Gemma's, and the decision-model errors are not simply a subset of Gemma's.
Calibration is reported, not gated, in this phase. Failure ends the experiment with
a dated review and no product change.

### Phase 1: a second judge actor for answer evaluation

Use the already judged runs (the 12-cell checked 12B candidate scored 88.4/100 by
the Scout judge, and the 297-cell method-scaffolding run). Build Jev actor rows from
`judge-cells.jsonl` using the rubric mapping in section 5, checking first that each
chart snapshot fits the 32K context (product charts are budgeted at 24,576 tokens).
Finalize with `scripts/judge-finalize.py <run> rows.json --actor jev-1.13
--actor-type llm-judge --model typesafe/jev-1.13 --method clinical-answer-scoring`
and never `--promote`. Compare with `adjudicate.agreement` and `ppi_benchmark`
against the Claude judge and existing human adjudications.

Hypotheses: Jev matches the Claude judge on categorical axes and harm, trails on the
ordinal axes, and its errors correlate with the Claude judge's. Gate G2: categorical
agreement with humans at least equal to the Claude judge's and no missed known-harm
cell. If G2 passes, the useful product of this phase is not a cheaper headline score
but a screening actor: run Jev on every cell and feed `adjudicate.sample_cells`
priority mode, so human adjudication time goes to the cells where the two actors
disagree or Jev is confident and wrong-looking. The canonical judge, with its
rationale, stays unchanged.

### Phase 2: shadow mode inside the Hub (conditional on G1)

Add a `grounding_backend` knob to one `visibility: evaluation` profile, for example
`eval-12b-checked-shadow`, so the `ground_verdicts` stage runs the existing Gemma
check and the decision model side by side, recording both verdicts and probabilities
in `groundingChecks[].method` and the trace while the shipped verdict stays Gemma's.
Product profiles and `GET /v1/models` are untouched. Run `small-model-answer-paths`
through the harness and compare disagreement rate, `unchecked` rate and stage
latency from `stage_timing`. The Hub owns the knob and its change record (the
harness's `pccp-change-record-template.md` is the right form); the harness owns the
comparison; the umbrella publishes after review.

### Phase 3: decision-making at the Hub level (conditional on Phase 2; design review first)

Three candidate decisions, in order of risk:

1. In-Depth claim drops by per-claim Noul instead of the one-shot JSON verdict,
   measured as claims dropped versus adjudicated labels. Low risk because In-Depth
   is already a review-only artifact.
2. A review gate: a Noul contradiction pre-check decides whether the rewrite
   validator runs. Deterministic gates stay unconditional. A turn that skipped the
   model review cannot be labeled Checked under the current
   [provider contract](../../docs/openmrs-provider-interface.md), so this needs a new
   honest label and a contract change through the umbrella before any product use.
   The Phase 0 stage timings tell us whether the review stage's latency share even
   justifies the design.
3. Team orchestrator routing by Choice, only if team profiles return to the product
   path.

Non-goals throughout: silent provider, mode or profile switching; replacing any
deterministic temporal or drug-safety gate; sending non-synthetic patient data to a
remote decision model; and promoting a decision model to a default product profile
before a domain calibration audit and a change record exist.

### Effort and ownership

Phase 0 and 1 are three to five working days including two to three hours of blind
adjudication. The harness owns the protocol and evidence (a short Feature 006
companion or a dated planning brief); the Hub owns the Phase 2 knob; the umbrella
roadmap carries one line in §7 and links this review. Publication of any result
goes through the umbrella's report catalog with the usual limits stated.

### Risks

Early-access instability (sign-ups paused and reopened; pin `jev-1.13` and record
the version); the 32K context against chart snapshots; calibration that does not
transfer across domains without an audit; weakness on ordinal axes; correlated
errors, which mean a decision model cannot be the independent safety layer our
guardrails note asks for and should be framed as cheap screening; no rationale
output; US hosting without a business associate agreement, irrelevant for synthetic
data and disqualifying for production until governance says otherwise.

## 7. Decisions requested from the owner

1. Approve Phases 0 and 1 as a harness experiment on synthetic data, with Laya
   included as the self-hostable arm.
2. Choose the Jev access route (OpenRouter avoids the direct sign-up queue) and the
   adjudicator tier for the 120 grounding pairs.
3. Merge Hub #33 or record the unmerged-PR pin in the roadmap status table (A1).
4. Move the 7 October sitrep out of the roadmap into a dated review (A2) and restore
   W04 to outstanding decisions or record its disposition (A5).
5. Decide the research-baseline Core overlay question behind the Appointments
   startup failure (A3) so Ross's installation has a path.

## Sources

Jev and Laya facts are drawn from these pages, reached through web search only:

- [TypeSafe AI introduction](https://docs.typesafe.ai/introduction), [API reference](https://docs.typesafe.ai/api) and [Choice primitive](https://docs.typesafe.ai/primitives/choice)
- [OpenRouter Jev guide](https://openrouter.ai/docs/guides/community/jev) and [Jev vs LLM-as-a-Judge](https://openrouter.ai/blog/tutorials/jev-vs-llm-as-a-judge/)
- [Cloudflare Workers AI model page](https://developers.cloudflare.com/ai/models/typesafe/jev/)
- [Langfuse: using Jev for evals](https://langfuse.com/blog/2026-09-18-using-typesafes-jev-for-evals) and [Spring AI integration](https://spring.io/blog/2026/09/21/spring-ai-typesafe-structured-judgment/)
- [eesel review](https://www.eesel.ai/blog/typesafe-jev-review), [eesel pricing](https://www.eesel.ai/blog/typesafe-jev-pricing), [DataCamp explainer](https://www.datacamp.com/blog/system-one-models-jev), [TrueFoundry analysis](https://www.truefoundry.com/blog/typesafe-ai-jev), [Hyperstack latency reproduction](https://www.hyperstack.cloud/technical-resources/tutorials/jev-inside-typesafe-ais-first-system-one-decision-model)
- [Self-hosting and deployment boundaries](https://befailproof.ai/jev/self-hosting/), [data retention](https://jevaiguide.com/faq/does-jev-train-on-your-data/), [enterprise security guide](https://neuraltrust.ai/blog/jev-typesafe-ai-security)
- [Jev in healthcare (iatrox)](https://www.iatrox.com/blog/jev-ai-healthcare-clinical-use-cases)
- [JEV vs. LLMs as Rubric Judges](https://arxiv.org/abs/2609.29769), [JEV-as-a-Judge](https://arxiv.org/abs/2609.26550), [Calibrated Decisions at Scale](https://arxiv.org/pdf/2609.24052), [JEV and Laya decision layers](https://arxiv.org/html/2609.28940v1), [Evaluating and Benchmarking Jev](https://arxiv.org/html/2609.37647v1)
- [Laya explained](https://www.layer3labs.io/guides/laya-explained), [Jev vs Laya](https://shop.zimaspace.com/blogs/product-comparisons/jev-vs-laya-decision-model), [Laya overview](https://www.eesel.ai/blog/laya-ai)
