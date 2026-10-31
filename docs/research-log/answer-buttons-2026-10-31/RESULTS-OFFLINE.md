# answer-buttons offline results (2026-10-31)

Code fa95bb40: `engine/answer_buttons.py` (which answers a pending question offers -- shared by card and binder),
`reply_cards/answer_buttons.py` (the ASK card's `ReplyChoices`, with the own-answer row), 3 lines in
`reply_cards/builder.py`, 6 lines in `engine/task_updates.bind_answers` (an exact button answer binds that option),
`tests/test_answer_buttons.py` 6 tests. Deviation from ROUND.md: the shared rule lives in `engine/` (the binder's
layer) rather than `reply_cards/`, so the binder does not import the card package.

## B1 round trip (`offline.py` -> `B1.md`, `b1.json`; pure code)

225 recorded ASK turns (j1-j8, j9 r1-r3, j10 arm M r1-r3): **218 get buttons, and every button of all 218 binds
exactly the option it shows -- 0 failures.** By kind: agent yes/no 62, group membership 35, data confirm 31,
"did you mean X's result" 29, sample count 17, feature count 11, input network 9, which file 7, data property 6, a
boolean setting (with_header) 6, input exists 4, network given 1.

7 ASK turns get no buttons:
- 1 open question with no candidates (j9 A12 t3, "How many independent biological samples are available ...?") --
  no closed answer set, as step 3 of ROUND.md says.
- **6 ASKs that asked two questions at once** (j3 R18, R37; j4 S32, S39; j7 Y25; all older runs -- in j9 and j10
  every ASK asked one). ROUND.md assumed one question per ASK. Read strictly, B1 ("every recorded ASK whose question
  is one of the kinds above ... has its buttons") is not met on these 6; read as the round trip of the buttons shown,
  it passes. I report both and do not choose between them: the user decides. With two questions the binder would
  also need to know which question a click answers; the card shows one choice block. Those turns stay typed-only,
  exactly as today.

## B2 build

- Flags off: harness replay byte-identical to `sa-off.json` (paths normalised).
- Clean-env suite: 5196 passed, 1 failed = the known `explicit_panda`, with the flag off and with it on (non-ASK
  cards and every other test unchanged by the flag). Module sizes pass.

## Next (needs the user's go-ahead)

Live: at most 20 recorded conversations whose typed answer was not bound or went wrong, rerun with the flag on and
the scripted user clicking the gold answer's button; L1 (hard) none ends worse, L2 (target) >= 70% end at the gold
call. About US$0.10, cap US$0.20.

## User decision (2026-10-31)

"Pass, run live": B1 is counted as passed (the 6 two-question ASKs stay typed-only, as today). The live run's clicks
are fixed in `CLICKS.json` before it starts: 12 conversations (j9 A16 x2, A42 x3, A04 x2, A44 x2; j10 B12 x3), the
recorded current-system runs whose first question gets buttons and that ended wrong.
