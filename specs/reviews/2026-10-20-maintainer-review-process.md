# The maintainer's review process, and ours (20 October 2026)

Research behind [review-process.md](../review-process.md): where the OpenMRS maintainer's
review method is documented, what it does, how our 20 October round compared, and what
the best-practice literature adds. Copies of the maintainer's files read for this are
under `work/research/daniel-pipeline/` (git-ignored); the sources are public.

## Where it is documented

The whole process is vendored in `openmrs/openmrs-module-querystore` under `.claude/`
(skills, hooks, a pipeline driver and run records; `pr-review` 0.20.0 last edited
19 October 2026, `pr-harden` 0.39.0) and in `openmrs/openmrs-module-chartsearchai/CLAUDE.md`
(92 commits by dkayiwa). The comments on our PRs are produced by `pr-review` run by an
agent the maintainer supervises.

| Piece | What it does |
| --- | --- |
| `pr-review` | Reads the ticket and every prior thread first; verifies each finding by building, running or tracing; a blocking comment carries "if merged as-is, X breaks because Y"; comments at most 60 words, no labels, no thanks; a fixed thread gets silence; Step 1 re-verifies claimed fixes against the head by running |
| `pr-harden` | A loop: fresh-context reviewer, fresh fixer that implements or declines on the record, root `mvn clean install`, fresh verifier on a real standalone for runtime-visible changes, one commit, push; exits only when the reviewer records zero blocking findings on the pushed sha; a Stop hook refuses to end the session otherwise; capped at four rounds, blocking-only from round four |
| Mutation probes | Every role mutates production code, reads which test reddens, restores with `git checkout`; "if you add a guard, prove which case reddens"; a guard meant to stay green is shown failing on the case it exists for |
| Verifier | Deploys the omod, deletes the lib cache, hashes the loaded class against the build, drives the REST call, records `observed`; repairs the environment, never the artifact; restores global properties as found |
| Test-coverage rule | For each behaviour change, the test that fails on base, passes on the PR and asserts the runtime effect, not a proxy; ask what the fixture can express |
| `measure-first` | Harness, baseline number and minimum threshold before any quality change; post-hoc thresholds banned |
| `verify` | Runtime claims come from the running system; "the test passes, so X works" is listed as a don't |
| Run records and `skill-retro` | Each run appends what was refuted by measurement, raised by a fresh agent, declined; a retro with a bar turns corroborated lessons into skill edits |
| `CLAUDE.md` | TDD with "write the strictest assertion; if it doesn't fail, tighten it until it does"; tests call the production pipeline; no test count or tally that tracks the code |

Everything in that tree is Claude Code-specific: Stop hooks registered in
`~/.claude/settings.json`, the `Agent` tool for fresh contexts, `EnterWorktree`, a state
file keyed on the session's working directory. More than half of `pr-harden` concerns
running unattended (agent death, rate limits, worktree isolation, pid ancestry), not
review.

The maintainer's model gates for slice-composition changes are chartsearchai's own
`eval/drift-metric/` scripts under ADR Decision 28. Since #603 (6 October)
`chartsearchai.chartMode` defaults to `fullChart`, so #587's slice affects only installs
that opt in; #587 is still held on the kidney cell.

## How the 20 October round compared

Our review (the [20 October record](2026-10-20-track-a-review-round.md)): four read-only
agents, one PR's diff each, no probe, no revert check, no runtime run, no cross-layer pass,
"suites green" as the bar. It found 2 blocking findings. The maintainer's pass on the same
code a day later found 12, each reproduced. Of the 39 threads:

- about 5 came from reverting a fix and seeing the tests stay green (#586 `system_range`,
  #55 `indepth_error`, #88's fake that ignores the limit, #56's reset, #585's only
  positive case);
- about 10 from running the code (paging that drops a record, a bootstrap loop that never
  ends, XML back-references, a panel close aborting the other panel's turn, E4B reasoning
  filling the context, `numCandidates` over 10,000, truncated charts);
- about 5 from interactions between PRs in a stack (#55 against #590's repair pass, #59
  against #590's stored error, #586's `finishTurn` against #590's fallback, #58 and #59 on
  the picker);
- the rest from reading core and Elasticsearch sources.

None is a style comment. The non-blocking ones are small and each says why.

## Existing tooling

- `claude-code-guards`: PreToolUse hooks on Bash for Claude Code and Codex; commit-time
  static checks (secrets, focused or disabled tests, assertion-free test files, mocked unit
  under test, narrative comments); advisory except secrets; never runs a test.
- `tdd-guard`: installed only in the validation harness repository.
- `work/run-suite.sh`: full suites per backend layer. `work/prs/pr-status.py` and
  `unanswered.py`: thread collection. `work/eval-88/`: the one-off eval runner and scorer.

## Best-practice reading

The searches added little beyond the maintainer's own material. Mutation testing tools
([PIT](https://dev.co/testing/open-source/pitest), release 1.25.6 of July 2026;
[Stryker](https://oneuptime.com/blog/post/2026-01-25-mutation-testing-with-stryker/view))
automate what the maintainer does by hand, at 5 to 20 minutes per run and with plugin
configuration in each build. [TDD Guard](https://claudelog.com/claude-code-mcps/tdd-guard)
and similar hooks enforce a failing test before an edit but are agent-specific and do not
run the revert check. The adversarial-review literature
([structured disagreement](https://arxiv.org/pdf/2608.18167),
[Imbue on AI review making correct code worse](https://imbue.com/blog/2026-04-29-how-ai-code-review-can-make-correct-code-worse))
supports the maker-checker separation and warns that a fixer acting on review comments
drifts out of scope, which is the maintainer's "declines on the record" rule.

## Assessment

The core is effective and mainstream, done unusually well: a separate reviewer, verify by
running, fail-first tests with mutation probes, the failure-mode sentence as the bar for
blocking, pre-registered gates, rules that carry their evidence. The shell around it (the
loop, state machine, gates, retro) exists to run overnight on a ticket pool and is tied to
one tool. The design in [review-process.md](../review-process.md) adopts the core as plain
files any agent or person runs, and leaves the shell.
