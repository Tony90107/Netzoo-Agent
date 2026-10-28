# Jev reads the answer to a fact-agent question against its contract line (2026-10-28) — declared before code

User decision (2026-10-28): fix the remaining problems in order. This is R01. Declare gates, measure offline, then ask.
Branch `jev-conditions` (J01's fix first), worktree `.worktrees/netzoo-j4`.

## Problem

j3 R01: "I'd like BONOBO … I don't know whether anyone centered the genes after the log transform." Turn 1 is ASK
`fact_agent`: "Did you center the genes after the log transform?", quoting BONOBO's contract ("… requires the caller to
declare log_transformed=true and centered=true …"). The reply "No, it was never centered; it's just log2 values." is
bound in code (`agent:BONOBO = no`), but an agent question's answer is only recorded (`task_answers`: what yes or no
leads to is the fact agent's own writing, `if_yes` / `if_no`, which code does not trust). Turn 2's new reading credits
BONOBO and the call is DO (gold DECLINE). j1 J09 is the same ("No, nobody ever built a PPI file for sorghum." -> DO
GIRAFFE, gold DECLINE).

The yes/no binding cannot simply be applied: p5 M04's "No idea, sorry; …" is bound `no` by its first word.

## Change (new flag `NETZOO_JEV_AGENT_ANSWERS`, default off; acts only with `NETZOO_JEV_GUARD` on too)

1. `engine/task_updates._pending`: an agent question that quoted a contract line keeps it as labels (`contract`,
   `workflow`), as Jev's own questions already do. Binding is unchanged (agent questions have no options, and the
   guard's `asked_contract_question` / `condition_answer` still select only `jev:` questions).
2. A new step after the data-first step in `routing_planning`: on the turn that answers an asked agent question with a
   contract line (bound this turn, or still pending), the guard's `judge_answer` reads the user's reply against that
   line (meets / fails / unclear, its frozen question), and the guard's `answered_core` makes the call: only a DO
   becomes DECLINE `jev_answer`, only on `fails` >= 0.7, its reason the user's answer and the contract clause (both
   verbatim). Anything else leaves the call. Neither the fact agent's `if_yes` / `if_no` nor the first-word binding
   decides anything here.

The guard's functions are called unchanged (`jev_guard_call.py` is not edited); the jev-guard session is told before
any code.

## Population (`scan.py`, `population-raw.json`)

Every recorded answer turn after an ASK `fact_agent` with a contract quote: 67 turns. The step can change only those
whose call is DO: 30 turns, 16 items. Labels (one labeller, me, with the item golds where the set has them):
- the answer fails the contract line, gold DECLINE (3 turns, 2 items): j1u J09; j3f R01, j3g R01.
- the answer meets it, or is no answer (a restated request), gold DO (27 turns): J19, J29, Q21, R21, R23, R37, S11 x2,
  S13 x2, S14 x2, S15 x2, p5 M01 x6, M03 x4, M06 (S08), M09 x2.
The other 37 turns (ASK, CLARIFY, DECLINE, no call) cannot change by construction; reported.

## Measurement

For each DO answer turn: the recorded turn-2 call, the turn-1 question (question, user quote, contract quote,
workflow) and the reply go through `judge_answer` (real Jev, cached in `jev-answer-cache.json`) and `answered_core`.
The hook and the labels are covered by unit tests.

## Gates

- A0, off = no change: with the flag off the step reads nothing; flags-off harness replay 0 of 1388 changed vs
  `replay-frozen.json`; the test suite has no new failures beyond the two known ones (env-dependent supervisor test;
  `test_planning_model_dump_is_characterized[explicit_panda]`, failing on main df806e15 too).
- A1, precision (hard): 0 of the 27 gold-DO answer turns become DECLINE.
- A2, recall: >= 2 of the 3 fails turns become DECLINE `jev_answer`, both items.
- A3, shape: every changed call is DO -> DECLINE `jev_answer` whose line quotes the reply and the contract clause; no
  other change.
- Reported: Jev's read on M04's "No idea" (it is not a DO there, so nothing changes), and on Q17 / R11 (already
  DECLINE `full_gap`).

Stop rule: if A1 fails, the change is withdrawn as declared.
