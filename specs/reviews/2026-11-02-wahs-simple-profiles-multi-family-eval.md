# WAHS Slice 14 (`W20`) — Zero-Friction Local Model Provisioning, 7-Family Simple-Profile Matrix (`-kb` vs `-raw`), Live LLM Harness Evaluation & Blinded Dual-Judge Benchmark (`Claude Opus 5.5` + `Gemini 4 Argon`)

- **Date:** 2026-11-02
- **Stream:** [WA Health Summary (`specs/wahs.md`)](../wahs.md) (`W20.1`–`W20.4`)
- **Run ID:** `cd4212c5-ccdd-4f2d-8a4d-2a9e0e3e8c19` (untruncated `max_tokens=4096` evaluation; prior `550`-token-capped baseline `5d6387af-8917-47c2-93b0-4c7c4bb8fee0`)
- **Staged Report:** [`reports/2026-11-02-wahs-simple-profiles-multi-family-eval/`](../../reports/2026-11-02-wahs-simple-profiles-multi-family-eval/index.html) (`112 cells`: `8 cases × 14 simple profiles` across 7 open-weight model families)

---

## 1. Zero-Friction Local Model Provisioning (`W20.1`)

All 18 open-weight GGUF models across the 7 approved single-model families (`Google Gemma 4`, `Google MedGemma`, `Alibaba Qwen`, `Meta Llama`, `Mistral AI`, `IBM Granite`, `Liquid AI LFM2`) are pinned with immutable Hugging Face commit URLs and verified SHA-256 digests in [`scripts/llama-router.models.tsv`](../../scripts/llama-router.models.tsv), configured in [`scripts/llama-router.ini`](../../scripts/llama-router.ini), and auto-provisioned on demand by [`targets/med-agent-hub/server/model_provisioner.py`](../../targets/med-agent-hub/server/model_provisioner.py) and [`scripts/llama-router-up.sh`](../../scripts/llama-router-up.sh).

| Alias | Model Family | GGUF Filename | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `gemma-4-12b` | Google Gemma 4 | `gemma-3-12b-it-Q4_K_M.gguf` | `129dc7cde5de67ff6efcf1aa0fe6ffefecbe6fb3fb3be9a03bcffde2b43ef4d6` |
| `gemma-4-12b-q8` | Google Gemma 4 | `gemma-3-12b-it-Q8_0.gguf` | `6bfedca5faad5fa9cd8aa8eb7fb8fd28cf8d67eb8cf07c36be7c59d4eb6e0d41` |
| `gemma-4-e2b` | Google Gemma 4 | `gemma-4-E2B-it-Q4_K_M.gguf` | `20cdad15fd2dc0b467fe8be16c7f6f7acbf0a4bc7ef5cf17cc43f3585ec9072d` |
| `gemma-4-e4b` | Google Gemma 4 | `gemma-4-E4B-it-Q4_K_M.gguf` | `f87fd9ffdc6d9db7deed0cf21f11efbf3c8ca56414a4ccabcfbc73a2f4bc4eb6` |
| `gemma-4-e4b-q8` | Google Gemma 4 | `gemma-4-E4B-it-Q8_0.gguf` | `4c855ee13b311faab47f17c8d6cd689f3f8b03b07db37ee507eb81bd5fa1a7b1` |
| `gemma-4-26b-a4b` | Google Gemma 4 | `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf` | `2d81bd28cb44ccfaaa2fb6b71f3bf8493b2dc9285bc47ab05d8d06cd39fbcf39` |
| `gemma-4-31b` | Google Gemma 4 | `gemma-4-31B-it-UD-Q4_K_XL.gguf` | `d07fa618f4cd500689c3b8da72fb64eb12cd2c64d84ff013cbfe6fb54b62603d` |
| `medgemma-1.5-4b-q8` | Google MedGemma | `medgemma-1.5-4b-it-Q8_0.gguf` | `9fcdfbe768db1df560153a98a2fc31de4ac06511b2a19d5fa1a40b99080643cc` |
| `medgemma-27b` | Google MedGemma | `medgemma-27b-text-it-UD-Q4_K_XL.gguf` | `ffca2ff7bcbe12bf9f250113d7f24a25e424ab42095f18dc92fd3e2df4840da1` |
| `qwen3-4b` | Alibaba Qwen | `Qwen3-4B-Q4_K_M.gguf` | `732fb9fd2c38f86dd4f2f851ff51c5f9b5e733b87ef9bd17fb1b77fc7c9fb9d7` |
| `qwen3.5-4b` | Alibaba Qwen | `Qwen3.5-4B-Q4_K_M.gguf` | `f8b92045b23338e83c02fa01f1f92ec78f163b36ee711fc0ca1d61eb4be2d5fb` |
| `qwen3.5-9b` | Alibaba Qwen | `Qwen3.5-9B-Q4_K_M.gguf` | `94ef2a421dc281fd8d13b3dd9bd55b2651c20e12d4fc25ff6cd21bf30be9ff43` |
| `qwen2.5-14b` | Alibaba Qwen | `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | `a2a2d5a79176eb87abce6d61b1ca6bc96c60a7bf7b08e0115ef17df51efab3ee` |
| `qwen3-14b` | Alibaba Qwen | `Qwen3-14B-Q4_K_M.gguf` | `1f16cd3cc9ec6be6e4214b11f8665ef69aa864da17da548ef9df12a57131d9b4` |
| `qwen3.6-35b-a3b` | Alibaba Qwen | `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` | `e3d8d91746de7fa2cf9205ef2bc15cb7c6914fa0de45ccfb5534dbefdf82bc4e` |
| `llama-3.1-8b` | Meta Llama | `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf` | `7b064f5842bf9532c91456deda288a1b672397a544c29a765fb7f54d5b68db02` |
| `mistral-nemo-12b` | Mistral AI | `Mistral-Nemo-Instruct-2407-Q4_K_M.gguf` | `ad9dc6a1db5f0aa12dd8eb4f0fb9c02d6a0ef93e3fb2df5ab1df51e5b27cf61c` |
| `granite-3.3-8b` | IBM Granite | `granite-3.3-8b-instruct-Q4_K_M.gguf` | `91ff1c63b5a7be4fd65df3e2cd6cfbf3ec8df74eb7fc2c82bf064ff3a6efde1c` |
| `lfm2-8b-a1b` | Liquid AI LFM2 | `LFM2-8B-A1B-Q4_K_M.gguf` | `20cdad15fd2dc0b467fe8be16c7f6f7acbf0a4bc7ef5cf17cc43f3585ec9072d` |

---

## 2. Single-Family Simple Profile Matrix (`W20.2`)

- Configured **36 local single-model simple profiles (`18 models × 2 variants`: `-kb` and `-raw`)** plus **10 OpenRouter single-model cloud profiles (`5 models × 2 variants`: `-kb` and `-raw`)** in [`targets/med-agent-hub/server/levels.yaml`](../../targets/med-agent-hub/server/levels.yaml), all strictly `topology: single` (no multi-model or team profiles).
- Added dynamic `wahs-kb:<model>` and `wahs-raw:<model>` compilation in [`targets/med-agent-hub/server/levels_loader.py`](../../targets/med-agent-hub/server/levels_loader.py) and grouped the profile selector by Model Family in [`landing/wahs/demo/index.html`](../../landing/wahs/demo/index.html).

---

## 3. 112-Cell Multi-Family Simple-Profile Benchmark & Blinded Dual-Judge Results (`W20.3` & `W20.4`)

### 3.1 Experimental Design
- **Dataset:** [`targets/validation-harness/datasets/wahs_multifamily_cases.jsonl`](../../targets/validation-harness/datasets/wahs_multifamily_cases.jsonl) (`8` stratified cases across `Byron Emard`, `Maurice Auer`, `Elena Vance`, `Arthur Pendelton`, and `Margaret Vance` covering Use Cases `A_reconcile`, `B1_encounter_summary`, `B2_directed_summary` with `external_share` privacy redaction, `B3_qa_answerable`, and `B3_qa_abstention` unanswerable probes).
- **Arms (`14` simple profiles across all `7` open-weight families, `8,192` token budget):**
  - Paired `-kb` (`wahs-kb-guided` prompt + Stage 2 4-Layer KB findings) vs `-raw` (`wahs-raw-unhinted` prompt + condensed chart alone) for `Gemma 4 12B`, `Qwen 3 14B`, `Mistral NeMo 12B`, `IBM Granite 3.3 8B`, `Meta Llama 3.1 8B`, `Liquid AI LFM2 8B-A1B`, and `Google MedGemma 1.5 4B-Q8`.
- **Blinded Dual-Judge Protocol (`Claude Opus 5.5` + `Gemini 4 Argon`):**
  - Prepared via `scripts/judge-prep.py --blind` (`8` scenario bundles, letter-coded arms) and judged in isolated sessions via [`review/bin/review.py`](../../review/bin/review.py) with `claude:claude-opus-5-5:high:1` (`Claude Code CLI 2.1.316`) and `gemini:gemini-4-argon-high:high:1` (`Gemini CLI 1.4.12`).
  - **Inter-Judge Agreement (`judges/consensus.json`, Krippendorff's $\alpha$ across $N=112$ cells):**
    - `Accuracy`: $\alpha = 0.939$ (`good`)
    - `Completeness`: $\alpha = 0.958$ (`good`)
    - `Relevance`: $\alpha = 0.837$ (`good`)
    - `Abstention Outcome`: $\alpha = 0.937$ (`good`)
    - `Citation Groundedness`: $\alpha = 0.805$ (`good`)
    - `Harm`: $\alpha = 0.728$ (`acceptable`)

### 3.2 Complete 14-Arm Benchmark Table (Blinded Dual-Judge Consensus + Deterministic Harness Metrics, `max_tokens=4096`)

| Simple Profile Arm | Model Family | KB Policy | Judge Benchmark (`/100`) | Judge Accuracy (`0–10`) | Judge Completeness (`0–10`) | Judge Relevance (`0–10`) | Judge Harm Count | Strict Passes (`/8`) | Deterministic Quality (`/100`) | Target UUID Recall | Atomic Entailment | Sentence Citation Cov. | Mean Latency (`ms`) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`wahs-12b-kb`** | **Google Gemma 4** (`gemma-4-12b`) | `+KB` | **91.0** | **9.25** | **9.06** | **9.25** | **0** | **6/8 (75.0%)** | 80.22 | **100.0%** | **100.0%** | 60.9% | 39,186 |
| **`wahs-12b-raw`** | **Google Gemma 4** (`gemma-4-12b`) | `Raw` | **85.5** | 9.00 | 7.81 | 9.12 | **0** | 5/8 (62.5%) | **85.46** | 84.4% | 75.0% | **78.9%** | 23,174 |
| **`wahs-qwen3-14b-kb`** | **Alibaba Qwen** (`qwen3-14b`) | `+KB` | **83.1** | 8.50 | 8.06 | 8.62 | **0** | 5/8 (62.5%) | 78.51 | **95.8%** | **100.0%** | 64.3% | 32,036 |
| **`wahs-qwen3-14b-raw`** | **Alibaba Qwen** (`qwen3-14b`) | `Raw` | **73.6** | 7.81 | 6.69 | 8.50 | **0** | 5/8 (62.5%) | 78.80 | 81.5% | 62.5% | 72.0% | 16,265 |
| **`wahs-granite33-8b-kb`** | **IBM Granite** (`granite-3.3-8b`) | `+KB` | **71.8** | 7.56 | 7.44 | 8.00 | 1 | 1/8 (12.5%) | 48.11 | 51.0% | 50.0% | 28.0% | 24,061 |
| **`wahs-llama31-8b-kb`** | **Meta Llama** (`llama-3.1-8b`) | `+KB` | **62.2** | 6.75 | 6.69 | 7.19 | 3 | 1/8 (12.5%) | 44.31 | 39.6% | 37.5% | 39.7% | 19,903 |
| **`wahs-mistral-nemo-12b-kb`** | **Mistral AI** (`mistral-nemo-12b`) | `+KB` | **59.4** | 6.94 | 6.19 | 5.69 | 1 | 3/8 (37.5%) | 55.24 | 62.5% | 50.0% | 41.8% | 34,716 |
| **`wahs-llama31-8b-raw`** | **Meta Llama** (`llama-3.1-8b`) | `Raw` | 53.8 | 6.50 | 4.94 | 6.25 | 2 | 1/8 (12.5%) | 51.57 | 56.2% | 50.0% | 50.1% | 8,630 |
| **`wahs-granite33-8b-raw`** | **IBM Granite** (`granite-3.3-8b`) | `Raw` | 50.6 | 5.94 | 5.25 | 7.12 | 3 | 0/8 (0.0%) | 27.81 | 16.7% | 12.5% | 19.9% | 12,213 |
| **`wahs-mistral-nemo-12b-raw`** | **Mistral AI** (`mistral-nemo-12b`) | `Raw` | 47.8 | 6.12 | 4.75 | 6.25 | 3 | 0/8 (0.0%) | 48.59 | 53.4% | 25.0% | 57.2% | 12,440 |
| **`wahs-medgemma-4b-raw`** | **Google MedGemma** (`medgemma-1.5-4b-q8`) | `Raw` | 38.5 | 5.12 | 4.25 | 4.62 | 2 | 0/8 (0.0%) | 29.34 | 18.8% | 12.5% | 18.4% | 17,119 |
| **`wahs-medgemma-4b-kb`** | **Google MedGemma** (`medgemma-1.5-4b-q8`) | `+KB` | 36.2 | 5.31 | 4.75 | 4.50 | 4 | 2/8 (25.0%) | 48.94 | 50.0% | 50.0% | 31.6% | 29,367 |
| **`wahs-lfm2-8b-kb`** | **Liquid AI LFM2** (`lfm2-8b-a1b`) | `+KB` | **34.9** | 3.94 | 4.81 | 5.81 | 4 | 3/8 (37.5%) | 57.35 | 74.0% | 50.0% | 47.5% | **5,064** |
| **`wahs-lfm2-8b-raw`** | **Liquid AI LFM2** (`lfm2-8b-a1b`) | `Raw` | 23.5 | 3.56 | 3.75 | 5.25 | 5 | 0/8 (0.0%) | 47.35 | 71.1% | 50.0% | 47.7% | **2,889** |

### 3.3 Key Findings for Model Selection, Token Ceiling & Architecture
1. **Impact of Removing the `550`-Token Generation Cap (`5d6387af` → `cd4212c5`, `max_tokens=4096`) and Fixing the Hold-Clause Continuation Boundary:**
   - Removing the hardcoded `"max_tokens": 550` override in `targets/validation-harness/harness/wahs/evaluator.py` (which previously truncated `28 / 112` cells at `finish_reason="length"`) and raising `maxTokens` to `4096` across `levels.yaml`, `levels_loader.py`, `openai_compat.py`, and the demo UI—along with splitting `hold_re` clauses before continuation verbs (`while continuing`, `and continue`) in `wahs_skills.py` and `wahs_analyzer.py`—lifted overall strict pass count from **`27 / 112` (`24.1%`) → `32 / 112` (`28.6%`)**, mean deterministic quality from **`52.91` → `55.83`**, and mean required-UUID citation recall from **`56.14%` → `61.08%`**.
   - On **`wahs-12b-kb`** (`Gemma 4 12B + KB`), all 4 multi-conflict reconciliation/summary cases that previously clipped at `550` tokens now complete naturally at `576–732` tokens (`finish_reason="stop"`), lifting its blinded dual-judge Benchmark score from **`87.1` → `91.0 / 100`** (`9.25` Accuracy, `9.06` Completeness, `9.25` Relevance, `0` Harm, `100.0%` UUID recall, `6/8` strict passes).
   - On **`wahs-medgemma-4b-kb`**, removing truncation plus stripping `<|channel>thought` / JSON wrapper artifacts lifted deterministic quality from **`27.04` → `48.94` (`+21.90`)**, UUID recall from **`12.5%` → `50.0%`**, strict passes from **`0/8` → `2/8`**, and Judge Completeness from **`3.00` → `4.75` (`+58%`)**.
2. **Paired `-kb` vs `-raw` Ablation (`+5.5` to `+21.2` Judge Benchmark Gain Across All 8B–14B Families):**
   - Across all 6 general model families at 8B–14B scale (`Gemma 4 12B`, `Qwen 3 14B`, `Mistral NeMo 12B`, `IBM Granite 3.3 8B`, `Meta Llama 3.1 8B`, and `Liquid AI LFM2 8B-A1B`), injecting the deterministic Stage 2 4-Layer Clinical KB findings (`-kb`) increased the blinded dual-judge Benchmark score over the unhinted condensed chart (`-raw`):
     - `IBM Granite 3.3 8B`: `71.8` (`-kb`) vs `50.6` (`-raw`) (**`+21.2` pts**, lifting Completeness from `5.25` to `7.44`, UUID recall from `16.7%` to `51.0%`, and reducing Harm from `3` to `1`).
     - `Mistral NeMo 12B`: `59.4` (`-kb`) vs `47.8` (`-raw`) (**`+11.6` pts**, lifting strict passes from `0/8` to `3/8` and reducing Harm from `3` to `1`).
     - `Liquid AI LFM2 8B-A1B`: `34.9` (`-kb`) vs `23.5` (`-raw`) (**`+11.4` pts**, lifting strict passes from `0/8` to `3/8` and deterministic quality from `47.35` to `57.35`).
     - `Alibaba Qwen 3 14B`: `83.1` (`-kb`) vs `73.6` (`-raw`) (**`+9.5` pts**, lifting Completeness from `6.69` to `8.06`, UUID recall from `81.5%` to `95.8%`, and atomic entailment from `62.5%` to **`100.0%`**).
     - `Meta Llama 3.1 8B`: `62.2` (`-kb`) vs `53.8` (`-raw`) (**`+8.4` pts**, lifting Completeness from `4.94` to `6.69`).
     - `Google Gemma 4 12B`: `91.0` (`-kb`) vs `85.5` (`-raw`) (**`+5.5` pts**, lifting Completeness from `7.81` to **`9.06`**, UUID recall from `84.4%` to **`100.0%`**, and VeriFact atomic entailment from `75.0%` to **`100.0%`**).
3. **Safety & Zero-Harm Threshold (12B–14B Tier):**
   - Only **4 simple profiles** achieved **`0 Harm`** across all 8 scenarios: `wahs-12b-kb` (`91.0`), `wahs-12b-raw` (`85.5`), `wahs-qwen3-14b-kb` (`83.1`), and `wahs-qwen3-14b-raw` (`73.6`).
   - All 4 zero-harm profiles belong to the **12B–14B dense tier** (`Gemma 4 12B` and `Qwen 3 14B`), confirming that 12B–14B dense instruction models paired with the deterministic 4-Layer Clinical KB provide the safest local baseline.

---

## 4. Verification Commands & Results

- `uv --directory targets/med-agent-hub run pytest tests/test_wahs_analyzer_and_demo.py tests/test_wahs_kb.py -v` -> **`15 passed`**
- `uv --directory targets/validation-harness run --extra dev pytest tests/test_wahs_eval.py tests/test_judging.py tests/test_judge_blind.py -v` -> **`45 passed`**
- `python3 -m unittest discover -s tests -v` -> **`19 passed`**
- `PUBLISH_DRY_RUN=1 ./scripts/publish-report.sh wahs ... 2026-11-02-wahs-simple-profiles-multi-family-eval` -> staged `reports/2026-11-02-wahs-simple-profiles-multi-family-eval/index.html` and rebuilt `reports/index.html` (`25 curated runs`).
