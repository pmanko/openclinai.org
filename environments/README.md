# Research Environments

OpenClinAI owns setup and updates. The validation harness runs experiments against
an already-prepared service and produces reports; it does not manage installations.

ChartSearchAI research uses only the verified HIV archive named in its preset.
The umbrella backend disables OpenMRS's stock demo-patient generator on every
boot. Starting/updating must preserve the imported corpus; importing/resetting is
explicit. Missing data is a setup failure, not a reason to generate other patients.

**Current implementation:** configuration selection and read-only status only.
Fresh setup, startup, updates and account provisioning through this interface
are not available yet. The intended setup starts from the verified HIV baseline,
not an old installation or database backup.

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

The verified HIV baseline uses the standard OpenMRS demo login: `admin` /
`Admin123`, already supplied by the shared defaults. No credential setup or
password reset is needed. Override `CHARTSEARCH_ADMIN_USER` and
`CHARTSEARCH_ADMIN_PASSWORD` only when an existing installation uses a different
login; these settings select credentials to use, not a new password to assign.

Supported overrides are the existing settings in `.env.chartsearch.example`, plus
database/index ports, database credentials/name, backend tag, timezone/anchor and
the optional warmup patient identifier. Unknown keys fail rather than being passed
to a service. Credential overrides belong in the private settings file, not
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
`artifacts/environments/<name>`. Native Compose container names and writable mounts
follow that selection; read-only prompts and profile files still reference the
recorded component checkout. Status lists the actual rendered names and mounts.
The native `chartsearchai-local.sh --prepare-core` helper now supports the selected
Compose services and artifact paths without configuring providers or importing
chart data. It is under disposable testing, not a public research setup command.
Existing stacks with another project name are not adopted or changed by inspection.
The environment selector still does not start an application. Native preparation
and HIV-only restart have disposable test evidence; the complete installer,
account provisioning and provider/browser walkthrough remain unfinished.

## Research Accounts and Setup Layers

The preset's account manifest is carried over from the reviewed source of
[setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148)
at `2b3b1fd0a112b3a3710cda45211212ae7d90c96f`, without obsolete study-tier metadata.
It defines clinical officer, nurse, pharmaceutical technologist, adherence counsellor,
health records officer, doctor and peer educator accounts. **No accounts are
provisioned by the current commands.** Doctor/Nurse inherited permissions must be
inspected when provisioning is implemented; these are not production least-privilege
accounts or an automatic role-based instruction policy.

The planned setup uses ordered layers: verified HIV baseline, native application
setup, then scenario additions such as these accounts and research settings.
Baseline metadata records the archive checksum/size and authorized project package
location. Selection currently does not download, import or apply any additions.

Saved additions must declare what they create or change and use existing tools
and application APIs. Repeating setup must not duplicate accounts, reset passwords
or reload the dataset; conflicting changes must be reported rather than silently
overwritten. The source HIV archive remains unchanged. Other scenarios can reuse
the baseline and select their own declared additions, without another database
dump or installer framework.

Fresh setup does not require a backup, old-schema repair or adoption of Ross's
previous installation. Ordinary start/update must not reset the new environment;
an explicit reset recreates only the selected disposable setup. See the
[implementation roadmap](../specs/reusable-environments-roadmap.md) for the
remaining implementation and recipient checks.
