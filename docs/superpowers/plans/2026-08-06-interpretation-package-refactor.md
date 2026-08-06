# Interpretation Package Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 958-line interpretation module with a responsibility-oriented package while preserving every public interface, deterministic decision, fallback, validation, exception, and legacy patch behavior.

**Architecture:** First characterize the current module and mechanically move it behind a package facade as `core.py`. Then extract deterministic text parsing, hydration, repair, provider fallback, and discovery into internal child modules. The package facade remains the only external seam and the legacy facade registers every implementation owner.

**Tech Stack:** Python 3.12, Pydantic models, pytest, standard-library `inspect`, `ast`, `importlib`, `pathlib`, and the existing NetZoo agent contracts and validators.

## Global Constraints

- This is a pure structural refactor; do not fix, consolidate, reorder, or reinterpret existing logic.
- Preserve the exact `interpretation.__all__` contents and order.
- Preserve every public function name, parameter list, default, annotation, return shape, mutation, error, and reason string.
- Preserve every regular expression, candidate score, 15-point ambiguity threshold, confidence value, and decision priority.
- Preserve `PREVIOUS_ACTION` continuation authority over router reclassification.
- Preserve coherent dataset-bundle validation and completed-episode reuse constraints.
- Preserve fatal handling for `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`.
- Add no broad exception handling, logging, trace events, warnings, or execution authority.
- Preserve assignment-based monkeypatch propagation through `scripts/netzoo_agent.py`.
- Keep `scripts/netzoo_agent.py` at or below 150 lines.
- Keep every final interpretation child module below its specified responsibility-size limit.
- Do not modify, stage, or commit unrelated working-tree changes.
- The accepted clean baseline is 270 passed, 12 skipped, and four deselected known failures.
- The accepted unfiltered baseline is 270 passed, 12 skipped, and the same four documented failures.

## File Map

| Path | Final responsibility |
| --- | --- |
| `scripts/netzoo_agent_core/interpretation/__init__.py` | Exact public facade and private compatibility tuple. |
| `scripts/netzoo_agent_core/interpretation/extraction.py` | Task paths, data-directory intent, LIONESS mode, documentation intent, and explicit preferences. |
| `scripts/netzoo_agent_core/interpretation/hydration.py` | Router result hydration into `TaskDecision`. |
| `scripts/netzoo_agent_core/interpretation/repair.py` | Router decision repair and LIONESS mode plan. |
| `scripts/netzoo_agent_core/interpretation/provider_fallback.py` | Fatal-error classification and deterministic provider fallback. |
| `scripts/netzoo_agent_core/interpretation/discovery.py` | Candidate selection, coherent demo bundles, and reusable episode inputs. |
| `scripts/netzoo_agent_core/interpretation.py` | Removed after mechanical package conversion. |
| `scripts/netzoo_agent_core/interpretation/core.py` | Temporary mechanical home; removed after all extractions. |
| `scripts/netzoo_agent.py` | Expand the interpretation implementation-module tuple. |
| `tests/test_interpretation_package.py` | Public contract, package structure, compatibility, privacy, size, and dependency tests. |

---

### Task 1: Characterize the Public Interpretation Contract

**Files:**
- Create: `tests/test_interpretation_package.py`
- Reference: `scripts/netzoo_agent_core/interpretation.py`

**Interfaces:**
- Consumes: the current module and legacy facade.
- Produces: exact exports, signatures, facade identities, and fatal-exception guardrails.

- [ ] **Step 1: Add public-contract characterization tests**

Create `tests/test_interpretation_package.py` with:

```python
from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.interpretation as interpretation  # noqa: E402


PUBLIC_EXPORTS = [
    "INPUT_LABELS",
    "_candidate_keywords",
    "_choose_unambiguous_candidate",
    "_task_path",
    "_mentions_unspecified_data_directory",
    "_needs_lioness_mode_choice",
    "is_versioned_documentation_request",
    "documentation_library_for_task",
    "extract_preference_proposals",
    "hydrate_router_decision",
    "_lioness_mode_plan",
    "repair_router_decision",
    "deterministic_router_fallback",
    "_is_fatal_exception",
    "_best_named_file",
    "discover_demo_bundle",
    "reusable_episode_inputs",
]

PUBLIC_SIGNATURES = {
    "_candidate_keywords": "(action: 'str', field_name: 'str') -> 'tuple[str, ...]'",
    "_choose_unambiguous_candidate": "(candidates: 'list[str]', keywords: 'tuple[str, ...]', nearby: 'Path') -> 'tuple[str | None, str]'",
    "_task_path": "(task: 'str', field_name: 'str') -> 'str | None'",
    "_mentions_unspecified_data_directory": "(task: 'str') -> 'bool'",
    "_needs_lioness_mode_choice": "(task: 'str') -> 'bool'",
    "is_versioned_documentation_request": "(task: 'str') -> 'bool'",
    "documentation_library_for_task": "(task: 'str') -> 'str | None'",
    "extract_preference_proposals": "(task: 'str') -> 'list[PreferenceProposal]'",
    "hydrate_router_decision": "(raw_decision: 'RouterDecision | TaskDecision | dict', task: 'str') -> 'TaskDecision'",
    "_lioness_mode_plan": "(decision: 'TaskDecision', task: 'str', *, memory_notes: 'list[str]', policy_hash: 'str | None') -> 'WorkflowPlan'",
    "repair_router_decision": "(raw_decision: 'TaskDecision', task: 'str') -> 'TaskDecision'",
    "deterministic_router_fallback": "(task: 'str', error: 'BaseException | None' = None) -> 'TaskDecision'",
    "_is_fatal_exception": "(error: 'BaseException') -> 'bool'",
    "_best_named_file": "(directory: 'Path', keywords: 'tuple[str, ...]') -> 'Path | None'",
    "discover_demo_bundle": "(action: 'str') -> 'tuple[dict[str, str], str] | None'",
    "reusable_episode_inputs": "(action: 'str', episodes: 'list[Episode]') -> 'tuple[dict[str, str], str] | None'",
}


def test_interpretation_public_surface_is_characterized():
    assert interpretation.__all__ == PUBLIC_EXPORTS
    for name, signature in PUBLIC_SIGNATURES.items():
        assert str(inspect.signature(getattr(interpretation, name))) == signature
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(interpretation, name)


@pytest.mark.parametrize(
    "error",
    [KeyboardInterrupt(), SystemExit(), GeneratorExit()],
)
def test_fatal_provider_exceptions_are_characterized(error):
    assert interpretation._is_fatal_exception(error) is True


def test_ordinary_provider_error_is_not_fatal():
    assert interpretation._is_fatal_exception(TimeoutError()) is False
```

- [ ] **Step 2: Run the characterization tests against the original module**

Run:

```bash
pytest tests/test_interpretation_package.py -q
```

Expected: `5 passed`.

- [ ] **Step 3: Run focused existing interpretation behavior**

Run:

```bash
pytest tests/test_agent_gate.py -k "deterministic_router or repair_router or hydrate_router or continuation or documentation or demo_bundle or reusable_episode or lioness_mode" -q
```

Expected: all selected tests pass except a selected test that belongs to the four documented baseline failures.

- [ ] **Step 4: Commit the guardrail**

```bash
git add tests/test_interpretation_package.py
git commit -m "test: characterize interpretation behavior"
```

---

### Task 2: Convert the Module to a Package Mechanically

**Files:**
- Delete: `scripts/netzoo_agent_core/interpretation.py`
- Create: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Create: `scripts/netzoo_agent_core/interpretation/core.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_interpretation_package.py`

**Interfaces:**
- Consumes: the complete current monolith.
- Produces: an import-compatible package with all behavior temporarily in `core.py`.

- [ ] **Step 1: Add failing package-structure tests**

Append:

```python
def test_interpretation_is_a_package_with_temporary_core():
    assert hasattr(interpretation, "__path__")
    core = importlib.import_module("netzoo_agent_core.interpretation.core")
    for name in PUBLIC_EXPORTS:
        assert getattr(core, name) is getattr(interpretation, name)


def test_interpretation_package_exports_only_the_existing_surface():
    assert interpretation.__all__ == PUBLIC_EXPORTS
```

- [ ] **Step 2: Verify the package test fails before conversion**

Run:

```bash
pytest tests/test_interpretation_package.py -k "package" -q
```

Expected: failure because the module has no `__path__`.

- [ ] **Step 3: Move the module into `core.py` without changing bodies**

Move all 958 lines into `scripts/netzoo_agent_core/interpretation/core.py`. Change only package-relative imports:

```python
from ..contracts import ...
from ..validation import ...
from ..execution import ...
from ..routing import ...
```

Keep the exact original `__all__` and every function body unchanged.

- [ ] **Step 4: Add the temporary package facade**

Create `interpretation/__init__.py`:

```python
"""Deterministic task hydration, repair, fallback, and input discovery."""

from . import core
from .core import (
    INPUT_LABELS,
    _best_named_file,
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _is_fatal_exception,
    _lioness_mode_plan,
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    deterministic_router_fallback,
    discover_demo_bundle,
    documentation_library_for_task,
    extract_preference_proposals,
    hydrate_router_decision,
    is_versioned_documentation_request,
    repair_router_decision,
    reusable_episode_inputs,
)

_INTERPRETATION_IMPLEMENTATION_MODULES = (core,)

__all__ = [
    "INPUT_LABELS",
    "_candidate_keywords",
    "_choose_unambiguous_candidate",
    "_task_path",
    "_mentions_unspecified_data_directory",
    "_needs_lioness_mode_choice",
    "is_versioned_documentation_request",
    "documentation_library_for_task",
    "extract_preference_proposals",
    "hydrate_router_decision",
    "_lioness_mode_plan",
    "repair_router_decision",
    "deterministic_router_fallback",
    "_is_fatal_exception",
    "_best_named_file",
    "discover_demo_bundle",
    "reusable_episode_inputs",
]
```

- [ ] **Step 5: Register the temporary implementation owner in the legacy facade**

Add:

```python
from netzoo_agent_core.interpretation import _INTERPRETATION_IMPLEMENTATION_MODULES
```

Change the tuple entry to:

```python
interpretation, *_INTERPRETATION_IMPLEMENTATION_MODULES,
```

Keep `scripts/netzoo_agent.py` at or below 150 lines.

- [ ] **Step 6: Run package, facade, graph, and boundary tests**

```bash
python -m compileall -q scripts/netzoo_agent_core/interpretation scripts/netzoo_agent.py
pytest tests/test_interpretation_package.py tests/test_graph_package.py tests/test_agent_module_boundaries.py -q
pytest tests/test_agent_gate.py -k "deterministic_router or repair_router or hydrate_router or continuation or documentation or demo_bundle or lioness_mode" -q
```

Expected: package and selected behavior pass except documented baseline failures selected by the expression.

- [ ] **Step 7: Commit the mechanical conversion**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/interpretation.py scripts/netzoo_agent_core/interpretation tests/test_interpretation_package.py
git commit -m "refactor: convert interpretation module to package"
```

---

### Task 3: Extract Deterministic Text Extraction and Hydration

**Files:**
- Create: `scripts/netzoo_agent_core/interpretation/extraction.py`
- Create: `scripts/netzoo_agent_core/interpretation/hydration.py`
- Modify: `scripts/netzoo_agent_core/interpretation/core.py`
- Modify: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Modify: `tests/test_interpretation_package.py`

**Interfaces:**
- Consumes: existing contracts, registry data, and routing parsing helpers.
- Produces: extraction functions and `hydrate_router_decision` in focused internal modules.

- [ ] **Step 1: Add failing child-module and patch tests**

Append:

```python
def test_extraction_and_hydration_modules_are_internal():
    extraction = importlib.import_module("netzoo_agent_core.interpretation.extraction")
    hydration = importlib.import_module("netzoo_agent_core.interpretation.hydration")
    assert extraction.__all__ == []
    assert hydration.__all__ == []


def test_legacy_hydration_patch_reaches_child():
    hydration = importlib.import_module("netzoo_agent_core.interpretation.hydration")
    original = legacy_agent.hydrate_router_decision

    def replacement(raw_decision, task):
        raise AssertionError("hydration patch sentinel")

    try:
        legacy_agent.hydrate_router_decision = replacement
        assert hydration.hydrate_router_decision is replacement
    finally:
        legacy_agent.hydrate_router_decision = original
```

- [ ] **Step 2: Verify child imports fail before extraction**

```bash
pytest tests/test_interpretation_package.py -k "extraction_and_hydration or hydration_patch" -q
```

Expected: import failures for both child modules.

- [ ] **Step 3: Move deterministic extraction exactly**

Create `extraction.py` with `__all__: list[str] = []` and move exact definitions for:

```python
INPUT_LABELS: dict[str, str]
_task_path(task: str, field_name: str) -> str | None
_mentions_unspecified_data_directory(task: str) -> bool
_needs_lioness_mode_choice(task: str) -> bool
is_versioned_documentation_request(task: str) -> bool
documentation_library_for_task(task: str) -> str | None
extract_preference_proposals(task: str) -> list[PreferenceProposal]
```

Import only `re`, the required contracts, `CONTEXT7_LIBRARY_ALIASES`, `_extract_named_path`, and `is_workflow_information_request`. Preserve the existing regular expressions and returned text exactly.

- [ ] **Step 4: Move hydration exactly**

Create `hydration.py` with `__all__: list[str] = []` and:

```python
def hydrate_router_decision(
    raw_decision: RouterDecision | TaskDecision | dict,
    task: str,
) -> TaskDecision:
```

Move the current body unchanged, including its current statement order and any duplication. Replace same-module references with imports from `.extraction`:

```python
from .extraction import (
    _task_path,
    documentation_library_for_task,
    extract_preference_proposals,
)
```

- [ ] **Step 5: Make the remaining temporary core depend on extraction**

Delete the moved definitions from `core.py`. Add imports for the extraction functions still used by repair and fallback:

```python
from .extraction import (
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    documentation_library_for_task,
    is_versioned_documentation_request,
)
```

Do not import the package facade.

- [ ] **Step 6: Update facade exports and compatibility owners**

Import `extraction`, `hydration`, and their public objects in `__init__.py`. Set:

```python
_INTERPRETATION_IMPLEMENTATION_MODULES = (core, extraction, hydration)
```

Keep the package `__all__` exactly equal to `PUBLIC_EXPORTS`.

- [ ] **Step 7: Run extraction, hydration, planning, and graph tests**

```bash
pytest tests/test_interpretation_package.py -q
pytest tests/test_agent_gate.py -k "hydrate_router or preference or documentation or lioness_mode or missing_input" -q
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
```

Expected: all selected tests pass except documented baseline failures selected by the expressions.

- [ ] **Step 8: Commit extraction and hydration**

```bash
git add scripts/netzoo_agent_core/interpretation/extraction.py scripts/netzoo_agent_core/interpretation/hydration.py scripts/netzoo_agent_core/interpretation/core.py scripts/netzoo_agent_core/interpretation/__init__.py tests/test_interpretation_package.py
git commit -m "refactor: extract interpretation hydration"
```

---

### Task 4: Extract Decision Repair and Provider Fallback

**Files:**
- Create: `scripts/netzoo_agent_core/interpretation/repair.py`
- Create: `scripts/netzoo_agent_core/interpretation/provider_fallback.py`
- Modify: `scripts/netzoo_agent_core/interpretation/core.py`
- Modify: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Modify: `tests/test_interpretation_package.py`

**Interfaces:**
- Consumes: extraction functions, contracts, registry authority, and routing capability helpers.
- Produces: repaired `TaskDecision`, deterministic provider fallback, and fatal-error classification.

- [ ] **Step 1: Add failing internal-module and patch tests**

Append:

```python
def test_repair_and_provider_fallback_modules_are_internal():
    repair = importlib.import_module("netzoo_agent_core.interpretation.repair")
    fallback = importlib.import_module(
        "netzoo_agent_core.interpretation.provider_fallback"
    )
    assert repair.__all__ == []
    assert fallback.__all__ == []


@pytest.mark.parametrize(
    ("module_name", "symbol"),
    [
        ("repair", "repair_router_decision"),
        ("provider_fallback", "deterministic_router_fallback"),
    ],
)
def test_legacy_decision_patch_reaches_owner(module_name, symbol):
    owner = importlib.import_module(
        f"netzoo_agent_core.interpretation.{module_name}"
    )
    original = getattr(legacy_agent, symbol)

    def replacement(*args, **kwargs):
        raise AssertionError("decision patch sentinel")

    try:
        setattr(legacy_agent, symbol, replacement)
        assert getattr(owner, symbol) is replacement
    finally:
        setattr(legacy_agent, symbol, original)
```

- [ ] **Step 2: Verify the new child imports fail**

```bash
pytest tests/test_interpretation_package.py -k "repair_and_provider or decision_patch" -q
```

Expected: import failures.

- [ ] **Step 3: Move router repair without changing authority order**

Create `repair.py` with `__all__: list[str] = []` and move exact bodies for:

```python
def _lioness_mode_plan(
    decision: TaskDecision,
    task: str,
    *,
    memory_notes: list[str],
    policy_hash: str | None,
) -> WorkflowPlan:

def repair_router_decision(
    raw_decision: TaskDecision,
    task: str,
) -> TaskDecision:
```

Import extraction dependencies directly from `.extraction`. Preserve documentation routing, information requests, `PREVIOUS_ACTION`, inferred deliverable repair, LIONESS repair, CONDOR repair, decision copying, missing-input calculation, and reason text in current order.

- [ ] **Step 4: Move provider fallback and fatal classification exactly**

Create `provider_fallback.py` with `__all__: list[str] = []` and move:

```python
def deterministic_router_fallback(
    task: str,
    error: BaseException | None = None,
) -> TaskDecision:

def _is_fatal_exception(error: BaseException) -> bool:
```

Import `_task_path`, `documentation_library_for_task`, and `is_versioned_documentation_request` directly from `.extraction`. Preserve all provider reason strings, validation calls, run detection, ambiguity results, missing-input rules, and confidence values.

- [ ] **Step 5: Remove moved definitions and register owners**

Delete the four moved functions and their now-unused imports from `core.py`. Update `__init__.py` imports and set:

```python
_INTERPRETATION_IMPLEMENTATION_MODULES = (
    core,
    extraction,
    hydration,
    provider_fallback,
    repair,
)
```

Keep `interpretation.__all__` unchanged.

- [ ] **Step 6: Run repair, fallback, continuation, and graph tests**

```bash
pytest tests/test_interpretation_package.py -q
pytest tests/test_agent_gate.py -k "deterministic_router or repair_router or continuation or documentation or lioness or condor_run" -q
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
```

Expected: only documented baseline failures may fail when selected.

- [ ] **Step 7: Commit decision modules**

```bash
git add scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/interpretation/provider_fallback.py scripts/netzoo_agent_core/interpretation/core.py scripts/netzoo_agent_core/interpretation/__init__.py tests/test_interpretation_package.py
git commit -m "refactor: extract interpretation decision logic"
```

---

### Task 5: Extract Discovery and Finalize the Package

**Files:**
- Create: `scripts/netzoo_agent_core/interpretation/discovery.py`
- Delete: `scripts/netzoo_agent_core/interpretation/core.py`
- Modify: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Modify: `tests/test_interpretation_package.py`

**Interfaces:**
- Consumes: existing file scoring, workflow validators, execution input checks, and episode contracts.
- Produces: final package with no temporary monolith and an acyclic child dependency graph.

- [ ] **Step 1: Add failing discovery, size, privacy, and dependency tests**

Append:

```python
def test_discovery_module_is_internal_and_patchable():
    discovery = importlib.import_module("netzoo_agent_core.interpretation.discovery")
    assert discovery.__all__ == []
    original = legacy_agent.discover_demo_bundle

    def replacement(action):
        return None

    try:
        legacy_agent.discover_demo_bundle = replacement
        assert discovery.discover_demo_bundle is replacement
    finally:
        legacy_agent.discover_demo_bundle = original


def test_interpretation_children_are_responsibility_sized():
    maximum_lines = {
        "discovery": 320,
        "extraction": 280,
        "hydration": 140,
        "provider_fallback": 230,
        "repair": 340,
    }
    for module_name, maximum in maximum_lines.items():
        module = importlib.import_module(
            f"netzoo_agent_core.interpretation.{module_name}"
        )
        assert len(inspect.getsource(module).splitlines()) <= maximum, module_name


def test_temporary_interpretation_core_is_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("netzoo_agent_core.interpretation.core")


def test_interpretation_package_uses_final_responsibility_owners():
    owners = {
        "discovery": (
            "_candidate_keywords",
            "_choose_unambiguous_candidate",
            "_best_named_file",
            "discover_demo_bundle",
            "reusable_episode_inputs",
        ),
        "extraction": (
            "INPUT_LABELS",
            "_task_path",
            "_mentions_unspecified_data_directory",
            "_needs_lioness_mode_choice",
            "is_versioned_documentation_request",
            "documentation_library_for_task",
            "extract_preference_proposals",
        ),
        "hydration": ("hydrate_router_decision",),
        "provider_fallback": (
            "deterministic_router_fallback",
            "_is_fatal_exception",
        ),
        "repair": ("_lioness_mode_plan", "repair_router_decision"),
    }
    for module_name, names in owners.items():
        owner = importlib.import_module(
            f"netzoo_agent_core.interpretation.{module_name}"
        )
        for name in names:
            assert getattr(interpretation, name) is getattr(owner, name)


def test_interpretation_child_dependencies_are_acyclic_and_scoped():
    child_names = {
        "discovery",
        "extraction",
        "hydration",
        "provider_fallback",
        "repair",
    }
    dependencies = {}
    for child_name in child_names:
        module = importlib.import_module(
            f"netzoo_agent_core.interpretation.{child_name}"
        )
        tree = ast.parse(inspect.getsource(module))
        dependencies[child_name] = {
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module in child_names
        }
    assert dependencies == {
        "discovery": set(),
        "extraction": set(),
        "hydration": {"extraction"},
        "provider_fallback": {"extraction"},
        "repair": {"extraction"},
    }


def test_interpretation_package_does_not_leak_new_helpers():
    assert interpretation.__all__ == PUBLIC_EXPORTS
    for name in ("core", "extraction", "hydration", "provider_fallback", "repair"):
        assert name not in interpretation.__all__
```

- [ ] **Step 2: Verify discovery and final-structure tests fail**

```bash
pytest tests/test_interpretation_package.py -k "discovery_module or responsibility_sized or temporary_interpretation_core or child_dependencies" -q
```

Expected: discovery import failure and temporary-core removal failure.

- [ ] **Step 3: Move candidate and bundle discovery exactly**

Create `discovery.py` with `__all__: list[str] = []` and move exact bodies for:

```python
def _candidate_keywords(action: str, field_name: str) -> tuple[str, ...]:
def _choose_unambiguous_candidate(
    candidates: list[str],
    keywords: tuple[str, ...],
    nearby: Path,
) -> tuple[str | None, str]:
def _best_named_file(directory: Path, keywords: tuple[str, ...]) -> Path | None:
def discover_demo_bundle(action: str) -> tuple[dict[str, str], str] | None:
def reusable_episode_inputs(
    action: str,
    episodes: list[Episode],
) -> tuple[dict[str, str], str] | None:
```

Preserve sorting keys, candidate scoring, validation calls, ambiguity thresholds, coherent-directory rules, LIONESS sample counts, episode status/workflow checks, path-existence checks, and reason strings exactly.

- [ ] **Step 4: Remove `core.py` and finalize package imports**

Replace the Task 2 test `test_interpretation_is_a_package_with_temporary_core` with `test_interpretation_package_uses_final_responsibility_owners` from Step 1. After discovery extraction, `core.py` has no remaining implementation and must be deleted. Define the final private tuple in `__init__.py`:

```python
_INTERPRETATION_IMPLEMENTATION_MODULES = (
    discovery,
    extraction,
    hydration,
    provider_fallback,
    repair,
)
```

Re-export the exact 17 public objects from their owning modules. Do not expose child module names through `__all__`.

- [ ] **Step 5: Run final structure and behavior tests**

```bash
python -m compileall -q scripts/netzoo_agent_core/interpretation scripts/netzoo_agent.py
pytest tests/test_interpretation_package.py tests/test_agent_module_boundaries.py -q
pytest tests/test_agent_gate.py -k "demo_bundle or reusable_episode or deterministic_router or repair_router or hydrate_router or documentation or continuation or lioness" -q
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
```

Expected: package, size, dependency, patch, and selected behavior pass except documented baseline failures selected by the expressions.

- [ ] **Step 6: Verify the legacy facade limit and commit final structure**

```bash
wc -l scripts/netzoo_agent.py scripts/netzoo_agent_core/interpretation/*.py
git diff --check
git add scripts/netzoo_agent_core/interpretation/core.py scripts/netzoo_agent_core/interpretation/discovery.py scripts/netzoo_agent_core/interpretation/__init__.py tests/test_interpretation_package.py
git commit -m "refactor: extract interpretation discovery"
```

Expected: legacy facade at most 150 lines and no child exceeds its test limit.

---

### Task 6: Verify Full Behavior and Repository Hygiene

**Files:**
- Verify: `scripts/netzoo_agent_core/interpretation/`
- Verify: `scripts/netzoo_agent.py`
- Verify: `tests/test_interpretation_package.py`
- Verify only: all unrelated dirty-worktree entries

**Interfaces:**
- Consumes: the completed interpretation package.
- Produces: evidence of public compatibility, exact behavior, clean dependencies, and repository scope.

- [ ] **Step 1: Verify compilation and final sizes**

```bash
wc -l scripts/netzoo_agent_core/interpretation/*.py scripts/netzoo_agent.py
python -m compileall -q scripts/netzoo_agent_core/interpretation scripts/netzoo_agent.py
```

Expected: compilation succeeds, facade is at most 150 lines, and no interpretation child exceeds its characterized limit.

- [ ] **Step 2: Run interpretation and adjacent integration tests**

```bash
pytest tests/test_interpretation_package.py tests/test_graph_package.py tests/test_graph_tracing.py tests/test_agent_module_boundaries.py tests/test_agent_gate.py tests/test_agent_stability.py -q
```

Expected: no failure beyond the same four documented baseline failures.

- [ ] **Step 3: Run the clean full baseline**

```bash
pytest -q -k 'not test_clarification_marker_preserves_previous_action_against_reroute and not test_clarification_wizard_selects_each_missing_field_independently and not test_recovered_plan_is_authorized_by_the_same_plan_evaluator and not test_selected_input_keeps_selected_provenance_after_replanning'
```

Expected: at least 270 passed, 12 skipped, four deselected, and no selected failure.

- [ ] **Step 4: Run the unfiltered full baseline**

```bash
pytest -q
```

Expected: at least 270 passed, 12 skipped, and exactly these four failures:

```text
test_clarification_marker_preserves_previous_action_against_reroute
test_clarification_wizard_selects_each_missing_field_independently
test_recovered_plan_is_authorized_by_the_same_plan_evaluator
test_selected_input_keeps_selected_provenance_after_replanning
```

- [ ] **Step 5: Verify dependency direction and legacy ownership**

```bash
rg -n "^from \\.|^from \\.\\." scripts/netzoo_agent_core/interpretation
pytest tests/test_interpretation_package.py -k "patch or dependencies or public_surface" -q
```

Expected: only `hydration`, `repair`, and `provider_fallback` import `extraction`; all compatibility tests pass.

- [ ] **Step 6: Verify commit range, whitespace, staging, and unrelated changes**

Use the design commit as the range base:

```bash
git diff --check 502f5ac..HEAD
git diff --cached --name-only
git status --short
git log --oneline 502f5ac..HEAD
```

Expected: no whitespace errors, empty staging after implementation commits, only planned commits in the range, and unchanged unrelated dirty-worktree entries.

- [ ] **Step 7: Report evidence without an empty verification commit**

Report:

- final child files and line counts;
- exact public-export and signature result;
- legacy patch propagation result;
- focused interpretation result;
- graph and planning integration result;
- clean full baseline;
- unfiltered baseline and known failures;
- implementation commit hashes; and
- confirmation that unrelated changes remained untouched.

Do not create a verification-only commit.
