# Local stacks: ChartSearchAI and Catalyst, alone and together

**Thread:** every product stack the umbrella owns runs on one machine on its own and
all together, from the current pins, with one Med Agent Hub, one model router and
one validation harness, and each mode has a smoke that proves it ·
**Status:** ChartSearchAI alone runs at the current pins, its smoke pending #22;
Catalyst runs only with its own Hub and a 2025 OpenELIS pin; nothing runs together ·
**Owners:** umbrella (compose, overrides, launchers, smokes, pins), Catalyst
(its MVP compose and scripts), Hub (serving both products from one container)

## Goal

A developer or reviewer can start the ChartSearchAI stack, the Catalyst stack, or
both, with one command each, and know within a minute that what is running is the
pinned source and answers end to end. Together means shared, not duplicated: one
Hub serves ChartSearchAI's clinical profiles and Catalyst's query profiles, one
router serves the Hub, and the harness runs its ChartSearchAI and Catalyst suites
against whichever stack is up. Catalyst boots the latest OpenELIS Global 2
release, because what it needs from OpenELIS is the `clinlims` database and the
FHIR server, not a particular application build.

Out of scope here: the HIV data setup itself
([local-hiv-environment.md](local-hiv-environment.md)), Catalyst's product journeys
and acceptance ([catalyst-delivery.md](catalyst-delivery.md)), and the demo host at
catalyst.openelis-global.org, which nothing here depends on.

## Where this stands (25 October 2026)

| Mode | Today | Checks on this revision | Pending |
| --- | --- | --- | --- |
| ChartSearchAI alone | `make local-stack-up`: OpenMRS, QueryStore, Hub (`harness-med-agent-hub`, :18081), router (:8077) at the current pins; restarted with data on 25 October ([record](reviews/2026-10-25-local-stack-restart.md)) | `make deployed-sources-check` (artifact identity only) | `make chartsearch-smoke`, the question-level check, lands with [#22](https://github.com/pmanko/openclinai.org/pull/22) |
| Catalyst alone | `make catalyst-mvp-up` builds a second Hub from the same checkout (:18082) on its own network, and clones DIGI-UW/openelis-docker at f118d0a for OpenELIS 3.2.1.11; not set up on this machine | Catalyst's `mvp-health.sh` gate | A question-level smoke (checkpoint 2) |
| Together | Not possible: Catalyst's compose hardcodes `MED_AGENT_HUB_BASE_URL=http://med-agent-hub:8080` and depends on its own Hub service; the two stacks sit on different Docker networks; `scripts/catalyst-mvp.sh` and the health gate assume port 18082 | None | Checkpoint 3 |

OpenELIS couplings in Catalyst (`targets/catalyst`): `env.recommended` pins
`OPENELIS_VERSION=3.2.1.11` and `OPENELIS_DOCKER_REF=f118d0a`; `scripts/mvp-seed.sh`
refuses any version outside 3.2.1.x and seeds `analytics/openelis/seed-openelis-3.2.1.sql`;
`docker-compose.mvp.yml` uses `catalyst/hapi-mtls-proxy:openelis-3.2.1`;
`scripts/mvp-health.sh` gates on the openelis-docker commit. The latest release is
OpenELIS Global 2 3.3.0 (20 October 2026).

## Target path

Each checkpoint is ticked only with a link to its evidence: a merged PR, or a dated
record under [`reviews/`](reviews/) naming the commands run and their results.

### Checkpoint 1: ChartSearchAI alone, proven

- [x] The stack runs at the current pins with data retained: modules, bundle and
      Hub rebuilt, index unchanged, identity probe green
      ([25 October record](reviews/2026-10-25-local-stack-restart.md)).
- [ ] `make chartsearch-smoke` is the setup acceptance step and the boot-check
      finisher; pending [#22](https://github.com/pmanko/openclinai.org/pull/22).
- [ ] Fresh setup (`make chartsearch-research-setup`) and the module upgrade from a
      database set up on the previous heads each end with a green smoke; recorded
      in a dated review.

### Checkpoint 2: Catalyst alone on the latest OpenELIS release

- [ ] Catalyst PR: OpenELIS Global 2 3.3.0. Bump the openelis-docker ref and
      `OPENELIS_VERSION`, lift the 3.2.1-only guard in `mvp-seed.sh`, check the seed
      SQL against the 3.3.0 schema (a new seed file if tables moved), rebuild the
      HAPI mTLS proxy image for the release, and update the health gate's pin.
- [ ] The MVP boots, seeds and passes `mvp-health.sh` on this machine in
      external-router mode (its Hub on :18082, the shared router on :8077);
      recorded in a dated review with the OpenELIS version it reports.
- [ ] `make catalyst-smoke`: Catalyst's own health gate, then one natural-language
      question through the local gateway that returns generated SQL and a result.
      Never against the demo host.
- [ ] Catalyst gitlink moved to the merged 3.3.0 commit.

### Checkpoint 3: together, one Hub

- [ ] Umbrella override (`compose/catalyst-mvp-isolated.override.yml`): the gateway's
      Hub URL points at `harness-med-agent-hub`, its dependency on the MVP's Hub is
      reset, the gateway joins the ChartSearchAI network, and the MVP's own Hub
      service is parked under an unused profile. Catalyst alone still uses its own
      Hub; only the override swaps it.
- [ ] `scripts/catalyst-mvp.sh` in shared mode requires the umbrella Hub healthy
      (`make med-agent-hub-up`) and points the health gate at :18081.
- [ ] Optional Catalyst PR: `MED_AGENT_HUB_BASE_URL` becomes an environment variable
      with the current literal as its default, so the override needs no `!override`.
- [ ] Both smokes green against the one Hub, recorded in a dated review: the
      ChartSearchAI answer unchanged, the Catalyst question answered, the Hub
      revision the same in both.
- [ ] Harness suites for ChartSearchAI and Catalyst each run once against the
      shared stack from one harness checkout; run ids in the review.

### Checkpoint 4: written down and repeatable

- [ ] `environments/README.md` names the three modes, their one command each and
      their smoke; `docs/catalyst-demo-operations.md` points at it for the local
      MVP and keeps only the demo-host material.
- [ ] The review process boot check (openmrs-contribution.md) names both smokes.
- [ ] Each pin move of the Hub, ChartSearchAI, QueryStore, ESM or Catalyst runs the
      smokes of the stacks it touches before the pin lands, and the record says so.

## Rules

- One Hub image, built from `targets/med-agent-hub`, in every mode. A mode may run
  its own container of it, never a different build.
- A smoke proves delivery, not content: the stack is the pinned source, a question
  goes in, an answer with resolving citations or a result comes out. What a provider
  puts inside its envelope is that provider's contract, tested in its repository.
- Each mode keeps working alone. A change that makes together work by breaking
  alone is not done.
- Nothing here depends on catalyst.openelis-global.org or any other demo host.

## Decisions

- **Hub sharing:** the umbrella's `harness-med-agent-hub` is the shared Hub; the
  Catalyst MVP's Hub service stays for standalone use (owner, 25 October).
- **OpenELIS version:** Catalyst follows the latest OpenELIS Global 2 release
  rather than a docker-repository commit (owner, 25 October).
- **CSiM:** the Superset dashboard work lives in DIGI-UW/csim; the umbrella carries
  none of it ([#20](https://github.com/pmanko/openclinai.org/pull/20) closes unmerged;
  owner, 25 October).
