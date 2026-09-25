# 2026-09-24 sample-specific guidance presentation follow-up

## Scope

This follow-up investigates the user's latest CLI transcript for a
patient-specific TF-to-gene network recommendation. It is an offline repair of
the deterministic guidance and progress surfaces. No provider was called and no
workflow was executed.

## Reproduction and root cause

The routing regression for the exact prompt already selected
`run_lioness_panda` as the single matched capability, with
`[run_panda, run_lioness_panda]` in `recommended_actions` because the registry
records PANDA as LIONESS-PANDA's guidance predecessor. The old
`render_workflow_composition_guidance` treated that ordered dependency chain as
two peer recommendations and hard-coded the same answer shown in the user's
transcript. The progress renderer also exposed the internal path as
`PANDA → LIONESS-PANDA`, which could imply that PANDA must be run separately.

There was a second reason the preceding repair did not appear in the user's
working copy: making the worktree clean had stashed all changes, including the
semantic-routing fix. This follow-up reapplied that stash without dropping it,
then reproduced the still-confusing answer from the renderer. A failing offline
regression asserted the desired sample-specific answer while the renderer
returned the exact old aggregate-plus-sample-specific introduction.

## Changes

- When the verified requested outcome is `sample_specific` and the selected
  final workflow supports both aggregate and sample-specific network outputs,
  guidance now leads with that final workflow, lists its inputs and outputs,
  and says that a separate aggregate workflow run is unnecessary. It no longer
  presents the predecessor as a second recommendation.
- Classification progress retains the registry-derived workflow path for
  routing data, and adds `display_workflow` for the one exact matched
  sample-specific workflow. The CLI uses this display value, so the progress
  line shows `LIONESS-PANDA` rather than the PANDA predecessor chain.
- The end-to-end response regression uses the user's TF/PANDA prompt and checks
  the single recommendation, both registered outputs, and the no-analysis
  statement. Generic composition guidance without a resolved sample-specific
  outcome keeps its existing presentation.

## Verification

- The new response-renderer regression failed before the fix with the same
  “aggregate and sample-specific workflow” text shown in the supplied
  transcript.
- The focused suite covering concept answers, graph responses, outcome
  routing, progress summaries, and CLI presentation passed **193 tests**.
- Ruff, `compileall`, and `git diff --check` passed. Pytest emitted one existing
  `pytz` deprecation warning.
- No live provider or workflow execution was used. The local provider/model
  accuracy of future prompts was not measured.

## Limits

The concise renderer requires a validated sample-specific requested outcome and
registered aggregate plus sample-specific outputs. If granularity remains
unknown, the response must continue to ask for clarification or use the generic
composition guidance. Registry-derived dependency metadata remains available
for routing and audit even when the user-facing progress label shows only the
selected final workflow. Claims remains experimental and is not the production
default.
