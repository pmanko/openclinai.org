# OpenClinAI

OpenClinAI brings together tools for clinical AI, patient-chart search, health-data
analysis, and reproducible evaluation. This repository connects the projects and
provides a shared development workspace.

**[Project website](https://openclinai.org)** ·
**[Explore the projects](#explore-the-projects)** ·
**[Contribute](#contribute)**

## Projects

| Project | What it does | Setup and source |
| --- | --- | --- |
| **ChartSearchAI** | Lets clinicians ask questions about an OpenMRS patient chart and inspect answers with source citations. | [Backend](https://github.com/pmanko/openmrs-module-chartsearchai) · [OpenMRS frontend](https://github.com/pmanko/openmrs-esm-chartsearchai) |
| **Med Agent Hub** | A shared service for applications to configure and call language models, including clinical-answer workflows. | [Repository](https://github.com/pmanko/med-agent-hub) |
| **Catalyst** | A supervised SQL workbench and dashboard builder for exploring health data, reviewing queries and publishing results to Apache Superset. | [Repository](https://github.com/DIGI-UW/catalyst-ai) |
| **QueryStore** | Retrieves and organizes OpenMRS clinical records for chart search and AI applications. | [Repository](https://github.com/pmanko/openmrs-module-querystore) |
| **Clinical AI Validation Harness** | Runs clinical-AI experiments, collects outputs and evidence, and produces evaluation and review reports. | [Repository](https://github.com/pmanko/clinical-ai-validation-harness) |

ChartSearchAI integrates with [OpenMRS](https://openmrs.org/). Catalyst supports
SQL-connected data sources, including reporting workflows for
[OpenELIS Global](https://openelis-global.org/). Each project provides installation
and usage documentation in its repository.

For ChartSearchAI background and community discussion, see the
[OpenMRS project page](https://openmrs.atlassian.net/wiki/spaces/projects/pages/373325839/Chart+Search+aka+ChartSearchAI).
The OpenMRS repository links above point to the development forks used by this workspace.

## Explore the projects

- [ChartSearchAI overview](https://openclinai.org/chartsearchai/): patient-chart
  search and clinical-answer workflows.
- [Catalyst overview](https://openclinai.org/catalyst/) and
  [screenshot walkthrough](https://openclinai.org/catalyst/hiv-gallery/): query
  workbench and reporting workflows.
- [Evaluation reports](https://reports.openclinai.org/): published experiments
  and supporting evidence.

To install a project, follow its setup guide in the repositories listed above.

## Contribute

For product development, use that project's repository and contributor instructions.
For component integration and shared development tooling, use this workspace.
The [architecture](specs/architecture.md) explains how the projects fit together;
the [implementation roadmap](specs/roadmap.md) records priorities, status and
acceptance criteria. Read the [repository instructions](AGENTS.md) before editing.

### Workspace checkout

Cloning requires Git and authenticated GitHub access to this private repository.
The checkout uses the component revisions recorded by the workspace.

```sh
git clone --recurse-submodules https://github.com/pmanko/openclinai.org.git
cd openclinai.org
```

For an existing clone, check for local changes before updating its submodules:

```sh
git submodule update --init --recursive
```

### Workspace checks

Requires Python 3.10+:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
```

These commands check documentation links and component checkout consistency.
Each product supplies its own build and test instructions.

### Shared development

For reusable research installations, see [Research environments](environments/README.md).
Configuration selection and read-only status are implemented; migration and the
tested researcher handoff remain in progress.

The root `Makefile` provides the shared environment and product build commands:

| Command | Purpose |
| --- | --- |
| `make openmrs-source-pair-build` | Build QueryStore, then ChartSearchAI, and stage their modules. |
| `make chartsearch-esm-build` | Build and stage the OpenMRS frontend. |
| `make chartsearchai-local` | Prepare the local ChartSearchAI environment. |
| `make catalyst-mvp-up` | Start the configured Catalyst environment, retaining existing data. |
| `make validate-run SET=demo` | Run the selected validation experiment against prepared services. |

Read the component's setup instructions before building or starting it. Product
builds require the component-specific Java, Node, Docker or model-service tools.
Connection settings and credentials belong in ignored environment files.

### Website

Website pages and assets are in `landing/`; documentation and interactive previews
are in `site/`. The [website guide](site/README.md) covers local builds, checks and
publication. Static hosting configuration lives in `compose/website/`, and the
GitHub Pages workflow is configured in this repository.
