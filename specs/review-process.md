# Review process and gates

**Stream:** review rigor · **Status:** designed 20 October 2026, nothing built; the
owner is marking this up · **Owner:** umbrella; each component repository keeps its
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

L0 and L1 are the default on every push. L2 to L4 run through `make review`.

## Parameters

```
make review PR=<n> [REPO=chartsearchai|esm|querystore] [AGENT=claude|codex|gemini|human]
            [EFFORT=low|medium|high] [ROUNDS=1] [STACK=1] [SCENARIOS=<set>] [GATE=<name>]
```

| Effort | Sweep |
| --- | --- |
| low | correctness and the test-coverage rule on the diff; blocking findings only |
| medium | plus trace one level out: unchanged neighbours, consumers of what the code emits, lifecycle, the merged result of the branch |
| high | plus security and performance dimensions, uncertain findings returned as questions, a refutation pass on each blocking finding |

`STACK=1` adds the contracts between layers (what one PR emits against what the PRs
above and below consume) and reads the stack's merged top. `ROUNDS` above 1 repeats
review and fix until the reviewer records zero blocking findings on the pushed head,
and every round after a clean one is blocking-only. `SCENARIOS` and `GATE` are off
unless named.

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
  bin/
    threads.py           open threads per PR into work/review/<repo>-<pr>/threads.json
    probe-revert.sh      <repo> <commit>: split main and test files, revert main files to
                         the parent, run the tests, expect red, restore, expect green
    probe-mutate.sh      <repo> <commit>: apply each Mutation: trailer, run Tests:,
                         expect red, restore
    runners/             maven.sh, jest.sh, pytest.sh: "run these tests, exit non-zero on
                         failure" for each build system; the umbrella's own tests use the
                         pytest runner on a fixture project
    role.sh              --agent --role --pr --effort: starts a fresh session with the
                         brief and the inputs, collects the JSON
    deploy-head.sh       build the PR head, deploy to the local stack, check the loaded
                         class hash against the build, print the module version
    review.py            drives `make review`: threads, role runs, probes, scenarios,
                         gate, the round record
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

The pre-push hook probes every commit the push adds that touches main code, in a
persistent probe worktree under `work/review/wt/<repo>` so Maven compiles incrementally.

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
| pre-commit | all | a likely secret; a focused or disabled test; a new test file with no assertion; malformed `Tests:` or `Mutation:` trailer | a mocked unit under test; narrative comments |
| commit-msg | all | trailer syntax | |
| pre-push | components | a push to any `openmrs/` remote; a force push without lease; a probed commit whose tests stay green under revert or mutation; a main-code commit with no tests, no `Tests:` and no `Probe: skip` | the red and green lines, into the ledger |
| pre-push | umbrella | `python3 -m unittest` or `check_workspace.py` failing | |

The existing agent-side guards (`claude-code-guards`, PreToolUse on Bash) stay for the
in-chat commit review; the git hooks carry the same checks so they hold for Codex, Gemini
and a person at a terminal.

## Scenarios and gates in the harness

- A review scenario set is a harness comparison set whose expectations are machine
  checkable: records that must be cited or present in the context, abstention, a refusal.
  Today the harness's expectations are notes for a human adjudicator; adding checkable
  expectations is a harness change in its own repository under its constitution.
- The maintainer's cohort (chartsearchai `eval/drift-metric/` gold files) and his
  citation-F1 scorer become an optional dataset and scoring path in the harness, beside
  our five-chart cohort. `work/eval-88/` retires into that.
- A gate file is written before the run: comparison set, dataset, baseline run id and
  number, threshold, date, who signed off. A threshold set after seeing the number is not
  a gate. The result goes in a dated record under `reviews/`.

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

- [ ] Hooks and probes: `review/hooks/`, `review/bin/probe-revert.sh`,
      `probe-mutate.sh`, the three runners, `make review-hooks-install`; behaviour tests
      on a pytest fixture project under `tests/`; installed in the three component
      checkouts and the umbrella.
- [ ] Threads, briefs and roles: `threads.py`, the four briefs, `role.sh` for claude,
      codex, gemini and human, `review.py` and `make review` with `EFFORT`, `ROUNDS`,
      `STACK`.
- [ ] Deployed-head scenarios: `deploy-head.sh`; harness checkable expectations (harness
      PR); a `review-smoke` comparison set; `SCENARIOS=`.
- [ ] Gates: the cohort and the maintainer's gold as harness datasets, the citation
      scorer path, `review/gates/`, `GATE=`; `work/eval-88/` retired.
- [ ] Applied to the open round: the twelve blocking findings fixed under L0 to L2 with
      probes and replies from the ledger; recorded under `reviews/`.
- [ ] `openmrs-contribution.md` review-round rules point here instead of restating them.

## Decisions taken 20 October

- Pre-push probes block; pre-commit keeps only the fast static guards.
- Reviewer, fixer and reply run as separate CLI sessions when an agent fills them; Claude
  Code, Codex CLI and Gemini CLI are supported first, a person always.
- The validation harness is the one evaluation path; the maintainer's cohort and scorer
  are optional inside it; scenarios are an optional review layer.
- Guards are proven by hand-named mutations in the commit, not by PIT or Stryker.
- Default on a push is L0 and L1 only; L2 to L4 are flags.
- No branch naming convention; nothing reads branch names.

## Open

- Whether the umbrella's own repository gets the probe at push or only its unit tests.
- The harness change for checkable expectations: scope and who reviews it.
- Whether a mutation that cannot be expressed as one textual replacement gets a patch
  file form, or stays out of the hook and in the fixer's record.
