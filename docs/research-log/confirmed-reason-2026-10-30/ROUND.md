# A confirmed contract violation replaces the "couldn't match" reason (2026-10-30, user "開這一輪")

## Problem (has-incompatible E5, live hi1)

j2 Q18: t1 the guard (with the has-read) ruled SAMBAR out for the user's expression matrix and asked its data confirm;
t2 the user confirmed ("Yes..."; bound `jev:condition = yes`), but the re-reading lost the SAMBAR link, so the call
was already DECLINE `full_gap` ("I couldn't match this to anything a registered NetZoo workflow produces"). The guard's
answer path applies a confirmed "yes" only to a DO (`answered_core`: `answer_not_on_do`), so the user saw the wrong,
unverified reason although they had just confirmed the verified one.

## Change (reason only; the kind never changes)

In the guard's answer branch: a bound data confirm "yes" on a turn whose call is DECLINE `full_gap` gives DECLINE
`jev_answer` with the confirmed contract line -- built by `answered_core` as for a DO, exactly as the data-first answer
branch already does (`jev_forms_call`: the call taken as a DO of the confirm's workflow). `kind_before` / `basis_before`
keep the real DECLINE / full_gap. Any other kind, basis or answer is left as it is. No flag: a DECLINE stays a
DECLINE; only an unverified reason becomes the verified one (top rule: never a wrong reason).

This round sits on branch data-has (has-incompatible's code, flag off), so its live check can run both.

## Gates (declared before the code)

- **R1** unit tests: full_gap DECLINE + bound "yes" -> DECLINE jev_answer quoting the reply and the contract line,
  `kind_before` DECLINE; a DO keeps today's path; ASK / CLARIFY / another DECLINE basis / "no" unchanged.
- **R2** survey of recorded `core.jev_answer` events `answer_not_on_do` with basis_before full_gap and value yes:
  each would become DECLINE jev_answer; listed with its gold (all must be gold DECLINE -- a gold-DO one fails R2).
- **R3** flags-off replay byte-identical; clean-env tests no new failures.
- **R4 live** (after the user agrees): has-incompatible's E5 set again with NETZOO_JEV_DATA_HAS=on; hard: Q18 ends
  DECLINE with SAMBAR's incompatible line; no control worse than in hi1.

Stop rule: a failed hard gate -> withdraw. The jev-guard session (owner of `jev_guard_call.py`) was not running when
this round opened; it reviews before any merge. No gate is changed after the run.
