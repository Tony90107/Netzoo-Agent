# Jev reads the answer to a fact-agent question — offline results (2026-10-28): A1 FAILS, WITHDRAWN (no code written)

Measured with the guard's `judge_answer` and `answered_core` as they are (`measure.py`, `measure.json`; Jev reads
cached in `jev-answer-cache.json`, under US$0.01). Nothing was implemented: the hook and labels were to follow the
offline gates, and the jev-guard session agreed to the plan (owner of step 2: this session).

| gate | result |
|---|---|
| A1 precision (hard) | **2 of 28 gold-DO answer turns became DECLINE: j4f S15 and j4g S15** ("We'll keep 300 genes.", judged `fails` 0.72) **FAIL** |
| A2 recall | 3/3: j1u J09, j3f R01, j3g R01 judged `fails` 1.00 -> DECLINE `jev_answer` (would pass) |
| A0, A3 | not run (stop rule) |

## Why S15 fails (post hoc, labelled)

S15 asks whether 300 or 800 genes will be kept; the deciding contract line is LIONESS-DRAGON's 20,000,000-value limit
(gold DO with 300 genes). The fact agent's turn-1 question quoted another line, `lambda1`'s shrinkage setting. Jev
judged "We'll keep 300 genes" against that unrelated line and read `fails` 0.72. So the answer judge is only as good
as the contract line the fact agent chose, and that choice is the model's writing, the same reason code never applied
agent answers. Two other fact-agent questions in the population also quote lines that do not decide them (M01's
"filtered export", M09's panel size: `meets` at 0.20-0.30, harmless here).

## Reported

- M04 "No idea, sorry; …": judged `unclear` 0.97 (t2 and t3, both runs). It is ASK there, so nothing would change.
- Q17, R11 (already DECLINE `full_gap`): `fails` 0.98 / 1.00. R07, J45, W04, Q28, S44, M07 also read `fails` on
  turns that already decline.
- Turns with no recorded call (p5 M02, M04-A/D, M06-A: the reply restates the request) show `UNCHECKED` in
  `measure.json`; that is the script's placeholder, not a change.
- The jev-guard session reports that `judge_answer`'s confidence varies between runs on the same input (j2 Q33: 0.88,
  then 0.40). No repeat-stability check was run, since A1 already fails.

## Separate issue found (not fixed here)

`bind_answers`' yes/no path binds "No idea, sorry; …" as `no` by its first word (p5 M04, both runs). It reaches every
agent yes/no question. Nothing applies agent answers today, so no call is wrong from it yet, but any step that trusts
the bound value would be.
