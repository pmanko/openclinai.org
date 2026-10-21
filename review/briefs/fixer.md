# Fixer brief

Whoever writes the fix follows this: a person, or an agent session on the PR branch.

1. **Reproduce first.** Run the failure the finding describes, or write the test that
   shows it, and see it fail for the stated reason.
2. **Strictest assertion.** Assert the runtime effect, through the production path,
   with no reimplementation in the test. If it does not fail, tighten it until it does.
3. **Fix in the owning PR**, the smallest change that makes the test pass. Nothing
   outside the finding; note anything else you saw in the ledger instead.
4. **Name the guard.** Put `Tests:` with the tests that prove the fix and one
   `Mutation:` per guard you added (the check deleted, `<` for `<=`, `&&` for `||`,
   the computed value replaced by the plain one) in the commit's final paragraph.
5. **Push.** The pre-push hook runs the revert and mutation probes; a refusal means
   the test does not prove the fix. Fix the test, never `--no-verify`.
6. **Decline on the record.** A finding you do not implement gets a failure-mode
   sentence for why the code is right, with the evidence, in the round's ledger.
7. Run the full suite of the layer and restack the layers above before handing back.
