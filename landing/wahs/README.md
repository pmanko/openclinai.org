# WA Health Summary (WAHS) pages

Canonical URLs:
- `https://openclinai.org/wahs/` (`landing/wahs/index.html`) — Plain-English project overview distinguishing **WA Health Summary (WAHS)** (UW CIRG & WA DOH's patient-mediated health summary on HAPI FHIR with IPS + SMART Health Link sharing) from **WAHS Explorer (OpenClinAI Sandbox)** (`https://wahs-demo.openclinai.org/`), with visual sandbox preview, curated benchmark packets, and clinical/interoperability standards links.
- `https://openclinai.org/wahs/llm-strategy/` (`landing/wahs/llm-strategy/index.html`) — Plain-language AI strategy & architecture overview covering patient-mediated workflows, HAPI FHIR integration & prompt caching, cloud/local inference hardware sizing, security/governance, and compatibility deep-link cards to `/wahs/engine-reference/`.
- `https://openclinai.org/wahs/engine-reference/` (`landing/wahs/engine-reference/index.html`) — Developer & reviewer technical reference covering service-to-service flow (`#pilot-architecture`), worked query trace (`#worked-query-example`), session & scope layers (`#session-and-scope-model`), OpenAI wire contract (`#wire-contract-details`), build record (`#action-plan`), and **Engine Internals (`#engine-internals`)** (2-stage monotonic structural condensation, `[TEMPORAL DIGEST]`, `ClinicalEntityGraph`, and Layer-3 enrichment).
- `https://openclinai.org/wahs/walkthrough/` (`landing/wahs/walkthrough/index.html`) — Step-by-step visual walkthrough and reproducible experiments for the WAHS Explorer sandbox (`wahs/demo/index.html`).

`wahs.openclinai.org` redirects with `308` to `https://openclinai.org/wahs/*`; retired `/wahs/design-report/*` redirects with `308` to `/wahs/llm-strategy/` and `/med-agent-hub/wahs-architecture/*` redirects with `308` to `/wahs/engine-reference/#engine-internals` via `compose/website/Caddyfile`.

## Verification and publishing

From the umbrella root:

```sh
python3 scripts/build-landing-sitemap.py
python3 scripts/check_workspace.py
python3 scripts/check-website-links.py
pytest -q tests/website
```

Use `./scripts/publish-landing.sh` (without `--landing-only` when `compose/website/Caddyfile` changes, or `--landing-only` for static page-only updates) after merging to `main`.
