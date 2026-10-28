# The scale question is not asked when the check read the scale (2026-10-28, user: "先修多問的問題")

## Trace

cd1 W01: the reply ends "Should the result be aggregate or sample-specific?" Routing writes this question when its
reading leaves the granularity open (here `unknown`, granularity-unknown-2026-10-28); it runs before the capability
check. The check read both asked results with `scale: whole_cohort` and credited only aggregate workflows (PANDA,
PUMA, OTTER, GIRAFFE), and the call was DO on them -- the question contradicts the turn's own decision.

All recorded replies with the question (38, `survey.py`): the check had read a scale on every credited result in 20
(per_sample 13, e.g. "a BONOBO co-expression network for each of our 25 pancreatic islet donors"; whole_cohort 7),
`unstated` in 12 (e.g. "help me see how genes are connected"), and credited nothing in 6.

## Change

After the check is attached (beside `with_checked_default_line`): when every result the check credited has a stated
scale (`per_sample` or `whole_cohort`), the routing sentence "Should the result be aggregate or sample-specific?" is
removed from the clarification question (the question is cleared when nothing else is left). Unchanged when any
credited result's scale is `unstated`, or the check credited no result.

## Gates (declared before the code)

- **S1** recorded replies (`survey.py`): the question is removed exactly in the turns whose credited results all have
  a stated scale (20), kept in the 12 `unstated` and the 6 with nothing credited.
- **S2** unit tests: removed when all stated; kept when one is unstated or none credited; other sentences kept.
- **S3** clean-env tests: no new failures; flags-off replay 0 of 1388.
- Live only after the user agrees: W01 and the "25 pancreatic islet donors" BONOBO request, turn 1 (no scale
  question), plus the sorghum request (unstated; the question stays); about US$0.03.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Live addendum (declared after the offline pass, before any run)

`run_live.py` (tag cs1): W01, Q06 (targets), C53 (control), turn 1, cap US$0.05.
- **T1** neither W01 nor Q06 ends with the scale question.
- Reported: C53's reply (its scale is unstated, so the question may stay).
