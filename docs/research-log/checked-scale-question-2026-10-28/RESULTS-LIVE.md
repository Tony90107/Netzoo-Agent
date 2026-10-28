# Checked scale question -- live (2026-10-28, user "跑 live"): T1 PASS -> KEPT

Run cs1: code 859364c1 (with granularity-unknown and checked-default-line), app settings, gpt-4o-mini, turn 1, 1 rep.
Spent **US$0.016** (cap 0.05). Raw: `live/cs1/`.

| item | call | scale question | events |
|---|---|---|---|
| j2 Q06 ("a co-expression network for each of our 25 pancreatic islet donors") | DO BONOBO | **gone** (recorded j2f/j2g: asked) | `scale_question_dropped` (scales: per_sample) |
| j5 W01 (aggregate, "rather than any per-sample networks") | DO PANDA, PUMA, OTTER, LIONESS-PANDA, LIONESS-PUMA | **none** (cd1: asked) | `granularity_left_unknown`, `default_line_checked` |
| C53 (control, scale unstated) | DO LIONESS-COEXPRESSION, COBRA, BONOBO | kept | -- |

- **T1 pass**: neither W01 nor Q06 ends with the scale question; the unstated control keeps it.

Post hoc, not gated -- W01 still names LIONESS-PANDA in this run: the check read both results `whole_cohort` yet
credited `lioness_panda.per_sample_networks` and `lioness_puma.per_sample_networks` (LIONESS contracts list an
aggregate output too), so the call lists them and the checked default line keeps "PANDA, LIONESS-PANDA" (GIRAFFE was
dropped as uncredited). The default-line fix follows the check; the check crediting a per-sample entry for a
`whole_cohort` result is the open question, outside these rounds. cd1's W01 run had credited no LIONESS entry.
