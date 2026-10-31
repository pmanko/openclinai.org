# WA Health Summary (WAHS) condensation, reconciliation and privacy

Patient-mediated clinical summarization, cross-clinic FHIR R4 reconciliation, selective-disclosure privacy segmentation, and citation-grounded Q&A developed in collaboration with UW CIRG and the Washington State Department of Health.

## Architecture and boundaries

- **Med Agent Hub (`targets/med-agent-hub`):** Owns the 5-Tier Progressive FHIR R4 / US Core / IPS Chart Condenser (`server/fhir/condenser.py`), the 4-Layer Deterministic Clinical Knowledge Base (`server/kb_data/`), on-demand full-chart retrieval tools, `sd-fhir` selective-disclosure bundle export, and WAHS model/team execution profiles.
- **Validation Harness (`targets/validation-harness`):** Owns the offline and HTTP WAHS evaluation runner (`harness/wahs/evaluator.py`), weighted patient-centered rubrics, atomic claim/citation entailment scoring, and run manifests.
- **Umbrella (`openclinai.org`):** Owns the public project overview ([`landing/wahs/index.html`](../landing/wahs/index.html)), detailed technical design dashboard ([`landing/wahs/design-report/index.html`](../landing/wahs/design-report/index.html)), interactive prototype (`landing/wahs/demo/` deployed to `https://wahs-demo.openclinai.org/`), and curated validation reports (`reports/2026-10-30-wahs-phase2-eval/` deployed to `https://reports.openclinai.org/`).

## Target path

### Phase 2 foundation (completed 30 October 2026)

- [x] **W1 · 5-Tier Progressive FHIR R4 / IPS Condenser:** Condenses longitudinal FHIR R4 bundles (`1.6 MB` to `18.8 MB`, up to `3.52M` raw tokens) into strict `16k`, `8k`, `4k`, `2k`, and `1k` token budgets while retaining 100% of the IPS safety core and `[N] -> resourceUuid` provenance ([med-agent-hub#54](https://github.com/pmanko/med-agent-hub/pull/54)).
- [x] **W2 · Multi-Source Perturbation Fixtures & 4-Layer Clinical KB:** Deterministic Set A / Set B synthetic cohort (`Byron202_Emard19`, `Lamar193_Beer512`, `Maurice742_Auer97`), 15 cross-clinic anomalies, and SNOMED CT / RxNorm / CDC ACIP / LOINC + 42 CFR Part 2 & WA MHMDA normalizers ([med-agent-hub#55](https://github.com/pmanko/med-agent-hub/pull/55), [med-agent-hub#56](https://github.com/pmanko/med-agent-hub/pull/56)).
- [x] **W3 · Phase 2 Evaluation Runner, Interactive Prototype & Public Pages:** Initial 32-case rubric runner ([validation-harness#205](https://github.com/pmanko/clinical-ai-validation-harness/pull/205)), interactive walkthrough at `https://wahs-demo.openclinai.org/`, project pages at `https://openclinai.org/wahs/` and `https://openclinai.org/wahs/design-report/`, and Phase 2 report with plain-English metric definitions and candid methodological audit at `https://reports.openclinai.org/2026-10-30-wahs-phase2-eval/index.html` ([med-agent-hub#57](https://github.com/pmanko/med-agent-hub/pull/57), [openclinai.org#33](https://github.com/pmanko/openclinai.org/pull/33)).

### Phase 3 active local slices

- [ ] **W4 · Slice 1 — Evaluation Methodology, Atomic Entailment & Report Revamp:** Align `harness.wahs` scorer keys (`abstained` + redaction notice check), upgrade `wahs_eval_cases.jsonl` to HealthBench-style weighted patient-centered rubrics, add VeriFact/MiniCheck atomic claim entailment verification against cited FHIR resources, and revamp the published report on `reports.openclinai.org` to separate deterministic condensation/rule verification from live local-LLM generation.
- [ ] **W5 · Slice 2 — Patient-Centered Scenario Taxonomy & Interactive Demo Upgrade (`wahs-demo.openclinai.org`):** Reframe default scenarios and questions around primary patient needs (*medication clarity, lab trends, hospital stay summary, next-visit checklist, school vaccine readiness, safe sharing*), add a persistent **Patient View (Plain English) ↔ Clinician View (Codes & Rules)** toggle, add a Step 3 live preview of `sd-fhir` (`sd-hash`) selective disclosure, and surface Step 4 hybrid chart lookups.
- [ ] **W6 · Slice 3 — Pragmatic Messy Synthetic Personas & De-Identified Real Clinical Summaries:** Expand the cohort with additional patient personas plus a lightweight messiness pass (~25% stripped standard codes to raw `code.text` + free-text note vs. `MedicationRequest.status` contradictions) alongside 2 de-identified real clinical summary fixtures (MIMIC-IV-on-FHIR / SMART Sandbox).
- [ ] **W7 · Slice 4 — Hybrid Full-Chart Queryability & Condensation-Level Ablation (`Tier 0 -> Tier 4`):** Implement on-demand read-only FHIR retrieval tools (`search_chart_entries`, `get_lab_history`, `read_clinical_note`) over Tier 0/1 overflow records so the full chart remains queryable when condensed to `1k–4k` tokens, and evaluate recall across condensation tiers and question horizons.
- [ ] **W8 · Slice 5 — Local Model Selection Funnel, Prompt Engineering & Orchestrated KB Agent Teams:** Screen local open-weight models (`1B–4B` edge to `8B–31B` on the 64 GB Mac `llama-router`) and run controlled ablations comparing single-pass prompting, deterministic 4-Layer KB pre-attachment, cross-family label-only review (`single-12b-xcheck`), and parallel specialist KB agent teams (`team-wahs-kb`).
- [ ] **W9 · Slice 6 — Cryptographic FHIR Selective Disclosure (`sd-fhir` SD-JWT `sd-hash` + SHL JWE):** Implement element- and `Bundle.entry[]`-level salted SHA-256 digest obfuscation (`http://smart.who.int/icvp/Extension/sd-hash` + companion `fhirR4.Parameters` disclosures following `DIGI-UW/ips-selective-disclosures`) and JWE encryption (`uwcirg/shl-ips`) in the WAHS exporter.

### Deferred external-infrastructure & partner tracks

- [ ] **W10 · Deferred — CIRG 4-VM Shared GPU Server Benchmarking (`uwcirg/llm-configs`):** Once CIRG 4-VM shared H200 MIG access is provisioned next week, configure LiteLLM + Ollama/vLLM (`num_ctx: 16384`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `turn_off_message_logging: true`) and re-run the Slice 4–5 model and condensation matrices under shared multi-tenant load.
- [ ] **W11 · Deferred — Evaluation on Partner-Supplied Real WAHS Summaries:** Run the validated pipeline on de-identified partner test summaries once supplied by the WAHS / CIRG team.
