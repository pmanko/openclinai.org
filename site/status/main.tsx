import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { inventories, projects, snapshot, filterRows, sourceHref, projectFor, type Project, type Row } from './model';
import './style.css';

type Location = { view: string; project: Project; query: string; kind: string; id: string };
function location(): Location {
  const p = new URLSearchParams(window.location.hash.slice(1));
  const project = p.get('project') || 'all';
  return { view: p.get('view') || 'overview', project: (project in projects ? project : 'all') as Project, query: p.get('q') || '', kind: p.get('kind') || '', id: p.get('id') || '' };
}
function go(changes: Partial<Location>, replace = false) {
  const next = { ...location(), ...changes };
  const p = new URLSearchParams();
  Object.entries(next).forEach(([key, value]) => { if (value && value !== 'all' && !(key === 'view' && value === 'overview')) p.set(key === 'query' ? 'q' : key, value); });
  if (replace) { history.replaceState(null, '', `#${p}`); window.dispatchEvent(new HashChangeEvent('hashchange')); }
  else window.location.hash = p.toString();
}
function openRecord(id: string) { go({ kind: 'reports', id }); }
function navigate(view: string, extra: Partial<Location> = {}) { go({ view, query: '', id: '', kind: '', ...extra }); }
const date = (value: string) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
const fields: Array<[keyof Row, string]> = [['source_date', 'Report date'], ['summary', 'Experiment'], ['recorded_takeaway', 'Reported findings'], ['claim_limit', 'Limitations'], ['url', 'Supporting report']];
function Reference({ value }: { value: string }) {
  const href = sourceHref(value);
  return href ? <a href={href} target="_blank" rel="noreferrer">{value}<span aria-hidden="true"> ↗</span></a> : <span>{value}</span>;
}
function Detail({ state }: { state: Location }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const row = inventories[state.kind]?.rows.find(r => r.id === state.id);
  useEffect(() => { if (state.id && !dialog.current?.open) dialog.current?.showModal(); if (!state.id) dialog.current?.close(); }, [state.id]);
  useEffect(() => { if (state.id) dialog.current?.scrollTo(0, 0); }, [state.id, state.kind]);
  const close = () => go({ id: '', kind: '' });
  return <dialog ref={dialog} className="detail" aria-labelledby="detail-title" onCancel={e => { e.preventDefault(); close(); }} onClick={e => { if (e.target === dialog.current) close(); }}>
    <div className="detail-content">
      <div className="detail-top"><span className="eyebrow">Dated evaluation evidence</span><button className="icon-button" aria-label="Close details" onClick={close}>×</button></div>
      <h2 id="detail-title">{row?.title || 'Report not found'}</h2>
      {row ? <dl className="record-fields">{fields.map(([key, title]) => <div key={key}><dt>{title}</dt><dd><Reference value={key === 'source_date' ? date(row[key]) : row[key]} /></dd></div>)}</dl> : <p>Close this panel and browse the selected reports.</p>}
    </div>
  </dialog>;
}
function Overview({ project }: { project: Project }) {
  return <>
    <div className="overview-intro"><div><span className="eyebrow">Dated project evidence</span><h1>Experiments and findings</h1><p>Explore selected ChartSearchAI and Catalyst evaluations. Each summary links to the recorded methods, results and limitations.</p></div><button className="secondary" onClick={() => navigate('reports')}>Browse reports <span aria-hidden="true">→</span></button></div>
    <div className="project-cards">{filterRows('reports', project, '').map(row => <section className={`project-card ${row.project}`} key={row.id}><div className="card-heading"><h2>{row.title}</h2></div><p className="evidence-note">{row.family} · {date(row.source_date)}</p><p className="card-summary">{row.summary}</p><p>{row.recorded_takeaway}</p><p className="evidence-note">{row.claim_limit}</p><div className="card-actions"><button onClick={() => openRecord(row.id)}>Inspect this evaluation →</button><a href={row.url}>Read the report ↗</a></div></section>)}</div>
    <div className="scope-note"><strong>Evidence has a date.</strong> These experiments describe the configurations and data recorded in each report. For setup and supported interfaces, use the <a href="https://pmanko.github.io/openclinai.org/#/spec/specs/background/component-contracts">component documentation</a>.</div>
  </>;
}
function Table({ rows }: { rows: Row[] }) {
  return <div className="table-wrap"><table><thead><tr><th>Report</th><th>Project / date</th><th>Experiment and limitations</th><th><span className="sr-only">Details</span></th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td><button className="row-title" onClick={() => openRecord(row.id)}>{row.title}</button></td><td>{projectFor(row).map(p => projects[p]).join(' · ')}<small>{date(row.source_date)}</small></td><td><p>{row.summary}</p><p className="small muted">{row.claim_limit}</p></td><td><button className="row-open" aria-label={`Open ${row.title}`} onClick={() => openRecord(row.id)}>→</button></td></tr>)}</tbody></table></div>;
}
function Inventory({ state }: { state: Location }) {
  const inv = inventories[state.view];
  if (!inv) return <div className="empty"><h1>Page not found</h1><button className="secondary" onClick={() => navigate('overview')}>Return to overview</button></div>;
  const rows = filterRows(state.view, state.project, state.query);
  function download() { const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${state.view}-${snapshot}.json`; a.click(); URL.revokeObjectURL(url); }
  return <><div className="page-heading"><div><span className="eyebrow">Dated evidence</span><h1>{inv.title}</h1><p>{inv.description}</p></div><button className="secondary" onClick={download}>Export this view ↓</button></div><div className="table-toolbar"><span aria-live="polite"><strong>{rows.length}</strong> of {inv.rows.length} reports</span>{(state.query || state.project !== 'all') && <button className="text-button" onClick={() => go({ query: '', project: 'all' })}>Clear filters</button>}</div>{rows.length ? <Table rows={rows} /> : <div className="empty"><h2>No matching reports</h2><p>Try another phrase or clear the project filter.</p><button className="secondary" onClick={() => go({ query: '', project: 'all' })}>Clear filters</button></div>}</>;
}
function Search({ state }: { state: Location }) {
  const rows = filterRows('reports', state.project, state.query);
  return <><div className="page-heading"><div><span className="eyebrow">Evaluation evidence</span><h1>Search results</h1><p>{state.query ? `Matches for “${state.query}”` : 'Search by project, experiment, finding or date.'}</p></div></div>{state.query && (rows.length ? <Table rows={rows} /> : <div className="empty"><h2>No matching reports</h2><p>Try a shorter phrase or choose All projects.</p></div>)}</>;
}
function App() {
  const [state, setState] = useState(location);
  const [menu, setMenu] = useState(false);
  useEffect(() => { const onHash = () => setState(location()); window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash); }, []);
  useEffect(() => { document.title = `${state.view === 'overview' ? 'Project evidence' : inventories[state.view]?.title || 'Project evidence'} · Open Clinical AI`; setMenu(false); window.scrollTo(0, 0); }, [state.view, state.project]);
  const nav = (view: string, title: string) => <button key={view} className={`nav-item ${state.view === view ? 'active' : ''}`} aria-current={state.view === view ? 'page' : undefined} onClick={() => navigate(view)}>{title}</button>;
  return <><a className="skip-link" href="#main-content" onClick={e => { e.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a><aside className={`sidebar ${menu ? 'shown' : ''}`}><a className="brand" href="#"><span className="brand-mark">+</span><span>Open Clinical AI<small>Evaluation evidence</small></span></a><nav aria-label="Evidence">{nav('overview', 'Overview')}{nav('reports', 'Evaluation reports')}</nav><div className="sidebar-bottom"><span className="snapshot-dot"/> Dated experiments<small>Each report records its own configuration</small></div></aside><div className="workspace"><nav className="site-parent" aria-label="Site navigation"><a href="https://openclinai.org/">Open Clinical AI</a><span aria-hidden="true">/</span><a href="#">Project evidence</a></nav><header className="topbar"><button className="mobile-menu icon-button" aria-label="Toggle navigation" aria-expanded={menu} onClick={() => setMenu(!menu)}>☰</button><div className="search-field"><span aria-hidden="true">⌕</span><input type="search" aria-label="Search reports" placeholder="Search experiments and findings…" value={state.query} onChange={e => go({ query: e.target.value, view: 'search', id: '', kind: '' }, true)} /></div><span className="checked-date">Reports through {date(snapshot)}</span></header><div className="project-tabs" role="group" aria-label="Filter by project">{Object.entries(projects).map(([id, title]) => <button key={id} aria-pressed={state.project === id} onClick={() => go({ project: id as Project, id: '', kind: '' })}>{title}</button>)}</div><main id="main-content" tabIndex={-1}>{state.view === 'overview' ? <Overview project={state.project} /> : state.view === 'search' ? <Search state={state} /> : <Inventory state={state} />}</main><footer>Open Clinical AI · Evaluation evidence <span>Dated experiments and reported findings</span></footer></div><Detail state={state} /></>;
}
const root = createRoot(document.getElementById('root')!);
root.render(<App />);
if (import.meta.hot) import.meta.hot.dispose(() => root.unmount());
