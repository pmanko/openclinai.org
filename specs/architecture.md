# OpenClinAI Architecture

OpenClinAI combines clinical applications, model execution, clinical-record
retrieval and validation. This document describes the target architecture and
interfaces. The [roadmap](roadmap.md) tracks implementation and delivery.

## 1. Components

| Component | Responsibilities |
| --- | --- |
| OpenClinAI umbrella | Component repositories and version pins; workspace configuration; builds, deployment and release orchestration; project documentation and website |
| Validation harness | Run configured experiments, collect outputs and traces, record provenance, evaluate results and produce evidence and review reports |
| ChartSearchAI and ESM | OpenMRS patient-chart questions, conversations, authorization, provider selection, streaming answers and clinical-evidence presentation |
| QueryStore | OpenMRS clinical-record projections, synchronization, retrieval, context selection and freshness/completeness metadata |
| Med Agent Hub | Model profiles, prompts, role mappings, model access and clinical-answer workflows |
| Catalyst | SQL workbench, source/schema context, query execution, Datasets, Widgets, Dashboards and publication |

ChartSearchAI uses QueryStore for clinical context and supports bundled inference
and configured Med Agent Hub workflows. Catalyst supplies schema context and
orchestrates query generation through model roles configured in Med Agent Hub.

Model servers execute inference requests. FHIR Data Pipes provides ingestion for
the reference analytics deployment; Apache Superset renders published dashboards.
OpenELIS also provides native reporting.

## 2. Development Workspace

The component layout is:

```text
openclinai.org/
  specs/
  scripts/
  tests/
  landing/
  site/
  compose/
    website/
  targets/
    validation-harness/
    med-agent-hub/
    catalyst/
    chartsearchai/
    chartsearchai-esm/
    querystore/
```

Each component has one umbrella gitlink. `.gitmodules` records repository locations,
and Git records the selected revisions.

The umbrella resolves component checkouts, configures shared environments, orders
builds, orchestrates deployment and verifies releases. Products expose native
build, test and runtime commands. Workspace tooling invokes those commands with
explicit component paths and environment settings.

## 3. Validation Experiments

The validation harness is an independently installable experiment runner. Its
modules provide target adapters, scenario execution, trace collection, evaluation
and report generation.

### Inputs

| Input | Purpose |
| --- | --- |
| Target adapter and connection settings | Select the target interface and connect to a local or remote service |
| Scenarios, fixtures and parameters | Define experiment inputs and execution conditions |
| Evaluation and review settings | Select evaluators, criteria and review workflows |
| Target and run metadata | Identify the tested system, models, data and experiment configuration |
| Output location | Store responses, traces, evaluation results and reports |

Adapters invoke product interfaces and capture their responses. Experiment
configuration selects the adapter and target. Readiness checks verify the
capabilities and connectivity needed by the experiment.

An experiment runs with the harness package, its selected adapter/evaluator
dependencies, input data and access to its target. The same interface supports
services launched by the umbrella, independently deployed services and externally
provided targets.

### Outputs and Provenance

Run artifacts contain experiment inputs, target responses, traces, evaluation
results and review records. Target identity can include a source revision, image
digest, model/profile identifier or deployment receipt supplied by the caller or
reported by the target. Unavailable metadata is explicitly identified.

Evaluators read captured inputs, outputs and evidence according to the experiment's
evaluation settings. Evaluation may invoke configured model services, recording
model, prompt and configuration provenance. Human review records the reviewer,
findings and rationale.

Report generation is an offline transformation of captured evidence, evaluation
results and review records. A report can be regenerated with the target and
evaluator services unavailable.

## 4. Interfaces

| Interaction | Contract |
| --- | --- |
| Umbrella → product | Component revision, build/runtime configuration and native command interface |
| Umbrella → harness | Experiment configuration, target connection settings, provenance and output location |
| Harness → product | Adapter-specific requests through the product's API or execution interface |
| Harness → evaluator | Captured inputs, outputs and evidence plus evaluation settings |
| Evaluator → report | Results, findings and review records linked to their source evidence |
| ChartSearchAI → QueryStore | Clinical-record retrieval and selected context with provenance and completeness metadata |
| ChartSearchAI → Med Agent Hub | Configured clinical profile execution with streamed answer and evidence events |
| Catalyst → Med Agent Hub | Configured model roles for Catalyst's application-controlled SQL workflow |

Product contracts define clinical and application behavior. Experiment contracts
define execution, evidence, scoring, sampling and review semantics. The umbrella
selects component versions and connects their interfaces.

## 5. Website and Publication

The `openclinai.org` repository contains the public website's page content, assets,
navigation, documentation/status interfaces, sitemap and site configuration.
It also contains the associated build tools, publication scripts, deployment
workflows and web-server configuration. Website CI and release operations run
from this repository.

The validation harness produces experiment artifacts and rendered reports.
OpenClinAI publication tooling consumes selected artifacts, maintains public
catalogs and publishes them to the configured web destinations. Publication uses
the recorded evidence and evaluation results as its inputs.

## 6. Contract References

These links identify contracts at the component revisions recorded by the workspace.

- [OpenMRS provider contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/9b5b87ef67397fe7705b37467b98d3550c8d0e47/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md)
- [QueryStore API](https://github.com/pmanko/openmrs-module-querystore/blob/8b79db9791fe47315d3aae9cb09e9fdf004e6ee6/docs/rest-api.md)
- [Catalyst–Med Agent Hub contract](https://github.com/DIGI-UW/catalyst-ai/blob/6ba00082519f9fb2d864895b292352d8987ce51c/docs/med-agent-hub.md)
