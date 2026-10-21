# Review process and gates

**Stream:** review rigor · **Status:** hooks and probes built and installed; later
layers in progress · **Owner:** umbrella; each component repository keeps its
own instructions and CI

Give every contribution the rigor the OpenMRS maintainer applies, so a stack passes
their gates in one round instead of three, and make that rigor usable in two ways: by
a person working attended, and as the blueprint an automated reviewer runs, whatever
agent runs it. What the maintainer's process is, and where ours fell short on the
20 October round, is recorded in
[the maintainer review-process record](reviews/2026-10-20-maintainer-review-process.md).

## Principles

1. **Plain files, any runner.** The procedure is scripts, Make targets and markdown
   briefs that a person, Claude Code, Codex, Gemini CLI or another agent runs the same
   way. An agent-specific adapter is one file that says "run `make review`" and names
   the brief. Nothing depends on one agent's hooks, subagents or session state.
2. **The bar is fixed; the width is a parameter.** What counts as a finding (a
   failure-mode sentence with evidence from a run), the revert and mutation probes,
   and a pre-registered threshold for any model gate never scale down. Sweep width,
   rounds, scenarios and gates are flags.
3. **Nothing of this lands in OpenMRS repositories.** Component checkouts get the hooks
   through `core.hooksPath` pointing into the umbrella. Probes, briefs, ledgers and
   gates live here.
4. **One evaluation approach.** Model-facing checks run through the validation
   harness as comparison sets. The maintainer's cohort and scorer are an optional
   dataset and scoring path inside it, not a second harness.
5. **Hooks look at content, never at names.** A probe runs because a commit touches
   main and test code, not because of a branch prefix.
6. **Evidence is what ran.** A reply or record quotes the probe's red and green lines,
   the scenario run directory, the gate's number against its threshold. A test count
   or "suites green" is not evidence of a fix.

## Layers

| Layer | When | Cost | What it does |
| --- | --- | --- | --- |
| L0 Guards | every commit, blocking | none | secrets (hard block), focused or disabled tests, a new test file with no assertion, a mocked unit under test, trailer syntax |
| L1 Probes | every push, blocking | one test run per probed commit | revert probe: the commit's tests fail with its main-code change reverted and pass with it restored; mutation probe: the tests fail under the mutation the commit names |
| L2 Review | on request | 100 to 300k tokens per PR per pass | a fresh session per role runs the brief at the chosen effort and returns findings as JSON; a stack pass reads the merged top for contracts between layers |
| L3 Scenarios | on request, optional | one harness run | the validation harness replays a comparison set against the deployed head and checks machine-readable expectations; the umbrella builds and deploys the head first |
| L4 Model gate | on request, optional, slice changes only | two harness runs | a pre-registered gate (comparison set, dataset, baseline, threshold) run on base and head; the record quotes the number |
| L5 Full evaluation | per milestone: a stack head ready to merge, a baseline rebuild, a model or provider change | about an hour of 12B time for the default | the harness runs the default matrix (`full-default`: 17 scenarios against the bundled arm and the Hub parity arm on one engine), scores it and produces its own report; further arms are the profiles the Hub advertises at run time; a previous run is cited only when a comparison is wanted |

L0 and L1 are the default on every push. L2 to L5 run through `make review`. L0 to L2
answer whether the code is right, L3 and L4 whether a change behaves or retrieves as
claimed, L5 how the assembled stack performs. L2 runs on the local head of a round
(`HEAD=` and `BASE=` name the layer and the layer below in the checkout) before the round
is pushed, so what it finds is fixed or declined locally and does not become a thread
upstream; the PR's threads and body still feed it, and `STACK=1` stays for pushed stacks. L5 is never a merge gate for one PR; its
report is the validation thread's output and feeds publication.

## Parameters

```
make review PR=<n> [REPO=chartsearchai|esm|querystore] [AGENT=claude|codex|gemini|human]
            [EFFORT=low|medium|high] [ROUNDS=1] [STACK=1] [SCENARIOS=<set>] [GATE=<name>]
            [FULL=1] [SET=full-default] [PROFILES=<advertised Hub profiles>] [BASELINE=<run id>]
            [HEAD=<local ref> BASE=<local ref>]  review the layer before it is pushed
            [MODEL=gpt-6.1-sol REASONING=medium]  the reviewer's model and effort (never a personal config's)
make review MEASURE=<set> GOLD=<gold file>      a gate's baseline, before the gate is written
make review FULL=1 [SET=] [PROFILES=]           the full evaluation without a PR
make review-replies PR=<n> [REPO=]              draft thread replies from the last round
```

| Effort | Sweep |
| --- | --- |
| low | correctness and the test-coverage rule on the diff; blocking findings only |
| medium | plus trace one level out: unchanged neighbours, consumers of what the code emits, lifecycle, the merged result of the branch |
| high | plus security and performance dimensions, uncertain findings returned as questions, a refutation pass on each blocking finding |

`STACK=1` adds the contracts between layers (what one PR emits against what the PRs
above and below consume) and reads the stack's merged top. `ROUNDS` above 1 repeats
review and fix until the reviewer records zero blocking findings on the pushed head,
and every round after a clean one is blocking-only. `SCENARIOS`, `GATE` and `FULL` are off
unless named. `FULL=1` runs the harness on `SET` (default `full-default`) against the set's two
arms and produces that run's report. `PROFILES=` adds arms from the profiles the Hub
advertises at run time (read from ChartSearchAI's `/models`, the same list the picker
shows), so a team or validated profile becomes an arm by being published on the Hub,
never by editing a list here. `BASELINE=<run id>` adds a comparison with an earlier run's
report; without it the report stands on its own.

## Layout

```
review/
  README.md              how a round runs, for a person or an agent
  briefs/
    reviewer.md          Steps: gather (ticket, every thread, prior round), is this the
                         right fix, verify by running, compose; the JSON contract
    fixer.md             fail first, name the mutation, trailers, decline on the record
    reply.md             what changed, commit, test, red and green lines, no longer than
                         the comment answered, no thanks, no acknowledgment of a fix
    stack.md             the cross-layer dimension for STACK=1
    judge.md             the harness rubric, for FULL=1
  bin/
    threads.py           open threads per PR into work/review/<repo>-<pr>/threads.json
    probe                [--repo] <commit>...: revert the main files, expect red; restore,
                         expect green; apply each Mutation:, expect red; --baseline records
                         already-pushed commits
    hook                 the hooks' entry point
    runners/             maven.sh, vitest.sh, pytest.sh: run the named tests, report RAN and
                         FAILED lines, exit 0 pass, 1 fail, 2 build error, 3 none ran
  lib/reviewkit/         the hooks, guards, probes and ledger in Python
    threads.py           the PR, its tickets and every thread into threads.json
    role.sh              <agent> <role> <workdir> <prompt> <out>: one fresh session of
                         claude, codex or gemini (or instructions for a person)
    deploy-head.sh       build the PR head, deploy to the local stack, check the loaded
                         class hash against the build, print the module version
    review.py            drives `make review`: threads, rounds, scenarios, MEASURE, gates,
                         the full evaluation, and the shared run step (parity taps up,
                         chartsearchai.llm.* settings and the Hub restored as found)
  hooks/
    pre-commit, commit-msg, pre-push   plain git hooks; installed per checkout by
                                       `make review-hooks-install`
  gates/
    <name>.md            pre-registered: comparison set, dataset, baseline run and number,
                         threshold, date, who signed off
  adapters/
    claude.md, codex.md, gemini.md     one file each: where the brief is, how to run it
work/review/             ledgers, round records, probe worktrees (git-ignored)
```

The validation harness owns the comparison sets, datasets, replay and scoring under
`targets/validation-harness`. The umbrella owns build, deploy, hooks, probes, briefs and
gates. The harness never calls Git, Docker or product paths; `deploy-head.sh` is the
umbrella's.

## Commit contract

A commit that changes main code carries trailers the hooks read:

```
Tests: ContextSliceTest#overFetchIsBoundedByTheLimit, ContextSliceTest#...
Mutation: api/src/main/java/.../QueryStoreServiceImpl.java "candidateLimit" -> "request.getSimilarityLimit()"
```

- `Tests:` names what the revert probe runs. Absent, the probe runs the test classes the
  commit changed. A main-code commit that changes no tests and names none is refused at
  push unless it carries `Probe: skip (<reason>)`, which the ledger records.
- `Mutation:` names the one edit the guard exists to catch (the check deleted, `&&`
  for `||`, `<` for `<=`, the computed value replaced by the plain one). The hook asserts
  the old text is present, applies it, expects `Tests:` red, restores. A commit may carry
  several.
- `Probe: skip` is the escape, visible in the message, never silent.

The pre-push hook probes every commit the push adds (not on any remote yet) that
touches main code, in a persistent probe worktree under `work/review/wt/<repo>` so Maven
compiles incrementally. A patch already probed with the same trailers is not probed again
after a rebase; commits pushed before the hooks were installed are recorded as the
baseline. Mutation strings use JSON escapes, so a multi-line edit is one trailer.

## Roles

- **Reviewer:** a session that never saw the fix being written. Runs `briefs/reviewer.md`
  on the pushed head against the PR's base, with the ticket, every existing thread and the
  prior round's ledger. Returns findings as JSON: file, line, finding, failure mode,
  evidence, blocking. `blocking` requires a non-empty failure mode and evidence; without
  them the finding is a question. Nothing is posted.
- **Fixer:** whoever writes the fix, a person or the working session. Follows
  `briefs/fixer.md`: reproduce first, write the test and see it fail, fix, name the
  mutation, run the probes before the suite, implement every finding agreed with and
  decline the rest on the record with a failure-mode sentence.
- **Reply:** `briefs/reply.md` turns the ledger into thread replies: what changed, commit,
  test name, the probe's red and green lines; never longer than the comment answered.
  The maintainer's reviewer re-verifies claimed fixes against the head by running, so a
  reply that names nothing runnable is ignored.
- **Scenarios and gate** replace a verifier role. `deploy-head.sh` proves the deployed
  bytes; the harness drives the behaviour and records what came back.

## Hooks

Installed by `make review-hooks-install` into each component checkout and the umbrella
through `core.hooksPath`. Plain shell and Python; no agent involved.

| Hook | Repo | Blocks | Prints |
| --- | --- | --- | --- |
| pre-commit | all | a likely secret; a focused or disabled test; a new test file with no assertion | a mocked unit under test; narrative comments |
| commit-msg | all | trailer syntax, or a trailer outside the final paragraph | |
| pre-push | components | a push to any remote's default branch; a non-fast-forward over remote commits not yet fetched; a probed commit whose tests stay green under revert or mutation; a main-code commit with no tests, no `Tests:` and no `Probe: skip` | the red and green lines, into the ledger |
| pre-push | umbrella | `python3 -m unittest` or `check_workspace.py` failing | |

The existing agent-side guards (`claude-code-guards`, PreToolUse on Bash) stay for the
in-chat commit review; the git hooks carry the same checks so they hold for Codex, Gemini
and a person at a terminal.

## Scenarios and gates in the harness

- A review scenario set is a harness comparison set whose expectations are machine
  checkable: records that must be cited or present in the context, abstention, a refusal.
  Today the harness's expectations are notes for a human adjudicator; adding checkable
  expectations is a harness change in its own repository under its constitution.
- The harness scores citations with the maintainer's drift-metric cell rule
  (`validate score-citations`) against a gold file; the October five-patient cohort is
  its dataset (`context-cohort`). The maintainer's own gold covers four patients that are
  not in the HIV dataset, so it is not imported; the scorer reads its format if those
  patients are ever loaded. `work/eval-88/` is superseded by this path.
- A gate file is written before the run: comparison set, dataset, baseline run id and
  number, threshold, date, who signed off. A threshold set after seeing the number is not
  a gate. The result goes in a dated record under `reviews/`.
- A full evaluation (L5) is a harness run of a matrix, not a gate. The `full-default`
  comparison set in the harness is the default matrix, approved 20 October:
  - arms: `engine-parity-bundled-12b` (ChartSearchAI alone, `provider=bundled`, the 12B
    engine through the bundled tap) and `engine-parity-hub-12b` (the same request with
    `provider=hub`, the Hub's single-12B checked profile, the same engine through the
    Hub tap), so the two differ only by the Hub being in the loop;
  - scenarios: the twelve single-turn scenarios of `hub-profile-candidate` (three
    patients; dates, tables, trends, appointments, labs, one out-of-chart abstention)
    and the five `convo-*` conversations (medications-adherence, diagnosis-evidence,
    vitals-monitoring, abstention-honesty, safety-escalation), about 35 turns per arm.
  Further arms come from `PROFILES=`: each named profile must be one the Hub advertises
  at run time, and the run step builds its backend from that advertisement. There is no
  static list of optional arms. The run step brings the parity taps up
  (`scripts/parity-engine-up.sh`) and restores the module's `chartsearchai.llm.*` global
  properties to their as-found values afterwards. The run produces its own report with
  the judge's scores and the captured evidence; the dated record under `reviews/` cites
  the run directory and, when `BASELINE` was given, the earlier report it was compared
  with. The report, not the score, is what publication consumes.

## Mapping to the maintainer's checks

| Maintainer's check | Our layer |
| --- | --- |
| Revert the fix, tests stay green | L1 revert probe at push |
| Mutate the guard, nothing reddens | L1 mutation probe at push |
| Reproduce on a running instance | L3 scenario, or the fixer's reproduce-first step |
| Interaction between PRs in a stack | L2 with `STACK=1` |
| Core and Elasticsearch behaviour read from sources | L2 reviewer brief, medium and above |
| Decision 28 gates for slice changes | L4 gate file and harness run |
| Replies re-verified against the head | reply brief: test name, commit, red and green |

## Target path

- [x] Hooks and probes: `review/hooks/`, `review/bin/probe`, the three runners,
      `make review-hooks-install`; behaviour tests on a pytest fixture project under
      `tests/review/`; installed in the three component checkouts and the umbrella
      ([record](reviews/2026-10-20-review-hooks-and-probes.md)).
- [x] Threads, briefs and roles: `threads.py`, the four briefs, `role.sh` for claude,
      codex, gemini and human, `review.py` and `make review` with `EFFORT`, `ROUNDS`,
      `STACK` ([record](reviews/2026-10-20-review-layers.md)).
- [x] Deployed-head scenarios: `deploy-head.sh`; harness checkable expectations (harness
      PR); a `review-smoke` comparison set; `SCENARIOS=`
      ([record](reviews/2026-10-20-review-layers.md)).
- [ ] Gates: the October cohort as a harness dataset, the citation scorer path,
      `review/gates/`, `MEASURE=`, `GATE=`; the cohort's harness baseline replaces
      `work/eval-88/`; the first gate signed by the owner and run.
- [x] Full evaluation: the `full-default` comparison set in the harness, `FULL=`,
      `SET=`, `PROFILES=` from the Hub's advertised profiles, optional `BASELINE=`; tap
      setup and property restore in the run step; the report recorded under `reviews/`
      ([record](reviews/2026-10-20-review-layers.md#l5-full-evaluation)).
- [x] Applied to the open round: the twelve blocking findings fixed under L0 to L2 with
      probes and replies from the ledger; recorded under `reviews/`
      ([record](reviews/2026-10-20-round3-remediation.md)).
- [x] `openmrs-contribution.md` review-round rules point here instead of restating them
      ([the contribution spec's round rules](openmrs-contribution.md)).

## Gaps the maintainer's 21 October round showed

Evidence: the inventory in `specs/reviews/2026-10-21-maintainer-round-on-the-stacks.md`
(on the remediation branch, PR #19). The
reviewer read the files, reported only what it could reproduce as blocking, had no prior
threads and no consumer checkout, and ran once.

- [x] Breadth before depth, and every non-blocking item returned as a question with a
      one-line suggestion: the reviewer brief's steps 2 and 5 and its "what counts"
      ([record](reviews/2026-10-21-harness-reproduction.md#result)).
- [x] Carried threads: `threads.py` attaches the replaced PR's threads under
      `previous`; the brief treats an unanswered ask there as open
      ([record](reviews/2026-10-21-harness-reproduction.md#reproduced-25)).
- [x] The consumer checkout: `review.py` adds the other repository at its stack top
      and the brief's step 7 checks the two sides of the contract
      ([record](reviews/2026-10-21-harness-reproduction.md#third-run-on-the-missed-cases)).
- [x] The states around the diff: the brief's step 6 names the restart, resume,
      blank-input, missing-store, cap and recovery cases
      ([record](reviews/2026-10-21-harness-reproduction.md#third-run-on-the-missed-cases)).
- [x] Measured: the changed reviewer run on the same heads with `THREADS_UNTIL` set
      before the maintainer's round reproduces 25 of his 32 threads, and the third run
      under the four brief changes 28
      ([record](reviews/2026-10-21-harness-reproduction.md)).
- [ ] A second run after fixes and after every cascade is part of the procedure in
      `openmrs-contribution.md`.

## Decisions taken 20 October

- Pre-push probes block; pre-commit keeps only the fast static guards.
- Reviewer, fixer and reply run as separate CLI sessions when an agent fills them; Claude
  Code, Codex CLI and Gemini CLI are supported first, a person always.
- The validation harness is the one evaluation path; the maintainer's cohort and scorer
  are optional inside it; scenarios are an optional review layer.
- Guards are proven by hand-named mutations in the commit, not by PIT or Stryker.
- Default on a push is L0 and L1 only; L2 to L5 are flags.
- A full harness evaluation is a rung of the ladder (L5), run per milestone on the
  approved default matrix (bundled and Hub parity arms, 17 scenarios), producing its own
  report; never a per-PR gate, and a comparison with an earlier run only when asked.
- Optional L5 arms are the profiles the Hub advertises at run time, never a static list.
- No branch naming convention; nothing reads branch names.

## Open

- Whether the umbrella's own repository gets the probe at push or only its unit tests.
- The harness change for checkable expectations: scope and who reviews it.
