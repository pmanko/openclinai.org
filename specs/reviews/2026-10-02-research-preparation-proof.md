# Research Preparation: Partial Proof

Observed 2 October 2026 local time, continuing into 3 October UTC. This is
implementation evidence for the [environment roadmap](../reusable-environments-roadmap.md),
not a setup procedure or recipient acceptance. The tested working diff is based
on umbrella `5116e8602bc9f216a2b1f385fa930e87a761d0d1`; component pins are unchanged.

## Implemented and Tested

- Core-only preparation reuses native builds and Compose services. It does not
  configure providers, provision accounts, warm a model, or call chat.
- Build staging, ESM importmap/registry generation and module-cache refresh use
  the selected project and artifact directory instead of another stack's names.
- Preflight rejects foreign checkout/project/service labels, wrong writable
  mounts, shared/orphaned volumes, missing retained database storage and occupied
  selected ports. Docker inspection failure is not an empty deployment.
- Selected process inputs retain the installed Java/Corepack toolchain without
  accepting ambient application configuration. A missing Java runtime fails
  before services start.
- Explicit seed rejects unsafe database/user identifiers and a failed backend
  stop. It uses selected credentials/artifacts, requires both consumer modules,
  bounds API waits and does not restart/reset because a wait expires.
  The standard OpenMRS demo login is the default; existing installations may
  supply a credential override without changing an account's password.
- Selected research imports require the preset's exact HIV archive identity in
  addition to the existing portable-corpus/provenance checks. No other dataset
  is an accepted fallback.
- Native backend startup supplies `referencedemodata.createDemoPatients=false`
  through OpenMRS's existing extra-properties merge before Java starts. A native,
  network-isolated image test verified both first-install server properties and
  existing runtime properties; unrelated settings were preserved.
- Seed captures deterministic clinical-table content before startup and refuses
  a success receipt if that content changes. Authentication rejection is terminal,
  not treated as a reason to wait, restart, reset or change a password.

Command doubles check routing and failure handling, not clinical operation.
The native scripts remain implementation helpers: public environment lifecycle
commands are not yet available.

## Actual Disposable Observation

The ignored `selector-proof-a` installation uses its own Compose project,
volumes, staged modules, frontend files and ports. No existing research stack was
adopted. A real port conflict was detected before startup and resolved only in
the disposable private settings.

Pinned QueryStore and ChartSearchAI source builds and the native frontend build
succeeded. Core containers reported healthy. The initial clinical API redirected
to initial setup, however, and logs showed a fresh-schema duplicate-index error.
Health alone did not establish authentication or application readiness.

After verifying no patient/user/encounter/observation records existed, the known
demo archive was explicitly imported with checksum/provenance verification. Its
initial restored counts were 5,334 patients, 14,322 encounters and 428,036
observations. This establishes import, not successful application startup.

**Original fresh research setup failed:** the stock distribution configured
`referencedemodata.createDemoPatientsOnNextStartup=50`. A Java thread dump showed
`ReferenceDemoDataActivator.started -> DemoVisitGenerator -> DemoObsGenerator ->
saveObs` blocking application startup. Counts later reached 5,384 patients,
14,756 encounters and 429,667 observations. QueryStore also logged missing
embedding-property failures. These observations are retained as failures, not
silenced or accepted as baseline parity.

The seed wait was stopped after diagnosis. No success corpus receipt was written;
there was no automatic restart or reset. The disposable backend was stopped to
retain evidence and prevent further generation; its storage was retained. Other
stacks, existing accounts/settings and all component sources remained unchanged.

## HIV-Only Correction and Retest

The required baseline is the existing HIV corpus; this was not an unresolved
choice of data. The historical import/provenance tooling was retained, not
replaced with a generator or a different dataset.
The installed Reference Demo Data 2.6.1 bytecode also recognizes the case-sensitive
runtime property `referencedemodata.createDemoPatients=false`; the stock environment
property converter lowercases names. The correction uses the native
`openmrs-extra.properties` path instead; its real startup script was exercised
for both new and existing runtime files.

Only `selector-proof-a` was rebuilt and explicitly restored from the same verified
44,057,876-byte archive. Backend image ID:
`sha256:470d0d0d2ee7e9963764e7b72f6f987639440c87e9161e48ce42361af75ecfad`.
The effective runtime property was exactly `referencedemodata.createDemoPatients=false`.
Restored and post-start counts remained 5,334 patients, 14,322 encounters and
428,036 observations.

The pre-start and post-start SHA-256 of deterministic data-only exports was:
`1f55a802be072114bf246a9c453d371f665c7dcdda500d052a84571de8c11b30`.
The comparison covered patient, patient_identifier, patient_program,
patient_state, person_address, person_attribute, encounter, encounter_provider,
obs, orders, drug_order, test_order, conditions, allergy, allergy_reaction and
visit. This checks record contents, not only aggregate counts. One explicit
selected-backend restart reached the native session API again, retained the
generator-off property and produced the same clinical-content digest. No other
installation was restarted or imported.

**Authentication correction, 3 October 2026:** the imported baseline accepts the
standard `admin` / `Admin123` demo login. The earlier rejection was caused by an
incorrect password override in the disposable instance settings. Removing that
override restored the existing shared default; no database account was changed.
An authenticated session returned `authenticated=true`, both required modules
reported started, no module reported stopped, and the FHIR Patient API returned
HTTP 200 with a patient record. An administrator bootstrap or a new credential
policy was unnecessary. The seed helper again accepts the standard demo defaults
as well as explicitly configured credentials.

QueryStore embedding configuration and bundled model provisioning remain open;
neither provider or the browser workflow is claimed ready. The earlier failed
seed did not write a success receipt; the later read-only checks do not invent one.

## Validation and Remaining Delivery

### Full backup and isolated restore, 3 October 2026

The native full-backup helper initially failed on macOS Bash 3.2 because
`set -u` rejects an empty exclusion-array expansion. Its guarded expansion now
passes zero exclusion arguments correctly. The existing real MariaDB integration
test failed before this correction and passed afterward. The test now supplies
the native helper's required global-property table and verifies both the clean
corpus and full-backup restores, including module records and settings.

Using the corrected helper on `selector-proof-a`, a checksum-verified full backup
restored into an empty database in the separate `selector-proof-b` project.
All 244 tables restored. Deterministic data exports matched across 26 selected
clinical, user/role, settings, conversation/audit and migration tables. The HIV
counts remained 5,334 patients, 14,322 encounters and 428,036 observations.
Conversation tables in this preparation-only instance do not substitute for the
later required populated conversation/reload test.

Stopping B with the native `stack-down.sh` (without volume deletion) and restarting
its database with `stack-up.sh --wait --no-build db` preserved its clinical digest.
A retained the same backend container ID/start time, healthy state and clinical
digest. No other project was restarted, imported or adopted. Private backup and
instance files remain ignored; neither their contents nor credentials are published.

The real round-trip test was run explicitly, separately from the default suite:

```sh
RUN_DOCKER_TESTS=1 uv run --project targets/validation-harness --extra dev \
  python -m pytest -o addopts='' tests/operations/test_dump_loaded_integration.py -q
```

It passed using `/bin/bash` 3.2.57. The default suite again passed 48 umbrella and
246 operational tests, with the Docker test deselected there. Workspace checks and
`git diff --check` passed. This proves backup/restore and bounded isolation, not
the historical-schema upgrade: that remains the next check before migration.

### Historical migration collision, 3 October 2026

Read-only inspection of the retained Git history recovered the original operation
at `f0c9a542758b53f6f90958f9fd2f8dc732233b84` (also present in
`8a46914deae2d5a10e6a450374f5740722418bfc`). Its `chartsearchai-009` changes
`chartsearchai_chat_message.audit_log_id` to `ON DELETE SET NULL`. The selected
ChartSearchAI `8622f1b5c8995ac5361dd634705434ba65fe2fae` instead uses that same
identifier, author and file path for the two reference-slice audit columns.
This confirms the conflicting operations in Ross's supplied test report.

A disposable in-memory H2/MySQL-mode diagnostic used Liquibase 4.32.0 from the
module's resolved dependencies. It applied the current production changelog,
constructed the representative historical state with the two columns absent,
and executed the recovered foreign-key operation through Liquibase under its
original identity. Attempting the current production changelog again failed:

```text
ValidationFailedException
liquibase.xml::chartsearchai-009::openmrs
was: 9:d781912f8a1c94b8e5b9fa2d1d31906b
now: 9:e8f2c324e2b3ae73733f62d15881021d
```

The diagnostic asserted the validation failure and that both columns remained
absent. It touched no installed database. This is a reproduction, not a passing
upgrade or the permanent product regression test; actual OpenMRS startup/version
handling and a MariaDB upgrade remain required.

**Proposed repair, awaiting owner approval:** accept only the exact known
historical checksum as additional migration metadata, retain the existing SQL
and applied-history rows, and add a new guarded forward migration for missing
columns. Unknown checksums must still fail. No reset, blanket checksum clearing,
wildcard acceptance or replay of the old foreign-key operation is proposed.
Verify that normal module upgrading executes the repair despite same-version
snapshot deployment before claiming it works in OpenMRS.

This needs a narrow exception to the roadmap's prohibition on editing an applied
changeset. [Liquibase's checksum guidance](https://www.liquibase.com/blog/what-affects-changeset-checksums)
describes exact `validCheckSum` metadata plus a new conditional repair; accepting
the checksum alone does not apply the missing schema change. The source remains
unchanged while that exception is awaiting approval.

### Earlier preparation checks

- Separate self-review checked selected-resource routing, private-value handling,
  native helper reuse, baseline enforcement and the distinction between command
  doubles, native properties and live clinical-content proof. It is not an
  independent final code-qa or release approval. No component pin/source was
  changed; model tuning, clinical permissions and rubric changes are out of scope.
- `make test`: 48 umbrella unit tests and 246 operational tests passed; one
  existing slow opt-in test deselected.
- `python3 scripts/check_workspace.py`: passed.
- `git diff --check`: passed.
- New startup tests failed on the old helper before its correction and passed
  afterward. Native first/existing-property conversion and the actual restored
  clinical-content comparison are separate from command-double tests.

The pushed implementation is `1c3fa31d140fad7ff53bf6a255b3655bac32297e` in
[umbrella PR #5](https://github.com/pmanko/openclinai.org/pull/5). Its workspace,
operational and GitGuardian checks passed, but the
[pinned source-pair CI job](https://github.com/pmanko/openclinai.org/actions/runs/37097306288/job/111129753661)
failed. `RemoteLlmEngineResponseSizeBoundTest.contextOverflowIsReportedThroughBlockingAndStreamingHttpCalls`
expected `ChartTooLargeException` in its streaming case and received `APIException`
with `HTTP/1.1 header parser received no bytes`. The ChartSearchAI API suite
reported 2,949 tests, one failure and 59 skips; subsequent frontend steps did not
run. The product pins are unchanged. The automatically triggered
[run for documentation head `19ab29e`](https://github.com/pmanko/openclinai.org/actions/runs/37097812744)
subsequently passed both the source pair and frontend checks with those same pins.
The earlier HTTP failure's cause remains unexplained; the later pass does not
establish a fix. No product source or test was changed to dismiss it.

Read-only account inspection found the archive administrator at user ID 1 with
system ID `admin`, no username and `retired=0`. The checked-in user transform
passes through the source password and salt rather than establishing the private
settings password. The successful standard-demo login above verifies its existing
credentials. Private connection settings are not password-reset instructions.

The native-property check is reproducible from the umbrella root with the built
backend image; it has no application volume mounts or network access:

```sh
docker run --rm --network none --user 1001 --entrypoint /bin/bash \
  --mount "type=bind,source=$PWD/tests/operations/fixtures/openmrs-startup-properties.sh,target=/tmp/proof.sh,readonly" \
  harness-openmrs-backend:3.6.0-temurin /tmp/proof.sh
```

Prove the historical-schema upgrade on the restored disposable database, then complete
account/provider readiness. No public installer, migration of
Ross's installation, seven-account/context, provider/browser, run/report or
recipient walkthrough is declared complete by this slice.

OpenMRS's own [performance-test instructions](https://github.com/openmrs/openmrs-contrib-performance-test)
document the next-startup demo-generation property. The installed bytecode,
distribution configuration, thread dump and database observations above are the
evidence for this specific failure; upstream documentation is not substituted
for runtime proof.
