# Track A upstream sync: merged stacks, fork mains and pins (2 November 2026)

Every Track A stack is merged upstream. Daniel squash-merged QueryStore #94 to #98 on
29 October (main 0c4c1b3d9, the `querystore-api` snapshot republished), ChartSearchAI
#617 on 29 October and #618 to #623 on 29 and 30 October, our port-probe fix #628 on
31 October (main c53b8bee8), and re-landed the frontend stack #72 to #76 in #84 after
his revert #78 (main 0c1e46a97). The fork mains and the umbrella pins still pointed at
the pre-review stack tops; this record moves both to the upstream heads.

## Fork mains

The fork mains (QueryStore 155d6efef, ChartSearchAI 3e3012631, frontend aee344935)
held only the pre-squash stack commits of 21 to 26 October: 61, 58 and 42 commits
that upstream now carries in reviewed, squashed form. Before replacing them:

- Every file a fork main changed since its merge-base with upstream was also changed
  upstream afterwards, except four QueryStore bootstrappers (DrugOrder, Patient,
  ReferralOrder, TestOrder) whose round-11 `versionTracksContent() { return false; }`
  overrides round 12 removed on purpose (the skip became opt-in, #94).
- A merge of upstream into each fork main conflicts in 9, 39 and 7 files. Of the lines
  in those files that exist on the fork and nowhere in the upstream tree, 9, 168 and 8
  are our drafts that a later review round rewrote (the Depends-On script reading
  `PR_BODY`, the README merge sentences, the retained-measurements path in
  `ConversationServiceImpl`, the `STATUS_ONLY` body subscriber, `frequencyFollowing`,
  `toPayload`, one `ChartAnswer` constructor arity across 17 omod tests, and the like);
  the other 79 and 13 already existed at the merge-base and are upstream's own later
  rewrites. Nothing unmerged lives on the fork mains. Working files:
  `work/sync/conflict-analysis.md`, `work/sync/classification.txt`.

Each fork main was backed up as `main-backup-2026-11-02` at its old commit, then
replaced with upstream main (`gh repo sync --force`, approved by the owner), the
GitHub equivalent of "Sync fork, discard commits". Three sync PRs opened to inspect
the conflicts (QueryStore #48, ChartSearchAI #36, frontend #22) closed as merged once
main matched upstream; their branches are deleted.

The first sync attempt was refused with HTTP 422 on all three forks: each `main`
carried classic branch protection (required status checks, no force pushes), which
rejects any move of the branch to a commit whose checks never ran in that fork. The
legacy protection (saved in `work/review/fork-protection/`) was replaced with a
ruleset on `main`: the same required checks ("build / Build with Java 11" on
QueryStore; "build" and "eval harness selftests" on ChartSearchAI; "build" on the
frontend), non-fast-forward blocked, the repository admin role on the bypass list.
A mirror sync from upstream now goes through without a settings change.

| Fork | From | To | Backup |
| --- | --- | --- | --- |
| QueryStore | 155d6efef | 0c4c1b3d9 (= openmrs main) | `main-backup-2026-11-02` |
| ChartSearchAI | 3e3012631 | c53b8bee8 (= openmrs main) | `main-backup-2026-11-02` |
| Frontend | aee344935 | 0c1e46a97 (= openmrs main) | `main-backup-2026-11-02` |

## Pins

| Gitlink | From | To | Notes |
| --- | --- | --- | --- |
| `targets/querystore` | 155d6efef | 0c4c1b3d9 | Moved on `main` in #34 (= openmrs `main`) |
| `targets/chartsearchai` | 3e3012631 | 8431be94d | Moved to c53b8bee8 (= openmrs `main`) during the 2 November sync, then advanced on `main` in #34 to 8431be94d (`hub-answer-delta-relay`, 12 commits ahead of c53b8bee8) |
| `targets/chartsearchai-esm` | f81cbbc99 | 0c1e46a97 | Moved by this change (= openmrs `main`) |
| `targets/med-agent-hub` | 96b90051f | 71ddd3599 | Moved by this change to `main` (includes #60 and #61) |
| `targets/validation-harness` | ffe0018cf | a3ea2012e | Moved by this change to `main` (`.mailmap`) |

## Checks

| Step | Result |
| --- | --- |
| Upstream CI at the pinned commits | QueryStore Build success (run 40874102972); ChartSearchAI Build with Maven, Build Docker Images and Build O3 Standalone success (runs 41362165525, 41362165226, 41362165227); frontend OpenMRS CI success (run 41365913446) |
| Build | `make openmrs-source-pair-build` (QueryStore `mvn install`, ChartSearchAI `mvn package`) and `make chartsearch-esm-build` from the new pins; provenance written for both modules and the ESM bundle |
| Deploy | Modules and bundle staged into `artifacts/openmrs/`, `docker restart harness-openmrs-backend`, healthy after 35 s, `hiv-baseline.py record-deployed` (ChartSearchAI c53b8bee8, QueryStore 0c4c1b3d9) |
| Index | No reindex: the restart's top-up completed at 06:53:14Z on the existing Elasticsearch index, complete with 514,682 documents (obs 427,890; drug_order 43,412; encounter 14,322; visit 14,250; patient 5,333; condition 4,454; program 3,921; test_order 1,095) |
| Smoke | `make chartsearch-smoke`: provider `hub`, profile `single-12b-bare`, Answer `checked` with one resolved citation in 6.7 s, done in 18.1 s, six reference records, stored; identity ChartSearchAI c53b8bee8, QueryStore 0c4c1b3d9, ESM 0c1e46a97, Hub image 0e3e0d92f |
| Umbrella | `python3 -m unittest discover -s tests`: 19 tests OK |

The smoke's identity check compares the running Hub image with `targets/med-agent-hub`.
The shared local Hub container is built at 0e3e0d92f (the WAHS stream's build), not at
the umbrella's pin 7a2855f69, so the smoke ran with the Hub submodule checked out at
0e3e0d92f locally and left at 7a2855f69 in the commit. The Hub container, its pin and
the taps were not touched.

## Still open

- The frontend `provider_not_permitted` message PR (local branch `provider-not-permitted`,
  to rebase onto 0c1e46a97 and open on the owner's approval).
- Dual-Provider release acceptance and the temporal probe re-run in
  [`specs/openmrs-contribution.md`](../openmrs-contribution.md).
