# Stack review consolidation — 31 October 2026

The earlier campaign reviewed 30 PRs independently in dependency order and published
one comment review per PR. Ordering did not prevent repeated findings. Its 105 blocker
occurrences were not 105 distinct issues or 105 separate comments.

The replacement tooling requires explicit root-cause identities and introducing-change
attribution, checks ownership against each PR base, and renders full findings only at
the owner. Affected descendants receive links. Cross-repository references resolve to
an owned issue. Baseline findings have tracking locations without falsely assigning
introduction to an open PR. Original observations remain in the local ledger.

Connected branches that have diverged are detected and require a curated manifest;
the automatic merged-top reviewer refuses to silently omit an amended lower PR.
Stack reviews cannot launch the fixer. Publication updates existing owned comment
reviews, checks heads, bases and existing body hashes, reads updates back, and resumes
without duplicate writes. Questions remain separate from reproduced blockers.

Validation: 79 review-tooling tests passed, including real Git ancestry, amended lower
heads, reworded findings, distinct causes, regressions, cross-repository references,
stale publication snapshots, human-edited bodies and idempotent retry. The umbrella's
19 unit tests passed. The implementation checkout's workspace check reports its
uninitialized component checkouts and two existing implementation-head differences;
those gitlinks were not changed by this tooling work. Pinned-checkout validation and
publication receipts are recorded separately after execution.

Hub #57, harness #205 and umbrella #31 advanced substantially after their original
source reviews. Consolidation preserves those observations as historical evidence;
it does not assert that their new heads still reproduce the failures. No product
changes, new acceptance claims, merges or deployments are part of this task.
