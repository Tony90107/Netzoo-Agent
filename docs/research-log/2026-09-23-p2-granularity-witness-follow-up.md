# P2 output-granularity witness follow-up

Date: 2026-09-23

## Finding

The saved round-6 traces showed claims outcomes for `role-tf-ss-en` repeatedly
choosing `regulatory_network_and_tf_activity` and then losing the requested
sample-specific granularity. `gran-tf-ss-individual-en` also had unstable
granularity. The current request witness did not recognize either “separately
in each patient” or “for each individual ... their own ... network”.

The old bare `per-patient` / `per-sample` expressions could also label an input
matrix as a sample-specific output when both appeared in one clause.

## Change

Updated `_GRANULARITY_PATTERNS` in
`scripts/netzoo_agent_core/interpretation/request_integrity.py`:

- Bind per-unit and `sample-specific` phrases to a nearby network noun.
- Recognize “their own network”, an output estimated “separately in each
  patient”, and a network estimated for each unit even when modifiers separate
  the words.
- Recognize the explicit aggregate forms “one network for the whole cohort”
  and “cohort-level”.
- Cover the common Chinese phrasing “每一位病人”.

These witnesses are included in claims `request_facts.granularity` and used by
legacy stated-field restoration. No provider prompt wording was changed, and
artifact-constraint alignment was not enabled.

## Offline audit

Fresh positive phrasings all yielded `sample_specific`, including:

- “Estimate a TF-to-gene network separately in each patient.”
- “For each individual in my study I want their own transcription-factor-to-
  gene regulatory network.”
- “Build an individual TF-to-gene regulatory network for each sample.”

Negative controls mentioning per-patient/per-sample expression matrices while
requesting one shared cohort network yielded only `aggregate`. A historical
per-patient network followed by a current cohort-wide request also yielded only
the current `aggregate` witness.

Across the 32 family cases, 8 variants, and 39 main scenarios, the audit found
zero explicit-witness contradictions with expected aggregate or
sample-specific granularity. Expected sample-specific prompts without a
sample-specific witness: 0/32 family cases, 0/8 variants, and 1/39 main
scenarios. The remaining prompt is the deliberately misspelled
`mirna-current-goal-misspelled`; its typo-heavy unit and output wording is not
covered by this closed-vocabulary witness, and it did not produce a contrary
witness.

Static checks passed: Python compilation, Ruff on the edited module, and
`git diff --check`. This round did not run the routing test suite or a live
provider round. The environment's `OPENROUTER_API_KEY` was unavailable during
the preceding live-validation attempt, so these results establish witness
coverage only, not that the stochastic route now passes live.

## Compact miRNA role witness follow-up

Date: 2026-09-24

The Round-6 claims trace for `role-mir-abbrev-terse` exposed a missed closed
role witness: `miR->gene`. Granularity extraction already read `per-sample`,
but role extraction required the full `miRNA` spelling and did not accept the
ASCII arrow. The semantic proposal also invented TF-activity and expression
inputs despite neither being named in the request.

The role witness now accepts `miR` and `->`. Replaying each of the three saved
claims proposals through current restoration, validation, and registry matching
removes both unsupported inputs, restores the witnessed miRNA-to-gene roles,
passes semantic validation, and yields exact `run_lioness_puma` in 3/3 trials.
The input-removal behavior predated this syntax fix; the role witness was the
missing piece that allowed the matcher to resolve the exact route.

This is a deterministic replay of recorded provider outputs, not a new live
round or a fresh result for the other Round-6 prompts. Compilation, Ruff, and
`git diff --check` passed.
