# NetZoo Core Navigation Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the CLI, contracts, and workflow-data clusters into responsibility-oriented packages while preserving all historical imports, runtime overrides, typed serialization, and safety behavior.

**Architecture:** Perform three sequential package conversions behind compatibility facades. Each conversion begins with characterization tests, makes one implementation owner for every symbol, updates the legacy facade owner registry, and passes focused tests before the next conversion begins.

**Tech Stack:** Python 3.11+, Pydantic, LangGraph/LangChain optional compatibility layer, pandas, pytest, standard-library `argparse`, `pathlib`, and `importlib`.

## Global Constraints

- Do not change workflow selection, plan evaluation, Executor authority, recovery behavior, CLI prompts, flags, exit codes, persistence formats, or trace formats.
- Preserve `python scripts/netzoo_agent.py ...`, `import netzoo_agent`, and current `netzoo_agent_core.<module>` imports.
- Preserve `__all__`, object identity, signatures, Pydantic fields/defaults/serialization, and legacy monkeypatch propagation where current tests characterize them.
- Do not add a third-party dependency.
- Do not overwrite, stage, or revert the user's existing changes in `memory.py`, `tests/test_agent_stability.py`, `tests/test_graph_tracing.py`, unrelated documentation, or untracked data. `NETZOO_HARNESS_ARCHITECTURE.md` is explicitly in scope because the approved design requires its package map to be updated; preserve all unrelated content in that file.
- Keep every code-enforced Planner, Plan Evaluator, Executor, Result Evaluator, path-safety, and policy gate fail-closed.
- Use exact-path staging for each commit because the worktree is dirty.
- Work only in `/Users/chenzhonghan/Documents/LLM AGENT/network-zoo-panda-puma` on the existing `main` branch.

---

### Task 1: Characterize and convert the CLI/interaction cluster

**Files:**
- Create: `tests/test_cli_package.py`
- Create: `scripts/netzoo_agent_core/cli/__init__.py`
- Create: `scripts/netzoo_agent_core/cli/arguments.py`
- Create: `scripts/netzoo_agent_core/cli/trace_commands.py`
- Create: `scripts/netzoo_agent_core/cli/clarification.py`
- Create: `scripts/netzoo_agent_core/cli/follow_up.py`
- Create: `scripts/netzoo_agent_core/cli/loop.py`
- Create: `scripts/netzoo_agent_core/cli/main.py`
- Replace: `scripts/netzoo_agent_core/interaction.py`
- Delete: `scripts/netzoo_agent_core/cli.py`
- Modify: `scripts/netzoo_agent.py`

**Interfaces:**
- Consumes: current `cli.__all__`, `interaction.__all__`, `scripts/netzoo_agent.py` compatibility registry, graph/session/memory/trace interfaces.
- Produces: `netzoo_agent_core.cli` package exposing `parse_args`, `main`, `export_local_trace`, and `local_trace_status`; `netzoo_agent_core.interaction` thin facade preserving all historical interaction names.

- [ ] **Step 1: Verify the baseline before changing the CLI**

Run:

```bash
pwd
git branch --show-current
python -m compileall -q scripts/netzoo_agent_core scripts/netzoo_agent.py
pytest -q
```

Expected: working directory and branch match the global constraints; compilation
passes. Record any pre-existing pytest failure without changing unrelated dirty
files. If there are three or more unrelated baseline failures, stop for review.

- [ ] **Step 2: Write the failing CLI package characterization tests**

Create `tests/test_cli_package.py` with tests equivalent to:

```python
from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.cli as cli  # noqa: E402
import netzoo_agent_core.interaction as interaction  # noqa: E402

CLI_EXPORTS = ["parse_args", "main", "export_local_trace", "local_trace_status"]
INTERACTION_EXPORTS = [
    "CLARIFICATION_FIELD_ALIASES",
    "_candidate_selection",
    "parse_clarification_assignments",
    "clarification_continuation",
    "resolve_clarification",
    "clarification_prompt",
    "preference_confirmation_prompt",
    "preference_continuation",
    "initial_next_turn_prompt",
    "build_next_turn_prompt",
    "follow_up_declined",
    "render_next_turn_prompt",
    "follow_up_returns_to_main",
    "resolve_next_turn_input",
]

def test_cli_is_a_package_with_responsibility_modules():
    assert hasattr(cli, "__path__")
    for name in (
        "arguments", "trace_commands", "clarification", "follow_up", "loop", "main"
    ):
        importlib.import_module(f"netzoo_agent_core.cli.{name}")

def test_cli_surface_and_legacy_identity_are_preserved():
    assert cli.__all__ == CLI_EXPORTS
    for name in CLI_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(cli, name)

def test_interaction_facade_preserves_historical_identity():
    assert interaction.__all__ == INTERACTION_EXPORTS
    clarification = importlib.import_module("netzoo_agent_core.cli.clarification")
    follow_up = importlib.import_module("netzoo_agent_core.cli.follow_up")
    for name in INTERACTION_EXPORTS:
        owner = clarification if hasattr(clarification, name) else follow_up
        assert getattr(interaction, name) is getattr(owner, name)
        assert getattr(legacy_agent, name) is getattr(owner, name)

def test_cli_main_is_orchestration_sized():
    main_module = importlib.import_module("netzoo_agent_core.cli.main")
    assert len(inspect.getsource(main_module.main).splitlines()) <= 140
```

Also copy the current signatures of the four CLI exports and representative
interaction functions into exact `inspect.signature` assertions.

- [ ] **Step 3: Run the new tests and verify the package-shape failure**

Run:

```bash
pytest tests/test_cli_package.py -q
```

Expected: FAIL because `netzoo_agent_core.cli` is still a module and has no
`__path__` or child modules. Existing CLI behavior assertions should already pass.

- [ ] **Step 4: Convert `cli.py` to a package without behavior edits**

Move the current implementation into package modules, changing only package-relative
imports and extraction seams:

```python
# cli/__init__.py
from .arguments import parse_args
from .main import main
from .trace_commands import export_local_trace, local_trace_status

__all__ = ["parse_args", "main", "export_local_trace", "local_trace_status"]
```

`arguments.py` receives the current `parse_args()` unchanged. `trace_commands.py`
receives the two trace helper functions unchanged. Keep environment variable names,
defaults, argument order, and help text byte-equivalent.

- [ ] **Step 5: Move interaction behavior beneath `cli/`**

Move clarification/preference functions and constants to `cli/clarification.py`.
Move next-turn/follow-up functions to `cli/follow_up.py`. Use an explicit facade:

```python
# netzoo_agent_core/interaction.py
from .cli.clarification import *  # noqa: F401,F403
from .cli.clarification import __all__ as _clarification_exports
from .cli.follow_up import *  # noqa: F401,F403
from .cli.follow_up import __all__ as _follow_up_exports

__all__ = [*_clarification_exports, *_follow_up_exports]
```

In the real implementation, prefer explicit imports over wildcard imports if that
is required to preserve the exact historical order shown in Step 2.

- [ ] **Step 6: Extract the interactive loop from CLI bootstrap**

Define a private context dataclass or keyword-only function parameters in
`cli/loop.py` so the loop receives constructed stores, graph, recorder, session
state, and CLI mode. Preserve the current state-machine body. The external seam is:

```python
def run_cli_loop(
    *,
    args,
    app,
    profile_id: str,
    profile_store,
    session_id: str,
    resume_id: str | None,
    recorder,
    trace_store,
    sync_worker,
) -> int:
    ...
```

If the exact dependency list becomes unwieldy, introduce one internal
`_CliRuntime` dataclass in `loop.py`; do not expose it from `cli.__init__`.
`main.py` continues option validation, administrative one-shot commands, policy and
store construction, graph construction, then delegates to `run_cli_loop()`.

- [ ] **Step 7: Update the legacy owner registry**

Modify `scripts/netzoo_agent.py` so `_IMPLEMENTATION_MODULES` includes the new CLI
children and both interaction owners. This preserves legacy symbol replacement and
runtime propagation:

```python
import netzoo_agent_core.cli.arguments as cli_arguments
import netzoo_agent_core.cli.clarification as cli_clarification
import netzoo_agent_core.cli.follow_up as cli_follow_up
import netzoo_agent_core.cli.loop as cli_loop
import netzoo_agent_core.cli.main as cli_main_module
import netzoo_agent_core.cli.trace_commands as cli_trace_commands
```

Do not add internal CLI names to `netzoo_agent_core.cli.__all__`.

- [ ] **Step 8: Run focused CLI and facade tests**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core/cli scripts/netzoo_agent_core/interaction.py scripts/netzoo_agent.py
pytest tests/test_cli_package.py tests/test_legacy_facade.py tests/test_agent_stability.py tests/test_graph_tracing.py -q
```

Expected: PASS, except an already recorded baseline failure in a user-modified test.
If a legacy monkeypatch misses the real owner, update `_IMPLEMENTATION_MODULES`; do
not duplicate implementation in the facade.

- [ ] **Step 9: Commit the CLI conversion with exact-path staging**

```bash
git add -- \
  scripts/netzoo_agent.py \
  scripts/netzoo_agent_core/cli.py \
  scripts/netzoo_agent_core/cli \
  scripts/netzoo_agent_core/interaction.py \
  tests/test_cli_package.py
git diff --cached --check
git commit -m "refactor: package CLI interaction flow"
```

---

### Task 2: Characterize and decompose the contracts cluster

**Files:**
- Create: `tests/test_contracts_package.py`
- Create: `scripts/netzoo_agent_core/contracts/__init__.py`
- Create: `scripts/netzoo_agent_core/contracts/decisions.py`
- Create: `scripts/netzoo_agent_core/contracts/planning.py`
- Create: `scripts/netzoo_agent_core/contracts/results.py`
- Create: `scripts/netzoo_agent_core/contracts/policy.py`
- Create: `scripts/netzoo_agent_core/contracts/memory.py`
- Create: `scripts/netzoo_agent_core/contracts/state.py`
- Create: `scripts/netzoo_agent_core/settings.py`
- Create: `scripts/netzoo_agent_core/framework_compat.py`
- Create: `scripts/netzoo_agent_core/presentation.py`
- Delete: `scripts/netzoo_agent_core/contracts.py`
- Modify: all `scripts/netzoo_agent_core/**/*.py` imports that consume moved owners
- Modify: `scripts/netzoo_agent.py`

**Interfaces:**
- Consumes: current `contracts.__all__`, runtime mutable-name synchronization, all existing Pydantic fixtures.
- Produces: responsibility-oriented contract children plus stable `netzoo_agent_core.contracts` facade, `settings`, `framework_compat`, and framework-neutral `presentation` modules.

- [ ] **Step 1: Write failing contract package and identity tests**

Create `tests/test_contracts_package.py`. Include the exact current
`contracts.__all__` list and representative identities:

```python
def test_contracts_is_a_package_with_final_owners():
    assert hasattr(contracts, "__path__")
    for name in ("decisions", "planning", "results", "policy", "memory", "state"):
        importlib.import_module(f"netzoo_agent_core.contracts.{name}")

def test_contract_facade_exports_exact_historical_surface():
    assert contracts.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(contracts, name), name

def test_models_have_one_owner_and_preserve_identity():
    decisions = importlib.import_module("netzoo_agent_core.contracts.decisions")
    planning = importlib.import_module("netzoo_agent_core.contracts.planning")
    results = importlib.import_module("netzoo_agent_core.contracts.results")
    assert contracts.TaskDecision is decisions.TaskDecision
    assert contracts.WorkflowPlan is planning.WorkflowPlan
    assert contracts.ToolExecutionResult is results.ToolExecutionResult
```

Add exact `model_json_schema()` or normalized `model_dump()` assertions for
`TaskDecision`, `WorkflowPlan`, `InputEvidence`, `ToolExecutionResult`,
`ProjectPolicySnapshot`, `UserProfile`, and `Episode`. Reuse the existing
conditional `derived_from` serialization fixture from `test_planning_package.py`.

Add AST/import tests asserting domain children do not import `langgraph` directly,
with the sole allowed `state -> framework_compat.add_messages` dependency.

- [ ] **Step 2: Run the tests and verify the package-shape failure**

Run:

```bash
pytest tests/test_contracts_package.py tests/test_planning_package.py tests/test_trace_contracts.py -q
```

Expected: the new package-shape/owner tests FAIL because `contracts` is still one
module; existing serialization tests PASS.

- [ ] **Step 3: Extract framework compatibility and settings**

Move the optional imports and local fallback classes/functions unchanged to
`framework_compat.py`, exporting:

```python
__all__ = [
    "AIMessage", "HumanMessage", "SystemMessage", "tool",
    "END", "START", "StateGraph", "add_messages",
]
```

Move constants and filesystem roots to `settings.py`. Keep mutable values as module
attributes so `runtime.set_runtime_value()` can update loaded consumers. Preserve
the exact historical constant names and values.

- [ ] **Step 4: Extract presentation behavior from contracts**

Move `_ui_text`, `output_language_policy`, `_clear_transient_trace`, `_trace_line`,
`_trace`, `CLI_FOLLOW_UP_STARTERS`, `strip_cli_owned_follow_up_question`,
`_display_path`, and `_is_demo_request` into `presentation.py`. Import mutable display
settings from `settings` in a form compatible with the runtime owner registry.

Do not import `cli`, `graph`, or contract model modules from `presentation.py`.

- [ ] **Step 5: Split contract models by ownership**

Move definitions without changing field order, defaults, annotations, validators,
model configuration, or docstrings:

```text
decisions.py -> PreferenceProposal, RouterDecision, TaskDecision
planning.py  -> InputEvidence, WorkflowStep, WorkflowPlan
results.py   -> EvaluationResult, PlanRubricItem, PlanEvaluationResult,
                ArtifactValidationResult, ToolExecutionResult
policy.py    -> AgentsPolicyHeader, WorkflowPolicySpec, ProjectPolicySnapshot
memory.py    -> UserProfile, Episode
state.py     -> AgentState, AgentTurnInterrupted, ClarificationInputError,
                LLMUsage, NextTurnPrompt
```

Use dependency direction `settings/framework_compat -> contract children` and avoid
child-to-facade imports. Children may import sibling owner modules directly when a
field annotation requires it.

- [ ] **Step 6: Build the historical contract facade**

Create `contracts/__init__.py` with explicit imports in the exact historical
`__all__` order. Re-export settings, framework, and presentation names for
compatibility, but keep their implementation in their owning modules.

The facade must satisfy:

```python
assert contracts.TaskDecision is contracts.decisions.TaskDecision
assert contracts.PROJECT_ROOT is settings.PROJECT_ROOT
assert contracts.AIMessage is framework_compat.AIMessage
assert contracts._trace is presentation._trace
```

- [ ] **Step 7: Update internal imports to direct owners**

Update high-fan-in consumers incrementally:

- framework-only imports use `framework_compat`;
- constants and roots use `settings`;
- progress/text helpers use `presentation`;
- model imports may continue through `contracts` where that is the intended stable
  interface, but contract child modules must use direct sibling owners.

Update `scripts/netzoo_agent.py` to include `settings`, `framework_compat`,
`presentation`, and all contract child modules in `_IMPLEMENTATION_MODULES` without
changing the historical global export list.

- [ ] **Step 8: Verify runtime override propagation and serialization**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core/contracts scripts/netzoo_agent_core/settings.py scripts/netzoo_agent_core/framework_compat.py scripts/netzoo_agent_core/presentation.py scripts/netzoo_agent.py
pytest tests/test_contracts_package.py tests/test_planning_package.py tests/test_evaluation_package.py tests/test_graph_package.py tests/test_trace_contracts.py tests/test_legacy_facade.py tests/test_agent_stability.py -q
```

Expected: PASS, with class identity and serialization unchanged. Explicitly verify
legacy assignments to `PROJECT_ROOT`, `EXECUTE_TOOLS`, `TRACE_ENABLED`, and
`TOOL_TIMEOUT_SECONDS` reach every loaded owning/consumer module characterized by
existing tests.

- [ ] **Step 9: Commit the contracts conversion with exact-path staging**

Stage only the deleted old contracts file, new contract/settings/framework/
presentation files, exact consumer files changed for imports, the legacy facade, and
`tests/test_contracts_package.py`. Inspect `git diff --cached --name-only` before:

```bash
git diff --cached --check
git commit -m "refactor: decompose core contracts"
```

---

### Task 3: Characterize and create the workflow data package

**Files:**
- Create: `tests/test_data_package.py`
- Create: `scripts/netzoo_agent_core/data/__init__.py`
- Create: `scripts/netzoo_agent_core/data/paths.py`
- Create: `scripts/netzoo_agent_core/data/table_validation.py`
- Create: `scripts/netzoo_agent_core/data/inspection.py`
- Create: `scripts/netzoo_agent_core/data/bundles.py`
- Create: `scripts/netzoo_agent_core/data/preparation.py`
- Create: `scripts/netzoo_agent_core/data/artifacts.py`
- Replace: `scripts/netzoo_agent_core/validation.py`
- Replace: `scripts/netzoo_agent_core/bundles.py`
- Replace: `scripts/netzoo_agent_core/preparation.py`
- Replace: `scripts/netzoo_agent_core/artifact_validation.py`
- Replace: `scripts/netzoo_agent_core/path_safety.py`
- Modify: `scripts/netzoo_agent_core/execution.py`
- Modify: data consumers under `planning/`, `evaluation/`, `interpretation/`, and `routing/`
- Modify: `scripts/netzoo_agent.py`

**Interfaces:**
- Consumes: existing validation, bundle, preparation, artifact, and path function signatures and reports.
- Produces: one `data/` implementation owner per behavior, thin top-level compatibility adapters, and dependency direction from interpretation/planning/evaluation/execution into data.

- [ ] **Step 1: Write failing data package and dependency tests**

Create `tests/test_data_package.py` with the exact historical facade exports and
owner identities:

```python
def test_data_is_a_package_with_final_owners():
    assert hasattr(data, "__path__")
    for name in (
        "paths", "table_validation", "inspection", "bundles",
        "preparation", "artifacts",
    ):
        importlib.import_module(f"netzoo_agent_core.data.{name}")

def test_legacy_validation_facade_uses_data_owner():
    owner = importlib.import_module("netzoo_agent_core.data.table_validation")
    for name in validation.__all__:
        assert getattr(validation, name) is getattr(owner, name)

def test_executor_reexports_moved_inspection_names():
    inspection = importlib.import_module("netzoo_agent_core.data.inspection")
    assert execution._expression_sample_count is inspection.expression_sample_count
    assert execution._inspect_condor_inputs_impl is inspection.inspect_condor_inputs_impl
```

Add an AST test which fails if any `netzoo_agent_core.data.*` module imports
`execution`, `planning`, `evaluation`, `graph`, or `cli`. Add identity tests for all
five legacy facades and behavior fixtures using existing PANDA/PUMA/CONDOR toy data.

- [ ] **Step 2: Run the new tests and verify the missing-package failure**

Run:

```bash
pytest tests/test_data_package.py tests/test_dataset_bundles.py tests/test_path_and_output_safety.py tests/test_agent_artifacts.py tests/test_condor_runner.py -q
```

Expected: new data package tests FAIL with `ModuleNotFoundError`; existing behavior
tests PASS at the recorded baseline level.

- [ ] **Step 3: Move path and table validation ownership**

Move path resolution and safety functions to `data/paths.py`. Move `TableCheck`,
table parsing/header helpers, biological validators, overlap reporting, and PANDA/
PUMA input inspection to `data/table_validation.py`.

Keep old modules as explicit adapters. For example:

```python
# validation.py
from .data.table_validation import (
    TableCheck,
    _drop_common_header,
    _identifier_overlap_report,
    _inspect_panda_inputs_impl,
    _looks_numeric,
    _read_checked_table,
    _read_expression_source,
    _resolve_user_path,
    _validate_edge_or_bed,
    _validate_expression,
    _validate_mirna_list,
    inspect_netzoo_inputs,
)

__all__ = [
    "TableCheck", "_resolve_user_path", "_read_expression_source",
    "_looks_numeric", "_drop_common_header", "_read_checked_table",
    "_validate_expression", "_validate_edge_or_bed", "_validate_mirna_list",
    "_identifier_overlap_report", "_inspect_panda_inputs_impl",
    "inspect_netzoo_inputs",
]
```

`_resolve_user_path` may remain a compatibility alias in `table_validation`; its
implementation owner is `data.paths`.

- [ ] **Step 4: Extract neutral inspection from Executor**

Move expression sample counting and CONDOR input inspection to
`data/inspection.py` with public internal-owner names:

```python
def expression_sample_count(expression_file: str) -> tuple[int, bool]: ...
def inspect_condor_inputs_impl(network_file: str) -> tuple[str, bool]: ...
```

In `execution.py`, preserve compatibility aliases:

```python
from .data.inspection import (
    expression_sample_count as _expression_sample_count,
    inspect_condor_inputs_impl as _inspect_condor_inputs_impl,
)
```

Move the decorated `inspect_condor_inputs` adapter only if doing so does not make
`data` depend on framework `tool`; otherwise keep that thin tool adapter in
`execution.py` and delegate to the neutral inspector.

- [ ] **Step 5: Move bundles, preparation, and artifact validation**

Move each implementation unchanged to its data owner and replace the old file with
an explicit identity-preserving adapter:

```text
bundles.py             -> data/bundles.py
preparation.py         -> data/preparation.py
artifact_validation.py -> data/artifacts.py
path_safety.py          -> data/paths.py
```

`data/bundles.py` imports neutral data inspection rather than `execution.py`.
`data/artifacts.py` imports path behavior from `data.paths` and table/path helpers
from their direct owners.

- [ ] **Step 6: Reverse internal callers toward the data owners**

Update:

- `interpretation/discovery.py` to import sample count and CONDOR inspection from
  `data.inspection`;
- `planning/evidence.py` to import path resolution and bundles from `data` owners;
- `evaluation/plan_review.py` and `evaluation/rendering.py` to use `data.paths`;
- `routing/results.py` to use `data.artifacts`;
- `execution.py` to use `data.paths`, `data.table_validation`, and
  `data.preparation`;
- package root exports to preserve existing stable imports.

Update `scripts/netzoo_agent.py` so all data owners participate in the compatibility
registry. Keep adapters in the registry only where their names remain historical
symbol owners; avoid duplicate owner ambiguity.

- [ ] **Step 7: Run focused data, execution, planning, and evaluation tests**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core/data scripts/netzoo_agent_core scripts/netzoo_agent.py
pytest \
  tests/test_data_package.py \
  tests/test_dataset_bundles.py \
  tests/test_path_and_output_safety.py \
  tests/test_agent_artifacts.py \
  tests/test_condor_runner.py \
  tests/test_command_processes.py \
  tests/test_planning_package.py \
  tests/test_evaluation_package.py \
  tests/test_interpretation_package.py \
  tests/test_legacy_facade.py -q
```

Expected: PASS. Compare exact inspection/report strings through existing tests; do
not accept changed output merely because semantics look equivalent.

- [ ] **Step 8: Commit the data conversion with exact-path staging**

Stage only the new data package, five legacy adapters, changed consumers, legacy
facade, and `tests/test_data_package.py`. Verify staged names exclude pre-existing
dirty user files, then:

```bash
git diff --cached --check
git commit -m "refactor: centralize workflow data behavior"
```

---

### Task 4: Verify architecture, update navigation documentation, and close the refactor

**Files:**
- Modify: `NETZOO_HARNESS_ARCHITECTURE.md`
- Modify: `scripts/netzoo_agent_core/__init__.py` only if stable exports require final owner corrections
- Modify: package tests only for fixes to incorrect architecture assertions

**Interfaces:**
- Consumes: all three completed package conversions.
- Produces: current architecture tree, problem-to-module navigation map, acyclic dependency evidence, and full-suite verification.

- [ ] **Step 1: Add a package-wide acyclic dependency assertion**

Extend the most appropriate architecture test, normally
`tests/test_agent_module_boundaries.py`, to parse relative imports under
`netzoo_agent_core`, construct the internal module graph, and assert there is no
strongly connected component containing more than one module.

Also assert:

```python
for forbidden in ("execution", "planning", "evaluation", "graph", "cli"):
    assert forbidden not in data_dependencies
```

- [ ] **Step 2: Update the current architecture document**

Replace the obsolete single-file tree with the actual package tree. Add a compact
problem-to-module map:

```text
wrong capability/action       -> routing/
wrong task extraction         -> interpretation/
wrong input discovery/evidence-> data/ + planning/evidence.py
plan rejection                -> evaluation/
input/output validation       -> data/
command execution             -> execution.py + command.py
CLI/resume/follow-up           -> cli/ + session.py
trace/audit                    -> trace_*.py + tracing.py
```

Do not rewrite historical specs or plans.

- [ ] **Step 3: Run package and compatibility verification**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core scripts/netzoo_agent.py
pytest \
  tests/test_cli_package.py \
  tests/test_contracts_package.py \
  tests/test_data_package.py \
  tests/test_agent_module_boundaries.py \
  tests/test_legacy_facade.py -q
```

Expected: PASS.

- [ ] **Step 4: Run the complete suite**

Run:

```bash
pytest -q
```

Expected: PASS. If one of the user-modified tests had a documented baseline failure,
the same failure may remain only if the refactor does not affect it; demonstrate
that with a focused comparison before reporting completion.

- [ ] **Step 5: Audit size, private cross-imports, and cycles**

Run:

```bash
find scripts/netzoo_agent_core -type f -name '*.py' -print0 | xargs -0 wc -l | sort -nr | sed -n '1,80p'
rg -n '^from \.|^from netzoo_agent_core' scripts/netzoo_agent_core
git status --short
```

Confirm:

- `cli.main` delegates the interactive loop;
- `contracts` has one model owner per family;
- data discovery does not depend on Executor internals;
- no unexpected user file is staged;
- all old implementation files are either deleted package predecessors or thin
  explicit compatibility adapters.

- [ ] **Step 6: Commit documentation and architecture-test closure**

```bash
git add -- NETZOO_HARNESS_ARCHITECTURE.md tests/test_agent_module_boundaries.py scripts/netzoo_agent_core/__init__.py
git diff --cached --check
git commit -m "docs: map refactored core modules"
```

Omit any unchanged path from `git add`. Never stage unrelated dirty documentation.
