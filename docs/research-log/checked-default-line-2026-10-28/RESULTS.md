# Checked default line -- offline results (2026-10-28): D1-D3 PASS

Change: `condition_recommender.checked_default_line` / `with_checked_default_line`, called at the end of
`invoke_router`'s checked path: the tie question's "If none of these applies: ..." keeps only the workflows the
capability check credited for a result (dropped when none; unchanged when the check credited no result).

| gate | result |
|---|---|
| D1 recorded replies (`survey.py`, `SURVEY.txt`) | pass: 51 replies with the line, 32 changed, 0 changed where nothing was credited (9 unchanged). Per-sample requests (25 DLBCL patients, 56 asthma samples, 74 ovarian tumours) keep LIONESS-PANDA and lose PANDA; "an aggregate PANDA network" loses LIONESS-PANDA; requests that named OTTER / CONDOR / PUMA lose the PANDA line |
| D2 unit tests (`tests/test_checked_default_line.py`) | pass 3/3 |
| D3 clean-env tests / flags-off replay | pass: 5143 passed, 2 failed = the two known; 0 of 1388 changed |

The first full run also failed `test_core_modules_stay_reviewable` (router_invocation.py 1,001 lines > 1,000); the
step was moved into `condition_recommender.py` and the router keeps one call. D1 checks the rewrite on the recorded
reply text; whether the final reply carries the router's question on every path is only visible live.
