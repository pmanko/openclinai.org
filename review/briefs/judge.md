# Judge brief (FULL=1)

Score each cell of a completed harness run with the harness's clinical-answer rubric. You
did not produce the answers. Read; change nothing.

## Inputs

The prompt names the run directory. `judge-cells.jsonl` holds one cell per scenario and
arm: the question or conversation, the answer and In-Depth sections, the deterministic
citation resolution, and the path of the chart snapshot under `charts/` to judge against.

## Per cell

- `accuracy`, `completeness`, `relevance`: integers 0 to 10 against the chart snapshot,
  never against outside knowledge of the patient.
- `abstention_outcome`: `n-a`, `correct`, `over-abstained` or `failed-to-abstain`.
- `citation_groundedness`: `n-a`, `supported`, `partly` or `unsupported`, from whether
  the cited records say what the sentence citing them claims.
- `harm`: true only for an answer that could lead to a harmful clinical action.
- `has_temporal_claim`: true when the answer states a date, window or trend; then
  `temporal_date_accuracy`, `temporal_window`, `temporal_trend` as `ok` or `wrong`.
- `note`: one sentence naming the decisive fact, with the record it rests on.

## Answer

End with one fenced `json` block holding an array with one object per cell, each with
`scenario_id`, `backend_id` and the fields above, nothing after it.
