# has-incompatible -- live E5 (2026-10-30, user "跑 live"): **FAIL** (Q18's reason) -> withdrawn

Run hi1: code bf2835c6, app settings + NETZOO_JEV_DATA_HAS=on, up to 3 turns, 1 rep. US$0.055. `SCORE-E5.txt`.

| item | role | gold | hi1 |
|---|---|---|---|
| **Q18** | target | DECLINE | t1 ASK jev_condition (data-first: **has expression_matrix 0.70 -> SAMBAR ruled out by the has-read**); t2 "Yes..." bound, but the re-read linked nothing -> DECLINE **full_gap** ("couldn't match"); the guard's answer path: `answer_not_on_do` |
| S32 | target | DECLINE | ASK jev_link -> ASK jev_condition -> DECLINE jev_answer, SAMBAR's incompatible line |
| S42 | target | DECLINE | ASK jev_condition (data read, PANDA) -> DECLINE jev_answer |
| W17 | chain control | DO | DO at t1 (the guard's own data read 0.72 ruled CONDOR out by its broad branch -- not all workflows, so no confirm) |
| Z14 | chain control | DO | DO |
| S08, W36 | DO control | DO | DO |
| Q37 | DO control | DO | t1 ASK jev_link -> t2 DECLINE full_gap (**FR**; no data read involved: a linking miss) |

- **Hard (controls)**: no control ended in a confirm-then-decline -- pass. Q37's false refusal is a link loss, not
  this change (no `core.jev_condition` read on it).
- **Hard (Q18 ends DECLINE with the incompatible line)**: **FAIL**. The has-read did its job at t1 (the confirm was
  asked for the right reason); at t2 the re-reading lost the SAMBAR link -- the Z20 pattern -- so the call was already
  a full_gap DECLINE and the guard applies a confirmed "yes" only to a DO. Stop rule: withdrawn (the flag code stays
  only on branch data-has, never merged).

What it shows: Q18's right reason needs two things at once -- the has-read (this round) and the link kept on the
answer turn (carry-links, which needs Q18 refused rightly). One way through that does not loosen anything: when the
user has confirmed a contract violation and the turn is already a DECLINE that credits nothing, the confirmed contract
line replaces the "couldn't match" reason (the call stays DECLINE; only an unverified reason becomes a verified one).
That is in the guard's answer path (jev-guard session's code) and would be its own round. Note too: Q18's has-read was
0.70 here (0.73-0.81 in the 10x run) -- right at the threshold.
