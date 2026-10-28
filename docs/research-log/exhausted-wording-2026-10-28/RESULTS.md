# Exhausted wording -- offline results (2026-10-28): X1, X2 PASS -> KEPT

Change: `task_answers.exhausted_body`, applied in `core_views` only when `EXHAUSTED_NOTE` opens an ASK reply:
"Before I choose a workflow, please tell me:" -> "Still missing:" and "No workflow has been selected and nothing runs
before you answer." -> "No workflow has been selected." Listed questions, quotes and contract lines unchanged.

| gate | result |
|---|---|
| X1 unit tests (`tests/test_exhausted_wording.py`) | pass 2/2: W18's turn-3 body now reads "Still missing:\n- Were the libraries sequenced on one lane? ..." with no "please tell me" / "before you answer"; other text unchanged. Non-exhausted replies do not pass through `exhausted_body` |
| X2 clean-env tests / flags-off replay | pass: 5147 passed, 2 failed = the two known; 0 of 1388 changed |

Not changed (outside the declared scope): an exhausted CLARIFY's own closing line from `clarify_goal` ("Nothing was
selected and nothing runs before you answer."). The deeper W18 causes stay open: the irrelevant doubt was asked at
all (jev-relevance withdrawn), and the replies never bound.
