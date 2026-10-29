# Decided, no "unavailable" -- offline results (2026-10-29): U1-U3 PASS -> KEPT

Change: `guidance_interaction` returns no `routing_unavailable` interaction when the decision's core call is DO or
DECLINE. UNCHECKED, a missing core, and every other branch are unchanged.

| gate | result |
|---|---|
| U1 unit tests (`tests/test_decided_no_unavailable.py`) | pass 2/2: DECLINE / DO core -> no interaction; UNCHECKED or no core -> `routing_unavailable` as before |
| U2 recorded ac1 j6 X22 t2 (`rerender.py`, `RERENDER.txt`) | pass: main's code gives `routing_unavailable` on this decision (match_basis semantic_validation_recovery); this code gives none, and the next-step prompt becomes "Enter a follow-up question or describe another NetZoo goal."; the DECLINE line with 31,960,000 is the core's own and unchanged |
| U3 clean-env tests / flags-off replay | pass: 5160 passed, 2 failed = the two known; 0 of 1388 changed |

Scope: 44 of the 104 recorded replies with the notice were on a core DECLINE (these lose the contradictory notice);
the 60 on UNCHECKED keep it. No live run (rendering only, as declared).
