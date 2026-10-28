# Granularity left unknown -- offline results (2026-10-28): U0-U4 PASS

Change: `graph/semantic_attempts.granularity_left_unknown`, called on the last attempt only: when every remaining
issue is a hypothesis's `granularity_contradicts_request`, those hypotheses keep their reading with granularity
`unknown` (their granularity evidence dropped) and are validated again; event `routing.granularity_left_unknown`.

| gate | result |
|---|---|
| U0 calibration (code before the change reproduces each recorded issue list) | 7 of 8 reproduced; the Chinese local run has no session file (not gated, English-first) |
| U1 granularity-only cases validate, other fields unchanged | pass 6/6: W01, P29, J19 x2, J45 x2 -> valid, granularity `unknown`, every other outcome field unchanged |
| U2 a case with another issue still fails | pass: j1smoke S02 (ungrounded artifact evidence on both hypotheses) still invalid, unchanged |
| U3 unit tests (`tests/test_granularity_unknown.py`) | pass 3/3: recorded W01 reading kept; mixed / unscoped issues keep the failure; the call sits only under `attempt + 1 >= MAX_SEMANTIC_ATTEMPTS` |
| U4 clean-env tests / flags-off replay | pass: 5140 passed, 2 failed = the two known; 0 of 1388 calls changed (the replay does not exercise the interpreter) |

Raw: `revalidate.py`, `revalidate-old.json`, `revalidate-new.json`. What the rest of the turn does with an `unknown`
granularity (the capability check reads scale itself) is only visible live.
