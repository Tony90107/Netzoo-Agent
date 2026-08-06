# Graph Package Refactor Design

## Status

Approved design, pending implementation planning.

## Context

`scripts/netzoo_agent_core/graph.py` currently contains 892 lines. Its public interface is only `build_graph()` and `invoke_graph_turn()`, but `build_graph()` spans 780 lines and defines the complete runtime as nested closures.

The function currently owns all of these responsibilities:

- validating response and router models;
- loading and validating project policy;
- creating profile and episode stores;
- creating the trace recorder and price catalog;
- constructing router and response LLMs;
- constructing routing and response prompts;
- enforcing token-budget preflight decisions;
- applying project policy to graph state;
- retrieving and consolidating memory;
- classifying user tasks;
- constructing workflow plans;
- evaluating plans before execution;
- executing and evaluating workflow steps;
- constructing recovery plans;
- producing deterministic or LLM-generated responses;
- registering graph nodes and edges;
- compiling the LangGraph application;
- translating `KeyboardInterrupt` at the CLI seam.

The nested functions share a large closure containing models, stores, policy, prompts, budget settings, tracing, and pricing. This makes individual nodes difficult to locate and test without building the entire graph. The refactor will replace the module with a package whose internal seams correspond to graph responsibilities while preserving the exact LangGraph interface and behavior.

## Goals

- Make every graph node easy to locate by responsibility.
- Separate graph topology from node implementation.
- Replace the 780-line closure with explicit internal dependency passing.
- Keep the public graph interface unchanged.
- Preserve node names, edges, state updates, trace events, prompts, fallback behavior, and execution authority.
- Preserve dependency patching through the legacy `netzoo_agent` facade.
- Allow topology and node behavior to be tested without executing unrelated stages.

## Non-goals

- Changing `AgentState` or any public contract model.
- Changing graph node names, ordering, conditional routes, or recovery rules.
- Changing router or response prompts.
- Changing budget thresholds, token accounting, pricing, or warning behavior.
- Changing planning, evaluation, execution, memory, or response policy.
- Fixing the four known baseline test failures.
- Adding public node interfaces, a plugin system, abstract base classes, or a general graph extension framework.
- Refactoring `cli.py` or other unrelated modules.

## Chosen Approach

Replace `graph.py` with a responsibility-oriented `graph/` package. Public callers continue to import two functions from `netzoo_agent_core.graph`. Internally, graph dependencies are stored in a frozen `_GraphContext`, nodes are ordinary functions that accept the context and state, and topology binds the context before registering nodes with LangGraph.

This approach was selected over retaining one module with top-level functions because a single file would still mix prompt construction, dependency assembly, nodes, transitions, and topology. It was selected over splitting only the topology because the nested node closure is the primary locality and testability problem.

## Package Structure

```text
scripts/netzoo_agent_core/graph/
  __init__.py
  factory.py
  context.py
  prompts.py
  policy_memory.py
  routing_planning.py
  execution.py
  response.py
  transitions.py
  topology.py
```

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Stable public facade and private child-module registration tuple. |
| `factory.py` | Validate configuration, create runtime dependencies, build `_GraphContext`, compile the graph, and translate `KeyboardInterrupt`. |
| `context.py` | Define `_GraphContext`, trace event recording, and token-budget preflight. |
| `prompts.py` | Build the routing prompt and the exact existing response system prompt. |
| `policy_memory.py` | Apply project policy, retrieve profile and episodes, and consolidate terminal episodes. |
| `routing_planning.py` | Classify tasks, handle router fallback, build plans, and apply pending preference confirmation. |
| `execution.py` | Evaluate plans, execute steps, evaluate results, and construct recovery state updates. |
| `response.py` | Produce needs-input, confirmation, rejected-plan, execution, budget fallback, provider fallback, or response-model output. |
| `transitions.py` | Select conditional routes after plan evaluation and step evaluation. |
| `topology.py` | Bind context to nodes, instrument nodes, define every edge, and compile the graph. |

Target sizes are review guides rather than runtime constraints:

- `factory.py`: about 120 to 150 lines;
- `context.py`: below about 120 lines;
- `prompts.py`: below about 100 lines;
- `policy_memory.py`: below about 130 lines;
- `routing_planning.py`: about 200 lines;
- `execution.py`: about 200 lines;
- `response.py`: about 220 lines;
- `transitions.py`: below about 50 lines;
- `topology.py`: below about 100 lines.

No final child module should contain multiple unrelated node clusters, and no replacement for the original 780-line closure may be introduced.

## Public Interface

The package public surface remains:

```python
__all__ = ["build_graph", "invoke_graph_turn"]
```

The existing `build_graph` parameters and defaults remain exact:

```python
def build_graph(
    model_name: str,
    temperature: float,
    profile_id: str = "default",
    profile_store: UserProfileStore | None = None,
    episode_store: EpisodeStore | None = None,
    project_policy: ProjectPolicySnapshot | None = None,
    router_model_name: str | None = None,
    router_max_tokens: int = DEFAULT_ROUTER_MAX_TOKENS,
    response_max_tokens: int = DEFAULT_RESPONSE_MAX_TOKENS,
    task_token_budget: int = DEFAULT_TASK_TOKEN_BUDGET,
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS,
    trace_recorder: TraceRecorder | None = None,
):
    pass
```

`invoke_graph_turn(app, invocation: dict)` also remains unchanged. No internal context, node, transition, prompt, or topology helper is re-exported by the package facade.

## Internal Context

`context.py` defines a frozen, slotted `_GraphContext`. It contains only graph-lifetime dependencies and configuration, including:

- profile ID;
- profile and episode stores;
- validated project policy;
- trace recorder;
- price catalog;
- structured router callable and response LLM;
- validated router and response model names;
- routing and response prompts;
- router and response output-token limits;
- task token budget.

It does not contain mutable per-turn `AgentState` data. Every node receives state separately.

The internal node interface is:

```python
def node(context: _GraphContext, state: AgentState) -> dict:
    pass
```

Topology binds context with `functools.partial`, so LangGraph continues to receive a callable with the existing effective interface:

```python
def node(state: AgentState) -> dict:
    pass
```

The context module also owns the two operations shared across node clusters:

```python
def record_event(
    context: _GraphContext,
    state: AgentState,
    event_type: str,
    node: str,
    payload: dict,
) -> None:
    pass
```

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
    pass
```

These are private implementation seams. They are absent from the package `__all__`.

## Dependency Direction

```text
callers
  -> graph/__init__.py
       -> factory.py
            -> context.py
            -> prompts.py
            -> topology.py
                 -> policy_memory.py
                 -> routing_planning.py
                 -> execution.py
                 -> response.py
                 -> transitions.py
       -> private child-module tuple for legacy patch propagation
```

Node modules may depend on `_GraphContext` and existing lower-level domain modules. Node modules do not import `factory.py`, `topology.py`, or the package facade. `context.py` does not import node modules. `topology.py` binds nodes but contains no domain decisions.

## Graph Data Flow

The topology remains exact:

```text
START
  -> apply_project_policy
  -> retrieve_memory
  -> classify
  -> plan
  -> evaluate_plan
       -> approved and ready: execute_tool
       -> deferred or rejected: consolidate_memory
  -> execute_tool
  -> evaluate
       -> continue: execute_tool
       -> replan: recover
       -> terminal: consolidate_memory
  -> recover
  -> evaluate_plan
  -> consolidate_memory
  -> respond
  -> END
```

The recovery path must continue through the pre-execution plan evaluator. There is no direct `recover -> execute_tool` edge.

## State Update Invariants

Each node retains its exact state update shape:

| Node | State update |
| --- | --- |
| `apply_project_policy` | `project_policy` |
| `retrieve_memory` | `profile`, `retrieved_episodes` |
| `classify` | `decision`, `token_usage`, `budget_warnings` |
| `plan` | `plan`, `decision`, `current_step`, `tool_results`, `replan_count` |
| `evaluate_plan` | `plan_evaluation` |
| `execute_tool` | `tool_result`, appended `tool_results` |
| `evaluate` | `evaluation`, and `current_step` only when continuing |
| `recover` | recovered `plan`, `decision`, `current_step`, `replan_count`, superseded `tool_results` |
| `consolidate_memory` | empty update after any episode storage side effect |
| `respond` | `messages`, and response-path `token_usage` plus `budget_warnings` |

Node names, event node labels, trace stages, and state keys must not be renamed for internal consistency.

## Behavioral Invariants

The refactor preserves all current behavior:

- default profile and episode stores are created at graph build time;
- default project policy is loaded from `PROJECT_ROOT` at graph build time;
- project policy code validation occurs before graph compilation;
- router and response model allowlists are enforced at the same stage;
- router temperature remains zero;
- router structured output uses `RouterDecision`, function calling, and no raw output inclusion;
- routing and response prompts remain byte-for-byte equivalent for the same runtime settings;
- price catalog construction remains at graph build time;
- node instrumentation occurs for every registered node;
- trace event names, order, payload fields, and emission timing remain unchanged;
- budget warning deduplication remains unchanged;
- no provider call occurs after a blocked budget decision;
- preference confirmation continues to clear executable steps;
- plan evaluation continues to gate every ready plan before execution;
- execution continues to use only the current planned step and its arguments;
- recovery continues to increment the bounded replan count and supersede the triggering failure;
- memory consolidation occurs only for terminal completed or failed evaluations with tool results;
- response rendering precedence remains needs input, preference confirmation, plan rejection, local execution response, then response-model path;
- CLI-owned trailing follow-up questions continue to be stripped;
- `EXECUTE_TOOLS` continues to affect prompts, trace payloads, and execution mode exactly as before.

## Error and Fallback Behavior

- If LangChain or LangGraph dependencies are unavailable, `build_graph()` raises the existing `RuntimeError` before creating runtime dependencies.
- Invalid router or response models raise at graph build time.
- Invalid project policy raises at graph build time.
- Router budget blocking skips the provider and uses deterministic routing fallback.
- Nonfatal router provider errors use deterministic routing fallback and record a failed LLM call.
- Fatal router provider errors are re-raised.
- Response budget blocking skips the provider and returns the existing deterministic budget message.
- Nonfatal response provider errors return the existing deterministic response and record a failed LLM call.
- Fatal response provider errors are re-raised.
- Policy, memory, planning, execution, evaluation, and trace storage failures are not hidden by a new broad exception handler.
- `invoke_graph_turn()` catches only `KeyboardInterrupt` and raises `AgentTurnInterrupted` from it.

## Legacy Facade Compatibility

Existing imports continue to work:

```python
from netzoo_agent_core.graph import build_graph, invoke_graph_turn
```

The legacy `scripts/netzoo_agent.py` facade continues to expose the same function objects.

The graph package defines a private tuple containing child implementation modules. The tuple is not part of `__all__`. The legacy facade expands it into its existing `_IMPLEMENTATION_MODULES` registry. This preserves assignment-based monkeypatch propagation for dependencies imported by child modules, including:

- `build_llm` in `factory.py`;
- `build_workflow_plan` in `routing_planning.py`;
- `execute_selected_tool` in `execution.py`;
- response rendering and LLM helpers in `response.py`.

Mutable runtime settings such as `PROJECT_ROOT` and `EXECUTE_TOOLS` continue to propagate through `set_runtime_value()` to every loaded graph child module containing that name.

The facade must remain at or below its existing 150-line boundary test.

## Testing Strategy

Add `tests/test_graph_package.py` for structural, topology, compatibility, and focused behavioral coverage.

Structural tests verify:

- `netzoo_agent_core.graph` imports as a package;
- every designed child module imports directly;
- package `__all__` contains exactly the two public functions;
- legacy facade public functions are identical to package functions;
- internal context, nodes, transitions, prompts, and topology helpers do not leak through the package facade;
- child implementation modules are registered for compatibility patching;
- final modules remain within their responsibility-oriented size guides.

Topology characterization verifies exact registration order for:

1. `apply_project_policy`;
2. `retrieve_memory`;
3. `classify`;
4. `plan`;
5. `evaluate_plan`;
6. `execute_tool`;
7. `evaluate`;
8. `recover`;
9. `consolidate_memory`;
10. `respond`.

It also verifies all ordinary edges and both conditional mapping dictionaries, including `recover -> evaluate_plan` and `respond -> END`.

Compatibility tests verify that facade patches reach the exact child module consuming each dependency. Runtime override tests verify that `PROJECT_ROOT` and `EXECUTE_TOOLS` reach graph children.

Behavioral verification retains and runs existing coverage for:

- missing dependency failure;
- `KeyboardInterrupt` translation;
- ordered trace recording;
- normal plan, execute, evaluate loop;
- plan evaluator rejection gate;
- deterministic router fallback;
- router budget blocking;
- response budget blocking;
- provider failure fallback;
- recovery loop through plan evaluation;
- interactive CLI integration using patched `build_graph`.

The existing source-based recovery topology assertion in `tests/test_agent_module_boundaries.py` moves from `graph.py` to `graph/topology.py` without weakening its requirement.

## Verification Baseline

The accepted full-suite baseline after the planning package refactor is:

- 254 tests passed;
- 12 tests skipped;
- 4 known failures.

The known failures remain:

- `test_clarification_marker_preserves_previous_action_against_reroute`;
- `test_clarification_wizard_selects_each_missing_field_independently`;
- `test_recovered_plan_is_authorized_by_the_same_plan_evaluator`;
- `test_selected_input_keeps_selected_provenance_after_replanning`.

Implementation acceptance requires a clean suite when those four tests are deselected. The unfiltered suite may contain only those same four failures. New graph package tests will increase the passed count.

## Acceptance Criteria

- `graph.py` is replaced by the designed package.
- `build_graph()` and `invoke_graph_turn()` retain their exact public interface.
- No graph node remains nested inside one monolithic factory function.
- Topology is readable in one focused file.
- Every node belongs to one responsibility-oriented module.
- `_GraphContext` contains graph-lifetime dependencies and no per-turn state.
- Node names, edges, conditional mappings, state updates, prompts, trace events, and fallback behavior remain unchanged.
- Legacy facade monkeypatching reaches every child implementation module.
- The legacy facade remains at or below 150 lines.
- Graph package tests pass.
- The clean baseline passes with the four known failures deselected.
- The unfiltered suite contains no new failures.
- No unrelated user changes are modified, staged, or committed.
