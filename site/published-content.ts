import type { ComponentType } from 'react';

// Reviewed public sources only; application contracts remain product-owned.
export const canvasModules = import.meta.glob([
  '../specs/artifacts/canvases/catalyst-demos.canvas.tsx',
  '../specs/artifacts/canvases/demo-data-profile.canvas.tsx',
  '../specs/artifacts/canvases/validation-research.canvas.tsx',
], { eager: true }) as Record<string, { default: ComponentType }>;

export const repoMd = import.meta.glob([
  '../README.md',
  '../specs/architecture.md',
  '../specs/background/component-contracts.md',
  '../specs/background/why-local-first-clinical-ai.md',
  '../specs/artifacts/planning/global-health-ai-background-research-2026-06-14.md',
  '../specs/artifacts/planning/guardrails-methodology-research.md',
], { eager: true }) as Record<string, { html?: string; raw?: string; default: string }>;
