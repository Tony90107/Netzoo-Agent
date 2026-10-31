# answer-buttons round 2 live (2026-10-31): D1 pass, D2 FAIL (4/6) -> no claim; the user decides

Tags ac1-ac3, code d47050ff, the app `.env` plus NETZOO_ANSWER_BUTTONS=on, the clicks of `CLICKS.json`, up to 3 turns.
US$0.050 (cap US$0.10); code unchanged during the run. Score `LIVE-2.md` (`score_live2.py`).

| gate | result |
|---|---|
| D1 (hard) none ends worse than recorded | **pass**: 0 |
| D2 (target) clicked conversations at the gold call >= 70% | **FAIL**: 4/6 (67%) |

## Per item

- **A42 x3 -- fixed by round 2.** The `needs_fact` card now shows "One group each" / "Several groups at once"; the
  click bound and all three ended DO (gold). Recorded: ASK three times in a row, wrong.
- **B12 -- 1 of 3 asked**; that one was clicked ("5") and ended right. The other two decided DO on turn 1 with no
  question (as in round 1): not clicked, still wrong, not counted in D2.
- **A16 x2 -- the click went through, the reading did not change.** "Yes, I mean GIRAFFE's result." was sent; turn 2's
  reading again credited `giraffe.tf_activity` but put "needs sign" on that ask, and left "whether it switches each
  target on or off" unlinked, so code ruled GIRAFFE out and the turn ended DECLINE with the generic line. This is the
  reading defect found earlier (one result split wrongly; GIRAFFE's signed matrix is a separate sheet entry), not a
  button problem: no answer to "did you mean X?" can fix how the request is split.

## Both rounds together (reported, not a gate)

Conversations where a button was shown and clicked: round 1 A04 x2, A44 x2 (4/4 right); round 2 A42 x3, B12 x1 (4/4
right), A16 x2 (0/2, the reading defect). 8 of 10 end right; all 10 were wrong when recorded. No conversation ended
worse in either round.

## Status

Nothing merged; flag off by default; code on branch `answer-buttons` (fa95bb40 + d47050ff). Open scope notes for the
user: 8 ASKs render on other cards (run-held setting questions, no card) and 6 two-question ASKs get no buttons.
