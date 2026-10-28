# Mixed notation -- live (2026-10-28, user "跑 live"): N1, N2 PASS -> KEPT

Run mn1: code 47d0c769, app settings, gpt-4o-mini, turn 1, 1 rep, 4 seen items. Spent **US$0.010** (cap 0.10).
Raw: `live/mn1/`, `live-mn1.log`.

| item | gold | call | candidate facts | wait |
|---|---|---|---|---|
| R35 (target) | ASK | **ASK/count_fact** (right; before: DO, j3 2/2 and fc1) | feature_count 200 / 600 only | 200 -> LIONESS-DRAGON, 600 -> none |
| R22 (target) | DO | DO/run (right; exit 2 = the run preview) | none (before: "1 or 60", "2 or 90" in 2/2) | -- |
| J40 (control) | ASK | ASK/count_fact | sample_count 25 / 30 | 25 -> LIONESS-DRAGON, 30 -> none |
| W39 (control) | ASK | ASK/count_fact | sample_count 2 / 4 | 2 -> none, 4 -> LIONESS-PANDA |

- **N1 pass**: no target reading keeps a digit/word candidate fact.
- **N2 pass**: both controls keep their candidates and wait on them in code.
- R35 now asks the right question on turn 1 (feature-count-doubts + mixed-notation together).
