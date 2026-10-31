# answer-buttons live (2026-10-31): L1 pass, L2 FAIL (4/12) -> no claim; the user decides

Tags ab1-ab3, code fa95bb40, the app `.env` plus NETZOO_ANSWER_BUTTONS=on, clicks fixed in `CLICKS.json` before the
run, up to 3 turns. US$0.117 (cap US$0.20); code unchanged during the run. Score `LIVE.md` (`score_live.py`).

| gate | result |
|---|---|
| L1 (hard) none ends worse than its recorded run | **pass**: 0 |
| L2 (target) >= 70% end at the gold call | **FAIL**: 4/12 (A04 x2, A44 x2 -- all four wrong when recorded) |

## What happened, per item

- **A04 x2, A44 x2 -- the buttons worked.** "Did your pipeline log-transform the expression values?" -> click Yes;
  "Did you mean COBRA's result?" -> Yes, then "350 or 600 genes?" -> 600. All four now end at the gold call (DO);
  recorded, the scripted user could only restate and all four ended wrong.
- **A42 x3 -- no buttons were shown.** Its question ("one group each, or several groups at once?") came through the
  `needs_fact` card (basis `needs_fact`, the legacy dimension path), and only the `ask_facts` card got buttons. The
  scripted user fell back to typing, as recorded. **This is a defect of my offline B1 check**: it called
  `ask_choices(core)` directly instead of rendering the card the app shows, so it counted buttons the user never
  sees on `needs_fact` ASKs (82 of 425 recorded ASKs have that basis).
- **A16 x2 -- the click bound, nothing used it.** "Did you mean GIRAFFE's result?" -> Yes was bound (`jev_link`), but
  no step reads a bound `jev_link` answer: turn 2 re-read the request, went CLARIFY, and turn 3 refused with the
  generic line. A button cannot help an answer the system never applies.
- **B12 x3 -- not reached.** This time turn 1 was DO with no question (run-to-run variance), so no click was possible.

## What it shows

- When the question is shown with buttons and the answer feeds a step that uses it (an agent question, a count), a
  click turns a lost conversation into a right one (4/4 here).
- Two gaps stop the rest: buttons missing on the `needs_fact` card, and answers to "did you mean X's result?" that
  nothing applies. Both need code changes, so a new round with its own gates (and an offline check that renders the
  real card).
- Nothing merged; the flag stays off; the branch keeps the code (the stop rule leaves an L2 failure to the user).
