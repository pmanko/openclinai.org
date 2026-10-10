# Working in OpenClinAI

- Start with `specs/roadmap.md`; it is the umbrella coordination index. Each
  delivery stream has one focused spec in `specs/` written as a target path with
  checkboxes. Tick a box only with a link to its evidence. Record dated
  verification (test counts, hashes, run narratives) in `specs/reviews/`, never in
  the index or a stream spec. A completed plan becomes a dated closeout record.
- `specs/architecture.md` supports design decisions; it is not another task list.
- Write and review for each document's audience: README, website and repository
  description for new users; roadmap for implementing agents; architecture for
  technical readers; AGENTS.md for repository working rules. Evaluate clarity and
  completeness for that audience separately from automated link/structure checks.
- Keep our cross-project integration specifications, acceptance requirements,
  roadmap and process documents in this umbrella. Do not add them to OpenMRS-owned
  repositories or their forks. Native module setup/API documentation remains with
  the module; umbrella documentation cleanup does not require module doc PRs.
- Keep each decision, phase status and requirement in its owning document. Link
  product specifications and detailed task registers instead of copying them.
- Add only material required by the new architecture. Do not import legacy
  directory trees, tooling or plans wholesale into the umbrella.
- Read the owning repository's instructions and current contracts before changing
  a component. This coordination project does not override product governance.
- Maintained specs describe current state or current implementation direction only.
  Reconcile or delete obsolete content; do not retain superseded banners, archived
  specs, old-plan appendices or placeholder documents. Git history owns past specs.
- Keep each current requirement with one maintained owner and update consumers
  directly when it moves. Preserve IDs for retained requirements, not obsolete text.
- Treat dated sitreps, run reports and memory as evidence, not current requirements;
  evidence retention does not justify retaining obsolete specifications.
- Update the roadmap's current focus when priorities change. Separate
  implementation, verification and publication.
- Use `targets/validation-harness` for this umbrella's implementation checkout;
  never reset or import unrelated changes from dirty sibling worktrees.
- The umbrella owns component gitlinks, version pins, checkouts, builds,
  deployment and release coordination. Remove these responsibilities from the
  harness; do not replace them with configurable harness-owned management.
- Keep openclinai.org website content, assets, site configuration, build tooling
  and deployment workflows in this repository. The harness produces validation
  artifacts; the umbrella owns their publication to OpenClinAI web properties.
- The harness is a modular validation runner. It must not require Git, submodules,
  product pins, local product source trees or the umbrella to run experiments.
  It records supplied or observed target provenance; it does not enforce pins.
- Implement the intended architecture, not backward compatibility with the old
  layout. Change paths, commands, imports and configuration and update consumers
  directly. Delete obsolete code and specs; Git history holds previous versions.
  Add a compatibility mechanism only for an explicit current requirement.
- Establish product repositories as direct umbrella submodules with one canonical
  gitlink each. Remove the harness's product gitlinks and the openmrs_chatbot target.
- Read component instructions before edits. Commit/publish component changes in
  their own repository before updating the umbrella gitlink to a reachable commit.
- Run `python3 -m unittest discover -s tests -v` and
  `python3 scripts/check_workspace.py` for umbrella changes. These checks are
  not component, deployed-runtime or release acceptance.

## Local HIV Environment

- `environments/README.md` owns prerequisites, setup/start/stop instructions,
  account logins and troubleshooting. Keep it aligned with the existing Make targets.
- Reuse the existing build, HIV import, configuration and account tools. Do not
  add an environment framework, migration/backup flow or generated service password.
- Fresh setup replaces the local database; ordinary startup retains it. Never
  generate stock patients or silently change the selected inference provider.
- Leave other installations alone. Changing someone else's running environment
  or publishing reports/demos requires their approval.
- Use checked Gemma 4 12B by default. Smaller models are explicit comparisons.
- Setup proof is a live smoke: log into OpenMRS, inspect known HIV patient records,
  and open ChartSearchAI on a patient chart. Provisioning checks the seven account
  logins. Model evaluations, reports and videos are separate functionality work.
- Keep completed setup instructions in the guide, not a separate implementation
  roadmap or review diary. Git history and PRs retain the work's past record.
