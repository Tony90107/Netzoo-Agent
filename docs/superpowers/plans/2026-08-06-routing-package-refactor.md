# Routing Package Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 877-line `routing.py` module with a responsibility-oriented `routing/` package while preserving all routing behaviour, imports, runtime overrides, and legacy monkeypatch propagation.

**Architecture:** `routing/__init__.py` remains the stable interface and re-exports all 37 historical names. Five child modules isolate in-process capability rules, bounded local discovery, remote retrieval, allow-listed dispatch, and result normalization; the legacy facade registers each child so assignments propagate to the implementation that consumes them.

**Tech Stack:** Python 3.10+, Pydantic 2, standard-library asyncio and filesystem utilities, LangChain MCP adapters, pytest/unittest, existing NetZoo compatibility facade.

## Global Constraints

- This is a structural refactor only; no routing rule or data-flow timing may change.
- Preserve every name and order in the historical `routing.py.__all__` list.
- Preserve all user-visible strings byte-for-byte for identical inputs.
- Preserve `netzoo_agent_core.routing` imports and the `netzoo_agent` legacy facade.
- Preserve facade monkeypatch propagation into routing child modules.
- Preserve runtime overrides for `PROJECT_ROOT`, `TOOL_LOG_ROOT`, and other mutable runtime settings.
- Preserve filesystem traversal bounds, remote MCP requests, dispatch allow-lists, artifact checks, retry hints, metrics, and log behaviour.
- Do not modify or commit unrelated working-tree changes.
- The four recorded baseline failures are out of scope; no new failure or changed failure location is acceptable.

---

## File Structure

| Path | Responsibility |
|---|---|
| `scripts/netzoo_agent_core/routing/__init__.py` | Stable package interface and historical re-exports |
| `scripts/netzoo_agent_core/routing/capability.py` | Deterministic intent, recommendation, validation, and authorization rules |
| `scripts/netzoo_agent_core/routing/discovery.py` | Named-path parsing, bounded file discovery, scoring, and output defaults |
| `scripts/netzoo_agent_core/routing/retrieval.py` | Read-only Context7 and Websearch MCP adapters |
| `scripts/netzoo_agent_core/routing/dispatch.py` | Selection of one allow-listed local or retrieval implementation |
| `scripts/netzoo_agent_core/routing/results.py` | Tool output diagnostics, artifact validation, logging, and typed normalization |
| `scripts/netzoo_agent.py` | Registration of routing children in the legacy compatibility facade |
| `tests/test_routing_package.py` | Package structure, export, monkeypatch, and runtime compatibility contract |

The child modules must not import `routing/__init__.py`. Existing callers must
continue importing the package interface rather than responsibility modules.

---

### Task 1: Record the Baseline and Add the Failing Routing Package Contract

**Files:**

- Create: `tests/test_routing_package.py`
- Reference: `scripts/netzoo_agent_core/routing.py`
- Reference: `scripts/netzoo_agent.py:35-109`

**Interfaces:**

- Consumes: historical `routing.py.__all__`, the `netzoo_agent` facade, and runtime assignment propagation.
- Produces: a red package-structure and child-propagation contract for Task 2.

- [ ] **Step 1: Run the complete pre-refactor baseline**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Expected: 236 passed, 12 skipped, and these four failures:

```text
test_clarification_marker_preserves_previous_action_against_reroute
test_clarification_wizard_selects_each_missing_field_independently
test_recovered_plan_is_authorized_by_the_same_plan_evaluator
test_selected_input_keeps_selected_provenance_after_replanning
```

Record exact traceback locations. Stop if the baseline contains any additional
failure, because the working tree has changed since design approval.

- [ ] **Step 2: Add the package and compatibility contract**

Create `tests/test_routing_package.py` with:

```python
from __future__ import annotations

import importlib
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.routing as routing  # noqa: E402


HISTORICAL_EXPORTS = [
    "MIN_TOOL_CONFIDENCE",
    "FILE_DISCOVERY_MAX_DEPTH",
    "FILE_DISCOVERY_MAX_VISITED",
    "FILE_DISCOVERY_MAX_RESULTS",
    "CONTEXT7_URL",
    "CONTEXT7_MAX_CHARS",
    "WEBSEARCH_URL",
    "WEBSEARCH_MAX_CHARS",
    "CONTEXT7_LIBRARY_ALIASES",
    "UNSUPPORTED_DELIVERABLE_PATTERNS",
    "WORKFLOW_INFORMATION_PATTERNS",
    "is_workflow_information_request",
    "infer_goal_capabilities",
    "infer_advisory_capabilities",
    "inferred_execution_action",
    "has_direct_execution_intent",
    "validate_task_text",
    "normalize_context7_library",
    "enforce_capability_gate",
    "_extract_named_path",
    "_score_candidate_file",
    "_find_candidate_files",
    "_default_lioness_outputs",
    "_default_network_output",
    "_tool_text",
    "_exception_text",
    "_find_mcp_tool",
    "_extract_context7_library_id",
    "_query_context7_async",
    "query_context7_docs",
    "_web_search_async",
    "query_web_search",
    "query_web_search_first_url",
    "execute_selected_tool",
    "_expected_artifacts",
    "_diagnostic_messages",
    "structure_tool_result",
]


def test_routing_is_responsibility_oriented_package():
    assert hasattr(routing, "__path__")
    for module_name in (
        "capability",
        "discovery",
        "retrieval",
        "dispatch",
        "results",
    ):
        importlib.import_module(f"netzoo_agent_core.routing.{module_name}")


def test_historical_routing_surface_is_preserved():
    assert routing.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(routing, name), name


def test_legacy_facade_uses_routing_package_exports():
    for name in HISTORICAL_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(routing, name)


def test_legacy_patch_reaches_retrieval_and_dispatch_children():
    retrieval = importlib.import_module("netzoo_agent_core.routing.retrieval")
    dispatch = importlib.import_module("netzoo_agent_core.routing.dispatch")
    original = legacy_agent.query_web_search

    def replacement(query: str) -> str:
        return (
            "Websearch MCP result (external, untrusted reference content):\n\n"
            '{"results": [{"url": "https://example.test/result"}]}'
        )

    try:
        legacy_agent.query_web_search = replacement
        assert retrieval.query_web_search is replacement
        assert dispatch.query_web_search is replacement
        assert (
            legacy_agent.query_web_search_first_url("genes")
            == "https://example.test/result"
        )
    finally:
        legacy_agent.query_web_search = original


def test_runtime_overrides_reach_routing_children(tmp_path: Path):
    discovery = importlib.import_module("netzoo_agent_core.routing.discovery")
    results = importlib.import_module("netzoo_agent_core.routing.results")
    original_project_root = legacy_agent.PROJECT_ROOT
    original_log_root = legacy_agent.TOOL_LOG_ROOT
    try:
        legacy_agent.PROJECT_ROOT = tmp_path
        legacy_agent.TOOL_LOG_ROOT = tmp_path / "logs"
        assert discovery.PROJECT_ROOT == tmp_path
        assert results.TOOL_LOG_ROOT == tmp_path / "logs"
    finally:
        legacy_agent.PROJECT_ROOT = original_project_root
        legacy_agent.TOOL_LOG_ROOT = original_log_root
```

- [ ] **Step 3: Run the new contract and verify the red state**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_routing_package.py -q
```

Expected: two existing surface tests pass. Package structure, child patch
propagation, and child runtime propagation fail because `routing` is still one
module.

---

### Task 2: Convert `routing.py` into the Responsibility-Oriented Package

**Files:**

- Delete: `scripts/netzoo_agent_core/routing.py`
- Create: `scripts/netzoo_agent_core/routing/__init__.py`
- Create: `scripts/netzoo_agent_core/routing/capability.py`
- Create: `scripts/netzoo_agent_core/routing/discovery.py`
- Create: `scripts/netzoo_agent_core/routing/retrieval.py`
- Create: `scripts/netzoo_agent_core/routing/dispatch.py`
- Create: `scripts/netzoo_agent_core/routing/results.py`
- Modify: `scripts/netzoo_agent.py:35-103`
- Test: `tests/test_routing_package.py`

**Interfaces:**

- Consumes: `TaskDecision`, `ToolExecutionResult`, workflow registry definitions,
  `LOCAL_TOOL_EXECUTORS`, artifact validation, private-log helpers, and MCP
  adapters.
- Produces: all 37 historical exports through `routing/__init__.py`, including
  `enforce_capability_gate(decision: TaskDecision, user_task: str | None = None) -> TaskDecision`,
  `execute_selected_tool(decision: TaskDecision) -> str`, and
  `structure_tool_result(action: str, decision: TaskDecision, raw_output: str, persist_log: bool = False, attempt_id: int = 0) -> ToolExecutionResult`.

- [ ] **Step 1: Create `capability.py` with pure authorization behaviour**

Move the original constants and complete function bodies without modifying
conditions or strings:

```text
MIN_TOOL_CONFIDENCE
CONTEXT7_LIBRARY_ALIASES
UNSUPPORTED_DELIVERABLE_PATTERNS
WORKFLOW_INFORMATION_PATTERNS
is_workflow_information_request
infer_goal_capabilities
infer_advisory_capabilities
inferred_execution_action
has_direct_execution_intent
validate_task_text
normalize_context7_library
enforce_capability_gate
```

Use this dependency surface:

```python
from __future__ import annotations

import re

from workflow_registry import LOCAL_WORKFLOW_ACTIONS, REQUIRED_INPUTS

from ..contracts import TaskDecision
```

Define `__all__` with the twelve names listed above, in that order.

- [ ] **Step 2: Create `discovery.py` with bounded local filesystem behaviour**

Move the three discovery constants and the complete original source block from
`_extract_named_path` through `_default_network_output` (`routing.py` lines
434–554 before this refactor). Use:

```python
from __future__ import annotations

import os
import re
from pathlib import Path

from ..contracts import PROJECT_ROOT, _display_path
```

Define `__all__` in this exact order:

```python
__all__ = [
    "FILE_DISCOVERY_MAX_DEPTH",
    "FILE_DISCOVERY_MAX_VISITED",
    "FILE_DISCOVERY_MAX_RESULTS",
    "_extract_named_path",
    "_score_candidate_file",
    "_find_candidate_files",
    "_default_lioness_outputs",
    "_default_network_output",
]
```

- [ ] **Step 3: Create `retrieval.py` with read-only remote adapters**

Move the four retrieval constants and the complete original source block from
`_tool_text` through `query_web_search_first_url` (`routing.py` lines 557–743).
Use:

```python
from __future__ import annotations

import asyncio
import json
import os
import re
```

Define `__all__` in this exact order:

```python
__all__ = [
    "CONTEXT7_URL",
    "CONTEXT7_MAX_CHARS",
    "WEBSEARCH_URL",
    "WEBSEARCH_MAX_CHARS",
    "_tool_text",
    "_exception_text",
    "_find_mcp_tool",
    "_extract_context7_library_id",
    "_query_context7_async",
    "query_context7_docs",
    "_web_search_async",
    "query_web_search",
    "query_web_search_first_url",
]
```

- [ ] **Step 4: Create `dispatch.py` with the allow-listed execution seam**

Move the complete `execute_selected_tool` body from original lines 746–759.
Use:

```python
from workflow_registry import executor_arguments

from ..contracts import TaskDecision
from ..execution import LOCAL_TOOL_EXECUTORS
from .retrieval import query_context7_docs, query_web_search

__all__ = ["execute_selected_tool"]
```

- [ ] **Step 5: Create `results.py` with typed result normalization**

Move the complete original source block from `_expected_artifacts` through
`structure_tool_result` (`routing.py` lines 762–877). Use:

```python
from __future__ import annotations

import re
import uuid
from typing import Literal

from ..artifact_validation import ARTIFACT_WRITE_ACTIONS, validate_output_artifacts
from ..contracts import (
    TOOL_LOG_ROOT,
    TOOL_RAW_MAX_CHARS,
    TaskDecision,
    ToolExecutionResult,
    _display_path,
)
from ..memory import _ensure_private_directory, _write_private_text

__all__ = [
    "_expected_artifacts",
    "_diagnostic_messages",
    "structure_tool_result",
]
```

- [ ] **Step 6: Create `routing/__init__.py` as the complete stable interface**

Import each historical name from its owning child module and define `__all__`
to exactly equal `HISTORICAL_EXPORTS` from Task 1. The initializer must contain
only its module docstring, child imports, and that 37-name list.

- [ ] **Step 7: Register routing children in the legacy facade**

Add explicit child imports after the existing `from netzoo_agent_core import`
block:

```python
from netzoo_agent_core.routing import (
    capability as routing_capability,
    discovery as routing_discovery,
    dispatch as routing_dispatch,
    results as routing_results,
    retrieval as routing_retrieval,
)
```

Insert the children immediately after `routing` in `_IMPLEMENTATION_MODULES`:

```python
    routing,
    routing_capability,
    routing_discovery,
    routing_retrieval,
    routing_dispatch,
    routing_results,
```

Do not change `_CompatibilityFacade.__setattr__`; the existing identity-based
propagation loop will update package exports, child globals, and caller globals.

- [ ] **Step 8: Compile and run the routing package contract**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core/routing
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_routing_package.py -q
```

Expected: compilation succeeds and all five package tests pass.

- [ ] **Step 9: Run focused routing behaviour tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_agent_gate.py \
  tests/test_agent_artifacts.py \
  tests/test_agent_stability.py \
  -k 'capability or workflow_information or context7 or web_search or candidate or structure_tool_result or artifact or recovery' \
  -q
```

Expected: no new failure relative to Task 1. The recorded recovery-plan failure
may remain; routing package tests must all pass.

- [ ] **Step 10: Compare every moved function body**

Use `git show HEAD:scripts/netzoo_agent_core/routing.py` as the original source
and compare these exact ranges with the corresponding child definitions:

```text
158–431 → capability.py
434–554 → discovery.py
557–743 → retrieval.py
746–759 → dispatch.py
762–877 → results.py
```

Run `diff -u` for each pair and accept only an end-of-file newline difference.
Then run:

```bash
git diff --check
wc -l scripts/netzoo_agent_core/routing/*.py
```

Expected: no whitespace errors and no responsibility module above approximately
300 lines without a cohesion-based explanation.

- [ ] **Step 11: Commit the atomic package conversion**

```bash
git add \
  scripts/netzoo_agent_core/routing.py \
  scripts/netzoo_agent_core/routing \
  scripts/netzoo_agent.py \
  tests/test_routing_package.py
git commit -m "refactor: split routing into focused package"
```

---

### Task 3: Verify Callers and Complete Regression

**Files:**

- Verify: `scripts/netzoo_agent_core/graph.py`
- Verify: `scripts/netzoo_agent_core/planning.py`
- Verify: `scripts/netzoo_agent_core/interpretation.py`
- Verify: `scripts/netzoo_agent_core/cli.py`
- Verify: `scripts/netzoo_agent_core/compatibility.py`
- Verify: `scripts/netzoo_agent.py`
- Test: `tests/test_routing_package.py`
- Test: complete `tests/` suite

**Interfaces:**

- Consumes: the stable routing package and compatibility registration produced by Task 2.
- Produces: evidence that all callers behave through the unchanged interface and the complete suite has no new failures.

- [ ] **Step 1: Verify production callers remain on the package interface**

Run:

```bash
rg -n 'from \.routing|netzoo_agent_core\.routing' scripts tests -g '*.py'
```

Expected: production callers import `.routing`; only `scripts/netzoo_agent.py`
and `tests/test_routing_package.py` intentionally name routing child modules.

- [ ] **Step 2: Run all directly affected tests together**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_routing_package.py \
  tests/test_agent_gate.py \
  tests/test_agent_artifacts.py \
  tests/test_agent_stability.py \
  tests/test_graph_tracing.py \
  tests/test_agent_module_boundaries.py \
  -q
```

Expected: package tests pass and no failure is added to the four recorded
baseline failures.

- [ ] **Step 3: Run the complete test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Expected: the same four baseline failures, with all other tests passing. Compare
node IDs and traceback locations with Task 1.

- [ ] **Step 4: Run the complete suite excluding recorded baseline failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -k \
  'not test_clarification_marker_preserves_previous_action_against_reroute and not test_clarification_wizard_selects_each_missing_field_independently and not test_recovered_plan_is_authorized_by_the_same_plan_evaluator and not test_selected_input_keeps_selected_provenance_after_replanning'
```

Expected: all selected tests pass.

- [ ] **Step 5: Verify final repository state**

Run:

```bash
git status --short
git show --stat --oneline --summary HEAD
```

Expected: routing implementation paths are clean after the scoped commit, while
all unrelated pre-existing working-tree changes remain untouched.

- [ ] **Step 6: Commit only if verification required a scoped correction**

If no correction was needed, do not create an empty commit. If a correction was
required, rerun Steps 2–5 and stage only routing paths, facade registration, and
the routing package test:

```bash
git add scripts/netzoo_agent_core/routing scripts/netzoo_agent.py tests/test_routing_package.py
git commit -m "test: preserve routing package compatibility"
```
