# Fresh HIV setup acceptance (13–14 October 2026)

Real-application run of the HIV research setup on the owner's Mac (Apple
silicon, OrbStack 29.4.0, 17 CPUs, 48 GB to Docker), from umbrella `main` at
`b0f1aaf` plus the changes on branch `claude/trusting-bhaskara-367c05`. It
proves the rebuild path, the baseline export, the restore path and ordinary
restart with the real HIV data. Ross's installation is not part of this run.

During the run the owner redirected the design: the cache is the whole finished
setup (OpenMRS database and QueryStore index), restored before OpenMRS starts,
keyed to the HIV dataset rather than to every pin, and distributed through
GitHub Container Registry. The commits on the branch carry that change.

## Inputs

| Input | Value |
| --- | --- |
| HIV dump | `refapp_28_demo.sql.gz`, SHA-256 `f76619b40b45f0261467ceaeb2708b97795d115d99a7b2c2a7c73b38d9a8512a`, matches its provenance; identical in every local copy |
| Distribution | backend `nightly-chartsearch@sha256:92cd19c480b5…`, gateway `@sha256:37b90415f834…`, frontend `@sha256:7a1810630a97…` |
| Core | `core.version` 2.9.0 (2.9.0-SNAPSHOT build in the pinned backend image) |
| QueryStore | `286993cc`, source tree `e1a86f2afdf7c262a710d8d7a82938496b00c1d9` |
| Embedding model | `model.onnx` `6fd5d72fe458…`, `vocab.txt` `07eced375cec…` |
| Elasticsearch | 8.13.4 |
| Chat model | Gemma 4 12B Q8, SHA-256 `f20e7ff1be28c283eeeb18fc895733791c56a5851d5cd3fe9691b7f7d12afa72` (matches the guide) |
| Toolchain | Java 21.0.5, Maven 3.9.16, Python 3.14.7, Node 22.23.2, Yarn 4.2.2 through Corepack, llama.cpp build 10809 |

The Docker volumes predated the run (3 October), so this was a reset of an
existing environment. Disk use inside the Docker VM stayed at 39–40%.

## Rebuild path

### Attempt 1: failed

`make chartsearch-research-setup REBUILD_INDEX=1` (the `main` command), started
22:54:49. Cold builds took 6 min 50 s, stack start with the new distribution
images 2 min 29 s, the frontend bundle 15 s and the dump import 38 s (5,334
patients, 14,322 encounters, 428,036 obs). OpenMRS then refused to start:

```
Validation Failed: 1 changesets check sum
org/openmrs/liquibase/updates/liquibase-update-to-latest-2.9.x.xml::20260519-create-outbox-event-table::rkorytkowski
was: 9:ebe49d65c5b15733bfba29d335163ed3 but is now: 9:60a8857e5c6a61207fc6484dda49d668
```

The HIV dump was taken on 22 July from a Core 2.9.0-SNAPSHOT that had already
applied this changeset. The pinned Core edited it afterwards: `payload` and
`completed_listeners` became `MEDIUMTEXT` instead of `TEXT`. The dump's
`outbox_event` table is empty. The only other unrun Core changeset,
`TRUNK-6549-2026-06-07`, rewrites a log-layout setting. The seed waited out its
health timeout and setup exited with status 2 at 23:15:12.

Fix (`00ea46a`): after importing the dump and before starting OpenMRS, seeding
drops the empty `outbox_event` table and its changelog row so the pinned Core
recreates the table from its current definition; a table holding rows stops the
seed instead.

### Attempt 2: passed

`make chartsearch-research-setup REBUILD_BASELINE=1`, 23:16:25 to 00:47:57
(1 h 31 min 32 s), exit 0.

| Phase | Time |
| --- | --- |
| Module, Hub and backend image builds (warm caches) | 16 s |
| Stack start | 22 s |
| Frontend bundle | 5 s |
| Dump import | 35 s |
| First OpenMRS start, Liquibase and module installs | 49 s; all modules started |
| Patient search reindex | 10 s |
| QueryStore embedding to a complete index with passing drift check | 1 h 29 min (obs alone about 72 min) |
| Provider settings and account check | 3 s; all seven accounts log in |

QueryStore drift after the rebuild: patient 5,334 core / 5,333 indexed, obs
427,897 / 427,890, every other type exact; all within the drift rule.

## State after the rebuild

- Modules (`/openmrs/ws/rest/v1/module?v=custom:(name,started)`): 33 of 33
  started, including Bahmni Appointment Scheduling 2.1.0 and OpenMRS Billing
  2.5.0, the pair from the [Appointments root cause](2026-10-13-appointments-fresh-import-root-cause.md),
  Chart Search AI 1.0.0-SNAPSHOT and Query Store 1.0.0-SNAPSHOT.
- `global_property`: `core.version` 2.9.0, `querystore.backend` elasticsearch,
  `querystore.bootstrap.autostart` true.
- `curl -s localhost:9200/_cat/indices/querystore_*?v`: ten indices, 514,682
  documents, about 2.8 GB.

| Index | Documents | Size |
| --- | --- | --- |
| querystore_obs | 427,890 | 2.4 GB |
| querystore_drug_order | 43,412 | 242.1 MB |
| querystore_encounter | 14,322 | 42.8 MB |
| querystore_visit | 14,250 | 40 MB |
| querystore_patient | 5,333 | 29.1 MB |
| querystore_condition | 4,454 | 25.6 MB |
| querystore_program | 3,921 | 19.7 MB |
| querystore_test_order | 1,095 | 4.2 MB |
| querystore_diagnosis | 3 | 38.9 kB |
| querystore_allergy | 2 | 26.6 kB |

## Baseline export

`make hiv-baseline-export`, 00:48:22 to 00:51:14, exit 0, before any smoke
test. ChartSearchAI held no conversations or audit rows. The snapshot took
76 s, the database dump 4 s and the image build 64 s.

- Local image `openclinai-hiv-baseline:local`, `sha256:aeb788730e63…`
- 2.96 GB: database `openmrs.sql.gz` 45.7 MB, SHA-256
  `3ce2f2e8286eeacb0d5fd9d17ed69a62cc5860bcb1ffab4c86e503dd89af34ab`;
  Elasticsearch snapshot 2.7 GB
- Manifest keyed to dataset `f76619b4…`, the embedding hashes above and
  Elasticsearch 8.13.4; built from umbrella `8494757`

## Acceptance smoke after the rebuild

Logged in as `admin` (Outpatient Clinic) and opened the sample chart. Zabella
Talai Halambe, 28, female, `2428TU-4`, shows active lamivudine, nevirapine and
stavudine (39 medication entries) and 11 vitals and biometrics records through
25 January 2026. ChartSearchAI opened on the chart with Med-Agent Hub and
"Checked answer (12B)". Asked which antiretrovirals the patient is on, it
answered "nevirapine, lamivudine, and stavudine" with high confidence, citing
three 26 January 2026 drug orders sourced from QueryStore, in about one minute
including the model's first load.

## Restore path

### Attempt 1: failed

`HIV_BASELINE_IMAGE=openclinai-hiv-baseline:local make chartsearch-research-setup`,
00:53:08 to 00:55:53, exit 2. The database (28 s) and index (84 s) restored, then
`local-stack-up` stopped on `container harness-openmrs-gateway is unhealthy`.
The gateway's health check passes through to OpenMRS, which the restore had
stopped; the gateway recovered seconds later. Fix (`fb683e0`): the restore path
stops the proxy, gateway and OpenMRS together, and startup brings them back in
order.

### Attempt 2: passed

Same command, 00:57:03 to 01:00:10 (3 min 7 s), exit 0. The package check ran
before any build. Database load 26 s; snapshot restore of 514,682 documents in
10 indices 83 s; stack start and frontend bundle 50 s; verification 9 s: every
module started, the embedding model matched the manifest, patient search
reindexed, QueryStore reported complete, the drift check passed and the tool
printed `514682 documents match the baseline; nothing was re-embedded`
(Elasticsearch recorded no document writes after the restore). All seven
accounts log in.

Smoke repeated: the same chart and records; ChartSearchAI answered a weight
question in 33 s from QueryStore evidence (two weight observations). Its own
citation check flagged one date and labelled the answer "Needs review"; answer
quality is not a setup gate.

## Ordinary restart

`make local-stack-down && make local-stack-up`, 01:03:37 to 01:04:45 (68 s),
exit 0. 33 of 33 modules started, QueryStore complete, index counts equal to the
baseline, zero documents written since Elasticsearch started, the drift check
passed, and the database kept its 5,334 patients, 428,036 obs and the smoke
conversation.

## Checks

- `python3 -m unittest discover -s tests -v`: 23 tests passed.
- `python3 scripts/check_workspace.py`: passed.
- `tests/operations` with the harness environment: 196 passed before the
  restore-ordering fix; `tests/operations/test_hiv_baseline.py` 9 passed after it.

## Not yet proven

- Publication to GitHub Container Registry and a restore that pulls the pinned
  digest on a machine without the local image or existing volumes.
- Ross's installation from the guide.
- Setup still needs Java, Maven, Node and Yarn on the host, and Maven compiles
  the modules against the newest Core snapshot rather than the pinned Core.
