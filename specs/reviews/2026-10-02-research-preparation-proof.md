# HIV Setup: Partial Startup Observations

Observed 2-3 October 2026 before the scope cleanup. These are earlier runtime
observations, not proof that the current public setup command is complete.

- The pinned QueryStore, ChartSearchAI and frontend builds succeeded.
- The existing HIV archive imported 5,334 patients, 14,322 encounters and
  428,036 observations.
- The stock demo-data module initially generated 50 extra patients and blocked
  startup. This was a real setup failure.
- Setting `referencedemodata.createDemoPatients=false` through the native
  `openmrs-extra.properties` startup path prevented generation. The corrected
  startup retained the imported counts.
- The standard `admin` / `Admin123` login succeeded; the authenticated session
  and FHIR Patient API were usable, and ChartSearchAI and QueryStore reported
  started.

The tested disposable environment used umbrella revision
`5116e8602bc9f216a2b1f385fa930e87a761d0d1` plus the working startup/import fix.
Component pins were unchanged. Its custom preparation wrapper has since been
removed; it is not the procedure researchers should use.

The remaining work is connecting the native setup command and seven-account
provisioner, then smoke-checking OpenMRS, ChartSearchAI availability and sampled
HIV records. The observations above do not close that work.

The [current roadmap](../reusable-environments-roadmap.md) and
[operator guide](../../environments/README.md) define the intended setup.
