import { describe, it, expect } from 'vitest';
import { neighbors, navTree, flattenLeaves, NavSection } from './nav';

const TREE: NavSection[] = [
  {
    title: 'S',
    items: [
      { kind: 'spec', slug: 'a', title: 'A' },
      { kind: 'spec', slug: 'b', title: 'B' },
      { kind: 'spec', slug: 'c', title: 'C' },
    ],
  },
];

// prev/next must work across the COMPLETE (auto-merged) tree, not just the
// curated default — otherwise auto-discovered pages get no prev/next links.
describe('neighbors', () => {
  it('finds prev/next within a provided tree', () => {
    const { prev, next } = neighbors('b', TREE);
    expect(prev?.slug).toBe('a');
    expect(next?.slug).toBe('c');
  });
});

// Policy invariant: implementation detail under specs/ — feature folders (specs/0NN),
// plans, briefs, contracts, handoffs, lanes — is dev-internal and must NOT appear in
// the published nav. (README, canvases, and the curated mission/background + research
// pages are the public surface.)
describe('public nav excludes dev feature specs', () => {
  const curated = flattenLeaves(navTree);
  it('does not publish component implementation registers or obsolete plans', () => {
    expect(Object.keys(curated).some(slug => /^specs\/0\d\d/.test(slug))).toBe(false);
    expect(curated['specs/roadmap']).toBeUndefined();
    expect(curated['specs/artifacts/canvases/answer-flow']).toBeUndefined();
  });
});

// The mission-first overhaul curates the cited background page into "Start here",
// and promotes the topic-referenced items that were stranded in nav-auto's
// collapsed "More documents" drawer into the real sidebar IA.
describe('overhaul curation', () => {
  const curated = flattenLeaves(navTree);

  it('curates the background "why" page in Start here', () => {
    expect(curated['specs/background/why-local-first-clinical-ai']).toBeDefined();
  });

  it.each([
    'specs/architecture',
    'specs/background/component-contracts',
    'specs/artifacts/planning/guardrails-methodology-research',
  ])('promotes %s out of the More-documents drawer', (slug) => {
    expect(curated[slug], `${slug} should be curated in navTree`).toBeDefined();
  });
});
