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

## Checks

| Step | Result |
| --- | --- |
| Backend api tests at 12255dd84 | 3,657 tests, one failure: the timing-dependent `LocalLlmServerAuthTest#aPortHeldByAListenerThatAcceptsNothingFailsTheStart`, which failed one of three reruns alone and is not touched by this change |
| QueryStore tests | not rerun: its code is identical to the tested cf6bca91f |
| Index | unchanged QueryStore code, so no reindex; after the restart the index reports complete with 514,682 documents |
| Build and deploy | `make openmrs-source-pair-build`, backend recreated (healthy in 35 s), `hiv-baseline.py record-deployed` |
| Smoke | `make chartsearch-smoke`: `single-12b-checked` Answer `checked` with one resolved citation in 18.9 s, done in 58.5 s, stored; identity ChartSearchAI 12255dd84, QueryStore 651f5e4, ESM aee3449, Hub 36708b5 |
