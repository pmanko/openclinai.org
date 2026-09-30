# OpenClinAI

OpenClinAI brings together tools for clinical AI, patient-chart search, health-data
analysis, and reproducible evaluation. This repository connects the projects and
provides a shared development workspace.

**[Project website](https://openclinai.org)** ·
**[Roadmap](specs/roadmap.md)** ·
**[Architecture](specs/architecture.md)**

## Projects

| Project | What it does | Source |
| --- | --- | --- |
| **ChartSearchAI** | Lets clinicians ask questions about an OpenMRS patient chart and inspect answers with source citations. Supports bundled inference and a separately configured Med Agent Hub provider. | [Backend](https://github.com/pmanko/openmrs-module-chartsearchai) · [OpenMRS frontend](https://github.com/pmanko/openmrs-esm-chartsearchai) |
| **Med Agent Hub** | Provides shared model profiles, prompts and execution services, including clinical-answer workflows and model roles used by Catalyst. | [Repository](https://github.com/pmanko/med-agent-hub) |
| **Catalyst** | A supervised SQL workbench and dashboard builder for exploring health data, reviewing queries and publishing results to Apache Superset. | [Repository](https://github.com/DIGI-UW/catalyst-ai) |
| **QueryStore** | Provides OpenMRS clinical-record retrieval and context selection for ChartSearchAI, and an optional patient-data source for Med Agent Hub. | [Repository](https://github.com/pmanko/openmrs-module-querystore) |
| **Clinical AI Validation Harness** | Runs reproducible evaluations through product APIs and captures scenarios, provenance, evidence and review reports. | [Repository](https://github.com/pmanko/clinical-ai-validation-harness) |

ChartSearchAI integrates with [OpenMRS](https://openmrs.org/). Catalyst supports
SQL-connected data sources, including reporting workflows for
[OpenELIS Global](https://openelis-global.org/). Each project provides installation
and usage documentation in its repository.

For ChartSearchAI background and community discussion, see the
[OpenMRS project page](https://openmrs.atlassian.net/wiki/spaces/projects/pages/373325839/Chart+Search+aka+ChartSearchAI).
The OpenMRS repository links above point to the development forks used by this workspace.

## Get started

Clone the workspace with its recorded component revisions. The roadmap describes
[current implementation status](specs/roadmap.md#2-implementation-status).

```sh
git clone --recurse-submodules https://github.com/pmanko/openclinai.org.git
cd openclinai.org
```

For an existing clone:

```sh
git submodule update --init --recursive
```

Read the component's README for installation, configuration and usage. Submodule
updates use the revisions recorded by the workspace. Check for local changes
before updating.

## Development

The [roadmap](specs/roadmap.md) describes current priorities and the
[architecture](specs/architecture.md) explains how the projects fit together.
Component repositories own their implementation, contracts and tests.

Workspace checks require Python 3.10+:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
```

These checks validate workspace links and component checkout consistency.
Products own their tests, the harness runs validation experiments, and the umbrella
owns workspace deployment and release verification. See
[contributor instructions](AGENTS.md) before making changes.
