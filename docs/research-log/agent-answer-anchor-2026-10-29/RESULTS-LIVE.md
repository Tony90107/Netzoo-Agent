# agent-answer-anchor -- live (2026-10-29, user "跑 live")

## aa1 + aa2: code b6a68489, app settings + NETZOO_AGENT_ANSWERS=on, gpt-4o-mini, up to 3 turns, 1 rep

aa1's reserve guard cut W16 after turn 1 and never started X29 (spent US$0.08); aa2 ran those two whole (US$0.013).
`SCORE-LIVE.txt`.

| item | role | gold final | live |
|---|---|---|---|
| J09 | target | DECLINE | t1 ASK jev_agent -> t2 **DECLINE jev_answer** (fails 1.0) |
| R01 | target | DECLINE | t1 ASK jev_agent -> t2 **DECLINE jev_answer** (fails 1.0) |
| W16 | target | DECLINE | t1 ASK fact_agent -> t2 **DECLINE jev_answer** (fails 1.0) |
| Y14 | target | DECLINE | t1 ASK jev_agent -> t2 **DECLINE jev_answer** (fails 1.0) |
| J19, R23, S11, S13 | control | DO | t2 DO; step reached, Jev `meets` 1.0, call kept |
| Q21 | control | DO | t2 ASK jev_fact -> t3 DO (step not reached on a DO) |
| X29 | control | DO | t1 DO (no question asked) |

- **L1 pass**: no control declined; all 6 end DO (gold DO).
- **L2 pass**: 4 of 4 targets end DECLINE `jev_answer`.

## Defect found and fixed after aa1/aa2 (display, not a gate)

The lines quoted the whole turn message -- "You answered "Previous NetZoo goal: ... User follow-up: ..."" -- because
an answer turn's message carries the previous goal. The step now passes Jev and the line only the text after "User
follow-up:" (as `goal_evidence` does); unit test added. The offline measurement already used the reply alone
(`scan.py` splits the same way). Verified in aa3 below.
