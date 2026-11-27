# WAHS Engine Architectural & Functional Audit (Verified Baseline · 25 November 2026)

Public page: [`landing/wahs/architecture/index.html`](../../landing/wahs/architecture/index.html) (`https://openclinai.org/wahs/architecture/`, consolidated from `/wahs/engine-audit/`).

## Audited and remediated revisions

- **`pmanko/wahs-engine` `main` (`808d16ace8898aeef9b72b5c20d3cd40fb949452`, via `PR #10`, `PR #11`, and `PR #12`):**
  - Production footprint: pure-stdlib `src/wahs_core/` (`extractors.py`, `clinical_graph.py`, `condenser.py`, `temporal_digest.py`, `normalizers.py`, `wahs_tools.py`, `kb_lookup.py`, `kb.py`, `chart_serializer.py`, verified under `python -S`) + 5 offline clinical KB packs (`src/wahs_core/kb_data/`) + FastAPI runtime `src/wahs_engine/` (`upstream.py`, `assembler.py`, `seeder.py`, `config.py`, `app.py`, `tokenizers_registry.py`, `jwt_claims.py`, `schemas.py`).
  - Test execution: `94 passed, 2 deselected` offline (`pytest -q -k "not live_hapi"`) + all 3 GitHub Actions jobs passing (`unit-and-contract`, `docker-smoke`, `live-hapi-jwt-proxy-integration`, `96/96` total tests).
- **Companion repository state (all clean and aligned on `main`):**
  - `pmanko/shl-ips`: `main` `@ cc119af` (`PR #2` and `PR #3` merged).
  - `pmanko/wahs-mobile-frontend`: `main` `@ a35ac01` (`PR #2` and `PR #3` merged).
  - `pmanko/med-agent-hub`: `main` `@ 532913d` (imports shared `wahs_core`; optional follow-up pin bump from `85fb799` to `808d16a`).
  - `pmanko/clinical-ai-validation-harness`: `main` `@ 08f40fc` (`PR #219` merged).

## Summary of verified baseline and empirical evidence

1. **Empirical performance & safety:** Across the 14 November 900-cell H200 `16k vs. 32k` calibration ([`reports/2026-11-14-wahs-engine-post-fix-16k-vs-32k-calibration/`](../../reports/2026-11-14-wahs-engine-post-fix-16k-vs-32k-calibration/index.html)) and the 16 November 900-cell 4-pathway sheet benchmark ([`reports/2026-11-16-wahs-engine-4pathway-sheet-eval/`](../../reports/2026-11-16-wahs-engine-4pathway-sheet-eval/index.html)), `Gemma 4 26B + Condensation & 4-Layer KB @ 16k` (`wahs-26b-kb`) achieved `85.1/100` (`84.1` safety-adjusted, `0/75` confirmed harms, `3.42s` median `p50`), with `Gemma 4 12B` (`82.0` to `82.8/100`) validated as the compact GPU alternative, while `2k` agentic tool-calling concentrated `24/37` (`64.9%`) of confirmed unsafe cells and `28/30` (`93.3%`) of over-abstentions. Token budget compliance passed `900/900` (`100%`), inline `[N]` UUID resolution reached `898/900` (`99.78%`), and third-party privacy leakage was `0/900`.
2. **Remediated `PR #10` runtime blockers (`E1`, `E2`, `E3`, `E10`):**
   - **E1 (`assembler.py`):** Replaced request-scoped `httpx.AsyncClient` capture inside single-flight `_inflight_datasets` with an app-lifespan shared client pool (`test_pr10_audit_remediations.py`).
   - **E2 (`config.py`, `upstream.py`):** Clamped `@<budget>` suffixes to `[512, 131072]` and model `context_window` ceilings.
   - **E3 (`assembler.py`):** Updated `effective_refresh=True` to write freshly fetched datasets back into `_dataset_cache`.
   - **E10 (`config.py`):** Preserved `cross_key`, `WAHS_DEFAULT_MODEL` suffixes, and `cl100k_base` tokenization for `wahs-qwen3-*`.
3. **Remediated `wahs_core` & `wahs_engine` baseline hardening (`C1`-`C10`, `E4`-`E9`, `E11` in `PR #12` @ `808d16a`):**
   - **C1 & C2:** Extraction-time and `wahs_tools._is_privacy_redacted()` full-text/reason/note/reference/org sensitivity scanning, fail-closed `validate_sharing_posture()`, and expanded MOUD, HIV ARV, and WA MHMDA lexical fallback rules.
   - **C3, C4 & C9:** Exclusion of `entered-in-error` allergies, meds, immunizations, procedures, notes, child panel labs, care plans, goals, and appointments; `mandatory=False` on `refuted` allergies; exclusion of `cancelled`/`noshow` appointments from upcoming care; extraction of `DiagnosticReport.conclusion` and list-valued `MedicationStatement.dosage[]` / `MedicationAdministration.dosage.dose`; and `RxNorm`/`SNOMED CT`/`LOINC`/`CVX` coding priority in `_coding_pair()`.
   - **C5, C6, C7, C8 & C10:** Electrolyte supplement preservation (*Potassium Citrate*, *Sodium Bicarbonate*, *Calcium Carbonate*), word-boundary note-cue matching, directional low-HbA1c hypoglycemia checks, unit-separated graph observation trajectories, mixed UTC + date-only multi-day trends, `on-hold` vs. `stopped` medication separation in `TemporalDigest`, NYHA `heart_failure_stage` conflict detection, and thread-safe per-index SQLite FTS5 locking.
   - **E4, E5, E6, E7, E8, E9 & E11:** Zero-dependency RFC 8017 RS256 JWKS verification + `urlsplit` `fhir-internal` guard + explicit `MasterPatient` ownership check; unclosed `<think>` stripping on length truncation; `start_stream()` preflight returning clean HTTP `400`/`422`/`502` before SSE headers commit; `wahs.emit_stream_events=false` for vanilla OpenAI SDKs; safe non-dict/non-int tool JSON handling; `asyncio.to_thread` worker offload + byte-bounded `_BoundedLRUCache`; Mode-A category scoping; OpenAI parameter forwarding (`top_p`, `stop`, `user`, penalties, `stream_options`); and aligned repo architecture docs (`test_pristine_baseline_remediations.py`).


## Follow-up: Pristine Slim Baseline & `wahs_extensions` Isolation (25 November 2026)

- **`pmanko/wahs-engine` `main` (`3b9dcc0f712a28bdcbd4458287f319e0f1764ddd`, `PR #13`):**
  - Slimmed default codebase from `17,325` LOC to a domain-neutral baseline: `src/wahs_core/` (`1,776` LOC pure Python stdlib verified under `python3 -S`; 3-tier verbatim-first condensation: `Tier 0` verbatim, `Tier 1` ontology-free RLE folding, `Tier 2` packed) + `src/wahs_engine/` (`1,871` LOC stateless OpenAI `/v1` proxy + `fhir-auth` bundle assembly, keeping E1/E3/E4/E5/E6/E9/E11 runtime hardenings).
  - Isolated reusable R&D enrichers (`note_rag`, `overflow_lookup`, `temporal_trends`, `experimental.clinical_reconciliation`) under `src/wahs_extensions/` behind `wahs_core.ports.ContextEnricher` (`WAHS_ENABLED_ENRICHERS=""` default, zero imports in standard baseline) and moved persona seeding to `src/wahs_devtools/seeder.py` (`wahs-seed-hapi`).
  - Removed premature privacy regex redactions (`sharing_posture`, `classify_sensitivity*`, Rule 5), heuristic note-hold splicing (`_HOLD_CLAUSE_RE`), `1k` `_build_ultra`, Synthea/MIMIC hacks, and multi-round LLM tool loops; patient selective disclosure stays unbuilt pending dedicated `W9` design.
- **Zero-Static-Prescription Remediation (`pmanko/wahs-engine` `PR #14` -> `666a9be`):**
  - Removed all hardcoded token sizes and static aspect targets from `wahs_core` and `wahs_engine`: `condense_bundle_to_budget(..., target_tokens: Optional[int] = None)` emits Tier 0 verbatim by default, Tier 1 runs uniform ontology-free RLE without per-section `keep_latest` quotas, and Tier 2 water-fills clinical notes continuously to remaining capacity (deleting `_NOTE_EXCERPT_HEAD_CHARS = 400` and `len(sec_items) <= 4`).
  - Replaced `chart_budget_ceiling = 16384` and pre-carved slice math in `assembler.py` with exact per-request measurement (`context_window - exact_turn_overhead`) plus budget-independent `_extracted_cache` and optional `WAHS_PREFERRED_CHART_TOKENS` (`None` default) strictly for `Auto` mode while honoring explicit caller `target_budget_tokens` un-clamped.
- **Lockstep Frontend Alignments:**
  - `pmanko/shl-ips`: `PR #4` (`f8d94a6`) + `PR #5` (`77e9f22`, `2k`–`64k` budget testing selector).
  - `pmanko/wahs-mobile-frontend`: `PR #4` (`08e660b`) + `PR #5` (`925dd95`, `2k`–`64k` budget pills).
  - `pmanko/med-agent-hub` remains pinned at `85fb799` intentionally for R&D benchmark continuity.
- **Public Documentation & Cloud Portal Sync (`W38`):**
  - Updated public `landing/wahs/*` pages and `wahs/cloud-gate/app.py` to present durable architecture, methods, boundaries, and standards/report links without internal commit SHAs, LOC counts, internal symbols, or ticket tables.
