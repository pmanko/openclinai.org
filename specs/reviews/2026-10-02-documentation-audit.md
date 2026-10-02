# Documentation ownership and public-site audit

Observed 2 October 2026. This is review evidence and a remediation proposal,
not another product specification or task authority. The umbrella
[roadmap](../roadmap.md) owns execution. The local consolidation and focused website patch are ready for owner review.
Application behavior and live deployments are unchanged. The review PR advances
Catalyst, Hub and harness pins to their published documentation commits; OpenMRS pins stay unchanged.

## Main finding

The architecture is clearer than its consumers. Current umbrella instructions
assign product behavior to products, experiments to the harness, and assembly,
delivery and publication to OpenClinAI. Several component instructions, long
delivery registers and the live website still describe the previous arrangement.
Updating the top-level roadmap alone will not remove those competing directions.

The existing homepage hierarchy works: ChartSearchAI, Catalyst, Med Agent Hub and
the Validation Harness have their own destinations. Preserve that structure.
The first repair should be ownership and current information, followed by a small
navigation/content pass, not a site redesign.

## Evidence and coverage

The [prior Catalyst task/evidence record](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/008-catalyst-query-workbench/tasks.md)
retains the dated demonstrations and implementation history removed from current planning.

- Source baseline: umbrella `6e048c2`, harness `9b5b87e`, Catalyst `6ba0008`,
  ChartSearchAI `8622f1b`, frontend `e60cea9`, QueryStore `55bf997`, Hub `6120c31`.
  The initial workspace and component checkouts were clean.
- Inventoried 178 Markdown, HTML and canvas source files across umbrella specs,
  landing/docs sources and the selected components. Seventy-four contain markers
  requiring ownership/status review. These are search candidates, not 74 defects.
- Read the umbrella authorities, component instructions, main Catalyst
  specification/program/plan/task sections, OpenMRS contract/roadmap/status,
  publication allowlist/navigation, and affected documentation checks. The historical registers were reviewed by section and owner. Old task chronology
  is not a current backlog; product-code/contract checks decide what remains.
- Found 199 references to the mixed Catalyst/OpenMRS authority files across docs,
  source, tests and status data. Consumers include generated views and executable
  checks, not just Markdown links.
- Browser review: homepage, all four project introductions, reporting pathways,
  OpenMRS contribution guide, the linked public documentation and its legacy
  roadmap, and the report catalog. Homepage inspected at 390 and 1280 CSS pixels;
  reporting pathways and its menu checked at 390 pixels. Neither checked mobile
  page had horizontal overflow. The menu opens and its links are named.
- The configured umbrella Pages destination returned HTTP 404. Browser navigation
  from the live homepage still reaches the old harness Pages deployment.
- Evidence is saved in `artifacts/documentation-audit-2026-10-02/`: source inventory
  and hashes, reference occurrences, live DOM snapshots and screenshots.
  These are one-time audit records, not new permanent tests.

Limits: no new clinical/model run, server deployment, full video playback review,
screen-reader audit, scientific re-scoring or fresh PR-readiness audit was done.
The website's claims of server verification are reported as published claims;
they do not establish current server correctness or owner acceptance.

## Ownership map and proposed dispositions

Paths beginning with `harness:` are in `targets/validation-harness/`;
`Catalyst:` means `targets/catalyst/`. These destinations follow the existing
architecture. Retain content only when it describes current code or explicit current direction.
Delete obsolete sections and consolidate duplicates; preserve IDs for retained
requirements. Historical approval alone does not make an old task current.

| Existing source | Maintained destination | Keep, move or remove |
| --- | --- | --- |
| `harness:specs/008-catalyst-query-workbench/spec.md` | Same harness feature for experiment scenarios and evidence; Catalyst specification/binding design for application requirements | Keep observations, static references and reader protocol. Replace duplicated application rules with product links. Move deployment and owner-signoff scheduling to the umbrella. |
| `harness:specs/008-catalyst-query-workbench/plan.md` and `tasks.md` | Umbrella roadmap for cross-project order and acceptance; Catalyst specification for product work; harness feature for validation work | Preserve `FP-001`–`FP-010` under the appropriate coordination/product responsibility; retain other IDs only where their requirements remain current. Extract current open work; remove repeated dated status narratives from maintained requirements. Historical evidence remains available by commit link. |
| `harness:specs/openelis-reporting-catalyst-integration.md` | Umbrella roadmap Catalyst section | Retain the four pathways, manual-correction acceptance, local/server/video distinctions, owner review and separate native OpenELIS ownership. Product import/Widget/SQL requirements already have Catalyst owners; link them. Delete competing sequences after migration. |
| `harness:specs/catalyst-program-roadmap.md` | Harness for the 12-scenario/21-turn comparison and reader protocol; Catalyst for future conversation behavior; umbrella for scheduling | Keep scenario IDs `A1`–`A4`, `M1`–`M3`, `B1`–`B3`, `U1`–`U2`. Broader conversation scope is intentionally undecided: preserve that decision without inventing requirements. |
| Catalyst responsiveness, URL sessions and follow-ons A/B/C currently in harness plan/tasks | Catalyst specification, linking Hub's profile/role contract; umbrella for rollout order | Preserve responsiveness/session navigation before A (multi-artifact design/shared controls), then B (Metabase), then C (Evidence); each has existing design/compatibility acceptance. Preserve both Dataset origins and explicit SQL execution. |
| `harness:docs/catalyst-demo-operations.md` | `docs/catalyst-demo-operations.md` in the umbrella | Moved locally in this audit. Update human and generated consumers; keep environment-specific commands distinguishable from observed deployment status. No runtime action. |
| `harness:specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md` | Umbrella for our shared integration requirements/reference; existing native module documentation for API behavior; Hub for its execution/checks; harness for fixture consumption/evidence protocol | Split by section; link actual product contracts. Keep shared fixture IDs and executable fixture copies where consumed. Avoid a second product contract owned by the harness. |
| `harness:specs/artifacts/planning/openmrs-dual-provider-parity-roadmap.md` and `...-status.md` | Umbrella OpenMRS delivery/release section; product docs for unique retained behavior; dated records as evidence | Disposition namespaced `OPENMRS-DUAL-PROVIDER-PARITY-2026-07-20:G01`–`G22`. Retain substantive release criteria; remove obsolete hash/branch/old-PR requirements. Do not transfer old signoff statuses as current acceptance. |
| Harness project-status JSON, Markdown/CSV views and lane records | Current coordination belongs to umbrella; dated experiment records stay in harness | Reconcile source JSON, then regenerate consumers. Stop treating frozen snapshots as current requirement owners. Preserve dated evidence links rather than repeatedly maintaining the same status in several files. |
| `Catalyst:docs/roadmap.md`, `harness:specs/catalyst-implementation-plan.md`, archive plans | Current owners above; Git history for obsolete plans | Remove retired authority stubs and obsolete bodies after updating incoming references. Do not add another superseded banner or successor-only placeholder. |
| Product machine-schema copies and the shared conformance fixture | Existing canonical product/fixture owner and explicit consumer copies | Intentional executable copies are not duplicate prose authorities. Preserve them while runtime consumers need them and retain meaningful schema/fixture checks. |

Native OpenELIS requirements remain in its repository. This checkout has no
OpenELIS product submodule; list any needed external consumer changes rather than
silently rewriting unrelated working trees.

## Findings for review

Priority 1 means wrong authority or materially misleading current information.
Priority 2 means confusing navigation, terminology or status presentation.

| ID | Priority | Evidence | Impact and suggested remediation |
| --- | --- | --- | --- |
| D01 | 1 | `Catalyst:AGENTS.md` Program order/Setup; product specification Delivery authority; `docs/med-agent-hub.md` | Catalyst still assigns delivery order, pins and shared runtime operations to the harness. Update instructions and README consumers atomically with the migrated requirements. |
| D02 | 1 | Feature 008 plan: Ownership boundary versus Authority and scope; 786-line plan and 1,643-line task register | The same feature says the umbrella owns delivery while claiming to be the authoritative product implementation roadmap. Separate product work, coordination and experiments; reduce repeated chronological status to linked evidence. |
| D03 | 1 | OpenMRS parity status opening and Control Record | It requires reading an immutable roadmap plus amendments, names the original integration PRs, and says a branch/publication checker enforces them. These contradict the current split and permanent-test boundary. Reconcile retained requirements directly into owners; remove obsolete branch/hash obligations. |
| D04 | 1 | [Live documentation](https://pmanko.github.io/clinical-ai-validation-harness/) and its Validation roadmap; [configured new destination](https://pmanko.github.io/openclinai.org/) returned 404 | Visitors receive the old control-plane architecture, retired feature folders and old worktree kickoff instructions. Local `site/published-content.ts` already excludes many of these. Publish the maintained docs before changing live links; address old public routes deliberately. |
| D05 | 1 | [Live harness page](https://openclinai.org/validation-harness/) says “Keep compatible component revisions”; homepage says Harness integrates components | Published ownership is wrong. Local landing sources already explain configured experiments correctly. This is primarily a publication gap, not another copy rewrite. |
| D06 | 1 | [OpenMRS contribution guide](https://openclinai.org/docs/openmrs-upstream/) says three PRs, names backend #157/frontend #23 and links harness #181 | Its September date is visible, but the page remains linked as current contribution/review guidance. Replace the current inventory with the approved 8+5 split and QueryStore dependency, refresh review evidence when publishing, and link umbrella coordination. Preserve historical PR discussions in GitHub rather than the current page. |
| D07 | 1 | [Catalyst introduction](https://openclinai.org/catalyst/) says four server dashboards are verified, then says final four-pathway server validation remains open; [pathway page](https://openclinai.org/catalyst/reporting-pathways/) records September 16 demonstrations; harness delivery status still describes earlier pending work | Reconcile the exact evidence and remaining acceptance scope. Use one dated public status summary and link it. Do not infer owner acceptance from recordings or quietly change historical evidence. This contradiction also exists in local landing source. |
| D08 | 1 | `specs/background/component-contracts.md` links to retired Catalyst `docs/roadmap.md` and unchanged `harness-integration` branches | A new technical reader is directed to obsolete delivery authority and older reference branches. Link maintained product authorities at reviewed revisions, and the umbrella for delivery; clearly label reference branches when actually needed. |
| D09 | 2 | Retired Catalyst roadmap, retired harness implementation stub, old planning/archive records still encountered through current references | “Retired” banners leave old instructions searchable beside new ones. Remove obsolete specifications and incoming authority links after unique-requirement mapping. Keep actual dated run/design evidence identifiable as evidence. |
| D10 | 2 | `harness:scripts/verify-docs-consistency.sh` and `tests/operations/test_dual_provider_conformance_contract.py` | Checks require prose phrases/section names and the old authority files. They cannot prove coherent ownership and can obstruct valid cleanup. Remove semantic wording assertions when moving the documents; retain file/link integrity and executable schema/product behavior checks. Do not add tests for this temporary migration map. |
| W01 | 2 | [ChartSearchAI page](https://openclinai.org/chartsearchai/) describes five “shared lifecycle” stages ending in In-Depth | A nontechnical visitor may read every stage as universal, though these depend on the selected provider/model. Say the recording shows the Hub workflow, and explain unavailable optional stages in one sentence. Keep profile codes and event details in developer documentation. |
| W02 | 2 | Product pages link “Source”, a demo, or older technical examples; setup link lands on legacy generic docs | Separate reader actions: watch an example, read setup requirements, inspect the code, understand limitations. A developer should reach product setup directly; a nontechnical visitor should not need to parse model profile names or repository status. Keep the existing four-project structure. |
| W03 | 2 | [Report catalog](https://reports.openclinai.org/) expands many detailed score tables in one long page | The catalog correctly labels historical evidence and uses newest-first ordering. Keep those. Propose concise dated study cards with question, sample/method and limitation; leave full tables in reports or disclosures. No new ranking, regrouping by project, or scoring change. |
| W04 | 1 | Report catalog “Lever sweep (dev)” describes two writers/4 prompt arms, while the displayed table includes `wide-31b-*` and team rows; “priority questions” metadata names Zabella but narrative names Aloice | Catalog narrative and data may refer to different runs. Check source manifests/summary provenance before editing either. Flag the mismatch; do not repair by guessing the intended results or changing the underlying reports. |
| W05 | 2 | Mobile reporting page repeats “complementary…not equivalent competitors” in the hero and following paragraph; no direct pathway jump list | Tighten repeated copy and offer four short pathway links for long-page navigation. The 390px layout and menu work; there is no observed need for a full layout redesign. |

## Persona review

These are observed journeys and editorial judgments, not completed usability
research with recruited participants.

| Reader and task | Observed strengths | Friction / proposed acceptance |
| --- | --- | --- |
| Clinician or program lead: understand what the tools do | Outcome-led homepage, separate ChartSearchAI/Catalyst pages, visible research limitations and recorded examples | Replace profile shorthand such as E4B/12B at first mention with a short explanation. A reader should identify the tool, see one example and understand what still needs human review without opening GitHub. |
| Reporting analyst: choose CSV or connected data | Four pathways explain snapshot versus live/pipeline freshness, and preserve the manual recovery observation | Add direct pathway navigation and consistent status. The reader should know where to start, whether SQL is involved, and whether the evidence is local video, server validation or owner acceptance. |
| Implementer/developer: install or contribute | Public sources are linked; maintained local component index and architecture exist | Publish current docs, fix product authority links and provide direct setup paths. The reader must reach one current setup/contract owner without traversing retired plans. |
| Research reviewer: inspect a claim | Dated studies, source reports, limitations and separate Answer/In-Depth results | Reconcile catalog mismatches; reduce the initial information load without changing results. The reader must be able to locate the study method and data behind every summary. |
| OpenMRS maintainer: find a reviewable change | Contribution page explains component responsibilities in plain language | Update to the exact small PR chains and their declared dependency. Each link should open the intended scoped diff; a page date must accompany any summarized CI/review claim. |

## Remediation proposal to verify with the owner

1. **Complete the ownership move locally.** Reconcile unique requirements by
   section/ID; update product instructions, spec references and status-data
   consumers in the same change. Keep only experiments/evidence in harness
   Feature 008. Remove obsolete specification bodies after the mapping is complete.
   Do not infer completion from deleting files or passing a wording check.
2. **Prepare a current public-content patch.** Update the OpenMRS inventory,
   reconcile Catalyst status, qualify optional ChartSearchAI stages, and make
   setup links direct. Keep the four-project homepage and current visual style.
   Show the changed pages locally for approval before publication.
3. **Publish in dependency order.** The existing configured destination is
   `https://pmanko.github.io/openclinai.org/`. Verify it serves the reviewed
   build first, then publish the already-corrected landing links and text.
   Propose redirects from public legacy routes to their maintained counterparts;
   keep historical report URLs stable. A move to `openclinai.org/docs/` is an
   optional hosting decision, not required for this cleanup.
4. **Reconcile report-catalog provenance separately.** Verify the two concrete
   mismatches against captured run metadata, then propose precise text/data
   corrections. Keep historical reports unchanged unless the evidence establishes
   a report defect. Catalog compression is a separate editorial choice.

Verification of the ownership move: a one-time review accounts for retained
requirements and identifies obsolete sections; removed sources have no maintained
authority consumers; existing link and schema checks pass; component review
confirms behavior was not changed. Build and test the website with its existing
commands. Then inspect the agreed reader journeys and desktop/narrow layouts.
Publication requires a separate live URL/content/link check against the reviewed
build. None of these checks claims clinical acceptance.

## Work performed and remaining

- Updated the umbrella roadmap's active priority to this cleanup and corrected
  its blanket claim that actual product builds were still pending.
- Moved the Catalyst operations guide into its owning umbrella repository and
  updated its harness consumers, including generated status views. This is a
  local change; the new GitHub destination is not claimed published.
- Completed the initial source inventory and the live journeys described above.
- Local consolidation and verification are complete. The proposal below and the
  focused public-content patch are submitted for owner review. The documentation is now published for PR review with companion component pins.
  No upstream feature merge or website deployment has been performed.

## Approved focused content patch

The owner approved preparing this patch on 2 October and then requested PR review.
The website changes are published for code review, not deployed to the live site. Changes retain the four-project layout and existing recordings:

- Replace the September three-PR inventory with the eight backend and five
  frontend contributions in the approved order, plus QueryStore #68. GitHub
  heads, bases, draft state and checks were refreshed; all fourteen PRs are open,
  non-draft and have successful applicable builds. Superseded cancellations and
  skipped publication jobs are distinguished from successful checks. This is
  not a new review-thread or runtime acceptance audit.
- Replace the historical review ledger with links to the live discussions and
  recorded acceptance, preserving the backend macOS socket-test limitation.
- Describe ChartSearchAI checks, In-Depth and streaming as capability-dependent;
  explicitly mention the streaming toggle and name the demonstration models.
- Give Catalyst one dated demonstration-status destination instead of
  contradictory summaries. Add pathway jump links and direct product setup
  links; replace the retired Catalyst roadmap link with its specification.
- Remove two editorial tests that enforced exact copy, a September date and
  the old three-PR inventory. Do not replace them with assertions for today's
  thirteen-PR arrangement. Existing link, asset and product behavior checks
  remain; other prose-only checks are still identified for the wider cleanup.

Evidence: `pr-inventory.json` and `patch-*.jpg` in the audit artifact directory.
The contribution page was checked at desktop and 390px widths; the reporting
page and its CSV jump link were checked at 390px. Neither narrow page overflowed.
No model, deployment or scientific-report acceptance was repeated.

Local verification: 125 website checks, 24 umbrella tests and 54 website
application tests pass.
The documentation/status build completes and writes 19 prerendered files; it
logs a sandbox WebSocket bind warning and the tests log existing server-render
warnings. Rendered navigation, fragments and local assets resolve. The workspace
checker reports the five locally edited components as dirty; it is not a green
workspace acceptance result. Component publication and gitlink updates remain
separate work.

## Consolidation prepared locally

The owner clarified that consolidation means a smaller current specification set,
not preserving or relocating an old backlog. The patch now uses the existing
umbrella roadmap and product specification instead of adding delivery registers
or a separate Catalyst implementation document.

| Material | Final disposition |
| --- | --- |
| Feature 008 product, release and task narratives | Product behavior/implementation direction in Catalyst's existing specification and binding design; shared acceptance in the umbrella roadmap. Feature 008 retains experiment specification, plan, tasks and quickstart. |
| Four-pathway reporting and retired Catalyst roadmaps | Removed competing plans and retired stubs. Retained FP IDs route to existing product owners or the umbrella roadmap. |
| Catalyst comparison and future conversation | Scenarios and reader methodology remain harness-owned; undecided product conversation scope stays explicitly undecided in Catalyst. |
| OpenMRS parity roadmap/status | Removed obsolete active bodies. Current stack/release coordination is in the umbrella roadmap; detailed past acceptance remains accessible by immutable commit links. G03–G22 retain substantive scope; old G01/G02 hash/branch procedures are not permanent requirements. |
| Provider contract and interface reference | Our shared integration requirements and adapter reference are in umbrella `docs/openmrs-provider-interface.md`. OpenMRS backend/frontend/QueryStore documentation stays unchanged; their existing API contracts remain authoritative. |
| Hub source/cache requirements | Hub README owns current QueryStore caching and explicitly deferred prefix/generic-source direction. Harness retains measurement protocols, not an implementation roadmap. |
| Completed context-slice consolidation plan | Removed; QueryStore ADR Decisions 17–18 and current adapters supersede its caller-side interpretation plan. |
| Answer/In-Depth and cache research plans | Retained only current experiment methods and evidence limits. Removed obsolete PR/phase directions and false claims that validators do not exist. |
| Old status index | Dated evidence, with owner links. It no longer serves as a competing current task list. Generated views updated from JSON. |
| Frozen Catalyst design handoff | Retained design/CI evidence; removed the duplicate implementation sequence and obsolete harness-delivery instructions. |
| Verification tooling | Removed exact-prose/obsolete-authority assertions; retained meaningful fixture, schema and link checks. No permanent tests were added for this cleanup or PR state. |

Material conflict for review: the old OpenMRS plan bans final-answer/disk caching
while also requiring preservation of bundled behavior. The current bundled router
contains an optional answer cache and the existing engine has its own cache
contract. This patch preserves that product behavior and scopes the Hub's cache
restrictions to Hub. A broader cache-policy change is a separate product decision.

Product runtime source, fixture bytes and product behavior are unchanged. Modified
code is limited to documentation checking and inventory rendering. Documentation
commits are published for review and pinned by the umbrella; no deployment occurred.

## Review and publication decisions

1. Review the consolidated ownership and focused website patch locally.
2. Publish component documentation through its owning repository, then update
   reachable umbrella pins and their contract links. New cross-repository links
   currently describe the local patch; they are not claimed available on `main`.
3. Publish the maintained documentation destination and verify it before updating
   live navigation away from the legacy harness documentation.
4. Investigate the two report-catalog provenance mismatches before changing their
   scientific summaries. A simpler catalog presentation remains optional.

The broader application release signoffs, website deployment and catalog-data
correction are not claimed complete by this documentation patch.

## Final local verification

The full harness run produced 1,009 passes and 95 sandbox-related failures; all
95 failed cases passed when rerun with permission for their local fixture servers.
Thirty-eight tests were skipped and three deselected. The focused documentation
and renderer tests, shared-fixture/evidence checks and 24 umbrella tests pass.
The website rebuild succeeds; rendered navigation/assets resolve. The remaining
workspace-check failures are exactly the five intentionally edited components.
These are documentation/runner checks, not a new product-runtime acceptance run.

Removed the explicitly superseded model-gateway and standalone knowledge-service
briefs, their duplicate scope document and obsolete planning archive. Historical
research references point to immutable source versions. No new service or backlog
was created to preserve those proposals. Current Markdown file links pass across the maintained harness documents
and changed product documents. Remote publication and anchor checks are distinct
from those local file checks.

Removed the eight June lane documents after comparing their requirements with
current code and Feature 006. Hub's current context-source interface and README
supersede the proposed MCP service; Feature 006 owns clinical smoke, review and
shared report semantics; the umbrella owns the completed OpenMRS stacks. Old
worktree/branch launch instructions and speculative report redesign were removed.
The report keeps its native 0–10 scale: the old percentage proposal conflicted
with Feature 006 and was never resolved. No scoring or report behavior changed.
Historical citations now use immutable Git links; obsolete lane entries were
removed from the current artifact/roadmap inventory.

The final sweep also removed obsolete picker, staged-answer, bridge, team-design
and website-consolidation plans. Current frontend state/provider behavior and
umbrella publication contracts supersede them. The harness artifact index now
links to the umbrella's visual documentation instead of listing missing canvases.
The umbrella provider reference was checked against registry, transport and
frontend code; it now uses real source paths and correctly distinguishes disabled
Hub providers from enabled-but-unavailable providers.

Retained literature surveys and dated run/handoff records are research/evidence,
not implementation instructions. Their original experiment claims do not establish
current product behavior. The LM Studio research no longer carries a false
Hub-only product claim or an obsolete picker/configuration plan.

## Completion review against the requested scope

| Requested result | Evidence and disposition |
| --- | --- |
| Move retained Catalyst/OpenMRS requirements, update consumers and remove duplicates | Existing umbrella roadmap, Catalyst specification/design, umbrella provider integration reference and Hub README; existing OpenMRS module docs remain unchanged own current responsibilities. Feature 008 and conformance/cache protocols retain experiments only. Old plans are removed; source JSON and generated views are consistent; product runtime files and fixture/schema bytes are unchanged. |
| Audit specs, documentation and live website | Source inventory, reviewed ownership map, D01–D10/W01–W05 findings and dated live DOM/screenshots above. Additional obsolete lane/product/website plans removed in the final sweep. Publication gaps and catalog provenance issues remain explicitly flagged, not silently declared fixed. |
| Review technical and non-technical reader journeys | Five persona journeys above, live homepage/product/setup/contribution/report routes, desktop and mobile observations. Local contribution/reporting patch screenshots confirm layout/navigation. This is an editorial/interaction review, not recruited-user or full accessibility testing. |
| Submit verifiable remediation | Consolidated local patch, owner/disposition table, focused website changes and four concrete review/publication decisions above. Review can compare source diffs and the saved local screenshots. No release or scientific-result correction is implied. |

The requested audit, local ownership consolidation and proposal are complete.
Next is owner review and merging of the linked PRs; website deployment remains a
separate step. The two report-catalog mismatches
need provenance investigation before a correction; changing report layout remains
an optional separate decision.

## PR review scope correction

The owner clarified that our integration specifications and coordination material
must stay in the umbrella, including when an OpenMRS module participates in the
integration. The proposed backend/frontend documentation PRs were withdrawn;
no changes to the existing upstream feature PRs were made. The umbrella owns
`docs/openmrs-provider-interface.md` and shared acceptance. Native module setup
and API documentation remains unchanged. Review publication comprises the
umbrella plus its Catalyst, Hub and harness documentation companions.

Review companions: [Catalyst #140](https://github.com/DIGI-UW/catalyst-ai/pull/140),
[Hub #32](https://github.com/pmanko/med-agent-hub/pull/32), and
[harness #198](https://github.com/pmanko/clinical-ai-validation-harness/pull/198).
The umbrella PR is the entry point for the complete change. The rejected OpenMRS
fork documentation PRs are closed and excluded; upstream feature PRs are unchanged.
