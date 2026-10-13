# Track A rebase and review remediation record

Verified 7 October 2026, with the QueryStore reconciliation on 6 October;
consolidated out of the roadmap on 10 October 2026. This is dated evidence for the
[OpenMRS contribution spec](../openmrs-contribution.md), not a current requirement.

## Heads as published on 7 October

| Existing work | Published PR | Immediate base | Head on 7 October |
| --- | --- | --- | --- |
| B1 shared provider contract | [Backend #583](https://github.com/openmrs/openmrs-module-chartsearchai/pull/583) | main | `3dafae15` |
| B4 exact token counting | [Backend #584](https://github.com/openmrs/openmrs-module-chartsearchai/pull/584) | #583 | `ad6117d9` |
| B3 safety-check execution status | [Backend #585](https://github.com/openmrs/openmrs-module-chartsearchai/pull/585) | #584 | `b28332d6` |
| B5 conversation persistence | [Backend #586](https://github.com/openmrs/openmrs-module-chartsearchai/pull/586) | #585 | `8139ab9a` |
| B4 QueryStore context and budgets | [Backend #587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587) | #586 | `881163df` |
| B3 bundled inference and cancellation | [Backend #588](https://github.com/openmrs/openmrs-module-chartsearchai/pull/588) | #587 | `4be7c58a` |
| B2 Hub discovery and transport | [Backend #589](https://github.com/openmrs/openmrs-module-chartsearchai/pull/589) | #588 | `795607f4` |
| B5 conversation endpoints and history | [Backend #590](https://github.com/openmrs/openmrs-module-chartsearchai/pull/590) | #589 | `20cb84ba` |
| F1 staged stream transport | [Frontend #55](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/55) | main | `3c0c513b` |
| F1 history client and session state | [Frontend #56](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/56) | #55 | `8055eaea` |
| F3 Markdown, tables and citations | [Frontend #57](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/57) | #56 | `04b7f245` |
| F2 provider/profile selection | [Frontend #58](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/58) | #57 | `071edf86` |
| F1/F3 conversation lifecycle, staged answers, evidence and streaming toggle | [Frontend #59](https://github.com/openmrs/openmrs-esm-chartsearchai/pull/59) | #58 | `475f6eb6` |

The umbrella gitlinks record the heads under review: backend `20cb84ba`, frontend
`475f6eb6` and QueryStore `286993cc`.

## Verified on 7 October

- Frontend #55–#59 are rebased on upstream `37ca2d6` and published in the agreed
  order. All five hosted builds pass on the heads listed above; release jobs are
  correctly skipped for PRs. Each layer passed local tests, lint, type checks,
  translation generation and build. #59 also explains the distinct safety
  limitation causes from backend #585; its latest local suite passes 658 tests.
  All eight inline review threads are resolved. The failed-provider-switch concern
  in the general review is fixed in `475f6eb6`: selection changes only after the
  new conversation succeeds, and a failed request preserves the previous
  conversation. The published head passes its hosted build; the review response
  links the fix and tests. Automated browser review exercised no flows because its
  environment lacked the application; it is not runtime proof.
- Backend #583–#590 are rebased on upstream `cf9e2046` and published through
  `gh stack` in the agreed order. Each actual PR base matches its predecessor's
  published head; the seven upstream prerequisite branches were updated with exact
  old-revision leases. The earlier combined revision's conflict resolutions are
  preserved. GitHub still rejects native Stack objects for fork PRs; local stack
  tracking and actual linear PR bases remain in use. Review fixes cover token-count
  compatibility, truthful safety coverage, conversation audit/retention, context
  limits/errors, cancellation, citation provenance, Hub timeouts, stream
  keep-alives/Unicode and mode validation. The full Linux Java 21 reactor at the
  pre-readiness-fix stack tip passed 3,300 tests with 63 skipped. The final
  model-path disclosure fix in #588 passed all 43 provider/REST contract tests on
  stack tip `20cb84ba`. Gateway build and isolated HTTP checks of both stream
  routes passed; no deployment is claimed. Exact token counting passed against the
  supported llama.cpp b8850 binary, and Hub transport passed 32 focused tests on
  Java 11. The unchanged occupied-port fixture failed on macOS and passed on Linux;
  its assertions were not weakened. Per-PR checks run on all eight heads, including
  the previously missing #584–#587 checks. Ordinary published-dependency and
  QueryStore-main checks are restored alongside the temporary paired-source build.
  The ordinary builds on #587–#590 fail to compile against the published/upstream
  QueryStore API; the job logs show the missing context-slice/chart-read symbols.
  Those failures remain visible while all twelve paired-source Java 11/17/21 builds
  pass on the proposed API together. All 46 inline threads have evidence-backed
  responses; 43 are resolved. #587's model-quality/temporal evaluation disposition,
  temporary dependency-job removal and reviewer disposition of
  retrieval-versus-safety classification remain open.
- QueryStore #68 at `286993cc` includes upstream `e12a1de2`. Reconciled on
  6 October: all 27 previously unresolved threads were resolved after checking the
  implemented fixes and regression coverage. The stopword findings are addressed by
  removing word stripping entirely; lab-panel expansion preserves the question's
  clinical qualifiers. Fresh native reactor: 585 passed, two skipped. MySQL
  integration: all 22 tests passed against temporary MySQL containers. Hosted Java
  8/11/17/21 builds pass; publication jobs are skipped for this PR. All 29 inline
  threads are resolved (27 reconciled in this pass, two already resolved). The
  [29 September request to split #68 into smaller pieces](https://github.com/openmrs/openmrs-module-querystore/pull/68#issuecomment-5893747702)
  is a separate, unanswered discussion comment. This is source and HTTP-dispatch
  evidence, not deployed-runtime or Elasticsearch integration acceptance.
- Umbrella [#8](https://github.com/pmanko/openclinai.org/pull/8) records published
  frontend `475f6eb6` and backend `20cb84ba` and updates their contract references.
  All 24 umbrella unit tests and 55 affected operational/contract checks passed. At
  published evidence head `2fbee128`, all hosted checks pass, including the
  [assembled OpenMRS source check](https://github.com/pmanko/openclinai.org/actions/runs/37591362619)
  with the updated pins. This builds the selected QueryStore and backend together
  and checks the frontend; it does not establish compatibility with the unpublished
  dependency artifact or deployment acceptance. Earlier combined frontend `e09ce24`
  and backend `713b8477` supplied rebase resolutions.
- All thirteen stack PR descriptions identify their published heads, actual
  predecessors, owning-PR remediation and current validation limitations. They
  retain earlier combined acceptance only for unaffected behavior and no longer
  describe the revised application code as unchanged by remediation.

## #587 context-composition finding

On 7 October, all five patients required by the native scope/temporal cohort
returned HTTP 404 from the local HIV instance. An
[isolated substitute comparison](2026-10-07-context-evaluation.md) records all 40
scope and 15 temporal questions on both #586 and #587. Off-topic citations fall
from 14 to zero, but mean citation F1 falls from 0.891 to 0.735: three on-topic
cells lose supporting citations. Both arms pass 14 temporal cases; one has
conflicting weights at the latest timestamp and remains ambiguous. The targeted
repeat reproduced the same cited-record sets on all twelve repeated answers. Exact
model requests confirm one renal retrieval regression: creatinine records reached
the baseline prompt but are absent after #587. The two other lower scores reflect
the prompt's rule to omit citations after a negative category verdict, despite the
gold awarding coverage for normal examinations. This is measured mixed evidence,
not a clean quality pass; disposition is tracked in the contribution spec.

## Execution sequence as completed

1. Both stacks rebased with `gh stack`, declared order and newer upstream behavior
   preserved; actual GitHub bases and heads checked after publication.
2. Findings fixed in their owning PRs with regression coverage for lasting behavior
   (token-count compatibility, truthful safety coverage, persistence/audit/retention,
   context budgets, cancellation, Hub timeouts, stream lifecycle). Already-fixed
   QueryStore threads reconciled with evidence rather than repeated.
3. Per-PR validation restored against declared bases without making permanent tests
   assert temporary stack state; the umbrella continues to build the selected
   QueryStore and ChartSearchAI sources together before upstream merge.
4. Component heads published, umbrella pins and consumers updated, affected native
   and assembled checks run. The earlier umbrella #8 configuration-comment
   assertion and generated translation failures were fixed.

Earlier checkpoints remain evidence for unaffected behavior only: the
[combined acceptance checkpoint](https://github.com/pmanko/openclinai.org/blob/6e048c2ac3d45987922270e6f2e59e5ff444d239/specs/roadmap.md#current-execution-review-ready-stacks),
the 3 October paired Java 21 build and the umbrella `37b260e` hosted checks. The
Java 11/macOS occupied-port fixture issue remains separate; use the setup guide's
verified Java 21 local path and report platform limitations.
