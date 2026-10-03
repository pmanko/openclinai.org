# Reusable Environments, Evaluations and Demos

**Current direction, 3 October 2026:** Deliver a fresh, reproducible ChartSearchAI
research setup for Ross using the verified HIV baseline and seven evaluation
accounts. Reuse native tooling and saved scenario inputs. No old-database
migration, backup restoration or adoption of Ross's old installation is required.

**Implementation status:** Saved configuration and read-only status are implemented.
Native core preparation and HIV-only startup have disposable test evidence. The
public fresh-setup command, account provisioning, account-context integration and
recipient walkthrough are not complete. Planned behavior below is not a claim
that these features already work.

This is the environment workstream under the [main roadmap](roadmap.md).
[Architecture](architecture.md) owns component boundaries; this roadmap owns
setup delivery and acceptance. Product behavior and experiments keep their
existing owners. The [scope audit](reviews/2026-10-02-ross-migration-inventory.md#scope-audit-3-october-2026)
records the removed requirements and their evidence.

## 1. Goal and Boundaries

A researcher can set up a fresh environment from a documented configuration,
use the application, run an experiment against it and retain a reproducible
report or demo. Ross's ChartSearchAI setup comes first. Reuse the conventions
with the existing Catalyst setup afterward; Catalyst work cannot block Ross.

For Ross, carry over useful setup code, account definitions and instructions,
not an old database. There is no need to inspect or repair his old database,
restore a backup, or request an old-installation migration approval. Leave
unrelated installations alone. Normal repeat startup must not reseed data or
reset accounts; that is ordinary setup correctness, not legacy upgrade support.

| Concern | Owner |
| --- | --- |
| Component pins, builds, deployment, saved setup and scenario additions | OpenClinAI umbrella |
| Database structure, APIs, model profiles, prompts and account-context transport | Respective product |
| Evaluation scenarios, comparisons, judging and captured run/report artifacts | Independent validation harness |
| Machine-specific ports, endpoints, model paths and private credentials | Ignored local settings |
| Demo coordination and publication | Umbrella, reusing real browser journeys |

A shared preset is a reusable scenario setup, not a separate installer for every
person, role, question or branch. The harness must still run against a prepared
local or remote endpoint without Git, Docker, the umbrella or product checkouts.
QueryStore and other application dependencies are not universal requirements for
future clients.

## 2. Reproducible Setup Layers

Apply a small, explicit sequence. Do not build a plugin registry, arbitrary-script
runner, database migration framework or general workflow language.

| Order | Layer | Ross setup | Rule |
| --- | --- | --- | --- |
| 1 | Reviewed baseline | The verified HIV archive identified by the preset | Keep the source archive unchanged; verify its checksum and provenance before import into the fresh database |
| 2 | Application setup | Pinned OpenMRS modules and existing provider/QueryStore configuration | Products own their database structure and native setup; disable generated patients before the first application start |
| 3 | Scenario additions | Seven evaluation accounts, roles and required research settings | Apply separately from the baseline through existing provisioning tools and supported application APIs |
| 4 | Optional additions | Only additions explicitly selected by another scenario | Declare their order and affected records/settings; none are needed just to make Ross's setup more general |

The preset selects the baseline and an ordered list of supported additions.
Each addition references a small saved input, such as the existing
[account definitions](../environments/chartsearch-research/accounts.json), and
an existing operation. Extend the current preset narrowly when wiring execution;
its present `files.accounts` reference is not yet a general ordered-additions
implementation. Do not duplicate native configuration or create per-scenario
database dumps.

Each addition must identify what it creates or changes and any prerequisite.
Use stable application identifiers and read back the result. Reapplying the same
input must not create duplicate accounts, reset passwords or rewrite unrelated
records. An unexpected conflict fails with the item and reason; there is no silent
last-writer-wins override. An intentional change to an earlier layer must name
the affected setting/record and expected prior state.

Account setup must not alter clinical evidence. A future scenario that needs
clinical fixture changes must declare those changes explicitly and verify the
resulting records; it must not modify the source HIV archive. Reproducing an
environment means recreating it from the same baseline, component versions and
ordered inputs, not copying somebody's working database.

Record the actual baseline checksum, component revisions, ordered addition
identities/input hashes and individual outcomes in the existing preparation
receipt. This is provenance, not a second version registry or a separate
setup-history database.

## 3. Existing Code to Reuse

| Source | Current behavior or gap | Action |
| --- | --- | --- |
| [Preset](../environments/chartsearch-research/preset.json), [accounts](../environments/chartsearch-research/accounts.json) and [selector](../scripts/environment.py) | Baseline/account references, private settings, read-only config/status and resource preflight exist; account application does not | Extend this path; do not add a parallel installer |
| [Native Compose](../compose/openmrs-2.8-refapp.yml), [startup](../scripts/stack-up.sh) and [preparation](../scripts/chartsearchai-local.sh) | Selected project/artifact paths and core-only preparation exist | Compose the fresh sequence using these helpers |
| [HIV import](../scripts/seed-local.sh), [archive checks](../scripts/verify-portable-dump.py) and [backend initialization](../compose/backend-init.sh) | Verified import and generator-off handling exist | Use the reviewed archive, import before first clinical application startup, then verify actual records |
| [Original setup PR #148](https://github.com/pmanko/clinical-ai-validation-harness/pull/148) | Contains reusable account provisioning, acquisition helpers, guide and assistant instructions | Port only needed behavior; do not copy old ownership or backup/upgrade machinery |
| [Account-context PR #33](https://github.com/pmanko/openmrs-module-chartsearchai/pull/33) | Older provider contracts contain work absent from the selected backend | Adapt the necessary transport/persistence changes in a companion PR |
| [Makefile](../Makefile) | `validate-run` still starts Hub | Remove preparation from selected-target experiment invocation |
| [Clinical runner](../targets/validation-harness/harness/validate/runner.py), [Catalyst run inputs](../targets/validation-harness/harness/catalyst/run_config.py) and [browser journey](../targets/validation-harness/tests/e2e/specs/chartsearchai-demo.spec.ts) | Existing execution, provenance and browser surfaces | Supply the selected endpoint and reuse reporting/recording |
| [Catalyst wrapper](../scripts/catalyst-mvp.sh) and [override](../compose/catalyst-mvp-isolated.override.yml) | Native lifecycle and explicit seeding exist | Reuse later without changing Catalyst product scope |

The [source inventory](reviews/2026-10-02-ross-migration-inventory.md) identifies
the inspected revisions. The [preparation evidence](reviews/2026-10-02-research-preparation-proof.md)
records actual tests, including the unnecessary backup/upgrade investigation.
Those historical observations do not create setup requirements.

## 4. Saved Configuration and Operator Experience

The existing layout remains the starting point:

```text
environments/
  README.md
  chartsearch-research/
    preset.json
    accounts.json
    settings.env.example
.local/environments/<name>/settings.env   # ignored machine-specific values
artifacts/environments/<name>/            # ignored preparation evidence
```

The [operator guide](../environments/README.md) is the single maintained entry
point for people and assistants. A later Catalyst preset follows the same
convention while referring to its native wrapper.

Shared defaults apply first, selected local settings second, and explicit
documented overrides last. Parse settings as data, not executable shell.
Configuration inspection must not expose private credentials. Model profiles,
system prompts and experiment definitions stay with their native owners; do not
copy them into the environment preset. Ross can vary prompts without creating
another installation or introducing an automatic role-to-prompt policy here.

Use the existing standard OpenMRS demo login, `admin` / `Admin123`.
No administrator bootstrap, forced password change or credential-policy approval
is required for this local demo. Document how to access the evaluation accounts
when their existing provisioning is ported. Never publish private overrides or
newly issued account passwords in logs, reports or screenshots. Documented public
demo defaults are not private secrets; this is not a production deployment.

The desired experience is one fresh-setup command after documented prerequisites
and authorized dataset/model acquisition. It selects saved inputs and invokes
native operations in order. Missing inputs must be reported clearly without
partially importing an invalid archive. Reuse acquisition/checksum tooling and
the existing authorized dataset distribution; no new hosting service is needed.
First-time indexing shows progress and bounded failure, not repeated resets.

| Operation | Required behavior |
| --- | --- |
| Fresh setup | Validate prerequisites and inputs, select unused resources, import verified HIV data, prepare applications, apply scenario additions and check readiness |
| Repeat setup/start | Reuse the selected environment; no reimport, duplicate accounts, password reset or implicit provider switch |
| Status | Show actual URLs and separate service, data, login and provider readiness; never repair implicitly |
| Software update | Use one selected umbrella revision and its exact pins with native build/start commands; do not fetch independent submodule heads or reseed |
| Run evaluation | Invoke the independent harness against the selected endpoint without starting/reconfiguring it |
| Record demo | Exercise the real UI; optional recording/pacing does not change requests or hide failures |
| Stop | Stop only the selected environment without deleting its data |
| Explicit reset | Recreate the selected disposable environment from the same recipe after confirmation; no backup/migration subsystem is required |

Only `make environment-config ENV=research` and
`make environment-status ENV=research` are public implemented commands through
the selector today. Publish setup/update/run examples only after they are
connected and tested. Do not present a manual chain of internal helpers as the
finished one-command handoff.

A software update must not discard dirty work or silently change a tested preview
to another branch. Use existing Git/workspace/native commands and a short guide or
thin wrapper; do not build a new branch manager or an old-schema compatibility
system. Native product schema initialization remains product-owned.

Check concrete selected port/resource conflicts without taking over another stack.
Retain the existing bounded ownership checks. A host model endpoint can be shared
explicitly; isolation does not promise independent GPU capacity. Keep warmup
optional and disclose it in demos; no model quality threshold or absolute local
latency target is a setup gate.

## 5. Tight Delivery Sequence

Work within the existing umbrella PR and necessary companions. Before each
iteration, identify the changed files, acceptance rows and tests. At its end,
record exact tested revisions, results and remaining work. Use native checks and
one separate review pass; do not require a new PR or approval for every small fix.
Ask the owner before a material scope change, not to reconsider settled baseline
or demo-login choices.

| Iteration | Deliverable | Exit evidence |
| --- | --- | --- |
| Select and inspect | Saved preset, local settings and read-only status | Input validation/redaction tests and resolved native resource selection; retain existing proof |
| Fresh setup | One entry point reusing native build/import/start/configuration; ordered scenario application | Fresh HIV-only startup and repeat setup with no duplicates, reimport or unintended record changes; failed required step cannot report ready |
| Accounts and context | Port all seven account definitions/provisioning and necessary current-product context transport | Seven real logins; repeated setup; actual roles/location through both providers and persistence; no automatic instruction-policy or authorization claim |
| Research handoff | One small real evaluation/report, real browser walkthrough, generic guide and published preview | ChartSearchAI acceptance and code-qa/security/scope review; then recipient observations |
| Later Catalyst reuse | Same saved-selection convention over the existing native setup | One bounded existing native journey, run/report and recording option; no Catalyst feature rewrite |
| Overall closeout | Review both delivered paths and remaining shared work | Complete acceptance matrix, exact heads, CI and owner acceptance |

### Fresh setup implementation

1. Resolve the existing preset and verify the HIV archive, native prerequisites,
   component files, selected resources and required model/embedding inputs.
2. Reuse native builds and bring up the selected database. Import the verified HIV
   baseline before the first application startup. Generator-off configuration
   must be in place before OpenMRS starts.
3. Start/configure the applications through existing helpers, including QueryStore
   indexing and the supported bundled/Hub provider setup. Do not rebuild/reindex
   unchanged inputs on ordinary repeat startup.
4. Apply the declared scenario additions after their application prerequisites
   are ready. Port the old account provisioner rather than inventing a second
   OpenMRS client. Verify every required account login and effective roles.
5. Report each check truthfully and write the receipt only for observed outcomes.
   A service health check alone is not application or model readiness.

The seven accounts are clinical officer, nurse, pharmaceutical technologist,
adherence counsellor, health records officer, doctor and peer educator. Do not
rewrite shared built-in role definitions to create them. Record actual inherited
privileges; these research accounts do not certify production least privilege.

### Context, browser and handoff

Adapt the existing account-context work to current ChartSearchAI provider and
persistence contracts. Both bundled and Hub paths receive authenticated account
context. Verify two distinct roles and browser-selected location through a turn
and reload; absent location remains absent. Stated role in a prompt is not proof
of authenticated context or permission enforcement.

Exercise both providers through the normal UI: answer, follow-up, inspectable
evidence, requested supported In-Depth state and reload. A controlled failure must
settle rather than remain pending. Diagnose a demonstrated setup/transport failure;
do not tune clinical answers or judging to make the environment pass.

Run one small existing clinical evaluation against that prepared target and
generate its report from captured artifacts. Reuse existing harness independence
and offline-report tests where unchanged; do not rebuild those test systems.
Browser video is optional; capture a trace/screenshots and record any warmup,
pacing or acceleration separately from measured time.

The generic handoff must contain:
- exact published preview/release revision and component pins;
- prerequisites and authorized baseline/model acquisition;
- tested fresh setup, repeat/start, status, update, stop and evaluation commands;
- application URLs, standard demo login, seven-account access and provider choice;
- a role/context, answer/follow-up, evidence, In-Depth and reload walkthrough;
- prompt-customization locations, limitations and redacted diagnostics.

A thin assistant instruction can link to this same guide. Validate the commands
without relying on this conversation; a separately launched assistant session is
not an additional delivery gate. No old-installation inspection or migration note
is needed. Mark the preview ready for recipient testing only after its own checks
pass; record Ross's or a designated recipient's observations separately from the
author's proof. Do not claim recipient acceptance before it occurs.

## 6. Pull Requests and Publication

Use [umbrella PR #5](https://github.com/pmanko/openclinai.org/pull/5) for the
reusable setup and Ross handoff; do not create another umbrella PR per iteration.
Use companion PRs only for necessary product changes, especially account-context
transport. Inspect the existing companion before updating or superseding it,
preserve attribution and explain the chosen review path.

Follow the [contribution model](roadmap.md#contribution-model). Publish component
commits before updating umbrella pins. A tested unmerged preview can be handed
off; upstream merges and release builds are not prerequisites for local review.
Check current CI, mergeability, bases and companion descriptions before declaring
PRs review-ready. Keep PR merging, public report/demo publication and recipient
acceptance separate from code/test completion and subject to their own approval.

## 7. Acceptance

The rows below apply to Ross unless explicitly marked later Catalyst. Test the
actual outcome, not just an exit code or total count. Use focused behavioral tests
for changed code and real application observations for runtime claims. Existing
unchanged evidence may be reused with its tested revision stated.

| Requirement | Pass condition | Evidence |
| --- | --- | --- |
| Native ownership | Setup invokes existing umbrella/product operations; harness remains independent | Diff and command-routing review plus existing source-free harness tests |
| Fresh reproducibility | One documented setup path constructs the fresh selected environment from pinned inputs; no old database/export required | Fresh installation receipt and actual application checks |
| HIV baseline only | Exact archive/checksum and provenance; generator disabled before startup; no extra generated clinical records | Before/after clinical identity/content checks and known patient records through real APIs; invalid archive rejected before import |
| Ordered additions | Saved inputs declare order, prerequisites and affected records/settings; same inputs recreate the same intended state | Fresh and repeat application tests, readback of account/role/settings state and ordered receipt; unexpected conflict fails explicitly |
| Repeat behavior | Same setup and ordinary stop/start do not reimport data, duplicate accounts, reset passwords or erase a created conversation/settings | Repeated setup, native stop/start with retained volumes, seven logins, clinical comparison and conversation reload |
| Resource targeting | Selected resources do not collide with or stop/change another installation | Existing resolver/ownership tests plus bounded native isolation proof; no backup restoration required |
| Accounts and context | Seven logins work; two distinct roles and actual location reach both provider paths and persistence | Provisioning/transport tests and browser turn/reload; absent location stays absent |
| Product operation | Both providers answer through the UI; follow-up/evidence/reload work; supported In-Depth settles; controlled failure is terminal | Browser trace/screenshots and corresponding captured responses |
| Evaluation and provenance | One small clinical run targets the prepared environment without deploying/reconfiguring it; report uses captured artifacts and records actual setup identity | Captured run/report, receipt and existing no-deployment/offline-report checks |
| Instructions | Generic guide's commands work from the published preview without private paths or conversation history | Walkthrough against fresh setup; recipient findings recorded separately |
| Final review | Relevant code-qa, security, scope and CI checks have no unresolved required failure | Findings and pass/fail/not-run matrix for exact tested heads; owner handoff review |
| Later Catalyst reuse | Existing native setup/journey and a small evaluation/report use the same selection conventions | Bounded Catalyst-native proof after Ross handoff; not a Ross blocker |

Reproducibility means agreement on declared clinical and scenario state, allowing
application-generated UUIDs, timestamps and private credential values to differ.
Do not demand byte-identical databases, another full live installation merely for
comparison, or a generic database diff engine. Compare the relevant stable
identifiers and meaningful fields with existing queries/tests.

### Final code-quality, security and scope review

Run the relevant [DIGI-UW/code-qa](https://github.com/DIGI-UW/code-qa) procedures
on the complete change and necessary companions. Record the review revision;
do not install a new tool framework merely to perform the review.

- **Coverage:** changed behavior has meaningful tests; demonstrated regressions
  fail before the fix. Mocks prove routing, not live application readiness.
- **Simplicity:** reuse native operations; no duplicate configuration authority,
  generic workflow/rollback framework or unused abstraction.
- **Alignment:** README, guide, roadmap, examples and assistant instructions
  distinguish implemented commands from plans and all describe the same scope.
- **Security:** private credentials stay out of public output/artifacts; reject
  unsafe paths or executable settings; verify assets; account setup does not
  overwrite unrelated users/roles or silently grant administrative rights.
- **Companions:** non-draft PRs, clear dependencies, published tested pins and
  inspected current CI; professional comments/tests and no unexplained drift.
- **Scope:** every changed file supports a listed requirement. No historical
  database repair, model tuning, rubric changes, production permission redesign,
  automatic role-to-prompt rules, new Catalyst feature or cloud platform.
- **Evidence:** actual browser/run outcomes and limitations, not narrated claims.

Use a separate reviewer when available; otherwise label the separate review pass
as self-review. Report pass/fail/not-run and remaining findings rather than calling
missing proof complete. Prior backup/schema research is not an open handoff gate.

Run the required umbrella checks and affected native tests:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_workspace.py
git diff --check
```

### Recorded Progress

| Delivery | Recorded status | Next work |
| --- | --- | --- |
| Configuration/status | Implemented and tested on the current branch | Extend the same entry point for fresh setup |
| Native preparation/HIV startup | Disposable native build/import, generator-off, standard login and repeat clinical-content checks recorded in the [preparation proof](reviews/2026-10-02-research-preparation-proof.md) | Connect complete public setup including indexing/providers; do not repeat old-database research |
| Accounts/context | Seven-account input exists; application/transport not connected | Port existing provisioner and necessary product changes |
| Browser/evaluation/handoff | Not complete | Both-provider role walkthrough, small run/report, generic instructions and recipient test |
| Catalyst reuse/final overall review | Later work | Follow Ross delivery; do not delay it |

These are recorded results, not a fresh CI or deployment assertion. The final
acceptance matrix must identify the actual tested revisions and observations.

## 8. Research and Reference

These references inform implementation; they do not authorize additional scope.
Use the current native product contracts for product behavior.

- [Docker project naming](https://docs.docker.com/compose/how-tos/project-name/),
  [configuration merging](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/)
  and [resolved configuration](https://docs.docker.com/reference/cli/docker/compose/config/)
  support reuse and inspection of selected native resources.
- [Compose profiles](https://docs.docker.com/compose/how-tos/profiles/) select
  optional services, not a new experiment inheritance system.
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
  distinguishes service startup from readiness.
- [Image pinning](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions)
  and [secret handling](https://docs.docker.com/compose/how-tos/use-secrets/)
  inform reproducible inputs and private overrides.
- [Promptfoo configuration](https://www.promptfoo.dev/docs/configuration/guide/)
  provides an example of reusable evaluation inputs; adopting it is not proposed.
- [Playwright projects](https://playwright.dev/docs/test-projects),
  [fixtures](https://playwright.dev/docs/test-fixtures) and
  [videos](https://playwright.dev/docs/videos) support reusable real browser proof.
- [DIGI-UW/code-qa](https://github.com/DIGI-UW/code-qa) informs the final coverage,
  simplicity, alignment, companion and evidence review.
