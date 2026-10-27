# Jev overlap second read — live check (2026-10-27)

User decision (2026-10-27): G2's denominator was declared too wide; keep the change and run the live check in
ROUND.md. Code 42dbc65d, `run_live.py` (tag jo1, after a 1-session smoke josmoke), 13 conversations × 1 rep, turns
1-3, gpt-4o-mini, NETZOO_JEV_OVERLAP=on, NETZOO_JEV_GUARD=on. Spent US$0.086 (+ smoke US$0.005). Raw:
`live/jo1/`, `score-jo1.json`, `score_live.py`. All items are seen, so these results are no generalization claim.

| item | gold | j2g final (overlap off) | jo1 calls by turn | final |
|---|---|---|---|---|
| Q01 | DO | DECLINE | DECLINE/full_gap [overlap reason] | wrong |
| Q02 | DO | DECLINE | ASK/fact_agent -> ASK groups -> UNCHECKED/check_unconfirmed | wrong |
| Q13 | DECLINE | DECLINE | CLARIFY -> DECLINE/full_gap [overlap reason] | right kind, wrong reason |
| Q18 | DECLINE | DO | ASK groups -> DECLINE/full_gap ("couldn't match") | right kind, generic reason |
| Q29 | DO | DECLINE | ASK groups -> DO | right |
| Q36 | DO | DECLINE | CLARIFY -> ASK groups -> DO | right |
| Q38 | DO | DECLINE | CLARIFY -> ASK groups -> DO | right |
| H26 (h5 Q26) | DO | – | DO (mini read not_stated; Jev not consulted) | right |
| J01 | DO | – | ASK groups -> DO | right (one needless question) |
| JN8 QN5 | DECLINE | – | DECLINE, Jev P(overlap) 1.0 | right |
| ON5 SN1 | DECLINE | – | DECLINE (Jev not consulted) | right |

- Controls: 0 of 4 were asked the group question; 4 of 4 declined with the overlap reason, which is right for them.
- The 7 j2 items: 5 right vs 1 for j2 arm G. These are different runs, 1 rep each, on seen items.
- Not-overlap items: 7 of 9 right (counting Q13 and Q18 by kind).
- Jev overlap reads: P(overlapping) was 0 on all 14 not-overlap reads and 1.0 on all 4 control reads. 0 errors.
- Binding: every group question was answered "One group each." and bound in code (`task.answers_bound`
  `dimension:group_membership ... one_group`: Q02 Q18 Q29 Q36 Q38 J01). On the next turn the re-read typed
  `one_group` itself, from the reply in the follow-up text. So the rows were available without `answered_check`
  having to settle a waiting row; that path is covered only by the unit test.

## Left as they were

- Q01, Q13: gpt-4o-mini credited the grouping ask to no workflow (`delivered_by: []`). The hook does not act, and the
  decline still prints "none returns overlapping memberships". These are linking misses that leave a wrong reason.
- Q18: after the answer, the re-read credited nothing, and the decline uses the generic "couldn't match" line. The
  kind is right; the real reason (SAMBAR takes no expression matrix) is not given.
- Q02 t3: the row was available, but the call was UNCHECKED (check_unconfirmed). That is the reading's variance,
  seen in j2 arm G too; the guard cannot cause it.
- Q29 t2: DO, plus a "couldn't match" line for the non-request sentence about the abstract deadline.
