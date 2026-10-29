# asked-history -- offline results (2026-10-29): H1, H2 PASS

| Gate | Result |
|---|---|
| H1 unit tests (`tests/test_asked_history.py`, 4) | pass: Z22 shape -- a jev question replaced unanswered is in `asked`, in `asked_sentences` and `asked_doubts`; an answered question is not kept as asked; a closed task's next state starts clean; **a replaced data confirm stays open**: `pending_condition` returns it, `condition_asked` false, its sentence not in `asked_sentences`, and `confirmed_core` on a DO re-asks it (jev-guard's case); a version-1 state loads with `asked = []`. |
| H2 flags-off replay | byte-identical to main's (1388 readings, right 609). |
| H2 clean-env tests | 5183 passed; the 2 known env-dependent failures only. |

H3 live not run yet.

## Second review fix (jev-guard, before any live run)

Case: confirm replaced -> re-asked -> answered "no" -> the task stays open -> a later round found the old copy in
`asked` and would re-ask an answered confirm. `after_turn` now drops from `asked` every question that is back in
pending or answered (a fact), and keeps one copy per question. Test added (5/5). Full suite re-run: 5184 passed, the 2 known env-dependent failures only.
