# j8 paired: old 7ad2367f vs new 8f60b653 on a fresh set (2026-10-29) -- NO significant difference

48 fresh sealed items (blind author + blind review), both arms on the app's settings (new also NETZOO_AGENT_ANSWERS
on), up to 3 turns, 1 rep. Spent US$0.287 (old) + US$0.290 (new). `RESULTS-J8.txt`, `score-j8.json`.

| arm | right /48 | strict | FA | FR | MA | extra questions | UNCHECKED |
|---|---|---|---|---|---|---|---|
| old 7ad2367f | 39 | 37 | 2 | 4 | 1 | 1 | 0 |
| new 8f60b653 | 39 | 36 | **1** | **3** | 1 | 3 | 1 |

**Primary (declared): new-only right 3 (Z13, Z31, Z39), old-only right 3 (Z04, Z20, Z22); exact two-sided sign test
p = 1.000 -- no significant improvement.** Secondary: false accepts 2 -> 1 (Z31 fixed, none new).

What the six discordant items are (traced, reported, not used to change the verdict):
- new wins, each from a change made since 10-28:
  - Z13, Z39 (SA, one result per group): old DECLINE full_gap, new DO DRAGON / PUMA -- per-group-scale/-base.
  - Z31 (U, BONOBO, user says the data are not log-transformed/centered): old DO (false accept), new DECLINE
    `jev_answer` -- agent-answer-anchor.
- new losses:
  - Z04: the new arm's capability check got provider error 520 twice (OpenRouter), so the turn was UNCHECKED -- an
    outage, not the code. (Without it: 3 vs 2, p = 1.0; the verdict does not change.)
  - Z20 (U, COBRA, gold DO after "400 genes"): new asked the count question "150 or 400?", bound 400, then asked a
    jev_link confirm "Did you mean COBRA's result?", and after the restate ended DECLINE full_gap. Old asked a fact-agent
    question and ended DO. A count/link path worth tracing.
  - Z22 (U, LIONESS-DRAGON, gold DO): new asked three questions about the same file and never reached DO in 3 turns;
    old reached DO at turn 3.

Reading: the targeted fixes show up on fresh items (3 wins, FA 2 -> 1), but the same number of items got worse, so the
overall score did not move. With 48 items and one rep, a real difference of a few items cannot be told from reading
variance (~20% of items flip between reps on the same code).
