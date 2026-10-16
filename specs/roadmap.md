# OpenClinAI Roadmap

This is the coordination index for the OpenClinAI workspace. Each delivery stream
has one focused spec written as a target path with checkboxes; dated evidence lives
in [`reviews/`](reviews/). [Architecture](architecture.md) owns component
boundaries, product repositories own application behavior, and the harness owns
experiments. The workspace refactor that created this layout
(`PR-DECOMPOSITION-2026-09`) is complete and closed in its
[closeout record](reviews/2026-10-02-refactor-closeout.md).

## Current priorities

1. [OpenMRS contribution delivery](openmrs-contribution.md): dispose of the open
   #587 context-composition finding and the QueryStore #68 split request, then
   obtain ordinary dependency compatibility and remove the temporary paired CI.
2. [Local HIV research environment](#local-hiv-research-environment): setup needs
   only Docker and the native model router.
3. [Catalyst delivery](catalyst-delivery.md): owner acceptance of the four local and
   server journeys and publication verification.
4. [Website and publication](#website-and-publication): deploy the reviewed landing
   content and close the public findings from the documentation audit.
5. [Decision-layer experiment](decision-layer-experiment.md): owner review of the
   proposal.

Upstream merging, deployment changes and release or clinical signoffs are not
authorized by any item here; each stream spec names its signoffs.

## Streams

| Stream | Spec | State | Next |
| --- | --- | --- | --- |
| OpenMRS contribution (Track A) | [openmrs-contribution.md](openmrs-contribution.md) | Thirteen PRs restacked and checked; QueryStore #68 open; #587 finding open | Dispositions for #587 and the #68 split request |
| Workspace and validation refactor (Track B) | [closeout record](reviews/2026-10-02-refactor-closeout.md) | Complete, 2 October | None |
| Local HIV research environment | [setup guide](../environments/README.md) and the list below | Setup and reset restore the published default baseline in about 5 minutes; Ross's fresh install passed; account context reaches the model | Docker-only prerequisites |
| Catalyst delivery | [catalyst-delivery.md](catalyst-delivery.md) | Four journeys demonstrated; acceptance open | FP-009 and FP-010 |
| Website and publication | list below | Documentation site deploys from `main`; landing deployment pending | Publish the reviewed landing content |
| Decision-layer experiment | [decision-layer-experiment.md](decision-layer-experiment.md) | Proposed | Decisions D1–D4 |

## Local HIV research environment

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
- [ ] Setup needs only Docker and the native model router: the pinned modules,
      frontend bundle and embedding model ship in published images instead of
      being built on the host with Java, Maven, Node and Yarn. Module builds
      currently compile against the newest Core snapshot rather than the pinned
      Core.

Role-specific instructions and answer caching, model evaluations, demonstrations
and publication are separate work, not setup gates.

## Website and publication

- [x] The documentation site publishes from `main` through the Pages workflow on
      every merge ([latest run](https://github.com/pmanko/openclinai.org/actions/runs/37865757697)).
- [ ] The reviewed landing content is deployed to `openclinai.org` and live links
      are checked (documentation audit findings D05 to D07).
- [ ] The public contribution page links the current coordination record instead
      of a retired branch.
- [ ] The report-catalog provenance mismatch (documentation audit W04) is
      investigated and its disposition recorded.

Broader navigation proposals and the separate landing deployment retain owner
review ([audit](reviews/2026-10-02-documentation-audit.md)).

## Standing checks

- `Workspace` workflow: umbrella unit tests and `scripts/check_workspace.py` on a
  recursive checkout.
- `operations` workflow: workspace operation tests, the assembled QueryStore and
  ChartSearchAI source build, and ESM verification.
- Pages workflow: website tests, build, rendered link and asset checks, deploy.
- Harness independence is asserted by `tests/test_operation_ownership.py`. Product,
  deployed-runtime and clinical acceptance need real-interface evidence recorded in
  the stream specs.

## Outstanding decisions

- **Hub pin:** `targets/med-agent-hub` records the head of Hub
  [#33](https://github.com/pmanko/med-agent-hub/pull/33) rather than Hub `main`.
  Merge #33 or keep the dependency visible here until it merges.
- **Data tooling:** assign a maintained owner for reusable migration and
  terminology utilities outside the validation runner.
- **Public hosting:** decide repository organization, visibility or hosting changes
  separately from documentation cleanup.
- **External consumers:** the Hub README and Catalyst documents link roadmap
  section anchors that no longer exist; update them when those components next
  publish.
- **Decision-layer experiment:** decisions D1 to D4 are recorded in
  [its spec](decision-layer-experiment.md).

## Evidence

- [2 October documentation audit](reviews/2026-10-02-documentation-audit.md)
- [2 October refactor closeout](reviews/2026-10-02-refactor-closeout.md)
- [7 October context evaluation](reviews/2026-10-07-context-evaluation.md)
- [14 October fresh setup acceptance](reviews/2026-10-14-fresh-setup-acceptance.md)
- [16 October account context](reviews/2026-10-16-account-context.md)
- [7 October Track A remediation record](reviews/2026-10-07-track-a-remediation.md)
- [10 October revamp audit and experiment proposal](reviews/2026-10-10-revamp-audit-and-jev-experiment.md)
- [13 October Appointments fresh-import root cause](reviews/2026-10-13-appointments-fresh-import-root-cause.md)
