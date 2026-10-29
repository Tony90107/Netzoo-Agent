# A result per group is a scale of its own, credited to aggregate workflows (2026-10-29, "照你的做")

## Trace (j6 X30, gold DO OTTER; ended DECLINE full_gap)

"With OTTER, I want one TF-to-gene network per stage, each built from all 12 samples of that stage." The check's
reading typed `scale: per_sample` -- its only options are per_sample, whole_cohort, unstated, none of which is "one
aggregate result for each group". `_fitting` then kept only entries with sample_specific granularity, which OTTER
has not, so the row was not available and the turn a full gap ("I couldn't match this ...").

## Change (contract shape)

The check schema's `scale` gains `per_group`: "one result for each group, condition, stage or time point, built from
all that group's samples together". `_fitting` reads it as aggregate (each group's result is an aggregate result);
the checked scale question treats it as stated. No other code reads the value.

Also (jev-guard's request on settled-answers, test only): when a bound form answer itself rules a workflow out
(several_groups for CONDOR), the refusal still comes from `answered_check`, not lost by skipping the condition check.

## Gates (declared before the code)

- **P1** unit tests: a per_group ask credited to OTTER stays available; per_sample still rules OTTER out; whole_cohort
  unchanged; the settled-answers opposite-direction test.
- **P2** enum count of the check schema still under the limit or compacted as today.
- **P3** flags-off harness replay: 0 right -> wrong (recorded readings never say per_group); clean-env tests no new
  failures.
- **P4 live** (after the user agrees), turn 1: targets j6 X30, X10 and j5 W20, W30 (one result per group; gold DO);
  controls j6 X14, j5 W13, W35 (one result per sample; must stay per-sample, gold DO). Hard: no control credited only
  aggregate workflows. About US$0.05.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.
