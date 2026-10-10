# Umbrella refactor closeout (`PR-DECOMPOSITION-2026-09`)

Recorded 2 October 2026; status snapshot as of umbrella `a53061f` (9 October);
consolidated out of the roadmap on 10 October 2026. This is dated evidence that the
workspace and validation refactor (Track B) completed. The
[roadmap index](../roadmap.md) owns current coordination and the
[architecture](../architecture.md) owns current component boundaries; neither
repeats this record.

## Phases

| Phase | Deliverable | Acceptance criteria | Final status |
| --- | --- | --- | --- |
| U0 Ownership and dependencies | Map capabilities, interfaces and consumers to component owners | Each capability has an owner, defined inputs/outputs and verification criteria | Ownership consolidation and its documentation companions merged |
| U1 Component and management ownership | Direct umbrella gitlinks and workspace-management tooling; removal of nested product gitlinks and `openmrs_chatbot` | One canonical gitlink per component; fresh umbrella checkout resolves recorded revisions; umbrella tooling manages component selection and checkouts | Implemented and merged; fresh recursive checkout and offline workspace verification recorded |
| U2 Independent validation | Modular experiment execution, target adapters, evidence collection, evaluation and reporting | Experiments run against configured targets without Git, submodules, product source trees, product pins or an umbrella installation; offline reports consume captured artifacts only | Implemented and merged; local and hosted harness suites pass; portable reports and isolation tested with doubles; product acceptance remains separate |
| U3 Environment and delivery tooling | Umbrella environment, build, deployment and release orchestration; website build and publication tooling | Configured workspace operations invoke product-native commands; website build/publication runs from umbrella-owned sources, configuration and workflows; build/run provenance records actual inputs | Ownership move merged; operational tests and documentation Pages build/deploy pass; local HIV setup documented in the setup guide |
| U4 Documentation and interfaces | Current specs, instructions, commands, configuration, CI and website consumers aligned with ownership | Consumers resolve directly to current owners; obsolete specs, copied history and unnecessary compatibility entry points are removed | Retained requirements, consumers and cleanup merged; documentation published; broader public-content proposals retain their own review |
| U5 Completion | Remove remaining obsolete code, dependencies and duplicate responsibilities; verify the assembled system | Independent harness checks and umbrella integration checks pass; current requirements have one maintained owner; component and deployed acceptance are explicit | Repository split and documentation closeout merged and verified; not a claim of Ross handoff, upstream merging or new clinical/product acceptance |

### Dependencies as planned

- U0 mapped the capabilities and consumers affected by each implementation change.
- U1 and U2 shared changes where component layout affected a validation adapter.
- U3 used the component configuration and native entry points established in U1.
  Website source and publication ownership was implemented independently of
  product checkout changes.
- U4 updated documentation, references and tests alongside their interfaces. With
  U1/U2, the harness constitution, agent instructions and SpecKit context were
  amended to define experiment-runner scope and configurable targets and to remove
  control-plane duties and fixed product-path requirements.
- OpenMRS contribution publication proceeded as a separate delivery track.

### Verification as performed

**Harness isolation:** configured experiments were installed and run in an
environment without Git, product source checkouts or the umbrella, confirming that
execution performs no pin lookups, checkouts, builds, deployments or release-policy
checks. Adapter configuration, output/trace capture, supplied or observed
provenance, missing-metadata handling and evaluation/report generation were tested.
Test doubles validated runner mechanics; product acceptance uses actual product
interfaces.

**Umbrella integration:** component gitlinks, remote reachability, required
build/deployment entry points and the configured handoff to validation were
verified. Component commits are published in their owning repositories before being
referenced by an umbrella gitlink. Experiment manifests capture the target identity
supplied by the workspace or reported by the target.

**Website delivery:** the selected public surfaces were built and previewed from
this repository with navigation, links, assets, media and narrow/desktop rendering
checked. Publication checks run through umbrella-owned tooling and record the
source revision, deployed output and live verification. The website pipeline
operates independently of the validation runtime.

**Contract coverage:** product safety and clinical behavior are verified against
product contracts, and scoring and sampling against experiment definitions. Test
coverage is maintained for each supported interface; tests for retired interfaces
were removed.

## Closeout evidence

Recorded 2 October 2026. These revisions replaced the pre-merge companion pins:

| Component | Merged changes | Recorded revision |
| --- | --- | --- |
| Validation harness | [#197](https://github.com/pmanko/clinical-ai-validation-harness/pull/197), [#198](https://github.com/pmanko/clinical-ai-validation-harness/pull/198) | `5f180650aab46e607e5f21595faa4d0dc1620d4c` |
| Med Agent Hub | [#32](https://github.com/pmanko/med-agent-hub/pull/32) | `96d0489660c161acdf28f6ace621a29654e48c49` |
| Catalyst | [#140](https://github.com/DIGI-UW/catalyst-ai/pull/140) | `94742f1af6d634f03b47b9e97f3512829ba265b1` |

The OpenMRS component pins were unchanged by the closeout. All four companion PRs
passed their applicable hosted checks before merging. The final harness tree was
identical to the checked documentation PR head. Local verification: 1,136 harness
tests passed, 36 skipped and 3 deselected; 97% changed-line coverage; 58 focused
checks passed on the documentation branch; Markdown consistency passed. Umbrella
verification: 24 unit tests, 230 operational tests, 125 website/publication tests
and 54 site tests passed. The operational suite deselected one opt-in test. These
are source, runner and tooling checks, not live clinical evaluation.

GitHub Pages was enabled in workflow mode without a custom-domain or DNS change.
The [documentation publication run](https://github.com/pmanko/openclinai.org/actions/runs/37078640482)
passed build, rendered-link/asset checks and deployment from
`30133f3db9c574dd918349ce2822fec54abba06a`. The
[published documentation](https://pmanko.github.io/openclinai.org/) and its
architecture page were inspected in the browser. Subsequent `main` updates publish
through the same workflow. This is not a claim that the separate `openclinai.org`
landing deployment or a product environment was updated.

On 4 October the Hub pin moved to `05a40fb4f074d4a108df0c705b30492d48309d94`
("Use checked Gemma 4 12B as the clinical default"), the head of Hub
[#33](https://github.com/pmanko/med-agent-hub/pull/33), which was still unmerged on
10 October.

## Status snapshot

As recorded in the roadmap at umbrella `a53061f` (9 October 2026):

| Area | State | Remaining work |
| --- | --- | --- |
| Umbrella repository | [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org) owns product operations, component pins and website sources; PRs #2–#8 merged | Review the local HIV setup and support fresh installations using the setup guide |
| Component checkouts | Exactly six direct components have recorded revisions; harness product gitlinks and `openmrs_chatbot` are absent; companion changes merged | Preserve recorded versions during environment setup and updates |
| Validation harness | PRs #197 and #198 merged; runners use configured targets and supplied/observed provenance; required fields/types are checked without treating caller claims as verified revisions | Verify actual product interfaces separately; fixture isolation is not product acceptance |
| Website | Sources and publication tooling umbrella-owned; GitHub Pages configured for Actions and build/deploy pass; browser inspection confirms the documentation loads | Public landing deployment and product/demo publication remain separate |
| Specifications | Product behavior, shared delivery and validation protocols have maintained owners; duplicate plans and obsolete lane instructions removed; companion documentation merged | Follow the maintained owners; broader content proposals retain their own review |
| Research setup | [Setup guide](../../environments/README.md) and `make chartsearch-research-setup` prepare the fresh HIV baseline, ChartSearchAI and seven accounts using existing tools. Local startup, account logins and the patient-chart browser smoke passed on 3 October 2026 | PR review and Ross's fresh install. Account-context enhancements and broader evaluation are follow-up, not setup gates |
| Product delivery | Both rebased stacks and owning-PR fixes published; all frontend builds, backend #583–#586 checks and the umbrella's assembled source checks pass. Backend #587–#590 pass paired-source builds but fail against the unpublished QueryStore API. Three #587 review threads and QueryStore's smaller-PR request remain open | See the [7 October remediation record](2026-10-07-track-a-remediation.md) and the [OpenMRS contribution spec](../openmrs-contribution.md) |

## Specification ownership migration map

Paths are relative to the validation harness. Each row records where the
requirements of the pre-refactor material now live. Identifiers were retained under
one maintained owner; SpecKit pointers, instructions, links, imports, navigation,
generated catalogs and tests were updated to reference that owner, and obsolete
specification content and its references were removed.

| Source material | Validation responsibility | Other ownership or disposition |
| --- | --- | --- |
| `specs/001-harness-control-plane-foundation/` | Experiment readiness, fixture/endpoint identity and run provenance | Component catalog, pins, checkouts, builds and shared environment management belong to the umbrella |
| `specs/002-openmrs-demo-data-2-8-remap/` | Reviewed validation corpus, mappings, fixtures, clinical-meaning checks and provenance | Reusable migration/terminology utilities require a data-tooling owner; shared deployment belongs outside the harness |
| Feature 006 smoke/evaluation criteria | Retains `SC-004.4` and namespaced `MAH-CONSOLIDATION-2026-07-09-v1:G09/G21` | Obsolete Feature 004/005/007 files and the redundant consolidation roadmap are deleted |
| `specs/006-validation-harness-mvp/`, metadata and evaluation contracts | Scenarios, adapters, evidence, evaluation, review and reporting | Transport and provider behavior link to their product contracts |
| `specs/008-catalyst-query-workbench/` | Validation scenarios, experiment protocols, evidence and reporting | Catalyst owns application requirements; the umbrella owns cross-project delivery coordination |
| `specs/catalyst-program-roadmap.md` | Evaluation methodology and test protocols | Current delivery priorities belong to the umbrella; application behavior belongs to Catalyst/OpenELIS |
| Four-pathway reporting coordination | Experiments and dated evidence remain in the harness | [Catalyst delivery](../catalyst-delivery.md) owns order and cross-project acceptance; the competing harness roadmap is removed and FP product requirements link directly to Catalyst |
| `specs/artifacts/planning/openmrs-dual-provider-*` | Conformance experiments and their evidence | Integration requirements/reference, joint delivery and release coordination belong to the umbrella; native OpenMRS API documentation is unchanged |
| Program lanes/status | Validation-specific results and dated evidence | Current coordination belongs to the umbrella; obsolete lane hierarchy and competing plans are removed; dated evidence links use immutable source versions |
| Website sources and tests | Experiment artifacts and report generation | `landing/`, `site/`, public catalogs and `tests/website/` are implemented in the umbrella |
| Website/report publication | Validation output artifacts supplied for publication | Umbrella `scripts/`, `.github/workflows/pages.yml` and `compose/website/` own static publication; product deployment is separate |

## Disposition on 10 October 2026

The refactor is complete and this record closes it. Its remaining concerns moved to
their streams: OpenMRS contribution delivery to [its spec](../openmrs-contribution.md),
Catalyst to [its spec](../catalyst-delivery.md), the research environment and
website items to the [roadmap index](../roadmap.md).
