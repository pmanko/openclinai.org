# Umbrella review safeguards, 31 October 2026

The review driver now supports explicit fork identities and the umbrella, Hub and
harness checkouts. Review reports account for changed files and preserve requested,
examined, base and consumer revisions. PR head, base and stack-top identity are
checked again after the review. Invalid results fail; incomplete or stale
source reviews remain undetermined. Source review does not certify runtime behavior.
Changed source or consumer checkouts invalidate the run independently of the
revision the reviewer reports.

The pytest and Maven runners read fresh JUnit results, exclude skipped cases, and separate
assertions from collection errors. Pytest uses isolated bytecode lookup for every run;
CI exposed a stale-bytecode case when equal-length fixture edits shared a timestamp. Probe evidence is re-executed, mutations preserve
tests, and restoration is checked. Historical hook baselines are not current evidence.
Fixing/pushing between rounds and evaluation publication require explicit options.
The Vitest adapter now records run completion and unhandled errors separately from
its assertion JSON. A real Vitest 4.1.6 run with one passing assertion and an unhandled
rejection previously returned green through the adapter. The repaired adapter returns
an infrastructure error; real pass, assertion failure, skip, and mixed assertion/runtime
error fixtures returned 0, 1, 3 and 2 respectively. Missing or interrupted execution
reports are rejected. Evidence: `work/review/vitest-exit-fixture/`.

Verification:

- `targets/validation-harness/.venv/bin/python -m pytest tests/review -q`: 35 passed.
- `python3 -m unittest discover -s tests -v`: 19 passed.
- `python3 scripts/check_workspace.py`: passed in an isolated clean checkout with
  all recorded component pins initialized. The active implementation checkout remains
  at PR heads and is not used as pin-validation evidence.
- Website verification in that clean checkout: `python -m pytest tests/website -q`
  passed 123 tests; `npm test` in `site/` passed 47 tests; `npm run build:pages`
  and `python3 scripts/check-website-links.py` passed. This built local artifacts
  without deploying them.
- Harness #205: interface repair `5597288`, diagnostic correction `0059042`;
  seven focused tests and 1,209 full-suite tests passed before the diagnostic-only
  correction; seven focused tests passed again afterward. Remote checks passed.
- Harness #203: calibration-gate repair `1143a89`; seven focused tests and
  1,191 full-suite tests passed. Remote checks passed.
- The actual Hub router with a synthetic two-patient catalog and fixed harness client
  selected the requested patient, preserved the observed 906-token count, resolved
  citations and recognized abstention. No model or deployed service was involved.
  Script and observed output: `work/review/applicability/verify-wahs-contract-fixed.py`
  and `wahs-contract-fixed-output.json`.

Follow-up verification:

- Harness #205 at `c528770` also resolves generated `patient_bundle` filenames to
  catalog IDs while preserving explicit `patient_id` values. The regression failed
  for both filename and relative-path input before the fix. All 12 focused tests
  and 1,214 full-suite tests passed (36 skipped, 3 slow tests excluded); CI passed.
  `work/review/applicability/verify-wahs-generated-case.py` exercised the actual
  Hub `bdba18f` router with a file-backed synthetic catalog. All four requests
  returned 200 for the intended patient; token, citation and abstention checks passed.
- Frontend fork #21 at `b7d9c9b` repairs the missing generated translations and
  validation errors exposed by umbrella #31. Lint, type checks, 780 tests and the
  production build passed; CI passed. Umbrella #31 pins this and the harness fix
  at `97e625b`; 19 unit tests and the post-commit workspace check passed. Live stack
  smoke remains unrun because automatic approval review rejected its data-clearing
  option pending installation approval.

The open-PR campaign collects reviews serially by repository, base-branch
dependency and actual commit ancestry, with explicit consumer revisions for the different feature branches.
Its results are in `work/review/campaign/results-resumed.json`; per-PR findings and
execution reports are under `work/review/<component>-<PR>/`. The local
`work/review/campaign/report.html` includes follow-up adjudications and evidence.
Campaign completion and review conclusions are not established by the tooling
tests above.
