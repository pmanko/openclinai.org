# Reusable Environments, Evaluations and Demos

**Status:** Ross setup contract approved. Read-only configuration/status selection
is implemented; lifecycle, migration and recipient acceptance remain open.
**Reviewed against source:** 2 October 2026.
**Publication scope:** Documentation publication is authorized; runtime execution
and changes to Ross's installation remain separate approvals.

Make OpenClinAI straightforward to set up, update, evaluate and demonstrate
without a separate installer or deployment branch for each researcher. Ross's
ChartSearchAI setup is the first delivery. Apply the same operating conventions
to the existing Catalyst setup, without making a Catalyst overhaul a prerequisite
for Ross's handoff. Future clients should reuse these conventions where useful.

Ross's next evaluation should use the revamped umbrella setup. There is no urgent
evaluation deadline requiring continued work on the old preview. Keep that
installation and its evidence intact as migration input and a recovery option,
not as the recommended ongoing research environment. Do not invest in a parallel
legacy setup or rush the new handoff to sustain old-branch evaluations.
Keep the pause short by making the reviewed port and instructions the immediate
priority. Ross's usable ChartSearchAI handoff must not wait for Catalyst alignment,
broader tooling cleanup or completion of every umbrella workstream. Reuse his
tested setup work, fix demonstrated migration gaps and defer unrelated improvements.

This is the detailed environment workstream under the [main roadmap](roadmap.md).
[Architecture](architecture.md) owns component boundaries. This document owns the
shared setup sequence and acceptance below; product behavior and experiment
definitions stay in their respective repositories. Saving this roadmap does not
authorize deployment, data migration, PR merging or report/demo publication.

## Delivery Goal

A researcher can select a documented ChartSearchAI or Catalyst setup, prepare or
resume it without losing existing work, run a chosen experiment against that exact
target, and record a real demo. Another researcher can understand and reproduce
the setup from tracked configuration and captured run inputs, without the original
author's machine, private paths or coding-assistant history.

Completion requires both usable paths, verified preservation/isolation, a tested
Ross handoff, and the final code-quality, security and scope review below. Saving
this document, a green unit suite or opening a PR does not meet that goal.
The earlier Ross handoff is a separately verified deliverable, not a claim that
the entire reusable-environment roadmap is complete.

## 1. Ownership and Scope

| Concern | Owner | What is saved |
| --- | --- | --- |
| Shared environment | OpenClinAI umbrella | Preset, component pins, native configuration references, setup/update commands and readiness checks |
| Product behavior | Product repository | APIs, model profiles, prompts, account-context transport and native build/runtime commands |
| Experiment | Validation harness | Scenarios, prompt/model comparisons, evaluator settings, captured inputs/outputs and review records |
| Demo | Umbrella coordinates existing browser tests | Selected environment and journey, recording options, preparation disclosure and publication |
| Personal installation | Local instance directory | Selected preset, ports, model paths, endpoint overrides and private credentials |

A preset describes a reusable setup; an instance is a particular installation of
it. `chartsearch-research` can support Ross's installation and other researchers.
It is not one preset per person, role, model, question or Git branch.

The harness must remain runnable against an already-prepared local or remote
target without the umbrella, Docker, Git or product source trees. Environment
preparation must not become a harness dependency. QueryStore, OpenMRS and FHIR
Data Pipes remain application-specific dependencies, not requirements for every
future client.

## 2. Current Starting Point

These are inspected implementation facts, not claims of recipient acceptance.

| Existing source | Useful behavior or gap | Planned treatment |
| --- | --- | --- |
| [ChartSearchAI defaults](../.env.chartsearch.example) and [ignore rules](../.gitignore) | Shared defaults and private local overrides already exist | Consolidate selection and preserve local values; do not add a parallel configuration store |
| [OpenMRS Compose](../compose/openmrs-2.8-refapp.yml) | Fixed `harness-*` container names; persistent named volumes and checkout-relative mounts | Make names, ports, storage and commands consistently instance-specific; explicitly migrate existing installations |
| [Stack startup](../scripts/stack-up.sh) and [ChartSearchAI preparation](../scripts/chartsearchai-local.sh) | Native lifecycle and preparation exist, but assume one local setup | Reuse these functions with explicit instance settings; separate first initialization from ordinary startup/update |
| [Catalyst wrapper](../scripts/catalyst-mvp.sh) and [override](../compose/catalyst-mvp-isolated.override.yml) | Startup, seed, restart and reset are separate; project/container prefixes are configurable | Adapt this established pattern; preserve native Catalyst lifecycle and data semantics |
| [Umbrella Makefile](../Makefile) | `validate-run` currently starts Hub before calling the harness | Make running against a selected target independent of preparation; name any combined operation explicitly |
| [Clinical runner](../targets/validation-harness/harness/validate/runner.py) and [Catalyst run configuration](../targets/validation-harness/harness/catalyst/run_config.py) | Inputs and run configuration are already captured | Supply environment identity through existing provenance/configuration inputs; do not create another report system |
| [Playwright configuration](../targets/validation-harness/tests/e2e/playwright.config.ts) and [demo journey](../targets/validation-harness/tests/e2e/specs/chartsearchai-demo.spec.ts) | Target URL, video options and presentation pacing exist | Reuse real browser workflows and make the selected environment explicit |

Ross's previous setup is in [harness PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148).
Its account-context companion is [ChartSearchAI fork PR #33](https://github.com/pmanko/openmrs-module-chartsearchai/pull/33).
Treat them as source material to inspect and port selectively, not branches to
merge wholesale into the new architecture. The umbrella does not yet carry the
complete setup/accounts workflow. The current selected backend also needs the
account-context work reconciled with its newer provider contracts.

## 3. Configuration Layout

Proposed paths below do not imply implemented commands or existing files:

```text
environments/
  README.md
  chartsearch-research/
    preset.json
  catalyst-workbench/
    preset.json
.local/environments/                 # ignored, private machine settings
  ross/
    settings.env
artifacts/environments/              # ignored, generated preparation evidence
  ross/
    receipt.json
```

`environments/README.md` is the operator entry point: available setups, prerequisites,
commands, expected outcomes and troubleshooting. Link it from the root README.
Keep product setup details with their owners instead of copying those guides.

### Shared presets

Use small JSON files and the existing standard-library tooling. A preset identifies
its human-readable purpose, application family, existing native configuration
files, reviewed data baseline, required account provisioning and compatible
experiment/demo references. Paths resolve relative to the umbrella root, not the
operator's working directory. Validate required fields and referenced paths before
any mutation; unknown presets or unsupported options fail with a useful message.

Presets select existing behavior; they do not contain executable scripts, a new
workflow language or a second copy of Compose, model profiles, prompts or scenarios.
Only expose variation actually needed by ChartSearchAI and Catalyst. A future
client can add its native setup integration and, separately, a harness adapter
when evaluation through an existing adapter is insufficient.

The reviewed baseline is an immutable asset identity, checksum and documented
retrieval location. Do not commit database dumps, model weights or credentials.
Download/import is explicit; a resumed environment does not fetch or reseed data
because its software revision changed. Existing harness-owned fixture/transform
utilities can be invoked without moving deployment ownership back to the harness.

### Private instances

Each instance records its preset once in `settings.env`, along with explicit
machine-specific overrides. Precedence is native/shared defaults, then selected
instance settings, then documented command options. Pass only supported overrides;
do not let an unrelated checkout's environment file silently select this target.
Do not overwrite local settings on startup/update, and do not execute arbitrary
content from an environment file as shell code.

An instance consistently selects its Compose project, service lookup, ports,
networks, storage and artifact directory. Prefer Compose service lookup over fixed
container names. Check concrete port/storage conflicts before changing a stack;
never stop an unrelated installation. A model endpoint may be explicitly shared
or externally managed. Environment isolation does not imply isolated GPU capacity.

Credentials are private, excluded from receipts/reports and stored with restricted
permissions. Generic instructions must work without a particular coding assistant.
The thin assistant entry point links to those instructions rather than defining
another setup procedure. Preserve user-managed prompt changes; repeatable study
prompt variations belong with their experiment and reference native product inputs.

The handoff must support the original one-request experience: "Update my OpenClinAI
evaluation environment and keep my data." Provide a thin assistant entry point
that follows the same maintained guide and deterministic commands available to a
human. It identifies the instance, proposes the exact update, preserves data by
default, and asks before any reset or new tool installation. Test this from a new
assistant session with no private conversation history; a script list alone does
not satisfy this requirement.

### Generated receipts and run records

After preparation, save the selected preset, configuration identity, actual source
revisions/running image identities, data identity, account-setup revision, model
configuration, service addresses and individual readiness outcomes. A receipt
reports observations, not desired state or a clinical approval. Missing provenance
is explicit. Check an old receipt against the selected running target before using
it as evidence; the mere presence of a file is not readiness.

Git and existing component pins track software history. Do not add a hand-maintained
version registry. Record actual image identities rather than assuming a mutable
tag identifies the tested build. Keep private operator details in local receipts;
pass only appropriate metadata into existing harness run records and redact before
publication. Resolved configuration inspection must not print secrets.

## 4. Operator Workflow

Extend existing Make/script entry points with one consistent environment selector.
The following is the intended interface, not a set of commands available today:

```sh
make environment-up ENV=ross
make environment-status ENV=ross
make environment-update ENV=ross
make validate-run ENV=ross SET=role-smoke
make demo ENV=ross SCENARIO=chartsearch-basic VIDEO=on
```

The examples name planned selections, not existing experiment or demo IDs.
Finalize supported names in the first implementation review, then update examples
and tests together. Do not maintain old and new public command surfaces indefinitely.

`environment-update` is the canonical preserve-first software update operation.
For the normal shared installation, "latest" means the latest fetched umbrella
`origin/main` commit and that commit's exact component pins, not the latest branch
in every submodule. Resolve the target commit once and show it before changing
anything. Before the work lands on main, preview instructions supply an explicit
published tested commit; the updater must not silently advance a moving preview
branch or switch a preview installation to main.

Inspect dirty/ahead/diverged checkouts and ignored-file collisions before changing
source. Stop with actionable details rather than reset, auto-stash, overwrite or
discard work. Use the selected umbrella pins, native build/migration commands and
readiness checks; preserve local settings and data. A failed update never triggers
a reset, reseed or provider fallback. Reset remains a separate confirmed operation.

| Operation | Required behavior |
| --- | --- |
| Create instance settings | Select a preset and validate prerequisites; no data import, software installation or stack takeover |
| Initialize | Explicitly prepare a genuinely new installation and import the selected baseline; refuse to overwrite existing state |
| Start | Resume the selected environment without seeding, resetting or changing user configuration |
| Status | Show the instance, preset, service URLs, data/model identity and specific readiness gaps; never repair implicitly |
| Update | Show intended software/configuration changes, preserve data/settings/accounts, and use native migrations and selective builds |
| Run experiment | Resolve the selected target and required capabilities, then invoke the independent harness; no deployment or global provider change |
| Record demo | Run the real journey with optional pacing/video; disclose preparation and retain actual failures |
| Stop | Stop only the selected environment; retain its data |
| Reset | Explicit confirmation naming the instance and affected data; retain a verified backup when preserving existing research state is required |

Readiness means the selected application, authentication, data and requested
capabilities work. Do not require every possible service or a high-quality model
answer. Distinguish startup failure, incomplete data, model failure and an adverse
evaluation result. Use health checks and observed progress, not blind sleeps or
unbounded polling; indexing should not restart simply because a wait expires.

Shared endpoints/accounts can still interfere. Preserve the clinical runner's
sequential execution where sessions share patient/account identity. Experiments
must not change Ross's active manual session or silently reset provider settings.
Use separate test identities or explicit scheduling where necessary, without
building a distributed scheduler.

Warmup is optional testing/demo preparation, not a general product optimization.
Separate cold preparation from measured warm operations. Keep original timing and
disclose accelerated recordings; no cached or substituted answers masquerading as
live output. Model quality findings remain visible and are not setup blockers.

## 5. Delivery Sequence and Review Points

### Tight implementation iterations

Work in the following order, using reviewable commit groups within the umbrella
PR and only necessary companion PRs. An iteration is a tested behavior change,
not permission to implement the rest of the plan at once.

| Iteration | Bounded deliverable | Required exit evidence |
| --- | --- | --- |
| 1. Select and inspect | Final preset fields, private instance settings, read-only resolved configuration/status and migration inventory; no startup or data changes | Precedence/invalid-input/redaction tests; two sample configurations resolve owned resources; owner approves the contract and migration approach |
| 2. Prepare and preserve ChartSearchAI | Existing lifecycle scripts operate on the selected instance; necessary confirmed upgrade fix only | Fresh setup, second-run preservation and old-data upgrade/restore on a disposable copy; no account-context or model-behavior rewrite in this slice |
| 3. Restore research accounts and context | Seven accounts and necessary account-context companion changes on current product contracts | Repeat provisioning/login, preserved credentials, role/location transport and persistence tests; both-provider browser happy path and explicit failure handling |
| 4. Run and hand off ChartSearchAI | Priority delivery: selected target/provenance, one small experiment and recorded browser journey, published preview and tested instructions | ChartSearchAI-scoped acceptance and code-quality/security/scope review pass; owner approves migration before Ross changes his installation, then recipient findings are recorded; Catalyst work is not a prerequisite |
| 5. Reuse with Catalyst | Existing Catalyst lifecycle follows the same selection/status conventions; one existing experiment and browser journey | Native setup and retained-state proof, bounded real run/report, demo evidence and a targeted isolation check; no new Catalyst product feature |
| 6. Close with independent review | Review the complete diff and exact tested companion heads against this roadmap | All required acceptance rows pass; code-qa, security and scope findings resolved; required CI checked at exact heads; owner accepts final handoff |

Before each iteration, name the acceptance rows being addressed, affected files
and exact tests/commands in the PR's current work note. Establish the baseline;
write failing regression checks before fixing a demonstrated defect. Prefer
behavioral assertions over source-string checks. A double can verify command
routing/no mutation; it cannot prove an application works.

At each exit, record the tested commits, commands, actual results, artifact paths,
findings and remaining work. Run affected native checks and the umbrella checks;
perform a separate review pass against the selected rows before proceeding. Do
not rerun unrelated expensive model matrices after every documentation or parser
change. Reuse evidence only when its tested inputs and relevant code are unchanged.

Stop the affected work at a failed required exit check or a material scope change;
report the concrete issue and proposed correction. Do not silently weaken criteria,
add a compatibility bridge, or begin unrelated remediation. Owner review is
required at the contract decision, before migration of existing research state,
and at final handoff. Other iterations need their recorded exit evidence, not an
extra approval for every small edit. These checkpoints do not require a PR per step.

### Confirm the migration inputs

Inventory the current umbrella commands and the useful files in Ross's preview:
guide, setup/update helpers, account definitions, assistant skill and test evidence.
For each, record reuse, adaptation or omission with a reason in the implementation
PR. Inspect the actual selected product heads and open companion PRs; do not assume
an old branch is compatible or a new browser test fixes Ross's earlier error.

Document the small preset fields, command-to-native-script mapping and selected
baseline before implementation. An already-verified local baseline package is a
valid initial input; creating a new distribution service is not a prerequisite.
Record its identity/checksum and give Ross a tested authorized retrieval route.
The current data-tooling ownership decision remains with the main roadmap.
Review this bounded design with the owner;
do not introduce a generic framework to settle unresolved details.

### Approved First Setup Contract

The owner approved this contract on 2 October 2026. Configuration/status selection
is now implemented; it is not an available installer. It uses the layout above
without moving product or experiment configuration into another format.

| Saved input | Contents and authority |
| --- | --- |
| `environments/chartsearch-research/preset.json` | Identifier, label, application, paths to the existing Compose/default files, reviewed baseline identity, required seven-account setup, and references to existing experiment/browser inputs |
| `.local/environments/<name>/settings.env` | Preset selection and only documented machine overrides: ports, model directory/endpoint and private connection credentials; parsed as data, never sourced as shell |
| Git checkout | Umbrella revision and its six component pins; no second software-version list in the preset |
| Native product configuration | Model profiles, prompts and provider behavior remain in their owning products; preserved user changes are reported, never overwritten to make setup pass |

Start with ChartSearchAI only. A second ChartSearchAI instance proves isolation;
Catalyst adoption follows later. The read-only resolver validates the name, keys,
paths and selected references before invoking any native operation. Its public
output contains selected paths/resource identities and configuration origins, not
credentials. Unknown inputs, path escape, unsafe permissions and unsupported
settings fail without writes. Shared defaults, private instance settings and
documented command overrides have that precedence; ambient shell variables and
another checkout's `.env` cannot silently choose the instance.

The first executable commands are `make environment-config ENV=<name>` and
`make environment-status ENV=<name>`. They inspect, never start, install, build,
seed, repair or create accounts. Status separates observed services from untested
authentication, provider response and browser behavior. Lifecycle commands from
section 4 remain unavailable until their preservation tests pass. The existing
fixed-name launchers must not be presented as instance-aware before adaptation.

For the next lifecycle slice, reuse the native Compose file and preparation/build
helpers, remove fixed container-name assumptions, and use Compose project/service
lookup throughout. Instance artifacts and private settings must stay separate;
the host model server can be explicitly shared. Do not introduce a generic task
runner or a copied Compose/model/scenario configuration.

Test fresh and repeat startup plus historical-schema upgrade on disposable
instances first. Adopting an existing installation is a separate reviewed step:
inspect its actual project, mounts, settings and schema, verify a restorable full
backup, and present the exact storage mapping before any stop or upgrade. Do not
infer ownership from a checkout name or rename volumes implicitly. Ross's current
installation remains untouched until that migration is approved.

The [source inspection](reviews/2026-10-02-ross-migration-inventory.md) records
which old setup files are useful, current gaps, the verified local baseline and
unverified recipient inputs. The [operator guide](../environments/README.md) states
which commands exist and their limits. Resolver/security tests and native read-only
inspection establish selection only, not lifecycle isolation or recipient readiness.

### Deliver ChartSearchAI research setup

Implement the first preset and thin command selection over existing operations.
Port the seven study accounts: clinical officer, nurse, pharmaceutical technologist,
adherence counsellor, health records officer, doctor and peer educator. Reapplying
setup must preserve existing credentials and unrelated users. Keep both bundled
and Hub provider paths available. Role/context metadata is not proof of role-based
authorization or automatic adaptation of model instructions.

For Ross's existing installation, first inspect ownership, Compose project/volume
names, data identity, configurations and component versions without mutation.
Present the migration and backup/rollback steps before stopping it. Carry over
verified storage and private settings intentionally; never bypass ownership checks
or infer that a renamed checkout owns the old volumes. A code rollback alone is
not a database rollback.

Reproduce the reported preserved-database audit-column/migration failure using a
retained snapshot or representative historical-schema fixture in a disposable
instance; an unavailable old export must not block starting that regression work.
Inspect Ross's actual current schema before his migration and reject unsupported
states before mutation. If the defect remains, add a forward product migration
and an old-schema regression test; do not edit an applied changeset or solve it
by forcing a reset.
Reconcile account-context transport with current provider/persistence contracts in
ChartSearchAI. Investigate any remaining In-Depth failure from its captured error,
not merely the event name. Keep model-quality changes out of this migration.

Use the supported Python toolchain, retain progress visibility during first-time
indexing, and avoid redundant builds where unchanged inputs can be verified.
Record preparation separately from recipient browser acceptance. Pause for owner
review before migrating Ross's working installation.

### Apply the convention to Catalyst

Add a preset referencing the existing Catalyst wrapper and configuration. Preserve
its explicit seed/reset operations, retained data and product-owned source setup.
Select a bounded existing journey for smoke/demo proof; this task does not reopen
all Catalyst feature acceptance or implement a new data source.

Verify that operations on one instance do not stop or alter the other. Demonstrate
the shared conventions without requiring simultaneous model inference on limited
hardware. Catalyst work may follow Ross's usable handoff rather than delay it.

### Connect experiments, demos and the handoff

Supply target connections and relevant receipt metadata to existing clinical and
Catalyst runners. Reuse captured inputs and offline reporting. Keep experiment
selection independent of environment preparation; show selected scenarios/arms and
expected workload before starting a costly comparison.

Reuse browser fixtures for actual account login, conversation or workbench steps,
persistence and visible evidence. Recording is an option, not a second fake demo
implementation. Finish the generic cheatsheet, a Ross-specific migration note that
links to it, and a concise message explaining what is verified and what remains.
Update the shared project handoff materials only with verified instructions; do
not upload private settings or credentials.
The recipient message asks Ross to pause further old-setup evaluations and wait
for the tested new setup, not to switch to an unverified branch. Resume research
on the revamped environment after the migration/readiness walkthrough; preservation
of the old installation does not count as completion of the new handoff.

### Ross handoff readiness and instructions

Ship the tested ChartSearchAI preview as soon as its own acceptance is satisfied;
do not wait for iterations 5 and 6. Before that handoff, apply the final-review
procedures to the ChartSearchAI changes and their companions. Mark Catalyst-only
and whole-program checks pending, not passed. Preservation, account/context,
provider/browser behavior, credential safety and accurate instructions remain
required; speed comes from bounded scope and reuse, not skipped safeguards.

For this handoff, the required rows in section 7 are Ownership, Configuration,
Preservation, Migration, Isolation, Accounts and context, Product operation,
Provenance, Demo and the ChartSearchAI portions of Experiment independence,
Portable evidence and Final review. Handoff is first recorded as ready for recipient
testing, then passes only after the recipient walkthrough. Catalyst operation and
the Catalyst portions of shared rows are later completion criteria, not Ross blockers.
Use a second disposable ChartSearchAI instance for the early isolation check; a
working Catalyst deployment is not required to prove resource targeting.

The handoff includes one generic guide plus a short migration note containing:

1. The exact published umbrella branch/commit and companion pins to use, required
   repository access, prerequisites and a tested initial checkout/update command.
2. Separate steps for adopting Ross's existing installation and for a genuinely
   fresh setup, including backup, baseline retrieval/checksum and confirmation
   points. Do not present a reset as the ordinary upgrade path.
3. Copyable commands for start, status, update, stop and one small evaluation;
   expected URLs/output; how to select bundled versus Hub and access the seven
   accounts securely; where prompt customizations are preserved or configured.
4. A short walkthrough: login as two roles, inspect session context, ask/follow up,
   inspect evidence and In-Depth state, reload, and retain a run/report. Distinguish
   setup failures from model-quality findings.
5. Known limitations, non-destructive recovery steps and how to send a redacted
   diagnostic receipt/results. Point Ross's assistant to the same maintained guide
   and repository instructions, not a separate undocumented procedure.

Validate the commands from the published preview before sending them. Report any
actual blocker with the next concrete action; do not leave Ross with an indefinite
pause or promise a completion date before the migration inputs have been checked.

## 6. Pull Request and Repository Plan

Open one non-draft umbrella PR carrying the reusable setup and Ross migration,
using a short-lived `codex/` branch. If the ownership/documentation changes remain
unmerged, declare the exact dependency and target the containing branch; retarget
after it lands. Do not silently add runtime work to the documentation-only PR.

Use companion PRs only where behavior must change: ChartSearchAI for account
context or a confirmed migration defect, harness for connection/provenance input
gaps, and other products only for demonstrated native setup requirements. Inspect
the existing account-context PR before deciding whether to update or supersede it;
explain that decision, preserve attribution and avoid duplicate review paths.
Follow the current [contribution model](roadmap.md#contribution-model), not historical
integration-branch instructions from the old setup.

Publish component commits before updating umbrella pins to reachable revisions.
Local review can use clearly identified unmerged source; upstream merging is not
a prerequisite for a recipient-testable preview. Keep reviewer checks, runtime
proof and merge/release status separate. Close the old setup PR only after the
replacement is verified and closure is approved. PR merging, destructive migration,
and publication remain explicit owner decisions.

## 7. Acceptance and Evidence

Every row is required for final completion. Evidence must identify its tested
revision and environment; proposed tests or source inspection alone cannot stand
in for a requested live observation. Narrow smoke fixtures and negative cases are
enough where listed; do not expand this into a full clinical benchmark.

| Requirement | Unambiguous pass condition | Verification |
| --- | --- | --- |
| Ownership | Presets reference existing native configuration; independently installed harness runs without umbrella, Git, Docker or product checkouts | Diff/owner review plus existing source-free runner isolation checks; no second deployment or version registry |
| Configuration | Defaults, instance and explicit options resolve in that order; unknown selections, malformed inputs and missing referenced files stop before side effects; updates resolve one approved umbrella revision and its exact pins | Resolver/update tests cover precedence, explicit preview versus main, dirty/diverged source and zero mutations on rejection |
| Preservation | Repeating startup/update retains selected clinical fixture records, existing user credentials/roles, unrelated users, saved conversations and custom settings; initialization refuses existing state | Before/after observations on a disposable installation, including repeat login and conversation reload; migration metadata may change as expected |
| Migration | A retained old snapshot or representative historical-schema fixture upgrades without reset; Ross's actual current schema is checked before mutation; recorded mapping names the correct existing volumes and backup can be restored | Historical-schema regression plus restore/upgrade evidence and recipient preflight before owner-approved migration; unknown schema fails safely rather than being reset |
| Isolation | Two instances resolve distinct application resources and data locations; stopping/updating one leaves the other's selected data and readiness unchanged | Resolved Compose inspection, command-target tests and one bounded real lifecycle check; explicitly shared inference is recorded |
| Accounts and context | All seven accounts authenticate after initial and repeated setup; two distinct role accounts carry their actual role/context through bundled and Hub request/persistence paths; a browser-selected location is retained and absent location stays absent | Account provisioning tests, product transport/persistence tests and representative browser login/turn/reload; no claim of production permission enforcement |
| Product operation | Both providers deliver an answer through the normal UI, follow-up and reload work, and evidence remains inspectable; requested supported In-Depth phases settle and persist their contract-defined state; a controlled failure becomes terminal and is displayed rather than left pending | Separate happy-path and failure-path proof; provider failures alone cannot satisfy the happy path; genuine model withholding/quality findings remain visible |
| Catalyst operation | The selected existing native journey reaches its saved/reloaded result without reseeding on resume | Bounded real journey defined before the iteration; generated SQL can be corrected through normal product controls and the correction is retained |
| Experiment independence | One clinical and one Catalyst smoke run use the selected target; neither performs build, restart, seed, reset or global provider reconfiguration | Routing/no-mutation tests plus actual runs with captured targets; changing an experiment does not rebuild the environment |
| Portable evidence | Both smoke reports regenerate from complete captured run directories while target/evaluator services are inaccessible to the reporting process | Offline report checks using copied artifacts, not the author's current sources or local dataset paths |
| Provenance | Run inputs identify the actual environment/data/model settings; deliberately missing metadata is recorded as missing; stale receipts cannot alone assert readiness | Receipt-to-run contract tests and inspection against actual running target identity |
| Demo | A real browser journey records visible results and limitations; optional recording does not change the requests or assertions | Browser trace/screenshots/video with disclosed warmup/pacing/speed changes and separately retained raw timings |
| Handoff | Generic guide has working setup/update/status/run/stop instructions and no required private paths; a new assistant session can follow one update request using that guide with preserve as default; Ross or a designated recipient records the preview walkthrough | Fresh-session assistant exercise plus recipient observations and exact tested versions; script presence or author-local success alone is insufficient |
| Final review | Code-qa, security, scope, required CI and documentation checks below have no unresolved blocker or missing required proof | Final acceptance matrix and findings ledger reviewed against exact PR heads, then owner acceptance |

For each delivery, update the progress table below with commit/PR and test evidence.
Use focused unit/contract tests for changed behavior and real-path smoke/browser
checks for acceptance. Run the umbrella's required unittest suite and workspace
checker. Review scope, simplicity, meaningful coverage, companion consistency and
documentation before calling it ready. Failed or unrun checks remain visible;
model answer quality and absolute local latency are not infrastructure pass gates.

Run the umbrella checks from its root; add affected product-native tests rather
than using these workspace checks as a substitute:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
git diff --check
```

### Final code-quality, security and scope review

Run [DIGI-UW/code-qa](https://github.com/DIGI-UW/code-qa) procedures against the
complete change and all necessary companion changes, not only the last commit.
Record the revision of the review instructions used. No new tool submodule or
blanket dependency installation is required merely to apply the procedures.

| Review | Required outcome |
| --- | --- |
| Meaningful test coverage | Every changed behavior has an assertion at the appropriate layer; demonstrated regressions fail on the old implementation and pass after the fix |
| Simplicity | No speculative framework, duplicated configuration authority, dead compatibility path or needless dependency remains; native scripts are reused and obsolete consumers updated |
| Spec/code alignment | Presets, commands, README, operator guide, roadmap, examples and assistant instructions describe the shipped behavior; proposed commands are not represented as available |
| Companion and PR hygiene | Necessary PRs are non-draft and cross-linked, bases/dependencies explicit, current mergeability and required check results inspected; pins refer to published tested commits; comments/tests are professional and durable |
| Evidence bundle | Real browser proof and run artifacts identify source versions, setup, observations and limitations; narration does not substitute for captured evidence |

Security is a separate explicit pass, not a presumed consequence of code-qa:

- Test with non-secret sentinel values that credentials cannot appear in resolved
  configuration output, logs, receipts, reports, screenshots or shared bundles.
  Check private files are ignored and access-restricted. Inspect the final diff
  and use available repository secret scanning; do not claim that redaction alone
  proves absence of leaks.
- Reject instance-name/path traversal and shell metacharacter injection before
  operations. Parse settings as data, preserve argument boundaries and test that
  a malicious value causes no command execution or writes outside owned storage.
  Deliberate external model paths remain explicit inputs, not preset traversal.
- Verify baseline checksums before extraction/import and reject corrupt inputs
  without database changes. Preserve existing ownership, reset confirmation,
  backup handling and authentication safeguards; never auto-adopt an unrelated
  stack or expose private endpoints as an incidental setup change.
- Verify research account provisioning does not grant administrative privileges
  accidentally, overwrite unrelated roles/users, or retain bootstrap secrets in
  outputs. Document actual inherited privileges and the limited research scope;
  production least-privilege redesign is not part of this work.

The final scope pass maps every changed file to an acceptance requirement or a
documented necessary dependency. Unmapped changes are removed or submitted for
explicit approval, not rationalized afterward. Confirm that no model tuning,
rubric changes, new clinical authorization claims, new Catalyst feature, cloud
platform or hidden provider fallback entered the implementation. Classify any
pre-existing unrelated finding separately; it cannot justify silently enlarging
this delivery.

Use a separate reviewer when available; otherwise record the review as a separate
self-review, not independent approval. Each finding includes severity, file/line,
reproduction/evidence, resolution and rerun result. No unresolved security, data-loss,
scope or required-behavior blocker may be marked complete. An owner-approved scope
change updates this roadmap explicitly; it is not an unreported test waiver.

Final handoff lists pass/fail/not-run for every acceptance row, exact tested heads,
required CI results, artifact links and residual non-blocking limitations. Required
failures or missing proof mean partial, not done. Check clean tracked changes and
publication of intended commits separately from actual deployment, report publication
and recipient acceptance. These remain distinct facts.

| Delivery | Status | Evidence |
| --- | --- | --- |
| Research and roadmap | Ross implementation authorized | User authorized diligent execution; contract and migration signoffs remain required |
| Select and inspect | Approved and locally verified; publication/CI pending | 39 umbrella unit and 230 operational tests passed (one existing opt-in deselected); two private configurations rendered distinct projects/ports/volumes through real read-only Compose inspection; no test installation started; separate self-review caught and fixed the Make default regression and covered secret-safe output, native reuse, scope and truthful readiness limits |
| Prepare and preserve ChartSearchAI | Not started | Pending tests and recipient-safe migration proof |
| Restore research accounts and context | Not started | Pending account and companion product/browser tests |
| Run and hand off ChartSearchAI | Not started | Pending real run, browser evidence and recipient confirmation |
| Reuse with Catalyst | Not started | Pending bounded native-path proof |
| Final quality, security and scope review | Not started | Pending complete acceptance matrix and owner review |

## 8. Scope Limits and Remaining Choices

No Kubernetes, plugin registry, general workflow engine, new reporting database,
automatic branch-per-study, forced provider switch or blanket rebuild/reindex.
Do not retune models or rewrite evaluation rubrics to make setup pass. Do not move
product specifications into this document or restore the harness as an umbrella.

Before handoff, confirm the baseline asset's authorized retrieval path and checksum
and Ross's actual installation identity. Use an existing verified local package for
implementation testing rather than waiting for new hosting. Inspect the current
account-context PR destination before changing its history. These are concrete migration inputs,
not reasons to design a new storage, identity or deployment platform.

## 9. Research Basis

These sources support the mechanisms below; the ownership and scope decisions are
project choices grounded in the inspected code, not claims made by the sources.

- [Docker project names](https://docs.docker.com/compose/how-tos/project-name/):
  named projects isolate environments; explicit ports, mounts and custom names
  still need consistent instance selection.
- [Compose configuration merging](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/)
  and [resolved configuration](https://docs.docker.com/reference/cli/docker/compose/config/):
  reuse base configuration and bounded overrides; inspect actual resolved paths
  and values without publishing secrets.
- [Compose profiles](https://docs.docker.com/compose/how-tos/profiles/): select
  optional services, not a new experiment or environment inheritance language.
- [Compose readiness](https://docs.docker.com/compose/how-tos/startup-order/):
  distinguish a running container from a ready dependency and application.
- [Docker image pinning](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions)
  and [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/):
  identify actual builds and keep credentials out of shared configuration/evidence.
- [Promptfoo configuration](https://www.promptfoo.dev/docs/configuration/guide/):
  reusable prompts, providers, cases and assertions inform our existing harness
  configuration; adopting another evaluation framework is not proposed.
- [Playwright projects](https://playwright.dev/docs/test-projects),
  [fixtures](https://playwright.dev/docs/test-fixtures) and
  [videos](https://playwright.dev/docs/videos): reuse browser journeys with explicit
  environment/account configuration and optional recording.
- [DIGI-UW/code-qa](https://github.com/DIGI-UW/code-qa): meaningful coverage,
  simplicity, specification alignment, companion review and captured evidence;
  project-specific security and scope checks above remain explicit additions.
