# Planning Package Refactor Design

## Status

Approved design, pending implementation planning.

## Context

`scripts/netzoo_agent_core/planning.py` currently contains 484 lines. Its public surface is small, but `build_workflow_plan()` spans roughly 387 lines and combines several distinct responsibilities:

- validating and normalizing the planning request;
- binding the user profile, prior episodes, and project policy;
- authorizing the selected action and handling early-return workflows;
- grounding explicit paths and discovering reusable inputs;
- assembling the input evidence ledger;
- deciding whether clarification is required;
- constructing validation and execution steps;
- rendering the completed plan.

These responsibilities form one planning pipeline, but keeping them in one function makes navigation, local reasoning, and behavioral regression review unnecessarily difficult. The refactor will replace the module with a package whose internal seams follow the stages of that pipeline.

## Goals

- Make each planning responsibility easy to locate by filename.
- Keep the public planning interface unchanged.
- Preserve all current planning decisions, evidence ordering, messages, and failure behavior.
- Keep internal dependency direction explicit and shallow.
- Allow each stage to be tested directly without exposing it as public API.
- Preserve compatibility with `scripts/netzoo_agent.py` and its dependency-patching facade.

## Non-goals

- Changing planning policy or workflow selection rules.
- Fixing the four known baseline test failures.
- Refactoring unrelated modules.
- Adding a plugin system, abstract base classes, or general-purpose adapters.
- Changing public contract models or serialized plan shapes.
- Broadening filesystem discovery or action authority.

## Chosen Approach

Use an internal `_PlanningContext` and a linear planning pipeline. The context holds validated, normalized state shared by the stages. Each stage owns one cohesive transformation and depends only on lower-level contracts or helpers it needs.

This approach was selected over a mechanical function move because merely relocating the existing 387-line function would improve the filename but not the module depth or locality. It was also selected over a class hierarchy because the workflow is a fixed sequence of transformations and does not need polymorphic extension points.

## Package Structure

The existing `planning.py` module will become this package:

```text
scripts/netzoo_agent_core/planning/
  __init__.py
  context.py
  evidence.py
  assembly.py
  builder.py
  rendering.py
```

Responsibilities:

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Stable public facade; exports only `build_workflow_plan` and `render_plan`. |
| `context.py` | Validate and normalize the request, bind policy and episode state, authorize the action, and produce early plans when the remaining pipeline is unnecessary. |
| `evidence.py` | Ground explicit inputs, reuse prior inputs, discover coherent bundles, apply reversible output defaults, and build the ordered evidence ledger. |
| `assembly.py` | Convert context and evidence into either one consolidated clarification request or a ready workflow plan with validation and execution steps. |
| `builder.py` | Public orchestration entry point; connect the stages without containing domain-detail branches. |
| `rendering.py` | Render a `WorkflowPlan` as the current human-readable text representation. |

Target sizes are guides rather than hard runtime constraints:

- `context.py`: about 170 lines;
- `evidence.py`: about 230 lines;
- `assembly.py`: about 100 lines;
- `builder.py`: no more than about 80 lines;
- `rendering.py`: about 40 lines.

## Dependency Direction

```text
callers
  -> planning/__init__.py
       -> builder.py
            -> context.py
            -> evidence.py
            -> assembly.py
       -> rendering.py
```

The package facade must not import internal stage helpers into its public namespace. Stage modules may import existing domain contracts and focused helpers from routing, interpretation, validation, bundles, policy, and workflow registry modules. Internal stages must not import the package facade, and `context.py`, `evidence.py`, and `assembly.py` must not depend on one another cyclically.

## Internal Interfaces

### Planning context

`context.py` defines an internal mutable `_PlanningContext`. It contains the normalized decision and the validated state currently carried through local variables in `build_workflow_plan()`, including the task, profile, episodes, policy snapshot, preferred workflow, authorized action, required input roles, and planning flags.

The principal entry point is:

```python
def _prepare_planning_context(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None,
    retrieved_episodes: list[Episode | dict] | None,
    project_policy: ProjectPolicySnapshot | dict | None,
) -> _PlanningContext | WorkflowPlan:
    pass
```

Returning `WorkflowPlan` represents a deliberate early result, including Lioness ambiguity, no-tool response-only plans, and retrieval-only ready plans. Returning `_PlanningContext` means evidence discovery and final assembly must continue.

The input `TaskDecision` is deep-copied before normalization, matching current behavior and preventing planner mutation from leaking to callers.

### Evidence construction

`evidence.py` exposes only an internal stage entry point:

```python
def _build_evidence_ledger(context: _PlanningContext) -> list[InputEvidence]:
    pass
```

This stage owns:

- explicit user-path grounding;
- selected-marker preservation;
- reusable episode inputs;
- demo bundle selection;
- coherent multi-file bundle discovery;
- reversible default output paths;
- missing-input candidate discovery;
- evidence status, source, and ordering.

It does not construct the final `WorkflowPlan`. Explicit user paths remain authoritative over router guesses. Routed paths that cannot be grounded are cleared rather than treated as user-provided evidence. Multi-file workflows continue to use one coherent bundle and must not mix candidates from unrelated datasets.

### Plan assembly

`assembly.py` exposes:

```python
def _assemble_workflow_plan(
    context: _PlanningContext,
    evidence: list[InputEvidence],
) -> WorkflowPlan:
    pass
```

This stage owns:

- identifying unresolved required inputs from the completed ledger;
- producing one consolidated input question when clarification is required;
- constructing validation steps;
- constructing the execution step;
- returning the final ready plan.

It must not perform filesystem discovery or reinterpret raw task text.

### Public builder and renderer

`builder.py` retains the existing five-parameter `build_workflow_plan` signature and `WorkflowPlan` return type. Its body performs stage orchestration only:

1. prepare context;
2. return an early plan when supplied;
3. build evidence;
4. assemble the final plan.

`rendering.py` retains `render_plan(plan) -> str` without behavioral changes.

## Data Flow

```text
raw decision, task, profile, episodes, policy
  -> context preparation
       -> Lioness ambiguity: needs_input plan
       -> no-tool action: respond_only plan
       -> retrieval action: ready retrieval plan
       -> local workflow context
            -> evidence construction
                 -> explicit grounding
                 -> episode reuse
                 -> demo or coherent bundle discovery
                 -> reversible output defaults
                 -> missing-input candidates
                      -> plan assembly
                           -> consolidated needs_input plan
                           -> ready validation and execution plan
```

The context may be mutated only by planning stages during this pipeline. Evidence construction completes the ledger before assembly begins. Assembly consumes the ledger as the authoritative description of input readiness.

## Behavioral Invariants

The refactor is behavior-preserving. The following details must remain unchanged:

- Pydantic validation occurs at the same logical boundary.
- Project policy identity mismatches are rejected and not swallowed.
- Preferred workflow and action authorization rules remain unchanged.
- Explicit user paths take precedence over router-inferred paths.
- Ungrounded inferred paths do not become selected evidence.
- Evidence entries retain their existing order, role, status, source, purpose, candidates, and notes.
- Episode reuse, demo inputs, coherent bundle discovery, and ordinary candidate discovery retain their current priority.
- A multi-file action never combines inputs from different discovered bundles.
- Default paths are created only for output roles and remain reversible defaults.
- Existing clarification question text remains exact.
- Existing step descriptions, commands, purposes, notes, and status strings remain exact.
- The current conversion of no-tool decisions into response-only plans remains exact.
- Filesystem checks occur at the same logical stage.
- No broad exception handler is introduced.

## Public and Legacy Compatibility

The package public surface is:

```python
__all__ = ["build_workflow_plan", "render_plan"]
```

Existing imports continue to work:

```python
from netzoo_agent_core.planning import build_workflow_plan, render_plan
```

Internal helpers and `_PlanningContext` are intentionally absent from the package `__all__` and are not re-exported by `__init__.py`.

The compatibility facade in `scripts/netzoo_agent.py` must register the planning package and its child implementation modules. This preserves the current testing and integration convention in which assigning a patched dependency on the legacy `netzoo_agent` module propagates to the implementation module that imported it. For example, patching `_find_candidate_files` through the facade must affect `planning.evidence`.

## Testing Strategy

Add `tests/test_planning_package.py` for structural, compatibility, and focused behavioral coverage.

Structural checks:

- `netzoo_agent_core.planning` imports as a package;
- each child module imports directly;
- public `__all__` contains exactly the two existing public functions;
- the legacy facade exposes the same public function objects;
- internal stage helpers do not leak through the package facade;
- `builder.py` remains an orchestration module rather than accumulating domain branches;
- facade monkeypatching of `_find_candidate_files` reaches `planning.evidence`;
- facade monkeypatching of `PROJECT_ROOT` reaches the stage that consumes it.

Behavioral characterization covers:

- no-tool response-only planning;
- retrieval-only ready planning;
- ambiguous Lioness mode clarification;
- missing required inputs;
- explicit ready inputs;
- selected-input continuation;
- prior-episode reuse;
- demo request autofill;
- coherent multi-file bundle selection;
- output defaults;
- policy binding and mismatch rejection;
- validation and execution step assembly;
- `render_plan()` output.

Before moving the implementation, representative plans will be captured with `model_dump()`. After the refactor, equivalent inputs must produce identical serialized structures, including decision fields, evidence ordering and statuses, question text, steps, notes, and policy hash.

## Verification Baseline

The current full-suite baseline is:

- 241 tests passed;
- 12 tests skipped;
- 4 known failures.

The four known failures are outside this refactor:

- `test_clarification_marker_preserves_previous_action_against_reroute`;
- `test_clarification_wizard_selects_each_missing_field_independently`;
- `test_recovered_plan_is_authorized_by_the_same_plan_evaluator`;
- `test_selected_input_keeps_selected_provenance_after_replanning`.

Three failures are affected by the existing untracked `data/official-toy/` directory, which supplies inputs those tests expect to be missing. The recovery failure predates this planning refactor. Implementation acceptance requires the same full-suite baseline and a clean run when those four known failures are excluded.

## Acceptance Criteria

- `planning.py` is replaced by the designed package.
- Public imports and function signatures remain compatible.
- `build_workflow_plan()` becomes a short pipeline orchestrator.
- Each internal responsibility has one clear owning module.
- Representative serialized plans are identical before and after the refactor.
- Package-specific tests pass.
- The full suite retains 241 passed, 12 skipped, and only the same four known failures.
- Excluding the four known failures, the full suite passes.
- No unrelated user changes are modified, staged, or committed.
