# A result per group is judged on each group's sample count, never on the total (2026-10-29, user "先修總樣本數")

## The gap (jev-guard, logged in per-group-base RESULTS.md)

A `per_group` row is one run per group, each on that group's samples, but the count checks (`data_issue`: a
workflow's minimum samples, COBRA's genes-vs-samples relation, a value cap) take the ask's `sample_count` as it is.
The four live per_group rows stated per-group numbers ("12 ... samples per stage", "20 animals per tissue"), so they
were right. A request stating only a total ("48 samples across 4 stages") would be judged on 48: a minimum passed
that a group may not reach (false accept), or a relation/cap failed that no group fails (false refusal, a reason
stated against the wrong number).

## Change (contract shape + code)

- The check's ask gains a typed `sample_count_in`: `each_group` (the stated number is each group's, condition's,
  stage's or time point's samples), `all_samples` (all the samples together), `not_stated` (no number, or the words do
  not say). Only on the ask, beside `scale`; the request-level conditions are unchanged.
- Code, for a `per_group` row whose count is not `each_group`: the count is not each group's, so it is not used as
  `samples` for the checks. Only what follows from a total holds: when the total is below a credited workflow's
  minimum, every group is too ("OTTER needs at least 2 samples in each group; the request has 1 sample in all"). A
  total at or above the minimum, and any relation or cap, are not judged (a count the request does not state is never
  judged -- `data_issue`'s rule). Every other scale, and `each_group`, are unchanged.

## Gates (declared before the code)

- **R1** unit tests: per_group + all_samples/not_stated total below the minimum -> refused with the per-group wording;
  at or above -> available, no limit; COBRA relation not judged on a total; per_group + each_group judged as before;
  per_sample / whole_cohort unchanged whatever the new field says.
- **R2** schema: the new field present on the ask only; enum-limit test passes.
- **R3** rebuild of the recorded pb1 X10, W20, X30, W30 readings (field absent -> `not_stated`): their per-group
  numbers are no longer judged, and each stays available on the same entry (none of them fails a minimum anyway);
  disclosed as a behaviour change for recordings without the field.
- **R4** flags-off harness replay: 0 changed calls (no recorded reading says per_group); clean-env tests: no new
  failures (module size included).
- **R5 live** (after the user agrees), turn 1, 1 rep, about US$0.03: four new prompts written for this round (not a
  sealed set) -- total only, enough ("one OTTER network per stage ... 48 samples across the 4 stages": DO OTTER, no
  count reason); total below a minimum (a DRAGON network per time point from 2 samples in all: refused, per-group
  wording); per-group stated (each_group, judged as before); a per-sample control with groups named -- plus pb1's
  X10, W20, X30, W30 again (per-group numbers: must stay DO on the same workflow). Hard: no control or kept item changes
  kind or workflow; no reason quotes a total as a group's size.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.
