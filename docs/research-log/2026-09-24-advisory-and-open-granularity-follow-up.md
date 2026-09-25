# 2026-09-24 advisory routing and open-granularity follow-up

## Scope

This follow-up uses the user-supplied tumour RNA / TF-to-gene wiring question
as an offline regression and replays the saved
`live-semantic-trace-2026-09-24-next-step-claims.json`. It does not call a live
provider, run a workflow, or change the production semantic-contract default.
The separate `prompt_seq` issue remains out of scope.

## Reproduction and root cause

The supplied question asks which method to use and ends with “Just advise.” It
states that TF-to-gene wiring differs between patients and that each patient
should have an individual picture. Before this follow-up, the bounded
granularity witnesses did not recognize that wording because they required a
per-patient network phrase. The unknown request mode also stayed unknown, and
local repair trusted a raw router choice of `run_lioness_panda`; the replay
therefore set `should_execute=true` for an advice-only question.

The saved `gran-mirna-unstated-control` claims trace has a second, distinct gap.
Its accepted hypotheses were `[unknown, sample_specific]`, while the user had
explicitly left a choice between one cohort network and per-patient networks.
The matcher asked which granularity the user wanted, but a downstream rematch
could still promote the sample-specific workflow from the selected hypothesis.
The accepted claims also lacked an explicit aggregate hypothesis, so the
candidate set did not preserve both grounded alternatives. The previous
consistency repair made the assembled primary outcome unknown; this follow-up
completes the candidate set when safe and guards the later rematch as well.

## Changes

- The granularity witness recognizes network wiring, edges, or links that differ
  from one patient/sample to the next, while a negative control about gene
  expression differences alone does not imply separate networks.
- An otherwise unknown request mode becomes `guidance` for an explicit workflow
  selection or advice request. A direct execution request still takes
  precedence.
- Router repair converts a selected local workflow to `no_tool` when the user
  asks for workflow information or advice without authorizing execution. This
  gate applies only to local workflows; documentation retrieval remains
  available.
- For a request that explicitly leaves granularity undecided, the claims path
  expands a compatible unknown/sample-specific hypothesis set into grounded
  aggregate and sample-specific candidates. It only does so when all
  non-granularity outcome fields and assumptions agree and both alternatives
  have literal spans in the request. Other shapes remain unchanged for
  validation and review.
- If downstream matching would otherwise make an exact/fallback choice while
  granularity remains explicitly open, matching rechecks with granularity
  withheld and preserves a clarification when distinct workflows remain.
- The evaluator now checks both that the projected `requested_outcome` stays
  `unknown` while clarification is pending and that both explicit alternatives
  remain represented in `outcome_hypotheses`.

## Offline replay result

For the supplied advice-only question, deterministic restoration identifies
`sample_specific`; capability matching identifies `run_lioness_panda`; its
aggregate dependency remains visible in the recommendation chain. The
structured action is `no_tool`, `should_execute=false`, and no clarification is
asked because the user already specified per-patient output.

For the saved undecided-granularity trace, the current claims path produces
`[aggregate, sample_specific]`, with explicit grounded evidence for both. The
semantic matcher remains ambiguous between `run_puma` and
`run_lioness_puma`, asks “Should the result be aggregate or sample-specific?”,
and decision assembly projects `requested_outcome.granularity=unknown`.
Scoring the historical inconsistent decision with the current evaluator now
reports the clarification-consistency error and reports a missing aggregate
hypothesis when that alternative is absent.

## Verification

- Four direct offline regressions passed: advice-only execution blocking,
  grounded completion of both open alternatives, evaluator rejection of a
  missing alternative, and claims-interpreter integration.
- The focused routing, evaluator, validation, repair, clarification, concept,
  and guidance suite passed **230 tests**. The previously reported
  clarification/concept/guidance subset passed **66 tests**; these are
  overlapping sets and their counts are not combined.
- Granularity witness checks passed **13 tests**. The selected witness and
  evaluator checks are also included in the broader focused counts above; do
  not add these denominators together.
- The final supplemental mixed run over ten test files reported **360 passed
  and 7 failed**. The former request-mode assertion was changed to test the new
  deterministic `guidance` behavior. Remaining failures concern sample entity
  preservation, full input-list restoration, aggregate evidence restoration,
  illegal artifact roles, an unmatched quote span, claim-repair feedback shape,
  and the unavailable optional `langchain_openai` dependency. They do not
  isolate the advice-only or open-granularity regressions fixed here. Since the
  shared worktree contains pre-existing changes, this run cannot establish a
  clean baseline or attribute those failures to a particular session.
- `compileall` and `git diff --check` passed. Pytest reports one existing
  `pytz` deprecation warning.

The test groups overlap, so their denominators are intentionally reported
separately. These deterministic tests and saved-trace replay do not measure raw
prompt live-model accuracy.

## Limits

The advice example is verified through deterministic interpretation and route
repair, not a new live model response. Literal witnesses remain bounded
language checks rather than a general natural-language parser. Alternative
completion fails closed when hypotheses disagree outside granularity or do not
share assumptions. Claims remains experimental and has not been made the
production default. No live provider calls or workflow executions were made.
