# Jev forms round 2 — offline results (2026-10-27): ALL GATES PASS

Change: `interpretation/jev_forms.forms_doubts`. On a credited, refused row where something else still blocks the
credits (another typed attribute, or the method checks), each doubted form with a form reason is added to
`doubted_forms`. That covers time_model, spatial, and group_membership when the overlap read doubts it. Status,
credits and waits are unchanged. Tests: 2 new in `tests/test_jev_forms.py`. Jev reads came from the jev-forms caches
(no new calls).

Raw: `measure-before.json` / `measure-after.json` (`measure.py`, 69 readings), `gates-measure.json`,
`replay-off.json`, `replay-on.json`, `gates-replay.txt`.

| gate | result |
|---|---|
| G0 off = no change | flags off, replay 0 of 1388 changed vs replay-frozen.json; tests 5085 passed, 51 skipped, 1 failed: the known env-dependent `test_history_says_which_sessions_can_be_resumed` (local awaiting_answer sessions from this worktree's live runs) **PASS** |
| G1 controls keep their reason (hard) | 20 control readings print a form reason; 0 lose it **PASS** |
| G2 misreads lose the wrong reason | 5 of 5 (R13: j3g t1, t2; j3f t1; jf1 t1, t2) **PASS** |
| G3 calls and rows unchanged | flags-on replay 0 of 1388 changed vs jev-forms replay-forms.json; 0 rows changed status, credits or wait **PASS** |
| G4 reasons | 5 changed lines, each now layer 2 ("I couldn't match this to anything a registered NetZoo workflow produces or lets you set."); 0 new reason text **PASS** |

## Note

R13's right answer (DO with GIRAFFE) is still not reached: gpt-4o-mini credits GIRAFFE's tf_activity but not its
signed-regulation entry, so `needs_sign` rules the credits out. This round only removes the wrong reason. The credit
miss is a linking problem.
