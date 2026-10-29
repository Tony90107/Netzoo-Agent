# jev-links-first P4 live on fresh j7 (2026-10-29): **FAIL** -> withdrawn, flag code reverted

Code 152de421, app settings, gpt-4o-mini, up to 3 turns, 1 rep; arms paired by item: j7off (flag off) and j7on (flag
on). Spent US$0.19 + US$0.19 = US$0.37. Full table: `RESULTS-J7.txt`, `score-j7.json`.

| arm | right /30 | strict | FA | FR | MA | extra questions |
|---|---|---|---|---|---|---|
| off | **21** | 20 | 3 | 3 | 1 | 1 |
| on | **20** | 20 | 3 | 4 | 0 | 3 |

- **Hard gate 1 FAIL:** right on (20) < off (21). Hard gate 2 (FA on <= off + 1) passes (3 = 3).
- Stop rule applied: the flag code (152de421) is reverted on this branch; nothing was merged.

Changed items (7), off -> on:
- better: Y16 (FT, LIONESS-PUMA) FR -> right; Y25 (U) MA -> right ASK on COBRA; Y20 (N) right on the wrong workflow
  LIONESS-COEXPRESSION -> COBRA (strict right).
- worse: **Y06, Y24 (SA, one network per group) right DO -> DECLINE "couldn't match"**; Y30 (GT) DO -> an extra
  question; Y19 (V) no call -> an extra question.

Why Y06 and Y24 broke: Jev picked "none" with confidence 0.82 / 0.87 for "one TF-to-gene network per diet / per stage,
each built from all ... of that group" -- the same miss as phase A's only right->wrong (j5 W30, 0.87). The menu
offers the sheet's result texts ("One weighted TF-to-gene network across all the samples given"), and Jev does not
take "one per group" as that result. Phase A's check-level shadow could not show this: it scored 1 such reading among
168, while j7 has 2 SA items of 30.

Read on the evidence: Jev linking helps where mini links the wrong workflow (Y20, Y25, Y16), and hurts on per-group
requests, which mini now handles (per_group, merged today). A fix would change what the menu offers for an aggregate
result (e.g. per group), i.e. the menu text -- not done here; it would be a new round with its own gates.
