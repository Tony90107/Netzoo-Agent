# Interpretation Package Refactor Design

**Date:** 2026-08-06

**Status:** Approved for implementation planning

## Objective

Replace the 958-line `scripts/netzoo_agent_core/interpretation.py` module with a responsibility-oriented `interpretation/` package. Preserve every public interface, deterministic decision, validation rule, fallback, exception, and legacy assignment-based monkeypatch behavior.

This is a pure structural refactor. It must not fix, consolidate, reorder, or otherwise reinterpret existing logic, even where the current implementation contains duplication or suspicious code. Such observations may be recorded separately but are outside this change.

## Motivation

The current module contains five independent reasons to change:

1. deterministic extraction of paths, documentation intent, preferences, and LIONESS mode;
2. hydration of a small router result into a complete `TaskDecision`;
3. repair of router decisions against local authority and continuation markers;
4. deterministic behavior when the provider fails; and
5. discovery of coherent demo bundles and reusable episode inputs.

These responsibilities share a public interpretation interface but do not need to share one implementation file. Moving them behind internal seams improves locality and navigation without expanding the interface.

## Architecture

The final package is:

```text
scripts/netzoo_agent_core/interpretation/
├── __init__.py
├── extraction.py
├── hydration.py
├── repair.py
├── provider_fallback.py
└── discovery.py
```

### Package facade

`interpretation/__init__.py` is the external seam. It re-exports the exact current interface in the exact current `__all__` order. It contains no routing, extraction, repair, fallback, or discovery implementation.

The facade also exposes the private compatibility tuple:

```python
_INTERPRETATION_IMPLEMENTATION_MODULES = (
    discovery,
    extraction,
    hydration,
    provider_fallback,
    repair,
)
```

Each child module defines:

```python
__all__: list[str] = []
```

Internal functions remain importable only for package assembly and focused tests. They are not added to the public interpretation interface.

## Responsibility Map

### `extraction.py`

Owns deterministic extraction from user task text:

- `INPUT_LABELS`
- `_task_path`
- `_mentions_unspecified_data_directory`
- `_needs_lioness_mode_choice`
- `is_versioned_documentation_request`
- `documentation_library_for_task`
- `extract_preference_proposals`

It preserves every regular expression, alias, localized label, preference reason, and return shape byte-for-byte where practical and semantically exactly everywhere.

### `hydration.py`

Owns:

- `hydrate_router_decision`

It converts `RouterDecision`, `TaskDecision`, or a compatible dictionary into a complete `TaskDecision`. It continues to extract paths, prefix, header mode, genes axis, retrieval fields, preferences, and missing inputs in the current order.

### `repair.py`

Owns:

- `_lioness_mode_plan`
- `repair_router_decision`

It preserves the present authority ordering, including:

- version-specific documentation routing;
- stable workflow information responses;
- `PREVIOUS_ACTION` continuation authority;
- inferred deliverable repair;
- explicit LIONESS mode selection;
- explicit CONDOR execution repair; and
- unchanged no-tool behavior.

The previous-action marker remains higher authority than router reclassification.

### `provider_fallback.py`

Owns:

- `deterministic_router_fallback`
- `_is_fatal_exception`

It preserves the current provider-error reason text, documentation fallback, capability rejection, advisory response, explicit run detection, LIONESS ambiguity behavior, required-input extraction, and confidence values.

`KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` remain fatal and must never be converted into deterministic fallback behavior.

### `discovery.py`

Owns:

- `_candidate_keywords`
- `_choose_unambiguous_candidate`
- `_best_named_file`
- `discover_demo_bundle`
- `reusable_episode_inputs`

It preserves candidate scoring, the 15-point ambiguity threshold, coherent-directory selection, input validation, LIONESS sample-count requirements, completed-episode restrictions, path-existence checks, and evidence reason text.

Discovery cannot expand execution authority. It may only return coherent bundles or episode inputs that satisfy the existing validators.

## Dependency Direction

Allowed dependency direction is:

```text
extraction -> existing contracts and routing helpers
hydration -> extraction and existing contracts/registry
repair -> extraction and existing contracts/routing helpers
provider_fallback -> extraction and existing contracts/routing helpers
discovery -> existing contracts, execution, routing, validation, and registry
__init__ -> child registration and re-exports
```

Child modules must not import the package facade. No child may import `hydration`, `repair`, `provider_fallback`, or `discovery` unless a concrete existing call requires it. The intended final graph has no child-to-child edge except dependencies on `extraction`.

## Public Interface Compatibility

The package preserves the current `interpretation.__all__` contents and order:

```python
[
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

Existing callers continue to use:

```python
from netzoo_agent_core.interpretation import repair_router_decision
import netzoo_agent_core.interpretation as interpretation
import netzoo_agent as legacy_agent
```

All public function names, signatures, annotations, return values, mutation behavior, and exception behavior remain unchanged.

## Legacy Facade Compatibility

`scripts/netzoo_agent.py` continues to import `interpretation` and additionally imports `_INTERPRETATION_IMPLEMENTATION_MODULES`. Its implementation-module tuple expands the child modules immediately after the package facade:

```python
interpretation, *_INTERPRETATION_IMPLEMENTATION_MODULES,
```

Consequently, assignment-based compatibility remains valid:

```python
legacy_agent.repair_router_decision = replacement
```

The replacement must reach the child module that owns the implementation and any package facade binding that still refers to the previous object. The legacy facade remains at or below 150 lines.

## Error Handling

The refactor adds no new exception types, broad exception handlers, logging, trace events, warnings, or fallback branches.

- Router and Pydantic validation errors propagate exactly as they do now.
- Fatal base exceptions remain fatal.
- Ordinary provider failures enter the same deterministic fallback.
- Missing paths, ambiguous candidates, failed dataset validation, and missing reusable episodes return the same current results.
- No child module catches errors that the monolith currently allows to propagate.

## Testing Strategy

Create `tests/test_interpretation_package.py` to characterize structure and compatibility before moving behavior.

The tests must cover:

1. the exact public `__all__` list and public function signatures;
2. conversion from module to package;
3. child module privacy through empty `__all__` lists;
4. absence of leaked child helpers on the package facade;
5. legacy assignment propagation to representative owners in hydration, repair, provider fallback, and discovery;
6. responsibility-size limits preventing a new monolith;
7. dependency direction and absence of child cycles; and
8. the current deterministic behavior through existing agent-gate, planning, graph, and stability tests.

Focused behavior includes router hydration, decision repair, continuation markers, documentation routing, provider fallback, demo bundles, episode reuse, and LIONESS mode selection.

The accepted repository baseline is:

```text
Clean baseline:
270 passed, 12 skipped, 4 deselected

Unfiltered baseline:
270 passed, 12 skipped, and the same four documented failures
```

The four documented failures are:

- `test_clarification_marker_preserves_previous_action_against_reroute`
- `test_clarification_wizard_selects_each_missing_field_independently`
- `test_recovered_plan_is_authorized_by_the_same_plan_evaluator`
- `test_selected_input_keeps_selected_provenance_after_replanning`

No new failure is acceptable.

## Implementation Sequence

Implementation proceeds through independently verified commits:

1. characterize the public interpretation interface and legacy behavior;
2. mechanically convert `interpretation.py` into an import-compatible package;
3. extract deterministic text extraction and router hydration;
4. extract router repair and provider fallback;
5. extract demo and episode discovery, finalize child registration, and enforce size/dependency rules; and
6. run focused, clean-baseline, unfiltered, compilation, whitespace, staging, and dirty-worktree verification.

Each implementation commit must contain only interpretation-refactor files. Existing unrelated working-tree changes remain unstaged and unmodified.

## Success Criteria

The refactor is complete when:

- `scripts/netzoo_agent_core/interpretation.py` no longer exists;
- the package facade presents the exact existing interface;
- no child file recreates the 958-line monolith;
- all deterministic decision ordering and text remain unchanged;
- coherent dataset and memory reuse constraints remain unchanged;
- fatal and provider failure behavior remain unchanged;
- legacy assignment patches reach the owning child modules;
- existing internal callers require no interface changes;
- the clean baseline passes completely;
- the unfiltered suite contains only the same four documented failures; and
- unrelated working-tree changes remain untouched.
