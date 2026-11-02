import { writeFileSync } from 'node:fs';

// Vitest's JSON report can say success even when an unhandled task rejects.
export default class ReviewExecutionReporter {
  onTestRunEnd(_modules, errors, reason) {
    writeFileSync(process.env.REVIEW_VITEST_EVIDENCE, JSON.stringify({
      reason,
      unhandled_errors: Array.isArray(errors) ? errors.length : null,
    }));
  }
}
