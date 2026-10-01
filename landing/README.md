# OpenClinAI landing pages

`landing/` contains the static website configured for publication at <https://openclinai.org/>. Caddy serves
these files directly; there is no application runtime or frontend build step.
The umbrella owns these pages, assets, hosting configuration and publication.
The searchable documentation/status application lives in `site/`.

## Content and navigation

The homepage introduces ChartSearchAI, Catalyst, Med Agent Hub and the Validation
Harness. Keep application entry points balanced and the shared components visible.
Use project pages for demonstrations, transcripts, processing explanations and
contribution resources rather than expanding the homepage.

| Destination | Purpose |
| --- | --- |
| `/` | Initiative, projects, evidence and contribution links |
| `/chartsearchai/` | Patient-chart questions, OpenMRS recordings and integration resources |
| `/catalyst/` | Query/import-to-dashboard workflows, human review and demonstrations |
| `/med-agent-hub/` | Shared model profiles and application integration |
| `/validation-harness/` | Configured experiments, captured evidence and evaluation reports |
| `/catalyst/reporting-pathways/` | Four complementary OpenELIS reporting routes and their limits |
| `/catalyst/questions/`, `/catalyst/hiv-gallery/` | Recorded questions and screenshot walkthroughs |
| `/docs/openmrs-upstream/` | Dated contribution-review evidence |
| `/wahs/` | Shareable WAHS design report, also served on its optional subdomain |

Product-native documentation owns application contracts. The native OpenELIS
CSV-to-Superset route does not require Catalyst or Hub. ChartSearchAI retains a
bundled-provider path. Do not imply every deployment uses all four projects.
Dated recordings, review reports and status snapshots are evidence, not current
requirements, clinical safety or release acceptance.

## Assets and verification

Keep small, reviewed page assets here. Recordings and large screenshots live on
the Catalyst demo host, with explicit URLs, accessible playback controls and
transcripts. Do not introduce video blobs or media symlinks into Git. Preserve
parent navigation, descriptive headings, keyboard focus, reduced-motion styling
and usable narrow-screen layouts.

From the umbrella root:

```sh
python3 scripts/build-landing-sitemap.py
python3 -m pytest -q tests/website
python3 scripts/check-website-links.py
```

The link checker also expects built documentation in `site/dist/`; see the
[website operator guide](../site/README.md) for build and static publication.
Tests cover local links/fragments, assets, media markup and isolated publication
control flow. Inspect actual playback, desktop/phone rendering, keyboard tasks
and text zoom separately; static checks are not browser or deployed acceptance.

The umbrella roadmap tracks ownership and delivery status. Publish only an
explicitly reviewed source revision and record local checks, owner review and
live verification separately. Generated evidence requires review/redaction
before public disclosure.
