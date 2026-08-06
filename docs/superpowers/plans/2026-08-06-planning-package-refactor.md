# Planning Package Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 484-line planning module and 387-line planner function with a responsibility-oriented package while preserving every public interface and planning result.

**Architecture:** A stable package facade exposes only `build_workflow_plan` and `render_plan`. The builder coordinates three internal stages: context preparation, evidence-ledger construction, and final plan assembly; rendering remains independent. A small mutable `_PlanningContext` carries validated state forward without creating a class hierarchy or extension framework.

**Tech Stack:** Python 3.12, Pydantic models, pytest, unittest-compatible existing tests, importlib, standard-library dataclasses and hashing.

## Global Constraints

- Preserve the existing five-parameter `build_workflow_plan` signature and `WorkflowPlan` return type.
- Preserve `render_plan(plan) -> str` exactly.
- The package `__all__` must equal `["build_workflow_plan", "render_plan"]`.
- Explicit user paths remain authoritative over router-inferred paths.
- Multi-file workflows must use one coherent dataset bundle and never mix discovered bundles.
- Only output roles may receive reversible default paths.
- Evidence order, statuses, sources, reasons, candidates, bundle IDs, question text, steps, notes, and policy hash must remain unchanged.
- Do not add broad exception handling, abstract base classes, plugins, or public internal helpers.
- Keep `builder.py` at or below 80 lines after extraction.
- Preserve legacy `netzoo_agent` dependency-patching behavior by registering every planning child module.
- Do not modify, stage, or commit unrelated user changes.
- The accepted full-suite baseline is 241 passed, 12 skipped, and the same four known failures documented in the design specification.

## File Map

| Path | Final responsibility |
| --- | --- |
| `scripts/netzoo_agent_core/planning/__init__.py` | Public package facade with two exports. |
| `scripts/netzoo_agent_core/planning/context.py` | `_PlanningContext` plus validation, normalization, authorization, policy binding, and early-plan construction. |
| `scripts/netzoo_agent_core/planning/evidence.py` | Explicit grounding, episode reuse, demo/coherent discovery, output defaults, candidate discovery, and ordered evidence. |
| `scripts/netzoo_agent_core/planning/assembly.py` | Missing-input decision, consolidated clarification, validation steps, execution step, and final plan. |
| `scripts/netzoo_agent_core/planning/builder.py` | Short public pipeline orchestrator. |
| `scripts/netzoo_agent_core/planning/rendering.py` | Human-readable plan renderer. |
| `scripts/netzoo_agent.py` | Register package child modules in the compatibility facade. |
| `tests/test_planning_package.py` | Exact characterization, structure, child-module, facade, runtime override, and locality tests. |
| `scripts/netzoo_agent_core/planning.py` | Delete after transferring its behavior into the package. |

---

### Task 1: Freeze Representative Planning Behavior

**Files:**
- Create: `tests/test_planning_package.py`
- Reference: `scripts/netzoo_agent_core/planning.py`

**Interfaces:**
- Consumes: current `build_workflow_plan(raw_decision, task, profile=None, retrieved_episodes=None, project_policy=None) -> WorkflowPlan`.
- Produces: three stable SHA-256 expectations over canonical `WorkflowPlan.model_dump(mode="json")` output.

- [ ] **Step 1: Add canonical serialization and representative cases**

Create the test module with imports, a canonical digest helper, and three deterministic cases:

```python
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.planning as planning  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402


def _plan_digest(plan) -> str:
    payload = json.dumps(
        plan.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


PLANNING_CASES = (
    (
        "respond_only",
        TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=0.99,
            reason="Explain PANDA.",
        ),
        "Explain PANDA.",
        "8a90e5eb0ae7412dd492867b4e4f62b16a10c0c364ce181813dc55f95ffffade",
    ),
    (
        "retrieval",
        TaskDecision(
            action="web_search",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Find current PANDA references.",
            web_query="current PANDA references",
        ),
        "Search the web for current PANDA references.",
        "3002acd9eebcce0114110e98620a1f6c0b74f82f2a28c72ff28c4cc906ee486b",
    ),
    (
        "explicit_panda",
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Run supplied PANDA inputs.",
        ),
        (
            "Run PANDA with expression_file=data/study/expression.tsv "
            "motif_file=data/study/motif.tsv ppi_file=data/study/ppi.tsv "
            "output_file=outputs/study/panda.tsv"
        ),
        "14e28c7aef73fdaa791174ba182b4d7037cc033429b9217fa35434d0d2541bd6",
    ),
)


@pytest.mark.parametrize(("case_name", "decision", "task", "expected"), PLANNING_CASES)
def test_planning_model_dump_is_characterized(case_name, decision, task, expected):
    before = decision.model_dump(mode="json")
    plan = planning.build_workflow_plan(decision, task)

    assert _plan_digest(plan) == expected, case_name
    assert decision.model_dump(mode="json") == before
```

The three hashes were captured from the approved pre-refactor implementation on 2026-08-06. They cover response-only, retrieval, and a ready local workflow including ordered evidence and steps.

- [ ] **Step 2: Run the characterization tests against the original module**

Run:

```bash
pytest tests/test_planning_package.py -q
```

Expected: `3 passed`.

- [ ] **Step 3: Run the existing focused planning coverage**

Run:

```bash
pytest tests/test_agent_gate.py tests/test_dataset_bundles.py tests/test_path_and_output_safety.py -q
```

Expected: only the already documented clarification failures may fail when the untracked `data/official-toy/` directory is present; all other selected tests pass.

- [ ] **Step 4: Commit the behavioral guardrail**

```bash
git add tests/test_planning_package.py
git commit -m "test: characterize planning behavior"
```

---

### Task 2: Convert the Module to a Package Without Changing Planner Logic

**Files:**
- Delete: `scripts/netzoo_agent_core/planning.py`
- Create: `scripts/netzoo_agent_core/planning/__init__.py`
- Create: `scripts/netzoo_agent_core/planning/builder.py`
- Create: `scripts/netzoo_agent_core/planning/rendering.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_planning_package.py`

**Interfaces:**
- Consumes: the exact current `build_workflow_plan` body and `render_plan` body.
- Produces: importable `netzoo_agent_core.planning` package, `planning.builder.build_workflow_plan`, and `planning.rendering.render_plan` with unchanged object identity through the legacy facade.

- [ ] **Step 1: Add failing package-structure tests**

Append:

```python
PUBLIC_EXPORTS = ["build_workflow_plan", "render_plan"]


def test_planning_is_responsibility_oriented_package():
    assert hasattr(planning, "__path__")
    for module_name in ("builder", "rendering"):
        importlib.import_module(f"netzoo_agent_core.planning.{module_name}")


def test_planning_public_surface_is_preserved():
    assert planning.__all__ == PUBLIC_EXPORTS
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(planning, name)
```

- [ ] **Step 2: Run the structure tests to verify they fail**

Run:

```bash
pytest tests/test_planning_package.py::test_planning_is_responsibility_oriented_package tests/test_planning_package.py::test_planning_public_surface_is_preserved -q
```

Expected: the first test fails because `planning` is still a module and has no `__path__`.

- [ ] **Step 3: Create the public package facade**

Use this complete `__init__.py`:

```python
"""Evidence-ledger construction and deterministic workflow planning."""

from .builder import build_workflow_plan
from .rendering import render_plan

__all__ = ["build_workflow_plan", "render_plan"]
```

- [ ] **Step 4: Move the existing planner body unchanged into `builder.py`**

Create `builder.py` from the current `planning.py` imports and lines 68 through 454. Because the module moves one package level deeper, change only relative imports from one dot to two dots:

```python
from ..bundles import MULTI_FILE_ACTIONS, discover_coherent_bundle
from ..contracts import (
    Episode,
    InputEvidence,
    OUTPUT_ROLE_FIELDS,
    PROJECT_ROOT,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
    WorkflowStep,
    _is_demo_request,
)
from ..interpretation import (
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _lioness_mode_plan,
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    discover_demo_bundle,
    reusable_episode_inputs,
)
from ..policy import ProjectPolicyLoader
from ..routing import (
    MIN_TOOL_CONFIDENCE,
    _default_lioness_outputs,
    _default_network_output,
    _find_candidate_files,
    enforce_capability_gate,
    validate_task_text,
)
from ..validation import _resolve_user_path

__all__ = ["build_workflow_plan"]
```

Keep the `workflow_registry` import absolute. Do not edit any branch, string, ordering, or assignment inside `build_workflow_plan` during this task.

- [ ] **Step 5: Move the existing renderer unchanged into `rendering.py`**

Use:

```python
"""Human-readable workflow-plan rendering."""

from __future__ import annotations

from ..contracts import WorkflowPlan

__all__ = ["render_plan"]


def render_plan(plan: WorkflowPlan) -> str:
    lines = [f"Workflow: {plan.workflow}", "Evidence ledger:"]
    if not plan.evidence:
        lines.append("- This task does not require local data files.")
    for item in plan.evidence:
        value = f" → {item.value}" if item.value else ""
        lines.append(f"- {item.field}: {item.status}{value} ({item.reason})")
        if item.status == "missing" and item.candidates:
            lines.append("  Candidates: " + ", ".join(item.candidates))
    if plan.steps:
        lines.append("Execution plan:")
        for index, step in enumerate(plan.steps, 1):
            lines.append(f"{index}. {step.action}: {step.purpose}")
    if plan.memory_notes:
        lines.append("Retrieved memory:")
        lines.extend(f"- {note}" for note in plan.memory_notes)
    if plan.policy_notes:
        lines.append(f"Project policy ({(plan.policy_hash or 'unknown')[:12]}):")
        lines.extend(f"- {note}" for note in plan.policy_notes)
    if plan.preference_proposals:
        lines.append("Preference changes awaiting confirmation:")
        lines.extend(
            f"- {proposal.key} = {proposal.value} ({proposal.reason})"
            for proposal in plan.preference_proposals
        )
    if plan.question:
        lines.append("User input required: " + plan.question)
    return "\n".join(lines)
```

- [ ] **Step 6: Register the first planning child modules in the legacy facade**

Add:

```python
from netzoo_agent_core.planning import (
    builder as planning_builder,
    rendering as planning_rendering,
)
```

Place `planning_builder` and `planning_rendering` immediately after `planning` in `_IMPLEMENTATION_MODULES`:

```python
    planning,
    planning_builder,
    planning_rendering,
```

- [ ] **Step 7: Run package and characterization tests**

Run:

```bash
pytest tests/test_planning_package.py -q
```

Expected: `5 passed`; all three digests remain unchanged.

- [ ] **Step 8: Commit the mechanical package conversion**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/planning tests/test_planning_package.py
git commit -m "refactor: convert planning module to package"
```

---

### Task 3: Extract Planning Context Preparation

**Files:**
- Create: `scripts/netzoo_agent_core/planning/context.py`
- Modify: `scripts/netzoo_agent_core/planning/builder.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_planning_package.py`

**Interfaces:**
- Consumes: raw decision, task text, optional profile, optional episodes, and optional project policy.
- Produces: `_prepare_planning_context(raw_decision, task, profile, retrieved_episodes, project_policy) -> _PlanningContext | WorkflowPlan` and `_PlanningContext` with exact fields shown below.

- [ ] **Step 1: Add tests for early and continuing context results**

Append:

```python
def test_context_stage_returns_early_response_plan():
    context_module = importlib.import_module("netzoo_agent_core.planning.context")
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=0.99,
        reason="Explain PANDA.",
    )

    result = context_module._prepare_planning_context(
        decision,
        "Explain PANDA.",
        None,
        None,
        None,
    )

    assert result.status == "respond_only"
    assert decision.action == "no_tool"


def test_context_stage_prepares_local_workflow_state():
    context_module = importlib.import_module("netzoo_agent_core.planning.context")
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=0.99,
        reason="Run PANDA.",
    )

    result = context_module._prepare_planning_context(
        decision,
        "Run PANDA.",
        None,
        None,
        None,
    )

    assert isinstance(result, context_module._PlanningContext)
    assert result.action == "run_panda"
    assert result.workflow == "PANDA"
    assert result.required == [
        "expression_file",
        "motif_file",
        "ppi_file",
        "output_file",
    ]
```

- [ ] **Step 2: Run the new context tests to verify they fail**

Run:

```bash
pytest tests/test_planning_package.py -k "context_stage" -q
```

Expected: import failure for `netzoo_agent_core.planning.context`.

- [ ] **Step 3: Define the context data contract**

Create `context.py` with focused imports and this data class:

```python
from dataclasses import dataclass

from ..contracts import (
    Episode,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
    WorkflowPolicySpec,
)

__all__: list[str] = []


@dataclass
class _PlanningContext:
    decision: TaskDecision
    task: str
    profile: UserProfile
    episodes: list[Episode]
    memory_notes: list[str]
    policy: ProjectPolicySnapshot | None
    policy_hash: str | None
    policy_notes: list[str]
    workflow_spec: WorkflowPolicySpec | None
    action: str
    workflow: str
    required: list[str]
```

- [ ] **Step 4: Move context preparation and early returns**

Move the current builder logic from the initial deep copy through required-role construction into:

```python
def _prepare_planning_context(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None,
    retrieved_episodes: list[Episode | dict] | None,
    project_policy: ProjectPolicySnapshot | dict | None,
) -> _PlanningContext | WorkflowPlan:
```

Keep the existing validation, policy check, preferred-workflow authorization, Lioness ambiguity, capability gate, action rejection, policy notes, no-tool plan, retrieval plan, and required-role logic unchanged. At the former transition into input grounding, return:

```python
    return _PlanningContext(
        decision=decision,
        task=task,
        profile=profile_model,
        episodes=episode_models,
        memory_notes=memory_notes,
        policy=policy_model,
        policy_hash=policy_hash,
        policy_notes=policy_notes,
        workflow_spec=workflow_spec,
        action=action,
        workflow=workflow,
        required=required,
    )
```

- [ ] **Step 5: Make the builder consume the new context stage**

Replace the moved block with:

```python
    context_or_plan = _prepare_planning_context(
        raw_decision,
        task,
        profile,
        retrieved_episodes,
        project_policy,
    )
    if isinstance(context_or_plan, WorkflowPlan):
        return context_or_plan
    context = context_or_plan
    decision = context.decision
    task = context.task
    profile_model = context.profile
    episode_models = context.episodes
    memory_notes = context.memory_notes
    policy_hash = context.policy_hash
    policy_notes = context.policy_notes
    workflow_spec = context.workflow_spec
    action = context.action
    workflow = context.workflow
    required = context.required
```

These aliases keep the not-yet-extracted evidence and assembly body byte-for-byte equivalent.

- [ ] **Step 6: Register `planning_context` in the compatibility facade**

Extend the planning child import and tuple:

```python
from netzoo_agent_core.planning import (
    builder as planning_builder,
    context as planning_context,
    rendering as planning_rendering,
)
```

```python
    planning,
    planning_builder,
    planning_context,
    planning_rendering,
```

- [ ] **Step 7: Run context, characterization, and policy tests**

Run:

```bash
pytest tests/test_planning_package.py tests/test_agent_gate.py -k "planning or planner or policy or preferred_workflow or lioness_mode" -q
```

Expected: all selected tests pass except any documented test whose missing-input assumption is invalidated by the untracked `data/official-toy/` directory.

- [ ] **Step 8: Commit the context seam**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/planning/context.py scripts/netzoo_agent_core/planning/builder.py tests/test_planning_package.py
git commit -m "refactor: extract planning context preparation"
```

---

### Task 4: Extract Evidence-Ledger Construction

**Files:**
- Create: `scripts/netzoo_agent_core/planning/evidence.py`
- Modify: `scripts/netzoo_agent_core/planning/builder.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_planning_package.py`

**Interfaces:**
- Consumes: `_PlanningContext` containing the authorized local workflow and required roles.
- Produces: `_build_evidence_ledger(context: _PlanningContext) -> list[InputEvidence]` while mutating only `context.decision` as the original planner does.

- [ ] **Step 1: Add failing child-module and facade-patching tests**

Append:

```python
def test_evidence_stage_is_importable_and_internal():
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    assert evidence_module.__all__ == []
    assert not hasattr(planning, "_build_evidence_ledger")


def test_legacy_candidate_patch_reaches_evidence_child():
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    original = legacy_agent._find_candidate_files
    calls = []

    def replacement(keywords, root):
        calls.append((keywords, root))
        return []

    try:
        legacy_agent._find_candidate_files = replacement
        assert evidence_module._find_candidate_files is replacement
        plan = legacy_agent.build_workflow_plan(
            TaskDecision(
                action="run_condor",
                in_scope=True,
                should_execute=True,
                confidence=0.99,
                reason="Run CONDOR.",
            ),
            "Run CONDOR with research data.",
        )
        assert plan.status == "needs_input"
        assert calls
    finally:
        legacy_agent._find_candidate_files = original


def test_project_root_override_reaches_evidence_child(tmp_path):
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    original = legacy_agent.PROJECT_ROOT
    try:
        legacy_agent.PROJECT_ROOT = tmp_path
        assert evidence_module.PROJECT_ROOT == tmp_path
    finally:
        legacy_agent.PROJECT_ROOT = original
```

- [ ] **Step 2: Run the new evidence tests to verify they fail**

Run:

```bash
pytest tests/test_planning_package.py -k "evidence_stage or candidate_patch or project_root_override" -q
```

Expected: import failure for `netzoo_agent_core.planning.evidence`.

- [ ] **Step 3: Create the evidence stage and move the evidence block**

Create `evidence.py` with the existing focused imports from bundles, contracts, interpretation, routing, and validation, plus:

```python
from pathlib import Path

from .context import _PlanningContext
from ..contracts import InputEvidence, OUTPUT_ROLE_FIELDS, PROJECT_ROOT, _is_demo_request

__all__: list[str] = []


def _build_evidence_ledger(context: _PlanningContext) -> list[InputEvidence]:
    decision = context.decision
    task = context.task
    profile_model = context.profile
    episode_models = context.episodes
    action = context.action
    required = context.required
```

Move the current builder logic beginning with `input_fields` and ending after the evidence loop into this function. Preserve the following exact order:

```python
    input_fields = [
        field_name
        for field_name in required
        if field_name not in {"output_file", "lioness_output", "output_dir"}
    ]
    explicit_input_values: dict[str, str] = {}
    selected_fields = set(
        re.findall(r"SELECTED_FIELD=([a-z_]+)", task, flags=re.IGNORECASE)
    )
```

Then retain explicit grounding, output grounding, episode reuse, demo selection, nearby-directory selection, coherent bundle discovery, output defaults, candidate discovery, and evidence append branches without wording or priority changes. End with:

```python
    return evidence
```

- [ ] **Step 4: Replace the moved builder block with one stage call**

Import and call:

```python
from .evidence import _build_evidence_ledger


    evidence = _build_evidence_ledger(context)
```

Remove builder imports that are now owned exclusively by `evidence.py`.

- [ ] **Step 5: Register `planning_evidence` in the compatibility facade**

Extend the import and tuple:

```python
from netzoo_agent_core.planning import (
    builder as planning_builder,
    context as planning_context,
    evidence as planning_evidence,
    rendering as planning_rendering,
)
```

```python
    planning,
    planning_builder,
    planning_context,
    planning_evidence,
    planning_rendering,
```

- [ ] **Step 6: Run evidence, bundle, path-safety, and characterization tests**

Run:

```bash
pytest tests/test_planning_package.py tests/test_dataset_bundles.py tests/test_path_and_output_safety.py -q
```

Expected: all tests pass and the three characterization hashes are unchanged.

- [ ] **Step 7: Commit the evidence seam**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/planning/evidence.py scripts/netzoo_agent_core/planning/builder.py tests/test_planning_package.py
git commit -m "refactor: extract planning evidence construction"
```

---

### Task 5: Extract Plan Assembly and Reduce the Builder to Orchestration

**Files:**
- Create: `scripts/netzoo_agent_core/planning/assembly.py`
- Modify: `scripts/netzoo_agent_core/planning/builder.py`
- Modify: `scripts/netzoo_agent.py`
- Modify: `tests/test_planning_package.py`

**Interfaces:**
- Consumes: `_PlanningContext` and the complete ordered `list[InputEvidence]`.
- Produces: `_assemble_workflow_plan(context, evidence) -> WorkflowPlan` and a public builder of at most 80 lines.

- [ ] **Step 1: Add failing assembly-boundary and builder-locality tests**

Append:

```python
def test_assembly_stage_is_importable_and_internal():
    assembly_module = importlib.import_module("netzoo_agent_core.planning.assembly")
    assert assembly_module.__all__ == []
    assert not hasattr(planning, "_assemble_workflow_plan")


def test_builder_is_a_small_pipeline_orchestrator():
    builder_module = importlib.import_module("netzoo_agent_core.planning.builder")
    source = inspect.getsource(builder_module)

    assert len(source.splitlines()) <= 80
    assert "_prepare_planning_context" in source
    assert "_build_evidence_ledger" in source
    assert "_assemble_workflow_plan" in source
    assert "discover_coherent_bundle" not in source
    assert "_find_candidate_files" not in source


def test_internal_planning_helpers_do_not_leak_from_facade():
    for name in (
        "_PlanningContext",
        "_prepare_planning_context",
        "_build_evidence_ledger",
        "_assemble_workflow_plan",
    ):
        assert not hasattr(planning, name)
```

- [ ] **Step 2: Run the new assembly and locality tests to verify they fail**

Run:

```bash
pytest tests/test_planning_package.py -k "assembly_stage or small_pipeline or do_not_leak" -q
```

Expected: import failure for `planning.assembly` and builder line-count failure.

- [ ] **Step 3: Create the assembly stage**

Create:

```python
"""Final clarification or executable plan assembly."""

from __future__ import annotations

from workflow_registry import CODE_VALIDATION_STEPS

from .context import _PlanningContext
from ..contracts import InputEvidence, WorkflowPlan, WorkflowStep

__all__: list[str] = []


def _assemble_workflow_plan(
    context: _PlanningContext,
    evidence: list[InputEvidence],
) -> WorkflowPlan:
    decision = context.decision
    action = context.action
    workflow = context.workflow
    workflow_spec = context.workflow_spec
    memory_notes = context.memory_notes
    policy_hash = context.policy_hash
    policy_notes = context.policy_notes
```

Move the existing builder block beginning with `missing =` through the final ready `WorkflowPlan` return into this function. Preserve the exact consolidated question:

```python
        question = (
            "Please provide the next missing input. The CLI wizard will ask for "
            "each unresolved field one at a time; advanced users may still enter "
            "field=value pairs for all remaining inputs."
        )
```

Keep decision mutation, validation step ordering, validation purpose, execution action selection, execution purpose, memory notes, policy notes, and policy hash unchanged.

- [ ] **Step 4: Reduce the builder to the final public pipeline**

Replace `builder.py` with:

```python
"""Public orchestration entry point for deterministic planning."""

from __future__ import annotations

from .assembly import _assemble_workflow_plan
from .context import _prepare_planning_context
from .evidence import _build_evidence_ledger
from ..contracts import (
    Episode,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
)

__all__ = ["build_workflow_plan"]


def build_workflow_plan(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None = None,
    retrieved_episodes: list[Episode | dict] | None = None,
    project_policy: ProjectPolicySnapshot | dict | None = None,
) -> WorkflowPlan:
    """Turn intent into an evidence-backed, multi-step NetZoo workflow."""
    context_or_plan = _prepare_planning_context(
        raw_decision,
        task,
        profile,
        retrieved_episodes,
        project_policy,
    )
    if isinstance(context_or_plan, WorkflowPlan):
        return context_or_plan
    evidence = _build_evidence_ledger(context_or_plan)
    return _assemble_workflow_plan(context_or_plan, evidence)
```

- [ ] **Step 5: Register `planning_assembly` in the compatibility facade**

The final planning child registration is:

```python
from netzoo_agent_core.planning import (
    assembly as planning_assembly,
    builder as planning_builder,
    context as planning_context,
    evidence as planning_evidence,
    rendering as planning_rendering,
)
```

```python
    planning,
    planning_assembly,
    planning_builder,
    planning_context,
    planning_evidence,
    planning_rendering,
```

- [ ] **Step 6: Run all package tests**

Run:

```bash
pytest tests/test_planning_package.py -q
```

Expected: all package tests pass, all three plan digests remain unchanged, the legacy public functions are identical, patched discovery reaches the evidence child, runtime overrides propagate, internal helpers remain private, and the builder is at most 80 lines.

- [ ] **Step 7: Run all existing planning-adjacent tests**

Run:

```bash
pytest tests/test_agent_gate.py tests/test_dataset_bundles.py tests/test_path_and_output_safety.py tests/test_agent_module_boundaries.py -q
```

Expected: only the documented clarification failures caused by the existing `data/official-toy/` directory may fail; no new failure is allowed.

- [ ] **Step 8: Commit the completed pipeline**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/planning/assembly.py scripts/netzoo_agent_core/planning/builder.py tests/test_planning_package.py
git commit -m "refactor: extract planning assembly pipeline"
```

---

### Task 6: Verify the Full Behavioral Baseline and Repository Hygiene

**Files:**
- Verify: `scripts/netzoo_agent_core/planning/`
- Verify: `scripts/netzoo_agent.py`
- Verify: `tests/test_planning_package.py`
- Verify only: unrelated dirty-worktree files

**Interfaces:**
- Consumes: completed package and all repository tests.
- Produces: evidence that the refactor preserves the accepted baseline and contains no unrelated staged changes.

- [ ] **Step 1: Check final module sizes and syntax**

Run:

```bash
wc -l scripts/netzoo_agent_core/planning/*.py
python -m compileall -q scripts/netzoo_agent_core/planning
```

Expected: `builder.py` is at most 80 lines; each file has one responsibility; compilation exits successfully.

- [ ] **Step 2: Run the clean baseline with known failures excluded**

Run:

```bash
pytest -q -k 'not test_clarification_marker_preserves_previous_action_against_reroute and not test_clarification_wizard_selects_each_missing_field_independently and not test_recovered_plan_is_authorized_by_the_same_plan_evaluator and not test_selected_input_keeps_selected_provenance_after_replanning'
```

Expected: 241 passed, 12 skipped, and 4 deselected, subject only to additional tests added by this plan increasing the passed count.

- [ ] **Step 3: Run the unfiltered full suite**

Run:

```bash
pytest -q
```

Expected: the same four known failures and no new failures. The passed count increases by the number of new package tests; 12 tests remain skipped.

- [ ] **Step 4: Check formatting and staged scope**

Run:

```bash
git diff --check 611ef06..HEAD
git status --short
git diff --cached --name-only
```

Expected: no whitespace errors; the pre-existing unrelated dirty-worktree entries remain untouched; the staging area is empty after the task commits.

- [ ] **Step 5: Review the final dependency direction**

Run:

```bash
rg -n "^from \.|^from \.\." scripts/netzoo_agent_core/planning
```

Expected dependency direction:

```text
__init__ -> builder, rendering
builder -> context, evidence, assembly, contracts
evidence -> context plus existing lower-level helpers
assembly -> context plus contracts and workflow_registry
context -> existing lower-level helpers
rendering -> contracts
```

No internal stage imports `planning.__init__`, and no dependency cycle exists.

- [ ] **Step 6: Record final evidence in the handoff**

Report the package file list and line counts, package-test result, focused-test result, full-suite result, known failures, and the implementation commit hashes. Do not create an empty verification commit.
