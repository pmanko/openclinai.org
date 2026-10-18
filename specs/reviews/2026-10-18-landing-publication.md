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

## What served the site

The VM `harness-chartsearch` still runs the pre-split validation-harness Caddy
(`harness-proxy`, from `/home/pmanko/clinical-ai-validation-harness/compose/Caddyfile`),
which mounts `/home/pmanko/clinical-ai-validation-harness/landing` as the site
root. The umbrella's publish script syncs to `/home/pmanko/openclinai.org/landing`,
the directory the umbrella's own website proxy (`compose/website/services.yml`)
would mount; that proxy has never been started on the VM, so a first run of the
script uploaded the pages where nothing serves them and its post-publish
verification failed. The publication above ran with
`GCP_REMOTE_REPO=clinical-ai-validation-harness`, which syncs into the directory
the live proxy serves; a dry run showed it deletes nothing there. Use the same
override until the website proxy is switched over to the umbrella checkout.

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
