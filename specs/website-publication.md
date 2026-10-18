# Website and publication

**Thread:** the documentation site and the openclinai.org landing content ·
**Status:** the documentation site deploys from `main`; the reviewed landing content
is live as of 18 October, served by the VM's old harness proxy; the switch to the
umbrella's website proxy is open · **Owner:** umbrella

- [x] The documentation site publishes from `main` through the Pages workflow on
      every merge ([latest run](https://github.com/pmanko/openclinai.org/actions/runs/37865757697)).
- [x] The reviewed landing content is deployed to `openclinai.org` and every live
      page matches the checkout
      ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [x] The public contribution page links the current coordination record instead
      of a retired branch
      ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [ ] The VM serves the site from the umbrella's own website proxy
      (`compose/website/`) instead of the pre-split harness Caddy, so the publish
      script's default target is the served directory. Until then, publish with
      `GCP_REMOTE_REPO=clinical-ai-validation-harness`
      ([why](reviews/2026-10-18-landing-publication.md#what-served-the-site)).
- [ ] The report-catalog provenance mismatch (documentation audit W04) is
      investigated and its disposition recorded.

Broader navigation proposals and the separate landing deployment retain owner
review ([audit](reviews/2026-10-02-documentation-audit.md)).
