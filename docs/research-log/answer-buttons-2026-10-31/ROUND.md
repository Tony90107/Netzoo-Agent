# Answer buttons for the system's questions (2026-10-31, user: "Answer buttons first")

## Why

- The user: many things can be settled by buttons -- Jev's or a model's suggested options for the user to pick, plus
  a row to type one's own answer, which can then help Jev or a model.
- j10: the data confirm on B31 was the right question 3/3, but "That's right, the two tables come from entirely
  different tumours." was never bound (the yes/no binder reads only the first word), so the refusal fell back to the
  generic line. reason-templates: one of its "wrong" labels was a reply the labeller could not see.
- Today no question has buttons: in the recorded j9 and j10 current-system runs, 0 of 93 ASK turns and 0 of 23
  CLARIFY turns showed choices (`cards.json`, `choices: null`). Every ASK asked exactly one question. Kinds asked
  (j9 + j10 arm M): agent yes/no 20, `group_membership` 18, `jev:condition` (data confirm) 14, `feature_count` 10,
  `sample_count` 9, `jev_link:*` (did you mean X's result) 13, `input_network` 3, `PANDA.with_header` 3,
  `jev:which_file` 3.

## Change (code only after this file is committed)

Branch `answer-buttons` from main 78071415. Flag `NETZOO_ANSWER_BUTTONS`: off (default) / on. Only the reply card and
the binding of an exact button answer change; the decision never does.

1. **Buttons on an ASK card** (`reply_cards/builder.py`, the `ask_facts` branch, through a new module
   `reply_cards/answer_buttons.py`; at most three lines in the builder): the core's question gets a `ReplyChoices`
   with one button per answer and `allow_other` (the "type your own answer" row, which today's follow-up path reads):
   - yes/no questions (an agent question, `jev:condition`, `jev_link:*`, a yes/no dimension such as
     `PANDA.with_header`): **Yes** / **No**;
   - option questions (a dimension with options -- `group_membership`, `input_network`, `jev:which_file` -- and a
     count judged in code, `by_code` with `outcomes`): one button per option, labelled with the option's own words
     (the dimension's label or the outcome), in the question's order.
   The button's `answer` (the text a click sends) is the option's exact words.
2. **Binding an exact button answer** (`engine/task_updates.bind_answers`, a few lines): a reply that equals, after
   folding, the `answer` of one button of the single pending question binds that option, before today's rules. Any
   other reply is bound exactly as today (so typed answers behave as now).
3. Questions without a closed answer set (none seen on recorded ASKs) and CLARIFY's "which result do you want?" get no
   buttons in this round.

## Gates

### Offline (pure code; all recorded current-system ASK turns j1-j8, j9 r1-r3, j10 arm M r1-r3)

- **B1 (hard, round trip)**: for every recorded ASK whose question is one of the kinds above, the new card has its
  buttons, and the recorded TaskState after that turn, given each button's `answer` as the reply, binds exactly that
  option (a yes/no button binds yes/no) -- 100%. Any kind that cannot round-trip is a failure, not left out.
- **B2 (hard)**: with the flag off, cards and replay byte-identical (`sa-off.json`); with it on, every non-ASK card
  identical to off; clean-env suite no new failures; module sizes pass.
- Reported: ASK turns with buttons (today 0), per kind.

### Live (only after B1, B2 and the user's go-ahead; at most 20 conversations, announced, cost listed then)

Recorded current-system conversations whose typed answer was not bound or went wrong (seen; e.g. j10 B31 r1-r3, plus
the others found when listing them), run again with the flag on; the scripted user clicks the button the item's gold
answer names (the `answer` text is what a click sends).
- **L1 (hard)**: no conversation ends worse than its recorded run.
- **L2 (target)**: at least 70% of them end at the gold call.

**Stop rule.** B1, B2 or L1 fails -> withdrawn, code reverted. L2 fails with the rest passing -> no claim; the user
decides. Merging needs the user; the flag stays off by default and the app `.env` is the user's.

## Cost

| part | estimate | cap |
|---|---|---|
| offline B1-B2 | no model call | -- |
| live (later, separate go-ahead) | about US$0.10 for <= 20 conversations, gpt-4o-mini | US$0.20 |
