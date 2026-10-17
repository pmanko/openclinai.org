# OpenClinAI roadmap

This is the landscape of OpenClinAI's efforts: one row per thread, each with its
own spec written as a target path with checkboxes, and the current priorities
across them. Dated evidence lives in [`reviews/`](reviews/).
[Architecture](architecture.md) owns component boundaries, product repositories
own application behavior, and the harness owns experiments. The workspace refactor
that created this layout (`PR-DECOMPOSITION-2026-09`) is complete and closed in its
[closeout record](reviews/2026-10-02-refactor-closeout.md).

## Threads

| Thread | Spec | State | Next |
| --- | --- | --- | --- |
| Local HIV research environment | [local-hiv-environment.md](local-hiv-environment.md) | Setup and reset restore the published default baseline in about 5 minutes; Ross's fresh install passed; account context reaches the model | Docker-only prerequisites |
| Provider parity and local inference efficiency | [provider-parity.md](provider-parity.md) | Hub checked answers take 5–8 minutes here and about 20 on Ross's machine, against 42 s for ChartSearchAI's built-in provider; causes identified, nothing fixed yet | Measured baseline, then configuration fixes |
| OpenMRS contribution (Track A) | [openmrs-contribution.md](openmrs-contribution.md) | Thirteen PRs restacked and checked, plus the account-context slice; QueryStore #68 open; #587 finding open | Dispositions for #587 and the #68 split request |
| Catalyst delivery | [catalyst-delivery.md](catalyst-delivery.md) | Four journeys demonstrated; acceptance open | FP-009 and FP-010 |
| Website and publication | [website-publication.md](website-publication.md) | Documentation site deploys from `main`; landing deployment pending | Publish the reviewed landing content |
| Decision-layer experiment (Jev, Laya) | [decision-layer-experiment.md](decision-layer-experiment.md) | Proposed | Decisions D1–D4 |
| Clinical knowledge bases | No umbrella spec yet. The Hub ships one static knowledge-base source; the harness holds the [research notes](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/clinical-kb-research.md) | Exploration | Owner decides whether to scope a thread |
| Validation methodology | The [harness](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/README.md) and its [evaluation methodology brief](https://github.com/pmanko/clinical-ai-validation-harness/blob/5f180650aab46e607e5f21595faa4d0dc1620d4c/specs/artifacts/planning/eval-methodology-brief.md) | Runs experiments against the local stack; the 7 and 10 October reviews are its latest outputs | Serves the other threads' evaluations |
| Workspace and validation refactor (Track B) | [closeout record](reviews/2026-10-02-refactor-closeout.md) | Complete, 2 October | None |

## Current priorities

1. [OpenMRS contribution delivery](openmrs-contribution.md): dispose of the open
   #587 context-composition finding and the QueryStore #68 split request, then
   obtain ordinary dependency compatibility and remove the temporary paired CI.
2. [Provider parity](provider-parity.md): measure both providers on one question
   set, then close the gap so Hub answers are at least as fast as the built-in
   provider.
3. [Local HIV research environment](local-hiv-environment.md): setup needs only
   Docker and the native model router.
4. [Catalyst delivery](catalyst-delivery.md): owner acceptance of the four local and
   server journeys and publication verification.
5. [Website and publication](website-publication.md): deploy the reviewed landing
   content and close the public findings from the documentation audit.
6. [Decision-layer experiment](decision-layer-experiment.md): owner review of the
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

- **Hub pin:** `targets/med-agent-hub` records the head of Hub
  [#33](https://github.com/pmanko/med-agent-hub/pull/33) rather than Hub `main`.
  Merge #33 or keep the dependency visible here until it merges.
- **Data tooling:** assign a maintained owner for reusable migration and
  terminology utilities outside the validation runner.
- **Public hosting:** decide repository organization, visibility or hosting changes
  separately from documentation cleanup.
- **External consumers:** the Hub README and Catalyst documents link roadmap
  section anchors that no longer exist; update them when those components next
  publish.
- **Decision-layer experiment:** decisions D1 to D4 are recorded in
  [its spec](decision-layer-experiment.md).

## Evidence

- [2 October documentation audit](reviews/2026-10-02-documentation-audit.md)
- [2 October refactor closeout](reviews/2026-10-02-refactor-closeout.md)
- [7 October context evaluation](reviews/2026-10-07-context-evaluation.md)
- [14 October fresh setup acceptance](reviews/2026-10-14-fresh-setup-acceptance.md)
- [16 October account context](reviews/2026-10-16-account-context.md)
- [16 October provider parity findings](reviews/2026-10-16-provider-parity-findings.md)
- [7 October Track A remediation record](reviews/2026-10-07-track-a-remediation.md)
- [10 October revamp audit and experiment proposal](reviews/2026-10-10-revamp-audit-and-jev-experiment.md)
- [13 October Appointments fresh-import root cause](reviews/2026-10-13-appointments-fresh-import-root-cause.md)
