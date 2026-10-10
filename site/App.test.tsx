import { describe, it, expect } from 'vitest';
import * as React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// The SPA stays the default human view, but each doc/canvas page should offer a
// link to its full-static-HTML twin (the LLM-readable mirror). Render the real
// app at a doc route and assert the twin link is present.
describe('App full-HTML twin link', () => {
  it('links a doc page to its static-HTML twin', () => {
    const html = renderToStaticMarkup(
      React.createElement(
        MemoryRouter,
        { initialEntries: ['/spec/README'] },
        React.createElement(App),
      ),
    );
    expect(html).toContain('spec/README.html');
  });

  it('links a canvas page to its static-HTML twin', () => {
    const html = renderToStaticMarkup(
      React.createElement(
        MemoryRouter,
        { initialEntries: ['/canvas/specs/artifacts/canvases/demo-data-profile'] },
        React.createElement(App),
      ),
    );
    expect(html).toContain('canvas/specs/artifacts/canvases/demo-data-profile.html');
  });
});


describe('documentation entry', () => {
  const html = renderToStaticMarkup(
    React.createElement(MemoryRouter, { initialEntries: ['/welcome'] }, React.createElement(App)),
  );

  it('links back to the public site and labels its navigation', () => {
    expect(html).toContain('href="https://openclinai.org/#projects"');
    expect(html).toContain('aria-label="Site navigation"');
    expect(html).toContain('href="https://openclinai.org/"');
  });

  it('routes into setup, architecture, methods and research', () => {
    expect(html).toContain('href="/spec/README"');
    expect(html).toContain('href="/topic/evidence"');
    expect(html).toContain('href="/spec/specs/architecture"');
    expect(html).toContain('href="/spec/specs/background/why-local-first-clinical-ai"');
  });

  it('retains search and a keyboard skip destination', () => {
    expect(html).toContain('aria-label="Search documentation"');
    expect(html).toContain('href="#main-content"');
    expect(html).toContain('id="main-content" tabindex="-1"');
  });
});
