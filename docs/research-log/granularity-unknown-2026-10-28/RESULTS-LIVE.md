# Granularity left unknown -- live (2026-10-28, user "跑 live"): V1 PASS -> KEPT

Run gu1: code c02e687c, app settings, gpt-4o-mini, turn 1, 1 rep. Spent **US$0.016** (cap 0.10). Raw: `live/gu1/`.

| item | before (recorded) | now | `granularity_left_unknown` |
|---|---|---|---|
| j5 W01 (gold DO: PANDA / OTTER / GIRAFFE per group) | UNCHECKED, "Semantic routing unavailable" | **DO** PANDA, PUMA, OTTER, GIRAFFE (options listed, a question to choose) | fired on hypothesis 0 |
| m3 P29 | interpreter failed | DO LIONESS-COEXPRESSION | fired |
| h2 J45 (three retina samples, LIONESS-PANDA named) | interpreter failed (x2) | DO LIONESS-PANDA | fired |

- **V1 pass**: none of the three ends with the interpreter failure; each turn's first attempt still raised the
  contradiction (with other issues the retry fixed), and the last attempt kept the reading with `unknown`.

Post hoc, not gated: W01's reply ends "If none of these applies: PANDA, LIONESS-PANDA". With the scale left unknown the
default line names the per-sample LIONESS-PANDA although the user wrote "rather than any per-sample networks". The
options themselves (PANDA, OTTER, GIRAFFE, aggregate) are right. A candidate for a later round: the recommender's
default should not add a per-sample sibling when the request's words exclude it.
