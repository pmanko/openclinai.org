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
2. [Local HIV research environment](#local-hiv-research-environment): unblock the
   fresh installation for Ross.
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
| Local HIV research environment | [setup guide](../environments/README.md) and the list below | Setup verified 3 October; fresh install blocked | PR #9 review; Appointments startup root cause |
| Catalyst delivery | [catalyst-delivery.md](catalyst-delivery.md) | Four journeys demonstrated; acceptance open | FP-009 and FP-010 |
| Website and publication | list below | Documentation site deploys from `main`; landing deployment pending | Publish the reviewed landing content |
| Decision-layer experiment | [decision-layer-experiment.md](decision-layer-experiment.md) | Proposed | Decisions D1–D4 |

## Local HIV research environment

The [setup guide](../environments/README.md) owns commands, accounts, acceptance
smoke and troubleshooting. This list holds only delivery state.

- [x] Fresh HIV baseline, both ChartSearchAI providers and the seven accounts
      provision from `make chartsearch-research-setup`; the 3 October local smoke
      passed ([record](reviews/2026-10-02-refactor-closeout.md#status-snapshot)).
- [ ] One setup, start and stop path: duplicate launchers and startup-embedded
      evaluations removed ([PR #9](https://github.com/pmanko/openclinai.org/pull/9),
      open).
- [ ] The Appointments startup failure during fresh import has a root cause and a
      fix or an upstream issue; a failed module start stops setup honestly.
- [ ] Fresh setup offers a full rebuild and a matching cached-index restore in the
      same command, using Elasticsearch's native snapshot API and QueryStore
      completion records; unchanged HIV data is not re-embedded, and ordinary
      restart retains data and index without reindexing.
- [ ] Both clean-start paths are proven with the real application, and Ross
      completes a fresh installation from the guide.

Account-context enhancements, model evaluations, demonstrations and publication
are separate work, not setup gates.

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

- `Workspace` workflow: umbrella unit tests, including the roadmap shape rules, and
  `scripts/check_workspace.py` on a recursive checkout.
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
- [7 October Track A remediation record](reviews/2026-10-07-track-a-remediation.md)
- [10 October revamp audit and experiment proposal](reviews/2026-10-10-revamp-audit-and-jev-experiment.md)
