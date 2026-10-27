# Data check before form questions — live check (2026-10-27)

User decision (2026-10-27): 6 sessions, all three Jev flags on, code 297b44fc (E4 included). `run_live.py` (tag jd1),
1 rep, up to 3 turns, gpt-4o-mini. Spent US$0.051. Raw: `live/jd1/`, `score-jd1.json`, `live-jd1.log`. All items are
seen; this is no generalization claim.

| item | data | calls by turn | data-first | final |
|---|---|---|---|---|
| S32 | ruled out | CLARIFY -> ASK jev_condition (data confirm instead of the group question) -> "Yes, it's TPM expression from RNA-seq." bound in code -> DECLINE jev_answer | ask, declined | right |
| Q18 | ruled out | group question -> confirm reply (not bound: Jev not_stated) -> DECLINE full_gap (layer-2 lines) | no_violation (typed read missed the data again) | right kind, unverified reason |
| S10 | ruled out | CLARIFY -> result reply -> ASK jev_condition ("is the data ... proteomics, metabolomics ...? (yes or no)") -> scripted restate, not an answer -> ASK jev_link | ask | wrong (ASK); the item has no reply for a data confirm |
| S05 | acceptable | network question -> natural answer bound by Jev -> DO | no_violation | right |
| R31 | acceptable | group question -> natural answer bound by Jev -> DO | no_violation | right |
| S39 | acceptable | DO at turn 1 | (not a form ASK) | right |

- E4 works live: S32's "yes" to the swapped confirm declines on the answer turn, where before it ended at the round
  cap with no call.
- Data acceptable: 0 of 3 got a data confirm; all reached DO. Final right: 5 of 6.

## Found (not this step's code)

- S32's decline line reads: 'You answered "Yes, it's TPM expression from RNA-seq." about "". the workflow's contract:
  "SAMBAR incompatible_input_artifacts: expression_matrix". So the workflow cannot do this as you asked.' It has an
  empty quote (the guard placed no sentence), says "the workflow" for SAMBAR (the bound fact has no workflows), and
  quotes a field key, not contract text. The guard's DO path produces the same line, so this lives in its
  `answered_core` / confirm wording. Reported to the jev-guard session.
- S10: the data confirm was the right question, but the scripted user restated instead of answering. The run shows
  the question order, not the decline.
