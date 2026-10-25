# Catalyst on OpenELIS 3.3.0, and both stacks on one Hub (25 October 2026)

Evidence for [local-stacks.md](../local-stacks.md), checkpoints 2 and 3. Everything
ran on one machine: the ChartSearchAI stack from the
[25 October restart](2026-10-25-local-stack-restart.md), the Catalyst MVP in its
isolated Compose project, one model router on port 8077. The umbrella pinned
Catalyst at the top of three stacked Catalyst branches (1bd5a68).

## Catalyst branches

| Branch | Change | Found by |
| --- | --- | --- |
| `result-freshness` (3fe7c36, on main) | The table contract takes the freshness the analytics adapter reports (data source, dialect, relation count); the provenance panel shows dialect and relation count | The smoke: every preview execution failed contract validation with a 502 on Catalyst main, because the contract still required a pipeline watermark the adapter stopped reporting; route tests used a fake with the old shape |
| `openelis-3.3.0` (6a9395f, 0259f98) | The MVP pins the itechuw 3.3.0 release images by digest and openelis-docker's 3.3.0 tag; the seed accepts 3.3.x; the seed creates the warehouse database before waiting for the Data Pipes controller | The first boot: "3.2.1.11" was 15 July images by digest plus a June openelis-docker commit on floating `develop`; on a fresh warehouse the controller exited before the seed created its database |
| `shared-hub` (1bd5a68) | `MVP_HUB=external` starts the MVP without its own Hub, the gateway reaches the running Hub at `MVP_GATEWAY_HUB_URL`, the health gate checks that Hub's router setting and image revision; overrides can be layered with `:` | Checkpoint 3 |

Catalyst checks at 1bd5a68: 58 analytics contract tests; on `result-freshness` the
gateway's 422 tests, ruff format and lint, and the UI's 309 tests and type check. The
new freshness test failed against the old contract.

## Umbrella changes (#23)

- The MVP override mounted the OpenMRS HIV source registry from `catalyst-sources/`
  under the umbrella root, a path left from the harness layout; the gateway exited on
  the missing file. It now mounts `targets/validation-harness/catalyst-sources/openmrs-hiv`.
- `scripts/catalyst-smoke.py` and `make catalyst-smoke` (9 unit tests).
- `CATALYST_HUB=shared` in `scripts/catalyst-mvp.sh` and
  `compose/catalyst-mvp-shared-hub.override.yml`.

## Catalyst alone (checkpoint 2)

| Step | Command | Result |
| --- | --- | --- |
| Fresh state | `make catalyst-mvp-reset` | MVP databases and warehouse removed |
| Boot | `make catalyst-mvp-external` | OpenELIS 3.3.0 up; seed wrote 96 patients and 1,152 results over 9 test types; backfill to HAPI and 1,152 specimen timestamps normalized; then stopped on the controller race fixed in 0259f98 |
| Seed and health | `make catalyst-mvp-seed`, `make catalyst-mvp-health` | Data Pipes FULL run completed, 10 views registered; health gates passed |
| Smoke | `make catalyst-smoke` | health passed; "How many patients are there?" became `SELECT count(DISTINCT t1.id) AS count_patients FROM openelis.patient_flat AS t1`, SQL in 11 to 22 s, one row |

Recorded provenance (`targets/catalyst/logs/mvp-provenance.json`): `openelisVersion`
3.3.0, openelis-docker cf6017c, application image `sha256:b69b2cb7…`, database
`sha256:4a85cb29…`, FHIR `sha256:d224b8de…`, profile `catalyst-query-e4b-qwen14b`
(writer gemma-e4b, reviewer qwen2.5-14b).

Two of eight generations of the smoke question came back `rejected` by the
profile's review before the run of five consecutive passes recorded above. The
smoke now prints the rejection's message; the rejection rate is the query
profile's, not the stack's.

## Together on one Hub (checkpoint 3)

| Step | Command | Result |
| --- | --- | --- |
| Start | `CATALYST_HUB=shared make catalyst-mvp-up` | the MVP's own Hub removed; the gateway on `catalyst-mvp-isolated-network` and `compose_default` with `MED_AGENT_HUB_BASE_URL=http://harness-med-agent-hub:8080` |
| Catalyst smoke | `CATALYST_HUB=shared make catalyst-smoke` | health passed, Hub recorded as `external:harness-med-agent-hub` at 9ac9d43; question answered with one row in 12.5 s |
| ChartSearchAI smoke | `make chartsearch-smoke` | checked Answer, one resolved citation, stored; 40.3 s to the Answer (10.6 s alone, while the router also held the Catalyst profile's models) |

One Hub container served both: the ChartSearchAI smoke's runtime identity and the
Catalyst health gate both name 9ac9d43.

## Harness suites against the shared stack

One harness checkout (c36c354), run after the smokes.

| Suite | Run | Result |
| --- | --- | --- |
| Catalyst `catalyst-notebook-t094-v1` (`harness-cli catalyst run`) | `72000c49-c4fa-45be-a997-c725e7a65f29` | 12 results, 3 passed, 1 skipped (manual-only), 0 infrastructure failures |
| ChartSearchAI `review-smoke` (`make validate-run SET=review-smoke`) | `b457ab49-9549-44f3-8775-e344cae2a274` | 4 turns, no errors; Answers `checked`, `edited`, `needs_review`, `checked`; 53 to 87 s |

The Catalyst failures are not the shared stack's:

- `base_execution_succeeded` (6): the suite's saved base query reads
  `analytics.lab_result_fact_v1`, a view of the retired PostgreSQL analytics engine;
  Spark reports it missing. The same scenarios' generated successors ran against
  `openelis.observation_flat`. The suite's base SQL needs the warehouse's views
  (harness).
- `hub_capacity_evidence` (6): the Hub reports no prompt token count for the
  qwen2.5-14b reviewer (`rendered_prompt_unavailable`) while it counts gemma-4-12b's
  (Hub).

`make validate-run` recreates `harness-med-agent-hub` with the run's temporal anchor;
the Catalyst gateway kept reaching it by name.

## After the Catalyst merge

Catalyst #142 to #144 merged as 7498348, whose tree is the tested head plus #141's
documentation; #23 pins it. On that pin `make chartsearch-smoke` passed (checked
Answer, one resolved citation, Hub 9ac9d43). `CATALYST_HUB=shared make
catalyst-smoke` passed its health gate three times and failed its question three
times, for the model's output rather than the stack: once the profile's review
rejected its own repair ("review repair failed deterministic lint"), and twice the
writer declared `count_patients` a `string`, so the table builder refused the
integer Spark returned (`Row 0 column count_patients does not match string`, 502).
Three further generations declared it `integer`. Across the day the default
profile (writer gemma-e4b, reviewer qwen2.5-14b) answered this question 17 times:
12 times with correctly typed SQL (9 executed, all with one row), 3 times rejected
by its own review, and twice with the count declared a string.

## Not done

- Catalyst #142 to #144 are open; #23 pins #144's head until they merge.
- Checkpoint 1's fresh-setup and upgrade cases.
