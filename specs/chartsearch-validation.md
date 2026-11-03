# ChartSearchAI validation fidelity, streaming parity, and bundled attribution

**Spec ID:** `CHARTSEARCH-VALIDATION-2026-11` · **Status:** in progress (owner, 3 November 2026) ·
**Owners:** umbrella (this spec, router presets, review records), harness (`client.py`, `metrics.py`,
`engine-tap.py`, `backends.json`), Med Agent Hub (staged answer streaming), ChartSearchAI (`HubClinicalAnswerProvider`
relay only; `bundled` implementation untouched)

Validation runs must record ChartSearchAI behavior and latency as a clinician experiences them inside
OpenMRS for both `bundled` and `med-agent-hub`, separate measurement artifacts from real product gaps in
`bundled`, and bring `med-agent-hub` to live main-answer token-streaming parity without masking `bundled`'s
actual behavior.

## Scope and boundaries

1. **Do not patch `bundled` in `openmrs-module-chartsearchai` to hide its product gaps.** The evaluation
   exists to measure and report `bundled` as shipped so decision makers can see where `bundled` falls
   short and what `med-agent-hub` adds.
2. **Relay-only exception in `openmrs-module-chartsearchai`:** `HubClinicalAnswerProvider` may advertise
   `token_streaming` and map `answer_delta` and `reasoning_delta` wire frames onto `TurnEvent.textDelta`
   so `med-agent-hub`'s live answer stream reaches the OpenMRS REST SSE controller and browser.
3. **Simulate `LocalLlmEngine` out-of-the-box behavior over `engine=remote`:** OpenMRS runs in a
   CPU-only container while inference runs on the host Metal GPU router. Rather than running a CPU
   `llama-server` child inside the OpenMRS container, `engine-tap.py` and the router configuration
   reproduce `LocalLlmEngine`'s exact sampler rules and model/context budgets on the host Metal router.

## Audit findings: measurement artifacts vs. `bundled` product gaps

### 1. Measurement and harness artifacts (Goal 1)

| Finding | Where | Effect on reported numbers | Remediation |
| --- | --- | --- | --- |
| Buffered SSE stream collapse | `harness/validate/client.py` (`ChartSearchAiClient.chat`, `collapse_turn_stream`) | Waits for the entire HTTP response to close (`turn_done`), discards `preliminary_delta`, `reasoning_delta`, and `answer_delta` events, and reports only terminal `turn_done` wall-clock as `latency_ms`. Hides `bundled`'s streaming time-to-first-token (`ttft_ms`) and conflates Hub main-answer completion (`answer_done_ms`) with post-answer review, grounding, and In-Depth stages. | V1 |
| Zeroed token and cache metrics | `harness/validate/metrics.py` (`_DEFERRED`) | Overwrites `tokens_in` and `tokens_out` with `None` and ignores `cachedTokens`, even though `BundledClinicalAnswerProvider.toAnswerEnvelope()` emits `inputTokens`, `outputTokens`, and `cachedTokens` on the SSE envelope. | V2 |
| Hardcoded `admin` basic auth and fixed pacing | `harness/validate/client.py` (`ChartSearchAiClient`) | Authenticates as `admin` (no clinical provider role or session location in `accountContext`) and sleeps a fixed `6.5 s` between turns to avoid `chartsearchai.rateLimitPerMinute=10`. | V3 |
| Non-streaming Hub primary answer synthesis | `med-agent-hub/server/team.py` (`_synthesize_answer`), `engine.py`, `HubClinicalAnswerProvider.java` | Hub waits for the complete writer JSON object and deterministic gate before sending `answer_done`, and `HubClinicalAnswerProvider` drops `answer_delta`. Clinicians see no incremental tokens during Hub synthesis. | V4 |

### 2. Why `bundled` scores lower on the L5 reports (Goal 2)

Across the published L5 runs (`l5-full-default-2026-10-22-d0e4e2d8`, `l5-full-default-2026-10-26-dffe15e9`,
`l5-full-default-2026-10-28-2a053c09`, and `l5-answer-rules-fresh-2026-10-29-effa8855`), the gap between
`bundled` (`7.33` mean accuracy in D4, `7.35` in R10, `1/17` Harm in D4) and `med-agent-hub`
(`hub-profile-single-12b-bare`: `8.25` in D4, `8.32` in R10, `0/17` Harm) comes from four distinct causes:

| # | Cause | Category | Mechanism |
| --- | --- | --- | --- |
| G2.1 | Multi-turn conversation amnesia | `bundled` product bug (kept as-is for evaluation) | `BundledClinicalAnswerProvider.execute()` calls `chartSearchService.searchStreaming(patient, question, ...)` and drops `request.getPriorClinicalTurns()`. On all four `convo-*` scenarios, Turn 2 has no memory of Turn 1. |
| G2.2 | No reference or current date in the `bundled` prompt | `bundled` product and benchmark gap (kept as-is for evaluation) | Neither `LlmProvider.DEFAULT_SYSTEM_PROMPT` nor `PatientChartSerializer` includes `LocalDate.now()` or the benchmark `reference_date` (`2026-06-20`). On calendar-relative questions (`single-upcoming-appointments`, `am-upcoming-appointments`, `am-orders-6mo`), `bundled` treats historical dates (`2026-02-23`, `2026-01-07`) as current or upcoming, producing `bundled`'s Harm flag (`2.5/2/8`, Harm=True) in `2a053c09`. |
| G2.3 | Out-of-the-box `LocalLlmEngine` DRY penalty (`dry_multiplier = 0.8`) on `fullChart` | Out-of-the-box `bundled` sampler interaction with `#603` (`fullChart`) | `LocalLlmEngine.buildRequestBody()` injects `samplers: ["dry", "temperature"]`, `dry_multiplier: 0.8`, `dry_base: 1.75`, `dry_allowed_length: 8`, `dry_penalty_last_n: -1` whenever no drug-safety reference block is in the prompt (`ReferenceRecords.NONE`), and disables DRY only when drug references are present. Over a ~12.2k-token `fullChart` prompt, `dry_multiplier: 0.8` penalizes copying repeated dates and drug names from the chart, causing garbled dates in `d0e4e2d8` and `dffe15e9` before `scripts/llama-router.ini` set `dry-multiplier = 0` on 28 October (`2a053c09`). |
| G2.4 | Architectural capabilities in `med-agent-hub` | Intentional product differentiation | Precomputed chart-wide temporal facts (`server/temporal.py`), deterministic post-generation answer rules (`server/answer_rules.py`, lifting 6-month order accuracy from ~5.8 to ~9.0 in R10), structured `blocks` tables, and the static WHO HIV clinical knowledge base. |

## Target path (Goals 1 & 2)

- [x] V1 Incremental SSE stream telemetry in the validation harness
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `ChartSearchAiClient.chat()` consumes `/ws/rest/v1/chartsearchai/chat/stream`
    as a live stream (`stream=True`, `iter_lines`) and timestamps each SSE frame with `time.perf_counter_ns()`
    relative to request start. `collapse_turn_stream()` remains compatible with static text inputs while
    attaching `stream_timings` to the response envelope: `ttft_ms` (first `preliminary_delta`,
    `reasoning_delta`, or `answer_delta`, falling back to `answer_done_ms` when no deltas precede
    `answer_done`), `preliminary_start_ms`, `reasoning_start_ms`, `answer_delta_start_ms`,
    `answer_done_ms`, `answer_validation_ms`, `evidence_updated_ms`, `indepth_done_ms`, `turn_done_ms`,
    `delta_count`, `answer_delta_count`, `itl_p50_ms`, `itl_p95_ms`, and `tpot_ms`. `latency_ms` stays
    the terminal turn latency (`turn_done_ms`) while `compute_metrics()` surfaces the stage and streaming
    latency fields.
- [x] V2 Token and prompt-cache accounting in validation metrics
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `compute_metrics()` removes the `_DEFERRED` override that forced `tokens_in`
    and `tokens_out` to `None`, extracts `tokens_in` (`inputTokens` / `prompt_tokens`), `tokens_out`
    (`outputTokens` / `completion_tokens`), and `cached_tokens` (`cachedTokens` / `cache_n`) from the
    response envelope or usage block, and leaves them `None` only when absent from the response.
- [x] V3 Configurable clinical persona and rate-limit pacing in `ChartSearchAiClient`
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `ChartSearchAiClient` reads optional clinical credentials (`CHARTSEARCH_USER`,
    `CHARTSEARCH_PASSWORD`) and session location (`CHARTSEARCH_LOCATION_UUID`) in addition to
    `VALIDATE_MIN_INTERVAL_S`, allowing runs under provisioned clinical accounts (`doctor`, `nurse`,
    `clerk`) or `admin` without modifying `bundled` module code.
- [x] V4 Live main-answer token streaming in `med-agent-hub` and the OpenMRS Hub relay
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** When `execute_profile` runs the `"answer"` stage for a streamed turn,
    `med-agent-hub` streams the primary writer completion (`stream=True`), incrementally extracts the
    JSON `"answer"` string value as chunks arrive (correctly decoding JSON escapes across chunk boundaries),
    and yields `answer_delta` SSE events (`{"delta": "<chunk>"}`) live before running
    `_ensure_substantive_answer`, `gate`, and `resolve_refs` and emitting the authoritative post-gate
    `answer_done` envelope. In `openmrs-module-chartsearchai`, `HubClinicalAnswerProvider` declares
    `ProviderCapability.TOKEN_STREAMING` and maps `answer_delta` and `reasoning_delta` wire frames to
    `TurnEvent.delta(...)`, with `bundled` classes untouched.
- [x] V5 Out-of-the-box vs. parity `bundled` simulation via `engine-tap.py` and backend matrix
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `targets/validation-harness/scripts/engine-tap.py` supports
    `--simulate-local-engine-dry` (injecting `LocalLlmEngine`'s exact conditional DRY payload when no
    drug-reference block is present in the prompt, and temperature-only when present) and records
    upstream `llama-server` token/cache timings (`prompt_n`, `cache_n`, `predicted_n`, `prompt_ms`,
    `predicted_ms`), paired with `engine-parity-bundled` (`gemma-e4b`) and `engine-parity-bundled-12b`
    (`gemma-4-12b`) in `datasets/validation/backends.json`.
- [x] V6 Verification and attribution review record
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** Unit test suites in `targets/validation-harness`, `targets/med-agent-hub`,
    and `targets/chartsearchai` (`HubClinicalAnswerProviderTest` and conformance tests) pass; a dated
    review in `specs/reviews/` records the verification results and the 4-factor attribution of the
    October L5 `bundled` vs. `med-agent-hub` gap.

## Target path (Goal 3: Hardware, multi-session concurrency, and deployment sizing)

- [x] V7 Stage 1 — Hardware profile metadata and streaming/stage latency breakdown in validation reports
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `write_run_meta()` in `harness/validate/runner.py` records optional serving
    hardware metadata (`VALIDATE_HARDWARE_TIER`, `VALIDATE_HARDWARE_GPU`, `VALIDATE_HARDWARE_VRAM_GB`,
    `VALIDATE_SERVING_ENGINE`, `VALIDATE_PARALLEL_SLOTS`, `VALIDATE_INFERENCE_ENDPOINT`) into `run_meta.json`,
    and `build_report()` in `harness/validate/report.py` surfaces `hardware` metadata, per-arm
    `streaming_latency` aggregates (`avg_ttft_ms`, `p95_ttft_ms`, `avg_answer_done_ms`, `p95_answer_done_ms`,
    `avg_turn_done_ms`, `avg_tpot_ms`, `avg_cached_tokens`), and per-cell `TTFT`, `answer`, and `TPOT`
    chips without altering existing golden report renders when optional fields are absent.
- [x] V8 Stage 2 — Configurable multi-slot router concurrency and multi-clinician session runner
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** `med-agent-hub/server/team.py` supports `MED_AGENT_ROUTER_CONCURRENCY`
    (default `1` -> `asyncio.Lock()`, `> 1` -> `asyncio.BoundedSemaphore(N)` via `configure_router_concurrency()`)
    so multi-slot GPU serving (`llama-server --parallel N`, vLLM, or LiteLLM) executes `N` concurrent
    turns in parallel while single-slot local routers stay serialized. In `targets/validation-harness`,
    `harness/validate/concurrency.py` and `harness-cli validate concurrency` drive `N` simultaneous
    clinician workers across distinct provisioned OpenMRS accounts (`eval-doctor`, `eval-nurse`,
    `eval-pharmacy`, `eval-clerk`, `eval-lab`, `eval-researcher`, `admin`) and patient sessions using
    `ThreadPoolExecutor`, emitting `concurrency_results.jsonl` and `concurrency_summary.json`
    (`n_users`, `throughput_turns_per_min`, `slo_thresholds_ms`, `goodput_turns`, `goodput_rate`,
    `goodput_turns_per_min`, `ttft_p50_ms`, `ttft_p95_ms`, `turn_1_ttft_p50_ms`,
    `turn_2plus_ttft_p50_ms`, `answer_done_p50_ms`, `answer_done_p95_ms`, `turn_done_p50_ms`,
    `turn_done_p95_ms`, `tpot_p50_ms`, `cache_hit_ratio_avg`, `error_rate`).
- [x] V9 Stage 3 — OpenMRS decision-maker hardware and deployment sizing matrix
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** Publish the OpenMRS implementer hardware and deployment sizing matrix below,
    grounding VRAM and KV-cache calculations in observed longitudinal HIV `fullChart` prompt sizes
    (~12.2k input tokens per turn) and comparing `bundled` vs. `med-agent-hub` across hardware tiers and
    concurrent clinician counts (`N=1, 2, 4+`).
- [x] V10 Ecosystem benchmark integration and `openclinai.org` project overview pages
  ([3 November verification](reviews/2026-11-03-chartsearch-validation-audit.md)).
  - **Acceptance criteria:** Incorporate external clinical QA and serving benchmark best practices
    (`ArchEHR-QA` / `EHRNoteQA` evidence-vs-alignment split, `HealthBench` / `MedHELM` multi-axis rubric
    with PPI human calibration, and `NVIDIA AIPerf` / `GuideLLM` / `vllm bench serve` SLO goodput and
    turn-position prefix-cache tracking) into `targets/validation-harness` and publish updated
    project overview pages at `landing/validation-harness/index.html` and
    `landing/chartsearchai/comparing-answer-paths/index.html`.

## OpenMRS decision-maker hardware and deployment sizing matrix

For longitudinal HIV patient charts (`fullChart` serialization in `#603`), each turn sends **~12,200 input
tokens** of structured clinical history plus system instructions. Hardware sizing is therefore governed by
**prefill compute (`ttft_ms`)** and **per-slot KV-cache memory** across concurrent clinician sessions (`N`):

| Tier | Representative Hardware | Serving Engine & Model | VRAM / Memory Budget (~12.2k ctx/slot) | Target Clinic Concurrency (`N` active clinicians) | Expected Interactive Latency (`N=1` -> `N=4`) | Recommended ChartSearchAI Path |
| --- | --- | --- | --- | --- | --- | --- |
| **Tier 0: CPU-only Clinic Server** | 8–16 vCPU Xeon/EPYC, 32 GB RAM (no GPU) | `LocalLlmEngine` (`llama-server` CPU, `Gemma 4 E4B Q4_K_M`, `-np 1`) | ~3.3 GB weights + ~2.5 GB KV (`16k` ctx, 1 slot) | `N=1` light/occasional use only | `ttft_ms`: **25–60 s** on 12.2k-token chart; `N>=2` queues serially (`>60–120 s`) | Not recommended for longitudinal `fullChart` HIV clinics without an external GPU inference host |
| **Tier 1: Entry Single GPU / Edge Box** | NVIDIA L4 / RTX 4090 (24 GB VRAM) or Apple Silicon M-series (32–64 GB unified) | `llama-server` (`--parallel 2 -cb --cache-ram 8192`) or vLLM (`Gemma 4 E4B` or `Gemma 4 12B Q4_K_M`) | 12B Q4 weights (~7.6 GB) + 2 slots x 16k KV (~5–6 GB FP16 / ~2.5 GB Q8_0) = **~13–15 GB** | `N=1..2` concurrent clinicians (supports 10–25 total clinic staff) | `N=1`: `ttft_ms` **0.8–2.5 s** (warm prefix cache) / **3–7 s** (cold), `answer_done_ms` **4–10 s**; `N=4` queues behind 2 slots | `med-agent-hub` (`single-12b-bare` for fast interactive turns; `single-12b-checked` when background grounding + In-Depth are desired) |
| **Tier 2: Clinic / District Hospital GPU Server** | NVIDIA L40S (48 GB), A100 (80 GB), or shared **NVIDIA H200 (141 GB)** | vLLM or `llama-server --parallel 4` + `MED_AGENT_ROUTER_CONCURRENCY=4` (`Gemma 4 12B` / `27B`) | 12B weights (~7.6–24 GB) + 4–8 slots x 16k KV with prefix caching = **~20–48 GB** | `N=4..8` simultaneous chart queries (supports 50–150+ clinic staff) | `N=1..4`: parallel prefill & decode with automatic prefix caching; `ttft_ms` **0.3–1.2 s**, `answer_done_ms` **2–5 s**, `tpot_ms` **12–25 ms/tok** | `med-agent-hub` (`single-12b-checked` or `team-12b-checked`) pointed at GPU server via `MED_AGENT_LLM_BASE_URL` |
| **Tier 3: Regional / Cloud Hub** | Managed OpenAI-compatible / Vertex / vLLM cluster behind LiteLLM | `med-agent-hub` with `MED_AGENT_ROUTER_CONCURRENCY=8+` | Elastic / managed | Multi-site / regional deployment (`N=8+` concurrent turns) | Sub-second `ttft_ms`, horizontal slot scaling | `med-agent-hub` with site-level governance and audit logging |

### Running comparative hardware and concurrency benchmarks

1. **Single-user accuracy + stage/streaming latency (`V1`–`V7`):**
   ```bash
   VALIDATE_HARDWARE_TIER=gpu_server \
   VALIDATE_HARDWARE_GPU="NVIDIA H200" \
   VALIDATE_HARDWARE_VRAM_GB=141 \
   VALIDATE_SERVING_ENGINE=vllm \
   VALIDATE_PARALLEL_SLOTS=4 \
   uv --directory targets/validation-harness run harness-cli validate run \
     engine-parity-l5 --reference-date 2026-06-20
   ```
2. **Multi-clinician session concurrency (`N=1, 2, 4`, `V8`):**
   ```bash
   # On med-agent-hub pointed at a multi-slot GPU server: set MED_AGENT_ROUTER_CONCURRENCY=4
   uv --directory targets/validation-harness run harness-cli validate concurrency \
     engine-parity-l5 --backend-id hub-profile-single-12b-bare --users 4 --turns-per-user 2
   ```
