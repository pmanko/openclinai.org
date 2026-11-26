# WA Health Summary (WAHS) pages

Canonical URLs:
- `https://openclinai.org/wahs/` (`landing/wahs/index.html`) · Plain-English project overview distinguishing **WA Health Summary (WAHS)** (UW CIRG & WA DOH's patient-mediated health summary on HAPI FHIR with IPS + SMART Health Link sharing) from **WAHS Explorer (OpenClinAI Sandbox)** (`https://wahs-demo.openclinai.org/`), with visual sandbox preview, curated benchmark packets, and clinical/interoperability standards links.
- `https://openclinai.org/wahs/llm-strategy/` (`landing/wahs/llm-strategy/index.html`) · Plain-language AI strategy & architecture overview covering patient-mediated workflows, HAPI FHIR integration & prompt caching, H200 model selection (`Gemma 4 26B` primary with `Gemma 4 12B` compact option), security/governance, and compatibility deep-link cards to `/wahs/engine-reference/`.
- `https://openclinai.org/wahs/engine-reference/` (`landing/wahs/engine-reference/index.html`) · Developer and reviewer architecture reference covering service-to-service flow, explicit scope boundaries (`#pilot-architecture`), worked query trace (`#worked-query-example`), session & scope layers (`#session-and-scope-model`), OpenAI wire contract (`#wire-contract-details`), milestones (`#action-plan`), and **Engine Internals (`#engine-internals`)** (continuous 3-tier verbatim-first condensation and modular research extensions).
- `https://openclinai.org/wahs/engine-audit/` (`landing/wahs/engine-audit/index.html`) · Design and rationale overview for standalone `wahs-engine`, featuring the 3-step Core Baseline + optional extension interface SVG diagram (`#high-level-architecture`), explicit scope boundaries (including deferred patient privacy), foundational standards links (`#foundational-pillars`), subsystem overview (`#wahs-core-audit`, `#wahs-engine-runtime`), ecosystem integration (`#ecosystem-alignment`), 900-cell H200 benchmark readout (`#empirical-benchmarks`), and five core design principles (`#audit-findings`).
- `https://openclinai.org/wahs/walkthrough/` (`landing/wahs/walkthrough/index.html`) · Step-by-step visual walkthrough and reproducible experiments for the WAHS Explorer sandbox (`wahs/demo/index.html`).

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
