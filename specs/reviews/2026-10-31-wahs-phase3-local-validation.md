# Washington Health Summary (WAHS+) Phase 3 Local Validation & Refinement Record (`W4`–`W8`, `W12`–`W13`)

**Date:** 2026-10-31  
**Umbrella Branch / PR:** `wahs/phase2-eval-and-demo` ([openclinai.org#33](https://github.com/pmanko/openclinai.org/pull/33))  
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
