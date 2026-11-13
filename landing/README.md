# OpenClinAI landing pages

`landing/` contains the static website configured for publication at <https://openclinai.org/>. Caddy serves
these files directly; there is no application runtime or frontend build step.
The umbrella owns these pages, assets, hosting configuration and publication.
Published evaluation reports live in `reports/` (<https://reports.openclinai.org/>), and the interactive WA Health Summary Patient Chart Explorer demo lives in `wahs/demo/` (<https://wahs-demo.openclinai.org/>).

## Content and navigation

The homepage introduces the four core platform areas (**01 · Client Applications**, **02 · Clinical AI Engine (`Med Agent Hub`)**, **03 · Evaluation Approaches (`Validation Harness`)**, and **04 · Post-Training & Decision-Layer Lab**) and links out to `/projects/` for applied clinical & public-health initiatives. Keep application entry points balanced and the shared components visible.
Use project pages for demonstrations, transcripts, processing explanations and
contribution resources rather than expanding the homepage.

| Destination | Purpose |
| --- | --- |
| `/` | Four-pillar platform overview, architecture strip, evidence and contribution links |
| `/chartsearchai/` | Patient-chart questions, OpenMRS recordings and integration resources |
| `/chartsearchai/comparing-answer-paths/` | Comparing ChartSearchAI's built-in provider with Med Agent Hub |
| `/catalyst/` | Query/import-to-dashboard workflows, human review and demonstrations |
| `/catalyst/reporting-pathways/` | Four complementary OpenELIS reporting routes and their limits |
| `/catalyst/questions/`, `/catalyst/hiv-gallery/` | Recorded questions and screenshot walkthroughs |
| `/med-agent-hub/` | 4-layer clinical AI engine architecture, model profile namespaces, and integration |
| `/validation-harness/` | 4-Layer Clinical Verification Stack, streaming telemetry, and evaluation methodology |
| `/experiments/` | Post-Training & Decision-Layer Lab: Track A (`Laya` ~0.4B System-1 gate) and Track B (5-Rung Post-Training Ladder) |
| `/projects/` | Applied Projects & Clinical Collaborations catalog (WA Health Summary, WHO SMART Guidelines L2→L3) |
| `/wahs/`, `/wahs/llm-strategy/`, `/wahs/walkthrough/` | WA Health Summary project overview, plain-language AI strategy overview for the whole team, and Explorer sandbox walkthrough (`wahs.openclinai.org` redirects 308 to `/wahs/*`) |
| `/wahs/engine-reference/` | Engine reference for developers: service flow, session and scope layers, wire contract, build record, and engine internals (`#engine-internals`). The strategy page keeps stub anchors for the old `#pilot-architecture`, `#wire-contract-details`, `#action-plan` and `#engine-internals` links. Both pages share `/wahs/strategy.css` and `/wahs/toc.js` |
| `/docs/openmrs-upstream/` | Dated OpenMRS upstream pull-request stacks and review evidence |

Product-native documentation owns application contracts. The native OpenELIS
CSV-to-Superset route does not require Catalyst or Hub. ChartSearchAI retains a
bundled-provider path. Do not imply every deployment uses all four projects.
Dated recordings, review reports and status snapshots are evidence, not current
requirements, clinical safety or release acceptance.

## Assets and verification

Keep small, reviewed page assets here. Recordings and large screenshots live in
the public `openclinai-media` Cloud Storage bucket (project `clinical-ai-harness`)
and are linked as `https://storage.googleapis.com/openclinai-media/<project>/<name>`,
with accessible playback controls and transcripts. Never link media or pages on a
demo or product server; those are stopped and redeployed. Give each new file a
dated or hashed name, since uploads are cached for a year, and upload it with:

```sh
gcloud storage cp --cache-control='public, max-age=31536000, immutable' \
  FILE gs://openclinai-media/catalyst/NAME
```

Do not introduce video blobs or media symlinks into Git. Preserve
parent navigation, descriptive headings, keyboard focus, reduced-motion styling
and usable narrow-screen layouts.

From the umbrella root:

```sh
uv run python scripts/build-landing-sitemap.py
uv run pytest -q tests/website
uv run python scripts/check-website-links.py
```

Tests cover local links/fragments, assets, media markup, size caps (`<= 400 KiB` across `landing/`), and isolated publication
control flow. Inspect actual playback, desktop/phone rendering, keyboard tasks
and text zoom separately; static checks are not browser or deployed acceptance.

The umbrella roadmap tracks ownership and delivery status. Publish only an
explicitly reviewed source revision and record local checks, owner review and
live verification separately. Generated evidence requires review/redaction
before public disclosure.

## Publication and branch previews

- **Feature-branch previews (`--preview <slug>`):** From any branch or worktree, run `./scripts/publish-landing.sh --preview <slug>` to sync `landing/` to an isolated preview host at `https://<slug>-preview.openclinai.org/` (and `wahs/demo/` to the disjoint `https://<slug>-preview-demo.openclinai.org/` namespace) with `X-Robots-Tag: noindex, nofollow`. Previews use Caddy on-demand TLS and never modify production directories, `.landing-deploy-receipt.json`, or proxy containers.
- **Production (`openclinai.org`):** Run `./scripts/publish-landing.sh --landing-only` (content only) or `./scripts/publish-landing.sh` (also updates `compose/website/` and `.env.website`, copied from `.env.website.example`) from a clean `main` checkout at or ahead of `origin/main`. Production deploys acquire a remote deploy lock, verify fast-forward ancestry against the VM's `.landing-deploy-receipt.json`, record the new deployed commit, and compare every live HTML/CSS/sitemap file byte-for-byte with the checkout. Pass `--force` only with explicit owner approval; see the [website publication spec](../specs/website-publication.md).
