# Appointments fresh-import startup failure: root cause (13 October 2026)

Code-trace analysis of the failure that blocks `make chartsearch-research-setup`
on a fresh HIV import. It is reasoned from the exact sources the stack runs (core
`master` at `5eb8cba`, Liquibase 4.32.0, Appointments 2.1.0, Billing 2.5.0, the
reference application distribution at `2806159`) and from this repository's
history. A synthetic [reproduction](#reproduction) on the pinned distribution
image later the same day confirmed the mechanism and the stopgap fix; the HIV
package itself was not available to the author.

## Summary

Fresh import fails because OpenMRS core `2.9.0-SNAPSHOT` no longer runs its own
Liquibase pass when the stored `core.version` is unchanged (TRUNK-6418, January
2026). That pass used to be the first Liquibase call on the startup thread, and it
created Liquibase's thread-bound root scope with a resource accessor wrapping
`OpenmrsClassLoader`, which can see every module. Without it, the root scope is
created inside the first module whose Liquibase runs and is bound to that module's
class loader for the life of the pooled thread. Core's `DatabaseUpdater` then lists
unrun changesets for the next module *before* entering its own module-scoped
accessor; for a changeset that already ran and is `runOnChange="true"`, Liquibase
recomputes the checksum, which for `<sqlFile>` means opening the file through the
scope's accessor. Appointments 2.1.0 has six such changesets, the HIV dump carries
their `liquibasechangelog` rows, and the 6 October switch of the base image to
`nightly-chartsearch` changed the installed Appointments and Billing versions, so
both modules' Liquibase ran again for the first time under the new core. Billing
ran first and claimed the thread's root scope; Appointments then looked for
`patientPastAppointments.sql` in Billing's jars, which is exactly what the log in
[PR #9](https://github.com/pmanko/openclinai.org/pull/9) showed.

Earlier environments never met all four conditions at once: stock core 2.8.x
always ran its own pass first, retained volumes skip module Liquibase entirely, and
an empty database has no already-ran changesets to checksum.

## Symptom

`scripts/seed-local.sh` restores the dump into a recreated `openmrs` schema,
restarts the backend and then fails its module check with Appointments not started.
PR #9 reports that the installed Appointments archive contains
`patientPastAppointments.sql` while the startup log searched Billing's resources.
The Liquibase message for this case is
`The file patientPastAppointments.sql was not found in the configured search path:`
followed by one line per URL of the class loader the accessor wraps
(`liquibase/util/FileUtil.java:45-50`, `ClassLoaderResourceAccessor.java:63-80`).
When those URLs are Billing's `.openmrs-lib-cache` jars, the accessor was built
from Billing's module class loader.

## Mechanism

1. **Core skips its Liquibase pass when `core.version` is unchanged.**
   `Context.startup` runs core Liquibase only if
   `isCoreSetupOnVersionChangeNeeded()` (`Context.java:1069-1072`), which with the
   default `optimized.startup=true` compares the `core.version` global property
   with `OPENMRS_VERSION_SHORT` (`AdministrationServiceImpl.java:1017-1027`).
   `DatabaseUpdater.updatesRequired()` has the same early return
   (`DatabaseUpdater.java:281-300`). Both arrived in TRUNK-6418 (`f7708fe`,
   7 January 2026) and exist only on `2.9.0-SNAPSHOT`; branch `2.8.x` calls
   `updatesRequired()` unconditionally from `checkForDatabaseUpdates`
   (`Context.java:1331-1334` on `2.8.x`).
2. **Module Liquibase is also gated on version change.** `startModuleInternal`
   runs a module's `liquibase.xml` only when `isModuleSetupOnVersionChangeNeeded`
   is true (`ModuleFactory.java:693-696`), that is when core changed or the
   `module.<id>.version` global property differs from the installed version
   (`AdministrationServiceImpl.java:1033-1050`). On `2.8.x` every module ran
   Liquibase on every boot (`ModuleFactory.java:701` on `2.8.x`).
3. **Liquibase's scope is per thread and its default accessor is the thread's
   context class loader at first use.** `Scope.getCurrentScope()` lazily creates a
   root scope per `InheritableThreadLocal` scope manager and gives it
   `new ClassLoaderResourceAccessor()` (`liquibase/Scope.java:95-122`), which
   captures `Thread.currentThread().getContextClassLoader()`
   (`ClassLoaderResourceAccessor.java:24-26`). A thread created after its parent
   has a scope inherits the parent's current scope; a thread created before, or
   one whose parent never touched Liquibase, builds its own.
4. **`DatabaseUpdater.executeChangelog` lists unrun changesets outside its own
   scope.** It sets the thread context class loader to the module's loader
   (`DatabaseUpdater.java:211`), builds the `Liquibase` object with the correct
   composite accessor for parsing (`:215`, `:461`), then calls
   `StatusCommandStep.listUnrunChangeSets` (`:217-218`) and only afterwards enters
   `Scope.enter` with the module-scoped accessor for validation and execution
   (`:228-232`). TRUNK-6295 (`7b6c77a2`, February 2025) added that `Scope.enter`
   for execution and left the status call outside it. The same ordering is in
   `2.8.x` (`DatabaseUpdater.java:218-234` on `2.8.x`) and in
   `getUnrunDatabaseChanges` (`:709-710`).
5. **Listing unrun changesets reads `sqlFile` bodies for already-ran
   `runOnChange` changesets.** `listUnrunChangeSets` enters a child scope with only
   the database set (`StatusCommandStep.java:115-124`), so the resource accessor is
   the root scope's. `ShouldRunChangeSetFilter` recomputes the checksum of any
   changeset that already ran and has `runOnChange="true"`
   (`ShouldRunChangeSetFilter.java:62-83`); `SQLFileChange` opens the file through
   `Scope.getCurrentScope().getResourceAccessor().getExisting(path)`
   (`SQLFileChange.java:102-117`), which throws `FileNotFoundException` when the
   accessor cannot see it (`ResourceAccessor.java:219-222`), wrapped into
   `UnexpectedLiquibaseException` (`SQLFileChange.java:164-178`). A changeset that
   has not run yet is accepted without a checksum, so nothing is read at listing
   time.
6. **Appointments has exactly this shape and the dump keeps its rows.**
   `api/src/main/resources/liquibase.xml` in Appointments 2.1.0 declares six
   `runOnChange="true"` changesets whose only change is `<sqlFile>`
   (`liquibase.xml:358-380` and following). `scripts/dump-loaded.sh` strips
   `liquibasechangelog` rows and `module.<id>.version` markers for ChartSearchAI
   and QueryStore only (`dump-loaded.sh:128-155`); every other module's rows and
   version markers travel with the dump.
7. **Module starts share one pooled thread and the first Liquibase user claims
   it.** Each module starts through `Daemon.startModule`, a task on
   `Executors.newCachedThreadPool()` (`Daemon.java:132-134`, `:364-379`,
   `OpenmrsThreadPoolHolder.java`). Startup submits them one at a time, so an idle
   pool thread is reused. The first module on that thread whose Liquibase runs
   creates the root scope with its own `ModuleClassLoader` as the accessor's class
   loader. A `ModuleClassLoader` resolves resources from its own jars, its required
   modules and its aware-of modules only (`ModuleClassLoader.java:823-889`);
   Billing 2.5.0 neither requires nor is aware of Appointments
   (`billing/omod/src/main/resources/config.xml:29-43`). `OpenmrsClassLoader`, by
   contrast, searches every loaded module's class loader
   (`OpenmrsClassLoader.java:208-222`), which is why the pre-TRUNK-6418 root scope
   never failed this lookup.

Putting it together on a fresh import under the current images: core sees
`core.version` unchanged (or, if the dump lacks it, runs its pass on the startup
daemon thread), Billing's and Appointments' stored versions differ from the installed
ones, Billing's Liquibase runs first and binds the module thread's root scope to
Billing's loader, Appointments' listing step checksums
`global-property-past-appointments-sql-09022021` and its siblings, the file lookup
goes through Billing's jars, Liquibase throws, `runLiquibase` wraps it as
`ModuleException("Unable to update data model using liquibase.xml.")`
(`ModuleFactory.java:952-975`), and Appointments is recorded as not started with
that message, which is what the seed script prints.

## Why there were no issues before

| Period | Backend | Core | What happened on start |
| --- | --- | --- | --- |
| Before 30 September | Stock reference application 3.6.0 | 2.8.4 from the distribution | Core ran `updatesRequired()` and its changelog on every boot before any module, so the module thread inherited a root scope wrapping `OpenmrsClassLoader`; every module's Liquibase ran every boot and resolved its files. |
| 30 September to 6 October (`d1073e7`) | 3.6.0 base rebuilt on Temurin | `2.9.0-SNAPSHOT` war overlaid, newest snapshot at each build | Existing volumes kept `core.version` and every `module.<id>.version` equal to the installed versions, so neither core nor any module ran Liquibase. The 3 October smoke ran on such an environment and therefore could not expose this. |
| From 6 October (`b3ddf4f`) | `nightly-chartsearch` base (Appointments 2.1.0 release instead of the 2.1.0 snapshot of 18 March 2025; Billing 2.5.0 instead of 2.2.0; Core 2.8.10 in the distribution) | Same overlay | The next fresh import restored a dump whose Appointments and Billing version markers no longer matched, so both modules' Liquibase ran under the new core for the first time, with the ordering above. |

A truly empty database (the upstream first-install path) never hits this because
no changeset has run yet, so nothing is checksummed at listing time. This is why
the defect in step 4 has survived upstream since 2025 and only surfaces on an
upgrade-style start of a module with already-applied `runOnChange` `sqlFile`
changesets.

## Trigger conditions

All four must hold:

1. Core does not run its own Liquibase pass before modules on the thread that
   starts modules (current `2.9.0-SNAPSHOT` with `optimized.startup=true` and an
   unchanged `core.version`, or a module thread that did not inherit the startup
   thread's scope).
2. A module's Liquibase actually runs (its `module.<id>.version` differs from the
   installed version, or core changed).
3. That module has `runOnChange="true"` changesets using `<sqlFile>` whose rows are
   already in `liquibasechangelog`.
4. Another module's Liquibase ran first on the same pooled thread.

Condition 4 depends on the topological sort of module dependencies and otherwise
on `File.listFiles()` order of the modules directory
(`ModuleFactory.java:177`, `:311-345`), which is filesystem dependent. The same
dump and images can therefore fail on one host and pass on another, which is the
"instability" observed.

## Proven and inferred

Proven from source: steps 1 to 7, the version and date facts in the table, the
Docker Hub push dates (`nightly-chartsearch` re-pushed 13 October 20:21 UTC,
`nightly` 10 October, `3.6.0` 11 March), and the Appointments changelog shape.
Proven by the reproduction below: the failure, its dependence on which module
runs Liquibase first, and the stopgap.

Still inferred for the HIV case: that Billing claimed the scope there (PR #9's
description of the log is the only evidence) and the value of `core.version` in
the dump. The clean-start proof on the real HIV package settles both.

## Reproduction

Run on 13 October against the pinned backend image
`openmrs/openmrs-reference-application-3-backend@sha256:92cd19c4…`, whose war
reports `openmrs.version.short=2.9.0-4cc6f8` (Core 2.9.0-SNAPSHOT, built
13 October) with Appointments 2.1.0 and Billing 2.5.0, on MariaDB 10.11.7. The
distribution's ChartSearchAI and QueryStore snapshots were removed, as the
umbrella image does. Each run restarted the same database and data volume.

| Run | State before start | Result |
| --- | --- | --- |
| First install | Empty database | 31 modules started; six Appointments `sqlFile` changesets recorded |
| A | Every `module.<id>.version` set to an old value; `core.version=2.9.0` unchanged; image default optimized startup | Appointments not started: `Unable to update data model using liquibase.xml`, caused by `The file patientPastAppointments.sql was not found in the configured search path`, listing only emrapi's `.openmrs-lib-cache` jars and the webapp's libraries |
| B | Same reset; `OMRS_EXTRA_OPTIMIZED_STARTUP=false` | 31 modules started; no search-path errors; runtime properties contain `optimized.startup=false` |
| C | Ordinary restart of B, no version change | 31 modules started |

Run A names emrapi rather than Billing: whichever module first runs Liquibase on
the startup thread claims the scope, which is the order dependence described
under trigger conditions. Both runs reached a healthy backend within the same
polling interval, so the stopgap's extra Liquibase checks did not lengthen
startup measurably on this machine.

The reproduction script and its logs are not retained in the repository; the
commands are those of an ordinary `docker run` of the image with the compose
file's backend environment, followed by
`UPDATE global_property SET property_value='0.0.0-repro' WHERE property LIKE 'module.%.version'`
before each restart.

## Confirmation steps

On a host with Docker and the HIV package, if `make chartsearch-research-setup`
still fails with the stopgap removed:

```sh
docker logs harness-openmrs-backend 2>&1 | grep -n -A12 "patientPastAppointments.sql was not found"
docker exec harness-openmrs-db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" openmrs -e "
  SELECT property, property_value FROM global_property
   WHERE property IN ('core.version','module.appointments.version','module.billing.version');
  SELECT id, filename FROM liquibasechangelog WHERE id LIKE '%past-appointments%';"
```

Expected: the search-path lines name Billing's `.openmrs-lib-cache` jars; the
version rows differ from the installed modules; the Appointments rows exist.
Then set `OMRS_EXTRA_OPTIMIZED_STARTUP=false` on the backend service and restart:
Appointments should start, because core's pass now runs first and the module
thread inherits a root scope that wraps `OpenmrsClassLoader`. One module order
check is also worth recording: `ls -U artifacts/openmrs/modules` on the failing
host versus a passing one.

## Fix options

- **A. Upstream core fix (root cause).** In `DatabaseUpdater.executeChangelog`,
  move the `listUnrunChangeSets` call inside the `Scope.enter(scopeValues)` block,
  or wrap it in `Scope.child` with the composite accessor built from the module
  class loader; apply the same to `getUnrunDatabaseChanges` (`:705-711`). This is
  a few lines, has no behavior change for the first-install path, and belongs in
  the [OpenMRS contribution stream](../openmrs-contribution.md) as a TRUNK ticket
  with the reproduction log attached. Tracked in that stream's target path.
- **B. Umbrella stopgap: `OMRS_EXTRA_OPTIMIZED_STARTUP: "false"`** on the backend
  service in `compose/openmrs-2.8-refapp.yml` (`startup-init.sh:162-170` maps it to
  `optimized.startup=false`). This restores the `2.8.x` ordering: core lists and
  applies its changelog on every boot before modules, every module runs Liquibase
  on every boot, and the module thread inherits the right scope. Cost: slower
  boots, the same cost the stack paid before 30 September. It also removes the
  snapshot-drift hazard below. **Applied** in the backend service's environment,
  with the reason in the compose comment; verified by runs B and C above.
- **C. Pin the moving parts.** `compose/Dockerfile.backend` took the newest
  `2.9.0-SNAPSHOT` war at every build on top of a `nightly-chartsearch` base that
  moves daily. This does not fix the defect but makes "fresh install" mean one
  reproducible artifact set, which Ross's installation needs regardless.
  **Applied:** gateway, frontend and backend base are pinned by digest, and the
  separate war download is removed because the pinned backend image already ships
  Core 2.9.0-SNAPSHOT build `4cc6f8`. A bump changes all three digests in one
  reviewed change.
- **D. Not fixes.** Stripping Appointments' `liquibasechangelog` rows or version
  markers from the dump would re-execute its changesets against HIV data; retrying
  startup only re-rolls condition 4; and the `2.8.10` core in the distribution is
  not an option while ChartSearchAI and QueryStore require `2.9.0`.

## Second hazard: snapshot drift is invisible to optimized startup

`OPENMRS_VERSION_SHORT` comes from the manifest's `Specification-Version`, which
is `openmrs.version.shortnumericonly` (`api/pom.xml:361`,
`OpenmrsConstants.java:79-81`), so every `2.9.0-SNAPSHOT` build stores
`core.version=2.9.0`. With `optimized.startup=true`, a newer snapshot that adds
core changesets is treated as unchanged on an existing database and the changesets
are never applied, and modules are skipped for the same reason. An unpinned
overlay therefore produces databases whose schema depends on which snapshot
happened to be newest when the image was last built. Option B neutralizes this,
and option C makes each change deliberate; both are applied.

## Sources

- OpenMRS core `master` `5eb8cba` (13 October 2026) and branch `2.8.x`:
  `api/src/main/java/org/openmrs/util/DatabaseUpdater.java`,
  `api/src/main/java/org/openmrs/module/ModuleFactory.java`,
  `api/src/main/java/org/openmrs/module/ModuleClassLoader.java`,
  `api/src/main/java/org/openmrs/util/OpenmrsClassLoader.java`,
  `api/src/main/java/org/openmrs/api/impl/AdministrationServiceImpl.java`,
  `api/src/main/java/org/openmrs/api/context/Context.java`,
  `api/src/main/java/org/openmrs/api/context/Daemon.java`,
  `api/src/main/java/org/openmrs/util/OpenmrsThreadPoolHolder.java`,
  `web/src/main/java/org/openmrs/web/Listener.java`, `startup-init.sh`,
  commits `f7708fe` (TRUNK-6418) and `7b6c77a2` (TRUNK-6295).
- Liquibase 4.32.0 sources (`liquibase-core-4.32.0-sources.jar`, the version in
  core's BOM on both lines): `Scope`, `ClassLoaderResourceAccessor`,
  `ResourceAccessor`, `StatusCommandStep`, `ShouldRunChangeSetFilter`,
  `SQLFileChange`, `FileUtil`.
- Bahmni Appointments tag `2.1.0` (`f8ff203`); OpenMRS Billing tag `2.5.0`.
- Reference application distribution `distro/pom.xml` at tag `3.6.0` and at
  `2806159`; Docker Hub tag metadata for `openmrs-reference-application-3-backend`.
- This repository: `compose/Dockerfile.backend`, `compose/openmrs-2.8-refapp.yml`,
  `scripts/seed-local.sh`, `scripts/dump-loaded.sh`, commits `d1073e7` and
  `b3ddf4f`, PR #9.
