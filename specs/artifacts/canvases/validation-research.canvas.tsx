import { Callout, H1, H2, Link, Stack, Table, Text } from 'cursor/canvas';

const methodologyRows = [
  [
    'Retrieval',
    'Precision@k, recall/coverage@k, miss@k, empty-answer correctness, latency',
    'Medical RAG studies show retrieval is often the main bottleneck; one large expert eval found only about 22% of top-16 passages relevant.',
  ],
  [
    'Test-data fidelity',
    'Import success, schema compatibility, concept mapping coverage, serialized resource coverage, known-answer fixtures',
    'OpenMRS demo data is version-sensitive; modern Ref App validation needs an importable corpus whose observations, concepts, encounters, notes, and demographics survive indexing.',
  ],
  [
    'Evidence selection',
    'Which retrieved records the answer actually cites or uses',
    'Separate retrieval quality from LLM use of evidence; relevant records can be retrieved and still ignored.',
  ],
  [
    'Answer grounding',
    'Claim-level support against retrieved context; unsupported, partially supported, contradicted',
    'Use RAGAS/TruLens-style faithfulness as a screening metric, but require clinician adjudication for acceptance thresholds.',
  ],
  [
    'Citation quality',
    'Statement-level citation precision and recall',
    'MedCite-style evaluation is a better fit than answer-level citation counts; every clinical claim should map to records.',
  ],
  [
    'Abstention',
    'Correct no-record/no-answer behavior, especially for negative clinical questions',
    'FHIR-AgentBench keeps empty-answer cases; OpenMRS should make absent-data cases first-class, not edge cases.',
  ],
  [
    'Security',
    'Prompt injection, system prompt leakage, schema escape, sensitive data disclosure',
    'OWASP LLM Top 10 2025 maps directly to regression suites plus structured-output validation.',
  ],
  [
    'Clinical review',
    'Blinded clinician scoring, inter-rater agreement, adjudication, reviewer instructions',
    'TRIPOD-LLM asks for assessor qualifications, annotation guidelines, and agreement reporting.',
  ],
  [
    'Governance',
    'Dataset transparency, intended use, change protocol, monitoring, rollback criteria',
    'NIST, CHAI, FDA PCCP, and STANDING Together all point toward documented lifecycle controls.',
  ],
];

const sourceRows = [
  [
    <Link href="https://openmrs.atlassian.net/wiki/spaces/docs/pages/26273323/Demo+Data">OpenMRS Demo Data</Link>,
    'Documents platform-versioned demo SQL datasets, including large demo data, plus the modern Ref App generator path.',
    'The dated demo-data profile describes a transformed 2.8-compatible corpus. Record dataset provenance and verify import fidelity for the version used in an experiment.',
  ],
  [
    <Link href="https://github.com/openmrs/openmrs-module-referencedemodata">openmrs-module-referencedemodata</Link>,
    'Reference Application module that creates demo patients on startup from the global property path documented by OpenMRS.',
    'Use this as a current Ref App schema/metadata reference and control data path, not as the replacement for the large demo corpus.',
  ],
  [
    <Link href="https://github.com/openmrs/openmrs-content-referenceapplication-demo">openmrs-content-referenceapplication-demo</Link>,
    'Reference Application demo content package with starter metadata such as labs, diagnoses, drugs, and configuration.',
    'Use as the metadata side of the mapping, especially when legacy SQL concepts do not align with current Ref App concepts.',
  ],
  [
    <Link href="https://arxiv.org/abs/2511.06738">Rethinking RAG for Medicine</Link>,
    'Stage-aware expert evaluation: retrieval, evidence selection, response factuality/completeness.',
    'Use its decomposition as the core OpenMRS validation model.',
  ],
  [
    <Link href="https://arxiv.org/abs/2501.16672">VeriFact</Link>,
    'EHR-grounded fact verification via RAG plus LLM-as-judge, compared with clinician ground truth.',
    'Adapt claim-level support labels for chart answers.',
  ],
  [
    <Link href="https://arxiv.org/abs/2506.06605">MedCite</Link>,
    'Medical citation generation and evaluation with statement-level citation precision and recall.',
    'Use citation precision/recall, not citation count, for answer quality.',
  ],
  [
    <Link href="https://arxiv.org/abs/2509.19319">FHIR-AgentBench</Link>,
    '2,931 clinical questions grounded in FHIR; reports retrieval and answer correctness, including empty answers.',
    'Borrow benchmark structure for querystore and OpenMRS resource-level QA.',
  ],
  [
    <Link href="https://medhelm.org/medhelm">MedHELM</Link>,
    'Holistic medical LLM evaluation emphasizing realistic tasks, safety, and reproducibility.',
    'Use for model-selection discipline, not as a replacement for OpenMRS-specific evals.',
  ],
  [
    <Link href="https://pmc.ncbi.nlm.nih.gov/articles/PMC12104976/">TRIPOD-LLM</Link>,
    'Healthcare LLM reporting checklist with data, metrics, annotation, prompting, compute, and intended-use items.',
    'Turn into metadata requirements for every eval run.',
  ],
  [
    <Link href="https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence">NIST GenAI Profile</Link>,
    'Risk-management lifecycle for design, development, use, and evaluation of GenAI systems.',
    'Use as governance backbone for release gates and monitoring.',
  ],
  [
    <Link href="https://chai.org/workgroup/responsible-ai/responsible-ai-checklists-raic">CHAI RAIC</Link>,
    'Healthcare AI self-review across usefulness, fairness, safety, transparency, privacy/security.',
    'Use for clinical-readiness checklist and review packet.',
  ],
  [
    <Link href="https://www.datadiversity.org/recommendations">STANDING Together</Link>,
    'Dataset diversity, inclusivity, generalisability, and transparency recommendations.',
    'Track who is represented in eval patients and clinical question sets.',
  ],
  [
    <Link href="https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/">OWASP LLM Top 10 2025</Link>,
    'Security risk taxonomy for prompt injection, leakage, vector weaknesses, misinformation, and more.',
    'Expand PromptInjectionEvalTest into a maintained red-team corpus.',
  ],
  [
    <Link href="https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/">RAGAS Faithfulness</Link>,
    'Claim-support scoring against retrieved context.',
    'Good automated screen; do not use as sole clinical acceptance criterion.',
  ],
  [
    <Link href="https://www.trulens.org/getting_started/core_concepts/rag_triad/">TruLens RAG Triad</Link>,
    'Context relevance, groundedness, and answer relevance.',
    'Matches the desired OpenMRS split: retrieve right records, cite facts, answer the question.',
  ],
];
export default function ValidationResearch() {
  return (
    <Stack gap={20}>
      <H1>Validation research and evidence</H1>
      <Text>Separate retrieval, evidence selection, answer grounding and clinical review.
        These research methods inform experiment design; they are not product contracts or release acceptance.</Text>
      <Callout tone="warning" title="Claims need evidence">
        Record-level evidence and reviewer rationale matter more than aggregate scores.
        Test doubles establish runner mechanics, not clinical safety. Keep final answers,
        In-Depth material and rejected drafts distinct, and review/redact artifacts before publication.
      </Callout>
      <H2>Evaluation methodology</H2>
      <Table headers={['Area', 'Measures', 'Why it matters']} rows={methodologyRows} striped />
      <H2>Research sources</H2>
      <Table headers={['Source', 'Finding', 'Use in experiment design']} rows={sourceRows} striped />
      <Link href="https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/006-validation-harness-mvp/spec.md">Current experiment and evidence contract</Link>
      <Link href="#/spec/specs/background/component-contracts">Product-native documentation and contracts</Link>
    </Stack>
  );
}
