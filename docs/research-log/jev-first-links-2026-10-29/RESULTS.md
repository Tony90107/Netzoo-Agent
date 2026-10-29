# Jev-first linking, phase A -- results (2026-10-29): A1-A3 PASS for arm H

433 recorded first-turn readings of j1-j6 (269 items; h7/h8 have no recorded readings in this tree), 553 asks, 367
distinct (request, quote) pairs read by Jev once each. Spent US$0.024, 0 errors. Every arm rebuilt with the same
pure-code check (no condition-check or second-opinion answers replayed). `SCORE.txt`, `shadow.json`.

| | M (mini) | J (Jev) | H (Jev when >= 0.7, else mini) |
|---|---|---|---|
| gold DO, right (168 readings) | 101 | 119 (+21 / -3) | **120 (+20 / -1)** |
| gold DO items right on every reading (111 items) | 69 | -- | 79 |
| gold DECLINE, check-level false accepts (126) | 40 | 43 | 42 (5 new, 3 removed) |

- **A1 pass** (H): 120 >= 101 + 5; wrong->right 20 >= 2 x 1.
- **A2 pass** (H): 42 <= 40 + 2. (J would fail A2 at 43; the gate is per arm, and H is the arm that passes all three.)
- **A3 pass**: Jev picks with confidence >= 0.7 on gold-DO asks name a gold workflow 184/194 (94.8%).

Changes worth naming:
- right -> wrong (H, 1): j5 W30, "an OTTER TF-to-gene network for each tissue, pooling the 20 samples" -- Jev chose
  none (0.87).
- new check-level false accepts (H): j2 Q12 x2 (DRAGON), Q44 x2 (COBRA), Q18 (SAMBAR) -- Jev linked the named result
  where mini linked nothing. These are refusals by a condition; whether today's condition check still refuses them
  was not replayed.

Where the remaining errors are (gold DO, H wrong, 48 readings): 46 credit nothing, 2 another workflow. Of the 46,
**39 have Jev linking a gold workflow that code then rules out** -- through mini's typed attributes or counts
(phase B's target), 7 Jev linked another result or none, and none lack an ask.

Limits (stated, not hidden): all sets are seen; check level only (the condition check, second opinion, fact agent
and Jev guard are not in this replay); readings repeat items (arms F/G), so item-level numbers are given too.

Next by the ROUND: propose phase B -- Jev reading the typed fields that rule results out (scale, group_membership,
input_network, time_model, ...), measured the same way, then a fresh-set live test before anything is adopted.
