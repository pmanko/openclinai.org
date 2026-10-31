# Umbrella review safeguards, 31 October 2026

The review driver now supports explicit fork identities and the umbrella, Hub and
harness checkouts. Review reports account for changed files and preserve requested,
examined, base and consumer revisions. Invalid results fail; incomplete or stale
source reviews remain undetermined. Source review does not certify runtime behavior.

The pytest runner reads fresh JUnit results, excludes skipped cases, and separates
assertions from collection errors. Probe evidence is re-executed, mutations preserve
tests, and restoration is checked. Historical hook baselines are not current evidence.
Fixing/pushing between rounds and evaluation publication require explicit options.

Verification:

- `targets/validation-harness/.venv/bin/python -m pytest tests/review -q`: 30 passed.
- `python3 -m unittest discover -s tests -v`: 19 passed.
- `python3 scripts/check_workspace.py`: failed because four components are
  uninitialized and the Hub/harness checkouts are at PR heads rather than umbrella pins.
- Harness #205: interface repair `5597288`, diagnostic correction `0059042`;
  seven focused tests and 1,209 full-suite tests passed before the diagnostic-only
  correction; seven focused tests passed again afterward. Remote checks passed.
- Harness #203: calibration-gate repair `1143a89`; seven focused tests and
  1,191 full-suite tests passed. Remote checks pending at this record's creation.
- The actual Hub router with a synthetic two-patient catalog and fixed harness client
  selected the requested patient, preserved the observed 906-token count, resolved
  citations and recognized abstention. No model or deployed service was involved.
  Script and observed output: `work/review/applicability/verify-wahs-contract-fixed.py`
  and `wahs-contract-fixed-output.json`.

The open-PR campaign is running serially by repository and base-branch dependency.
Its current results are in `work/review/campaign/results.json`; per-PR findings and
execution reports are under `work/review/<component>-<PR>/`. Campaign completion and
review conclusions are not established by the tooling tests above.
