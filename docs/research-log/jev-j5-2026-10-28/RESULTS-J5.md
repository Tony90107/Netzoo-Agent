# j5 results -- baseline of the app's settings on a fresh sealed set (2026-10-28)

Run j5a: code 7ad2367f unchanged throughout, app settings (GUARD, OVERLAP, FORMS on; own check model; 30k turn
budget; 45k check allowance), gpt-4o-mini, 48 conversations, up to 3 turns, 1 rep. Spent **US$0.29** (cap 0.80).
Scores: `RESULTS-J5.txt`, `score-j5.json`. j5 is now seen.

## Headline

| | j5 (this run) |
|---|---|
| right finals | **36 / 48 (75%)** |
| FA / FR / MA | 4 / 3 / 1 |
| extra questions / wrong question kind / UNCHECKED | 2 / 1 / 1 |
| enum 400s, check-family budget refusals, provisional checks | 0, 0, 0 |
| form reasons said on a DECLINE the item did not ask for | 0 |

j4 arm G was 38/48 on another set and other settings; cited only, not compared.

By group: form traps and controls 13/15, data type T+TC 6/7, MF 2/3, SA 2/3, SP 2/2, P 2/2, N 5/6, V 2/4, **U 2/6**.

## The 12 wrong finals, by cause (classes declared in PLAN-J5.md; read from the traces)

| class | n | items | what happened |
|---|---|---|---|
| **linking** (result words -> workflow) | **3** | W23, W45, W41 | "activity of each TF in each sample" + "activates or represses" not linked to GIRAFFE (W23 at t1, W45 after CLARIFY); "one partial-correlation network linking proteins and metabolites" not linked to DRAGON (W41, after CLARIFY). All three end in a no-match DECLINE |
| **binding of a reply** | **3** | W42, W16, W39 | W42: natural answer to the group_membership question not bound, asked 3 times. W16: "raw counts" answer led to a reroute to LIONESS-COEXPRESSION (DO) instead of declining BONOBO; the per-edge p-value requirement was dropped. W39: "only two lungs" answer to the 2-or-4 count question not applied; went to a jev_link question, then CLARIFY |
| counts | 1 | W26 | fact question asked about the wrong threshold ("at least 60?"); the answer 70 gave DO, the 20M-value cap left to a file check (319,600 pairs x 70 = 22.4M) |
| form | 1 | W11 | time-lagged model: the reply says no workflow models change over time, yet the call is DO on DRAGON |
| data type | 1 | W40 | somatic-vs-germline doubt never raised; DO on SAMBAR |
| goal | 1 | W43 | after the per-sample reply (2 samples, below the minimum) the vague opening sentence was credited as a result -> DO |
| fact question on an irrelevant doubt | 1 | W18 | asked about sequencing lanes (no contract condition) 3 times |
| routing reader failure | 1 | W01 | semantic routing output failed validation (ValueError) -> UNCHECKED |

No check-budget, enum or reserve failure occurred.

## Reading

- On the app's settings the system gets 75% of a fresh set right; the check layer is healthy.
- The U group (one open fact) is the weakest: 2/6. Its failures are mostly what happens **after** the user answers
  (W16, W39, W26), not the question itself (4 of 6 asked a right question at t1).
- Two classes tie at 3: linking (W23 and W45 are the same GIRAFFE description; W41 DRAGON) and binding of a reply
  (three different kinds of answer: form, fact, count). Linking has been tried twice before and failed precision;
  binding of a reply is where answers to questions the system itself asked are lost.
- One rep per item: single misses may be reading variance.
