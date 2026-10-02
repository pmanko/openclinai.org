export type Project = 'all' | 'chartsearch' | 'catalyst';
export const projects = { all: 'All projects', chartsearch: 'ChartSearchAI', catalyst: 'Catalyst' };
export type Row = {
  id: string;
  title: string;
  project: Exclude<Project, 'all'>;
  family: string;
  source_date: string;
  url: string;
  summary: string;
  recorded_takeaway: string;
  claim_limit: string;
};

// Selected evaluations also featured in the public screenshot gallery.
const reports: Row[] = [
  {
    id: 'small-model-answer-paths-2026-07-15',
    title: 'Small-model answer paths: E4B and 12B',
    project: 'chartsearch',
    family: 'ChartSearchAI',
    source_date: '2026-07-15',
    url: 'https://reports.openclinai.org/small-model-answer-paths-2026-07-15/index.html',
    summary: 'Twelve temporal and chart-grounding scenarios compare answer-only, deterministic temporal checking, and full checked profiles on E4B and 12B.',
    recorded_takeaway: "The report found that deterministic checking fixed E4B's past-appointment error, but did not fix strict six-month windows and degraded one 12B child-growth answer. The full checked E4B profile scored highest in this run while adding reviewed, resolved evidence.",
    claim_limit: 'Exploratory findings from this dated run do not establish current deployment behavior or clinical safety.',
  },
  {
    id: 'catalyst-phase1-comparison',
    title: 'Catalyst: three SQL-writing teams on HIV questions',
    project: 'catalyst',
    family: 'Catalyst',
    source_date: '2026-08-25',
    url: 'https://reports.openclinai.org/catalyst-phase1-comparison/index.html',
    summary: 'An August development comparison of three SQL-writing teams across twelve HIV questions, with results checked against independently written reference queries.',
    recorded_takeaway: 'The report found that no team met its acceptance thresholds. Ambiguous follow-up questions exposed interpretation failures despite favorable SQL-quality scores.',
    claim_limit: 'This PostgreSQL-based experiment describes its recorded configurations and methods, not current Catalyst or Spark performance.',
  },
];
export const inventories: Record<string, { title: string; description: string; rows: Row[] }> = {
  reports: { title: 'Evaluation reports', description: 'Selected dated experiments, their recorded findings and supporting evidence. Each report retains its own methods and limitations.', rows: reports },
};
export const snapshot = '2026-08-25';

export function projectFor(row: Row): Project[] { return [row.project]; }
export function filterRows(kind: string, project: Project, query: string): Row[] {
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return (inventories[kind]?.rows || []).filter(row =>
    (project === 'all' || projectFor(row).includes(project)) &&
    words.every(word => JSON.stringify(row).toLowerCase().includes(word)),
  );
}
export function sourceHref(value: string): string | null {
  if (/^https?:\/\//.test(value)) return value;
  if (inventories[value]) return `#view=${value}`;
  return null;
}
