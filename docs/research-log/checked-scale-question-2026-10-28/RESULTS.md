# Checked scale question -- offline results (2026-10-28): S1-S3 PASS

Change: `condition_recommender.checked_scale_question`, applied in `with_checked_default_line` after the check is
attached: routing's "Should the result be aggregate or sample-specific?" is removed when every result the check
credited has a stated scale (`per_sample` / `whole_cohort`); event `routing.scale_question_dropped`.

| gate | result |
|---|---|
| S1 recorded replies (`survey.py`, `SURVEY.txt`) | pass: 20 distinct recorded replies with the question (the ROUND's 38 counted copies in both trees); removed in the 11 whose credited results all state a scale, kept in the 6 with an `unstated` scale and the 3 with nothing credited |
| S2 unit tests (`tests/test_checked_scale_question.py`) | pass 2/2 (plus the default-line tests) |
| S3 clean-env tests / flags-off replay | pass: 5145 passed, 2 failed = the two known; 0 of 1388 changed |

Spot check of the 11 removals: each request states its scale ("a co-expression network for each of our 25 pancreatic
islet donors", "a LIONESS co-expression network for each region", W01 "built from all tumour samples together") or
names a one-scale method (OTTER); j3 R38's turn 2 follows the user's chosen result.
