# Review tooling

The procedure in [specs/review-process.md](../specs/review-process.md), as plain git
hooks, scripts and briefs that a person or any agent runs the same way.

## Hooks (L0 and L1)

`make review-hooks-install` points `core.hooksPath` of the umbrella, Hub, harness,
and three OpenMRS component checkouts (and their worktrees) at `review/hooks/`, and records the
component commits already pushed to the forks as historical baseline records. These
records do not certify tests or exempt rebased changes from fresh probes. Remove with `git -C <checkout> config --unset core.hooksPath`.

| Hook | Refuses |
| --- | --- |
| pre-commit | a likely secret; a focused or disabled test; a new test file with tests and no assertion. Prints narrative comments and a test that mocks its own unit |
| commit-msg | a malformed `Tests:`, `Mutation:` or `Probe:` trailer, or one outside the final trailer paragraph |
| pre-push, component | a push to any remote's default branch; a non-fast-forward over remote commits you have not fetched; a pushed commit that changes main code and fails its probe |
| pre-push, umbrella | the umbrella's unit tests or `scripts/check_workspace.py` failing |

## Probes

Every commit a push adds (not already on any remote) that changes main code, or changes
only tests and carries a `Mutation:` trailer, is probed in a persistent worktree,
`work/review/wt/<repo>`:

1. **Revert:** the commit's main-code files go back to the parent; the tests must fail.
   A file whose change is only comments or blank lines is not reverted, and a commit
   with no other main-code change and no mutation is not probed.
2. **Green:** at the commit the same tests must pass.
3. **Mutation:** each `Mutation:` trailer is applied at the commit; the tests must fail.

The tests are the `Tests:` trailer, otherwise the test files the commit adds or
changes. A main-code commit with neither is refused unless it carries
`Probe: skip (<reason>)`. The red and green lines go to stderr and to
`work/review/ledger/<repo>.jsonl`; quote them in replies. A commit whose patch was
already probed is run again; a patch ID cannot establish environment freshness. Logs are in
`work/review/logs/<repo>/`.

```
Tests: ContextSliceTest#overFetchIsBoundedByTheLimit, ContextSliceTest
Mutation: api/src/main/java/org/x/Store.java "candidateLimit" -> "request.getLimit()"
Probe: skip (generated migration; covered by the next commit's test)
```

`Mutation:` strings use JSON escapes (`\"`, `\n`); the old text must occur exactly once
in the file at the commit. Probe by hand with `review/bin/probe --repo <checkout>
<commit>...`. The runner is chosen from the checkout's build files (`pom.xml`: Maven,
offline; `package.json` with Vitest; pytest) or `git config review.runner`.

`git commit --no-verify` and `git push --no-verify` skip the hooks; the ledger then has
no record for that work, and a reply cannot quote one.


## Review your repository PRs

Use `make review REPO=hub REPOSITORY=pmanko/med-agent-hub PR=49 AGENT=codex`.
`REPO` selects the checkout: `umbrella`, `hub`, `harness`, `chartsearchai`, `esm`, or
`querystore`. `REPOSITORY` selects the exact GitHub repository and matching remote;
it prevents a fork PR from being mistaken for an upstream PR.

Set `REVIEW_PYTHON` to an absolute prepared interpreter for Python components.
The runner never installs pytest alone as a substitute for component dependencies.
Reports record dependency-file hashes and supplied consumer revisions. Missing
default consumer checkouts leave a partial review; an unavailable explicitly
selected consumer stops the run. Unexecuted tests remain explicit gaps.

Use `CONSUMER_REPO=<checkout alias> CONSUMER_HEAD=<commit>` to select the repository
and feature revision on the other side of this particular contract. The default
consumer maps Hub and harness to each other; a Hub export called by umbrella scripts
needs `CONSUMER_REPO=umbrella`. Without an explicit revision the driver uses that component's current local checkout,
which may belong to a different experiment. A mismatch against that revision does
not establish a defect in a different producer/consumer pair. The report records
the exact consumer commit; `NO_CONSUMER=1` omits this comparison explicitly.
Report and worktree paths include the encoded GitHub repository identity. Saved
human answers are archived and requested again when their review prompt or thread
snapshot changes.
Test adapters record the identities of executed cases. Every case that supplied
red evidence must execute and pass after restoration; an unrelated passing test
cannot replace a skipped target.

Reports carry `scope: source_review`: complete file coverage and no findings do
not certify tests, deployed behavior or acceptance. Unavailable execution remains
visible in the test evidence; source completion is not a merge approval.

The default is a local source review. `FIX=1` explicitly permits the fixer to
commit and push between rounds, only after a complete, current review. Full evaluation reports remain local unless
`PUBLISH_EVALUATION=1` or `PUBLISH=<run directory>` is selected.

Reports must identify the examined revision and account for every changed file.
The driver also verifies that the source and consumer checkouts retain their
supplied revisions and have no pending changes when the reviewer finishes.
Incomplete coverage is `partial`; a changed PR head, base or stack top is `superseded`. Neither can
produce `no_findings`. Findings, execution status and behavior verification are
separate: a source review does not establish deployed-runtime acceptance.

Probes require executed tests. Skips, collection errors and dependency failures
cannot prove behavior. Mutations preserve tests and require a passing restoration.
Hub profiles and prompts, harness scenarios/comparison sets, and WAHS dataset inputs
are executable inputs; prose remains review-only.

The Vitest adapter also requires a fresh execution report from its test-run-end
reporter. Passing assertions with an unhandled runtime error are infrastructure
failures, and an interrupted or missing report cannot prove a mutation failed.
