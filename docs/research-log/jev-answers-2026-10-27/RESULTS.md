# Jev answer binding for form questions — offline results (2026-10-27): ALL GATES PASS

Code (branch `jev-answers`, from main ce8be114):
- `interpretation/jev_forms.py`: `ANSWER_VALUES`, `BIND`, `answer_value`, `bind_form_answers`.
- `graph/jev_forms_call.py`: `answer_reader`, which keeps its own reads.
- `engine/task_updates.py`: `_jev_answers` after `bind_answers` (event `task.answers_read`).
- `interpretation/core_decision.py`: `form_doubt`, and `_facts` merging one question per doubted form.
- `interpretation/task_answers.py`: a bound doubted-form answer settles every waiting row.
- Tests: `tests/test_jev_answers.py` (5).

Flag: `NETZOO_JEV_FORMS=on` (shadow and off read nothing). Jev answer reads cost US$0.0005.

Raw: `cases.json`, `synthetic.json`, `answer_q.py` (frozen), `reads.json` (`measure_answers.py`), `merge.json`
(`measure_merge.py`), `replay-off.json`, `replay-on.json`, `gates-replay.txt`.

| gate | result |
|---|---|
| B0 off = no change | flags off: replay 0 of 1388 calls changed vs replay-frozen.json. Tests: 5090 passed, 51 skipped, 1 failed, the known env-dependent `test_history_says_which_sessions_can_be_resumed` (this worktree holds j4's recorded sessions) **PASS** |
| B1 recall | 8 of 8 unbound natural answers bind the right value: S02, S05 t1/t2 regulator_gene at 0.99-1.0; S39, R12, R18, R31, R34 one_group at 0.99-1.0. T3 binds not_dynamic, P3 not_spatial **PASS** |
| B2 precision (hard) | 0 wrong bindings. S10, S32 and X1-X4 bind nothing. G1 G2, T1 T2, P1 P2 and N1 bind their stated ruling value; N2 binds nothing (other 0.83) **PASS** |
| B3 code first | Jev reads only questions the code binding left open (unit test); the 9 option-label answers bind in code as before, and `bind_answers` is unchanged **PASS** |
| B4 merge | S32 t2, S39 t1 and R18 t2: 2 group questions -> 1 each. Unit test: one bound answer settles two rows quoting different words. Flags-on harness replay: 0 of 1388 calls changed vs main's flags-on replay (jev-forms-r2 replay-on.json) **PASS** |

## Notes

- A binding to the ruling value (G1, T1 ...) is the user's own answer: the row then follows its outcome for that value
  (no registered workflow), as `answered_check` already does for code bindings. Jev still never lifts a limit that the
  user did not answer away.
- Not measured offline: the whole multi-turn path (the next turn's re-read with the bound fact). The unit test covers
  binding plus `answered_check`. A live check would need the user's approval.
