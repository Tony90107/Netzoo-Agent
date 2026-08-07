# NetZoo Core Navigation Refactor Design

**Date:** 2026-08-07

**Status:** Proposed for implementation

**Scope:** CLI/interaction packaging, contract decomposition, and workflow-data packaging

## 1. Objective

Restructure `scripts/netzoo_agent_core` so maintainers can locate failures by
capability without changing user-visible behavior, execution authority, serialized
contracts, or supported import paths.

This design implements three independently verifiable phases:

1. convert `cli.py` into a `cli/` package and move interaction behavior beneath it;
2. convert `contracts.py` into a `contracts/` package and move settings, framework
   compatibility, and presentation behavior out of the contract implementation;
3. concentrate input/output discovery, validation, preparation, and path behavior in
   a `data/` package, removing discovery's dependency on Executor internals.

The refactor is structural. It must not change workflow selection, plan evaluation,
tool execution, prompts, CLI output, persistence formats, trace formats, or policy
semantics.

## 2. Context and constraints

The package already has useful lifecycle modules for routing, interpretation,
planning, evaluation, and graph orchestration. Static analysis found no internal
module cycle. The remaining navigation problems are concentrated in three clusters:

- `cli.py` owns argument parsing, administrative commands, dependency construction,
  resume behavior, and a roughly 470-line interactive loop; `interaction.py` is used
  only by the CLI.
- `contracts.py` is imported by most of the package while also owning mutable
  settings, LangGraph/LangChain fallbacks, terminal presentation behavior, and
  several unrelated model families.
- dataset discovery and bundle selection import private functions from
  `execution.py` and `validation.py`, so input-discovery defects can require reading
  the Executor implementation.

The repository has a historical `scripts/netzoo_agent.py` facade. Existing tests
also patch exported names and process-wide runtime settings. The conversion must
therefore preserve:

- `python scripts/netzoo_agent.py ...` behavior and exit codes;
- `import netzoo_agent` and its historical exported names;
- current `netzoo_agent_core.<module>` imports, including documented private
  compatibility names used by tests;
- Pydantic model names, fields, defaults, validation, JSON serialization, and module
  identity assumptions covered by tests;
- every code-enforced Planner, Plan Evaluator, Executor, and Result Evaluator gate;
- the current workflow registry and YAML policy semantics;
- the user's existing uncommitted changes in `memory.py` and related tests.

No new third-party dependency is permitted.

## 3. Considered approaches

### 3.1 Recommended: staged package conversions with compatibility facades

Convert one cluster at a time. Before moving implementation, add package-shape and
compatibility characterization tests. Preserve the old import path by making the new
package `__init__.py` re-export the established interface. Keep temporary thin shims
only where a differently named old module must remain importable.

Advantages:

- each phase is independently testable;
- callers move gradually without a big-bang import rewrite;
- the external seam remains stable while implementation gains locality;
- regressions can be attributed to one conversion.

Cost: compatibility exports remain broader than the desired final interface until a
separate deprecation phase is approved.

### 3.2 Rejected: big-bang package rewrite

Move all files and update every import in one change. This produces a clean final
tree quickly, but combines CLI state-machine risk, Pydantic identity risk, mutable
runtime synchronization, and data-validation risk in one review surface. A failure
would be difficult to localize.

### 3.3 Rejected: wrapper-only directory structure

Add new packages which merely import the old full modules. This preserves behavior
but leaves two navigation paths and keeps the old modules as the real owners. It
improves appearance without improving locality or dependency direction.

## 4. Target architecture

After all three phases, the relevant tree will be:

```text
scripts/netzoo_agent_core/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── arguments.py
│   ├── trace_commands.py
│   ├── clarification.py
│   ├── follow_up.py
│   ├── loop.py
│   └── main.py
├── interaction.py                 # thin legacy import facade
├── contracts/
│   ├── __init__.py
│   ├── decisions.py
│   ├── planning.py
│   ├── results.py
│   ├── policy.py
│   ├── memory.py
│   └── state.py
├── settings.py
├── framework_compat.py
├── presentation.py
├── data/
│   ├── __init__.py
│   ├── paths.py
│   ├── table_validation.py
│   ├── inspection.py
│   ├── bundles.py
│   ├── preparation.py
│   └── artifacts.py
├── validation.py                  # thin legacy import facade
├── bundles.py                     # thin legacy import facade
├── preparation.py                 # thin legacy import facade
├── artifact_validation.py         # thin legacy import facade
├── path_safety.py                 # thin legacy import facade
└── ... existing lifecycle packages ...
```

The thin legacy modules are compatibility adapters. New internal code imports the
owning package directly. They contain no independent behavior.

## 5. Phase 1: CLI and interaction package

### 5.1 External seam

`netzoo_agent_core.cli` exposes:

```python
def parse_args() -> argparse.Namespace: ...
def local_trace_status(run_id: str, *, trace_root: Path = TRACE_ROOT) -> dict: ...
def export_local_trace(run_id: str, destination: Path, *, trace_root: Path = TRACE_ROOT) -> Path: ...
def main() -> int: ...
```

`scripts/netzoo_agent.py` continues to call `cli.main()`.

`netzoo_agent_core.interaction` remains importable as a thin facade and re-exports
the historical interaction names from `cli.clarification` and `cli.follow_up`.

### 5.2 Internal ownership

- `arguments.py` owns only `argparse` construction and environment-backed defaults.
- `trace_commands.py` owns the two trace status/export helpers.
- `clarification.py` owns clarification parsing, continuation construction,
  preference confirmation, and their prompts.
- `follow_up.py` owns `NextTurnPrompt` construction, rendering, decline/back
  detection, and follow-up input resolution.
- `loop.py` owns the interactive task state machine. It accepts already constructed
  dependencies and runtime values rather than parsing CLI arguments.
- `main.py` validates options, constructs stores/graph/tracing dependencies, handles
  administrative one-shot commands, and delegates conversation execution to
  `loop.py`.

`main()` should become an orchestration function rather than the implementation of
the interactive state machine. Exact line count is not an interface requirement;
the success criterion is that the loop can be read and tested without administrative
command setup, and vice versa.

### 5.3 Behavior preservation

- All existing flags, defaults, help text, exit codes, and environment variables
  remain unchanged.
- Interactive and one-shot task behavior remains unchanged.
- Session pause/resume, clarification selection, preference confirmation, ephemeral
  checkpoint deletion, trace pause/finish, and interrupt handling remain unchanged.
- No new prompt strings are introduced during the mechanical conversion.

## 6. Phase 2: contracts, settings, framework compatibility, and presentation

### 6.1 Contract package ownership

- `decisions.py`: `PreferenceProposal`, `RouterDecision`, `TaskDecision`.
- `planning.py`: `InputEvidence`, `WorkflowStep`, `WorkflowPlan`.
- `results.py`: `EvaluationResult`, `PlanRubricItem`, `PlanEvaluationResult`,
  `ArtifactValidationResult`, `ToolExecutionResult`.
- `policy.py`: `AgentsPolicyHeader`, `WorkflowPolicySpec`,
  `ProjectPolicySnapshot`.
- `memory.py`: `UserProfile`, `Episode`.
- `state.py`: `AgentState`, `LLMUsage`, `NextTurnPrompt`,
  `AgentTurnInterrupted`, `ClarificationInputError`.

`contracts/__init__.py` re-exports the exact historical contract surface during this
refactor. Callers do not need to change immediately.

### 6.2 Settings ownership

`settings.py` owns filesystem roots, limits, model defaults, runtime flags, role-field
sets, and constants previously stored in `contracts.py`. It must remain compatible
with `runtime.set_runtime_value()` and the legacy facade's monkeypatch behavior.

Settings that vary per constructed graph should continue their existing migration
toward explicit dependency injection. This phase does not redesign runtime behavior;
it only gives the remaining process-wide compatibility values one discoverable home.

### 6.3 Framework compatibility ownership

`framework_compat.py` owns LangChain message/tool imports, LangGraph symbols, and the
current local fallbacks used when those optional packages are absent. Domain contract
modules must not import LangGraph directly except `state.py`, which requires
`add_messages` for `AgentState`.

### 6.4 Presentation ownership

`presentation.py` owns deterministic user-visible language enforcement, compact
progress rendering, transient trace state, output-language policy text, display-path
formatting, demo-request recognition, and CLI follow-up stripping.

This is intentionally not placed below `cli/`: graph nodes also emit progress and
response cleanup. Putting it below a `cli/__init__.py` that imports `main` could create
a `cli -> graph -> cli` import cycle. `presentation.py` is an in-process module with
no graph or CLI dependency.

### 6.5 Compatibility rules

- `from netzoo_agent_core.contracts import WorkflowPlan` remains valid.
- Existing model serialization remains byte-for-byte equivalent for the same input
  where JSON ordering is already deterministic.
- `contracts.__all__` remains available for `scripts/netzoo_agent.py`.
- Framework fallback behavior remains testable without installed LangGraph.
- Mutable runtime values remain synchronized across loaded legacy implementation
  modules until a later explicit `RuntimeConfig` migration.

## 7. Phase 3: workflow data package and dependency direction

### 7.1 Package ownership

- `paths.py`: user-path resolution, safe output basenames, CONDOR derived paths, and
  input/output collision checks.
- `table_validation.py`: `TableCheck`, table reading, header detection, expression,
  edge-list, miRNA, biological-ID overlap, and PANDA/PUMA inspection behavior.
- `inspection.py`: reusable dataset facts and inspectors currently misplaced in the
  Executor, including expression sample count and CONDOR input inspection.
- `bundles.py`: coherent dataset bundle selection.
- `preparation.py`: expression formatting and expression-to-coexpression conversion.
- `artifacts.py`: post-execution artifact structure validation.

### 7.2 Dependency rule

The dependency direction after conversion is:

```text
interpretation ─┐
planning ───────┼──> data
evaluation ─────┤
execution ──────┘
```

`data` must not import `execution`, `planning`, `evaluation`, `graph`, or `cli`.

Specifically:

- expression sample counting moves from `execution.py` to `data.inspection`;
- CONDOR input inspection implementation moves from `execution.py` to
  `data.inspection`;
- bundle and interpretation discovery import these data functions directly;
- `execution.py` imports and re-exports the historical private names only for
  compatibility;
- path resolution moves to `data.paths`, eliminating cross-module imports of the
  private function from the legacy `validation` module.

### 7.3 Legacy import adapters

The five old top-level data-related modules remain as thin re-export adapters during
this change. `scripts/netzoo_agent.py` includes the real data implementation modules
in its compatibility owner registry so historical monkeypatch propagation continues
to work.

No function may have two independent implementations after the conversion.

## 8. Error handling and safety

This refactor does not broaden error recovery. Existing exceptions, `SystemExit`
messages, return values, and fail-closed policy behavior remain unchanged.

The following safety invariants must be covered by the final verification:

- ready plans still require Plan Evaluator approval before Executor access;
- no arbitrary shell command becomes executable;
- path collision and output containment checks still run before command launch;
- discovery cannot mark unvalidated multi-file inputs as one coherent bundle;
- persistence and trace writes retain current private permissions and atomicity;
- imports do not initialize provider clients or execute local tools.

## 9. Testing strategy

Each phase follows replace-don't-layer testing at its external seam while retaining
existing regression coverage until the conversion is complete.

### 9.1 Baseline

Before implementation, run focused package tests and the complete test suite. Record
any pre-existing failure caused by the dirty working tree; do not silently change
unrelated user work to make the baseline green.

### 9.2 CLI tests

Add characterization tests proving:

- `netzoo_agent_core.cli` is a package;
- its four public functions remain available;
- `netzoo_agent_core.interaction` resolves historical names to the new owning
  modules;
- argument defaults/help and representative administrative commands are unchanged;
- one-shot, clarification/resume, and interrupt paths retain their exit behavior.

### 9.3 Contract tests

Add characterization tests proving:

- `netzoo_agent_core.contracts` is a package;
- public model imports and `__all__` remain compatible;
- representative old and new import paths resolve to the same class objects;
- model validation and serialization fixtures remain unchanged;
- framework fallback and mutable runtime propagation remain functional.

### 9.4 Data tests

Add characterization tests proving:

- old facade and new owner imports resolve to the same function/class objects where
  identity is part of compatibility;
- PANDA/PUMA/CONDOR inspection reports remain unchanged for existing fixtures;
- bundle discovery, path collision, preparation, and artifact validation behavior
  remains unchanged;
- `data` modules do not import Executor implementation modules;
- legacy monkeypatch tests continue to patch the effective owner.

### 9.5 Final verification

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core scripts/netzoo_agent.py
pytest -q
```

Also run the repository's architecture/import compatibility tests explicitly so a
full-suite skip or collection issue cannot hide a broken facade.

## 10. Documentation

Update `NETZOO_HARNESS_ARCHITECTURE.md` and other current architecture indexes that
still describe routing, planning, evaluation, interpretation, or graph packages as
single `.py` files. Add a short problem-to-module map for:

- routing/classification failures;
- task extraction and discovery failures;
- evidence/planning failures;
- plan-evaluation failures;
- input and artifact validation failures;
- execution failures;
- CLI/session failures;
- trace/observability failures.

Historical design and plan documents are records and must not be rewritten.

## 11. Completion criteria

The work is complete only when:

1. all three package conversions are present and importable;
2. old supported imports and the legacy `netzoo_agent` facade still work;
3. CLI behavior and serialized typed contracts remain unchanged;
4. discovery and bundle modules no longer import Executor private implementations;
5. the package has no internal import cycle;
6. characterization, focused, and complete tests pass, apart from any explicitly
   documented pre-existing dirty-tree failure;
7. current architecture documentation reflects the real package tree and includes
   the problem-to-module map;
8. no unrelated user modification is overwritten or staged.
