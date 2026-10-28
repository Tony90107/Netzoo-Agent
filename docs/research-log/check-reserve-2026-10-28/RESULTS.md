# The check model's output cap fits gpt-4o-mini — offline results (2026-10-28): ALL GATES PASS

Code: `graph/required_check_budget.capability_max_tokens`, used for the own LLM's max_tokens, `check_output_reserve`
and the fact-check reservation. Tests: `tests/test_check_enum_limit.py` (2 more). Raw: `measure.json` (`measure.py`).

| gate | result |
|---|---|
| R0 unchanged elsewhere | the variable set (9,000) wins; nemotron keeps 16,000; the study-purpose LLM keeps router_max_tokens (unit tests). Harness replay 0 of 1388 changed vs `replay-frozen.json`. Tests: 5105 passed, 51 skipped, 2 failed, both known (the env-dependent supervisor test; `test_planning_model_dump_is_characterized[explicit_panda]`, failing on main df806e15 too) **PASS** |
| R1 no output cut | gpt-4o-mini outputs in the recordings: capability_check n=840 max 2,258; re-read n=193 max 883; second opinion n=72 max 136; condition check n=10 max 8. 0 over 4,000 **PASS** |
| R2 the blocks clear | 65 of 65 recorded `budget.blocked` events of the check model fit the 60,000 limit with a 4,000 reserve (54 re-reads, 11 second opinions) **PASS** |

Live effect not measured: what the unblocked second opinions and re-reads decide needs live calls. The trace that
found this is `TRACE-2026-10-28.md` (all 16 UNCHECKED gpt-4o-mini finals: 11 reserve, 5 enum limit).
