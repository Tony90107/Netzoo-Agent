# Answer buttons, round 2: the needs_fact card and "did you mean X?" answers (2026-10-31, user: "Yes, fix both")

## Why (RESULTS-LIVE.md)

Round 1's live L2 failed 4/12. Where a button was shown and its answer used, 4/4 went from wrong to right (A04, A44).
Two gaps stopped the rest:
1. **A42 x3**: its question came through the `needs_fact` card (basis `needs_fact`; 82 of 425 recorded ASKs), which
   got no buttons -- only the `ask_facts` card did. My B1 check called `ask_choices` directly instead of rendering the
   card the app shows, so it missed this.
2. **A16 x2**: "Did you mean GIRAFFE's result?" -> Yes was bound, but no step uses a bound `jev_link` answer; the next
   turn re-read the request alone and went CLARIFY, then a generic DECLINE.

## Change (on top of round 1's fa95bb40; same flag `NETZOO_ANSWER_BUTTONS`, off by default)

1. The `needs_fact` card gets the same `ask_choices(decision.core)` buttons (one line in `reply_cards/builder.py`).
2. A "did you mean X's result?" button sends the answer in words the next reading can use: **Yes** sends
   "Yes, I mean X's result." and **No** sends "No, not X's result." (`engine/answer_buttons.buttons`, shared with the
   binder, so the click still binds yes/no exactly). No new step applies the answer: the follow-up turn reads the
   request with that reply, as every follow-up is read -- the checks after the reading judge X as they judge any
   workflow the user names. (A step that would turn a bound "yes" into a DO directly was not chosen: a DO needs the
   checks' own plan, which only the reading path builds.)

## Gates

### Offline (pure code; all recorded ASK turns of j1-j8, j9 r1-r3, j10 arm M r1-r3)

- **C1 (hard, real card)**: each recorded ASK is rendered through the card builder's `_core_card` with the branch its
  recording used (`ask_facts` or `needs_fact`, read from the recorded card's headline) and the recorded decision
  (`session.json` plan). Every ASK whose single question has a closed answer set must show buttons, and each button's
  `answer`, sent as the reply to the recorded task state, binds exactly its option -- 100%.
- **C2 (hard, build)**: flags off byte-identical replay (`sa-off.json`); suite no new failures with the flag off and
  on; module sizes.

### Live (after C1-C2; at most 8 conversations, about US$0.06, cap US$0.10, gpt-4o-mini)

The round-1 conversations the gaps hit, with the same `CLICKS.json`: A16 x2, A42 x3, B12 x3 (tags ac1-ac3).
- **D1 (hard)**: none ends worse than its recorded current-system run.
- **D2 (target)**: of the conversations where a button was shown and clicked, >= 70% end at the gold call.

**Stop rule.** C1, C2 or D1 fails -> round 2 withdrawn (round 1's code stays as it was, unmerged). D2 fails with the
rest passing -> no claim; the user decides. Merging needs the user; the flag stays off by default.
