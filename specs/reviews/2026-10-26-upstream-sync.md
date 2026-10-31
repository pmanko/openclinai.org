# Sync with the rebased OpenMRS stacks (26 October 2026)

Daniel squash-merged QueryStore #92 (3491096) and #93 (0c12429) and backend #615
(5272a5c), #616 (69add36) and #625 (88f369f), and his `gh stack merge` rebased the
remaining layers onto main. Upstream main then moved on: QueryStore to eeb9648
(three `.claude/` skill commits), ChartSearchAI to 77ed45f (16 drug-safety commits,
ADR 451 to 458).

## Local stacks

Every open layer was reset to its upstream head and the merged layers dropped;
`git range-diff` of the old and new stacks shows only the merged commits differ, so
nothing local was lost. `gh stack checkout` adopted the GitHub stacks (QueryStore
stack #99).

| Repository | Open layers, upstream heads |
| --- | --- |
| QueryStore | #94 f08dc41 (base main), #95 aecb9f6, #96 7a1f47f, #97 bc3d7d5, #98 3c0783d |
| Backend | #617 c83fa3c (base main), #618 b5d4115, #619 09ad023, #620 455fcdf, #621 bbb1f57, #622 03325a3, #623 a087da3 |
| Frontend | unchanged, #76 aee3449 |

The open stacks were not restacked onto the newer mains; that is the owner's call
for the round-10 push. The backend's newer main changes `QueryScopeRouter.java`,
`DrugReferenceInjector.java` and `docs/adr.md`, which the stack also changes, and
merges cleanly.

## Fork mains and pins

Each fork main is its stack's top merged with upstream main, so the local stack runs
current upstream code. Both moves were force pushes, approved by the owner, because
upstream was rebased.

| Fork | From | To | Content |
| --- | --- | --- | --- |
| QueryStore | cf6bca91f | 651f5e4 | #98 3c0783d + main eeb9648; code identical to the previous pin, nine `.claude/` files differ |
| ChartSearchAI | 46b30eb75 | 12255dd84 | #623 a087da3 + main 77ed45f; adds the 16 drug-safety commits |
| ESM | aee3449 | aee3449 | unchanged |

After round 10 (the same evening) both stacks were pushed again with the maintainer's fixes, and
the fork mains moved a second time, again by approved force push:

| Fork | From | To | Content |
| --- | --- | --- | --- |
| QueryStore | 651f5e4 | 155d6efef | #98 after round 10, on main 8bbc5ea (`.claude/` tooling commits only) |
| ChartSearchAI | 12255dd84 | 3e3012631 | #623 after round 10, on main 2508d82 (ADR Decision 460); the paired build replaced by the Depends-On check |
| ESM | aee3449 | aee3449 | unchanged |

## Checks

| Step | Result |
| --- | --- |
| Backend api tests at 12255dd84 | 3,657 tests, one failure: the timing-dependent `LocalLlmServerAuthTest#aPortHeldByAListenerThatAcceptsNothingFailsTheStart`, which failed one of three reruns alone and is not touched by this change |
| QueryStore tests | not rerun: its code is identical to the tested cf6bca91f |
| Index | unchanged QueryStore code, so no reindex; after the restart the index reports complete with 514,682 documents |
| Build and deploy | `make openmrs-source-pair-build`, backend recreated (healthy in 35 s), `hiv-baseline.py record-deployed` |
| Smoke | `make chartsearch-smoke`: `single-12b-checked` Answer `checked` with one resolved citation in 18.9 s, done in 58.5 s, stored; identity ChartSearchAI 12255dd84, QueryStore 651f5e4, ESM aee3449, Hub 36708b5 |
| Round-10 pins | QueryStore: every layer's full suite green (635 api and 66 omod tests at the tip). Backend: full suites at #617 and #619 green but for the known timing-dependent `LocalLlmServerAuthTest`; at #620 the body-read guard caught the `ofInputStream` change, which was dropped before the push, after which `ArchitectureGuardTest` and the wiring tests pass at #620 and the tip. `make openmrs-source-pair-build`, `docker restart`, healthy in 40 s, `record-deployed` (ChartSearchAI 3e3012631, QueryStore 155d6efef). Index unchanged and complete (514,682). `make chartsearch-smoke`: `single-12b-checked` Answer `checked` with 1 resolved citation in 39.6 s, done in 64.2 s, stored |
