# OpenClinAI Architecture

This document defines component responsibilities and dependency boundaries.
The [roadmap](roadmap.md) owns priorities, implementation phases and progress.

## 1. System Overview

OpenClinAI brings together clinical AI applications, model execution, clinical
record retrieval and validation. The umbrella repository assembles the development
workspace and owns cross-project operations. Each product owns its application
contracts. The validation harness is an independent consumer of those contracts,
not the workspace manager or a required product runtime.

This architecture defines the intended implementation. Current delivery status
is recorded in the roadmap. The umbrella contains only the tooling, configuration
and documentation required by this setup; it is not a copy of the previous
workspace. Paths, commands and package interfaces may change to establish these
boundaries. Backward compatibility requires an explicit current use case.

## 2. Responsibility Map

| Owner | Responsibilities | Excluded responsibilities |
| --- | --- | --- |
| OpenClinAI umbrella | Component gitlinks and version pins; checkout resolution; build/dependency order; shared environment configuration; deployment/lifecycle tooling; release verification; cross-project planning; public website and program status | Clinical application behavior; experiment scoring; a mandatory service for running validation |
| Validation harness | Configured experiment execution; validation adapters; scenarios and fixtures; output/trace collection; provenance recording; evaluation and human-review workflows; evidence and reports | Product gitlinks or pins; checkout/build/deployment management; release-policy enforcement; a fixed registry of OpenClinAI repositories |
| ChartSearchAI and ESM | OpenMRS authorization and conversations; provider lifecycle and persistence; bundled inference and configured Hub integration; clinical/evidence UI | A duplicate retrieval implementation or compulsory Hub-only application |
| QueryStore | OpenMRS read projections, synchronization, retrieval, shared context slices, freshness/completeness and public read API | Model execution, application chat UI or umbrella metadata |
| Med Agent Hub | Model profiles, prompts, role mappings, model access and hosted clinical execution contracts | Catalyst schema discovery, SQL execution or Dataset/Dashboard state |
| Catalyst | Source/dialect/schema context; query orchestration; advisory validation; selected SQL execution; Datasets, Widgets, Dashboards and publication | FHIR ingestion, a mandated warehouse engine or clinical-answer scoring |
| Data tooling | Reusable data migration and terminology operations under an explicit owner outside the harness | Application records or validation scoring; validation-specific fixture definitions remain experiment inputs |

Model serving remains an external runtime. FHIR Data Pipes and Superset own their
ingestion and visualization functions. Native OpenELIS reporting remains useful
independently of Catalyst or Hub.

## 3. Umbrella Workspace

The intended component checkout layout is:

```text
openclinai.org/
  specs/
  scripts/
  tests/
  targets/
    validation-harness/
    med-agent-hub/
    catalyst/
    chartsearchai/
    chartsearchai-esm/
    querystore/
```

In this design, each component has one umbrella gitlink and the validation harness
has no product gitlinks. `.gitmodules` describes repository locations; Git records
the selected revisions without a duplicate revision catalog.

The umbrella owns checkout discovery, component selection, cross-component builds,
shared environment configuration, deployment orchestration and release verification.
Products supply their native build, test and runtime entry points. The umbrella
invokes those entry points with explicit inputs; neither component assembly nor
product lifecycle management belongs to the validation harness.


## 4. Validation Harness Interface

An experiment supplies:

- a validation adapter and target connection/configuration;
- scenarios, fixtures and experiment parameters;
- evaluation and review settings;
- an output location and relevant target/run provenance.

The harness invokes the configured target's actual interface, captures responses
and traces, evaluates the experiment and writes evidence/report artifacts. An
adapter may be product-specific without making its product repository or checkout
layout a requirement of the harness core. Target identifiers are experiment
configuration, not a hard-coded list of workspace repositories.

Experiments must run against supplied targets without Git, submodules, product
source checkouts, version pins or an umbrella installation. The harness does not
clone, build, deploy or release targets as a prerequisite to validation. A target
may run locally or remotely; connection details come from experiment configuration.
Readiness checks test the capabilities needed by the experiment, not repository
branch, pin or worktree state.

Source revisions, image digests, model/profile identities and deployment receipts
can be supplied by the caller or observed through a target interface and recorded
as provenance. Recording identity is not selecting or enforcing a pin. Missing
metadata must be represented honestly under the experiment's evidence contract,
not inferred from an unrelated local checkout.

Offline evaluation/reporting consumes captured artifacts without starting product
services, making live clinical queries or silently rerunning model judgments.
Local unit-test fixtures and test doubles are not real-target acceptance evidence.

## 5. Dependency and Contract Rules

- Workspace assembly and deployment must not import validation scoring or run
  experiments as a prerequisite. Validation must not import umbrella checkout or
  release-policy machinery.
- Products expose their own interfaces and remain independent of the validation
  runner. Validation adapters consume those interfaces rather than implementing
  product behavior a second time.
- Hub profiles and model settings remain product-owned. Experiment parameters and
  provenance are separate from product configuration management.
- Catalyst owns its SQL workflow; Hub supplies configured model roles. Hub's
  clinical execution capabilities do not move into the validation harness.
- Product and experiment correctness is defined by current contracts, including
  clinical policy, scoring and sampling semantics. Workspace interface changes
  are independent of those application and evaluation requirements.
- Each requirement has one maintained owner. Documentation consumers link directly
  to that owner; historical evidence does not define current requirements.

## 6. Component Authorities

The linked contracts and registers correspond to recorded workspace revisions.
The component repositories maintain their subsequent development and release status.

- [Harness constitution](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/.specify/memory/constitution.md)
  supplies experiment governance; its control-plane scope must be amended in the
  harness repository as part of the ownership change.
- [Dual-provider contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/artifacts/planning/openmrs-dual-provider-conformance-contract.md)
  defines current OpenMRS provider behavior. Coordination moves to the umbrella;
  product requirements and validation protocols go to their respective owners.
- [Catalyst-Hub contract](https://github.com/DIGI-UW/openelis-catalyst/blob/6ba00082519f9fb2d864895b292352d8987ce51c/docs/med-agent-hub.md)
  defines the application/model-execution boundary.
- [Catalyst delivery register](https://github.com/pmanko/clinical-ai-validation-harness/blob/a27d7e51b7268653420e8f91306c9aaa4ab5a8ee/specs/008-catalyst-query-workbench/tasks.md)
  records product work at the selected component revision; its coordination and
  validation content is assigned to the respective owners in the roadmap.

Component changes follow their owning repository's governance. Implementation,
local verification, CI, publication and deployed acceptance are distinct outcomes.
