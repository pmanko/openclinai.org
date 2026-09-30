# First Feature005 cleanup: preparation inventory

**Status:** Preparation only, at pinned source `a27d7e51b7268653420e8f91306c9aaa4ab5a8ee`. **Deletion readiness:** eligible in substance, **not ready for an isolated file deletion**; reconcile the named consumers and resolve gate 3 first. No unique current requirement was found in Feature005 that needs a new specification.

Authority: [umbrella roadmap](roadmap.md#validation-only-harness-boundary-and-spec-disposition) and [umbrella instructions](../AGENTS.md). This first documentation slice does not require completion of all U0 or authorize U1 runtime work. Preparation does not execute harness deletion or grant release acceptance.

## Source and governance boundary

All harness-relative paths below resolve under [`targets/validation-harness/`](https://github.com/pmanko/clinical-ai-validation-harness/tree/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee), never a sibling checkout. Implementation uses the local `spec/005-current-contract-cleanup` harness branch, starting at the umbrella's recorded pin; `origin/main` supplied the published baseline. Products remain at the harness's exact gitlinks. `git submodule status --recursive` reports those revisions; this inventory is not a second pin catalog.

Read [harness AGENTS](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/AGENTS.md), [constitution](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/.specify/memory/constitution.md), harness `CLAUDE.md`, and applicable product guidance: [ChartSearchAI CLAUDE](https://github.com/pmanko/openmrs-module-chartsearchai/blob/2b020dd268fa526c7fa0e168a0a1a8bbc1e6761c/CLAUDE.md) and [QueryStore CLAUDE](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/CLAUDE.md). No nested AGENTS applies under umbrella `specs/` or harness `specs/`/`site/`; no Hub/ESM instruction file was found. ChartSearchAI's reference-subsystem instructions apply before future changes there, not to this inventory-only preparation.

Actual branch rule: harness `AGENTS.md:104–121` requires a short-lived harness branch/PR, `--allow-harness-branch` for repository-line checks during the PR, strict checks after merge, and separate publication checks. It does **not** prescribe a particular cleanup branch name. Upstream OpenMRS products retain exact fork `harness-integration` heads; do not change their branches/pins for documentation cleanup. Bootstrap establishes the matching umbrella/harness cleanup branches; products remain at their recorded revisions. Constitution `:139–156` requires PR governance for amendments; its broader control-plane wording at `:98–115` is not implicitly amended by umbrella prose and need not be rewritten for this slice.

These are **source observations**, not fresh remote checks, passing CI, deployed identity or acceptance. Dual-provider status `:20–52` explicitly separates older live evidence from source candidates and contains pins different from this checkout. No deployment was inspected or changed.

## Removal and consolidation map

Primary removal candidate: [`specs/005-med-agent-hub-bridge/spec.md`](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/005-med-agent-hub-bridge/spec.md), the only file in that feature directory.

| Feature005 lines | Disposition and maintained owner |
| --- | --- |
| 1–18, 28–54 | Delete the old bridge/status/provenance narrative, fixed model/topology assumptions and endpoint-override selection description. Do not transfer implementation history into another spec. |
| 20–26, 30–32, 55–59 | Current API/profile responsibilities already belong to [Hub README](https://github.com/pmanko/med-agent-hub/blob/6120c313856a40700367afe07452e546c9bff8fd/README.md):14–58,94–107 and [ChartSearchAI README](https://github.com/pmanko/openmrs-module-chartsearchai/blob/2b020dd268fa526c7fa0e168a0a1a8bbc1e6761c/README.md):9–27. Hub product profiles own the schema; low-level legs retain caller-controlled response formats. Do not preserve unconditional forwarding/fallback claims as product requirements. |
| 38–44 | Current knowledge-source/evidence behavior belongs to Hub README:60–82; [ESM README](https://github.com/pmanko/openmrs-esm-chartsearchai/blob/77f61c8a1f9afcf7eb03208caac3dd7ae8ea35a2/README.md):17–31 owns reference rendering. Do not transfer the old chart-only citation carve-out or promote F009's service proposal. |
| 45–50, 61–72 | Current provider choice/lifecycle is covered by the [conformance contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md):28–99 and [dual-provider roadmap](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-parity-roadmap.md):16–39,91–120. Validation scenarios/provenance belong to [Feature006](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/006-validation-harness-mvp/spec.md):24–48, not 005. Old deferred gateway/MCP/A2A work is not silently revived. |

Read the dual-provider status amendments at `:661–741` and publication rule at `:10–11,54–57`; the upstream inventory is a dated keep/port/exclude record, not today's pin list. QueryStore's [ADR](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/adr.md):1370–1488 owns shared selection and interpretation; engines retain prompt/token policy and Hub remains source-neutral. **Preserve bundled as fresh-install default, explicit Hub selection and no silent fallback. No bundled/runtime/configuration changes are part of this cleanup.**

Feature005 has no `FR-005.*`/`SC-005.*` IDs in this pinned file. References to such IDs in the old gateway brief do not justify inventing requirements or recreating absent `plan.md`/`tasks.md`. Preserve IDs of any genuinely current requirement encountered during execution in its existing owner.

## Bounded inbound audit and required consumer work

Search covered harness source documentation, instructions, `.specify`, `.claude`, `.cursor`, scripts/tests, `.github`, site/landing, umbrella specs, and tracked text in the four relevant product submodules. Searched the path, feature-number/ID variants and named old-plan dependencies; excluded generated builds, dependencies, runtime artifacts and bulk datasets. This is a Feature005 audit, not the full U0 audit.

| Exact harness-relative source/lines | First-slice action or boundary |
| --- | --- |
| `specs/roadmap.canvas.tsx:306–326` | Remove/consolidate the obsolete F005 card into current provider/Hub ownership; do not move the whole canvas in this slice. It is explicitly published. |
| Same canvas `:158,338–347,408,440,524,537,558–560,603–604,616,1143` | Reconcile references, dependency arrays, status/lane rows and obsolete gateway sequencing together; avoid dangling F005 graph nodes. Resolve active-looking MCP lane claims against current Hub, not the old feature number. |
| `specs/artifacts/project-status/efforts.json:159–184` (`sources` at `:179`) | Point the current `clinical.hub` effort directly at the existing Hub contract. Preserve the effort ID and dated evidence; do not refresh deployment claims without proof. |
| Status `sources.json:261–274`, `roadmaps.json:274–285`, `artifacts.json:695–706` | Reconcile/remove the obsolete maintained spec-catalog entries and current existence claims; do not create replacement historical-spec rows. Existing `CLIN-A22` is an inventory identifier, not a product requirement ID. |
| Status `efforts.md:15`, `roadmaps.md:31`, `artifacts.md:59`; `exports/efforts.csv:6`, `roadmaps.csv:22`, `artifacts.csv:50` | Generated consumers: edit JSON then regenerate, not hand-edit. `site/status/model.ts:1–24` imports these JSON sources; maintenance rules are `maintenance.md:38–61`. Leave dated reports/reviews and commit-bound evidence intact. |
| `specs/artifacts/planning/chartsearchai-model-gateway-brief.md:8,20–24,111,181–184,274,282` | Remove/reconcile obsolete 005 dependencies and nonexistent contract citations. It is not active Feature008 Catalyst delivery. Do not authorize its gateway proposal. Whole-file disposition is a separate owner-reviewed cleanup candidate. |
| Planning `clinical-kb-brief.md:37,168`, `clinical-kb-research.md:397` | Replace 005-as-future-consumer references with current Hub knowledge-source ownership where still relevant; discard obsolete product-planning claims, not the underlying research evidence. |
| Planning `archive/README.md:11`, `archive/med-agent-team-poc-roadmap.md:27,29,33` | Existing old-spec copies/index are removal candidates, not an archive destination. For any still-maintained consumer, remove its live-source dependency. Dated `archive/kb-roadmap-sync-2026-05-31.md:22,38,69–75` and `archive/landscape-and-sync-2026-05-30.md:49,118,126,147` are evidence, not deletion blockers or current requirements. |

No direct 005 source dependency was found in harness README/WORKSPACE, agent pointers, `.specify`, scripts/tests, CI, landing source, or tracked relevant product text. Feature006 currently depends on the relay/profiles (`spec.md:11`), not 005, but its hub-only transport wording at `:3–6,25,36` needs separate reconciliation; do not bundle a Feature006 policy rewrite.

**Auto-discovery is bounded by publication selection:** [`site/nav-auto.ts`](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/site/nav-auto.ts):24–62 expands supplied keys, not all repository files. `site/App.tsx:9,19–23` and `prerender-entry.tsx:19,34–40` supply `published-content.ts:5–27`: 005 Markdown is excluded, while `specs/roadmap.canvas.tsx` is included at `:19`. `nav.ts:1–15,37–80` has no 005 route. `nav.test.ts:25–36` and `topics.test.ts:6–18` discover files for assertions; `nav-auto.test.ts:15–41` uses synthetic keys. No need to widen discovery, add a redirect stub, or edit nav-auto for this deletion. The status dashboard remains an indirect consumer. Source publication selection does not establish what is currently deployed.

**Old-plan deletions must remain separate:** 005 points to bridge delta, ReAct design, A2A research and the old PoC (`spec.md:14–18`), and incorrectly treats consolidation as current (`:3–5`). Candidate follow-up deletions/consolidations require their own requirement audit. In particular, `scripts/verify_dual_provider_parity_gates.py:361–401` requires both consolidation plan/status files and a marker; `scripts/verify-hub-consolidation-gates.sh:18–19` reads them; `scripts/verify-doc-drift.sh:48–65,114–123` permits/requires old marked artifacts; `tests/test_hub_consolidation_gate_script.py:62–79` binds the legacy matrix/wrapper. Do not delete those files or weaken gates to make the first slice pass. Reconcile their obsolete specification content with their consumers in a separate slice; a script's historical immutability rule is not a reason to retain obsolete specs indefinitely. No banners or archives are a cleanup outcome.

## Numbered gates and owner questions

1. **Recovery — verified for 005.** Git object `a27d7e51b7268653420e8f91306c9aaa4ab5a8ee:specs/005-med-agent-hub-bridge/spec.md` exists; `git ls-tree` identifies blob `0b8333cb6a9f618b58142c93b7213ea4423108cf`; `git show` bytes equal the checkout. No unique uncommitted 005 content exists. Recheck against the execution baseline before removal. Git history is sufficient; no spec copy/archive/stub is needed.
2. **Scope/branch — parent.** Confirm a documentation-only harness PR covering 005 and its direct consumers. Keep products, gitlinks, runtime, old gate machinery and publication out. Full U0 completion, product staging and release acceptance are not prerequisites for this first slice.
3. **Genuine owner question — canvas disposition.** Which gateway/MCP dependency claims, if any, remain current intended work? `roadmap.canvas.tsx:338–347,392–409,431–443,603–604` presents active-looking work that conflicts with Hub README:178's retired MCP/A2A boundary. Umbrella owner plus Hub owner must choose removal versus a direct link to an already-approved current owner. Do not infer that planned MCP work is authorized, or migrate the old plans. This is the remaining substantive ambiguity; core provider/profile/schema ownership is already established.
4. **Consumer closure — harness/site maintainer.** Reconcile the named canvas/catalog/brief consumers with no obsolete requirement retention; regenerate status views. Keep immutable dated evidence unchanged. Re-run the bounded search and check any newly exposed dependency before deleting 005. A raw `rm` without this closure is not ready.
5. **Verification and publication — executor.** Run the focused checks below and review a doc/consumer-only diff. Source checks do not establish CI/merge/deployment acceptance. No deploy/reseed/model/benchmark run is needed for this documentation slice.

## Concrete checks for the later slice

From the **umbrella root**, scripts verified in [`site/package.json`](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/site/package.json):6–15:

```sh
npm --prefix targets/validation-harness/site test -- nav-auto.test.ts nav.test.ts topics.test.ts landing-content.test.ts prerender-entry.test.ts
npm --prefix targets/validation-harness/site run status:test
npm --prefix targets/validation-harness/site test
npm --prefix targets/validation-harness/site run build:pages
```

After JSON edits, run `scripts/project-status.sh refresh` from `targets/validation-harness`; it regenerates views and runs `status:test`/`status:build` (`scripts/project-status.sh:48–58`). It writes generated consumers, so it was **not run during this inventory-only preparation**. Dependencies must first be installed through the parent-approved workflow; `site/node_modules` is absent here. These commands are proposed checks, not recorded passes.

For recovery, from `targets/validation-harness`:

```sh
git --no-pager cat-file -e a27d7e51b7268653420e8f91306c9aaa4ab5a8ee:specs/005-med-agent-hub-bridge/spec.md
git --no-pager show a27d7e51b7268653420e8f91306c9aaa4ab5a8ee:specs/005-med-agent-hub-bridge/spec.md
```

This inventory establishes source/reference coverage and Git recovery for the first slice, not a passing site build or executed deletion. Bootstrap publishes the umbrella and prepares branches separately; no harness/product change or runtime acceptance is claimed. Other cleanup families (004/007 and broader status migration) remain roadmap-owned follow-ups, not bundled into this first slice.
