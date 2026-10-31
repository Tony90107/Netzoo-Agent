# no-reask offline results (2026-11-01): N1, N2 pass

Code 758595d0: `interpretation/answered_doubts.py` (pure), `graph/fact_check_call._without_answered` (flag, record
`core.no_reask`, rule "R9 answered"); `tests/test_no_reask.py`.

- **N1** (`offline.py` -> `N1.md`): 18 fact-agent questions on later recorded turns; 3 blocked, each read: ca-P3-2 t2
  ("at least three tumour samples?" after the count was answered 2), ca-P4-2 t2 and ca-P4-3 t2 (the same "at least
  three matched samples?" after it was answered no / yes). No other question blocked; a form answer blocks nothing.
- **N2**: unit tests pass; flags-off replay byte-identical to `sa-off.json`; clean-env suite 5204 passed, 1 failed =
  the known `explicit_panda`.

Next (user's go-ahead): live M1/M2, 8 conversations (P3, P4 x 4), about US$0.04, cap US$0.08.
