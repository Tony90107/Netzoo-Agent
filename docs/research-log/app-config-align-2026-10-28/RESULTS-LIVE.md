# App config align -- live on the app's settings (2026-10-28, user decision "跑 live")

Runner `run_live.py` (ck1's, FORMS off), code 7c9fbdd4, gpt-4o-mini, 1 rep, up to 3 turns. Smoke casmoke (S35)
US$0.013, round ca1 (14 items) US$0.133; total US$0.146 (cap 0.20). Raw: `live/`, `score-casmoke.json`, `score-ca1.json`.

## Check health

| | ck1 (runner, FORMS on) | ca1 (app settings, FORMS off) |
|---|---|---|
| enum 400s | 0 | 0 |
| check-model budget blocks | 0 | **1** (J34) |
| UNCHECKED finals | 0 | **1** (J34) |
| right finals | 11 / 14 | 8 / 14 |

**Defect (J34, declared to be reported, not explained away):** turn 1 took the long reading path (interpreter,
sibling repair, reviewer: 21.4k before routing), then the check (18.4k in) and re-read (11.5k in) reached 57,264 of
the 60,000 check allowance; the second opinion (2.4k in + 4,000 reserve) and fact_check were refused, so the final
is UNCHECKED. `selection_conditions` was also refused at 25,506 of the 30,000 turn budget. These are the same budgets
the runners used, so this can happen under ck1's settings too; the 4 residual turns of the offline replay are the
same kind. Not fixed here.

## Item by item vs ck1 (FORMS-gated events counted per turn: `core.jev_forms`, `core.jev_data_first`, `task.answers_read`)

| item | ck1 | ca1 | cause |
|---|---|---|---|
| S05 | DO right (t1 ASK via jev_forms + data_first) | DECLINE/full_gap wrong | **FORMS off**: ck1 t1 had 2 FORMS events, ca1 none |
| J20 | DECLINE right | ASK x3 wrong (t1 fact_agent instead of jev_fact) | reading variance: 0 FORMS events in either run |
| Q02 | DO right | ASK x3 wrong (t2 needs_fact, t3 jev_link SAMBAR) | reading variance: 0 FORMS events in either run |
| J34 | DO right (t1 CLARIFY) | UNCHECKED | budget defect above (long reading path) |
| S35 | DO wrong | DECLINE right | reading variance (ck1's own smoke ended DECLINE too) |
| J46, Q25 | wrong | wrong | unchanged (J46 data type "several"; Q25 vague -> DO) |
| other 7 | right | right | |

## Reading

- One of the three new misses (S05) is the FORMS flag; turning FORMS on in the app `.env` is the user's call.
- Two (J20, Q02) are reading variance on single runs; 1 rep cannot separate them from settings, and the settings
  of the paths they took are identical to ck1's.
- The aligned settings still leave a budget hole for a long-reading turn (J34). Not a regression from the app's old
  settings (20,000 would have refused more), but the check can still end UNCHECKED.
- Seen, picked items: no system-wide rate.
