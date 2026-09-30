# OpenClinAI

Scoped umbrella workspace for OpenClinAI coordination, shared tooling and pinned
component checkouts. Repository: [pmanko/openclinai.org](https://github.com/pmanko/openclinai.org)
(private initially; a future organization/visibility change is separate).

**Start with [specs/roadmap.md](specs/roadmap.md).** It owns priorities, cross-project
decisions and migration gates. [Architecture](specs/architecture.md) explains
responsibility boundaries, not a second task list.

## Scope and checkout layout

```text
openclinai.org/
  specs/                         # current coordination and implementation direction
  scripts/                       # umbrella workspace checks
  tests/                         # checks for umbrella tooling
  targets/validation-harness/     # pinned harness submodule
    targets/                     # product submodules pinned by the harness
      catalyst/
      chartsearchai/
      chartsearchai-esm/
      med-agent-hub/
      openmrs_chatbot/
      querystore/
```

The umbrella owns program coordination and, as migration proceeds, shared
checkout/build/deployment tooling. The harness owns validation scenarios, thin
adapters, reproducible fixtures, provenance, evaluation/review and reports.
Products own their behavior and contracts. This is a submodule-based umbrella,
not a merger of product histories or another clinical application.

The initial topology deliberately preserves the harness's nested product paths
and pins. There are **no duplicate top-level product gitlinks or revision lockfiles**.
Promoting products to direct umbrella submodules requires a reviewed path/consumer
migration; it is not achieved by checking out a second independently pinned copy.
The harness still contains mixed responsibilities pending the roadmap's splits.

The public website remains in the harness's `landing/` and `site/` flows. No
website, domain, runtime, deployment or existing dirty checkout has been migrated.

## Bootstrap and offline checks

Requires Git and Python 3.10+; these umbrella checks do not install product dependencies.

```sh
git clone --recurse-submodules https://github.com/pmanko/openclinai.org.git
cd openclinai.org
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
```

For an existing clone, initialize the recorded revisions:

```sh
git submodule update --init --recursive
```

Do **not** use `git submodule update --remote` as bootstrap. Gitlinks are exact
revision authority; `.gitmodules` contains URLs and branch hints, not moving pins.
Check for local component work before any update that may switch its checkout.

The [workspace CI](.github/workflows/workspace.yml) initializes recursive submodules,
runs unit tests and checks umbrella links, recorded pins and component cleanliness.
It does not build products, invoke models, deploy, or certify release/publication
policy. Component tests and CI remain owned by their repositories.

Cross-repository document links use GitHub permalinks to the recorded component
commits so they work on GitHub as well as locally. The offline checker verifies
those paths against the local pinned Git objects. Update links with reviewed pin
changes, not independently of their source checkout.

## Component changes and first slice

Read each component's own instructions and current contracts before editing it.
Use a short-lived branch in each affected repository. Commit/publish component
changes in that repository first, then update the umbrella gitlink to the reviewed,
remote-reachable commit. Never publish an umbrella pin to a local-only commit.
Do not stage dirty product pins or unrelated files with documentation changes.

The prepared first slice is [Feature 005 cleanup](specs/spec-cleanup-inventory.md):
reconcile its direct canvas/catalog consumers, consolidate any current requirements
into existing owners, and delete obsolete specification content. No superseded
banners, archived spec copies or redirect stubs. Git history owns prior specs.
One canvas direction question must be resolved before executing that deletion.

Implementation uses matching local `spec/005-current-contract-cleanup` branches in
the umbrella and harness after the bootstrap main is published. Only branch setup
and preparation are included in bootstrap; no harness deletion is claimed.

The existing sibling `clinical-ai-validation-harness` checkout remains independent.
Its dirty report-index, Hub profile, submodule and Compose work is not imported.
Upstream OpenMRS projects keep their existing `harness-integration` publication
policy; umbrella setup does not authorize replacement PRs or product pushes.
