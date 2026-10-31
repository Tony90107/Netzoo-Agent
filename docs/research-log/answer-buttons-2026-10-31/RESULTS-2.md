# answer-buttons round 2: offline results (2026-10-31)

Code d47050ff (on round 1's fa95bb40): the `needs_fact` card gets `ask_choices(decision.core)`; a "did you mean X's
result?" button sends "Yes, I mean X's result." / "No, not X's result." (shared rule in `engine/answer_buttons.py`,
so the binder still binds yes/no exactly).

## C1 real card (`offline2.py` -> `C1.md`, `c1.json`)

Each recorded ASK rendered through `_core_card` with the branch its recording used and the recorded decision.

- **210 of 225 ASKs show buttons and every button binds exactly its option: 0 failures.** By card: `ask_facts` 165
  (agent 60, data confirm 31, did-you-mean 29, sample count 17, feature count 11, which file 7, data property 6,
  input exists 4); `needs_fact` 45 (group membership 35, input network 9, network given 1).
- 7 have no closed answer set (open counts, two-question ASKs): no buttons, as designed.
- **8 render on other cards and get no buttons**: 6 setting questions (PANDA `with_header`) shown on the run-held card
  ("PANDA was not planned: confirm the run you want first."), and 2 agent questions whose turn showed no card. C1 as
  written renders the two ASK cards; read strictly ("every ASK whose single question has a closed answer set must
  show buttons") these 8 are not covered. Reported, not decided by me -- the user decides, as with round 1's B1.

**Harness correction, disclosed.** The first C1 run failed 9 `input_network` turns. Cause: it built the binding state
from the trace's copy of the core, whose options are listed in another order than the decision the card is built from;
the task state the app kept (`session.json`) has the card's order, and every button binds there. The check now uses
the app's saved task state. The gate is unchanged.

## C2 build

- Flags off: harness replay byte-identical to `sa-off.json`.
- Clean-env suite with the flag off and on: 5195 passed, 2 failed -- the known `explicit_panda`, and
  `test_server_supervisor::test_history_says_which_sessions_can_be_resumed`, which reads this checkout's real session
  history (`.netzoo/sessions`, where round 1's live run left conversations waiting). With those sessions set aside it
  passes; on a checkout without them (netzoo-rt) it passes. Not a code failure.
- Module sizes pass.

## Next (needs the user's go-ahead)

Live D1/D2 as ROUND-2.md: A16 x2, A42 x3, B12 x3 with the same `CLICKS.json`, about US$0.06, cap US$0.10.
