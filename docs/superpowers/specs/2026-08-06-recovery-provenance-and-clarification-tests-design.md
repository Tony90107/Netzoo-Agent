# Recovery Provenance and Clarification Test Repair Design

## Goal

Restore a fully green test suite without weakening coherent dataset discovery or
the pre-execution evidence contract. The repair must distinguish a file created
by an allow-listed recovery step from a file autonomously discovered in an
existing dataset bundle, and clarification tests must not depend on incidental
workspace datasets.

## Confirmed Root Causes

Three clarification tests construct a PANDA request anchored to
`data/lioness-toy`. That directory now forms a complete, validated coherent
bundle, so the planner correctly fills the expression and PPI inputs and returns
a ready plan. The tests still expect those inputs to remain missing and therefore
exercise clarification functions with an invalid fixture.

The recovery failure is a product contract mismatch. `recover_workflow_plan()`
creates a new headerless expression file but marks its evidence as `discovered`.
For multi-file workflows, discovered inputs must identify one coherent dataset
bundle. The generated recovery artifact has no bundle identifier, so the same
evaluator that approves the original plan rejects the otherwise allow-listed
recovery plan.

## Decisions

### Preserve coherent-bundle autofill

When an explicit input anchors a request to a directory containing one complete,
validated dataset bundle, the planner will continue filling the remaining inputs
atomically. The repair will not restore redundant clarification prompts or make
dataset selection depend on test expectations.

### Isolate clarification fixtures

Clarification tests will create a `WorkflowPlan` whose evidence explicitly marks
the expression and PPI fields as missing and supplies deterministic candidate
lists. The fixture will retain the original PANDA decision and candidate values
needed to test wizard ordering, continuation markers, router repair, and selected
provenance after replanning. It will not call workspace discovery to establish
its precondition.

### Represent recovery outputs as derived evidence

`InputEvidence.status` will add `derived`. This status means an input was created
by a code-authorized transformation during bounded recovery. It is distinct from:

- `provided` and `selected`, which require direct user grounding;
- `discovered` and `demo_bundle`, which identify existing workspace data; and
- `defaulted`, which is limited to reversible output roles.

`recover_workflow_plan()` will set the recovered expression evidence to
`derived`, clear obsolete candidates and bundle identity, and retain the current
human-readable recovery reason.

## Evidence Validation

A derived evidence entry is valid only when all of these conditions hold:

1. The plan declares `recovery_action="format_expression_headerless"`.
2. The recovered workflow action is `run_puma`.
3. The evidence field is `expression_file` and has a non-empty value and reason.
4. Its value exactly matches the decision's current expression path.
5. The plan contains the allow-listed `format_expression` step at the recorded
   recovery position.
6. That step's `output_file` exactly matches the derived evidence value.
7. The derived evidence has no bundle identifier and no stale selection
   candidates.

The historical `_evidence_contract_failures(evidence, user_task)` signature will
remain unchanged. It will enforce the context-free shape of derived evidence,
while a new private validator receives the plan and decision context needed for
the recovery-specific rules. `evaluate_workflow_plan()` will combine both
results under the existing evidence-provenance rubric. Invalid or fabricated
derived evidence will reject the plan. Dataset bundle validation will continue
examining only genuinely discovered inputs, so a valid derived artifact neither
needs a synthetic bundle identifier nor conflicts with the source dataset's
bundle identity.

## Rendering

Plan rendering will label `derived` evidence as `derived input`. Existing labels,
public function signatures, decision strings, and bundle behavior remain
unchanged.

## Test Strategy

The implementation will proceed test-first:

1. Preserve the three existing failures as the red baseline, then convert their
   setup to an isolated helper and confirm the original interaction assertions
   pass without changing planner behavior.
2. Add recovery-contract tests that require `derived` evidence, approve a valid
   allow-listed recovery, and reject fabricated or mismatched derived evidence.
3. Update rendering coverage for the new label.
4. Run the focused clarification, recovery, evaluation, planning, and dataset
   bundle suites.
5. Run the complete `pytest -q` suite and require zero failures.
6. Re-run `finishing-a-development-branch` only after the full suite is green.

## Scope and Compatibility

The change is limited to evidence vocabulary, recovery provenance validation,
rendering, and stale test setup. It does not change candidate scoring, coherent
bundle selection, user-path parsing, recovery step ordering, tool authority,
execution behavior, or public legacy facade exports. Unrelated dirty worktree
files will not be modified, staged, or committed.
