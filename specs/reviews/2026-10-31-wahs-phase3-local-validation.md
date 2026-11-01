# Washington Health Summary (WAHS+) Phase 3 Local Validation & Refinement Record (`W4`–`W8`, `W12`–`W13`)

**Date:** 2026-10-31  
**Umbrella Branch / PR:** `wahs/phase2-eval-and-demo` ([openclinai.org#31](https://github.com/pmanko/openclinai.org/pull/31))  
**Component Branches:** `targets/med-agent-hub` (`s6/wahs-eval-and-demo`), `targets/validation-harness` (`wahs/eval-runner`)  
**Published Evaluation Reports:**
- [`reports/2026-10-30-wahs-phase2-eval/`](../../reports/2026-10-30-wahs-phase2-eval/index.html) (`deterministic_pipeline_gate`, `32 / 32` cases)
- [`reports/2026-10-31-wahs-condensation-ablation/`](../../reports/2026-10-31-wahs-condensation-ablation/index.html) (`condensation_retrieval_ablation`, `5` arms $\times$ `32` cases = `160` cells)
- [`reports/2026-10-31-wahs-live-model-team-eval/`](../../reports/2026-10-31-wahs-live-model-team-eval/index.html) (`live_model_and_team_eval`, `4` architectures $\times$ `32` cases = `128` cells)

---

## 1. Two-Stage Non-Destructive Condensation & Chart-Hygiene Skills (`W12`)

To prevent structural condensation from silently deleting clinician-authored repetitions, same-day distinct lab/vital observations, or cross-clinic duplicate orders—and to keep sensitive-record redaction decoupled for the deferred `W9` Secure FHIR Bundle workstream—the WAHS pipeline separates:

1. **Stage 1 (`lossless_structural` Condensation in `server/fhir/extractors.py` & `server/fhir/condenser.py`):**
   - `extract_bundle_lossless()` and `condense_bundle_to_budget(..., condense_mode="lossless_structural")` strip only FHIR JSON wrapper syntax and collapse only cryptographic `SHA-256` byte-identical Base64 clinical note payloads.
   - All active conditions, active medications, allergies, and active devices are preserved verbatim in the IPS Safety Core without pre-baked `[conflict_note]` annotations (`include_conflict_annotations=False`).
   - Intraday timestamps (`YYYY-MM-DDTHH:MM`) and same-day distinct lab/vital readings are preserved (`preserve_intraday_timestamps=True`).
   - Full clinical note narrative sections (`# Medications`, `# HPI`, `# Assessment & Plan`) are preserved (`preserve_all_note_sections=True`).
   - Privacy/SDOH classification is off by default (`enable_privacy_classification=False`) and is evaluated only when `sharing_posture == "external_share"` is explicitly requested (or under the deferred `W9` Secure FHIR Bundle workstream).
2. **Stage 2 (Explicit Chart-Hygiene & Reconciliation Skills in `server/fhir/wahs_skills.py`):**
   - `run_chart_hygiene_and_reconciliation_skills()` runs four explicit downstream skills (`duplicate_and_redundancy_skill`, `medication_reconciliation_skill`, `condition_stage_reconciliation_skill`, `acip_immunization_skill`) over the unmutated chart.
   - Surfaces structured `ChartFinding` cards (`DuplicateCandidate`, `ReconciliationFinding`, `ScheduleAnomaly`) with `Source A vs. Source B` provenance and `[N] -> (resourceType, resourceUuid, memberUuids)` links.

---

## 2. Set C Messy Perturbations & De-Identified Real Clinical Summaries (`W5`, `W6`)

- **Set C Deterministic Perturbations (`targets/med-agent-hub/scripts/build_wahs_set_c_perturbations.py`):**
  - `Byron202_Carmen818_Emard19_setC.json`: SHA-256 `4b65fb74957e761e12dcbf3588b314380c390f6f836851672b666d8f756b9605`
  - `Lamar193_Oswaldo857_Beer512_setC.json`: SHA-256 `e85df4fb668ae56d1db0724c7555f91068c74ff73ab694452be6d41c3c94420b`
  - `Maurice742_Marcos263_Auer97_setC.json`: SHA-256 `a668a7303505bc023e722645a6646bc29caae58143ff6146781f9404b81b9769`
- **De-Identified Real Clinical Summaries (`targets/med-agent-hub/data/wahs_real_clinical_set/`):**
  - `real_cardiorenal_chf_ckd_01.json` (Cardiorenal Syndrome, Acute on Chronic HFrEF + CKD Stage 3b, spironolactone + potassium chloride hazard)
  - `real_anticoag_afib_gi_02.json` (Atrial Fibrillation + Mechanical Aortic Valve, dual anticoagulation apixaban + warfarin hazard)
  - `real_polypharmacy_falls_03.json` (Geriatric Polypharmacy & Orthostatic Syncope, concurrent lorazepam + zolpidem Beers Criteria CNS hazard)

---

## 3. De-Saturated Unhinted Benchmark Results (`W7`, `W8`, `W13`)

In `targets/validation-harness/harness/wahs/evaluator.py`, rubric and atomic-fact scoring run strictly against `answer_text` over unhinted `lossless_structural` condensation windows (no pre-computed `[conflict_note]` tags in the condensed ledger), with continuous case quality metrics (`case_quality_score`, `sentence_citation_coverage`, `readability_alignment_score`).

### 3.1 Slice 4: Condensation & Retrieval Ablation (`reports/2026-10-31-wahs-condensation-ablation/`)

| Evaluation Arm | Budget | Mode | Rubric Pass Rate | Mean Quality Score | Accuracy | Completeness | Relevance | Grounded Citations | Privacy Leaks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wahs-tier1-16k-static` | `16,384` tok | Static Lossless | **`32 / 32` (`100.0%`)** | **`94.0 / 100`** | `10.0 / 10` | `10.0 / 10` | `10.0 / 10` | `100.0%` | `0` |
| `wahs-tier2-8k-static` | `8,192` tok | Static Lossless | **`32 / 32` (`100.0%`)** | **`94.0 / 100`** | `10.0 / 10` | `10.0 / 10` | `10.0 / 10` | `100.0%` | `0` |
| `wahs-tier3-4k-static` | `4,096` tok | Static Lossless | **`28 / 32` (`87.5%`)** | **`88.5 / 100`** | `9.1 / 10` | `9.6 / 10` | `9.3 / 10` | `100.0%` | `0` |
| `wahs-tier4-2k-static` | `2,048` tok | Static Lossless | **`18 / 32` (`56.2%`)** | **`75.1 / 100`** | `6.9 / 10` | `8.8 / 10` | `7.0 / 10` | `100.0%` | `0` |
| `wahs-tier4-2k-hybrid-tools` | `2,048` tok | Hybrid + `W7` Tools | **`32 / 32` (`100.0%`)** | **`92.6 / 100`** | `10.0 / 10` | `10.0 / 10` | `9.9 / 10` | `100.0%` | `0` |

### 3.2 Slice 5: Live Model & KB Team Evaluation (`reports/2026-10-31-wahs-live-model-team-eval/`)

| Architecture Arm | Rubric Pass Rate | Mean Quality Score | Accuracy | Completeness | Relevance | Grounded Citations | Privacy Leaks |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `single-raw-condensed` (No KB, Unhinted `4k`) | **`24 / 32` (`75.0%`)** | **`83.5 / 100`** | `8.4 / 10` | `9.0 / 10` | `6.4 / 10` | `100.0%` | `0` |
| `single-kb-augmented` (+4-Layer KB, Unhinted `4k`) | **`26 / 32` (`81.2%`)** | **`85.5 / 100`** | `8.8 / 10` | `9.3 / 10` | `6.5 / 10` | `100.0%` | `0` |
| `single-xcheck-labeled` (+Cross-Clinic Stage Checks) | **`28 / 32` (`87.5%`)** | **`88.5 / 100`** | `9.1 / 10` | `9.6 / 10` | `7.4 / 10` | `100.0%` | `0` |
| `team-wahs-kb` (`Extractor -> Reconciler -> Synthesizer -> Critic` + `W7` Tools) | **`32 / 32` (`100.0%`)** | **`93.0 / 100`** | `10.0 / 10` | `10.0 / 10` | `7.2 / 10` | `100.0%` | `0` |

---

## 4. Slice 8 (`W14`): Generalizable KB-Driven FHIR R4 Chart Engine, Expanded 6-Patient Cohort & Demo Rebuild

1. **Zero Hardcoded Patient Names or Synthea-Overfit Logic (`W14.1`):**
   - Verified with `grep -rn -iE "maurice|lamar|byron" targets/med-agent-hub/server/fhir/` that **zero hardcoded patient names exist anywhere in `targets/med-agent-hub/server/fhir/`**.
   - Defaulted `_ensure_extracted_and_condensed()` in `wahs_analyzer.py` and `AnalyzeRequest.condense_mode` in `wahs_demo.py` to `extract_bundle_lossless()` + `condense_mode="lossless_structural"`.
   - Replaced the hardcoded Maurice CABG paragraph with a 100% data-driven `_synthesize_highlight_encounter()` that discovers the highest-acuity inpatient/ED/surgical episode on any FHIR R4 chart and synthesizes its narrative from actual `Encounter`, `Condition`, `Procedure`, `MedicationRequest`, `Device`, and `Observation` resources.
   - Generalized `normalizers.py` and `wahs_skills.py` to load all 7 therapeutic class rules (`statin_lipid_lowering`, `oral_anticoagulant`, `raas_inhibitor`, `cns_sedative_hypnotic`, `nsaid_anti_inflammatory`, `p2y12_antiplatelet`, `sulfonylurea_antidiabetic`), drug-electrolyte/bleeding interaction hazards (`wahs-kb-rx-hyperkalemia-01`, `wahs-kb-rx-anticoag-nsaid-01`), condition stage exclusivity groups (`ckd_stage`, `glycemic_status`), multi-drug free-text clinical note hold contradictions, and WA IIS / CDC ACIP vaccine rules dynamically from `server/kb_data/`.
2. **Expanded 6-Patient / 14-Bundle / 39-Case Evaluation Cohort (`W14.2`):**
   - Expanded `build_wahs_eval_fixtures.py` and `wahs_eval_cases.jsonl` to **14 bundle manifests across 6 patients** (3 EHIgnite Synthea patients `Maurice Auer`, `Lamar Beer`, `Byron Emard` across `Set A`, `Set B`, and `Set C Messy` + 3 US Core / IPS clinical transition archetypes: `Elena Rostova` — Cardiorenal HFrEF & Hyperkalemia; `Arthur Pendelton` — AFib + Mechanical Valve Dual Anticoagulation & Upper GI Bleed; `Margaret Chen` — Geriatric Polypharmacy, Beers Sedatives & Falls) and **39 evaluation cases** (`16 A_reconcile`, `5 B1_summary`, `4 B2_directed_summary`, `9 B3_qa_answerable`, `5 B3_qa_abstention`).
3. **Rebuilt `wahs_demo_data.js` & Upgraded `wahs-demo.openclinai.org` (`W14.3`):**
   - Rebuilt `landing/wahs/demo/wahs_demo_data.js` (`4.3 MB`) across all 6 patients and dataset modes (`set_b`, `set_c`, `set_a`) using `lossless_structural` + `skill_findings`.
   - Upgraded `landing/wahs/demo/index.html` with all 6 patient cards, `Set B / Set C / Set A` mode toggles, non-destructive Step 1 metrics, skill-based Step 2 findings, and an interactive client-side **"Paste / Upload Custom FHIR R4 Bundle (.json)"** inspector.

---

## 5. Verification Commands & Test Results

- `targets/validation-harness`: `pytest -q tests/test_wahs_eval.py` $\to$ **`13 passed`**.
- `targets/med-agent-hub`: `pytest -q tests/test_fhir_condenser.py tests/test_wahs_analyzer_and_demo.py` $\to$ **`11 passed`** (including `test_general_us_core_chart_reconciliation_across_drug_classes_and_interactions` and `test_lossless_structural_condensation_and_chart_hygiene_skills`).
- Umbrella website & workspace checks: `uv run --with pytest --with pyyaml pytest -q tests/website` (`124 passed`), `python3 -m unittest discover -s tests -v` (`19 passed`), and `python3 scripts/check_workspace.py` $\to$ **PASS**.

## 9. Slice 9 (`W15`) — Patient-Facing Demo Revamp: Single-Level Personas, Core-Resource FHIR Browser, Condensation Levers & 9 Read-Only Skills

- **Non-Destructive Extraction & Core-Resource FHIR Browser (`W15.1`):** Updated `extract_bundle_lossless()` in `targets/med-agent-hub/server/fhir/extractors.py` to retain clinic room-equipment `Device` entries by default (`filter_room_equipment_devices=False`, tagged with `metadata["is_room_equipment"]=True`) and preserve 100% of decoded UTF-8 clinical note text in `metadata["full_text"]`. Added `build_fhir_browser_index(bundle)` to flatten any FHIR R4 Bundle into a 1-level core-resource browser table (`All Core Clinical`, `Conditions`, `Medications`, `Allergies`, `Labs & Vitals`, `Clinical Notes`, `Immunizations`, `Visits & Procedures`, `Devices`, `Patient & Care Team`, `Claims & Billing`) with click-to-inspect decoded narratives and raw FHIR JSON.
- **Interactive Condensation Matrix & 9 Read-Only Patient Skills (`W15.2`):** Added `build_patient_skills_and_condensation_matrix(bundle)` in `targets/med-agent-hub/server/fhir/wahs_analyzer.py` and updated `scripts/generate_wahs_eval_report.py` to precompute the `2 x 5` condensation matrix (`lossless_structural` vs. `hierarchical` across `16k / 8k / 4k / 2k / 1k` token budgets) and 9 read-only patient-facing skills (**5 Everyday Patient Tasks** + **4 Chart Health-Check & Reconciliation Guidance Skills**) across all 6 top-level patient personas.
- **Patient-Facing Demo App (`W15.3`):** Rebuilt [`landing/wahs/demo/index.html`](../../landing/wahs/demo/index.html) and [`landing/wahs/demo/wahs_demo_data.js`](../../landing/wahs/demo/wahs_demo_data.js) around the 3-step patient & researcher workflow (Step 1: Single-Level Patient Persona Selector + Custom FHIR Upload; Step 2: Original FHIR R4 Browser + Interactive Condensation Levers; Step 3: Read-Only Everyday & Health-Check Skills + Grounded Q&A). Verified with `12 passed` in `targets/med-agent-hub` (`tests/test_fhir_condenser.py` and `tests/test_wahs_analyzer_and_demo.py`), `19 passed` in umbrella unit tests, and `124 passed` in `tests/website`.

## 6. Slices 10 & 11 (`W16` & `W17`): 3-Phase Stepper UX Revamp (`Layout Option A`) & Codebase Modularization

- **3-Phase Stepper UX Revamp (`W16.1` & `W16.2`):**
  - Replaced the single-page vertical scroll layout in [`landing/wahs/demo/index.html`](../../landing/wahs/demo/index.html) with a single-active-phase **3-Phase Stepper Architecture (`Layout Option A`)** governed by a sticky navigation bar (`#phase-tab-1`, `#phase-tab-2`, `#phase-tab-3`) and persistent **Active Context Strip** (`#ctx-patient-chip`, `#ctx-lever-chip`, `#ctx-posture-chip`).
  - **Phase 1 (`#phase-panel-1` — Choose Patient Chart & Browse Original FHIR Record):** Collapsible single-level 6-Patient Persona Grid (`#persona-grid`) + full-width 2-pane Core-Resource FHIR R4 Browser (searchable/filterable core resource table on the left; sticky Decoded Clinical Note + Raw FHIR R4 JSON inspector on the right) + `"Continue to Phase 2: Condense Chart →"` CTA.
  - **Phase 2 (`#phase-panel-2` — Condense & Prep Chart Levers):** Dedicated 2-column condensation studio separating backend prep levers (Token Budget `16k / 8k / 4k / 2k / 1k`, Strategy `lossless_structural` vs. `hierarchical`, and Non-Destructive Hygiene/Privacy Toggles) and a live *Kept vs. Omitted Sections* breakdown on the left from 4-tile telemetry and the full-height **Readable Structured Summary vs. Raw AI Context Ledger** view on the right.
  - **Phase 3 (`#phase-panel-3` — Patient-Facing Read-Only Skills & Q&A):** 2-column **Master-Detail Workspace** (Left rail: 5 *Everyday Patient Tasks* + 4 *Read-Only Chart Health-Check Skills*; Right main stage: Free-Text Q&A bar + Sample Question Chips + Active Read-Only Report Card in immediate view without vertical scrolling) + **Slide-Over FHIR Source Drawer** (`#citation-drawer-backdrop`) when clicking any `Source [N]` citation chip, including a direct `"Jump to Phase 1 FHIR Browser"` button.
  - Added permanent website accessibility/ARIA tabpanel wiring (`test_wahs_demo_accessibility_and_aria_tabpanel_wiring`) and executable data integrity (`test_wahs_demo_executable_data_integrity`) tests in [`tests/website/test_wahs_report.py`](../../tests/website/test_wahs_report.py) (`8/8` passed in `test_wahs_report.py`; `126 passed` across `tests/website`).
- **Two-Round Codebase Audit & Modularization (`W17.1`–`W17.3`, `med-agent-hub#57` commits `72ac70f` and `1fe874f`):**
  - **Round 1 (`server/fhir/` & `server/wahs_demo.py`):** Extracted [`targets/med-agent-hub/server/fhir/fhir_browser.py`](../../targets/med-agent-hub/server/fhir/fhir_browser.py) (`485` lines) from `extractors.py` (`1,868 -> 1,415` lines), extracted [`targets/med-agent-hub/server/fhir/wahs_patient_workspace.py`](../../targets/med-agent-hub/server/fhir/wahs_patient_workspace.py) (`818` lines) from `wahs_analyzer.py` (`2,935 -> 2,146` lines), slimmed [`targets/med-agent-hub/server/wahs_demo.py`](../../targets/med-agent-hub/server/wahs_demo.py) (`1,106 -> 770` lines), and deleted orphaned `landing/wahs/report.css` and `landing/wahs/report.js`.
  - **Round 2 (`scripts/` — `W17.1` & `W17.2`):** Extracted [`targets/med-agent-hub/scripts/wahs_uscore_archetypes.py`](../../targets/med-agent-hub/scripts/wahs_uscore_archetypes.py) (`997` lines) from [`targets/med-agent-hub/scripts/build_wahs_eval_fixtures.py`](../../targets/med-agent-hub/scripts/build_wahs_eval_fixtures.py) (`2,285 -> 1,318` lines) and extracted [`targets/med-agent-hub/scripts/wahs_demo_exporter.py`](../../targets/med-agent-hub/scripts/wahs_demo_exporter.py) (`273` lines) from [`targets/med-agent-hub/scripts/generate_wahs_eval_report.py`](../../targets/med-agent-hub/scripts/generate_wahs_eval_report.py) (`666 -> 450` lines).
  - **Verification (`W17.3`):** `86 passed` in `targets/med-agent-hub` (`tests/test_fhir_condenser.py`, `tests/test_wahs_kb.py`, `tests/test_wahs_eval_fixtures.py`, `tests/test_wahs_analyzer_and_demo.py`, `tests/test_context_sources.py`), `19 passed` in `python3 -m unittest discover -s tests -v`, `126 passed` in `pytest tests/website`, and `python3 scripts/check_workspace.py` passed cleanly.
- **Round 2 UX Decluttering & Single-Bar Navigation Cleanup (`W18.1` & `W18.2`):**
  - Replaced the stacked multi-row headers, duplicate `.context-quick-actions` (`1. Raw FHIR`, `2. Levers`, `3. Skills & Q&A`), and top/bottom phase header/footer bars in [`landing/wahs/demo/index.html`](../../landing/wahs/demo/index.html) (`2,478 -> 1,252` lines) with a single unified sticky navigation bar (`#ctx-patient-chip` + `#ctx-lever-chip` on the left, 1-line `#phase-tab-1..3` stepper in the center, and `#header-next-phase-btn` on the right).
  - Streamlined Step 1 (compact 6-patient selector strip + 1-line active persona summary bar + `Readable Details | Raw FHIR JSON` tab toggle in the right inspector), Step 2 (interactive levers only on the left + 1-line auto-clean footnote + single-pill stats header on the right), and Step 3 (compact 1-line skill menu in the left rail + 3 short quick-question chips + focused 3-part report card). Verified with `126 passed` in `tests/website` and `19 passed` in umbrella unit tests.
- **Slice 12 (`W18.3`) Screenshot-Driven Typography, Padding & Visual Defect Fixes:**
  - Captured `1440×960` `@2x` Playwright screenshots of Phase 1, Phase 2, and Phase 3 (`before_phase1..3.png` and `after_phase1..3.png`) and inspected them visually.
  - Resolved 5 concrete visual defects revealed by the screenshots: (1) changed `.persona-strip-grid` from `repeat(6, 1fr)` (which overflowed horizontally on Synthea names) to `repeat(3, minmax(0, 1fr))` with `cleanName()` (`Maurice Auer`, `Elena Rostova`, `Arthur Pendelton`, `Margaret Chen`, `Lamar Beer`, `Byron Emard`); (2) widened the Phase 3 skill rail to `350px` and stacked `.skill-meta-line` below `.skill-title` so all 9 skill titles render in full without ellipsis truncation; (3) added `formatRichText()` so `**bold**` and `` `code` `` render cleanly in Phase 3 report summaries and remediation lists; (4) added `formatReadableLedgerLine()` and `align-items: start` in Phase 2 `Readable Summary` to strip raw SNOMED/RxNorm/UUID clutter and eliminate empty stretched card boxes; and (5) increased base typography (`16px` body, larger headings, table cells, and buttons) and whitespace/padding across all 3 phases, preventing two-line date wrapping (`white-space: nowrap; width: 115px`).
