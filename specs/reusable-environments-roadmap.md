# HIV OpenMRS Research Setup

## Goal

Provide a fresh OpenMRS environment with the existing HIV dataset, ChartSearchAI
and seven evaluation accounts. Ross and other researchers should be able to
start it using the umbrella's existing tools and a short guide.

OpenClinAI owns setup and builds. Products own their functionality. The validation
harness runs experiments against the prepared services; evaluations are not part
of installing the environment.

The setup command is `make chartsearch-research-setup`. It connects the existing
build, startup, import and configuration tools, followed by the saved accounts.
The [operator guide](../environments/README.md) owns prerequisites and logins.

## Implementation

1. Build the pinned QueryStore, ChartSearchAI and frontend using the existing
   [Makefile](../Makefile) targets.
2. Import the existing HIV archive with [seed-local.sh](../scripts/seed-local.sh).
   Use [backend-init.sh](../compose/backend-init.sh) to disable the stock
   patient generator before OpenMRS starts.
3. Apply the existing ChartSearchAI and QueryStore configuration and indexing.
4. Apply the [seven account definitions](../environments/chartsearch-research/accounts.json)
   through [provision-evaluation-users.py](../scripts/provision-evaluation-users.py),
   reusing the existing OpenMRS REST client rather than importing the old installer.
5. Document the tested command, application address and logins in the
   [operator guide](../environments/README.md).

Keep these operations in the short [setup script](../scripts/chartsearch-research-setup.sh).
Use the existing local configuration conventions.
The standard demo administrator login is `admin` / `Admin123`.

Work in [umbrella PR #5](https://github.com/pmanko/openclinai.org/pull/5).
No custom environment manager, storage/ownership audit, per-installation build
framework, migration, backup or recovery work belongs in this PR. No added
command-detail tests, exact-archive restriction or clinical-table hashing.
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

Local proof on 3 October 2026: the setup command completed, both modules started,
and all seven account logins worked. The clinical-officer account opened the
sample patient chart, showing its vitals and HIV medications, and launched
ChartSearchAI with the E4B checked profile selected. The import loaded 5,334
patients, 14,322 encounters and 428,036 observations. Ross's install remains
recipient verification, not a prerequisite for submitting this setup PR.

## Later Work

Authenticated role/location context, In-Depth, model comparisons, judging,
reports and demonstrations are subsequent functionality work. Catalyst and other
scenarios may reuse these native tools with their own saved inputs when scheduled.
Do not build speculative support now.

The [main roadmap](roadmap.md) owns cross-project priorities.
