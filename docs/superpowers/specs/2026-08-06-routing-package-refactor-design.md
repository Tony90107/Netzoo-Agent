# Routing Package Refactor Design

**Date:** 2026-08-06

## Objective

Refactor `scripts/netzoo_agent_core/routing.py` from an 877-line module with
five unrelated responsibilities into a responsibility-oriented `routing/`
package. This is a structural refactor only: public imports, task authorization,
file discovery, retrieval behaviour, dispatch, result normalization, output
text, runtime overrides, and legacy monkeypatch behaviour must remain unchanged.

## Scope

This phase covers `scripts/netzoo_agent_core/routing.py`, the minimal legacy
facade registration needed for child-module monkeypatch propagation, and tests
that prove structure and compatibility.

Existing callers must continue to use the same interface:

```python
from netzoo_agent_core.routing import validate_task_text
import netzoo_agent as agent
```

`graph.py`, `planning.py`, `interpretation.py`, `cli.py`, and
`compatibility.py` must not import routing responsibility modules directly.

## Chosen Approach

Replace `routing.py` with a `routing/` package. The package initializer remains
the stable external seam and re-exports the complete historical `__all__`
surface in the same order.

```text
scripts/netzoo_agent_core/
└── routing/
    ├── __init__.py
    ├── capability.py
    ├── discovery.py
    ├── retrieval.py
    ├── dispatch.py
    └── results.py
```

Internal files are grouped by responsibility and dependency category, not by
line count.

### `routing/__init__.py`

Provides the stable package interface. It re-exports every name currently
listed in `routing.py.__all__`, including historical underscore-prefixed
helpers and constants. It contains no routing, retrieval, dispatch, or result
implementation.

### `routing/capability.py`

Owns deterministic task interpretation and authorization rules:

- workflow information-request recognition;
- goal and advisory capability inference;
- direct execution-intent recognition;
- task/action validation;
- Context7 library allow-list normalization;
- the final capability gate.

It also owns the constants consumed exclusively by these rules:
`MIN_TOOL_CONFIDENCE`, `CONTEXT7_LIBRARY_ALIASES`,
`UNSUPPORTED_DELIVERABLE_PATTERNS`, and `WORKFLOW_INFORMATION_PATTERNS`.

This module is pure in-process computation and must not import remote MCP or
local tool executors.

### `routing/discovery.py`

Owns local path parsing, candidate scoring, bounded filesystem discovery, and
default output-name construction:

- `_extract_named_path`;
- `_score_candidate_file`;
- `_find_candidate_files`;
- `_default_lioness_outputs`;
- `_default_network_output`.

It also owns `FILE_DISCOVERY_MAX_DEPTH`, `FILE_DISCOVERY_MAX_VISITED`, and
`FILE_DISCOVERY_MAX_RESULTS`. Existing symlink, depth, visited-file, result-count,
extension, and sorting rules remain unchanged.

### `routing/retrieval.py`

Owns read-only Context7 and Websearch MCP access, including response conversion,
exception flattening, MCP tool lookup, Context7 ID extraction, async operations,
sync wrappers, truncation, and first-URL extraction.

It owns `CONTEXT7_URL`, `CONTEXT7_MAX_CHARS`, `WEBSEARCH_URL`, and
`WEBSEARCH_MAX_CHARS`. It does not import or invoke local NetZoo executors.

### `routing/dispatch.py`

Owns only `execute_selected_tool`. It selects exactly one implementation from
the existing `LOCAL_TOOL_EXECUTORS` allow-list or one of the two read-only
retrieval functions. Unsupported actions continue to raise `ValueError`.

### `routing/results.py`

Owns executor-result normalization:

- expected artifact selection;
- diagnostic line extraction;
- success, dry-run, and failure classification;
- artifact existence validation;
- PUMA header recovery hints;
- private log persistence;
- raw-output truncation;
- construction of `ToolExecutionResult`.

It interprets completed tool output but never selects or executes a tool.

## Interfaces and Dependency Direction

The intended dependency direction is:

```text
callers → routing/__init__.py → capability
                            ├→ discovery
                            ├→ retrieval
                            ├→ dispatch → retrieval + execution
                            └→ results → artifact_validation + memory helpers
```

Responsibility modules may import existing contracts and their documented
dependencies. They must not import `routing/__init__.py`, preventing circular
dependencies.

The split respects dependency categories:

- `capability` is in-process computation;
- `discovery` uses bounded local filesystem access;
- `retrieval` is a true external dependency handled by existing MCP adapters;
- `dispatch` selects existing adapters at the execution seam;
- `results` combines in-process interpretation with bounded local log storage.

No new abstract base class or port will be introduced. Existing local and
remote implementations already vary at the dispatch seam, and the refactor does
not need another layer of indirection.

## Legacy Facade Compatibility

`scripts/netzoo_agent.py` currently propagates assignments and monkeypatches
through `_IMPLEMENTATION_MODULES`. After the split, routing child modules that
own historical exports must be registered in that tuple as well as the routing
package.

This preserves behaviours such as:

```python
with patch("netzoo_agent.query_web_search", return_value="https://example.test"):
    netzoo_agent.query_web_search_first_url("query")
```

The patched function must be visible inside `retrieval.py`, not only on the
package initializer. The same rule applies to patched dispatch functions and
functions imported by existing callers.

Process-wide runtime settings require no new bridge. `set_runtime_value`
already scans every loaded `netzoo_agent_core.*` module, but package tests must
prove that `PROJECT_ROOT` and `TOOL_LOG_ROOT` reach `discovery.py` and
`results.py`.

## Behaviour Preservation

The following observable behaviour is invariant:

- Capability recommendations, task rejection conditions, reasons, confidence
  checks, missing-input handling, and `no_tool` conversion remain unchanged.
- Context7 library normalization and model-generated library-ID rejection remain
  unchanged.
- Candidate roots, traversal bounds, symlink handling, scoring, extensions,
  sorting, display paths, and default output names remain unchanged.
- Context7 and Websearch connections, headers, MCP tool names, arguments,
  truncation limits, success text, and failure text remain unchanged.
- Retrieval exceptions continue to be converted to the existing user-visible
  failure text; nested exception formatting remains unchanged.
- Dispatch continues to select from `LOCAL_TOOL_EXECUTORS`, Context7, or
  Websearch only, and rejects unsupported actions with the same `ValueError`.
- Result failure markers, diagnostics, exit-code interpretation, dry-run
  detection, artifact validation, retry hints, summaries, metrics, warnings,
  errors, log paths, and bounded raw output remain unchanged.
- File and network operations occur at the same points in the data flow.
- Existing callers and tests do not need import changes.

The refactor will not add broad exception handling or redesign any rule.

## Testing and Verification

Before changing production code, record the current complete-suite baseline.
At design time the working tree reports 236 passing tests, 12 skipped tests,
and four known failures. One recovery-plan failure existed before the previous
evaluation refactor; three clarification failures occur in `interaction.py`
because the current workspace discovery state leaves no missing inputs for tests
that expect clarification. The refactor must not add failures or alter those
failure locations.

Add `tests/test_routing_package.py` to verify:

- `netzoo_agent_core.routing` is a package;
- every responsibility module imports independently;
- the historical `__all__` names and ordering are preserved;
- legacy facade exports resolve to the package exports;
- facade monkeypatches reach the child modules that call patched functions;
- runtime overrides reach the child modules that consume them.

Run existing tests for capability inference, task validation, capability gating,
candidate discovery, Context7 and Websearch retrieval, local dispatch,
structured results, artifact validation, recovery hints, log persistence,
planning, interpretation, graph orchestration, CLI, and the legacy facade.

Compile the new package, run the complete test suite, and compare every moved
function body with the original module. The final diff must contain only source
moves, package imports and exports, child-module facade registration, module
docstrings, and compatibility tests.

## Acceptance Criteria

The refactor is complete when:

1. `routing.py` has been replaced by the documented `routing/` package.
2. Every responsibility module has one clear purpose and a one-directional
   dependency path.
3. No responsibility module exceeds approximately 300 lines without a
   cohesion-based reason.
4. All 37 historical exports remain available in the same order.
5. Existing stable and legacy imports work without caller changes.
6. Legacy monkeypatch and runtime-setting propagation work through child
   modules.
7. Capability, discovery, retrieval, dispatch, and result behaviour are
   unchanged.
8. Focused package and compatibility tests pass.
9. The complete suite has no new failures relative to the recorded baseline.
10. All new modules compile and import successfully.

## Out of Scope

- Changing capability rules, patterns, thresholds, or user-visible text.
- Changing filesystem discovery or output naming behaviour.
- Replacing Context7 or Websearch MCP adapters.
- Changing the local executor allow-list.
- Redesigning `ToolExecutionResult` or artifact validation.
- Refactoring planning, interpretation, graph, CLI, memory, contracts,
  validation, or execution modules.
- Fixing the four pre-existing test failures.
