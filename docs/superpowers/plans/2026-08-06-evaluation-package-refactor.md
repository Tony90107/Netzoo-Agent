# Evaluation Package Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 995-line `evaluation.py` module with a responsibility-oriented `evaluation/` package without changing any public interface or observable behaviour.

**Architecture:** `evaluation/__init__.py` remains the stable interface for callers and the legacy facade. Plan review delegates pure checks to `plan_rules`; step-result evaluation, bounded recovery, and response rendering live in independent sibling modules with no imports back through the package initializer.

**Tech Stack:** Python 3.10+, Pydantic 2, standard-library `unittest`/pytest, existing NetZoo contracts and runtime compatibility bridge.

## Global Constraints

- This is a structural refactor only; evaluation decisions and mutation semantics must not change.
- Preserve every name and order in the historical `evaluation.py.__all__` list.
- Preserve all user-visible strings byte-for-byte for identical inputs.
- Preserve both `netzoo_agent_core.evaluation` imports and the `netzoo_agent` legacy facade.
- Preserve runtime overrides for `EXECUTE_TOOLS` and `VERBOSE_OUTPUT` in the new child modules.
- Do not change contracts, workflow registry definitions, rubric criteria, rubric order, score calculation, or recovery authorization.
- Do not modify or commit unrelated working-tree changes.

---

## File Structure

| Path | Responsibility |
|---|---|
| `scripts/netzoo_agent_core/evaluation/__init__.py` | Stable package interface and historical re-exports only |
| `scripts/netzoo_agent_core/evaluation/plan_rules.py` | Pure evidence, path, bundle, and recovery-sequence rules |
| `scripts/netzoo_agent_core/evaluation/plan_review.py` | Pre-execution rubric orchestration and scoring |
| `scripts/netzoo_agent_core/evaluation/step_results.py` | Structured step-result state transition |
| `scripts/netzoo_agent_core/evaluation/recovery.py` | Allow-listed bounded PUMA repair mutation |
| `scripts/netzoo_agent_core/evaluation/rendering.py` | Plan, execution, missing-input, and preference response formatting |
| `tests/test_evaluation_package.py` | Package layout, public surface, facade, and runtime-override contract |

The package initializer is the only external seam. Internal modules may import
contracts and existing sibling modules, but must never import from
`netzoo_agent_core.evaluation` or `evaluation.__init__`.

---

### Task 1: Record the Behaviour Baseline and Add the Failing Package Contract

**Files:**

- Create: `tests/test_evaluation_package.py`
- Reference: `scripts/netzoo_agent_core/evaluation.py`

**Interfaces:**

- Consumes: historical `evaluation.py.__all__`, legacy `netzoo_agent` facade, and `set_runtime_value` propagation.
- Produces: a package-structure contract that Task 2 must satisfy.

- [ ] **Step 1: Run the focused existing tests before changing production code**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_agent_gate.py \
  tests/test_agent_stability.py \
  tests/test_graph_tracing.py \
  -k 'evaluator or evaluation or recovery or execution_response or successful_recovery' \
  -q
```

Expected: PASS. If a test already fails, save its exact node id and error so the
same failure can be distinguished from a refactor regression.

- [ ] **Step 2: Add the package and compatibility contract**

Create `tests/test_evaluation_package.py` with:

```python
from __future__ import annotations

import importlib
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.evaluation as evaluation  # noqa: E402


HISTORICAL_EXPORTS = [
    "_path_literal_in_task",
    "_evidence_contract_failures",
    "_path_hygiene_failures",
    "_expected_plan_steps",
    "evaluate_workflow_plan",
    "render_plan_evaluation",
    "render_plan_rejection_response",
    "render_verbose_execution_response",
    "_compact_field_label",
    "_extract_command_preview",
    "_compact_validation_highlights",
    "render_compact_execution_response",
    "render_execution_response",
    "render_needs_input_response",
    "render_preference_confirmation_response",
    "evaluate_step_result",
    "recover_workflow_plan",
]


def test_evaluation_is_responsibility_oriented_package():
    assert hasattr(evaluation, "__path__")
    for module_name in (
        "plan_rules",
        "plan_review",
        "step_results",
        "recovery",
        "rendering",
    ):
        importlib.import_module(f"netzoo_agent_core.evaluation.{module_name}")


def test_historical_evaluation_surface_is_preserved():
    assert evaluation.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(evaluation, name), name


def test_legacy_facade_uses_package_exports():
    for name in HISTORICAL_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(evaluation, name)


def test_runtime_overrides_reach_evaluation_child_modules():
    step_results = importlib.import_module(
        "netzoo_agent_core.evaluation.step_results"
    )
    rendering = importlib.import_module("netzoo_agent_core.evaluation.rendering")
    original_execute = legacy_agent.EXECUTE_TOOLS
    original_verbose = legacy_agent.VERBOSE_OUTPUT
    try:
        legacy_agent.EXECUTE_TOOLS = not original_execute
        legacy_agent.VERBOSE_OUTPUT = not original_verbose
        assert step_results.EXECUTE_TOOLS is (not original_execute)
        assert rendering.VERBOSE_OUTPUT is (not original_verbose)
    finally:
        legacy_agent.EXECUTE_TOOLS = original_execute
        legacy_agent.VERBOSE_OUTPUT = original_verbose
```

- [ ] **Step 3: Run the new test and verify the red state**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_evaluation_package.py -q
```

Expected: FAIL because `netzoo_agent_core.evaluation` is still a module and has
no `__path__` or child responsibility modules. The historical surface checks
should continue to pass.

---

### Task 2: Convert `evaluation.py` into the Responsibility-Oriented Package

**Files:**

- Delete: `scripts/netzoo_agent_core/evaluation.py`
- Create: `scripts/netzoo_agent_core/evaluation/__init__.py`
- Create: `scripts/netzoo_agent_core/evaluation/plan_rules.py`
- Create: `scripts/netzoo_agent_core/evaluation/plan_review.py`
- Create: `scripts/netzoo_agent_core/evaluation/step_results.py`
- Create: `scripts/netzoo_agent_core/evaluation/recovery.py`
- Create: `scripts/netzoo_agent_core/evaluation/rendering.py`
- Test: `tests/test_evaluation_package.py`
- Existing regression tests: `tests/test_agent_gate.py`

**Interfaces:**

- Consumes: `WorkflowPlan`, `TaskDecision`, `ToolExecutionResult`,
  `PlanEvaluationResult`, `EvaluationResult`, workflow-registry constants, and
  existing validation/policy/outcome helpers.
- Produces:
  - `evaluate_workflow_plan(plan: WorkflowPlan, user_task: str, project_policy: ProjectPolicySnapshot | dict | None = None) -> PlanEvaluationResult`
  - `evaluate_step_result(plan: WorkflowPlan, step_index: int, result: ToolExecutionResult | dict | str, replan_count: int = 0) -> EvaluationResult`
  - `recover_workflow_plan(plan: WorkflowPlan, step_index: int, evaluation: EvaluationResult) -> tuple[WorkflowPlan, int]`
  - all historical rendering and helper functions through `evaluation.__init__`.

- [ ] **Step 1: Create `plan_rules.py` by moving the five pure rule functions unchanged**

Move the complete current source block from `_path_literal_in_task` through the
end of `_expected_plan_steps` (`evaluation.py` lines 77–219 before this
refactor), without editing conditions, return values, or strings. The five
functions are `_path_literal_in_task`, `_evidence_contract_failures`,
`_path_hygiene_failures`, `_bundle_provenance_failures`, and
`_expected_plan_steps`.

Use only the imports those functions currently consume:

```python
from __future__ import annotations

import re

from ..contracts import (
    INPUT_ROLE_FIELDS,
    MAX_RECOVERY_ATTEMPTS,
    OUTPUT_ROLE_FIELDS,
    InputEvidence,
    TaskDecision,
    WorkflowPlan,
    _is_demo_request,
)
from ..bundles import MULTI_FILE_ACTIONS
from ..interpretation import _mentions_unspecified_data_directory
```

- [ ] **Step 2: Create `plan_review.py` and move pre-execution orchestration unchanged**

Move `evaluate_workflow_plan` exactly, including rubric append order, exception
handling, score calculation, and summaries. Import the five helpers from
`.plan_rules`. Preserve these external dependencies:

```python
import re

from workflow_registry import (
    CODE_VALIDATION_STEPS,
    LOCAL_EXECUTION_ACTIONS,
    REQUIRED_INPUTS,
    RUN_ACTIONS,
    workflow_name as _workflow_name,
)

from ..contracts import (
    INPUT_ROLE_FIELDS,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    PlanRubricItem,
    ProjectPolicySnapshot,
    TaskDecision,
    WorkflowPlan,
)
from ..path_safety import condor_artifact_paths, resolved_output_collisions
from ..policy import ProjectPolicyLoader
from ..routing import validate_task_text
from ..validation import _resolve_user_path
from .plan_rules import (
    _bundle_provenance_failures,
    _evidence_contract_failures,
    _expected_plan_steps,
    _path_hygiene_failures,
)
```

- [ ] **Step 3: Create `step_results.py` and move result-state evaluation unchanged**

Move only `evaluate_step_result`. Retain `EXECUTE_TOOLS` as a module global
import so the runtime compatibility bridge can update it:

```python
from ..contracts import (
    EXECUTE_TOOLS,
    EvaluationResult,
    MAX_RECOVERY_ATTEMPTS,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
)
from ..routing import structure_tool_result
```

- [ ] **Step 4: Create `recovery.py` and move bounded recovery unchanged**

Move only `recover_workflow_plan`, retaining `Path`, `InputEvidence`,
`EvaluationResult`, `MAX_RECOVERY_ATTEMPTS`, `TaskDecision`, `WorkflowPlan`, and
`WorkflowStep`. Do not extract mutation helpers: the complete allowed recovery
must remain readable in one file.

- [ ] **Step 5: Create `rendering.py` and move all rendering functions unchanged**

Move the contiguous rendering section from `render_plan_evaluation` through
`render_preference_confirmation_response`, including:

```python
render_plan_evaluation
render_plan_rejection_response
render_verbose_execution_response
_compact_field_label
_extract_command_preview
_compact_validation_highlights
render_compact_execution_response
render_execution_response
render_needs_input_response
render_preference_confirmation_response
```

Retain `VERBOSE_OUTPUT` as a module global import. Keep all regular expressions,
headings, whitespace, path checks, file-size checks, and calls to
`effective_results`, `terminal_failed`, `_resolve_user_path`, and `_ui_text`
unchanged.

Use the complete dependency set:

```python
import re

from ..contracts import (
    EvaluationResult,
    PlanEvaluationResult,
    ToolExecutionResult,
    VERBOSE_OUTPUT,
    WorkflowPlan,
    _ui_text,
)
from ..outcomes import effective_results, terminal_failed
from ..validation import _resolve_user_path
```

- [ ] **Step 6: Create the complete compatibility interface in `evaluation/__init__.py`**

Use this exact export order:

```python
"""Plan review, step evaluation, recovery, and response rendering."""

from .plan_rules import (
    _evidence_contract_failures,
    _expected_plan_steps,
    _path_hygiene_failures,
    _path_literal_in_task,
)
from .plan_review import evaluate_workflow_plan
from .recovery import recover_workflow_plan
from .rendering import (
    _compact_field_label,
    _compact_validation_highlights,
    _extract_command_preview,
    render_compact_execution_response,
    render_execution_response,
    render_needs_input_response,
    render_plan_evaluation,
    render_plan_rejection_response,
    render_preference_confirmation_response,
    render_verbose_execution_response,
)
from .step_results import evaluate_step_result

__all__ = [
    "_path_literal_in_task",
    "_evidence_contract_failures",
    "_path_hygiene_failures",
    "_expected_plan_steps",
    "evaluate_workflow_plan",
    "render_plan_evaluation",
    "render_plan_rejection_response",
    "render_verbose_execution_response",
    "_compact_field_label",
    "_extract_command_preview",
    "_compact_validation_highlights",
    "render_compact_execution_response",
    "render_execution_response",
    "render_needs_input_response",
    "render_preference_confirmation_response",
    "evaluate_step_result",
    "recover_workflow_plan",
]
```

Do not export `_bundle_provenance_failures`: it was not in the historical
`__all__` list.

- [ ] **Step 7: Run compilation and the package contract**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core/evaluation
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_evaluation_package.py -q
```

Expected: compilation succeeds and all four package tests PASS.

- [ ] **Step 8: Run focused behavioural regression tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_agent_gate.py \
  tests/test_agent_stability.py \
  tests/test_graph_tracing.py \
  -k 'evaluator or evaluation or recovery or execution_response or successful_recovery' \
  -q
```

Expected: the result matches Task 1's baseline with no new failures.

- [ ] **Step 9: Review the structural diff**

Run:

```bash
git diff --check
git diff --stat -- scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/evaluation tests/test_evaluation_package.py
git diff --color-moved=dimmed-zebra -- scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/evaluation
```

Confirm that function bodies are detected as moves, all historical strings and
conditionals remain unchanged, and only package imports/docstrings are new.

- [ ] **Step 10: Commit the atomic package conversion**

```bash
git add \
  scripts/netzoo_agent_core/evaluation.py \
  scripts/netzoo_agent_core/evaluation \
  tests/test_evaluation_package.py
git commit -m "refactor: split evaluation into focused package"
```

---

### Task 3: Verify Cross-Module Compatibility and Complete Regression

**Files:**

- Verify: `scripts/netzoo_agent_core/__init__.py`
- Verify: `scripts/netzoo_agent_core/graph.py`
- Verify: `scripts/netzoo_agent.py`
- Test: `tests/test_evaluation_package.py`
- Test: `tests/test_agent_gate.py`
- Test: `tests/test_agent_stability.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**

- Consumes: the stable exports produced by Task 2.
- Produces: evidence that all callers and the complete repository still operate
  through the unchanged interface.

- [ ] **Step 1: Verify callers need no source changes**

Run:

```bash
rg -n 'from \.evaluation|netzoo_agent_core\.evaluation' \
  scripts/netzoo_agent_core scripts/netzoo_agent.py tests
```

Expected: existing imports continue to target `.evaluation`; callers do not
import `plan_review`, `plan_rules`, `step_results`, `recovery`, or `rendering`.
Only `tests/test_evaluation_package.py` may intentionally name child modules.

- [ ] **Step 2: Run the package, facade, stability, and tracing tests together**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_evaluation_package.py \
  tests/test_agent_stability.py \
  tests/test_graph_tracing.py \
  tests/test_agent_gate.py \
  -q
```

Expected: PASS with no new failure relative to the pre-refactor baseline.

- [ ] **Step 3: Run the complete test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Expected: PASS. If the recorded baseline contained an unrelated failure, the
same node may remain failing only if its traceback and assertion are unchanged;
document that exception explicitly.

- [ ] **Step 4: Verify final module sizes and repository state**

Run:

```bash
wc -l scripts/netzoo_agent_core/evaluation/*.py
git status --short
```

Expected: no implementation file approaches the original 995-line size;
`__init__.py` contains only imports and `__all__`; unrelated pre-existing working
tree changes remain untouched.

- [ ] **Step 5: Commit only if verification required a scoped correction**

If no correction was needed, do not create an empty commit. If a correction was
required, rerun Steps 2–4, then stage only evaluation-package paths and their
test:

```bash
git add scripts/netzoo_agent_core/evaluation tests/test_evaluation_package.py
git commit -m "test: preserve evaluation package compatibility"
```
