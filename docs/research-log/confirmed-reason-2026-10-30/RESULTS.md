# confirmed-reason -- offline results (2026-10-30): R1-R3 PASS

| Gate | Result |
|---|---|
| R1 unit tests (`tests/test_confirmed_reason.py`, 2) | pass: a full_gap DECLINE + bound "yes" -> DECLINE jev_answer quoting the reply and SAMBAR's line, `kind_before` DECLINE / `basis_before` full_gap; a DO keeps today's path; ASK, CLARIFY, another DECLINE basis and a confirm with no workflow are left as they are. |
| R2 survey | recorded `answer_not_on_do` turns with basis full_gap and a code-bound "yes": **2** -- has-incompatible hi1 Q18 t2 (gold DECLINE; SAMBAR / expression) and j5a W07 t2 (gold DECLINE; its confirmed line "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff" is the gold's own reason). Both gold DECLINE: pass. (Jev-judged answer turns are another path, untouched.) |
| R3 | flags-off replay byte-identical; clean-env tests 5189 passed, only the 2 known env-dependent failures. |

R4 live not run yet. The jev-guard session (owner of `jev_guard_call.py`) was not running; it reviews before a merge.
