# Check allowance -- offline results (2026-10-28): ALL GATES PASS

Change: `CHECK_EXTRA_TOKENS` 30,000 -> 45,000 (`graph/capability_check_call.py`); tests that pinned the 60,000 ceiling
now pin 75,000, and the "15k left" preflight test keeps its 15k (60,000 used of 75,000).

| gate | result |
|---|---|
| A1 0 check-family refusals on the recorded gpt-4o-mini turns | pass: 808 turns, family refusals 2 turns -> 0, J34 ca1 t1 included |
| A2 no call goes from run to refused | pass: 0 |
| A3 routing refusals unchanged | pass: `selection_conditions` 4 = 4, `hypothesis_bases` 2 = 2 |
| A4 clean-env tests | pass: 5105 passed, 2 failed = the two known ones |

Raw: `replay_allowance.py`, `replay-allowance.json`.

Note on calibration: the replay uses recorded tokens where preflight estimates input from characters, so on the old
allowance it refuses J34's (and ca1 R21 t2's) re-read, where the live run refused the second opinion and fact check
after the re-read. Either way the family call lost is a check-family call, and on 45k none is lost.

Live: not run. J34's long reading path is random, so a rerun may not reproduce it; a rerun needs the user's go.
The runners (`run_live.py`) set `OPENROUTER_CAPABILITY_EXTRA_TOKENS=30000` explicitly, so later live rounds must drop
or raise that line to measure the app's default.
