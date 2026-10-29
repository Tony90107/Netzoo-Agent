# A question asked earlier in the task is remembered after a later round replaces it (2026-10-29, user "先照你的順序去做修補")

## Trace (fresh j8, paired run; j8 is now seen)

Z22 (gold DO after "Use the trimmed 800-protein panel"), new arm: t1 the Jev guard asks `jev:which_file` ("Which of the
files do you have?"); t2 the user only restates, and `after_turn` replaces `pending` with t2's fact-agent question --
the unanswered t1 question is now neither pending nor a fact; t3 the user answers and the call is DO, but the guard
asks `jev:which_file` again (`asked_sentences` / `asked_doubts` read only pending + facts). Three questions, no DO.
The old arm reached "already_asked" and DO.

Z20 (the other loss, traced) is reading-level: the answer turn's re-reading read no goal (CLARIFY goal_open), then the
restate turn linked nothing (full_gap), although the count answer "400" was bound. Not addressed here.

## Change

- `TaskState.asked`: questions this task asked that a later round replaced unanswered (`after_turn` appends them);
  `TASK_STATE_VERSION` bumped (a newer saved state is refused by older code, never misread).
- The guard's `asked_sentences` and `asked_doubts` also read `asked` (agreed with the jev-guard session).
Nothing else reads it; binding and the pending list are unchanged.

## Gates (declared before the code)

- **H1** unit tests: the Z22 shape (asked at t1, replaced unanswered at t2) is in `asked` and in both helpers at t3;
  an answered question is not duplicated into `asked`; a closed task starts a new state without it.
- **H2** flags-off replay byte-identical; clean-env tests no new failures.
- **H3 live** (after the user agrees): j8 Z22 plus multi-turn controls from j8 that ended right in the new arm (Z10,
  Z11, Z16, Z19, Z25, Z37, Z48), app settings, up to 3 turns, 1 rep. Hard: no control ends worse than its new-arm run;
  Z22 asks no question twice. About US$0.06.

Stop rule: a failed hard gate -> withdraw. No gate is changed after the run.
