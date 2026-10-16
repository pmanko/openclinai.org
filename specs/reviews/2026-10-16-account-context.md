# Account context to the model (16 October 2026)

Live check of the account-context items on the owner's Mac, from umbrella branch
`claude/account-context-plan` with ChartSearchAI pinned at `ca136063`
([fork #35](https://github.com/pmanko/openmrs-module-chartsearchai/pull/35)) and the
Hub at `3269502` ([Hub #34](https://github.com/pmanko/med-agent-hub/pull/34)).

## Component checks

- ChartSearchAI: the five focused provider and REST test classes passed (67 tests);
  `mvn -B -pl api,omod -am test` passed, api 3,036 run (62 skipped) and omod 336 run.
- Hub: `tests/test_requester_context.py` failed before the change and passed after;
  the full suite passed (718) in `python:3.11-slim` with `HUB_BUILD_REVISION` set.

## Reset on the new pins

`make chartsearch-research-setup`, 13:46:26 to 13:51:18 (4 min 52 s), exit 0: the
published baseline restored with nothing re-embedded, all modules started and all
seven accounts log in. No new baseline was needed.

## Two accounts, one question

Each account signed in with Outpatient Clinic as its session location and asked
the Hub `single-12b-checked` profile on the sample chart "What is this patient's
most recent weight?" through `POST /ws/rest/v1/chartsearchai/chat/stream`.

| Account | Hub trace requester step | Saved turn `accountContext` assigned roles | Answer | Turn time |
| --- | --- | --- | --- | --- |
| `eval-nurse` | `Requester: Application: Uses ChartSearchAI (Research), Organizational: Nurse at Outpatient Clinic` | Uses ChartSearchAI (Research), Nurse; location Outpatient Clinic | 71 kg on 2026-01-26, citing [19] | 467 s |
| `eval-pharmacy` | `Requester: Application: Uses ChartSearchAI (Research), Organizational: Pharmaceutical Technologist at Outpatient Clinic` | Uses ChartSearchAI (Research), Pharmaceutical Technologist; location Outpatient Clinic | 71 kg on 2026-01-26, citing [19] | 282 s |

The line names every assigned role, including the shared access role. For the
nurse, the Hub's In-Depth checker withheld the In-Depth section because the model
cited the wrong records for its claims; the checked answer itself was correct.
