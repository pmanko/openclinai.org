# Background & evidence — clinical AI for low-resource health settings

Research on infrastructure, health-data governance and open models informs
OpenClinAI's clinical AI experiments. Sources include WHO guidance, peer-reviewed
literature and recent preprints. Confidence notes distinguish reported findings
from qualified estimates; some guidance and paywalled studies are represented by
official summaries or abstracts rather than full texts.

---

## 1. WHO SMART Guidelines — computable, guideline-concordant care

- **SMART = Standards-based, Machine-readable, Adaptive, Requirements-based, Testable** — WHO's approach to getting its recommendations into countries' digital systems faithfully and fast. (WHO, "From paper to digital pathway," 18 Feb 2021 — who.int/news; confirmed across 3 sources incl. JMIR 2025. *high*)
- They are "a comprehensive set of reusable digital health components … that transform the guideline adaptation and implementation process to **preserve fidelity and accelerate uptake**." (WHO Digital Health & Innovation — who.int/teams/digital-health-and-innovation/smart-guidelines. *high*)
- Organized into **five knowledge layers (L1–L5)** — "a systematic, transparent and testable structure": **L1 Narrative** (human-readable recommendations) → **L2 Operational** (software-neutral requirements, delivered as Digital Adaptation Kits) → **L3 Machine-readable** (structured specs with coding/terminology/interoperability standards) → **L4 Executable** (software running static algorithms) → **L5 Dynamic** (algorithms optimized with analytics). (WHO smart.who.int DAK pages; L1–L4 *high*, L5 one-line definition *medium* — WHO confirms the name "Dynamic" but L5 content is largely "not yet available".)
- Motivation (peer-reviewed): converting narrative guidelines to digital systems has been "laborious, prone to error, and lacks accompanying technical documentation appropriate for digital use." (Muliokela et al., JMIR Medical Informatics, 7 Feb 2025 — medinform.jmir.org/2025/1/e58858. *high*) Foundational paper: Mehl et al., "WHO SMART guidelines…," Lancet Digital Health, 2021 (PMID 33610488 — thesis confirmed, full text paywalled).
- **Project tie-in:** the harness asks for the same property SMART Guidelines demand of software — answers that are **standards-based, verifiable, and traceable**, not opaque.


## 2. WHO ethics & governance of AI / LMMs in health

- WHO's first global guidance, **"Ethics and governance of artificial intelligence for health"** (28 Jun 2021, ISBN 9789240029200), sets six principles: human autonomy; well-being/safety/public interest; transparency & explainability; responsibility & accountability; inclusiveness & equity; responsive & sustainable AI. (who.int/news 28-06-2021. *high*)
- **Equity warning:** AI "systems trained primarily on data collected from individuals in **high-income countries may not perform well for individuals in low- and middle-income settings**." (WHO, 28 Jun 2021. *high*)
- Second, dedicated guidance, **"…Guidance on large multi-modal models (LMMs)"** (18 Jan 2024, ISBN 9789240084759), 40+ recommendations. (who.int/news 18-01-2024. *high*)
- **Hallucination/harm:** LMMs carry "documented risks of producing **false, inaccurate, biased, or incomplete statements, which could harm people** using such information in making health decisions." (WHO, 18 Jan 2024. *high*)
- **Automation bias:** LMMs "can also encourage 'automation bias' … whereby errors are overlooked that would otherwise have been identified." (WHO, 18 Jan 2024. *high*)
- Data risk: data disclosed to LMM developers "can usually not be retrieved as future iterations of the model may be trained on this data." (WHO, 18 Jan 2024. *high*)
- Safeguards WHO recommends: inclusive design with clinicians/patients from the start; mandatory independent post-release auditing & impact assessment; assigning a regulator to approve health LMMs; models designed "to perform well-defined tasks with the necessary accuracy and reliability." (WHO, 18 Jan 2024. *high*)


## 3. Why low-resource settings need a different design

- **Electricity:** "Close to **1 billion people** in low- and lower-middle-income countries are … served by health-care facilities **without reliable electricity or with no electricity** at all." In sub-Saharan Africa only **40%** of facilities have reliable electricity, **15%** none. (WHO fact sheet, 31 Aug 2023 — who.int/news-room/fact-sheets/detail/electricity-in-health-care-facilities. *high*)
- **Connectivity:** **78%** of people in low-income countries are offline (vs 7% in high-income); in rural low-income areas only **1 in 6 (16%)** use the internet. (ITU Facts and Figures 2024. *high*)
- **Workforce:** WHO projects a shortfall of **~11 million health workers by 2030**, mostly in low/lower-middle-income countries. (WHO health-workforce page. *high* for current figure; the number has moved 10–18M across WHO docs/years — treat as version-dependent.)
- **Research/data concentration:** >87% of healthcare-LLM research is led by high-income-country institutions; Africa ≈0.31% despite ~20% of world population. (Chen et al., Lancet Regional Health – Western Pacific, Oct 2025 — PMC12556221. *high*)
- **Performance gap:** "LLMs make up to **three times more errors** when retrieving information related to low-income countries"; accuracy can fall "from around 80% in English to just 50% in Thai." (Chen et al., 2025. *high* for citation; underlying primary numbers *medium*.)
- **Cloud economics:** a 70B model needs ~8 A100 GPUs (~US$300k/yr cloud); serving one per 100k people "could consume up to 15% of national healthcare expenditure"; even a $20/mo fee "exceeds the financial means of nearly half the global population." (Chen et al., 2025. *high* as reported.)
- **Independent confirmation + recommendation:** 2026 scoping review (44 studies) — fragile infrastructure a barrier in 77.3%, hardware limits 50%, literacy/staffing gaps 61.4%, fragmented/paper records 81.8%; recommends "**offline-capable AI models with local data caching**." (Al-Ganad et al., Frontiers in Digital Health, 2026. *high*)
- **Project tie-in:** unreliable infrastructure motivates experiments with locally hosted models and application-supplied clinical context. Disconnected operation depends on the complete service configuration and available hardware.

## 4. Data privacy, sovereignty & local ownership

- **Sovereignty:** at WHO's May 2026 digital-health/AI debate, LMICs warned AI "risks accelerating data extraction"; Cameroon (African Region) feared corporations would "harvest data from the Global South to train AI models"; Barbados argued health data should be "**a national asset under local control**." (Health Policy Watch, 2 May 2026. *high*)
- **Governance principle:** the Health Data Governance Principles support federated approaches that keep data near its point of generation, informing the case for local processing. ([Transform Health, 2022](https://healthdatagovernance.org/principles/). *Paraphrase of the published principles.*)
- **Cloud-LLM privacy risk:** a review of **464** healthcare-LLM studies found six privacy risks from external/cloud LLMs and that **38.4%** reported *no* PHI-protection measures; its top recommendation: "**Priority should be given to deploying the LLM locally.**" (Zhong et al., JMIR, 21 Nov 2025 — jmir.org/2025/1/e76571. *high*)
- **Data colonialism:** research on decolonizing global health examines extractive practices that move data away from the communities that generate it. ([Scoping review, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12560380/). *Concept summarized, not a verbatim definition.*)

- **Project tie-in:** local processing can reduce disclosure risk. Verify configured providers, evaluation services and evidence redaction for each deployment; this is not a blanket privacy guarantee.


## 5. Open-weight models & right-sizing per task

- **Small can run offline:** a **3.8B** open model (Phi-3-mini) runs fully offline on an iPhone in ~1.8 GB at >12 tok/s, at roughly GPT-3.5 quality. (Microsoft Research, Phi-3 Technical Report, Apr 2024 — arxiv.org/abs/2404.14219. *high*)
- **Open is closing the gap:** on 1,933 real radiology cases, closed GPT-4o scored **79.6%** and open Llama-3-70B **73.2%**; authors: "open-source LLMs are quickly closing the gap to proprietary LLMs." (Kim et al., npj Digital Medicine, 12 Feb 2025 — PMC11814077. *high*)
- **Medical open models:** MedGemma (open, Gemma-3-based, 4B/27B) scores 64.4% (4B) / 87.7% (27B w/ test-time scaling) on MedQA vs 50.7%/74.9% base; authors recommend it when a use case needs "ability to run locally or offline." (Sellergren et al., Google, Jul 2025 — arxiv.org/abs/2507.05201. *high*; the 87.7% includes test-time scaling.)
- **Right-sizing / routing:** matching model size to task difficulty (small for easy, escalate to large only for hard) yields large savings (e.g. a router hitting 97% of GPT-4 quality at ~24% cost). (Moslem & Kelleher survey, ADAPT/TCD, Apr 2026 — arxiv.org/abs/2603.04445. Direction *high*; exact percentages *medium*, setup-dependent.)
- **Capable size range on modest hardware:** Llama 3.2 1B, Qwen2.5 1.5B, Gemma 2 2B/9B, Phi-3-mini 3.8B/Phi-4 14B, Mistral 7B — 1–9B built for on-device. (model cards; anchored by Phi-3. *high*.)
- **Safety limit — small models can't self-verify:** AI self-verification wrongly accepted incorrect medical answers **>60%** of the time, and smaller models were no better — "cannot serve as a universal safety layer." (Jin et al., "Verification Mirage," UBC/Vector, May 2026 — arxiv.org/abs/2605.10850. *medium*, recent preprint, consistent w/ peer-reviewed LLM-as-judge literature.) This motivates independent evidence-based evaluation and human review; a larger model's judgment also needs validation for the task.
- **Project tie-in:** applications can use configured open models, while harness experiments use separately selected evaluation methods and reviewers. Model evaluation may use local or remote services; provider configuration determines connectivity and disclosure requirements.

**Study limitations:** the self-verification finding is reported in a recent preprint, not established deployment performance. MedGemma's 27B headline result includes test-time scaling.

---

## How the external evidence maps to the project (the through-line)

| The reality (cited above) | The project's answer (in-repo) |
|---|---|
| Care runs offline, on modest hardware (§3) | Configurable local model services; disconnected operation depends on the selected services and hardware |
| HIC-trained AI underperforms for LMIC patients (§2, §3) | Application-supplied clinical context and evaluation on intended records, terminology and populations |
| Sending PHI to clouds is a privacy/sovereignty risk (§4) | Prefer local processing; verify providers and publication/redaction boundaries |
| LMMs hallucinate; small models can't self-verify (§2, §5) | Evaluate claim support against captured source evidence using selected evaluators and human review |
| Software should be guideline-concordant & testable (§1) | Configured experiments that capture responses, available evidence and review findings |

The research supports **local processing, context appropriate to the deployment,
and independent evaluation against recorded evidence** as priorities for clinical AI experiments.
