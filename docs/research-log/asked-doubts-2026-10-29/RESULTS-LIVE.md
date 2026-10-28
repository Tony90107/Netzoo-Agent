# Asked doubts -- live D4 (2026-10-29): NOT PASSED (X22 final DO)

Runs ad1 (X02, X22, up to 3 turns) and ad2 (W40 t1): code ed07f696, app settings, gpt-4o-mini. Spent US$0.027.

| item | t1 | t2 | final vs gold |
|---|---|---|---|
| X02 | ASK/jev_agent (design table?) | "yes" bound; `jev_agent: already_asked`; DO | **right** (DO) |
| X22 | **ASK/count_fact "150 or 400?"** | "400" bound (`count:feature_count` = 400); `jev_agent: already_asked`; **DO** | **wrong** (gold DECLINE) |
| W40 | ASK/jev_agent, somatic question shown | -- | right (asks) |

Why X22 is DO: turn 2 re-reads the whole request ("Previous NetZoo goal: ..."). This reading typed no doubt
(`unknown_facts` empty), so its LIONESS-DRAGON row is `available` with 400 transcript features and no wait; the bound
answer "400" is applied only to a row waiting on that count (`task_answers.answered_check`), so it had nowhere to go.
In lc1 the turn-2 reading did type the doubt and the same answer gave DECLINE: reading variance meets a structural
gap (a known count answer is not applied when the re-reading drops the doubt).

What did work: the jev part (no revival after any answer: X02, X22 both `already_asked`) and the count part's turn 1
(the feature-sized doubt asked as a code-judged count).

Stop rule: the round's D4 gate (X22 final DECLINE) failed; how to proceed is the user's decision.

## Withdrawn (user decision 2026-10-29: "撤回並開新輪")

Per the stop rule this round is withdrawn and not merged. Both parts are carried, unchanged, into answered-counts-
2026-10-29, which also applies an answered count when the turn's re-reading drops the doubt, under new gates.
