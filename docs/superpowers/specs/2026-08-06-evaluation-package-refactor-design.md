# Evaluation Package Refactor Design

**Date:** 2026-08-06

## Objective

Refactor `scripts/netzoo_agent_core/evaluation.py` from a 995-line module with
multiple responsibilities into a clearly structured `evaluation/` package. This
is a structural refactor only: public imports, decisions, output text, recovery
behaviour, runtime overrides, and data models must remain unchanged.

## Scope

This phase covers only `scripts/netzoo_agent_core/evaluation.py` and the tests
needed to prove its package structure and backward compatibility. Other large
modules in `netzoo_agent_core` are outside this phase, except for minimal import
adjustments if package conversion requires them.

The refactor must preserve both supported import paths:

```python
from netzoo_agent_core.evaluation import evaluate_workflow_plan
import netzoo_agent as agent
```

Existing callers must not need to know which internal file implements a public
function.

## Chosen Approach

Replace `evaluation.py` with an `evaluation/` package. The package initializer is
the stable external seam and re-exports the complete historical `__all__`
surface. Internal modules are grouped by business responsibility rather than by
line count.

```text
scripts/netzoo_agent_core/
└── evaluation/
    ├── __init__.py
    ├── plan_review.py
    ├── plan_rules.py
    ├── step_results.py
    ├── recovery.py
    └── rendering.py
```

### `evaluation/__init__.py`

Provides the package interface. It re-exports every name currently listed in
`evaluation.py.__all__`, including historically exported underscore-prefixed
helpers. It contains no evaluation policy or rendering implementation.

### `evaluation/plan_review.py`

Owns `evaluate_workflow_plan`. It validates the plan decision, assembles rubric
items in the existing order, calculates the score, and returns the typed
`PlanEvaluationResult`. It delegates focused pure checks to `plan_rules` but
continues to own the overall review flow.

### `evaluation/plan_rules.py`

Owns the pure plan-review helpers:

- `_path_literal_in_task`
- `_evidence_contract_failures`
- `_path_hygiene_failures`
- `_bundle_provenance_failures`
- `_expected_plan_steps`

These rules remain internal implementation details even though the package
initializer preserves any historical exports for compatibility.

### `evaluation/step_results.py`

Owns `evaluate_step_result`. It converts legacy string results when necessary
and returns the existing `continue`, `completed`, `failed`, or `replan` result.

### `evaluation/recovery.py`

Owns `recover_workflow_plan`. It applies only the existing allow-listed,
bounded `format_expression_headerless` PUMA recovery and preserves all current
plan mutation semantics.

### `evaluation/rendering.py`

Owns plan-review rendering, rejection responses, compact and verbose execution
responses, missing-input responses, preference confirmation responses, and
their rendering helpers. Moving these functions together keeps all
user-visible formatting changes local.

## Interfaces and Dependency Direction

The external dependency direction is:

```text
callers → evaluation/__init__.py → responsibility modules
                                plan_review → plan_rules
```

The internal responsibility modules may import contracts and existing sibling
modules such as `outcomes`, `routing`, `validation`, `policy`, `bundles`, and
`path_safety`. They must not import `evaluation/__init__.py`, preventing circular
dependencies.

No new abstract base classes, adapters, or dependency-injection framework will
be introduced. Evaluation is predominantly in-process computation, so direct
function interfaces remain the deepest and clearest seam.

Runtime settings imported by the new modules, including `EXECUTE_TOOLS` and
`VERBOSE_OUTPUT`, must remain discoverable by the existing runtime compatibility
bridge. The bridge already updates loaded `netzoo_agent_core.*` modules, so the
tests must prove it also updates the new package children.

## Behaviour Preservation

The following observable behaviour is invariant:

- A plan whose status is not `ready` returns a deferred plan evaluation.
- An invalid decision schema returns a rejected plan evaluation without leaking
  the validation exception.
- Rubric criteria, order, required flags, results, details, scoring, and summary
  text remain unchanged.
- Project-policy validation and policy-hash binding remain unchanged.
- Step evaluation retains legacy string conversion and structured-result
  handling.
- Retryability, recovery hints, `MAX_RECOVERY_ATTEMPTS`, and `EXECUTE_TOOLS`
  continue to control replanning exactly as before.
- Recovery remains limited to the current headerless-expression PUMA repair and
  mutates the same decision, evidence, steps, and recovery metadata.
- Compact and verbose reports remain byte-for-byte compatible for the same
  inputs, including headings, warnings, errors, command previews, paths, file
  sizes, and next-step text.
- Missing-input and preference-confirmation responses remain unchanged.
- `VERBOSE_OUTPUT` continues to select the default renderer when the explicit
  `verbose` argument is absent.

The refactor will not add broad exception handling. Exceptions that currently
surface to callers must continue to surface; only the existing deliberately
handled validation failures remain handled.

## Testing and Verification

Before changing the module, run the evaluation-related existing tests to record
the baseline. Any existing failure must be distinguished from a regression
introduced by this refactor.

Add a focused compatibility test that verifies:

- `netzoo_agent_core.evaluation` is a package;
- every historical `__all__` name is available;
- the legacy `netzoo_agent` facade resolves the same public functions;
- updates to `EXECUTE_TOOLS` and `VERBOSE_OUTPUT` reach the responsibility
  modules that consume them.

Run existing tests covering plan evaluation, result evaluation, recovery,
rendering, graph tracing, agent stability, and the legacy facade. Then run the
complete test suite and Python compilation checks.

Review the final diff to confirm that implementation changes are moves and
import adjustments only, with no accidental changes to strings, conditionals,
rubric order, or mutation behaviour.

## Acceptance Criteria

The refactor is complete when:

1. `evaluation.py` has been replaced by the documented `evaluation/` package.
2. Each implementation file has one clear responsibility and no unnecessary
   pass-through abstraction.
3. Existing public and legacy imports work without caller changes.
4. Evaluation rules, recovery behaviour, runtime overrides, and rendered output
   are unchanged.
5. Focused compatibility tests pass.
6. Existing relevant tests pass.
7. The complete test suite has no new failures.
8. All new modules compile and import successfully.

## Out of Scope

- Redesigning evaluation policy or rubric criteria.
- Changing user-visible output.
- Changing contracts or workflow registry definitions.
- Refactoring other large `netzoo_agent_core` modules.
- Adding new recovery actions or execution capabilities.
