# jev-agent once -- offline results (2026-10-29): O1-O3 PASS

Change: `jev_guard_call.agent_doubts` + `agreed_fact_core(agent_asked=...)`: the rule skips a Jev sentence that
overlaps the user words of an agent question the task already asked (pending) or the user answered (facts).

| gate | result |
|---|---|
| O1 recorded turns rebuilt (`rebuild.py`, `REBUILD.txt`) | pass: j6 X02 t2, t3 and X22 t2, t3 -> `already_asked` (recorded: ASK/jev_agent); ra2 W40 t1, J46 t1 -> still `ask` |
| O2 unit tests (`tests/test_r1_jev_agreement.py`) | pass 4/4: pending or answered agent question on the sentence stops the revival; a non-agent pending item does not |
| O3 clean-env tests / flags-off replay | pass: 5152 passed, 2 failed = the two known; 0 of 1388 changed |
