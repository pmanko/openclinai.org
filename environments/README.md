# Research Environments

OpenClinAI owns setup and updates. The validation harness runs experiments against
an already-prepared service and produces reports; it does not manage installations.

**Current implementation:** configuration selection and read-only status only.
Startup, initialization, updates, account provisioning and migration through this
interface are not available yet. Do not use it to replace an existing installation.

## Select an Installation

An installation has a name such as `research` or `ross`. Names start with a lowercase
letter and contain only lowercase letters, digits and hyphens, at most 48 characters.
The shared preset `chartsearch-research` references native configuration and the
required seven research accounts. It does not duplicate model profiles or prompts.

From the umbrella checkout, create private settings without putting credentials
in shell history:

```sh
mkdir -p .local/environments/research
test ! -e .local/environments/research/settings.env && \
  install -m 600 environments/chartsearch-research/settings.env.example \
    .local/environments/research/settings.env
```

Edit the copy for this installation. Do not overwrite an existing settings file.
Its directory is ignored by Git; the file must be owned by you and mode `600`.
Never commit it or paste its contents into a report.

Settings are literal `KEY=VALUE` lines. Single or double quotes may surround a value.
There is no shell expansion, `export`, multiline value or inline-comment syntax.
Shared `.env.chartsearch.example` defaults are applied first, then this file, then
explicit command options. The old checkout-wide `.env.chartsearch` and ambient
shell settings do not silently supply installation overrides.

Supported overrides are the existing settings in `.env.chartsearch.example`, plus
database/index ports, database credentials/name, backend tag, timezone/anchor and
the optional warmup patient identifier. Unknown keys fail rather than being passed
to a service. Credentials are accepted only from the private settings file, not
command options. Warmup remains optional test preparation, not a product change.

## Inspect Without Changes

```sh
make environment-config ENV=research
make environment-status ENV=research
```

Configuration inspection needs Python 3.11+ and the referenced component files.
Initialize the recorded checkouts using `git submodule update --init` if a reference
is missing. Docker status additionally needs Git and a running local Docker engine
with Compose. Native Windows orchestration is not supported; use a Linux WSL2 shell.

For a temporary non-secret override without editing the file:

```sh
python3 scripts/environment.py config --environment research \
  --set HARNESS_PROXY_HTTP_PORT=8108
```

Both commands are read-only: no startup, package installation, build, seed, repair,
account creation or receipt writing. Public output shows configuration origins,
ports, selected paths and observed service state, not credential values. A Docker
error is a failure, not evidence of an empty installation.

The selected project is `openclinai-<name>` and its future artifacts directory is
`artifacts/environments/<name>`. The current native Compose file still uses fixed
container names and shared artifact mounts. Status reports that limitation;
distinct selected project names alone do **not** prove runtime isolation. Existing
stacks with another project name are not adopted or changed by these commands.

## Research Accounts and Migration

The preset's account manifest is carried over from the reviewed source of
[setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148)
at `2b3b1fd0a112b3a3710cda45211212ae7d90c96f`, without obsolete study-tier metadata.
It defines clinical officer, nurse, pharmaceutical technologist, adherence counsellor,
health records officer, doctor and peer educator accounts. **No accounts are
provisioned by the current commands.** Doctor/Nurse inherited permissions must be
inspected when provisioning is implemented; these are not production least-privilege
accounts or an automatic role-based instruction policy.

Baseline metadata records the verified SQL archive checksum/size and the private
project package location. Selection does not download or import it, and package
access does not imply verified restore/upgrade behavior.

Normal future startup/update must preserve data, accounts, conversations and custom
settings. First initialization and reset remain distinct explicit operations.
An existing installation requires an ownership/schema inventory, restorable backup
and approved storage mapping before changes. See the
[implementation roadmap](../specs/reusable-environments-roadmap.md); recipient
browser testing and final handoff remain open.
