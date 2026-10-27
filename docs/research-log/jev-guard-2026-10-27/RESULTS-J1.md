# Jev guard arm S on sealed j1 (2026-10-27) — NOT PASSED (F1)

Plan: jev-shadow-2026-10-27/PLAN-FRESH.md (approved 2026-10-27). Code: guard commit 0634ead5 (frozen 041f0ee9 + the
guard), NETZOO_JEV_GUARD=shadow, gpt-4o-mini. 48 first turns, runtime code unchanged, spent US$0.1947 (+ smoke
US$0.015). Raw: RESULTS-J1.txt, gates-j1.json.

| | right | FA | FR | MA | wrong kind | extra q |
|---|---|---|---|---|---|---|
| live (frozen) | 37/48 | 2 | 2 | 4 | 0 | 2 |
| with the guard | **40/48** | 2 | 2 | **1** | 0 | 2 |
| Jev alone | 39/48 | | | | | |

- Guard hits: J04, J20, J48 (U items the system answered DO; all three became ASK with a sentence found).
  False alarms: 0 (K 0, DRAGON 0). U 8/12 -> 11/12.
- Gates: F1 **fail** (3 hits; needs >= 4 on >= 4 items), F2 pass, F3 pass, F4 pass, F5 pass (3/3 sentences found).
- As declared, a fail withdraws J-ask; arm A (turns 2-3, F6/F7) is not run.

## Post hoc only (not a gate)

- F1 was close to unreachable on this set: the live system made only 4 MA errors (J04, J20, J46, J48) and J-ask acts
  only on MA by design; it caught 3 (J46: Jev ASK at 0.45, under the threshold). The other errors are FA/FR
  (J11, J24, J17, J37) or a crash (J13), which J-ask cannot touch. I set F1 from h10's 6 MA without checking that
  the set would offer >= 4 MA; that is a design flaw of the gate, not something the result fixes.
- Across every set run so far, J-ask's record is hits 43 (replay) + 2 (h9) + 2 (h10) + 3 (j1), false alarms 0 on
  all four, including the K and DRAGON controls. Only j1 is fresh.
- J13 is a frozen-system crash unrelated to the guard: DRAGON `lambda1` 1.5 fails `TaskDecision` validation
  (`le=1`) during routing and the turn ends in an error instead of a DECLINE.

## User decision (2026-10-27): KEPT

The user kept J-ask despite F1 ("better than the original -> keep"): on j1 right 37 -> 40, MA 4 -> 1, FA/FR
unchanged, 0 false alarms on every set. Arm A then runs as planned on the three changed items (J04, J20, J48), turns
1-3 with the guard on, gates F6/F7.

Declared before arm A: the scripted reply rule (`next_reply`) matches `fact_keywords` against an ASK's question text
only. A `jev_fact` question carries the fact in the quoted sentence, not in its generic question, so for basis
`jev_fact` the match also reads the fact's `user_quote` (the sentence the reply asks the user to settle). F6 is that
keyword check plus my reading of the three replies; F7 = final call right after `reply_fact`, and no DO run on a
wrong final call.

## Arm A (guard on, turns 1-3; J04, J20, J48) — US$0.07 for both runs

First run (guard 0634ead5, `live/j1a`): every turn 1 asked the deciding fact (keywords matched in all 3; the
`reply_fact` branch was sent each time). Defect: on turn 2 the guard asked the same sentence again in J20 and J48
(an option-free answer is never bound, so the question stayed pending and Jev re-read the same sentence); turn 3
ended UNCHECKED. Fixed in 2e18980a: a sentence a Jev question already asked in the task is never asked again
(`already_asked`); unit test added; flag off still 0/1388 replay changes.

Rerun (2e18980a, `live/j1a2`):

| item | turn 1 | turn 2 (after reply_fact) | gold final | frozen system (turn 1, no question) |
|---|---|---|---|---|
| J04 | ASK jev_fact | DO PANDA (guidance) | DECLINE | DO PANDA, no run |
| J20 | ASK jev_fact | DO LIONESS-PANDA (guidance, `already_asked`) | DECLINE | DO/run LIONESS-PANDA, **run_allowed** |
| J48 | ASK jev_fact | DO CONDOR | DO | DO CONDOR |

- F6 pass: 3/3 questions ask the deciding fact.
- F7 pass: final right 1/3 = the frozen system's 1/3, no run approved on a wrong final. The frozen system approved a
  LIONESS-PANDA run on J20 before knowing whether the file is the COBRA matrix; with the guard it did not.
- Not fixed by the guard: after the answer, J04 ("the PPI file was never made") and J20 ("it's the COBRA matrix")
  still get DO guidance. That is the frozen system's follow-up reading, not the guard; Jev only asks.
