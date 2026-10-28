# Jev read of a request-level form condition row — offline results (2026-10-28): ALL GATES PASS

Code: `jev_forms.condition_doubts`, called on `condition_requirements`' rows in `capability_check` (flags as before;
no reader = nothing read). Tests: `tests/test_jev_conditions.py` (3). Raw: `measure-after.json` (`measure.py`),
`replay-off.json` / `compare-off.txt`, `replay-on.json` / `compare-on.txt`. Jev reads under US$0.001.

| gate | result |
|---|---|
| C0 off = no change | flags off: harness replay 0 of 1388 changed vs `replay-frozen.json` (right 609 -> 609). Tests: 5100 passed, 51 skipped, 2 failed: the known env-dependent `test_history_says_which_sessions_can_be_resumed`, and `test_planning_model_dump_is_characterized[explicit_panda]`, which fails the same way on main df806e15 in a fresh worktree (not this change; it passed on 2026-10-27) **PASS** |
| C1 precision (hard) | 3/3 written controls keep their reason: time_model P(dynamic) 1.0, spatial P(uses_neighbors) 1.0, group_membership not doubted by the overlap read **PASS** |
| C2 recall | J01 "five time points": Jev P(dynamic) 0.06 (separate 0.42, not_stated 0.52), doubted; the time reason is no longer said **PASS** |
| C3 calls unchanged | flags on: 0 of 1388 calls changed vs `jev-permissive/replay-before.json` (right 610 -> 610) **PASS** |
| C4 reasons | J01's line was "not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; …"; now the layer-2 line "I couldn't match this to anything a registered NetZoo workflow produces or lets you set." No new reason text **PASS** |

One recorded reading: this is a targeted fix for the wrong-reason rule, not a rate.
