# ChartSearchAI validation fidelity, streaming parity, and bundled attribution (3 November 2026)

Verification and root-cause record for `CHARTSEARCH-VALIDATION-2026-11` ([specs/chartsearch-validation.md](../chartsearch-validation.md)), pinning:
- Validation harness `e06c0f0` ([clinical-ai-validation-harness#207](https://github.com/pmanko/clinical-ai-validation-harness/pull/207))
- Med Agent Hub `83c700f` ([med-agent-hub#58](https://github.com/pmanko/med-agent-hub/pull/58))
- ChartSearchAI `a8eade4` ([openmrs-module-chartsearchai#629](https://github.com/openmrs/openmrs-module-chartsearchai/pull/629))

## 1. Component verification

- **Validation harness (`targets/validation-harness`):**
  - Added incremental SSE stream frame timestamping (`stream=True`, `iter_lines()`, `time.perf_counter_ns()`) in `harness/validate/client.py`, computing `stream_timings` (`ttft_ms`, `preliminary_start_ms`, `reasoning_start_ms`, `answer_delta_start_ms`, `answer_done_ms`, `answer_validation_ms`, `evidence_updated_ms`, `indepth_done_ms`, `turn_done_ms`, `delta_count`, `answer_delta_count`, `itl_p50_ms`, `itl_p95_ms`, `tpot_ms`) while keeping `collapse_turn_stream()` compatible with static text inputs.
  - Restored `tokens_in`, `tokens_out`, `cached_tokens`, and `cache_hit_ratio` extraction in `harness/validate/metrics.py` (`compute_metrics()`), including OpenAI/vLLM `usage.prompt_tokens_details.cached_tokens` and `llama-server` `timings.cache_n`.
  - Added configurable clinical session credentials (`CHARTSEARCH_USER`, `CHARTSEARCH_PASSWORD`) and session location (`CHARTSEARCH_LOCATION_UUID`) in `ChartSearchAiClient`.
  - Added general-purpose `OpenAICompatibleClient` (`transport="openai-compatible"`) in `harness/validate/client.py`, `harness/validate/models.py`, `harness/validate/execution.py`, `harness/validate/runner.py`, `harness/validate/concurrency.py`, and `harness/cli.py`, plus the unified multi-modality adapter registry in `harness/adapters/__init__.py` (`ChartSearchAiClient`, `MedAgentHubClient`, `OpenAICompatibleClient`, `NotebookHttpClient`, `WahsHubClient`).
  - Updated `scripts/engine-tap.py` with `--simulate-local-engine-dry` (`apply_local_engine_dry_policy()`, `has_reference_records()`, `extract_upstream_telemetry()`) to reproduce `LocalLlmEngine`'s out-of-the-box conditional DRY rule (`dry_multiplier: 0.8` when no drug-reference block is present in the user prompt; temperature-only when drug-reference records are present).
  - Added optional hardware target metadata (`VALIDATE_HARDWARE_TIER`, `VALIDATE_HARDWARE_GPU`, `VALIDATE_HARDWARE_VRAM_GB`, `VALIDATE_SERVING_ENGINE`, `VALIDATE_PARALLEL_SLOTS`, `VALIDATE_INFERENCE_ENDPOINT`) in `harness/validate/runner.py` (`write_run_meta()`, `resolve_hardware_metadata()`) and surfaced `hardware`, `streaming_latency` aggregates (`avg_ttft_ms`, `p95_ttft_ms`, `avg_answer_done_ms`, `p95_answer_done_ms`, `avg_turn_done_ms`, `avg_tpot_ms`, `avg_cached_tokens`), and per-cell `TTFT`, `answer`, and `TPOT` chips in `harness/validate/report.py` while keeping golden report parity (`evals/validate/test_report_golden.py`).
  - Added multi-clinician session concurrency runner `harness/validate/concurrency.py` (`run_concurrency_benchmark()`, `summarize_concurrency_rows()`) and CLI subcommand `harness-cli validate concurrency` in `harness/cli.py`, driving `N` concurrent sessions across distinct provisioned OpenMRS clinical accounts (`eval-doctor`, `eval-nurse`, `eval-pharmacy`, `eval-clerk`, `eval-lab`, `eval-researcher`, `admin`) or transport-matched API clients and computing `AIPerf`/`GuideLLM`-style **SLO goodput** (`goodput_turns`, `goodput_rate`, `goodput_turns_per_min`), `turn_1_ttft_p50_ms` vs. `turn_2plus_ttft_p50_ms`, and `cache_hit_ratio_avg`.
  - Test run: `uv --directory targets/validation-harness run pytest tests/ -q` — **598 passed in 58.89s** (`evals/validate/`: **180 passed**).
- **Website & Landing (`landing/`):**
  - Updated `landing/validation-harness/index.html` and `landing/chartsearchai/comparing-answer-paths/index.html` with the stage-aware OpenMRS SSE validation methodology, capability vs. sampler attribution, 4-tier OpenMRS hardware sizing matrix, and external benchmark alignment (`ArchEHR-QA`, `EHRNoteQA`, `HealthBench`, `MedHELM`, `NVIDIA AIPerf`, `GuideLLM`, `vllm bench serve`).
  - Test run: `uv run --no-project --with pytest --with pyyaml pytest tests/website/ -q` — **127 passed in 9.57s**.
- **Med Agent Hub (`targets/med-agent-hub`):**
  - Added `_AnswerJsonDeltaExtractor`, `_stream_chat_chunks()`, and `_synthesize_answer_stream()` in `server/team.py`, and wired live `answer_delta` SSE emission into `server/engine.py` (`stage == "answer"`) before `_ensure_substantive_answer`, `gate`, `resolve_refs`, and `answer_done`.
  - Added `_make_router_lock()` and `configure_router_concurrency()` in `server/team.py` reading `MED_AGENT_ROUTER_CONCURRENCY` (default `1` -> `asyncio.Lock()`, `> 1` -> `asyncio.BoundedSemaphore(N)`).
  - Test run: `uv run --no-project --with fastapi --with uvicorn --with httpx --with psutil --with python-dotenv --with pyyaml --with rfc8785 --with python-multipart --with pytest pytest -q` — **869 passed in 15.52s** (`tests/test_staged_stream.py` and `tests/test_query_role_transport.py`: **92 passed in 2.65s**).
- **ChartSearchAI (`targets/chartsearchai`, Hub relay only; `bundled` untouched):**
  - Updated `HubClinicalAnswerProvider` to advertise `ProviderCapability.TOKEN_STREAMING` and map `reasoning_delta` and `answer_delta` wire frames before `answer_done` onto `TurnEvent.delta(...)`.
  - Test run: `mvn -B -pl api -Dtest=HubClinicalAnswerProviderTest,TurnLifecycleConformanceTest,ProviderRegistryConformanceTest,HttpHubStreamTransportTest test` — **62 tests run, 0 failures, 0 errors**.

## 2. Attribution of the October L5 `bundled` vs. `med-agent-hub` benchmark gap

Across `l5-full-default-2026-10-22-d0e4e2d8`, `l5-full-default-2026-10-26-dffe15e9`, `l5-full-default-2026-10-28-2a053c09` (D4), and `l5-answer-rules-fresh-2026-10-29-effa8855` (R10):

| Metric / Slice | `bundled` (`gemma-4-12b` on router) | `hub-profile-single-12b-bare` | `hub-profile-single-12b-checked` | Root Cause |
| --- | --- | --- | --- | --- |
| Overall Mean Accuracy (D4 / R10) | `7.33` / `7.35` | `8.25` / `8.32` | `7.89` / `8.16` | Combined effect of G2.1–G2.4 below |
| Harm Flags (D4) | `1 / 17` (`single-upcoming-appointments`) | `0 / 17` | `0 / 17` | **G2.2**: No current/reference date (`2026-06-20`) in `bundled` prompt; historical `2026-02-23` appointment reported as upcoming (`2.5/2/8`, Harm=True) |
| Multi-turn Conversations (`convo-*`, Turn 2) | Stateful context lost on Turn 2 (`5.5–7.0`) | Turn 1 Q/A retained (`8.0–9.0`) | Turn 1 Q/A retained (`7.5–9.0`) | **G2.1**: `BundledClinicalAnswerProvider.execute()` drops `request.getPriorClinicalTurns()` when calling `chartSearchService.searchStreaming(...)` |
| 6-Month Rolling Window (`am-orders-6mo` in R10) | `5.8` | `9.0` | `8.9` | **G2.2 + G2.4**: Missing reference date in `bundled` plus deterministic temporal precomputation (`server/temporal.py`) and post-generation answer rules (`server/answer_rules.py`) in `med-agent-hub` |
| Date / Token Corruption (`d0e4e2d8`, `dffe15e9` vs. `2a053c09`) | Garbled dates (`20226-01`, `20225-07`) when `dry-multiplier = 0.8` | Affected prior to `2a053c09`; resolved when router set `dry-multiplier = 0` | Affected prior to `2a053c09`; resolved when router set `dry-multiplier = 0` | **G2.3**: Out-of-the-box `LocalLlmEngine` injects `dry_multiplier = 0.8` when no drug-reference block is present, which corrupts repeated date strings across 12.2k-token `fullChart` prompts |

## 3. UW CIRG GPU server 1-call parity benchmark (`30e1b771`) and `N=1, 2, 4` concurrency scaling (7 November 2026)

- **Deterministic completeness & longitudinal series remediations (`med-agent-hub` `83c700f`):**
  - Added `_extract_categorical_series(events)` in `server/temporal.py` and trimmed duplicate `"summary"` strings from `_extract_medication_order_summary` to keep `temporal_render: full` within the `16,384`-token budget across 5-turn conversations (`convo-medications-adherence` Turns 1–5).
  - Updated `_series_in_answer`, `_series_edits`, `_adherence_edits`, `_last_visit_purpose_edits`, and `_missed_return_visit_edits` in `server/answer_rules.py` so partial drafts that cite only one date or one anthropometric series deterministically receive the full longitudinal adherence history (`Overall drug adherence in last month: No` `[344]..[46]` and `Antiretroviral adherence in past week: All` `[343]..[45]`), all anthropometric series (`Weight`, `Height`, `Head circumference`) + active growth diagnoses (`Failure to thrive [131]`, `Delayed milestones [132]`), all uncited same-day clinical highlights on the most recent visit (`2026-01-07`), and explicit missed-return-visit framing (`2026-02-23 [22]` recorded on `2026-01-26` with no subsequent encounter).
  - Unit tests: `pytest tests/test_temporal.py tests/test_answer_rules.py tests/test_prompts.py tests/test_staged_stream.py -q` — **263 passed in 0.70s**.
- **34-cell / 70-turn `full-default` GPU server parity benchmark (`30e1b771-f083-4c6d-ad7c-66517fcdaf2a`, published at `l5-full-default-2026-11-07-30e1b771`):**
  - Executed against `https://llm.co.dev.cirg.uw.edu` (`ollama/gemma4:12b`, `parallel_slots=4`, `REFERENCE_DATE=2026-06-20`), scored by the blinded dual-judge panel (`claude-opus-5-5:high:1` + `gpt-6-astra:high:1`):
    - **`engine-parity-hub-answer-12b`**: **87.2/100** (`Accuracy: 9.12`, `Completeness: 8.59`, `Relevance: 9.03`, `Harm: 0/17`, `Confabulations: 0`, `date_wrong: 0`, `Citations resolved: 82/82` = `100.0%`).
    - **`engine-parity-bundled-12b`**: **78.5/100** (`Accuracy: 8.76`, `Completeness: 7.21`, `Relevance: 8.35`, `Harm: 0/17`, `date_wrong: 1`, `Over-abstentions: 4/17`, `Citations resolved: 50/50` = `100.0%`).
  - All 4 remediated cells improved on `engine-parity-hub-answer-12b` relative to `e774b280`:
    - `single-upcoming-appointments`: `77.0 -> 100.0` (`+23.0`, `10/10/10` on both judges)
    - `convo-medications-adherence`: `71.2 -> 86.0` (`+14.8`)
    - `am-last-visit`: `74.0 -> 82.2` (`+8.2`)
    - `ek-growth`: `80.8 -> 86.0` (`+5.3`)
- **Multi-clinician concurrency (`N=1, 2, 4`, `--turns-per-user 2`) on UW CIRG GPU server (`MED_AGENT_ROUTER_CONCURRENCY=4`):**
  - `engine-parity-bundled-12b`:
    - `N=1` (`d5f30fd1`): `10.64 turns/min`, `goodput_rate = 100%` (`10.64 goodput turns/min`), `ttft_p50_ms = 1,662.5 ms` (`turn_1 = 2,390.0 ms`, `turn_2plus = 935.0 ms`), `tpot_p50_ms = 11.3 ms/token`.
    - `N=2` (`e46c9f8a`): `10.73 turns/min`, `goodput_rate = 50%` (`5.36 goodput turns/min`), `ttft_p50_ms = 6,372.5 ms` (`turn_1 = 11,457.5 ms`, `turn_2plus = 1,301.5 ms`), `tpot_p50_ms = 16.0 ms/token`.
    - `N=4` (`96d7276b`): `9.20 turns/min`, `ttft_p50_ms = 17,800.5 ms`, `tpot_p50_ms = 15.6 ms/token`.
  - `engine-parity-hub-answer-12b` (warm-slot sweep):
    - `N=1` (`759e32de`): `3.74 turns/min`, `ttft_p50_ms = 3,253.5 ms` (`turn_1 = 3,217.0 ms`, `turn_2plus = 3,290.0 ms`), `tpot_p50_ms = 0.3 ms/token`.
    - `N=2` (`7f0c04af`): `6.30 turns/min` (`1.68x`), `ttft_p50_ms = 5,119.5 ms` (`turn_1 = 6,479.5 ms`, `turn_2plus = 3,396.0 ms`), `tpot_p50_ms = 6.2 ms/token`.
    - `N=4` (`c51f78b2`): `12.96 turns/min` (`3.47x`), `goodput_rate = 50%` (`6.48 goodput turns/min`), `ttft_p50_ms = 4,259.0 ms` (`turn_1 = 5,268.0 ms`, `turn_2plus = 3,170.5 ms`), `tpot_p50_ms = 7.5 ms/token`.
- **KV prefix cache boundary finding on Ollama (`gemma4:12b`):**
  - When `msg[0]` (`Structured temporal facts` + `Patient records (most recent first):`) is held constant across turns for the same patient, warm TTFT on an `18.1k`-token prompt drops from `15.6s` (cold prefill) to `2.19s–2.36s` (`7.1x` speedup). Question-dependent compaction inside `msg[0]` mutates the tail of `msg[0]` on each turn and invalidates Ollama's message-level prefix cache unless the static chart/temporal prefix is kept invariant across turns.

