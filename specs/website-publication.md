# Website and publication

**Thread:** the documentation site and the openclinai.org landing content ·
**Status:** the documentation site deploys from `main`; the landing site is live
from the umbrella's own website proxy as of 18 October · **Owner:** umbrella

- [x] The documentation site publishes from `main` through the Pages workflow on
      every merge ([latest run](https://github.com/pmanko/openclinai.org/actions/runs/37865757697)).
- [x] The reviewed landing content is deployed to `openclinai.org` and every live
      page matches the checkout
      ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [x] The public contribution page links the current coordination record instead
      of a retired branch
      ([18 October publication](reviews/2026-10-18-landing-publication.md)).
- [x] The VM serves the site from the umbrella's own website proxy
      (`compose/website/`) with no product behind it; the pre-split harness Caddy
      and the OpenMRS demo it fronted are down
      ([record](reviews/2026-10-18-landing-publication.md#the-site-became-its-own-deployment)).
- [ ] The report-catalog provenance mismatch (documentation audit W04) is
      investigated and its disposition recorded.

Broader navigation proposals and the separate landing deployment retain owner
review ([audit](reviews/2026-10-02-documentation-audit.md)).
