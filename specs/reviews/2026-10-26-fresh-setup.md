# Fresh ChartSearchAI setup at the 26 October pins (26 October 2026)

Evidence for [local-stacks.md](../local-stacks.md), checkpoint 1: the fresh-setup
case, and the module upgrade from a database set up on the previous heads. The
pinned default baseline (`hiv-20261020-231108`,
`sha256:6d828211…`) was exported on 20 October from the stack then running, so
restoring it and starting the current modules is that upgrade.

## Pins

Umbrella main 174736c: ChartSearchAI 46b30eb75, QueryStore cf6bca91f, ESM aee3449,
Med Agent Hub 36708b5, harness c36c354, Catalyst 8af4a85.

## Commands and results

| Step | Command | Result |
| --- | --- | --- |
| Fresh setup | `make chartsearch-research-setup` (19:15 to 19:20 UTC) | builds at the pins; database and 514,682 indexed documents restored from the baseline; `hiv-baseline.py verify`: "514682 documents match the baseline; nothing was re-embedded"; ChartSearchAI started with providers `bundled,hub`, default `hub`; all seven eval-* logins work |
| Smoke | `make chartsearch-smoke` | eval-doctor logged in, patient 2428TU-4 loaded, `single-12b-checked` Answer `checked` with one resolved citation in 13.0 s, turn done in 53.0 s, stored; identity ChartSearchAI 46b30eb75, QueryStore cf6bca91f, ESM aee3449, Hub 36708b5 |

## What the first smoke attempts found

- **No record of the rebuilt ChartSearchAI module as deployed.** Setup builds the
  modules and restarts OpenMRS on them, but only the QueryStore record was written
  (by the restore), so the identity check read every fresh setup as a stale
  deployment. `hiv-baseline.py record-deployed` now writes both records, and setup
  runs it once OpenMRS has restarted on the new builds.
- **The smoke could not read the Hub's revision after a rebuild.** Setup rebuilt
  the Hub image without recreating the running container, and Docker's containerd
  image store cannot inspect the untagged image a running container was started
  from. The smoke now reads the revision label from the container, which carries
  the labels of the image it was created from. Catalyst's health gate reads an
  external Hub the same way and needs the same change.

The Catalyst MVP stayed up on the shared Hub throughout.
