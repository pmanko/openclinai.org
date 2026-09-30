# Working in OpenClinAI

- Start with `specs/roadmap.md`; it is the umbrella coordination authority.
- `specs/architecture.md` supports design decisions; it is not another task list.
- Keep each decision, phase status and requirement in its owning document. Link
  product specifications and detailed task registers instead of copying them.
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
  never reset or import dirty sibling worktrees as part of a spec slice.
- Product submodules remain nested under the harness until a reviewed path
  migration. Gitlinks are canonical pins; do not add duplicate product pins.
- Read component instructions before edits. Commit/publish component changes in
  their own repository before updating the umbrella gitlink to a reachable commit.
- Run `python3 -m unittest discover -s tests -v` and
  `python3 scripts/check_workspace.py` for umbrella changes. These checks are
  not component, deployed-runtime or release acceptance.
