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

Verification:

- `targets/validation-harness/.venv/bin/python -m pytest tests/review -q`: 34 passed.
- `python3 -m unittest discover -s tests -v`: 19 passed.
- `python3 scripts/check_workspace.py`: passed in an isolated clean checkout with
  all recorded component pins initialized. The active implementation checkout remains
  at PR heads and is not used as pin-validation evidence.
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

The open-PR campaign is running serially by repository and base-branch dependency.
Its current results are in `work/review/campaign/results.json`; per-PR findings and
execution reports are under `work/review/<component>-<PR>/`. Campaign completion and
review conclusions are not established by the tooling tests above.
