import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { filterRows, inventories, projectFor, sourceHref } from './model';

const rows = inventories.reports.rows;

describe('public project evidence browsing', () => {
  it('publishes only report rows with complete public fields', () => {
    expect(Object.keys(inventories)).toEqual(['reports']);
    expect(rows.length).toBeGreaterThan(0);
    for (const row of rows) {
      expect(Object.keys(row).sort()).toEqual(['claim_limit', 'family', 'id', 'project', 'recorded_takeaway', 'source_date', 'summary', 'title', 'url']);
      expect(row.source_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      for (const field of ['summary', 'recorded_takeaway', 'claim_limit', 'url'] as const) expect(row[field]).toBeTruthy();
    }
  });
  it('filters by project and search text and returns nothing for unknown inventories', () => {
    for (const row of rows) {
      for (const project of projectFor(row)) {
        expect(filterRows('reports', project, '').map(r => r.id)).toContain(row.id);
      }
      expect(filterRows('reports', 'all', row.title).map(r => r.id)).toContain(row.id);
    }
    expect(filterRows('reports', 'all', 'no-such-report-anywhere')).toEqual([]);
    expect(filterRows('no-such-inventory', 'all', '')).toEqual([]);
  });
  it('links published URLs and inventory views, and rejects anything else', () => {
    expect(sourceHref(rows[0].url)).toBe(rows[0].url);
    expect(sourceHref('reports')).toBe('#view=reports');
    for (const value of ['internal/notes.md', 'javascript:alert(1)']) expect(sourceHref(value)).toBeNull();
  });
  it('does not import harness sources', () => {
    const main = readFileSync(new URL('./main.tsx', import.meta.url), 'utf8');
    const model = readFileSync(new URL('./model.ts', import.meta.url), 'utf8');
    expect(main + model).not.toMatch(/import.*targets\/validation-harness/);
  });
});
