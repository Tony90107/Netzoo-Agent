# Check fixes (enum limit + output cap) — live check (2026-10-28)

User decision (2026-10-28): run live on the seen conversations where the two bugs hit. Code 7c9fbdd4 (branch
`jev-conditions`), `run_live.py` (smoke cksmoke: S35; run ck1: 14 items), 1 rep, up to 3 turns, gpt-4o-mini, the three
Jev flags on (as the recorded runs). Spent US$0.129 + smoke US$0.013 (cap 0.20). Raw: `live/ck1/`, `score-ck1.json`
(`score_live.py`), `score-before.json` (`score_before.py`: the recorded runs of the same items). All items are seen.

| | right | enum 400s | check-model budget blocks | provisional checks | UNCHECKED finals |
|---|---|---|---|---|---|
| recorded runs (before) | 2 / 14 | 6 | 12 | 6 | 10 |
| ck1 (after) | **11 / 14** | **0** | **0** | **0** | **0** |

**Selection caveat:** the recorded runs were chosen because the bugs hit them, so "before" is the worst case for these
items; the gain is not a rate for the system. What the run shows is that the failure modes are gone: two 5-sentence
third turns (J06 t3, S35 t3) were checked with the compact schema, and no optional check call was refused.

## Misses (3)

- **J46** (gold ASK): DO, as in the recorded run. The data read put 0.37 on `several` (a file of unknown kind among
  three inputs). Not related to the fixes.
- **Q25** (V, gold CLARIFY: "look at gene interactions"): DO at turn 1. Before, UNCHECKED. The check now runs and the
  goal read takes the vague request as a named result. A goal-read miss, newly visible.
- **S35** (gold DECLINE after the fact): t1 ASK `jev_fact`; t2 the user says "I checked: it's the COBRA
  batch-adjusted co-expression matrix." The guard's data read (coexpression_network 0.88) rules LIONESS-PANDA out and
  asks its yes/no confirm. The scripted reply repeats the sentence; the yes/no binder reads only a first word, so it
  does not bind; t3 the confirm is `already_asked` and the call is **DO, a false accept**. Before, this turn was
  UNCHECKED (the enum 400). The fix let the check run and exposed the natural-reply gap on the yes/no confirm (the
  smoke run of the same item ended DECLINE at t2: its turn 1 went another way).

Right: J06, J20, J34, J48, Q02, Q10, Q26, R03, R21, S03, S05.
