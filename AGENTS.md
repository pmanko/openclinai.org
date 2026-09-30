# Working in OpenClinAI

- Start with `specs/roadmap.md`; it is the umbrella coordination authority.
- `specs/architecture.md` supports design decisions; it is not another task list.
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
