# HIV OpenMRS Research Setup

## Goal

Provide a fresh OpenMRS environment with the existing HIV dataset, ChartSearchAI
and seven evaluation accounts. Ross and other researchers should be able to
start it using the umbrella's existing tools and a short guide.

OpenClinAI owns setup and builds. Products own their functionality. The validation
harness runs experiments against the prepared services; evaluations are not part
of installing the environment.

**Current status:** The HIV-only startup fix and account definitions are present.
The public setup command and account provisioning still need connecting. Earlier
startup/import observations are partial proof, not a completed handoff.

## Implementation

1. Build the pinned QueryStore, ChartSearchAI and frontend using the existing
   [Makefile](../Makefile) targets.
2. Import the existing HIV archive with [seed-local.sh](../scripts/seed-local.sh).
   Use [backend-init.sh](../compose/backend-init.sh) to disable the stock
   patient generator before OpenMRS starts.
3. Apply the existing ChartSearchAI and QueryStore configuration and indexing.
4. Port the existing account provisioner from [setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148)
   and apply the [seven account definitions](../environments/chartsearch-research/accounts.json).
5. Document the tested command, application address and logins in the
   [operator guide](../environments/README.md).

Connect these native operations through one short public setup command.
The [saved recipe](../environments/chartsearch-research/preset.json) identifies
the data and account inputs. Use the existing local configuration conventions.
The standard demo administrator login is `admin` / `Admin123`.

Work in [umbrella PR #5](https://github.com/pmanko/openclinai.org/pull/5).
No custom environment manager, storage/ownership audit, per-installation build
framework, migration, backup or recovery work belongs in this PR. Remove the
added command-detail tests, exact-archive restriction and clinical-table hashing.
Keep existing native tools unchanged unless a demonstrated setup failure needs
a small fix. Never generate replacement patients or silently switch providers.

## Setup Proof

Only simple live smoke checks are needed:

| Check | Evidence |
| --- | --- |
| OpenMRS is running | Open the application and log in |
| ChartSearchAI is available on OpenMRS | Open it in a patient chart |
| The intended HIV data is loaded | Inspect a few known patient records |

The setup must also apply the saved evaluation accounts and must not add
stock-generated patients. Do not create a setup-testing framework or require
model-quality scores, full provider walkthroughs, reports or videos to install it.

Review the retained diff for simplicity, readable instructions and accidental
private data. Run the existing repository checks; these are not a substitute
for the smoke checks:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
git diff --check
```

Update the PR with observed results and unfinished work. Do not call the handoff
ready until its documented setup command works.

## Later Work

Authenticated role/location context, In-Depth, model comparisons, judging,
reports and demonstrations are subsequent functionality work. Catalyst and other
scenarios may reuse these native tools with their own saved inputs when scheduled.
Do not build speculative support now.

See the [source inventory and scope audit](reviews/2026-10-02-ross-migration-inventory.md)
and [earlier startup/import observations](reviews/2026-10-02-research-preparation-proof.md).
The [main roadmap](roadmap.md) owns cross-project priorities.
