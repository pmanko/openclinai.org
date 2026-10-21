# Review hooks and probes built and installed (20 October 2026)

Evidence for the first item of [review-process.md](../review-process.md): the L0 guards
and L1 probes under `review/`, installed with `make review-hooks-install`.

| Check | Result |
| --- | --- |
| `pytest tests/review` (fixture pytest project, real git pushes to a bare fork) | 14 passed |
| Same, with the probe's "stays green" verdict flipped to pass | 2 failed (the revert and mutation refusals), so the tests detect a disabled probe |
| `review/bin/probe --repo targets/querystore ff48441` (Maven, offline) | red: 2 of 33 failed with the main file reverted; green: 33 passed; 9 s |
| `review/bin/probe --repo targets/chartsearchai-esm fdd9b5f` (Vitest) | red: 35 of 395 failed with seven main files reverted; green: 395 passed; 9 s |
| Install | `core.hooksPath` set in the umbrella, chartsearchai, chartsearchai-esm and querystore; baseline of already-pushed commits: 126, 53 and 56 |

The baseline means commits pushed to the forks before today are not probed when a
restack rewrites them with the same patch; a commit that changes its patch or adds probe
trailers is probed.
