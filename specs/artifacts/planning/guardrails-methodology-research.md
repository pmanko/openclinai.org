# Guardrails and control-flow methodology — research

This public research summary informs clinical-AI experiments. It does not prescribe
Med Agent Hub's current implementation or replace product safety contracts.

## Findings

- **Defense in depth:** every guardrail has failure modes. Combine prompt guidance,
  deterministic checks and review rather than trusting one system prompt. The
  Swiss Cheese model and agentic-defense research support layering, not a claim
  that any particular clinical system is safe.
- **Mix enforcement types:** NeMo Guardrails separates input, retrieval, dialog,
  execution and output checks. LlamaFirewall combines deterministic detectors and
  a model-based auditor. Its reported AgentDojo attack-success reduction
  (17.6% to 1.75%) motivates layering; it does not predict clinical-QA performance.
- **Prompt guidance:** explicit scoped instructions, diverse examples, quote-first
  grounding and a non-contradictory instruction hierarchy are useful methods.
  Vendor guidance for frontier models does not establish equivalent reliability
  for small local models.
- **Well-formed is not correct:** structured decoding can constrain an output's
  shape, but cannot guarantee groundedness, correct clinical interpretation or
  appropriate abstention. Measure those outcomes separately.
- **Reliability is separate from accuracy:** small-model studies report consistent
  but incorrect answers and sensitivity to paraphrases. Evaluate diverse cases,
  paraphrases and adversarial content, not only one successful response.
- **Verification needs independent evidence:** a model's self-check is not a
  universal safety layer. Citation resolution can be checked deterministically;
  claim support and clinical interpretation still require suitable evaluation
  and human review.

## Applying the research to experiments

Capture the exact inputs, output, model and prompt provenance when available,
retrieved evidence, deterministic findings and reviewer rationale. Keep optional
model judgments separate from deterministic safety checks. Study unsupported
claims, fabricated citations, absent evidence, abstention and disclosure limits.
A score or schema-valid response is not product or clinical acceptance.

Whether a workflow needs deterministic control flow or additional output checks
is a product design decision informed by measured failures. Consult the
[product-native contracts](#/spec/specs/background/component-contracts) and the
[current harness experiment contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/006-validation-harness-mvp/spec.md).

## Caveats

- Here, prompt-level guidance and code/constrained-decoding enforcement are
  different mechanisms. Do not equate them with academic uses of “soft” and
  “hard” ethical guardrails.
- Published measurements do not establish exact performance for a deployment's
  4–8B models, prompts, corpus or clinical questions.
- NeMo and LlamaFirewall are examples, not a complete framework comparison or a
  recommendation to add either dependency.
- Security attack-success rates and clinical evidence-grounding measures are
  distinct outcomes.

## Sources

- [Swiss Cheese AI safety](https://arxiv.org/html/2408.02205v3)
- [Agentic defense taxonomy](https://arxiv.org/html/2603.11088v1)
- [NeMo Guardrails process](https://docs.nvidia.com/nemo/guardrails/latest/user-guides/guardrails-process.html)
- [LlamaFirewall](https://arxiv.org/pdf/2505.03574)
- [Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [OpenAI GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
- [Small-model clinical reliability](https://arxiv.org/abs/2603.00917)
- [Reliability versus accuracy](https://arxiv.org/html/2512.14754v1)
