# Stack review and canonical issues (STACK=1)

Review the supplied layer snapshots and the assembled top. Read each layer's
incremental change and trace contracts across layers. Test the top and check
whether later changes repair, bypass or reintroduce earlier failures.

Report each root cause once. Consult the repository issue ledger before inventing
an issue key. Rewording, moved lines, additional affected descendants, or a question
that now has reproduction evidence do not create a new issue. Similar wording does
not prove two failures share a cause. Separate different causes and regressions.

Every finding must add these fields to the ordinary finding schema:

- `issue_key`: stable lowercase root-cause name, reused from the ledger.
- `introduced_commit`: full commit that introduced or activated the failure.
- `origin_file`: a file changed by that commit.
- `origin_evidence`: explain the inspected introducing diff, why earlier layers
  lack this cause, and the reproduction or source comparison supporting ownership.
  Blame alone does not establish causation. A later configuration can activate old code.
- `owner_pr`: the earliest open layer introducing that change, or null when no
  open PR owns it. Do not assign baseline defects to the first open PR.
- `affected_prs`: only layers actually checked for this cause. Do not assume that
  every descendant is affected; later layers may fix it. Name the per-layer evidence
  in `origin_evidence`. Unknown layers remain unverified.
- `attribution_status`: `open`, `baseline`, or `unattributed`. Missing ownership
  evidence means `unattributed`; it cannot become a publishable blocker.
- `regression_of`: optional prior issue key when a later change reintroduces a
  resolved defect. Use a new key and introducing commit for that regression.

The driver validates commit ownership, snapshot membership and complete observation
coverage, maintains shared issue identities, and writes `stack_plan`. Publication
renders full action items only on their owners and links from affected descendants.
Stack mode is report-only: it never chooses a product branch to fix automatically.
