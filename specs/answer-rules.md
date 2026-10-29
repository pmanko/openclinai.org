# Answer rules: deterministic checks for the faults the judges find

**Spec ID:** `ANSWER-RULES-2026-10` · **Status:** started 28 October 2026 (owner) · **Owners:**
umbrella (this spec, runs, records), Hub (the rules, their tests and their place in the gate)

Runs A2 to D4 showed that model checks at the sizes this host runs do not move the judged
scores and see under a tenth of the judged faults
([run D4 record](reviews/2026-10-28-confidence-labels-run-d4.md)). The deterministic date
check is the only check right often enough to show a clinician, and the judged faults recur in
patterns the chart's own records can decide. This stream turns those patterns into rules in
the same deterministic gate. The default profile is `single-12b-bare` (owner, 28 October), so
the rules are what the clinician's answer is checked by.

## Failure patterns (runs D3 and D4, both judges, every Hub arm)

Read from the judges' notes and per-point verdicts (`work/rules/judged-faults.md`, 142 wrong
points and 46 faulted cells over the Hub arms). Each pattern recurs in every arm, so it is the
writer's, not a check's.

| # | Pattern | Where it was judged | What the chart holds |
| --- | --- | --- | --- |
| P1 | A "past 6 months" table or list includes older records | am-orders-6mo, date-aloice-orders-table: accuracy 5 in every arm | each record's date and the reference date |
| P2 | Relative time words that the cited records' dates contradict ("the last two months" for January records in June; "past week" for a January form) | ek-growth, date-zabella-weight-table, convo-medications-adherence | record dates, reference date |
| P3 | The latest value is months before the reference date and the answer does not say so | ek-growth (4.5 months), am-weight-trend (5 months) | the series' last point |
| P4 | A trend gives the endpoints and drops the readings between, or calls an up-and-down series steady | am-weight-trend, ek-growth | every point of the series |
| P5 | A drug name cites another drug's order record ("stavudine [1]" where [1] is nevirapine) | convo-medications-adherence, convo-abstention-honesty | drug order records |
| P6 | A non-antiretroviral is called part of the antiretroviral regimen (RHZE, co-trimoxazole) | date-aloice-orders-table, date-aloice-last-visit-exact, am-orders-6mo | drug names; a fixed class list |
| P7 | The demographics record is cited for a clinical statement | convo-safety-escalation, single-upcoming-appointments | the record's class (`Patient:`) |
| P8 | Advanced HIV disease denied although WHO stage 3 or 4 (or CD4 below 200) is recorded | convo-diagnosis-evidence | WHO stage and CD4 records; the WHO definition |
| P9 | "The record does not state a diagnosis" although an HIV programme enrolment is recorded | convo-diagnosis-evidence: accuracy 6 in every arm | programme and diagnosis records |

Not rules (owner, 28 October: a rule is general or reads its parameters from the chart, and
what cannot be generalised now is not built): P6 needs a drug classification the system does not
carry (a hand list of antiretrovirals would fit the rule to these charts) and P8 a disease-specific
definition (WHO advanced HIV disease). Also out: a historical drug called current, a "None" plan
described as managing a risk and an omitted active diagnosis, which need a model of which orders
and plans are current. Any of them returns only with a general mechanism, for example a
classification source the deployment supplies.

## What the research says

- Deterministic clinical fact-checking works when the summary and the record are reduced to
  the same atomic tuple (entity, attribute, value, time) and typed checks compare them:
  numerical, temporal, presence (omission), negation, implication. A recent LLM-free checker
  of this kind reached 0.89 precision against clinicians; its errors came from extraction
  (wrong entity boundaries, wrong value pairing, missed times), not from the logic
  ([granular fact-checking, 2025](https://arxiv.org/html/2512.16189v4)). Our own misfires
  agree: every deterministic false mark in D3 and D4 was an extraction error ("cells" matching
  white blood cells, the 3 of "mm3", a change amount read as a value).
- Implication rules from a clinical source (pneumonia implies an antibiotic; here, WHO stage 3
  implies advanced HIV disease) are the checks that need a named reference, not a model.
- Omission is the main fault class of clinical answers and the hardest to judge; a presence
  check is only decidable where the question names what must be present (a series in a
  window, the latest value) ([omissions in medical summarisation](https://arxiv.org/pdf/2311.08303),
  [conformal safety layer](https://arxiv.org/pdf/2606.08969)).
- Temporal confusion (historical facts read as current) is a documented failure of LLM
  clinical reading ([chain of thought in clinical text](https://arxiv.org/pdf/2509.21933)).

## Rules for these rules

1. A rule reads only the chart's records, the temporal facts and the reference date; no model.
2. A rule edits the answer only with chart-derived text: dropping a table row or list line
   whose cited records fall outside the asked window, replacing a citation with the record
   that states the named drug, appending a sentence built from the series. It never rewrites
   a clinical statement; a contradiction it can prove is marked with the chart's value.
3. Each rule is scoped to the words it understands (the extraction step). A misfire found in a
   run becomes a test before the next run.
4. Every rule reports a finding named `rule_<name>` with the chart's value, in the answer's and
   the In-Depth's gate checks, so the dashboard, the report and the envelope share it.
5. A rule's marks are measured against the judge like every check (confidence-labels L1, LG1).
6. A rule is general or takes its parameters from the chart in hand: no built-in list of drugs,
   diseases or measurements, no cutoff fitted to the charts it was written from. When a value
   is old comes from the series' own measuring rhythm; which words name a measurement comes
   from the chart's other measurements; which drug a record holds comes from its drug order.
7. Evidence for a rule comes from patients and questions it was not written from. A replay on
   the runs that showed the pattern is development work, not measurement.

## Target path

- [ ] R1 Window: under a question that names a window ("past 6 months", "last year"), a table
  row or list line whose cited records all predate the window start is dropped and the answer
  says how many were dropped; a prose sentence citing only such records is marked.
- [ ] R2 Relative time: a claim saying "the last/past N days, weeks, months" (or "last week",
  "last month") whose cited records all predate that span before the reference date is marked
  with the records' dates.
- [ ] R3 Stale latest value: an answer about a series whose gap from its last reading to the
  reference date is longer than any interval between its own readings, and that does not give
  the gap, gets one sentence naming the last date and the gap.
- [ ] R4 Series: a trend answer that names two or fewer of a series' in-window readings gets
  the readings appended (up to eight, else count, first, last, lowest, highest); "steady",
  "steadily", "consistent" or "continuous" about a series that changes direction is marked
  with the readings.
- [ ] R5 Drug citation: a drug name followed by a citation to a drug order of another drug
  gets the citation of the order that names it (preferring a record the answer already cites,
  then the latest); with no such order it is marked.
- [ ] R7 Demographics citation: a claim that cites only the patient demographics record for
  anything but name, sex, age, birth date, address or identifier is marked.
- [ ] R9 Diagnosis presence: a claim that the record states no diagnosis while an active
  programme enrolment or diagnosis record names a condition is marked with that record.
- [ ] R10 Measured on held-out patients: charts captured for 10 to 20 HIV-baseline patients the
  rules were not written from, scenarios that exercise each pattern and question types the rules
  were not written for; first an unjudged pass counting how often each rule fires, with a hand
  check of a sample; then one judged run of the default (bare) and the built-in reference. Per
  rule, marks and edits against the judge, recorded in `reviews/`. A rule keeps marking only if
  it clears LG1 there.

## Order of work

1. R1 to R5, R7 and R9 built in one Hub layer (`answer-rules`, PR #52), each tested on the
   fixture charts with the D3 and D4 texts and on a diabetes chart the rules were not written
   from; the development replay on D3 and D4 is in
   [the replay record](reviews/2026-10-28-answer-rules-replay.md). The ChartSearchAI panel names
   the findings "Chart rule" (ESM `findings-view`). A judged run on the same 17 scenarios was
   started and stopped (owner, 28 October): a temperature-0 writer on the same questions would
   reproduce the development answers and give a false signal.
2. R10 on held-out patients.
3. The rules that clear LG1 keep marking; a rule below it runs hidden until fixed or dropped.
