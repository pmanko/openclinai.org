# Landing publication (18 October 2026)

The reviewed `landing/` tree at umbrella `ff176a7` was published to
<https://openclinai.org/> on 18 October with
`scripts/publish-landing.sh --landing-only`. The script ran the landing tests
(5 passed), synced the tree and then compared every published HTML, CSS and
sitemap file with the checkout byte for byte: all 17 matched. The
[OpenMRS upstream contributions page](https://openclinai.org/docs/openmrs-upstream/)
now describes the fourteen open pull requests, their 18 October heads, the review
status and the recorded checks, and links the coordination spec on `main`. The
previous live version dated 15 September named three pull requests (documentation
audit finding D06).

## The site became its own deployment

Until this evening the VM `harness-chartsearch` served openclinai.org through the
pre-split validation-harness Caddy (`harness-proxy`), which mounted
`/home/pmanko/clinical-ai-validation-harness/landing` and also fronted the
OpenMRS demo stack at `openmrs.openclinai.org`, the reports subdomain and wahs.
The umbrella's publish script syncs to `/home/pmanko/openclinai.org/landing`, so
its first run uploaded the pages where nothing served them and its verification
failed; an interim publication used `GCP_REMOTE_REPO=clinical-ai-validation-harness`.

With the owner's go, the demo stack was brought down (`docker compose -p compose
down`; its volumes were kept), the 32 published report directories were copied
to `/home/pmanko/openclinai.org/artifacts/reports`, and a full
`scripts/publish-landing.sh` run installed the umbrella's website proxy
(`compose/website/`, project `openclinai-website`) on ports 80 and 443 from
`.env.website` (the committed example's values). Caddy obtained Let's Encrypt
certificates for `openclinai.org`, `reports.openclinai.org` and
`wahs.openclinai.org` within seconds; a second run verified every landing file
against the checkout, the reports index lists 21 entries, and
`openmrs.openclinai.org` no longer answers. The publish script now needs no
override. `www.openclinai.org` resolves to the VM but is not configured on either
proxy, as before.

Left on the VM: the stopped demo stack's volumes and the old harness checkout
directory, both unused by the website.

## Demo-host check removed

The script had refused to publish while the recordings linked on the Catalyst demo
host (`catalyst.openelis-global.org`) were unreachable. That host is stopped
often to save cost and all its ports were closed on 18 October. The check and its
test were removed (`ff176a7`); publication verifies the pages it publishes, and the
test stub now fails any call to that host.

## Not done

- The switch from the harness proxy to the umbrella's website proxy
  (`compose/website/`), which needs `.env.website` on the VM and a full
  publication; the reports subdomain and the OpenMRS demo paths on that VM are
  still served by the harness Caddyfile.
- The documentation audit's W04 report-catalog provenance item.
