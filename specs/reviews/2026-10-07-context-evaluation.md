# ChartSearchAI #587: context-composition evaluation

Recorded 7 October 2026. This is measured review evidence, not a new specification
or an acceptance decision. It addresses the [scope/temporal evaluation finding on
#587](https://github.com/openmrs/openmrs-module-chartsearchai/pull/587#discussion_r4187626995).

## Result

The changed composition removes off-topic citations in this sample but loses
on-topic citation coverage. This is a mixed result, **not a clean quality pass**.
The evaluation thread remains open for review of the regression and the substitute
cohort's limitations. No model, prompt or selection setting was tuned to these answers.

| Measurement | Before: #586 `8139ab9a` | After: #587 `881163df` |
| --- | ---: | ---: |
| Scope questions captured | 40/40 | 40/40 |
| Mean citation F1, 18 cells with on-topic records | 0.891 | 0.735 |
| Correct citation abstention, 22 cells without on-topic records | 20/22 | 22/22 |
| Off-topic citations | 14 | 0 |
| Unclassified citations | 0 | 0 |
| Temporal cases with matching value/date and newest source citation | 14/15 | 14/15 |
| Temporal cases requiring source-ambiguity review | 1 | 1 |

These scores measure citation behavior against the frozen record set. They do not
establish medical correctness, medication currency, clinical safety or the quality
of the Hub checked-answer workflow.

## Comparison and provenance

The baseline is the immediate predecessor of #587. Both arms use QueryStore
`286993cc094499ed29f97d4574775cd2c96f5676`, the same copied synthetic HIV database,
Lucene records and embedding model, and Gemma 4 12B Q8_0. Model settings are
temperature 0, seed 42, reasoning budget 0 and context size 24,576. The model file's
SHA-256 is `f20e7ff1be28c283eeeb18fc895733791c56a5851d5cd3fe9691b7f7d12afa72`.

The two ChartSearchAI modules came from hosted builds
[37585658347](https://github.com/openmrs/openmrs-module-chartsearchai/actions/runs/37585658347)
and [37585660147](https://github.com/openmrs/openmrs-module-chartsearchai/actions/runs/37585660147).
Their file checksums, exact commits, database dump checksum, core WAR checksum,
model metadata, settings and frozen manifests are retained in
[provenance.json](2026-10-07-context-evaluation/provenance.json).

The temporary evaluation ran in its own Docker project, database volume and
network at loopback port 18089. The existing installation was only read to obtain
the database and artifacts. Between arms, only the ChartSearchAI module was
replaced and the isolated backend restarted. All five source-record universes
remained identical after the restart. No existing installation was reset or deployed.

Both arms call the native `/chartsearchai/search` endpoint in `queryScoped` mode,
with `chartsearchai.querystore.topK=12` and the remote Gemma engine. The copied
settings have grounding and drug-reference checks disabled in both arms. This
therefore tests answer-generation context composition; it does not test local
token-budget enforcement, Hub review, safety checks, streaming or In-Depth.

## Substitute cohort and scoring

All five UUIDs required by the original native cohort returned HTTP 404 from the
available installation. Five existing synthetic HIV patients were selected before
capturing answers. They cover program enrollment, two recorded allergies,
medication histories, renal records, depression, negative examinations and absent
topics. Each patient received the eight native scope questions and three native
temporal questions, in the same question-first order in both arms.

| Patient ID | Source records | Purpose in the sample |
| --- | ---: | --- |
| 39 | 320 | Program, allergy, medication history, renal and negative examination records |
| 5587 | 121 | Allergy, repeated medication orders and tied latest weights |
| 36 | 168 | Program, medications and renal records |
| 2606 | 157 | Program, medications, renal records and depression |
| 3666 | 214 | Medications, renal records and depression; no program |

The actual QueryStore full-chart reads matched all source record identities, with
no missing records, no truncation and complete projection. These are record-identity
comparisons, not only matching counts.

The native `build_gold_rc2.py` record enumeration and classification functions were
reused, adapting only the database connection to the isolated instance. Before
capture, “Review of systems, genitourinary: Menstruating” was excluded from kidney
evidence: reproductive history is not a renal finding. Negative cardiac and
psychiatric examination records remain on-topic evidence. The frozen
[gold.json](2026-10-07-context-evaluation/gold.json) contains 18 cells with on-topic
records and 22 without. “Present” means relevant records exist, not that the
patient has a positive diagnosis.

Scope scoring uses the native `metric_score.py`, including its exclusion of
module-attached references. Its focus universe here is the full source chart, so
all cited records are classified. To reproduce from a capture directory containing
the individual responses from the evidence packet:

```sh
printf '{}\n' > /tmp/context-eval-empty-adjudications.json
python3 targets/chartsearchai/eval/drift-metric/metric_score.py \
  CAPTURE_DIRECTORY /tmp/context-eval-empty-adjudications.json \
  specs/reviews/2026-10-07-context-evaluation/gold.json
```

The second argument supplies an empty adjudication file; no post-capture
adjudications were added. The complete unmodified responses are stored by arm and
original filename in [captures.json](2026-10-07-context-evaluation/captures.json).
[scores.json](2026-10-07-context-evaluation/scores.json) contains per-cell scores,
answers and temporal checks.

The first baseline batch reached the default ten-query throttle. Its one HTTP 429
was not scored. The limit was raised to 1,000 only in the isolated instance, and
the remaining questions resumed without replacing the ten successful captures.
Both arms completed all 55 questions; the changed arm used the same raised limit.

## Changed scope results

Thirty-five of the forty cells have unchanged scores. Five differ:

| Patient / question | Before | After |
| --- | --- | --- |
| 39 / fractures | Negative answer also cites two general musculoskeletal records | Negative answer, no off-topic citations |
| 2606 / heart | Negative answer enumerates twelve blood-pressure/pulse records | Negative answer, no off-topic citations |
| 39 / heart | Cites the normal cardiac examination; F1 1.0 | Negative answer without that citation; F1 0 |
| 39 / kidney | Cites both creatinine measurements; F1 0.8 | Negative answer without renal evidence; F1 0 |
| 39 / mental health | Cites the normal psychiatric examination; F1 1.0 | Negative answer without that citation; F1 0 |

A follow-up read of the real ranked QueryStore endpoint, with the same raw
questions and limit 12, still returns the normal cardiac and psychiatric records.
It returns none of the three on-topic renal records for the kidney question.
Thus these omissions should not all be described as model errors: the renal case
also has a retrieval-coverage limitation. This diagnostic is retained in provenance;
it is a subsequent ranked read, not a recording of the exact inference prompt.

The answers' negative wording does not establish that every omission is a false
clinical claim. It does establish the loss of supporting record coverage under
the native metric. Accepting that tradeoff or changing composition requires an
explicit product-review decision; this report does neither.

## Temporal review

Database truth was frozen before capture, retaining source UUIDs, values, dates
and all records tied at the newest timestamp. The other fourteen cases in each
arm name the expected value or visit date and cite a matching newest source.
Explicit dates in those answers also match. Last-visit questions accept the newest
visit or encounter, consistent with the native probe.

Patient 5587 has weights 56, 54 and 55 kg at the same latest timestamp,
2026-06-01. Both answers choose 55 kg and cite that real record, without explaining
the conflict. This is **one ambiguous case per arm**, not an arbitrary 15/15 pass.
No absent-temporal-record cases are represented in this substitute cohort.

## Limits and follow-up

- This is one capture per cell, on a small substitute cohort. It is not directly
  comparable to earlier native-cohort aggregates and does not establish a stable
  effect size. Repeat affected failures if diagnosing or changing behavior.
- Eye and fracture topics have no positive cases here. Several other positive
  cells represent normal tests/examinations, so coverage is narrower than a broad
  clinical evaluation.
- Medication recall includes historical orders under the native gold. It is not
  current-medication accuracy. The baseline repeated drug names, while the changed
  answer consolidated some of them. The metric scores returned reference entries;
  it does not require every returned reference to remain an inline marker after
  answer rendering. Do not read its medication recall as displayed completeness.
- This supplies measured evidence for #587's review discussion. The reduced
  citation coverage and tied-value handling remain visible findings; substitute
  acceptance and remediation/disposition remain open.
- Temporary capture/analysis adapters stayed outside maintained product tooling.
  No permanent test asserts PR identities, stack arrangement or this one-time run.
