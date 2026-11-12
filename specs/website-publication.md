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

## Standardized `v2` Report Pipeline (`reports.openclinai.org`)

Every published evaluation report on `reports.openclinai.org` follows a single
downstream pipeline and positive `v2` schema contract:

1. **Single Compiler (`harness/validate/report.py`):** All families
   (`chartsearchai`, `wahs`, `catalyst`) compile packets through `build_report()`
   into `report-data.json` (`openclinai.report.v2`), `dashboard-data.json`
   (`openclinai.dashboard.v2`), and `run-summary.json` (`openclinai.summary.v2`),
   paired with `editorial.json` (`openclinai.editorial.v2`). Multi-seed runs
   (`__s42`, `__s43`, ...) consolidate `scenarios` and `judge_rows` onto canonical
   clinical questions (attaching `seed_replicates`) while aggregating `scout`
   (`Benchmark /100`), latency, and safety totals across all `N` cells.
2. **Closed Positive Schema & `Benchmark /100` Readiness Gate:** `scripts/publish-report.py`
   validates exact allowed keysets across all four `v2` JSON files (rejecting any
   unknown key) and requires populated blinded `scout` (`Benchmark /100`) +
   `runs[0].judge` scores on every available featured report unless
   `family == "catalyst"` or `"diagnostic": true` (`--diagnostic`).
3. **Unconditional 4-Tab Viewer Shell + `domain_guardrails`:** `reports/assets/report-shell.js`
   renders only the four standard tabs (`Overview`, `Browse All Questions`,
   `Speed & Multi-User Scaling`, `Methodology & Raw Data`) and opens unconditionally
   on `Overview`. Family-specific deterministic verifiers emit `domain_guardrails`,
   which renders inside `Methodology & Raw Data` without altering the core
   `Benchmark /100` scorecard.
4. **Canonical ISO Dates & Explicit Additive Deploy:** `editorial.json` and
   `run-summary.json` store `date` strictly as ISO `YYYY-MM-DD` (formatted to
   `D Mon YYYY` only when rendering HTML). `scripts/build-reports-index.py` orders
   featured reports deterministically newest-first (`-date`, `-generated_at`,
   `slug`) with no manual `catalog_order` overrides. `publish-report.py stage`
   updates the local checkout; `publish-report.py deploy --slug <slug>` additively
   syncs `reports/<slug>/`, `reports/assets/`, and `reports/index.html` to
   `/srv/openclinai-site/reports/` under explicit operator control.
