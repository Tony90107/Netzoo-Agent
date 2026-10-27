# Jev forms read — live check (2026-10-27)

User decision (2026-10-27): keep the change despite F2 and run the live check. Code 34dbdfc1, `run_live.py` (smoke
jfsmoke: J40; run jf1: 15 items), 1 rep, turns 1-3, gpt-4o-mini, NETZOO_JEV_FORMS=on, NETZOO_JEV_OVERLAP=on,
NETZOO_JEV_GUARD=on. Spent US$0.062 + smoke US$0.012. Raw: `live/jf1/`, `live/jfsmoke/`, `score-jf1.json`,
`live-jf1.log`. All items are seen; this is no generalization claim.

| item | role | expected | calls by turn | final |
|---|---|---|---|---|
| J40 (smoke) | misread | DO | ASK network question -> "Regulators to genes." -> DO | right |
| R39 | misread | DO | ASK network question -> "Regulators to genes." -> DO | right |
| R47, Q13 | misread | DO | DO (mini typed the network correctly this run; Jev not consulted) | right |
| C21 | misread | DO | DO at turn 1 (mini typed not_stated; the user's doubt about which network was not asked) | right by the declared expectation; the item's turn-1 gold is ASK |
| C23 | misread | CLARIFY | CLARIFY (time doubted, row credited to nothing) | right |
| J17 | misread | DO | DECLINE: network typed regulator_gene this run, so the forms read had nothing to act on; another blocker | wrong |
| L35 | misread | DO | ASK jev_condition (the guard's data confirm, against PANDA/OTTER/GIRAFFE), and the runner does not answer it for non-j items | wrong (ended at the ASK) |
| R13 | misread | DO | ASK jev_fact (PPI) -> "Yes" -> DECLINE: time doubted, but the credits fail needs_sign (signed entry not credited); the wrong time reason is still said | wrong |
| HN2, RN1 | control | DECLINE | DECLINE with the time reason; Jev confirmed dynamic | right |
| QN10, SN8 | control | DECLINE | DECLINE with the spatial reason; Jev confirmed neighbours | right |
| Q34, Q18 | control | DECLINE | DECLINE; Jev confirmed a gene-gene (DRAGON) network | right |

- Controls: 0 of 6 asked a form question; 6 of 6 declined with their form reason.
- Misread items: 6 of 9 final right. 2 were asked the form question and both reached DO (3 of 3 with the smoke).
- Jev reads: 0 errors. Every doubt fell on a misread and every confirmation on a control.
- The misread itself appeared in only 4 of the 9 target sessions this run (J40, R39, R13, C23). gpt-4o-mini's typing
  varies from run to run, so most target items never reached the hook.

## Left as they were

- R13: a doubted form on a row with another blocker keeps its (wrong) form reason. The time reason could be left
  unsaid there too, as ROUND-2 did for uncredited rows. Not done; it needs its own round.
- J17 and L35 failed for reasons outside this change: another blocker on J17, and the guard's data confirm on L35.
- C21: the user's doubt about which network went unasked when mini typed not_stated. That is the guard's job (J-ask);
  it did not fire.
