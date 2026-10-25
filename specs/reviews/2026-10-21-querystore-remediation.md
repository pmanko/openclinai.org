# QueryStore stack: the maintainer's round and our breadth round remediated (21 October 2026)

Evidence for the QueryStore item of the remediation in
[openmrs-contribution.md](../openmrs-contribution.md). The threads are inventoried in
`2026-10-21-maintainer-round-on-the-stacks.md`; the reviewer's own findings in
`2026-10-21-harness-reproduction.md`. Every fix landed in its owning layer as its own commit
with a fail-first test, the stack was restacked onto upstream `main` (six commits ahead,
one of them code: the ONNX session close, #84) and pushed bottom-up through the pre-push
probes. Stack top: `db90860` (#98).

## The maintainer's twenty threads

| PR | Thread | Commit | Test |
| --- | --- | --- | --- |
| #93 | bulkDelete on a never-created index | d9fb06f | `ElasticsearchBackendStoreIntegrationTest#bulkDeleteOnAnIndexNeverCreatedIsANoOp` |
| #93 | ADR item still describing `_delete_by_query` | d9fb06f | (doc) |
| #93 | displaced javadoc | d9fb06f | (doc) |
| #94 | interrupted resync resumed with the skip (blocking) | 8ae16e8 | `BootstrapServiceImplTest#anInterruptedResyncResumedByABootstrapKeepsRewriting` |
| #94 | `prepare` waits for the commit | 2a29baf | `AfterCommitDispatcherTest#dispatchPrepared_withActiveSynchronization_preparesOnlyAfterCommit` |
| #94 | same-second sentence in Decision 12 | 8ae16e8 | (doc) |
| #94 | `dispatch` rewritten without a change | 02c7c9a | (revert of a no-op) |
| #95 | per-patient walk re-embeds stored records (blocking) | f756789 | `TypeBootstrapperTest#runForPatient_skipsRecordsStoredAtTheirCurrentVersion` |
| #95 | blank `patient` runs a cross-patient search (blocking) | 3082117 | `PatientRecordEndpointTest#returns400_whenPatientIsBlank_insteadOfSearchingAcrossPatients` |
| #96 | `withheldTypes` | 8b9e7d9 | `ContextSliceTest#aTypeTheCallerCannotReadIsWithheldAndLeavesTheEffectiveScope`, `PatientRecordEndpointTest#contextPageNamesTheTypesWithheldFromTheCaller` |
| #96 | second canonical form for `sliceId` | d8c8b58 | `PatientRecordEndpointTest#contextSliceIdentityTellsANumberFromItsStringForm` |
| #96 | `continuesIdentifier` on quoted phrases | 277c1e8 | `ContextSliceTest#aQuotedPhraseIsExactBesideAConnector` |
| #96 | codes cap | 0ef69b5 | `ConceptNameUtilTest#getMappingCodes_keepsEveryLiveCodeHoweverManyMappingsAConceptHas` |
| #96 | member as the similarity hit | b5b683c | `ContextSliceTest#obsGroupFamilies_completeFromAMemberHit_whenTheParentIsNotIndexed` |
| #97 | `at last` idiom (blocking) | 5a68a83 | `ContextQuestionInterpreterTest#interpret_readsAtLastBeforeANounAsRecency` |
| #97 | medication cues (blocking) | 8e8d7d0 | `ContextQuestionInterpreterTest#interpret_recognizesEveryTypedCueFamily` |
| #97 | caller's temporal flag | 1482b50 | `ContextSliceTest#interpretMode_keepsTheCallersTemporalFlag` |
| #97 | preprocessing javadoc | 18ad6bd | (doc) |
| #98 | stable-series javadoc | ad27700 | (doc) |
| #98 | hits the chart does not hold | ad27700 | `ContextSliceTest#similarityLeg_skipsAHitTheChartDoesNotHold` |

Only #96's `withheldTypes` departs from the thread: the set is on the slice (request,
envelope and `sliceId`) and not on `PatientChartRead`, which returns records and no scope;
the reply offers to add it there.

## Our round's findings taken on

| PR | Finding | Commit | Test |
| --- | --- | --- | --- |
| #93 | a failed bulk request reported every id of the chunk, settled ones included | 209e312 | `ElasticsearchBulkDeleteAccountingTest` |
| #94 | the fallback document kept an edited record's previous version | 6cd9ecf | `RecordProjectorTest#project_leavesTheVersionUnsetWhenTheCommittedRecordCannotBeSerialized` |
| #95 | the Lucene skipped-index set was shared between enumerations | 9c988f2 | structural; `LuceneBackendStoreTest#findPatientChart_marksAnIndexTheEnumeratorCouldNotOpenIncomplete` pins the single-reader case |
| #97 | "patient-reported" lost its first half; curly possessive | de5f7da | `ContextQuestionInterpreterTest#preprocess_dropsThePatientEverySliceRecordIsAbout` |
| #98 | a raised similarity limit asked Elasticsearch past its result window | db90860 | `ElasticsearchSearchWindowTest` |

Not taken on, for the owner: #95's three completeness findings (the open owner decision), the
#98 similarity-limit multiplication overflow and the newest-record promise within fetched
candidates, and the remaining questions of the third run's outputs under
`work/review/querystore-<pr>/round-1.md`.

## Verification

Full suites at every layer after the restack (`work/review/qs-remediation-suites.txt`):

| Layer | Head | Tests |
| --- | --- | --- |
| #92 query-cache-separator | c82182b | 513 |
| #93 es-delete-at-version | 209e312 | 514 |
| #94 bootstrap-skip-unchanged | 6cd9ecf | 528 |
| #95 patient-record-rest | 9c988f2 | 590 |
| #96 context-slice | b5b683c | 640 |
| #97 question-interpretation | de5f7da | 658 |
| #98 retrieval-diversity | db90860 | 669 |

No failures, two skips each. The new top differs from the old one in upstream's files
only (scratch diff of `e6aad12` against `f5e2898`); the pre-push probe then refused the
first #93 fix, whose only named test needed a cluster, so that commit gained a unit test
and the layers above were replayed onto it; the probe then found that the hunk split of
the #96 commits had left the withheld-types commit uncompilable on its own, so those two
commits were rebuilt and the layers above replayed again. `db90860` differs from `f5e2898`
by that one test file; the top suite re-run there: 670 tests, no failures. Elasticsearch integration tests at the
top: 42, no failures (`work/review/qs-remediation-integration.log`). Pre-push probes
(`work/review/qs-remediation-push.log`, ledger `work/review/ledger/openmrs-module-querystore.jsonl`):
every new main-code commit red on the revert of its files, green at the commit and red
under its named mutation; the two comment-only commits carry `Probe: skip`; the replayed
commits were skipped as the same patch. Pushed 11:27 to 11:28; the PR heads are the layer
heads above. The backend's paired build is pinned to `db90860` (context-budget and above
replayed). Reviewer run on the fixed heads: started 11:30, results in the section below
when it ends.

Replies drafted in `work/review/daniel-replies-qs.md`, to post on the owner's go-ahead.
