# asked-history -- offline results (2026-10-29): H1, H2 PASS

| Gate | Result |
|---|---|
| H1 unit tests (`tests/test_asked_history.py`, 4) | pass: Z22 shape -- a jev question replaced unanswered is in `asked`, in `asked_sentences` and `asked_doubts`; an answered question is not kept as asked; a closed task's next state starts clean; **a replaced data confirm stays open**: `pending_condition` returns it, `condition_asked` false, its sentence not in `asked_sentences`, and `confirmed_core` on a DO re-asks it (jev-guard's case); a version-1 state loads with `asked = []`. |
| H2 flags-off replay | byte-identical to main's (1388 readings, right 609). |
| H2 clean-env tests | 5183 passed; the 2 known env-dependent failures only. |

H3 live not run yet.
