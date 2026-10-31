# OpenClinAI roadmap

This is the landscape of OpenClinAI's efforts: one row per thread, and the current
priorities across them. Each delivery thread has its own spec written as a target
path with checkboxes; an exploration links its research until the owner scopes it
as a thread. Dated evidence lives in [`reviews/`](reviews/).
[Architecture](architecture.md) owns component boundaries, product repositories
own application behavior, and the harness owns experiments. The workspace refactor
that created this layout (`PR-DECOMPOSITION-2026-09`) is complete and closed in its
[closeout record](reviews/2026-10-02-refactor-closeout.md).

## Threads

| Thread | Spec | State | Next |
| --- | --- | --- | --- |
| Local HIV research environment | [local-hiv-environment.md](local-hiv-environment.md) | Setup and reset restore the published default baseline in about 5 minutes; Ross's fresh install passed; account context reaches the model; the 18 October module heads need a rebuilt baseline | New default baseline for the 18 October heads; Docker-only prerequisites |
| Provider parity and local inference efficiency | [provider-parity.md](provider-parity.md) | Hub reads its context once per answer: checked answers take 16–56 s here when the router reuses the chart's temporal facts, 83–204 s when it does not, against 7–51 s built-in | Cross-question reuse; OpenRouter comparison; Ross re-measures |
| OpenMRS contribution (Track A) | [openmrs-contribution.md](openmrs-contribution.md) | Three gh-stack stacks on the OpenMRS repositories since 21 October, one PR per layer targeting the layer below; the frontend stack (#72–#76) merged 27 October; QueryStore #94–#98 and backend #617–#623 are restacked with the maintainer's rounds 10 and 11 answered ([record](reviews/2026-10-26-upstream-sync.md)) | The maintainer's merge order for QueryStore and the backend; the ESM fork main and umbrella pin moved to the merged upstream |
| Review process and gates | [review-process.md](review-process.md) | Designed 20 October from the maintainer's documented method ([record](reviews/2026-10-20-maintainer-review-process.md)); nothing built | Owner marks up the design; then hooks and probes, applied to the open round |
| Judging | [judging.md](judging.md) | C1 to C5 built on harness #200 and umbrella #28 (judge cards, repeated passes with agreement, a judge panel, blinded per-scenario sessions, per-pass drill-down); no run has used them yet | The first blinded, three-pass run (the checked-answers runs), then tick the boxes |
| Checked answers | [checked-answers.md](checked-answers.md) | A1 to A4 built (Hub #41 to #44); run A judged 27 October and rerun on the fixed Hub (8dacd7b1, judging in progress); run B waits for the label remediation | Run B on the remediated Hub, then A7 from the judged runs |
| Confidence labels | [confidence-labels.md](confidence-labels.md) | Proposed 27 October from the dashboard review: the checks mark correct claims (35% of In-Depth points marked, half the red false), the strict citation prompt made Qwen reject everything, DRY garbles copied dates; the judge no longer sees the checks and scores every In-Depth point | L1 measure each check against the judge on run 8dacd7b1; the cheap Hub label changes before run B |
| Catalyst delivery | [catalyst-delivery.md](catalyst-delivery.md) | Four journeys demonstrated; acceptance open | FP-009 and FP-010 |
| Local stacks, alone and together | [local-stacks.md](local-stacks.md) | Each stack alone and both on one Hub, Catalyst at OpenELIS Global 2 3.3.0; all smokes and both harness suites run on 25 October ([record](reviews/2026-10-25-local-stacks-together.md)) | The harness Catalyst suite's retired base SQL and the Hub's missing qwen2.5-14b token count |
| Website and publication | [website-publication.md](website-publication.md) | Documentation site deploys from `main`; landing site live from the umbrella's own website proxy since 18 October | Audit item W04 |
| WA Health Summary (WAHS) | [wahs.md](wahs.md) | Phase 2 (`W1`–`W3`) and Phase 3 active local validation & refinement slices (`W4`–`W8` & `W12`–`W14`) complete and published 31 October ([openclinai.org#33](https://github.com/pmanko/openclinai.org/pull/33), [record](reviews/2026-10-31-wahs-phase3-local-validation.md)): non-destructive `lossless_structural` condensation decoupled from skill-based chart-hygiene/reconciliation findings (`W12`), generalized KB-driven FHIR R4 engine across 6 patients / 14 bundles / 39 cases (`W14`: 3 Synthea Set A/B/C + 3 US Core clinical transition archetypes + client-side Custom FHIR R4 Bundle inspector on `wahs-demo.openclinai.org`), optional `W9` privacy decoupling, hybrid full-chart overflow lookup tools, and 3 de-saturated modality-separated reports | Deferred tracks `W9` (optional sensitive-record redaction & `sd-fhir` cryptographic selective disclosure in the Secure FHIR Bundle workstream after team discussion), `W10` (CIRG 4-VM shared H200 GPU run next week), and `W11` (partner-supplied real WAHS summaries) |
| Decision-layer experiment (Jev, Laya) | [decision-layer-experiment.md](decision-layer-experiment.md) | Proposed; aligned 27 October with the label-only pipeline in [checked-answers.md](checked-answers.md) | Decisions D1–D5 |
| Clinical knowledge bases | No umbrella spec yet. The Hub ships one static knowledge-base source; the harness holds the [research notes](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/artifacts/planning/clinical-kb-research.md) | Exploration | Owner decides whether to scope a thread |
| Validation methodology | The [harness](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/README.md) and its [evaluation methodology brief](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/artifacts/planning/eval-methodology-brief.md) | Runs experiments against the local stack; the 7 and 10 October reviews are its latest outputs | Serves the other threads' evaluations |
| Workspace and validation refactor (Track B) | [closeout record](reviews/2026-10-02-refactor-closeout.md) | Complete, 2 October | None |

## Current priorities

1. [Review process and gates](review-process.md): the owner marks up the
   design; hooks and probes first, applied to the 20 October round.
2. [OpenMRS contribution delivery](openmrs-contribution.md): the
   [target path](openmrs-contribution.md#target-path): the fresh-reviewer
   findings in their owning layers, the local boot check of the stack tops, then
   the maintainer's review and the merge order.
3. [Confidence labels](confidence-labels.md): measure every check against the
   judge on the rerun, then the label semantics, checker prompts and sampling
   changes in the Hub, so a red mark means a proven contradiction.
4. [Checked answers](checked-answers.md): run B on the remediated Hub, then the
   default profile from the judged runs.
5. [Provider parity](provider-parity.md): close the remaining gap, the router's
   reuse of the chart's temporal facts across questions, so Hub answers are at
   least as fast as the built-in provider.
6. [Local HIV research environment](local-hiv-environment.md): setup needs only
   Docker and the native model router.
7. [Local stacks, alone and together](local-stacks.md): the two harness suite
   defects the shared run found.
8. [Catalyst delivery](catalyst-delivery.md): owner acceptance of the four local and
   server journeys and publication verification.
9. [Website and publication](website-publication.md): close audit item W04.
10. [Decision-layer experiment](decision-layer-experiment.md): owner review of the
   proposal.

Upstream merging, deployment changes and release or clinical signoffs are not
authorized by any item here; each thread spec names its signoffs.

## Standing checks

- `Workspace` workflow: umbrella unit tests and `scripts/check_workspace.py` on a
  recursive checkout.
- `operations` workflow: workspace operation tests, the assembled QueryStore and
  ChartSearchAI source build, and ESM verification.
- Pages workflow: website tests, build, rendered link and asset checks, deploy.
- Harness independence is asserted by `tests/test_operation_ownership.py`. Product,
  deployed-runtime and clinical acceptance need real-interface evidence recorded in
  the stream specs.

## Outstanding decisions

- **Fork-main pushes:** fork mains are the integration branches the umbrella pins
  ([AGENTS.md](../AGENTS.md)), but the pre-push hook refuses every push to a
  default branch, so moving one needs `--no-verify` today. Decide how pushes to
  the pmanko fork mains get through.
- **Data tooling:** assign a maintained owner for reusable migration and
  terminology utilities outside the validation runner.
- **Public hosting:** decide repository organization, visibility or hosting changes
  separately from documentation cleanup.
- **External consumers:** the Hub README and Catalyst documents link roadmap
  section anchors that no longer exist; update them when those components next
  publish.
- **Decision-layer experiment:** decisions D1 to D5 are recorded in
  [its spec](decision-layer-experiment.md).

## Evidence

- [2 October documentation audit](reviews/2026-10-02-documentation-audit.md)
- [2 October refactor closeout](reviews/2026-10-02-refactor-closeout.md)
- [7 October context evaluation](reviews/2026-10-07-context-evaluation.md)
- [7 October Track A remediation record](reviews/2026-10-07-track-a-remediation.md)
- [10 October revamp audit and experiment proposal](reviews/2026-10-10-revamp-audit-and-jev-experiment.md)
- [13 October Appointments fresh-import root cause](reviews/2026-10-13-appointments-fresh-import-root-cause.md)
- [14 October fresh setup acceptance](reviews/2026-10-14-fresh-setup-acceptance.md)
- [16 October account context](reviews/2026-10-16-account-context.md)
- [16 October decision-layer research update](reviews/2026-10-16-decision-layer-research-update.md)
- [16 October provider parity findings](reviews/2026-10-16-provider-parity-findings.md)
- [17 October provider parity measurements](reviews/2026-10-17-provider-parity-measurements.md)
- [18 October Track A upstream sync](reviews/2026-10-18-track-a-upstream-sync.md)
- [18 October landing publication](reviews/2026-10-18-landing-publication.md)
- [19 October Track A review revalidation](reviews/2026-10-19-track-a-review-revalidation.md)
- [20 October Track A end-to-end check on the stack tips](reviews/2026-10-20-track-a-e2e.md)
- [20 October Track A independent review and fixes](reviews/2026-10-20-track-a-review-round.md)
- [20 October QueryStore #88 retrieval diversity evaluation](reviews/2026-10-20-querystore-88-retrieval-diversity.md)
- [21 October cutover to gh-stack stacks on the OpenMRS repositories](reviews/2026-10-21-stack-cutover.md)
- [21 October maintainer round on the new stacks: inventory and harness gaps](reviews/2026-10-21-maintainer-round-on-the-stacks.md)
- [30 October WAHS Phase 2 evaluation report](reviews/2026-10-30-wahs-evaluation-report.md)
- [31 October WAHS Phase 3 local validation and de-saturated ablation closeout](reviews/2026-10-31-wahs-phase3-local-validation.md)
