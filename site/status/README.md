# Project evidence dashboard

Browse selected dated evaluations already featured in the public gallery. Each
summary links to its report's methods, results and limitations. `model.ts` contains
the reviewed public selection; reports and the full evidence inventory remain at
their owning sources.

Deployment destination: <https://pmanko.github.io/openclinai.org/status/>

From `site/`:

```sh
npm ci
npm run status:dev
npm run status:test
npm run status:build
```

The preview prints its local address. The build output is in `status/dist/`.
Summaries are included at build time, with no component checkout, database or
runtime GitHub connection required. Project filters, search and open details can
be bookmarked; export downloads only the filtered public records.

Review the selected summaries and report links when updating `model.ts`, retaining
the experiment dates and limitations. `npm run build:pages` copies this dashboard
to `site/dist/status/` for the configured GitHub Pages workflow. Local builds do
not publish it or verify the deployed destination.

Automated tests cover the public selection, dated report fields, project/search
filters and link handling. Check keyboard interaction, detail dialogs and narrow
and desktop rendering in a browser before publication.
