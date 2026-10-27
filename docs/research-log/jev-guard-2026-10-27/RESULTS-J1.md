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
