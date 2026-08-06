# Graph Package Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 892-line graph module and its 780-line nested closure with a responsibility-oriented package while preserving the exact LangGraph interface, topology, state updates, tracing, prompts, fallbacks, and legacy patch behavior.

**Architecture:** `factory.py` constructs a frozen `_GraphContext` containing graph-lifetime dependencies. Responsibility-oriented node modules expose private `(context, state) -> dict` functions, and `topology.py` binds context with `functools.partial` before registering the unchanged LangGraph nodes and edges. The package facade exposes only `build_graph` and `invoke_graph_turn`.

**Tech Stack:** Python 3.12, LangGraph, LangChain message contracts, Pydantic models, pytest, unittest mock patching, standard-library dataclasses, functools, inspect, and hashlib.

## Global Constraints

- Preserve the exact `build_graph` parameter list, defaults, and return behavior.
- Preserve `invoke_graph_turn(app, invocation: dict)` and its `KeyboardInterrupt` translation.
- The package `__all__` must equal `["build_graph", "invoke_graph_turn"]`.
- Preserve all ten node names and their registration order.
- Preserve every ordinary edge and both conditional route mappings.
- Preserve `recover -> evaluate_plan`; never add `recover -> execute_tool`.
- Preserve every node state-update key and value shape.
- Preserve routing and response prompts byte-for-byte for the same runtime settings.
- Preserve trace event names, node labels, payloads, order, and emission timing.
- Preserve budget decisions, warning deduplication, provider fallback, and fatal-error propagation.
- Preserve planning, evaluation, execution, memory, and response authority.
- Do not add public nodes, plugins, abstract base classes, or broad exception handling.
- Preserve legacy `netzoo_agent` assignment-based monkeypatch propagation to graph child modules.
- Keep `scripts/netzoo_agent.py` at or below 150 lines.
- Do not modify, stage, or commit unrelated user changes.
- The accepted unfiltered baseline is 254 passed, 12 skipped, and the same four documented failures before new graph tests are counted.

## File Map

| Path | Final responsibility |
| --- | --- |
| `scripts/netzoo_agent_core/graph/__init__.py` | Public facade and private compatibility-module tuple. |
| `scripts/netzoo_agent_core/graph/factory.py` | Runtime dependency assembly, public graph construction, and Ctrl-C adapter. |
| `scripts/netzoo_agent_core/graph/context.py` | Frozen `_GraphContext`, event recording, and budget preflight. |
| `scripts/netzoo_agent_core/graph/prompts.py` | Exact routing and response prompt construction. |
| `scripts/netzoo_agent_core/graph/policy_memory.py` | Policy application, memory retrieval, and episode consolidation nodes. |
| `scripts/netzoo_agent_core/graph/routing_planning.py` | Classification and planning nodes. |
| `scripts/netzoo_agent_core/graph/execution.py` | Plan evaluation, tool execution, result evaluation, and recovery nodes. |
| `scripts/netzoo_agent_core/graph/response.py` | Deterministic and response-model response node. |
| `scripts/netzoo_agent_core/graph/transitions.py` | Conditional routing functions. |
| `scripts/netzoo_agent_core/graph/topology.py` | Dependency guard, node binding, instrumentation, edges, and compilation. |
| `scripts/netzoo_agent.py` | Expand the graph package child-module tuple in the legacy facade. |
| `tests/test_graph_package.py` | Public contract, prompt, package, topology, privacy, and compatibility tests. |
| `tests/test_graph_tracing.py` | Patch the graph implementation module that owns LLM construction. |
| `tests/test_agent_module_boundaries.py` | Read recovery topology from the new topology module. |
| `scripts/netzoo_agent_core/graph.py` | Delete after transferring all behavior into the package. |

---

### Task 1: Freeze the Public Graph Contract and Current Behavior

**Files:**
- Create: `tests/test_graph_package.py`
- Reference: `scripts/netzoo_agent_core/graph.py`

**Interfaces:**
- Consumes: current `build_graph` and `invoke_graph_turn` functions.
- Produces: exact public-signature and Ctrl-C characterization that must survive every later task.

- [ ] **Step 1: Add public-interface characterization tests**

Create:

```python
from __future__ import annotations

import hashlib
import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.graph as graph  # noqa: E402


PUBLIC_EXPORTS = ["build_graph", "invoke_graph_turn"]
BUILD_GRAPH_SIGNATURE = (
    "(model_name: 'str', temperature: 'float', profile_id: 'str' = 'default', "
    "profile_store: 'UserProfileStore | None' = None, episode_store: "
    "'EpisodeStore | None' = None, project_policy: 'ProjectPolicySnapshot | None' "
    "= None, router_model_name: 'str | None' = None, router_max_tokens: 'int' "
    "= 500, response_max_tokens: 'int' = 800, task_token_budget: 'int' = 20000, "
    "timeout_seconds: 'float' = 30.0, trace_recorder: 'TraceRecorder | None' = None)"
)


def test_graph_public_surface_is_characterized():
    assert graph.__all__ == PUBLIC_EXPORTS
    assert str(inspect.signature(graph.build_graph)) == BUILD_GRAPH_SIGNATURE
    assert str(inspect.signature(graph.invoke_graph_turn)) == "(app, invocation: 'dict')"
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(graph, name)


def test_invoke_graph_turn_translates_keyboard_interrupt():
    class InterruptedApp:
        def invoke(self, invocation):
            raise KeyboardInterrupt

    with pytest.raises(legacy_agent.AgentTurnInterrupted):
        graph.invoke_graph_turn(InterruptedApp(), {"messages": []})
```

Keep the initially unused `hashlib`, `importlib`, and `SimpleNamespace` imports because later tasks in this same test module use them.

- [ ] **Step 2: Run the characterization tests against the original module**

Run:

```bash
pytest tests/test_graph_package.py -q
```

Expected: `2 passed`.

- [ ] **Step 3: Run the existing focused graph behavior**

Run:

```bash
pytest tests/test_graph_tracing.py tests/test_agent_gate.py -k "graph or plan_evaluator_blocks or deterministic_fallback or task_budget" -q
```

Expected: all selected graph tests pass except any test already included in the four documented baseline failures.

- [ ] **Step 4: Commit the graph guardrail**

```bash
git add tests/test_graph_package.py
git commit -m "test: characterize graph public behavior"
```

---

### Task 2: Convert `graph.py` to a Package Without Changing Graph Logic

**Files:**
- Delete: `scripts/netzoo_agent_core/graph.py`
- Create: `scripts/netzoo_agent_core/graph/__init__.py`
- Create: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_graph_package.py`
- Modify: `tests/test_graph_tracing.py`
- Modify: `tests/test_agent_module_boundaries.py`

**Interfaces:**
- Consumes: the complete current `graph.py` implementation.
- Produces: importable `netzoo_agent_core.graph` package and mechanically moved `graph.factory` implementation with unchanged behavior.

- [ ] **Step 1: Add failing package-structure tests**

Append:

```python
def test_graph_is_a_package_with_factory_child():
    assert hasattr(graph, "__path__")
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    assert factory.build_graph is graph.build_graph
    assert factory.invoke_graph_turn is graph.invoke_graph_turn


def test_graph_package_exports_only_public_entrypoints():
    assert graph.__all__ == PUBLIC_EXPORTS
```

- [ ] **Step 2: Run the package tests to verify the package assertion fails**

Run:

```bash
pytest tests/test_graph_package.py -k "package" -q
```

Expected: failure because the current module has no `__path__`.

- [ ] **Step 3: Create the package facade**

Use:

```python
"""LangGraph orchestration across policy, planning, execution, and evaluation."""

from . import factory
from .factory import build_graph, invoke_graph_turn

_GRAPH_IMPLEMENTATION_MODULES = (factory,)

__all__ = ["build_graph", "invoke_graph_turn"]
```

- [ ] **Step 4: Move the current module into `factory.py` mechanically**

Move the complete current `graph.py` content into `graph/factory.py`. Change relative imports from one dot to two dots, including:

```python
from ..contracts import AgentState, AgentTurnInterrupted
from ..memory import EpisodeStore, UserProfileStore
from ..planning import build_workflow_plan, render_plan
from ..evaluation import evaluate_step_result, evaluate_workflow_plan
```

Keep `build_graph`, all nested nodes, all prompt text, topology, and `invoke_graph_turn` unchanged in this task. Set:

```python
__all__ = ["build_graph", "invoke_graph_turn"]
```

- [ ] **Step 5: Register the private graph implementation tuple in the legacy facade**

Add one import:

```python
from netzoo_agent_core.graph import _GRAPH_IMPLEMENTATION_MODULES
```

Expand it immediately after `graph` in the existing tuple:

```python
    graph, *_GRAPH_IMPLEMENTATION_MODULES,
```

Keep `scripts/netzoo_agent.py` at or below 150 lines.

- [ ] **Step 6: Redirect tests that patch or inspect the implementation module**

In `tests/test_graph_tracing.py`, replace the implementation import with:

```python
import netzoo_agent_core.graph.factory as graph_module  # noqa: E402
from netzoo_agent_core.graph import build_graph  # noqa: E402
```

In `tests/test_agent_module_boundaries.py`, temporarily read the mechanically moved topology from:

```python
graph_source = (CORE_ROOT / "graph" / "factory.py").read_text(encoding="utf-8")
```

- [ ] **Step 7: Run package, boundary, tracing, and graph integration tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_graph_tracing.py tests/test_agent_module_boundaries.py -q
pytest tests/test_agent_gate.py -k "graph or plan_evaluator_blocks or deterministic_fallback or task_budget" -q
```

Expected: all selected tests pass, public signatures remain exact, and the recovery topology assertion still passes.

- [ ] **Step 8: Commit the mechanical package conversion**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/graph tests/test_graph_package.py tests/test_graph_tracing.py tests/test_agent_module_boundaries.py
git commit -m "refactor: convert graph module to package"
```

---

### Task 3: Extract Graph Context, Budget Preflight, and Prompts

**Files:**
- Create: `scripts/netzoo_agent_core/graph/context.py`
- Create: `scripts/netzoo_agent_core/graph/prompts.py`
- Modify: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent_core/graph/__init__.py`
- Modify: `tests/test_graph_package.py`

**Interfaces:**
- Consumes: validated graph-lifetime dependencies created by `factory.py`.
- Produces: frozen `_GraphContext`, `record_event`, `preflight_budget`, `_GraphPrompts`, and `build_graph_prompts`.

- [ ] **Step 1: Add failing prompt and context tests**

Append:

```python
RESPONSE_PROMPT_SHA256 = "7a93cdf9d10628fcb8de5c7b6c292bb40c6b7b97da0e924e858fa805f9f6a8a0"


def test_response_prompt_is_byte_characterized(monkeypatch):
    prompts = importlib.import_module("netzoo_agent_core.graph.prompts")
    monkeypatch.setattr(prompts, "EXECUTE_TOOLS", False)
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()

    result = prompts.build_graph_prompts(policy)

    assert hashlib.sha256(result.response.encode("utf-8")).hexdigest() == RESPONSE_PROMPT_SHA256
    assert result.routing == legacy_agent.build_routing_prompt(policy)


def test_record_event_uses_run_id_and_exact_payload():
    context_module = importlib.import_module("netzoo_agent_core.graph.context")
    calls = []
    runtime = SimpleNamespace(
        recorder=SimpleNamespace(
            append=lambda run_id, event_type, node, payload: calls.append(
                (run_id, event_type, node, payload)
            )
        )
    )

    context_module.record_event(
        runtime,
        {"run_id": "run-1"},
        "plan.created",
        "plan",
        {"status": "ready"},
    )

    assert calls == [
        ("run-1", "plan.created", "plan", {"status": "ready"})
    ]
```

- [ ] **Step 2: Run the new tests to verify child-module imports fail**

Run:

```bash
pytest tests/test_graph_package.py -k "response_prompt or record_event" -q
```

Expected: import failures for `graph.prompts` and `graph.context`.

- [ ] **Step 3: Define `_GraphContext`**

Create `context.py` with:

```python
from dataclasses import dataclass
from typing import Any

from ..contracts import AgentState, ProjectPolicySnapshot
from ..memory import EpisodeStore, UserProfileStore
from ..llm import _estimated_tokens, evaluate_budget_call
from ..pricing import PriceCatalog
from ..tracing import NullTraceRecorder, TraceRecorder

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _GraphContext:
    profile_id: str
    profile_store: UserProfileStore
    episode_store: EpisodeStore
    project_policy: ProjectPolicySnapshot
    recorder: TraceRecorder | NullTraceRecorder
    price_catalog: PriceCatalog
    router: Any
    response_llm: Any
    router_model_name: str
    response_model_name: str
    routing_prompt: str
    response_prompt: str
    router_max_tokens: int
    response_max_tokens: int
    task_token_budget: int
```

- [ ] **Step 4: Move recording and budget logic into context helpers**

Implement:

```python
def record_event(
    context: _GraphContext,
    state: AgentState,
    event_type: str,
    node: str,
    payload: dict,
) -> None:
    context.recorder.append(state.get("run_id"), event_type, node, payload)
```

Move the exact current `preflight_budget` body from `factory.py` into:

```python
def preflight_budget(
    context: _GraphContext,
    state: AgentState,
    *,
    role: str,
    model: str,
    input_text: str,
    reserved_output_tokens: int,
    allow_reserve: bool,
):
```

Replace `task_token_budget` with `context.task_token_budget` and replace each nested `record` call with `record_event(context, state, event_type, node, payload)`. Preserve warning deduplication and returned `(decision, emitted)` exactly.

- [ ] **Step 5: Move prompt construction into `prompts.py`**

Create:

```python
from dataclasses import dataclass

from ..contracts import EXECUTE_TOOLS, ProjectPolicySnapshot, output_language_policy
from ..llm import build_routing_prompt

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _GraphPrompts:
    routing: str
    response: str


def build_graph_prompts(project_policy: ProjectPolicySnapshot) -> _GraphPrompts:
```

Move the response f-string from the original `graph.py` lines 152 through 197 byte-for-byte into `build_graph_prompts`. Return:

```python
    return _GraphPrompts(
        routing=build_routing_prompt(project_policy),
        response=response_prompt,
    )
```

- [ ] **Step 6: Construct and use context in the factory**

After LLM and prompt construction, create:

```python
    prompts = build_graph_prompts(project_policy)
    context = _GraphContext(
        profile_id=profile_id,
        profile_store=profile_store,
        episode_store=episode_store,
        project_policy=project_policy,
        recorder=recorder,
        price_catalog=price_catalog,
        router=router,
        response_llm=response_llm,
        router_model_name=router_model_name,
        response_model_name=model_name,
        routing_prompt=prompts.routing,
        response_prompt=prompts.response,
        router_max_tokens=router_max_tokens,
        response_max_tokens=response_max_tokens,
        task_token_budget=task_token_budget,
    )
```

Replace nested `record` calls with `record_event` using the original event type, node, and payload arguments. Replace nested `preflight_budget` calls with the context helper using the original role, model, input text, reserved output tokens, and reserve flag. Remove the two nested helper definitions. Keep node bodies nested during this task.

- [ ] **Step 7: Register the new internal modules**

Extend the package private tuple:

```python
_GRAPH_IMPLEMENTATION_MODULES = (context, factory, prompts)
```

All internal modules use `__all__: list[str] = []`; `factory.py` retains the two public exports.

- [ ] **Step 8: Run prompt, package, tracing, and budget tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
pytest tests/test_agent_gate.py -k "graph or task_budget" -q
```

Expected: all selected tests pass and the response prompt digest remains exact.

- [ ] **Step 9: Commit context and prompt extraction**

```bash
git add scripts/netzoo_agent_core/graph/context.py scripts/netzoo_agent_core/graph/prompts.py scripts/netzoo_agent_core/graph/factory.py scripts/netzoo_agent_core/graph/__init__.py tests/test_graph_package.py
git commit -m "refactor: extract graph context and prompts"
```

---

### Task 4: Extract Policy, Memory, Routing, and Planning Nodes

**Files:**
- Create: `scripts/netzoo_agent_core/graph/policy_memory.py`
- Create: `scripts/netzoo_agent_core/graph/routing_planning.py`
- Modify: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent_core/graph/__init__.py`
- Modify: `tests/test_graph_package.py`

**Interfaces:**
- Consumes: `_GraphContext`, `AgentState`, `record_event`, and `preflight_budget`.
- Produces: `apply_project_policy`, `retrieve_memory`, `consolidate_memory`, `classify_task`, and `plan_task`, each with `(context, state) -> dict` internal interface.

- [ ] **Step 1: Add failing child-module and patch-propagation tests**

Append:

```python
def test_policy_memory_and_routing_planning_modules_are_internal():
    policy_memory = importlib.import_module("netzoo_agent_core.graph.policy_memory")
    routing_planning = importlib.import_module(
        "netzoo_agent_core.graph.routing_planning"
    )
    assert policy_memory.__all__ == []
    assert routing_planning.__all__ == []
    assert not hasattr(graph, "classify_task")
    assert not hasattr(graph, "plan_task")


def test_legacy_plan_patch_reaches_routing_planning_child():
    routing_planning = importlib.import_module(
        "netzoo_agent_core.graph.routing_planning"
    )
    original = legacy_agent.build_workflow_plan

    def replacement(raw_decision, task, profile=None, retrieved_episodes=None, project_policy=None):
        raise AssertionError("patch propagation sentinel")

    try:
        legacy_agent.build_workflow_plan = replacement
        assert routing_planning.build_workflow_plan is replacement
    finally:
        legacy_agent.build_workflow_plan = original
```

- [ ] **Step 2: Run the child tests to verify imports fail**

Run:

```bash
pytest tests/test_graph_package.py -k "policy_memory or routing_planning or plan_patch" -q
```

Expected: import failures for both new modules.

- [ ] **Step 3: Move policy and memory nodes**

Create `policy_memory.py` and relocate the exact current bodies for:

```python
def apply_project_policy(context: _GraphContext, state: AgentState) -> dict:
def retrieve_memory(context: _GraphContext, state: AgentState) -> dict:
def consolidate_memory(context: _GraphContext, state: AgentState) -> dict:
```

Replace closure variables with these exact context fields:

```python
context.project_policy
context.profile_store
context.profile_id
context.episode_store
```

Replace event recording with `record_event`, passing context and state before the original event type, node, and payload. Preserve return dictionaries and memory storage side effects exactly.

- [ ] **Step 4: Move classification and planning nodes**

Create `routing_planning.py` and relocate the exact current bodies for:

```python
def classify_task(context: _GraphContext, state: AgentState) -> dict:
def plan_task(context: _GraphContext, state: AgentState) -> dict:
```

Use these context fields in place of closure variables:

```python
context.routing_prompt
context.router
context.router_model_name
context.router_max_tokens
context.task_token_budget
context.price_catalog
context.profile_store
```

Call `preflight_budget` with context, state, and the original keyword arguments. Call `record_event` with context and state before the original event arguments. Preserve provider fallback, fatal exception handling, token accounting, preference confirmation, trace output, and state updates exactly.

- [ ] **Step 5: Bind extracted nodes in the existing factory topology**

Import `partial` and replace registrations with:

```python
recorder.instrument_node(
    "apply_project_policy",
    partial(apply_project_policy, context),
)
```

Use the same binding for `retrieve_memory`, `classify_task`, `plan_task`, and `consolidate_memory`. Do not change node registration names or order.

- [ ] **Step 6: Register both child modules**

Extend `_GRAPH_IMPLEMENTATION_MODULES` to include `policy_memory` and `routing_planning`. Keep both internal `__all__` lists empty.

- [ ] **Step 7: Run package, facade, tracing, fallback, and planning tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
pytest tests/test_agent_gate.py -k "graph or preferred_workflow or deterministic_fallback or plan_evaluator" -q
```

Expected: all selected tests pass except the documented recovered-plan baseline failure when selected by the expression.

- [ ] **Step 8: Commit the first node clusters**

```bash
git add scripts/netzoo_agent_core/graph/policy_memory.py scripts/netzoo_agent_core/graph/routing_planning.py scripts/netzoo_agent_core/graph/factory.py scripts/netzoo_agent_core/graph/__init__.py tests/test_graph_package.py
git commit -m "refactor: extract graph policy and planning nodes"
```

---

### Task 5: Extract Execution Nodes and Conditional Transitions

**Files:**
- Create: `scripts/netzoo_agent_core/graph/execution.py`
- Create: `scripts/netzoo_agent_core/graph/transitions.py`
- Modify: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent_core/graph/__init__.py`
- Modify: `tests/test_graph_package.py`

**Interfaces:**
- Consumes: `_GraphContext`, `AgentState`, plan and evaluation contracts.
- Produces: four execution-stage nodes and two state-only conditional transition functions.

- [ ] **Step 1: Add failing module and executor-patch tests**

Append:

```python
def test_execution_and_transition_modules_are_internal():
    execution = importlib.import_module("netzoo_agent_core.graph.execution")
    transitions = importlib.import_module("netzoo_agent_core.graph.transitions")
    assert execution.__all__ == []
    assert transitions.__all__ == []
    assert not hasattr(graph, "execute_tool")
    assert not hasattr(graph, "route_evaluation")


def test_legacy_executor_patch_reaches_graph_execution_child():
    execution = importlib.import_module("netzoo_agent_core.graph.execution")
    original = legacy_agent.execute_selected_tool

    def replacement(decision):
        return "patch propagation sentinel"

    try:
        legacy_agent.execute_selected_tool = replacement
        assert execution.execute_selected_tool is replacement
    finally:
        legacy_agent.execute_selected_tool = original
```

- [ ] **Step 2: Run the new tests to verify imports fail**

Run:

```bash
pytest tests/test_graph_package.py -k "execution_and_transition or executor_patch" -q
```

Expected: import failures for `graph.execution` and `graph.transitions`.

- [ ] **Step 3: Move execution-stage nodes**

Create `execution.py` and relocate exact bodies into:

```python
def evaluate_plan(context: _GraphContext, state: AgentState) -> dict:
def execute_tool(context: _GraphContext, state: AgentState) -> dict:
def evaluate_result(context: _GraphContext, state: AgentState) -> dict:
def recover(context: _GraphContext, state: AgentState) -> dict:
```

Use `context.project_policy` only where the current state lookup does not already supply policy. Preserve all current state lookups, decision mutation, step argument application, `EXECUTE_TOOLS` mode reporting, result structuring, recovery count, failure supersession, and event payloads. Replace event recording with `record_event`, passing context and state before the original event arguments.

- [ ] **Step 4: Move conditional route functions**

Create `transitions.py` with exact state-only functions:

```python
def route_plan_evaluation(state: AgentState) -> str:
    plan = WorkflowPlan.model_validate(state["plan"])
    evaluation = PlanEvaluationResult.model_validate(state["plan_evaluation"])
    return (
        "execute_tool"
        if evaluation.status == "approved" and plan.status == "ready" and plan.steps
        else "consolidate_memory"
    )


def route_evaluation(state: AgentState) -> str:
    status = state["evaluation"]["status"]
    if status == "continue":
        return "execute_tool"
    if status == "replan":
        return "recover"
    return "consolidate_memory"
```

- [ ] **Step 5: Bind execution nodes and use extracted transitions**

In the still-inline topology, bind the four nodes with `partial(function, context)`. Pass `route_plan_evaluation` and `route_evaluation` directly to conditional-edge registration. Preserve mapping dictionaries exactly.

- [ ] **Step 6: Register both child modules**

Add `execution` and `transitions` to `_GRAPH_IMPLEMENTATION_MODULES` and keep internal `__all__` lists empty.

- [ ] **Step 7: Run package, evaluator-gate, execution-loop, and recovery tests**

Run:

```bash
pytest tests/test_graph_package.py -q
pytest tests/test_agent_gate.py -k "graph_runs_plan_execute_evaluate_loop or plan_evaluator_blocks or recovery or header_failure" -q
```

Expected: extracted-node tests pass; only the documented recovered-plan baseline failure may remain.

- [ ] **Step 8: Commit execution and transition extraction**

```bash
git add scripts/netzoo_agent_core/graph/execution.py scripts/netzoo_agent_core/graph/transitions.py scripts/netzoo_agent_core/graph/factory.py scripts/netzoo_agent_core/graph/__init__.py tests/test_graph_package.py
git commit -m "refactor: extract graph execution nodes"
```

---

### Task 6: Extract the Response Node

**Files:**
- Create: `scripts/netzoo_agent_core/graph/response.py`
- Modify: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent_core/graph/__init__.py`
- Modify: `tests/test_graph_package.py`

**Interfaces:**
- Consumes: `_GraphContext`, `AgentState`, response renderers, typed plan/result/evaluation models, and response LLM helpers.
- Produces: `respond(context: _GraphContext, state: AgentState) -> dict`.

- [ ] **Step 1: Add failing response-module and patch tests**

Append:

```python
def test_response_module_is_internal():
    response = importlib.import_module("netzoo_agent_core.graph.response")
    assert response.__all__ == []
    assert not hasattr(graph, "respond")


def test_legacy_response_helper_patch_reaches_response_child():
    response = importlib.import_module("netzoo_agent_core.graph.response")
    original = legacy_agent.build_response_messages

    def replacement(system_prompt, trusted_context, user_task, tool_result):
        return []

    try:
        legacy_agent.build_response_messages = replacement
        assert response.build_response_messages is replacement
    finally:
        legacy_agent.build_response_messages = original
```

- [ ] **Step 2: Run the response tests to verify the module import fails**

Run:

```bash
pytest tests/test_graph_package.py -k "response_module or response_helper_patch" -q
```

Expected: import failure for `graph.response`.

- [ ] **Step 3: Move the response node as one cohesive module**

Create `response.py` and move the exact current response body into:

```python
def respond(context: _GraphContext, state: AgentState) -> dict:
```

Replace closure values with:

```python
context.project_policy
context.response_prompt
context.response_llm
context.response_model_name
context.response_max_tokens
context.task_token_budget
context.price_catalog
```

Use `preflight_budget` with context, state, and the original response-budget keyword arguments. Use `record_event` with context and state before the original response event arguments. Preserve response precedence, trusted-context text, raw-result treatment, budget fallback copy, provider fallback copy, token accounting, follow-up stripping, traces, and returned state update exactly.

- [ ] **Step 4: Bind the extracted response node**

Replace the nested response registration with:

```python
graph.add_node(
    "respond",
    context.recorder.instrument_node("respond", partial(respond, context)),
)
```

- [ ] **Step 5: Register the response child module**

Add `response` to `_GRAPH_IMPLEMENTATION_MODULES`; keep `response.__all__` empty.

- [ ] **Step 6: Run package, response, budget, and tracing tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_graph_tracing.py -q
pytest tests/test_agent_gate.py -k "guidance_response or response_model or task_budget or graph" -q
```

Expected: all selected tests pass and response prompt digest remains unchanged.

- [ ] **Step 7: Commit response extraction**

```bash
git add scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/graph/factory.py scripts/netzoo_agent_core/graph/__init__.py tests/test_graph_package.py
git commit -m "refactor: extract graph response node"
```

---

### Task 7: Extract Topology and Reduce the Factory to Dependency Assembly

**Files:**
- Create: `scripts/netzoo_agent_core/graph/topology.py`
- Modify: `scripts/netzoo_agent_core/graph/factory.py`
- Modify: `scripts/netzoo_agent_core/graph/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_graph_package.py`
- Modify: `tests/test_agent_module_boundaries.py`

**Interfaces:**
- Consumes: `_GraphContext` and all extracted node and transition functions.
- Produces: `ensure_graph_dependencies()` and `compile_graph(context, graph_cls)` plus a final small public factory.

- [ ] **Step 1: Add failing exact-topology and final-locality tests**

Append:

```python
class _FakeRecorder:
    def __init__(self):
        self.instrumented = []

    def instrument_node(self, name, function):
        self.instrumented.append(name)
        return function


class _FakeStateGraph:
    instance = None

    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = []
        self.edges = []
        self.conditionals = []
        _FakeStateGraph.instance = self

    def add_node(self, name, function):
        self.nodes.append(name)

    def add_edge(self, source, target):
        self.edges.append((source, target))

    def add_conditional_edges(self, source, router, mapping):
        self.conditionals.append((source, router.__name__, mapping))

    def compile(self):
        return self


def test_topology_is_exact_and_fully_instrumented(monkeypatch):
    topology = importlib.import_module("netzoo_agent_core.graph.topology")
    recorder = _FakeRecorder()
    runtime = SimpleNamespace(recorder=recorder)
    monkeypatch.setattr(topology, "START", "START")
    monkeypatch.setattr(topology, "END", "END")

    compiled = topology.compile_graph(runtime, graph_cls=_FakeStateGraph)

    expected_nodes = [
        "apply_project_policy",
        "retrieve_memory",
        "classify",
        "plan",
        "evaluate_plan",
        "execute_tool",
        "evaluate",
        "recover",
        "consolidate_memory",
        "respond",
    ]
    assert compiled.nodes == expected_nodes
    assert recorder.instrumented == expected_nodes
    assert compiled.edges == [
        ("START", "apply_project_policy"),
        ("apply_project_policy", "retrieve_memory"),
        ("retrieve_memory", "classify"),
        ("classify", "plan"),
        ("plan", "evaluate_plan"),
        ("execute_tool", "evaluate"),
        ("recover", "evaluate_plan"),
        ("consolidate_memory", "respond"),
        ("respond", "END"),
    ]
    assert compiled.conditionals == [
        (
            "evaluate_plan",
            "route_plan_evaluation",
            {
                "execute_tool": "execute_tool",
                "consolidate_memory": "consolidate_memory",
            },
        ),
        (
            "evaluate",
            "route_evaluation",
            {
                "execute_tool": "execute_tool",
                "recover": "recover",
                "consolidate_memory": "consolidate_memory",
            },
        ),
    ]


def test_factory_is_dependency_assembly_only():
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    source = inspect.getsource(factory)
    assert len(source.splitlines()) <= 150
    assert "_GraphContext(" in source
    assert "compile_graph(" in source
    assert "def classify_task" not in source
    assert "def respond" not in source
    assert "add_edge" not in source


def test_graph_children_remain_responsibility_sized():
    maximum_lines = {
        "context": 140,
        "execution": 230,
        "factory": 150,
        "policy_memory": 150,
        "prompts": 120,
        "response": 260,
        "routing_planning": 230,
        "topology": 130,
        "transitions": 70,
    }
    for module_name, maximum in maximum_lines.items():
        module = importlib.import_module(f"netzoo_agent_core.graph.{module_name}")
        assert len(inspect.getsource(module).splitlines()) <= maximum, module_name


def test_graph_internal_helpers_do_not_leak():
    for name in (
        "_GraphContext",
        "apply_project_policy",
        "classify_task",
        "execute_tool",
        "respond",
        "route_evaluation",
        "compile_graph",
    ):
        assert not hasattr(graph, name)
```

- [ ] **Step 2: Run the final topology tests to verify they fail**

Run:

```bash
pytest tests/test_graph_package.py -k "topology_is_exact or dependency_assembly or internal_helpers" -q
```

Expected: import failure for `graph.topology` and factory-size failure.

- [ ] **Step 3: Create dependency guard and exact topology**

Create `topology.py` with internal imports for all nodes and transitions. Implement:

```python
def ensure_graph_dependencies() -> None:
    if StateGraph is None or HumanMessage is None or SystemMessage is None:
        raise RuntimeError(
            "LangChain/LangGraph dependencies are required to run the LLM agent. "
            "Install the project environment or use the Docker image."
        )
```

Implement:

```python
def compile_graph(context: _GraphContext, *, graph_cls=StateGraph):
```

Construct `graph_cls(AgentState)`, bind every node with `partial(node, context)`, instrument every node with `context.recorder.instrument_node`, register the ten nodes in exact order, add the nine ordinary edges and two conditional mappings from the characterization test, and return `graph.compile()`.

- [ ] **Step 4: Replace the factory body with final dependency assembly**

The final `build_graph` keeps its exact signature. Its body performs only:

1. `ensure_graph_dependencies()` before stores or providers are created;
2. default store and policy construction;
3. policy validation;
4. model validation;
5. router and response LLM construction;
6. structured router construction;
7. prompt and context construction;
8. `compile_graph(context, graph_cls=StateGraph)`.

Keep `StateGraph` imported in `factory.py` so existing graph tracing tests can skip and patch the implementation owner. Keep this exact public adapter:

```python
def invoke_graph_turn(app, invocation: dict):
    """Invoke one graph turn without leaking a Ctrl-C traceback to the CLI."""
    try:
        return app.invoke(invocation)
    except KeyboardInterrupt as error:
        raise AgentTurnInterrupted from error
```

- [ ] **Step 5: Finalize the private compatibility tuple**

In `graph/__init__.py`, import all child modules and define:

```python
_GRAPH_IMPLEMENTATION_MODULES = (
    context,
    execution,
    factory,
    policy_memory,
    prompts,
    response,
    routing_planning,
    topology,
    transitions,
)
```

Keep only `build_graph` and `invoke_graph_turn` in package `__all__`. Confirm the legacy facade still expands this tuple and remains at or below 150 lines.

- [ ] **Step 6: Move the source-based recovery assertion to topology**

Change `tests/test_agent_module_boundaries.py` to:

```python
graph_source = (CORE_ROOT / "graph" / "topology.py").read_text(encoding="utf-8")
```

Keep its positive `recover -> evaluate_plan` and negative `recover -> execute_tool` assertions unchanged.

- [ ] **Step 7: Run final package, topology, boundary, tracing, and integration tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_agent_module_boundaries.py tests/test_graph_tracing.py -q
pytest tests/test_agent_gate.py -k "graph or plan_evaluator or deterministic_fallback or task_budget or recovery" -q
```

Expected: package, topology, prompt digest, facade, tracing, and graph integration tests pass except the one documented recovered-plan baseline failure when selected.

- [ ] **Step 8: Commit topology and final factory**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/graph/topology.py scripts/netzoo_agent_core/graph/factory.py scripts/netzoo_agent_core/graph/__init__.py tests/test_graph_package.py tests/test_agent_module_boundaries.py
git commit -m "refactor: extract graph topology and factory"
```

---

### Task 8: Verify the Full Baseline, Dependency Direction, and Repository Hygiene

**Files:**
- Verify: `scripts/netzoo_agent_core/graph/`
- Verify: `scripts/netzoo_agent.py`
- Verify: `tests/test_graph_package.py`
- Verify: existing graph, tracing, CLI, and full-suite tests
- Verify only: unrelated dirty-worktree entries

**Interfaces:**
- Consumes: the completed graph package.
- Produces: evidence that behavior, compatibility, topology, and repository scope meet the approved specification.

- [ ] **Step 1: Check final file sizes and compilation**

Run:

```bash
wc -l scripts/netzoo_agent_core/graph/*.py scripts/netzoo_agent.py
python -m compileall -q scripts/netzoo_agent_core/graph scripts/netzoo_agent.py
```

Expected: `factory.py` is at most 150 lines, the facade is at most 150 lines, no child recreates the original monolith, and compilation succeeds.

- [ ] **Step 2: Run graph-specific and planning-adjacent tests**

Run:

```bash
pytest tests/test_graph_package.py tests/test_graph_tracing.py tests/test_agent_module_boundaries.py tests/test_agent_gate.py tests/test_agent_stability.py -q
```

Expected: no new failures beyond the same four documented baseline failures.

- [ ] **Step 3: Run the clean full baseline with known failures deselected**

Run:

```bash
pytest -q -k 'not test_clarification_marker_preserves_previous_action_against_reroute and not test_clarification_wizard_selects_each_missing_field_independently and not test_recovered_plan_is_authorized_by_the_same_plan_evaluator and not test_selected_input_keeps_selected_provenance_after_replanning'
```

Expected: all selected tests pass; 12 tests remain skipped and four are deselected. The passed count is at least 254 plus the new graph package tests.

- [ ] **Step 4: Run the unfiltered full suite**

Run:

```bash
pytest -q
```

Expected: exactly the same four known failures, 12 skipped tests, and no new failures.

- [ ] **Step 5: Verify package dependency direction is acyclic**

Run:

```bash
rg -n "^from \.|^from \.\." scripts/netzoo_agent_core/graph
```

Expected direction:

```text
__init__ -> child registration and factory exports
factory -> context, prompts, topology, existing lower-level modules
topology -> context, nodes, transitions
nodes -> context and existing lower-level domain modules
transitions -> contracts
context -> contracts, memory, pricing, tracing, llm
prompts -> contracts, llm
```

No node imports factory, topology, or the package facade. No cycle exists.

- [ ] **Step 6: Verify commit range, whitespace, staging, and unrelated changes**

Run:

```bash
git diff --check 4fbcaec..HEAD
git diff --cached --name-only
git status --short
git log --oneline 4fbcaec..HEAD
```

Expected: no whitespace errors, an empty staging area after implementation commits, and unchanged unrelated dirty-worktree entries.

- [ ] **Step 7: Report final evidence**

Report child file list and line counts, public-interface result, response prompt digest, topology result, facade patch tests, graph-focused result, clean full baseline, unfiltered full baseline, known failures, and implementation commit hashes. Do not create an empty verification commit.
