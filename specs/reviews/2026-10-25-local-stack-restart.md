# Local ChartSearchAI stack restarted at the 25 October pins (25 October 2026)

Evidence for [local-stacks.md](../local-stacks.md), checkpoint 1: the restart-with-data
case of the boot check. The stack built on 20 to 22 October (ChartSearchAI 4baefe82a,
QueryStore 23cf7fbe2, ESM 72b33a43e, Hub f2add44ce) was rebuilt at the pins umbrella
[#19](https://github.com/pmanko/openclinai.org/pull/19) merged, with the database and
the QueryStore index retained.

## Pins

| Component | Pin | Where it is |
| --- | --- | --- |
| ChartSearchAI | 46b30eb75 | fork main: the #623 stack head with upstream main merged (15 drug-safety wording commits) |
| QueryStore | cf6bca91f | fork main: the #98 stack head with upstream main merged (5 skill-file commits) |
| ESM | aee3449 | fork main: the #76 stack head, level with upstream |
| Med Agent Hub | 9ac9d43 | main, after the squash merge of #33 to #38 |
| Harness | c36c354 | main, after the squash merge of #199 |

The QueryStore diff from the deployed build (23cf7fbe2 to cf6bca91f) touches nine
Java files and no index mapping, document shape or schema version, so the index was
not rebuilt and the published HIV baseline stays valid.

## Commands and results

| Step | Command | Result |
| --- | --- | --- |
| Build | `make openmrs-source-pair-build chartsearch-esm-build med-agent-hub-build` | provenance manifests name 46b30eb75, cf6bca91f, aee3449; Hub image labelled 9ac9d43 |
| Start | `make local-stack-up` | router, OpenMRS, Hub up; no rebuild |
| Load the new modules | `docker compose ... up -d --force-recreate backend` | backend healthy after 20 s; `chartsearchai` and `querystore` 1.0.0-SNAPSHOT started |
| Hub | `make med-agent-hub-up` | healthy after 6 s with the QueryStore settings (a plain `--force-recreate` had dropped them: `context_source_unavailable`) |
| Configure | `make querystore-configure`; `CHARTSEARCH_PROVIDERS_DEFAULT=hub make chartsearch-configure` | hub endpoint, providers `bundled,hub`, default `hub` |
| Identity | `python3 scripts/probe-chartsearchai-relay.py --identity-only` (the smoke's `--identity-only` after #22) | mounted module hashes, served bundle files and Hub revision match the builds |
| Data | REST `session`, `patient`, Elasticsearch `_cat/indices` | eval-doctor logs in; patient 2428TU-4 loads; 427,890 obs and 5,333 patient documents indexed |
| Smoke | `make chartsearch-smoke` ([#22](https://github.com/pmanko/openclinai.org/pull/22) at d041b0a) | checked Answer in 10.6 s, turn done in 30.2 s, one Answer citation resolved, five references, In-Depth complete, stored, Hub 9ac9d43 |

The deployed-module manifests (`artifacts/chartsearchai-local/deployed-*-omod.json`)
were copied from the fresh build manifests, since nothing in the repository writes
the ChartSearchAI one any more.

## The probe's stale contract

The pre-#22 probe failed the same turn with "checked answer retained unresolved or
unsupported evidence": one In-Depth claim ("...93% [14], which should be monitored
as a baseline") carried `groundingStatus: unsupported` while the Answer's own
citation was verified. Hub [#37](https://github.com/pmanko/med-agent-hub/pull/37)
labels such claims instead of withholding them; the probe asserted the 30 September
behaviour. #22 replaces that assertion with the smoke described above.

## Not run

Fresh setup (`make chartsearch-research-setup`) and the module upgrade from a
database set up on the previous heads: the other two cases of checkpoint 1.
