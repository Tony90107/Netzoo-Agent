# Data check before form questions — offline results (2026-10-27): ALL GATES PASS

Code (branch `jev-answers`): `graph/jev_forms_call.data_first_core` / `apply_data_first`, hooked in
`graph/routing_planning.py` right after `apply_jev_guard` (event `core.jev_data_first`). It runs only with
`NETZOO_JEV_FORMS=on` and `NETZOO_JEV_GUARD=on`. It calls the guard's `check_typed_data`, `conditioned_core` and
`asked_sentences` unchanged, and `jev_guard_call.py` was not edited. Tests: `tests/test_jev_data_first.py` (3).
Jev typed reads: US$0.0007.

Raw: `cases.json`, `measure.py`, `measure.json`, `gates-replay.txt`.

| gate | result |
|---|---|
| E0 off = no change | flags off: harness replay 0 of 1388 changed vs replay-frozen.json; tests 5093 passed, 51 skipped, 1 failed (the known env-dependent `test_history_says_which_sessions_can_be_resumed`) **PASS** |
| E1 precision (hard) | 0 of 23 data-acceptable form ASKs changed (typed reads: regulatory_network or mutation_matrix, 0.46-1.0, none ruling out) **PASS** |
| E2 recall | 4 of 5: j4g S32 t2 and ja1 S32 t2 (expression_matrix 1.0 vs SAMBAR); j4g S10 t2 and t3 (measurement_dataset 0.73 / 0.80 vs CONDOR). Missed: jo1 Q18 (typed read "several" 0.32, so nothing ruled out) **PASS** |
| E3 shape | all 4 changed calls are ASK `jev_condition` from `conditioned_core`, with evidence kind_before ASK and the form questions they replaced; no DO or DECLINE made here **PASS** |

## Notes

- The harness replay does not run the graph's planning step, so it shows only that flags-off is unchanged. The
  effect is measured on the recorded calls above.
- E4 (ROUND.md amendment, PASS): the guard declines a bound "yes" only on a DO, and S32's turn-2 call is the form
  ASK again. This step now declines it (`answered_core` on the DO copy). `test_the_confirms_yes_declines_on_the_answer_turn_even_when_the_call_is_the_form_ask_again`
  and `test_the_confirms_no_leaves_the_form_question` pass. The gap was found by the jev-guard session's review;
  my first note here wrongly said the guard's path covered it.
