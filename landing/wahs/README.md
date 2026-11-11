# WA Health Summary (WAHS) pages

Canonical URLs:
- `https://openclinai.org/wahs/` (`landing/wahs/index.html`) — Plain-English project overview distinguishing **WA Health Summary (WAHS)** (UW CIRG & WA DOH's patient-mediated health summary on HAPI FHIR with IPS + SMART Health Link sharing) from **WAHS Explorer (OpenClinAI Sandbox)** (`https://wahs-demo.openclinai.org/`), with visual sandbox preview, curated benchmark packets, and clinical/interoperability standards links.
- `https://openclinai.org/wahs/llm-strategy/` (`landing/wahs/llm-strategy/index.html`) — Canonical AI strategy & architecture reference covering patient-mediated workflows, HAPI FHIR integration & prompt caching, cloud/local inference hardware sizing, security/governance, and Section 6 **Engine Internals (`#engine-internals`)** (the 9-budget condensation hierarchy, `ClinicalEntityGraph`, and `Med Agent Hub` bounded enrichment).
- `https://openclinai.org/wahs/walkthrough/` (`landing/wahs/walkthrough/index.html`) — Step-by-step visual walkthrough and reproducible experiments for the WAHS Explorer sandbox (`wahs/demo/index.html`).

`wahs.openclinai.org` redirects with `308` to `https://openclinai.org/wahs/*`, and retired legacy paths (`/wahs/design-report/*` and `/med-agent-hub/wahs-architecture/*`) redirect with `308` to `/wahs/llm-strategy/` and `/wahs/llm-strategy/#engine-internals` via `compose/website/Caddyfile`.

## Verification and publishing

From the umbrella root:

```sh
python3 scripts/build-landing-sitemap.py
python3 scripts/check_workspace.py
python3 scripts/check-website-links.py
pytest -q tests/website
```

Use `./scripts/publish-landing.sh` (without `--landing-only` when `compose/website/Caddyfile` changes, or `--landing-only` for static page-only updates) after merging to `main`.
