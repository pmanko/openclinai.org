# Local HIV research environment

**Thread:** fresh setup and reset of the local OpenMRS, ChartSearchAI, QueryStore
and Hub stack with the HIV dataset · **Status:** setup and reset restore the
published default baseline in about 5 minutes; Ross's fresh install passed; account
context reaches the model · **Owner:** umbrella (setup, pins, baseline publication)

The [setup guide](../environments/README.md) owns commands, accounts, acceptance
smoke and troubleshooting. This list holds only delivery state.

- [x] Local startup, account logins and the patient-chart smoke passed on an
      existing environment on 3 October
      ([record](reviews/2026-10-02-refactor-closeout.md#status-snapshot)). This did
      not prove a fresh installation.
- [x] One setup command and one start and stop path; duplicate launchers and
      startup-embedded evaluations removed
      ([PR #9](https://github.com/pmanko/openclinai.org/pull/9)).
- [x] The Appointments module startup failure during fresh import has a root cause
      and a fix; a failed module start stops setup honestly
      ([root cause, reproduction and fix](reviews/2026-10-13-appointments-fresh-import-root-cause.md#reproduction)).
      The upstream Core fix is tracked in the
      [OpenMRS contribution stream](openmrs-contribution.md).
- [x] Fresh setup uses one digest-pinned OpenMRS distribution build, including Core,
      instead of a moving tag and a newest-snapshot Core download
      ([record](reviews/2026-10-13-appointments-fresh-import-root-cause.md#fix-options)).
- [x] Fresh setup and reset restore an HIV baseline, the OpenMRS database and
      QueryStore's Elasticsearch snapshot, before OpenMRS starts, so nothing is
      re-embedded; `REBUILD_BASELINE=1` builds the state from the HIV dump, and
      ordinary restart keeps data and index
      ([14 October run](reviews/2026-10-14-fresh-setup-acceptance.md): rebuild
      1 h 31 min, restore 3 min, restart 68 s, on the owner's machine).
- [x] The default HIV baseline is published on GitHub Container Registry, pinned
      by digest, and fresh setup pulls it without a login; any state can be
      exported and published as a named alternate baseline
      ([publication and clean-machine reset](reviews/2026-10-14-fresh-setup-acceptance.md#clean-machine-reset-from-the-registry)).
- [x] Both clean-start paths are proven with the real application, and Ross
      completes a fresh installation from the guide
      ([record](reviews/2026-10-14-fresh-setup-acceptance.md#second-machine-15-october)).
- [x] ChartSearchAI sends the signed-in account's roles and session location to
      the Hub: `9416ffa` cherry-picked onto the pinned line as the next slice after
      Backend #590, superseding fork PR #33
      ([fork #35](https://github.com/pmanko/openmrs-module-chartsearchai/pull/35)).
- [x] The Hub reads that context and adds one line, `Requester: <assigned roles>
      at <session location>`, to the answer and In-Depth prompts and to the turn
      trace; nothing else about the account is sent to the model
      ([Hub #34](https://github.com/pmanko/med-agent-hub/pull/34)).
- [x] `main` pins both heads, and a reset with the published baseline followed by
      a question as two different evaluation accounts shows each account's line
      in the Hub trace and `accountContext` on the saved turn
      ([record](reviews/2026-10-16-account-context.md)).
- [ ] A default baseline for the 18 October ChartSearchAI heads is rebuilt from the
      HIV dump, published and pinned before `main` pins those heads. Changeset
      `chartsearchai-010` dropped the conversation title column on 18 October, so
      the 14 October baseline's database fails the module's Liquibase validation on
      the new heads; Ross's 15 October install needs a reset once the new baseline
      is pinned.
- [ ] Setup needs only Docker and the native model router: the pinned modules,
      frontend bundle and embedding model ship in published images instead of
      being built on the host with Java, Maven, Node and Yarn. Module builds
      currently compile against the newest Core snapshot rather than the pinned
      Core.

Role-specific instructions and answer caching, model evaluations, demonstrations
and publication are separate work, not setup gates.
