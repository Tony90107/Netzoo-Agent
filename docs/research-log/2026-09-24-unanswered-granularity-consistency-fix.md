# 2026-09-24 unanswered granularity consistency repair

## Scope

This repair follows up the `gran-mirna-unstated-control` gap recorded in the
live semantic contract A/B. It uses the saved claims trace and a deterministic
replay of its accepted hypotheses through the current matcher, decision
assembly, and evaluator. No live provider or workflow was called.

## Root cause and reproduction

The saved prompt says the user has not decided between one cohort network and
separate per-patient networks, and asks the agent to clarify. Its accepted
claims hypotheses had granularities `[unknown, sample_specific]`. The matcher
returned `ambiguous`, held `run_puma` and `run_lioness_puma`, and asked:

> Should the result be aggregate or sample-specific?

`assemble_task_decision` projected a primary hypothesis using
`select_primary_hypothesis`. That selector ranked hypotheses by evidence count
and confidence; explicit evidence counted two points and inferred evidence one.
The sample-specific hypothesis had one extra inferred granularity item, so it
ranked above the otherwise stronger-confidence unknown hypothesis. Assembly
therefore wrote `requested_outcome.granularity=sample_specific` while retaining
the clarification question.

The evaluator passed the saved result because the corpus intentionally leaves
`expected.granularity` unset for this case. `_score` compared only dimensions
whose expected value was non-null, so it did not check whether an open
granularity choice remained unknown.

## Repair

- Primary-outcome selection now receives the user request. If a bounded
  granularity witness says the user has left that choice open, the projected
  primary outcome keeps its other strongest fields but changes any selected
  `aggregate` or `sample_specific` value to `unknown`, adds the unresolved
  dimension, and removes evidence that supported only the suppressed choice.
  Equal-ranked alternatives with the same other outcome fields also project to
  unknown instead of disappearing as a tie.
- Decision assembly, raw-router hydration, and compatibility repair use this
  task-aware projection. The original hypotheses remain available for candidate
  matching and audit.
- The evaluator now reports
  `clarification_consistency` when a case requires clarification, its prompt
  leaves granularity open, and the structured requested outcome does not say
  `unknown`.

This does not infer that aggregate is the user's choice. The saved hypotheses
still contain `[unknown, sample_specific]` rather than an explicit aggregate
hypothesis; candidate matching continues to expose PUMA and LIONESS-PUMA as the
two registry-compatible options.

## Verification

- The two initial regression tests failed before the repair and pass after it:
  - assembly preserves unknown granularity while asking the choice;
  - evaluator rejects a sample-specific requested outcome while the question is
    still open.
- A third regression added for tied aggregate/sample-specific candidates passes;
  it verifies the projected outcome stays unknown and both hypotheses remain
  intact.
- Replaying the saved accepted hypotheses through the current matcher and
  assembly preserves the ambiguous route and clarification, projects
  `requested_outcome.granularity=unknown`, and passes the evaluator.
- Scoring the historical saved decision with the updated evaluator now fails
  with `clarification_consistency: requested_outcome.granularity must remain
  unknown until the user answers, got sample_specific`.
- The focused baseline suite in
  `test_clarification_planner.py`, `test_concept_answers.py`, and
  `test_guidance_consistency.py` passed **66/66**.
- The broader focused command across outcome routing, evaluator, validation,
  repair interaction, and those baseline files reported **246 passed, 2 failed**.
  The failures are existing assertions outside this repair path:
  `test_language_variations_preserve_the_router_selected_network_action` and
  `test_measurement_metadata_is_retained_without_reselecting_action`. Both
  concern advice/tool-selection wording or measurement routing; their prompts do
  not trigger the open-granularity witness. They were left untouched.
- Ruff and `py_compile` passed for the modified Python files. Pytest reported
  one existing `pytz` deprecation warning.

The 66-test baseline and broader focused suite are separate test sets; their
denominators are not combined. Neither number measures raw-prompt live model
accuracy.

## Limits

This verifies one saved claims trial and deterministic downstream behavior; it
does not establish how a live model will phrase future hypotheses. No provider
calls were made. The hypotheses still lack an explicit aggregate alternative,
which remains a semantic-completeness limitation for the model proposal. Claims
has not been promoted to production default. The unrelated `prompt_seq` desktop
protocol issue is outside this repair.
