# Report Display vs. Content Separation, Payload Bloat, and Publication Architecture Remediation

**Date:** 2026-11-09  
**Scope:** `clinical-ai-validation-harness` (`harness/validate/report.py`) · `openclinai.org` (`reports/`, `scripts/reshell-reports.py`, `scripts/build-reports-index.py`, `scripts/deploy-reports.sh`)

---

## 1. Executive Summary & Root-Cause Audit

On 9 November 2026, an end-to-end audit of `https://reports.openclinai.org/` and all 33 staged report directories under `reports/` identified four structural failure modes caused by tightly coupling **report presentation (`_STYLE` + `_SCRIPT` + HTML shell)** to **report content (`#report-data` JSON)** inside monolithic static `reports/<slug>/index.html` files and deploying them from parallel git worktrees:

| Failure Mode | Observed Symptom on `reports.openclinai.org` | Root Cause |
| :--- | :--- | :--- |
| **F1. Frozen Legacy UI on Published Reports** | 31 of 32 published reports (including all WAHS and MacBook runs) rendered without the 5-Tab Casual-First UI or 3-Layer Verification Banner (`5-tab=False`, `vtiers=False`). | `build_report()` bakes `_STYLE` (CSS) and `_SCRIPT` (JS) directly into each `reports/<slug>/index.html` at creation time. Subsequent upgrades to `harness/validate/report.py` never propagate to already-published reports unless they are re-shelled. |
| **F2. 18.5 MB Payload Bloat on Multi-Arm WAHS Reports** | `2026-11-05-wahs-multi-family-3-pathway-eval/index.html` (`27 setups × 36 turns = 972 cells`) was **18,537.7 KB (18.5 MB)**; `2026-11-03` was **4.45 MB**; `2026-11-02` was **3.24 MB**. | Inside `run.scenarios` (**15.1 MB**), every cell stored **both** `cell.sources` (**6.5 MB** of raw structured JSON repeating full patient chart snippets across all 27 setups) **and** `cell.sources_html` (**6.0 MB** of pre-rendered HTML cards for the exact same citations), even though the client JS only reads `cell.sources.diagnostics` (3 integer ref counts) and `cell.sources_html`. |
| **F3. Multi-Second Main-Thread Freeze on Boot** | Opening `2026-11-05-wahs-multi-family-3-pathway-eval` blocked the browser main thread while constructing **50,000+ DOM nodes** before first paint. | `renderRun()` synchronously iterated over all 972 cells and injected 6.0 MB of `cell.sources_html` + `cell.refs_html` into live DOM nodes on page load—even when the user starts on **Tab 1 (`Overview`)** (`#sec-answers` hidden) and `.compact-tiles` hides `.sources` (`display: none`). |
| **F4. Parallel Worktree `rsync --delete` Collisions** | Running `scripts/deploy-reports.sh` from a feature worktree lacking sibling branches' `reports/<slug>/` directories wiped WAHS reports from `reports.openclinai.org`. | Multiple active git worktrees had direct SSH access to run `rsync -az --delete` against `34.59.0.158:openclinai.org/artifacts/reports/` without checking remote or sibling-worktree report manifests. |
| **F5. CSS Table Collision & Domain-Hardcoded Overview Copy** | On `2026-11-05-wahs-multi-family-3-pathway-eval/index.html`, the `Head-to-Head Comparison` table rows (`<tr class="exec-row">`) were squished into CSS grids inside the first column, the 9-model × 3-pathway study takeaway (`run.context.text`) was hidden, `Layer 1` showed `0/0 refs resolved`, and `3 · Response Speed` showed `— avg total wait`. | `.exec-row { display: grid }` overrode `<tr class="exec-row">` table rows; `renderExecutiveSummary()` hardcoded ChartSearchAI HIV copy (`"10 synthetic HIV patient charts"`, `"OpenMRS chart UUIDs"`) and assumed non-zero latency instead of adapting declaratively to the run's data capabilities (`judge[b].citation_resolution`, `run.context`, `safety_adjusted_benchmark_score`). |

---

## 2. Why We Had 4 Separate Report Formats (and How We Eliminate Per-Type Migration Forever)

### 2.1 Inventory of the 33 Staged Report Directories in `reports/`

| Format / Generator | Count | Example Slugs | Data Representation | Current Status |
| :--- | :---: | :--- | :--- | :--- |
| **1. Unified `validate` Schema (`harness/validate/report.py`)** | **28** | All 21 ChartSearchAI runs (`2026-07-*` to `2026-11-07-*`) + 7 WAHS / MacBook runs (`2026-11-02` to `2026-11-06`, including `2026-11-05-wahs-multi-family-3-pathway-eval` & `2026-11-04-wahs-macbook-direct-vs-hub-multi-scenario-eval`) | `<script id="report-data">` containing `runs[0].{meta, context, summary, scenarios, judge, judge_rows, adjudication_rows, calibrated}` | **Unified & Live Now** (all 28 share `../assets/report-shell.{css,js}`) |
| **2. Early Bespoke WAHS Runs (`Oct 30–31`)** | **3** | `2026-10-30-wahs-phase2-eval`, `2026-10-31-wahs-condensation-ablation`, `2026-10-31-wahs-live-model-team-eval` | Converted from `results.jsonl` + `inputs/wahs_eval_cases.jsonl` + `meta.json` into canonical `runs[0]` `#report-data` (`96`, `160`, and `128` cells) | **Unified & Live Now** (all 3 share `../assets/report-shell.{css,js}`) |
| **3. Catalyst Suite Runs (`catalyst-*`)** | **2** | `catalyst-phase1-comparison`, `catalyst-notebook-t094-2026-07-22` | `<script id="report-data">` enriched with canonical `runs[0]` (`36` and `5` SQL cells) alongside `{report_family: "catalyst", manifest, suite, results, judges}` | **Unified & Live Now** (both share `../assets/report-shell.{css,js}`) |
| **4. Catalog-Only Unavailable Entry** | **1** | `catalyst-t094-release` | No `index.html` (`availability: "unavailable"`) | Handled by catalog index |

### 2.2 The Architectural Rule: Capability-Driven Rendering Over One Canonical Data Contract

To guarantee we **never** maintain separate report templates or manually migrate report types (`ChartSearchAI`, `WAHS`, `MacBook Direct vs. Hub`, `Catalyst`, `WHO SMART`) again, the report architecture enforces two strict boundaries:

1. **One Canonical Data Envelope (`report-data.json` / `#report-data`) Across Every Eval Family:**
   - Every evaluation family emits the same top-level `runs[]` structure:
     - `meta`: `{run_id, timestamp, git_sha, suite, domain_label, models, pathways, ...}`
     - `context`: `{text, url, label}` (study description, methodology takeaway, external sheet/spec link)
     - `summary[backend]`: `{total_turns, valid_turns, resolved_chart_refs, unresolved_chart_refs, temporal_gate_pass, avg_latency_ms, p50_latency_ms, p95_latency_ms, ...}`
     - `judge[backend]`: `{benchmark_score, safety_adjusted_benchmark_score, citation_resolution, criteria, safety_flags: {critical_omission, severe_harm, unsupported_claim, ...}}`
     - `calibrated[backend]`: `{theta_hat, ci_low, ci_high, n_human, n_total, method}`
     - `scenarios[]`: `[{id, title, category, patient, question, cells: {backend: {answer_md, status, latency_ms, source_refs, judge_verdict, human_verdict, domain_artifacts}}}]`
2. **One Capability-Driven Presentation Shell (`/assets/report-shell.{css,js}`):**
   - The UI shell never branches on `if (family === 'wahs')` or hardcodes domain prose (`"synthetic HIV patient charts"`). Instead, it inspects **data capabilities** present in `run` and renders components declaratively:

| Data Capability Detected in `run` | What the Shared UI Shell Renders Automatically |
| :--- | :--- |
| `run.context && run.context.text` | Renders the **Study Takeaway & Experimental Context** callout banner at the top of `Overview` with optional deep-link pill (`run.context.url`). |
| `hasLatency` (`any summary[b].avg_latency_ms > 0`) | Shows `Avg Wait (P50 / P95)` column in `Head-to-Head Comparison`, `3 · Response Speed` KPI card, and enables Tab 3 (`Speed & Multi-User Scaling`). When `false` (e.g. offline-judged WAHS sweeps), automatically replaces the blank speed card with `3 · Safety-Adjusted Score & Spread` + `Resolved Refs` (`5,112 / 5,112`). |
| `hasSafetyAdj` (`safety_adjusted_benchmark_score != null`) | Shows `Safety-Adj` column alongside raw `Quality Score` in `Head-to-Head Comparison` and `Safety-Adjusted Benchmark` delta cards in Layer 2. |
| `hasCitationResolution` (`summary.total_chart_refs > 0` or `judge[b].citation_resolution`) | Populates `Layer 1 · Deterministic Gate` (`972/972 valid · 5,112/5,112 refs resolved`) and `Citation Resolution` column in the leaderboard. |
| `hasHumanAdjudication` (`adjudication_rows.length > 0` or `calibrated[b].n_human > 0`) | Activates `Layer 3 · Human Adjudication & PPI` calibrated intervals and human override badges; otherwise displays `0 human ratings · Awaiting clinician sign-off`. |
| `classifyScenario(sc)` (`A01–A20`, `B01–B16`, `convo-*`, `date-*`, `single-*`, `sql-*`) | Groups scenarios into domain-appropriate clinical task categories (`Outpatient Longitudinal Scenarios (A01–A20)`, `Inpatient & Specialty Care (B01–B16)`, `Medication & Reconciliation`, `Privacy & Boundary Guardrails`, `Multi-Turn Clinical Reasoning`, etc.) without per-report configuration. |

---

## 3. Guiding Principles & Target Architecture

```mermaid
flowchart LR
    subgraph DataLayer["1. Canonical Content Layer (Schema-Versioned Data)"]
        Manifest["run_manifest.json + results.jsonl"]
        Judge["judge.jsonl + judges/*/judge.jsonl"]
        Human["adjudication.jsonl"]
        Blob["Canonical Run Blob (#report-data / report-data.json)\n• Slimmed cell.sources.diagnostics (no duplicate raw snippet arrays)\n• Deduplicated patient chart records\n• Enriched Layer 1 / Layer 2 / Layer 3 summaries"]
        Manifest & Judge & Human --> Blob
    end

    subgraph ViewLayer["2. Decoupled Presentation Layer (UI Shell)"]
        Shell["harness/validate/report.py (_document)\n• 5-Tab Casual-First Progressive Disclosure\n• 3-Layer Verification Banner & Tables\n• Two-Level Lazy DOM Rendering"]
        Reshell["scripts/reshell-reports.py\n(Upgrades all reports/*/index.html in <3s)"]
        SharedAssets["Phase 3 Target: Shared /assets/report-shell.{css,js}\n+ Split overview.json / cells.json"]
        Shell --> Reshell
        Shell -.-> SharedAssets
    end

    subgraph PublishLayer["3. Safe Publication Pipeline"]
        Validate["build-reports-index.py\n(Non-empty #report-data guard)"]
        Deploy["deploy-reports.sh\n(Remote + sibling-worktree superset guard;\ncanonical deploy from main)"]
    end

    Blob --> Reshell --> Validate --> Deploy
```

### Principle 1 — Strict Separation of Content (`#report-data` / `report-data.json`) from Presentation (`report.py` Shell)
- Evaluation runs persist canonical, schema-versioned **content** (`meta`, `summary`, `scenarios`, `judge`, `judge_rows`, `adjudication_rows`, `calibrated`, `arm_cards`).
- The **presentation shell** (`_STYLE` + `_SCRIPT` + HTML skeleton) is a stateless view over that data island. Any UI improvement in `harness/validate/report.py` must be propagatable across the entire historical archive in one deterministic pass (`scripts/reshell-reports.py`), and in Phase 3 via externalized versioned assets (`/assets/report-shell.v2.js`, `/assets/report-shell.v2.css`).

### Principle 2 — Store Facts Once, Render on Demand (Zero Payload Duplication)
- Never embed both multi-megabyte raw citation arrays (`cell.sources.sources`) and pre-rendered HTML (`cell.sources_html`) in the same published artifact.
- Deduplicate patient chart records at the run/patient level (`run.patient_records[patient_uuid]`) rather than repeating identical chart snippets across $M \text{ setups} \times K \text{ turns}$.

### Principle 3 — Sub-200ms First Paint via Progressive / Lazy DOM Construction
- Initial page boot in `Overview (At a Glance)` must only construct DOM nodes for visible overview/summary elements (~2,000–5,500 nodes).
- Scenario answer bands (`#sec-answers`) are constructed lazily when switching to `Browse All Questions` or `All Sections` (for runs with $>20$ cells).
- Per-tile evidence cards (`cell.sources_html` + `cell.refs_html`) are parsed into DOM nodes lazily only when a user clicks `expand`, `⛶` (fullscreen), or `Show evidence & audit tables` (for runs with $>60$ cells).

### Principle 4 — Single Canonical Publication Baseline (`main`) + Mechanical Superset Guards
- Feature branches and worktrees merge to `main` rather than diverging indefinitely.
- `scripts/build-reports-index.py` rejects any staged report whose `<script id="report-data">` has `0` scenarios or `0` backends.
- `scripts/deploy-reports.sh` verifies that local `reports/reports-index.json` is a strict superset of **both** the live remote host manifest over SSH **and** all local sibling git worktrees before `rsync` runs.

---

## 4. Phased Remediation Plan & Execution Status

### Phase 1 — Immediate Unification, Re-Shelling, Payload Slimming, Domain-Agnostic UX, & PR Consolidation (COMPLETED 2026-11-09)
- [x] **1.1 Unify 5-Tab Casual-First UI + 3-Layer Verification Revamp in `harness/validate/report.py`:**
  - Combined the 5-Tab progressive disclosure navigation (`Overview`, `Browse All Questions` + Slide-Over Answer Reader, `Speed & Multi-User Scaling`, `Methodology & Raw Data`, `All Sections`) with the 3-Layer Verification Banner (`Layer 1 · Deterministic Guardrails`, `Layer 2 · Advisory LLM Judge`, `Layer 3 · Human Adjudication & PPI`), `renderDeterministic`, `Safety-Adjusted Benchmark`, `renderAdjudication`, read-only `.tile-eval-footer`, and `#verdict-filter`.
- [x] **1.2 Add Two-Level Lazy DOM Construction in `harness/validate/report.py`:**
  - Deferred `#sec-answers` tile-band DOM construction until tab switch (`questions` / `all`) for runs with $>20$ cells.
  - Deferred per-tile `cell.sources_html` + `cell.refs_html` DOM injection until `expand` / `⛶` / `Show evidence & audit tables` for runs with $>60$ cells.
- [x] **1.3 Build `scripts/reshell-reports.py` and Re-Shell All 28 Validation Reports:**
  - Enriched historical `#report-data` blobs with `valid_turns`, `resolved_chart_refs`, `unresolved_chart_refs`, `temporal_gate_pass`, `benchmark_score`, `safety_adjusted_benchmark_score`, `critical_omission`, `severe_harm`, and `calibrated`.
  - Stripped duplicate `cell.sources.sources` arrays when `cell.sources_html` is present (preserving `cell.sources.diagnostics`), shrinking the archive from **49.56 MB to 40.88 MB** (`2026-11-05-wahs` shrunk from **18.54 MB to 12.61 MB**, initial DOM nodes reduced from **~50,000+ to 5,461**, local render time **192 ms**).
- [x] **1.4 Add Remote + Sibling-Worktree Superset Guard (`scripts/deploy-reports.sh`) & Non-Empty `#report-data` Guard (`scripts/build-reports-index.py`):**
  - Verified with 189 passing tests in `clinical-ai-validation-harness` and 132 passing tests in `openclinai.org/tests/website/`.
- [x] **1.5 Deploy All 32 Curated Runs (Including All 10 WAHS/MacBook Runs) Live to `https://reports.openclinai.org/`:**
  - Verified live via headless Chromium (`HTTP 200`, `tab=overview`, `vtiers=3`, `0` console/page errors).
- [x] **1.6 Merge Outstanding PRs into `main` Across All 3 Repositories:**
  - Merged `report-ux-revamp` $\to$ `main` in `pmanko/clinical-ai-validation-harness` (`16a36b3` / `ccf96bf`).
  - Merged PR `#58` (`answer-delta-streaming` $\to$ `main`) in `pmanko/med-agent-hub` (`4de6cf5`).
  - Merged PR `#34` (`audit_validation_harness_chartsearchai` $\to$ `main`) and `wahs/simple-profiles-and-eval` in `pmanko/openclinai.org` (`106216d` / `c53215e`).
- [x] **1.7 Fix `tr.exec-row` CSS Table Collision & Make `renderExecutiveSummary` / `renderVerificationTiers` Capability-Driven:**
  - Scoped `div.exec-row { display: grid }` so `<tr class="exec-row">` inside `<table class="ov-comp-table">` renders as proper table rows.
  - Surfaced `run.context.text` + `run.context.url` in `Overview`, fell back to `judge[b].citation_resolution` for Layer 1 (`5,112/5,112 refs resolved`), replaced blank `Response Speed` KPI card with `3 · Safety-Adjusted Score & Spread` + `Resolved Refs` when `avg_latency_ms == 0`, and generalized `classifyScenario()` for WAHS (`A01–A20`, `B01–B16`) and ChartSearchAI.

### Phase 2 — Unify the Remaining 5 Non-`validate` Reports & Client-Side Evidence Pool Reconstruction (COMPLETED 2026-11-09)
- [x] **2.1 Convert the 3 Early Static WAHS Reports (`2026-10-30-wahs-phase2-eval`, `2026-10-31-wahs-condensation-ablation`, `2026-10-31-wahs-live-model-team-eval`) to Canonical `#report-data` Blobs:**
  - Built `build_early_wahs_blob()` in `scripts/reshell-reports.py` reading their staged `results.jsonl`, `inputs/wahs_eval_cases.jsonl`, `meta.json`, and `run_manifest.json` (`96`, `160`, and `128` cells across all 32 WAHS cases).
- [x] **2.2 Deduplicate `source_card_pool` & `refs_pool` and Reconstruct Evidence Cards Client-Side:**
  - Added `resolveCellSourcesHtml(run, cell)` and `resolveCellRefsHtml(run, cell)` in `harness/validate/report.py`, deduplicated repeated `<article class='source-card'>` blocks into `run.source_card_pool` and `cell.refs_html` into `run.refs_pool`, and slimmed redundant `indepth_view` and `judge_passes` fields.
  - Shrunk `2026-11-05-wahs-multi-family-3-pathway-eval/index.html` from **18.54 MB $\to$ 4.67 MB (4,783 KB)** (a **75% reduction**) and the entire 33-report archive from **49.56 MB $\to$ 24.20 MB**!
- [x] **2.3 Normalize the 2 Catalyst Reports (`catalyst-phase1-comparison`, `catalyst-notebook-t094-2026-07-22`) into the Shared `runs[0]` Envelope:**
  - Built `enrich_catalyst_blob()` in `scripts/reshell-reports.py` mapping `{manifest, suite, results, judges}` into `runs[0].{meta, summary, judge, judge_rows, scenarios}` with `.sql-code` query blocks and gold execution-match assertions while keeping top-level Catalyst keys intact.

### Phase 3 — Externalized Shared Shell Assets (`reports.openclinai.org`) (COMPLETED 2026-11-09)
- [x] **3.1 Externalize Shared Versioned Report Shell (`reports/assets/report-shell.css`, `reports/assets/report-shell.js`):**
  - Updated `render_document()` (`harness/report_shell/document.py`) and `_document()` (`harness/validate/report.py`) to support `external_shell_prefix="../assets"` (while keeping inline `<style>`/`<script>` default for standalone `build_report()` runs).
  - All 33 staged reports in `reports/*/index.html` now load `../assets/report-shell.css` (`53.6 KB`) and `../assets/report-shell.js` (`148.1 KB`). Updating the shared shell assets updates every published report simultaneously without modifying individual report HTML files.

### Phase 4 — Additive Per-Slug Publishing on Feature Branches & Worktree Hygiene (COMPLETED 2026-11-09)
- [x] **4.1 Additive Per-Slug Rsync on Feature Branches (`scripts/publish-report.sh` & `scripts/deploy-reports.sh`):**
  - `scripts/deploy-reports.sh` now supports `--slug <slug>` (or `DEPLOY_SLUG`), scoping `rsync --delete` strictly to `artifacts/reports/<slug>/` while syncing `index.html`, `reports-index.json`, `sitemap.xml`, and `assets/` additively without root `--delete`.
  - `scripts/publish-report.sh` automatically invokes `deploy-reports.sh --slug "${SLUG}"` when executed on a non-`main`/`master` branch, and `deploy-reports.sh` refuses full-archive `rsync --delete` from feature branches unless `--slug <slug>` (or `ALLOW_BRANCH_FULL_DEPLOY=1`) is explicitly passed.
- [x] **4.2 Cross-Repository Worktree Hygiene (`hq/scripts/wt.sh audit` & `prune`):**
  - Pruned 14 broken `/private/tmp/*` worktree metadata entries (`clinical-ai-validation-harness`, `catalyst-dev`) and removed 17 clean merged/detached sibling worktrees across `openclinai.org`, `digging-in-research`, and `clinical-ai-validation-harness`.
  - Fast-forwarded `/Users/pmanko/.gemini/antigravity/worktrees/openclinai.org/organize_project_workstreams` to `main` so all active workspaces share the identical 33-report archive and Phase 1–4 publication guardrails.

### Phase 5 — Full 3-Layer Architectural Decoupling & 6-Invariant Scorecard (COMPLETED 2026-11-09)

To eliminate the remaining structural tangles between `clinical-ai-validation-harness` (producer) and `openclinai.org` (publisher/viewer), the report architecture enforces **6 measurable invariants** across three strict layers:

- [x] **Invariant 1 — Native Data Deduplication & Enrichment in Harness (`harness/validate/report_data.py`):**
  - `build_report()` in `clinical-ai-validation-harness` natively produces the deduplicated `source_card_pool` + `refs_pool` and Layer 1/2/3 summaries via `harness/validate/report_data.py`, and writes `run_dir / "report-data.json"` alongside `run_dir / "report.html"`.
  - Zero scripts in `openclinai.org/scripts/` import `from harness` or `import harness` (enforced by `tests/website/test_website_ownership.py`).
- [x] **Invariant 2 — First-Class CSS & JS Assets (`harness/report_shell/report-shell.{css,js}`):**
  - `_STYLE` and `_SCRIPT` are extracted out of `harness/validate/report.py` into real static files `harness/report_shell/report-shell.css` and `harness/report_shell/report-shell.js` (loaded by `harness/report_shell/assets.py` and mirrored to `openclinai.org/reports/assets/report-shell.{css,js}`), shrinking `harness/validate/report.py` from 249.4 KB (4,267 lines) to 51.0 KB (1,194 lines) of pure Python.
- [x] **Invariant 3 — Standalone `report-data.json` Separated from Display Shell in `openclinai.org/reports/<slug>/`:**
  - Every published report directory in `openclinai.org/reports/<slug>/` carries a standalone `report-data.json` file alongside `meta.json` and a pure **2.7 KB** `index.html` shell (`<script type='application/json' id='report-data' data-src='./report-data.json'></script>`, loading `../assets/report-shell.{css,js}?v=58cbaf97e1`). Total HTML across all 35 published reports is **0.09 MB** (down from 49.56 MB).
  - `report-shell.js` supports both inline `#report-data` and external `./report-data.json`.
  - `scripts/reshell-reports.py` is a pure, harness-free static shell updater that reads `reports/assets/report-shell.{css,js}` and `reports/<slug>/report-data.json` without importing `harness`.
- [x] **Invariant 4 — Single-Pass `publish-report.sh` & `stage-report.py`:**
  - Running `publish-report.sh` stages a report and automatically links `../assets/report-shell.{css,js}?v=<hash>` and writes `report-data.json` when `reports/assets/report-shell.js` is present, while preserving 100% compatibility with `tests/website/test_publish_report_contract.py` and `test_stage_report.py`.
- [x] **Invariant 5 — Catalog Builder (`build-reports-index.py`) Reads Canonical `meta.json` & `report-data.json`:**
  - `build-reports-index.py` validates archives against `report-data.json` (or `#report-data`) and reads frozen `meta.json` / `report-data.json` first without requiring raw `results.jsonl` to be parsed when `meta.json` is populated.
- [x] **Invariant 6 — Single Canonical `main` Baseline & Complete Published Catalog (35 Reports Live):**
  - Canonical `main` in both `clinical-ai-validation-harness` and `openclinai.org` holds 100% of commits, the 2 stranded published reports from `checked-answers` (`l5-full-default-2026-10-28-2a053c09` and `l5-answer-rules-fresh-2026-10-29-effa8855`) are restored and reshelled onto `main` (35 active report directories total), `deploy-reports.sh` checks local branches as well as worktrees, and live `https://reports.openclinai.org/` matches `origin/main` byte-for-byte.

