# OpenClinAI website

The umbrella owns the public website sources, assets, configuration and delivery:

- `landing/`: static project pages, galleries, posters and styles configured for publication at `openclinai.org`.
- `site/`: documentation, searchable static HTML twins, status interface and reviewed Catalyst design assets.
- `site/published-content.ts`: the explicit public source allowlist. Navigation and topics must resolve to these sources. Product contracts are linked, not copied.
- `compose/website/`: independent Caddy static hosting; it contains no product services.
- `scripts/publish-landing.sh`, `scripts/publish-report.sh`, `scripts/reports-backup.sh`: static publication to an existing VM and versioned report backup.
- `.github/workflows/pages.yml`: configured documentation/status GitHub Pages publication from this repository.

## Local verification

From the umbrella root, use an environment with the existing test dependencies
`pytest` and `PyYAML`; no harness installation is needed:

```sh
python3 -m pytest -q tests/website
python3 scripts/build-landing-sitemap.py
```

From `site/`:

```sh
npm ci
npm test
npm run build:pages
```

Then, from the umbrella root:

```sh
python3 scripts/check-website-links.py
```

`npm run build` builds documentation and full-HTML twins into `site/dist/`.
`build:pages` also builds the status interface into `site/dist/status/`. The status
build publishes the selected dated evaluation summaries in `site/status/model.ts`
and links to their report evidence. No component checkout or harness installation
is required. Documentation uses the Pages project
base `/openclinai.org/` and links back to the static landing site.

For a local static landing preview, use any static web server rooted at `landing/`.
For documentation, run `npm run preview` from `site/` after building.

## Static publication

Publishing is an explicit operator action; verification commands above do not
publish. The VM must already exist. Configure the connection with `GCP_PROJECT`,
`GCP_ZONE`, `GCP_VM_NAME`, `GCP_SSH_USER`, `GCP_SSH_KEY` and `GCP_REMOTE_REPO`
(default remote serving directory: `openclinai.org`). The connection helpers do
not create VMs, update firewalls, synchronize a checkout or deploy applications.

Copy `.env.website.example` to the ignored `.env.website` and set the hostnames,
TLS contact and published ports. `scripts/publish-landing.sh` updates only
`landing/` and `compose/website/`, using Compose project `openclinai-website`.
`--landing-only` changes content without changing configuration or restarting a
service. Media referenced on the Catalyst demo host is checked before and after
publication; HTML/CSS/sitemap bytes are compared with the live output.

Report publication consumes an already rendered, reviewed/redacted evidence
packet containing `report.html`, its relative assets/evidence and recorded run
metadata. Generate reports with the harness separately; publication does not
run the renderer or freeze dashboards. Optional `comparison.html` and
`dashboard.html` are copied if supplied. From the umbrella root:

```sh
PUBLISH_DRY_RUN=1 scripts/publish-report.sh catalyst /path/to/reviewed-run example-report
```

Dry-run staging changes only `REPORTS_ROOT` (default `artifacts/reports/`). Omit
`PUBLISH_DRY_RUN=1` only when deliberately uploading. Set `CADDY_SITE_REPORTS`
(default `reports.openclinai.org`) and a pre-created, versioned
`REPORTS_BACKUP_BUCKET`. Successful upload requires a successful additive backup.
The catalog reads staged evidence and optional recorded `meta.json` summaries;
it never resolves live models, product Git revisions or the original run tree.
Review/redaction is required before publishing any clinical evidence.

## Catalyst design review

`site/public/catalyst-design/` contains generated publication copies, not design
sources. Edit the Catalyst repository's `docs/specs/` sources. The umbrella's
operations owner maintains `scripts/sync-catalyst-design.py` and its verification
in `tests/operations/`; design synchronization is separate from runtime pins.

From the umbrella root:

```sh
python3 scripts/sync-catalyst-design.py --source targets/catalyst --revision FULL_COMMIT
python3 scripts/sync-catalyst-design.py --source targets/catalyst --revision FULL_COMMIT --check
```

Review and version the generated assets and `source.json` together. The manifest
records the reviewed source revision and hashes. OpenELIS screens/styles remain
owned by `openelis-work`; the design preview links to its canonical gallery.
