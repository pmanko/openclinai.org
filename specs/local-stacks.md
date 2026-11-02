# Local stacks: ChartSearchAI and Catalyst, alone and together

**Thread:** every product stack the umbrella owns runs on one machine on its own and
all together, from the current pins, with one Med Agent Hub, one model router and
one validation harness, and each mode has a smoke that proves it ·
**Status:** each stack runs alone and both run together on one Hub at OpenELIS
Global 2 3.3.0, from component mains; both smokes green on 26 October, after a
fresh ChartSearchAI setup too. Open: two harness suite defects ·
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

## Where this stands (26 October 2026)

| Mode | Command and smoke | Proven |
| --- | --- | --- |
| ChartSearchAI alone | `make local-stack-up`; `make chartsearch-smoke` | restart with data ([record](reviews/2026-10-25-local-stack-restart.md)); fresh setup from the baseline ([record](reviews/2026-10-26-fresh-setup.md)) |
| Catalyst alone | `make catalyst-mvp-up`, its own Hub on 18082; `make catalyst-smoke` | fresh boot on OpenELIS 3.3.0 ([25 October record](reviews/2026-10-25-local-stacks-together.md)) |
| Together | `make local-stack-up`, then `CATALYST_HUB=shared make catalyst-mvp-up`; both smokes | one Hub, both smokes, both harness suites run ([25 October record](reviews/2026-10-25-local-stacks-together.md)) |

The modes, commands and first-start steps are in
[environments/README.md](../environments/README.md#chartsearchai-and-catalyst-alone-or-together).
Open: two harness suite defects found against the shared stack, which belong to
the harness and the Hub ([record](reviews/2026-10-25-local-stacks-together.md)).

## Target path

Each checkpoint is ticked only with a link to its evidence: a merged PR, or a dated
record under [`reviews/`](reviews/) naming the commands run and their results.

### Checkpoint 1: ChartSearchAI alone, proven

- [x] The stack runs at the current pins with data retained: modules, bundle and
      Hub rebuilt, index unchanged, identity probe green
      ([25 October record](reviews/2026-10-25-local-stack-restart.md)).
- [x] `make chartsearch-smoke` is the setup acceptance step and the boot-check
      finisher ([#22](https://github.com/pmanko/openclinai.org/pull/22)).
- [x] Fresh setup (`make chartsearch-research-setup`) and the module upgrade from a
      database set up on the previous heads each end with a green smoke
      ([26 October record](reviews/2026-10-26-fresh-setup.md)).

### Checkpoint 2: Catalyst alone on the latest OpenELIS release

- [x] Catalyst [#142](https://github.com/DIGI-UW/catalyst-ai/pull/142) and
      [#143](https://github.com/DIGI-UW/catalyst-ai/pull/143) merged: the
      result-freshness contract fix the smoke exposed, then the 3.3.0 release images
      by digest and openelis-docker tag, the seed's version guard and the warehouse
      ordering fix.
- [x] The MVP boots, seeds and passes `mvp-health.sh` on this machine in
      external-router mode, reporting OpenELIS 3.3.0 ([25 October record](reviews/2026-10-25-local-stacks-together.md)).
- [x] `make catalyst-smoke`: Catalyst's own health gate, then one natural-language
      question through the local gateway that returns generated SQL and a result
      ([25 October record](reviews/2026-10-25-local-stacks-together.md)).
- [x] Catalyst and Hub gitlinks on their mains (Catalyst 8af4a85, Hub 36708b5) after
      Catalyst #142 to #147 and Hub #40 merged, both smokes green on them
      ([#24](https://github.com/pmanko/openclinai.org/pull/24)).
- [x] `make catalyst-smoke` reliably green: 8 of 8 with
      [Catalyst #146](https://github.com/DIGI-UW/catalyst-ai/pull/146) (result types
      from the database), [#147](https://github.com/DIGI-UW/catalyst-ai/pull/147) and
      [Hub #40](https://github.com/pmanko/med-agent-hub/pull/40) (the reviewer gives
      feedback, the writer revises), all merged
      ([record](reviews/2026-10-25-local-stacks-together.md#reviewer-as-feedback-only-catalyst-147-hub-40)).

### Checkpoint 3: together, one Hub

- [x] Umbrella override (`compose/catalyst-mvp-shared-hub.override.yml`, layered on
      the isolated one): the gateway joins the ChartSearchAI network, its dependency
      on the MVP's Hub is reset, and the MVP's own Hub sits behind an unused profile.
      Catalyst alone still uses its own Hub ([25 October record](reviews/2026-10-25-local-stacks-together.md)).
- [x] `CATALYST_HUB=shared` in `scripts/catalyst-mvp.sh` requires the umbrella Hub
      healthy and points Catalyst and its health gate at it ([25 October record](reviews/2026-10-25-local-stacks-together.md)).
- [x] Catalyst [#144](https://github.com/DIGI-UW/catalyst-ai/pull/144) merged:
      `MVP_HUB=external`, the gateway's Hub URL as `MVP_GATEWAY_HUB_URL`, layered
      overrides.
- [x] Both smokes green against the one Hub, the Hub revision the same in both
      ([25 October record](reviews/2026-10-25-local-stacks-together.md)).
- [x] Harness suites for ChartSearchAI and Catalyst each run once against the
      shared stack from one harness checkout ([25 October record](reviews/2026-10-25-local-stacks-together.md)). Two Catalyst suite
      defects it found are open: the suite's base SQL reads a retired PostgreSQL
      view (harness), and the Hub reports no prompt token count for qwen2.5-14b
      (Hub).

### Checkpoint 4: written down and repeatable

- [x] `environments/README.md` names the three modes, their one command each and
      their smoke; `docs/catalyst-demo-operations.md` points at it for the local
      MVP ([#23](https://github.com/pmanko/openclinai.org/pull/23)).
- [x] The OpenMRS boot check (openmrs-contribution.md) finishes with
      `make chartsearch-smoke` ([#22](https://github.com/pmanko/openclinai.org/pull/22)).
- [x] Each pin move runs the smokes of the stacks it touches before the pin lands,
      and the PR says so: the rule is in [AGENTS.md](../AGENTS.md)
      ([#23](https://github.com/pmanko/openclinai.org/pull/23)).

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
