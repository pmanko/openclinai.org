# Website and publication

**Thread:** `openclinai.org` static platform site, `reports.openclinai.org` evaluation archive, `wahs-demo.openclinai.org` sandbox, and isolated `<slug>-preview.openclinai.org` branch previews ·
**Status:** GitHub Pages serves only canonical redirects to `openclinai.org` and `reports.openclinai.org`; production static hosts deploy from clean `main` checkouts with remote fast-forward receipt protection · **Owner:** umbrella

- [x] GitHub Pages (`pages.yml`) runs website link/contract checks on pull requests and deploys a minimal canonical redirect bundle to `https://openclinai.org/` and `https://reports.openclinai.org/` on `main` ([PR #39](https://github.com/pmanko/openclinai.org/pull/39)).
- [x] The reviewed landing content is deployed to `openclinai.org` and every live page matches the checkout ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [x] The public contribution page links the current coordination record instead of a retired branch ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [x] The VM serves the site from the umbrella's own website proxy (`compose/website/`) with no product behind it; the pre-split harness Caddy and the OpenMRS demo it fronted are down ([record](reviews/2026-10-18-landing-publication.md#the-site-became-its-own-deployment)).
- [x] `scripts/publish-landing.sh` enforces clean-tree, `main` / `origin/main` ancestry, remote deploy locking, and `.landing-deploy-receipt.json` fast-forward checks on production deploys, and supports isolated HTTPS branch previews at `https://<slug>-preview.openclinai.org/` via `--preview <slug>` ([publish-landing.sh](../scripts/publish-landing.sh), [test_publish_landing.py](../tests/website/test_publish_landing.py)).
- [ ] The report-catalog provenance mismatch (documentation audit W04) is investigated and its disposition recorded.

Broader navigation proposals and the separate landing deployment retain owner review ([audit](reviews/2026-10-02-documentation-audit.md)).
