import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { filterRows, inventories, projectFor, sourceHref } from './model';

const selectedIds = ['small-model-answer-paths-2026-07-15', 'catalyst-phase1-comparison'];

describe('public project evidence browsing', () => {
  it('publishes only the reviewed reports also featured in the public gallery', () => {
    expect(Object.keys(inventories)).toEqual(['reports']);
    expect(inventories.reports.rows.map(row => row.id)).toEqual(selectedIds);
    const gallery = readFileSync(new URL('../../landing/catalyst/hiv-gallery/index.html', import.meta.url), 'utf8');
    for (const row of inventories.reports.rows) {
      expect(gallery).toContain(row.url);
      expect(row.source_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(row.summary).toBeTruthy();
      expect(row.recorded_takeaway).toBeTruthy();
      expect(row.claim_limit).toBeTruthy();
      expect(Object.keys(row).sort()).toEqual(['claim_limit', 'family', 'id', 'project', 'recorded_takeaway', 'source_date', 'summary', 'title', 'url']);
    }
  });
  it('combines project and search filters without exposing internal records', () => {
    expect(filterRows('reports', 'chartsearch', 'temporal E4B').map(row => row.id)).toEqual([selectedIds[0]]);
    expect(filterRows('reports', 'catalyst', 'PostgreSQL').map(row => row.id)).toEqual([selectedIds[1]]);
    expect(filterRows('reports', 'catalyst', 'E4B')).toEqual([]);
    expect(filterRows('reports', 'all', 'no-such-report')).toEqual([]);
    for (const kind of ['efforts', 'pull-requests', 'decisions', 'roadmaps', 'sessions', 'sources', 'public-surfaces']) {
      expect(filterRows(kind, 'all', '')).toEqual([]);
    }
    expect(projectFor(inventories.reports.rows[0])).toEqual(['chartsearch']);
  });
  it('links reports without routing to obsolete authority or working guides', () => {
    expect(sourceHref(inventories.reports.rows[0].url)).toBe(inventories.reports.rows[0].url);
    expect(sourceHref('reports')).toBe('#view=reports');
    for (const value of ['maintenance.md', 'reviews/2026-09-12.md', '.specify/memory/constitution.md', 'specs/catalyst-program-roadmap.md', 'WORKSPACE.md', 'javascript:alert(1)']) {
      expect(sourceHref(value)).toBeNull();
    }
  });
  it('does not bundle the internal inventory, working narratives or legacy navigation', () => {
    const main = readFileSync(new URL('./main.tsx', import.meta.url), 'utf8');
    const model = readFileSync(new URL('./model.ts', import.meta.url), 'utf8');
    expect(main + model).not.toMatch(/import.*targets\/validation-harness/);
    for (const text of ['maintenance', 'mergeReview', 'resumeIds', 'Keeping it current', 'Codex & Claude', 'Roadmaps & plans', 'clinical-ai-validation-harness/status/']) {
      expect(main + model).not.toContain(text);
    }
    expect(main).toContain('Reported findings');
    expect(main).toContain('Limitations');
    expect(main).not.toContain('current deployment');
  });
});
