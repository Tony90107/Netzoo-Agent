# Jev menu -- offline results (2026-10-28): K1-K4 PASS -> KEPT (guard flag only)

Change: `result_menu()` options end with "Produces: <the contract's produced_artifacts>." Old vs new menu run on the
175 recorded calls of `links-offline.json` plus j5 W23 / W45 (`menu_ab.py`, `menu-ab.json`, `K-SCORE.txt`), US$0.016.

| gate | result |
|---|---|
| K1 step-4 picks on gold-CLARIFY CLARIFY calls (hard) | pass: 0 -> 0 of 69 |
| K2 step-4 picks on the other 23 CLARIFY calls | pass: 16 -> 17 |
| K3 changed CLARIFY picks | pass: 1 changed, right: h10 W08 (gold DO BONOBO) none (LIONESS-COEXPRESSION 0.45) -> BONOBO 0.99 |
| K4 flags-off replay / tests | pass: 0 of 1388 changed; 5137 passed, 2 failed = the two known |

All 175 calls (jev-guard asked for per-workflow moves): 169 same result; moves LIONESS-PANDA -> GIRAFFE 3,
LIONESS-COEXPRESSION -> BONOBO 1, DRAGON -> none_registered 1, none_registered -> SAMBAR 1. No move between PANDA and
LIONESS-PANDA or among the regulatory_network workflows.

Correction to my first score: K3 first read the rows' `workflows`, which are the recorded call's workflows
(`conditions_data.py`), not the gold's, and so counted W08 against the round. The scorer now reads the gold
workflows from the j1 / h9 / h10 item files; the gate is unchanged.

Reported, not gated (j5, seen): W23 LIONESS-PANDA 0.45 -> GIRAFFE 0.90, but W23 was a `full_gap` DECLINE, where the
link stays off (step 2 withdrawn); W45 (a CLARIFY at turn 1) LIONESS-PANDA 0.45 -> GIRAFFE 0.66, still under the 0.7
threshold, so it would not link live. The old menu's one gold-CLARIFY pick of 10-27 (J23) did not recur (0 now).

Effect in the app: only with NETZOO_JEV_GUARD on (it is on), only on CLARIFY calls; the confirm question quotes the
YAML description, not the menu, so what the user reads does not change.
