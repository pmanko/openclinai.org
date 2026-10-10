## Summary

<!-- What changes and why, for the reviewer of this repository. -->

## Verification

<!-- Mechanical checks run and their results (unit tests, check_workspace.py,
     website build and link check, component suites). One-time checks against
     the current acceptance criteria go here as commands and results, not as new
     tests. Dated evidence (counts, hashes, run narratives) belongs in
     specs/reviews/. Approval of this PR is the verification record for
     documentation, specification and website-copy changes. -->

## Checklist

- [ ] No new or changed test asserts hand-written copy, the text of a script,
      Makefile, workflow or compose file, an exact inventory, retired names, PR
      numbers, branch names or roadmap state.
- [ ] New tests run the code against fixtures, or protect an invariant listed in
      AGENTS.md and name it in their docstring.
- [ ] No new tooling marks a requirement satisfied because files contain words.
- [ ] Stream specs changed only by ticking boxes with evidence links; dated
      narrative went to `specs/reviews/`.
