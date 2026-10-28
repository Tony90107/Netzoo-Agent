# Answered counts -- offline results (2026-10-29): A1-A3 PASS

Change: parts 1-2 carried from asked-doubts (feature-sized layer counts; `asked_doubts` of any source but `goal`);
part 3 `task_answers._applied_counts`: a known count answer that settled no wait is applied to the single credited
result row (features inside the doubt's words replaced by the answered size, or the answered sample count), re-fitted,
not available with the reason and the user's answer when nothing fits. `router_invocation` passes the turn's task.

| gate | result |
|---|---|
| A1 unit tests | pass 13/13 (`test_answered_counts.py`: X22 re-read without the doubt + "400" -> not available, 800 features, the 31,960,000-value limit and the answer quoted; "150" -> available, 550; a waiting row still settles; two credited results -> unchanged; plus the carried jev and count tests) |
| A2 recorded ad1 turn 2 (`rebuild.py`, `REBUILD.txt`) | pass: X22 -> not_available (feature items 400 transcripts + 400 metabolites = 800, "LIONESS-DRAGON writes at most 20,000,000 values", "You answered ..."); X02 unchanged (available, COBRA) |
| A3 clean-env tests / flags-off replay | pass: 5156 passed, 2 failed = the two known; 0 of 1388 changed |

Added before live (jev-guard review, tests only, code unchanged): a superseded "400" with a known "150" refits to 550
(available); the refusal line is `method_fitting`'s limit holding both 20,000,000 and 31,960,000, followed by the
user's answer quoted; the "150" control stays available. `test_answered_counts.py` 4/4.
