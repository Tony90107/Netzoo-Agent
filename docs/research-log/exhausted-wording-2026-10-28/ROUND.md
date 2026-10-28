# An exhausted ASK says what is missing, not "please tell me" (2026-10-28, user: "修連問三次")

## Trace

j5 W18 turn 3 is the designed P3 exhausted ASK (two rounds asked, `task_answers.EXHAUSTED_NOTE`): it opens "I have
asked about this request twice already, so I will not ask again." But `core_views` only puts the note in front of the
normal ASK body (`ask_facts`: "Before I choose a workflow, please tell me: ... No workflow has been selected and
nothing runs before you answer."), so the reply asks the same question a third time right after saying it will not.
The other exhausted path (`engine/task_updates`, a reply that answers nothing) already writes "Still missing:".

Recorded replies with the note: 18; with "please tell me" after it: 9; with "before you answer": 10.

## Change

When the note opens the reply, the ASK body's head "Before I choose a workflow, please tell me:" becomes "Still
missing:" and "No workflow has been selected and nothing runs before you answer." becomes "No workflow has been
selected." (the note already says nothing runs until then). The listed facts, quotes and contract lines are unchanged.
Non-exhausted replies are unchanged.

## Gates (declared before the code)

- **X1** unit tests: an exhausted ASK reply contains no "please tell me" and no "before you answer", keeps every
  listed question line; a non-exhausted ASK reply is byte-identical to before.
- **X2** clean-env tests: no new failures; flags-off replay 0 of 1388.
- No live run (wording only).
