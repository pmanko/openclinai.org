# WAHS Engine Architectural & Functional Audit (19 November 2026)

Public page: [`landing/wahs/engine-audit/index.html`](../../landing/wahs/engine-audit/index.html) (`https://openclinai.org/wahs/engine-audit/`).

## Audited revisions and test verification

- **`pmanko/wahs-engine` `main` (`85fb799987ddc3ff5ce89d701f4f468d9921483d`):**
  - Production footprint: `8,893` LOC in pure-stdlib `src/wahs_core/` (`extractors.py`, `clinical_graph.py`, `condenser.py`, `temporal_digest.py`, `normalizers.py`, `wahs_tools.py`, `kb_lookup.py`, `kb.py`, `chart_serializer.py`) + `2,115` lines across 5 offline clinical KB packs (`src/wahs_core/kb_data/`) + `4,392` LOC in FastAPI runtime `src/wahs_engine/` (`upstream.py`, `assembler.py`, `seeder.py`, `config.py`, `app.py`, `tokenizers_registry.py`, `jwt_claims.py`, `schemas.py`).
  - Test execution: `81 passed, 2 skipped` (`101.88s`).
- **`pmanko/wahs-engine` open PR #10 (`s6/seed-all-12-demo-profiles` @ `193cf1a`):**
  - Delta over `main`: `+1,820 / -80` lines across `src/wahs_engine/` and `tests/` (`0` lines modified in `src/wahs_core/`), adding 12-persona HAPI star-graph seeding + Keycloak 26 user sync, `parse_wahs_profile_spec` (4 pathways + `@<budget>` suffixes), 96-character SSE lookahead streaming (`x_wahs_stream`), and single-flight cold dataset fetch coalescing.
  - Test execution: `86 passed, 2 skipped` (`103.75s`).
- **Companion repository state:**
  - `pmanko/shl-ips`: `main` `@ 63d183d` (PR #1 merged), open PR #2 (`17e4fc9`).
  - `pmanko/wahs-mobile-frontend`: `main` `@ f536318` (PR #1 merged), open PR #2 (`d70a827`).
  - `pmanko/med-agent-hub`: `main` `@ 532913d` (pins `wahs-engine` at `85fb799`).
  - `pmanko/clinical-ai-validation-harness`: `main` `@ 59ad40a` (unified `wahs` runner after PR #218), open PR #219 (`ee01bca`).

## Summary of key findings

1. **Empirical performance & safety:** Across the 14 November 900-cell H200 `16k vs. 32k` calibration ([`reports/2026-11-14-wahs-engine-post-fix-16k-vs-32k-calibration/`](../../reports/2026-11-14-wahs-engine-post-fix-16k-vs-32k-calibration/index.html)) and the 16 November 900-cell 4-pathway sheet benchmark (`run_id=3da9c15f`, commit `a3bad4a9d5` sharing exact `85fb799` `wahs_core`), `Gemma 4 26B + Condensation & 4-Layer KB @ 16k` achieved `85.1/100` (`84.1` safety-adjusted, `0/75` confirmed harms, `3.42s` median `p50`), while `2k` agentic tool-calling concentrated `24/37` (`64.9%`) of confirmed unsafe cells and `28/30` (`93.3%`) of over-abstentions. Token budget compliance passed `900/900` (`100%`), inline `[N]` UUID resolution reached `898/900` (`99.78%`), and third-party privacy leakage was `0/900`.
2. **Pre-merge blockers on `wahs-engine` PR #10 (`E1`, `E2`, `E3`):**
   - **E1 (`assembler.py:737, 894-933, 1034`):** Single-flight `_inflight_datasets` captures Request 1's request-local `httpx.AsyncClient` inside `asyncio.shield(task)`, closing the client under concurrent Request 2 if Request 1 disconnects or times out.
   - **E2 (`config.py:72-79, 238-251`, `upstream.py:462`):** Unbounded `@<budget>` suffixes lift `context_window = req_b * 2` and pass arbitrary `"num_ctx"` values southbound to Ollama/LiteLLM.
   - **E3 (`assembler.py:920-944`):** `effective_refresh=True` omits `_dataset_cache.put()`, leaving stale entries in `_dataset_cache` after in-place HAPI resource edits.
3. **High-priority `wahs_core` & runtime hardening (`C1`-`C6`, `E4`-`E6`):**
   - **C1 & C2:** `extractors.py` classifies `Medication*`/`Procedure`/`CarePlan`/`Goal` sensitivity on `(code, display)` without `reasons`/`source_org`/`notes`, allowing `wahs_tools.search_chart_entries` to leak sensitive items under `external_share`; direct `wahs_tools`/`temporal_digest`/`clinical_graph` calls fail open on unknown `sharing_posture` strings; lexical sensitivity packs omit uncoded MOUD, HIV antiretroviral, and WA MHMDA medications.
   - **C3 & C4:** `entered-in-error`/`refuted`/`not-done` statuses on `AllergyIntolerance`, `Procedure`, panel child `Observation`s, `DocumentReference`, `Immunization`, and `Appointment` remain rendered as clinical or planned events; `DiagnosticReport.conclusion` and list-valued `MedicationStatement.dosage` are dropped.
   - **C5 & C6:** `_DOSE_NOISE` salt stripping corrupts potassium/sodium/calcium supplements; trailing spaces in `note_resume_or_continue_cues` miss clause-final resume statements; high HbA1c triggers a false hypoglycemia contraindication edge.
   - **E4, E5 & E6:** `jwt_claims.py` performs no local RS256 verification (relying on `fhir-auth`); `clean_model_text()` returns unclosed `<think>` blocks verbatim when `finish_reason == "length"`; `stream=True` commits HTTP 200 headers before `prepare_upstream_messages()` validation.
