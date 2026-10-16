# Decision-layer research update: mechanism, Laya, access and the Hub map

**Date:** 16 October 2026 · **Spec:** [`DECISION-LAYER-2026-10`](../decision-layer-experiment.md) ·
**Kind:** desk review before owner decisions; no run was made.

This record updates the [10 October audit and proposal](2026-10-10-revamp-audit-and-jev-experiment.md)
with four days of further research: how decision models work and differ from the
Hub's LLM, what Laya's own model card says about zero-shot use, the access situation,
and a decision-by-decision reading of a checked Hub turn at the pinned source. It
does not replace the primer or the mapping table in that review; it corrects and
extends them. The spec was changed accordingly (section 7).

Sources: the pinned Hub source (`05a40fb`), the QueryStore ADR (`286993c`), the
committed context-evaluation gold, and web research on 14 and 16 October. The Laya
model card was read through secondary coverage because `huggingface.co` is blocked
from the cloud coding environment; its figures must be confirmed on the card before
any training run.

## 1. Findings in brief

1. **Laya is not a zero-shot arm.** Its base checkpoint is near chance on its own
   benchmark; the published numbers come from fine-tuning. It leaves the grounding
   replay and re-enters as a trained arm on the relevance pairs, where labels exist.
2. **The relevance replay can run first, from files already committed.** The gold is
   rule-made, so each disagreement is read before it counts as a model error.
3. **For context admission, Jev's honest competitor is a local cross-encoder
   reranker**, not Gemma. The Hub makes no model call in context preparation today;
   every relevance signal is lexical, a bi-encoder cosine, a type or a date.
4. **The grounding swap changes kind, not only speed.** A probability per pair allows
   a threshold policy that maps onto the harness's supported, unsupported and unclear
   labels; the fail-open path largely disappears.
5. **The review stage decomposes into a fast check and a slow repair.** The decision
   half (`answer_ok`, per-sentence support) is decision-shaped; the correction and the
   clinician-facing note stay generative. Whether it is worth building depends on the
   review stage's latency share, which the run packets hold.
6. **Every Jev route is blocked from the cloud coding environment.** Phase 0 runs on
   the owner's workstation or after `openrouter.ai` is allowed there. OpenRouter's
   `typesafe/jev-router` is a different product and never a route.

## 2. Mechanism: how a decision model differs from the Hub's LLM

Jev, Laya and Gemma are transformers trained on text. The difference is the output
head and the training objective.

Gemma is a decoder trained on next-token prediction. When the Hub asks it a yes/no
question under a JSON schema, the answer is a side effect of generation: the model
predicts which token is likely next in a document shaped like the prompt. Constrained
decoding only masks illegal tokens at each step, which guarantees shape, not
correctness. The probability one could read off the YES token is a language-model
quantity that moves with phrasing and formatting; no training step rewarded it for
being calibrated on the question. Each output token is one more sequential pass, which
is why output tokens cost money and latency is seconds.

Laya's model card documents the open version of the alternative: a ModernBERT-large
encoder with a decision head trained from scratch. The text to judge, the question and
its options go in together; each option gets its own mask token; the model reads the
whole input bidirectionally in one forward pass, scores each mask position and applies
a softmax across that question's options. Score questions are the same mechanism over
ordered levels; a yes/no question is a two-option choice. TypeSafe describes Jev as a
"parallel sampler that generates all outputs in a single query rather than
autoregressively" (vendor description; architecture undisclosed). The inference is that
Jev is the same shape at larger scale, with the question text conditioning the head so
one model answers any question. In older terms this is a BERT-style classifier whose
task is an input rather than a fixed head.

The closest analogy in our stack is QueryStore. Its embedding model is a bi-encoder:
query and record are vectorised separately and compared by cosine. A cross-encoder
reads query and record together and outputs one relevance score, more accurate than
cosine and far cheaper than generation. A per-record relevance yes/no is a
cross-encoder judgment with a natural-language criterion.

Calibration is the central claim. A classifier emits a probability; calibrated means
that of everything scored 0.8, about 80% is true. Laya is trained against the Brier
score, the squared error between the predicted probability and the 0/1 outcome, a
proper scoring rule under which reporting one's actual belief is optimal. TypeSafe
describes "Reinforcement Learning for Calibrated Decisions" with no published details.
Two cautions from the evidence: Jev's self-reported expected calibration error is
0.246, which is poor; Laya reaches 0.081 only after temperature scaling, a single
scalar refitted per question type on labelled data, from 0.466 before. The crash
narrative paper found the same, with recalibration cutting error 3.3 times. Expect to
calibrate on our charts before trusting any probability.

What the shape gives up: no chain of thought and no rationale, so a verdict can be read
off the text but not derived; the arXiv results show Jev trailing on ordinal scales and
wherever the answer must be computed. And its errors are not independent of LLM
judges: on Jev's most confident errors about 96% of LLM verdicts repeat the same wrong
answer.

| | LLM (Gemma 4 12B) | Jev / Laya |
| --- | --- | --- |
| Network | Decoder transformer | Encoder transformer with a decision head |
| Output | Token sequence, one pass per token | One probability distribution per question, one pass |
| Training signal | Next-token cross-entropy, then preference tuning | Proper scoring rule on decision outcomes |
| "Probability of yes" | Language-model artefact | The trained output |
| Rationale | Yes | None |
| Cost driver | Output tokens | Input tokens only |
| Strong at | Writing, deriving, explaining | Closed criteria readable from the text |
| Weak at | Calibrated closed decisions | Ordinal scales, multi-step inference |

## 3. Laya: a base to specialise

The 10 October proposal ran Laya untrained beside Jev. Laya's model card says: "Laya
is a fast base to specialise, not a zero-shot decision engine." The figures reported
in secondary coverage of the card:

- Base English checkpoint, zero-shot, on the typed-decisions benchmark: 0.362, against
  a random baseline of 0.318 and a majority-class baseline of 0.461.
- The 0.766 headline belongs to a checkpoint fine-tuned on that benchmark's own
  1,200-case training split (per primitive: noul 0.857, choice 0.733, score 0.723).
- Calibration out of the box is poor; refitting one temperature per question type
  moves mean expected calibration error from 0.466 to 0.081.
- Convai publishes a notebook that runs dataset building, training, calibration and
  evaluation on two T4 GPUs.
- Sources disagree on the context window: 512, 1,024 (typed-decisions checkpoint) or
  8,192 tokens. A record plus a topic question fits any of them; a chart does not.

Consequence: a zero-shot Laya arm would measure nothing. The grounding replay has about
120 adjudicated pairs, too few to train on. The relevance replay has 7,840 labelled
pairs across five patients, enough to fine-tune leave-one-patient-out: train on four
patients, test on the fifth, rotating. Laya therefore moves to the relevance arm as a
trained model, and the D3 recommendation changes accordingly.

## 4. Jev status and access

- No October news beyond launch coverage; Jev remains in early access. The version to
  pin is `jev-1.13`.
- OpenRouter now lists `typesafe/jev-router`, a model router that picks an LLM and
  reasoning effort per request. It runs on Jev but is not the decision model; it is
  never a route for this experiment.
- Retention: Vercel's AI Gateway documents per-request zero data retention and no
  training for Jev. OpenRouter does not confirm either for Jev; TypeSafe's direct API
  does not document retention tiers publicly. With synthetic data this does not block
  the experiment; each manifest records the route.
- From the cloud coding environment, `openrouter.ai`, `api.typesafe.ai`,
  `ai-gateway.vercel.sh`, `api.cloudflare.com` and `huggingface.co` are all refused
  by the network policy. Phase 0 runs on the owner's workstation, or in that
  environment once `openrouter.ai` is allowed and the key is supplied as an
  environment variable.

## 5. A checked turn, decision by decision

The hosted `clinical_answer` pipeline at the pinned Hub runs
`context, answer, gate, resolve_refs, review, gate, final_resolve_refs,
ground_verdicts, indepth, indepth_gate`. A checked turn makes up to six Gemma passes
on a single-slot router (answer, review, an optional recheck of the correction,
grounding, In-Depth synthesis and its gate); all but the answer and the In-Depth
synthesis exist only to decide something.

| Stage | Today | Decision shape | What a decision model changes | Plan |
| --- | --- | --- | --- | --- |
| `context`: QueryStore slice tiers (`mandatory`, `exact`, `typed`, `recency_anchor`, `similarity`, `panel`; [ADR Decision 17](https://github.com/pmanko/querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/adr.md)) then the Hub's local ranker in [`context_sources.py`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/context_sources.py#L1298): exact terms, token overlap, QueryStore rank, slice tier, recent core, then a `zero_relevance` bucket, fitted to the exact token budget | No model call. Every signal is lexical, a bi-encoder cosine, a type or a date; nothing reads the record against the question. This is where #587 lost patient 39's creatinine records | Noul per record: "is this record relevant to this question?" | Drop order when the budget overflows and a recall net over the zero-relevance bucket, engine-side beside the local ranker (QueryStore's contract excludes question interpretation). The honest competitor is a local cross-encoder reranker, which is the same mechanism without the natural-language criterion and can be trained on our pairs | P0.5, G0, P3.4 |
| `answer` | Generative | None | Nothing | Out |
| `gate` (both) | Deterministic temporal, date and drug-safety rules | None | Nothing; Checked requires deterministic results | Out by contract |
| `review`: [`_validate_answer_rewrite`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/team.py#L1749) returns `{answer_ok, errors[], corrected_answer}`; a correction is rechecked by a second pass, then re-gated | One or two full-chart generation passes | `answer_ok` is a Noul; `errors` is a per-sentence Noul with probabilities doing the localisation; `corrected_answer` and the clinician-facing note are generative | A fast check decides whether the slow repair runs; the repair and the note stay with Gemma. A turn that skipped the generative review cannot be Checked under the current provider contract, so this needs a new label and a contract change. Worth building only if the review stage's latency share, from the packets' `stage_timing`, says so | P0.2, P3.2 |
| `ground_verdicts`: [`_entailment_verdicts`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/team.py#L525), batched YES/NO per (source, statement) under `_ENTAILMENT_SYSTEM_PROMPT`, JSON schema, fail-open to `unchecked`; `unsupported` drives `needs_review` | One generation pass; batched because per-pair fan-out is no faster on one slot | Already a pure closed decision: Noul per pair, all pairs in parallel | A probability per pair in one sub-second request. A threshold policy (unsupported below a band, unclear within it, supported above) maps onto the harness's adjudication labels instead of a binary token; the malformed-output fail-open goes away (a transport failure still fails open), the context-overflow one remains at 32K. Risk: correlated errors add speed, not evidence | P0.2–P0.7, G1, Phase 2 |
| `indepth_gate`: [`_validate_indepth_verdict`](https://github.com/pmanko/med-agent-hub/blob/05a40fb4f074d4a108df0c705b30492d48309d94/server/team.py#L1871) returns `{drop:[claims], issues}` | One JSON call | Noul per claim: the grounding question at claim granularity | Per-claim probabilities; low harm because In-Depth is review-only | P3.1 |
| `gather` (team profiles) | Orchestrator tool loop | Choice | Routing; team profiles are not the product path | P3.3 |

The principle that falls out: keep Gemma for drafting, repairing and explaining; move
the deciding to a model whose output is a calibrated probability. The gains, if it
works on our charts: checks drop from generation passes to parallel sub-second calls;
fewer `unchecked` fall-throughs; thresholds instead of binaries, so uncertain cases
can route to a person; localisation without asking the LLM for an errors array. The
costs: no rationale, so `errors`, `issues` and the confidence notes stay generative and
run only when a check fails; Jev is cloud-only and cannot be a product dependency under
the local-first design, while Laya needs our labels; and the published result is that
Jev is wrong where LLM judges are wrong.

The evaluation side follows the same logic. The Hub's validation is the product's
self-check; the harness's Scout judge is the external evaluation. Its categorical axes
and `harm` are closed; the 0 to 10 axes are ordinal, Jev's documented weakness; the
`note` is generative. Jev's role there is a screening actor that allocates human
adjudication, never the promoted judge.

## 6. Inputs on disk for Phase 0

The [context-evaluation gold](2026-10-07-context-evaluation/gold.json) carries the
record text, so the relevance replay needs nothing from the workstation:

| | |
| --- | --- |
| Patients | 5 (ledgers of 320, 214, 168, 157 and 121 records; 980 in total) |
| Topics | 8 (programs, allergies, medications, eye, heart, fractures, kidney, mental) |
| Record–topic pairs | 7,840 |
| On-topic pairs | 91 (about 1.2%), in 18 of 40 cells |

Two consequences. The labels were produced by the native `build_gold_rc2.py` rules
with one manual exclusion (see the [7 October review](2026-10-07-context-evaluation.md)),
not by clinicians, so a disagreement with the gold is read before it counts as a model
error; the model may be right. And with on-topic pairs near 1%, agreement statistics
are dominated by the easy negatives; recall of on-topic records and precision per
patient and topic, plus a calibration curve, are the informative measures.

The `hub-profile-candidate` and `small-model-answer-paths` run packets are not in the
umbrella checkout; only their comparison-set definitions are. The traces live in the
harness run directories on the owner's workstation, which is another reason the
grounding replay runs there.

## 7. Changes made to the spec

- Status line records this update; the rationale pointer adds this review.
- Rule added: `typesafe/jev-router` is never a route. Rule added: rule-made labels are
  recorded as such and disagreements are read.
- Phase 0 split into 0a (relevance, committed inputs, runs first) and 0b (grounding,
  run packets). Item IDs kept.
- P0.5 gains three arms: Jev, an untrained local cross-encoder reranker, and Laya
  fine-tuned leave-one-patient-out; scored as recall and precision per patient and
  topic with a calibration curve; every disagreement read.
- G0 added: a routing decision for P3.4, not a stop rule; a local arm that matches
  Jev is preferred because it can ship.
- P0.3 and P0.6 drop the zero-shot Laya arm; P0.6 adds the probability bands that
  reproduce the adjudicators' three labels.
- G1 failure now closes Phase 2 and P3.1 to P3.3; Phase 1 and P3.4 do not depend on
  it. The 10 October text closed the whole experiment, which would have discarded the
  evaluation arm for a grounding result.
- P2.2 records the P0.6 bands as a proposed threshold policy, not applied.
- P3.2 states the fast-check, slow-repair split and its latency-share condition.
- P3.4 added: context admission by relevance probability, engine-side, arm chosen by
  G0, QueryStore unchanged. Not in scope adds question interpretation inside QueryStore.
- D3 changes to a trained Laya arm on relevance only. D5 added: where Phase 0 runs.
- Budget adds about one day for Laya fine-tuning.

## 8. Open decisions

D1 to D5 as the spec states them. The owner also supplies the path of the run packets
on the workstation, and, if the cloud environment is to run Phase 0, allows
`openrouter.ai` and sets the key.

## Sources

- [Laya model card, Hugging Face](https://huggingface.co/convaiinnovations/laya);
  [Laya repository](https://github.com/NandhaKishorM/laya);
  [i-scoop on Laya](https://www.i-scoop.eu/laya-system-1-decision-model/);
  [OrcaRouter: Laya explained](https://www.orcarouter.ai/blog/laya-decision-model-explained)
- [nexos.ai: what is Jev](https://nexos.ai/blog/what-is-jev/);
  [Jev API access guide](https://opentweet.io/jev/api-access);
  [OpenRouter: Jev Router](https://openrouter.ai/typesafe/jev-router);
  [RuntimeWire on Jev Router](https://runtimewire.com/article/typesafe-jev-router-openrouter-launch)
- arXiv [2609.29769](https://arxiv.org/abs/2609.29769), [2609.26550](https://arxiv.org/abs/2609.26550),
  [2609.24052](https://arxiv.org/pdf/2609.24052), [2609.28940](https://arxiv.org/html/2609.28940v1)
  (summarised in the 10 October review)
