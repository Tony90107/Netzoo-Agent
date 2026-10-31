# count-answers offline results (2026-10-31)

Code bd9d2040: `graph/count_answer_call.py`; 3 hook lines in `routing_planning.py`; `count_answer` added to the DECLINE
bases that clear the plan (`core_decision.with_core`) and to the answer-line rendering (`core_views.decline_reply`, as
`jev_answer`: the user's answer and the contract line only, never "No registered workflow ..."). Those two one-word
edits are outside the ROUND's "new module + hook" wording; they are needed so the refusal neither keeps a plan nor
claims more than the line says. `tests/test_count_answers.py` 5 tests.

| gate | result |
|---|---|
| E1 (hard) yes answers unchanged; no answer turns a gold-DO end into a refusal | pass -- but **vacuous**: 0 in-scope recorded answer turns. Only 12 agent yes/no answers were ever bound in the recorded runs (the scripted replies to "at least three samples?" are sentences such as "QC cleared all of them", not "yes"/"no"), and none was about a sample minimum. The offline step has no evidence either way; the live step carries it. |
| E2 (hard) build | pass: unit tests; flags-off replay byte-identical to `sa-off.json`; clean-env suite 5201 passed, 1 failed = the known `explicit_panda`; module sizes |

Live prompts fixed before any run: `LIVE-PROMPTS.json` (P1 the user's biopsy prompt; P2-P4 alike). Needs the user's
go-ahead: 12 conversations, about US$0.06, cap US$0.12.
