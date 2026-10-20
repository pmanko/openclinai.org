# Track A independent review and fixes (20 October 2026)

After the [end-to-end check](2026-10-20-track-a-e2e.md), every PR of the three
[OpenMRS contribution](../openmrs-contribution.md) stacks was reviewed independently, the
findings were fixed in their owning layers, the stacks were pushed to the forks, and the
replies to the maintainer's 19 October threads were posted. The backend was first rebased
onto upstream `7d052573`, which added drug-safety changes; the one conflict (#585's screen
gate) kept upstream's gate and set #585's flag inside it.

## Review

Four reviewers read each PR's own diff against its predecessor branch, read-only. Findings:
two blocking, about twenty should-fix, the rest minor. The owner chose to fix all of them in
this round. Summaries were posted on the top PR of each stack:
[backend #590](https://github.com/openmrs/openmrs-module-chartsearchai/pull/590#issuecomment-6293755597),
[frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59#issuecomment-6293756109),
[QueryStore #87](https://github.com/openmrs/openmrs-module-querystore/pull/87#issuecomment-6294067407),
with a note on [#90](https://github.com/openmrs/openmrs-module-querystore/pull/90#issuecomment-6294067968).

- Blocking, #590: `/chat/stream` did not pass the question through upstream's `asTyped`
  (ADR Decision 375), so an escaped `&` reached validation, the stored turn and the Hub.
- Blocking, QueryStore #90: sync stamped the committed version onto content serialized
  before the save, so a new condition kept a null date that the restart skip never repaired.

Owner decisions taken with the fixes:

1. The Hub profile picker lists only the profiles the Hub advertises as available; if the
   selected one drops out, the panel asks for a new pick and does not send.
2. A bare `unavailable` safety status on a final answer draws no box.
3. #585: a drug-reference loader finding limits an answer only when it concerns a drug that
   answer screened; a finding about the file or the configuration still limits every answer.
   The loader now records the affected entries of each finding to make this decidable.

## Heads after the fixes

| Project | PRs | Tip |
| --- | --- | --- |
| Backend | #583 to #590, fork #35 | `codex/account-context` `c8c8f8abd` |
| Frontend | #55 to #59 | `codex/conversation-lifecycle` `fdd9b5f` |
| QueryStore | #85 to #88 | `codex/retrieval-diversity` `56360db` (#87 `1bd12c1`) |
| QueryStore | #89, #90 | `e6168df` (unchanged), `525f8b7` |

The backend's paired CI build now pairs with QueryStore `1bd12c1`.

## Suites

- Backend, full `mvn -o test` on every layer against QueryStore `1bd12c1` (the macOS-only
  occupied-port test excluded): all nine layers pass, 3,632 to 3,855 tests, no failures.
- Frontend, tests, lint and type check on every layer: all pass, 515 to 718 tests.
- QueryStore, `mvn -o test` on #85 to #88 and #90: all pass; #89 unchanged.
- The #585 change failed first on two tests (another drug's defect, and the shipped DDInter
  data screening ibuprofen, which reported `source_data_partially_invalid` before and not
  after) and passes with its guard tests (a defect on the screened drug, an unreadable file).

## Replies

The 32 drafted thread replies to the 19 October review and one PR comment on #87 were posted
on 20 October, each citing a commit on the pushed branches. GitHub rewrites the text
`\u0000` in a comment, so the #85 separator reply was edited to name the escape in words.

## Not checked

- QueryStore `-Pintegration` against MySQL and Elasticsearch after the #90 fixes (Docker was
  not running).
- The evaluation behind the retrieval changes in #88.
- Fresh setup from the baseline, and a rerun of the running-stack check on these heads.

## Rebase onto the 20 October upstream

Upstream `main` moved by four drug-safety commits (`7d052573` to `9827db15`) after the fixes
above. The nine backend branches were rebased in stack order with `git rebase --onto`, without
conflicts, and force-pushed to the fork with explicit lease values at 21:40 UTC.

| PR | Branch | Before | After |
|---|---|---|---|
| #583 | `codex/provider-contract` | `7ecd5c625` | `cc41d9b7d` |
| #584 | `codex/local-token-counting` | `4ff5817d7` | `b40421f93` |
| #585 | `codex/safety-check-status` | `3d2ee3e68` | `124719b8a` |
| #586 | `codex/conversation-storage` | `fa897901f` | `92a2d429c` |
| #587 | `codex/context-budget` | `9a8e9ee4a` | `19248d1b2` |
| #588 | `codex/bundled-provider` | `24c9bb4d6` | `9fafd0659` |
| #589 | `codex/hub-provider` | `0cbff174c` | `b495a2a1a` |
| #590 | `codex/conversation-endpoints` | `d40f126b2` | `96cf7ad22` |
| fork #35 | `codex/account-context` | `c8c8f8abd` | `9ed746a2b` |

Full `mvn -o test` on every rebased layer against QueryStore `d61c14d` (the merge of #88 with
#91 the umbrella now pins; the macOS-only occupied-port test excluded): all nine layers pass,
3,636 to 3,859 tests, no failures. The frontend and QueryStore upstreams did not move.

Of the items not checked earlier in this record: the QueryStore `-Pintegration` run against
MySQL and Elasticsearch ran on #90 (560 tests) and #88 (626 tests), each with the one
pre-existing `hybridFusesBm25AndKnnViaSpiDefault` zero-vector error that #89 fixes; the #88
evaluation is in [its own record](2026-10-20-querystore-88-retrieval-diversity.md). Fresh setup
from the baseline ran on 20 October before that evaluation.
