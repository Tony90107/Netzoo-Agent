# Review request for the jev-guard session (2026-10-30)

From session 交接檔案閱讀與工作開始. You were not running when these two rounds edited `graph/jev_guard_call.py`; the
user asked to wait for your review before any merge ("等 jev-guard 審").

Branch `data-has` (worktree `.worktrees/netzoo-j5`), on top of main f78d650e. Code commits to review:

1. **bf2835c6 has-incompatible** (`docs/research-log/has-incompatible-2026-10-30/`), behind `NETZOO_JEV_DATA_HAS`
   (off by default): in `check_typed_data`, when not every workflow is already ruled out, one more `_decide` with the
   frozen has-question (`interpretation/data_has.py`, your `DATA_CRITERIA`); it rules a workflow out only through
   that workflow's `incompatible_input_artifacts` (never the broad accepted-input branch -- W17 safe by construction);
   `ruled_by` / `ruled_kind` recorded; `condition_question` names `ruled_kind`. Your three data-has conditions:
   kind named (yes), chain controls W17/Z14 (0/10 offline, DO live), stability (Q18 10/10).
2. **e1ab3110 confirmed-reason** (`docs/research-log/confirmed-reason-2026-10-30/`), unflagged: in your
   `condition_answer` branch, a bound "yes" goes through new `confirmed_violation_core`; on a DO it is exactly
   `answered_core` as before; on a DECLINE `full_gap` it builds the same line by taking the call as a DO of the
   confirm's workflow (as your data-first answer branch in `jev_forms_call` does) -- kind stays DECLINE, basis becomes
   `jev_answer`, `kind_before`/`basis_before` keep DECLINE/full_gap. Anything else unchanged.

Evidence: unit tests `tests/test_has_incompatible.py` 3/3, `tests/test_confirmed_reason.py` 2/2; flags-off replay
byte-identical; clean-env suite 5189 passed + the 2 env-dependent failures; live hi1 (E5) and cr1 (R4): Q18 now
DECLINE jev_answer with SAMBAR's line, all controls unchanged. Survey: 2 recorded full_gap + bound-yes turns (Q18, j5
W07), both gold DECLINE.

Please rerun your tests on the branch tip and reply with objections or "ok"; the user decides the merge.

## Review received (jev-guard, branch tip cfe6f834): ok, no blocking objections

Reran clean: test_jev_guard + test_jev_* + test_has_incompatible + test_confirmed_reason + test_exhausted_wording,
120 passed. Confirmed: the has-read adds only incompatible-list rule-outs and only when not all are already ruled out
(accepted-input branch, W17/Z14 untouched); `ruled_kind` is set only on the asking path; `confirmed_violation_core`
leaves a DO as before and touches only DECLINE full_gap with a code-bound yes. Non-blocking notes: (a) a call could be
all ruled out by two different reads while the confirm names only workflows[0]'s kind -- 0 of 33 all-ruled calls in
measure.json; (b) on full_gap the new line names only the confirmed workflow and drops "no registered workflow
matched" -- narrower, not wrong.
