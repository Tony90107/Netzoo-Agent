# CLI, Memory, Data Direction, and Code Reading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen the CLI and memory seams, make the data dependency direction honest, and add a practical code-reading path without removing existing behavior.

**Architecture:** Keep all historical facades and signatures stable while moving lifecycle, persistence, pure data, and framework-adapter behavior to explicit owner modules. Characterization tests protect each seam before mechanical extraction, and the reading guide traces one PANDA request through the resulting owners.

**Tech Stack:** Python 3.12, pytest, Pydantic, LangChain tools, LangGraph, pandas, pathlib, AST dependency tests, Git.

## Global Constraints

- Existing successful CLI commands, interactive behavior, resume behavior, stored data formats, tool outputs, and workflow decisions must remain unchanged.
- Historical imports and exported object identity remain valid wherever current compatibility tests define them.
- Preserve the existing uncommitted UUID JSON-sanitization behavior when converting `memory.py` into a package.
- Ordinary one-shot Graph failures return `1`; interactive failures remain recoverable; interruption returns `130`; pending non-interactive input returns `2`.
- Do not redesign Planner, Evaluator, Executor command behavior, memory ranking, retention rules, trace integrity, or workflow policy.
- Use `apply_patch` for edits and stage only files named by the active task.
- Existing unrelated dirty-worktree changes remain untouched.

---

## File ownership map

| File | Responsibility after this plan |
|---|---|
| `scripts/netzoo_agent_core/cli/commands.py` | Immediate web, trace, memory, and policy command handling |
| `scripts/netzoo_agent_core/cli/bootstrap.py` | Runtime validation and dependency construction |
| `scripts/netzoo_agent_core/cli/conversation.py` | One-shot, interactive, clarification, resume, and result lifecycle |
| `scripts/netzoo_agent_core/cli/loop.py` | Short stable `run_cli(args) -> int` coordinator |
| `scripts/netzoo_agent_core/memory/storage.py` | Safe identifiers, JSON sanitation, permissions, locks, atomic writes |
| `scripts/netzoo_agent_core/memory/profiles.py` | `UserProfileStore` |
| `scripts/netzoo_agent_core/memory/normalization.py` | Episode metadata normalization and compact rendering |
| `scripts/netzoo_agent_core/memory/episodes.py` | `EpisodeCleanupReport` and `EpisodeStore` |
| `scripts/netzoo_agent_core/memory/__init__.py` | Stable memory compatibility interface |
| `scripts/netzoo_agent_core/data/discovery.py` | Neutral candidate keywords, scoring, and best-file selection |
| `scripts/netzoo_agent_core/data/tables.py` | Pure table parsing and biological validation |
| `scripts/netzoo_agent_core/data/transforms.py` | Pure expression and co-expression transformations with explicit write policy |
| `scripts/netzoo_agent_core/data/table_validation.py` | Historical data-path facade |
| `scripts/netzoo_agent_core/data/preparation.py` | Historical data-path facade |
| `scripts/netzoo_agent_core/tool_adapters.py` | Decorated data tools and mutable execution-mode adapter |
| `CODE_READING_GUIDE.md` | Maintained basic-Python reading route and PANDA trace |

---

### Task 1: Characterize and deepen the CLI lifecycle

**Files:**
- Create: `tests/test_cli_lifecycle.py`
- Create: `scripts/netzoo_agent_core/cli/commands.py`
- Create: `scripts/netzoo_agent_core/cli/bootstrap.py`
- Create: `scripts/netzoo_agent_core/cli/conversation.py`
- Modify: `scripts/netzoo_agent_core/cli/loop.py`
- Modify: `scripts/netzoo_agent_core/cli/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Test: `tests/test_cli_package.py`
- Test: `tests/test_cli_lifecycle.py`
- Test: `tests/test_netzoo_chat_launcher.py`

**Interfaces:**
- Consumes: the exact current `run_cli(args) -> int` behavior and the existing clarification, session, trace, memory, policy, and Graph functions.
- Produces: `handle_preflight_command(args) -> int | None`, `MemoryRuntime`, `bootstrap_memory(args) -> MemoryRuntime`, `handle_memory_command(args, runtime) -> int | None`, `load_project_policy() -> ProjectPolicySnapshot`, `handle_policy_command(args, policy) -> int | None`, `CliRuntime`, `bootstrap_runtime(args, memory_runtime, policy) -> CliRuntime`, `run_conversation(args, runtime) -> int`, and the unchanged `run_cli(args) -> int`.

- [ ] **Step 1: Record the full regression baseline**

Run:

```bash
pytest -q
python -m compileall -q scripts/netzoo_agent.py scripts/netzoo_agent_core
```

Expected: at least `316 passed, 12 skipped`; compileall exits `0`.

- [ ] **Step 2: Add failing CLI seam and exit-code tests**

Create `tests/test_cli_lifecycle.py` with package-path setup matching
`tests/test_cli_package.py`, then add these tests:

```python
from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.cli.bootstrap import CliRuntime
from netzoo_agent_core.contracts.state import AgentTurnInterrupted


def fake_cli_runtime(*, invoke_error, interactive_answers=()):
    answers = iter(interactive_answers)

    def input_func(_prompt: str) -> str:
        return next(answers)

    def invoke_graph_turn_func(_app, _invocation: dict) -> dict:
        raise invoke_error

    recorder = Mock()
    recorder.start_run.return_value = "test-run"
    return CliRuntime(
        memory=SimpleNamespace(
            profile_id="test-profile",
            profile_store=Mock(),
            episode_store=Mock(),
        ),
        project_policy=Mock(),
        session_id="test-session",
        resume_id=None,
        conversation=[],
        pending_plan=None,
        active_usage=None,
        run_id=None,
        recorder=recorder,
        trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None,
        app=object(),
        input_func=input_func,
        invoke_graph_turn_func=invoke_graph_turn_func,
    )


def test_cli_lifecycle_modules_define_the_intended_seams():
    commands = importlib.import_module("netzoo_agent_core.cli.commands")
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")

    assert str(inspect.signature(commands.handle_preflight_command)) == "(args) -> 'int | None'"
    assert str(inspect.signature(bootstrap.bootstrap_memory)) == "(args) -> 'MemoryRuntime'"
    assert str(inspect.signature(conversation.run_conversation)) == "(args, runtime: 'CliRuntime') -> 'int'"


def test_one_shot_ordinary_failure_returns_one(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = fake_cli_runtime(
        invoke_error=RuntimeError("provider unavailable"),
    )

    assert conversation.run_conversation(SimpleNamespace(task="run PANDA", keep_session=False), runtime) == 1


def test_interactive_ordinary_failure_can_continue(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = fake_cli_runtime(
        invoke_error=RuntimeError("provider unavailable"),
        interactive_answers=["first request", "exit"],
    )

    assert conversation.run_conversation(SimpleNamespace(task=None, keep_session=False), runtime) == 0


def test_interrupt_remains_130():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = fake_cli_runtime(
        invoke_error=AgentTurnInterrupted(),
    )

    assert conversation.run_conversation(SimpleNamespace(task="run PANDA", keep_session=False), runtime) == 130
```

Define `fake_cli_runtime` in the test file. It constructs the production
`CliRuntime` with `unittest.mock.Mock` stores/recorder, empty conversation state,
an `input_func` that consumes `interactive_answers`, and an
`invoke_graph_turn_func` that raises `invoke_error`. No test-only constructor or
test branch belongs in production code.

- [ ] **Step 3: Run the new tests and confirm the missing seams fail**

Run:

```bash
pytest -q tests/test_cli_lifecycle.py
```

Expected: collection or import failure because `commands`, `bootstrap`, and
`conversation` do not exist.

- [ ] **Step 4: Extract immediate commands without changing their text or order**

Create `cli/commands.py`. Move the current `--web-url`, trace status/export, memory
cleanup/status/delete, and policy status branches unchanged. Use these interfaces:

```python
@dataclass(frozen=True, slots=True)
class MemoryRuntime:
    profile_id: str
    profile_store: UserProfileStore
    episode_store: EpisodeStore
```

The exact interfaces are `handle_preflight_command(args) -> int | None`,
`handle_memory_command(args, runtime: MemoryRuntime) -> int | None`, and
`handle_policy_command(args, policy: ProjectPolicySnapshot) -> int | None`.
Each handler returns the current exit code when it handled a command and `None`
otherwise. Preserve every JSON key, message, indentation option, and validation
error.

- [ ] **Step 5: Extract bootstrap dependencies into typed contexts**

Create `cli/bootstrap.py` with:

```python
@dataclass(slots=True)
class CliRuntime:
    memory: MemoryRuntime
    project_policy: ProjectPolicySnapshot
    session_id: str
    resume_id: str | None
    conversation: list
    pending_plan: WorkflowPlan | None
    active_usage: dict | None
    run_id: str | None
    recorder: TraceRecorder
    trace_store: LocalTraceStore
    ensure_trace_sync: Callable[[str], None]
    app: object
    input_func: Callable[[str], str]
    invoke_graph_turn_func: Callable[[object, dict], dict]
```

The module defines `bootstrap_memory(args) -> MemoryRuntime`,
`load_project_policy() -> ProjectPolicySnapshot`, and
`bootstrap_runtime(args, memory_runtime: MemoryRuntime, policy:
ProjectPolicySnapshot) -> CliRuntime`. Production contexts use `input` and
`invoke_graph_turn` for the two injected callables.

Move the existing positive-limit checks, model validation, API-key check, cleanup,
resume loading, trace preflight/sync setup, and `build_graph` call without changing
their ordering relative to the immediate commands.

- [ ] **Step 6: Extract the conversation lifecycle**

Create `cli/conversation.py` and move the current loop beginning with `queued_task`
through terminal run handling. The seam is:

Its exact interface is `run_conversation(args, runtime: CliRuntime) -> int`.

Keep current prompts, clarification parsing, preference confirmation, session save,
token tracing, run pause/finish events, and ephemeral checkpoint deletion exact.
Change only the ordinary-exception branch:

```python
except Exception as error:
    recorder.append(
        run_id,
        "error.recorded",
        "cli",
        {"error_type": type(error).__name__, "message": str(error)},
    )
    _clear_transient_trace()
    print(_ui_text("The agent could not finish this request. No unfinished provider or local-tool step will be reported as completed."))
    print(_ui_text("Error type: ") + type(error).__name__)
    if one_shot:
        return 1
    next_prompt = NextTurnPrompt(
        kind="failed",
        question=_ui_text("Would you like to retry with a clearer request, describe a different NetZoo goal, or enter exit?"),
    )
    continue
```

Use injected callables on `CliRuntime` for input and Graph invocation in focused
tests; production defaults remain `input` and `invoke_graph_turn`.

- [ ] **Step 7: Reduce `run_cli` to lifecycle coordination**

Replace `cli/loop.py` with a coordinator shaped as:

```python
def run_cli(args) -> int:
    configure_runtime(
        EXECUTE_TOOLS=args.execute,
        TRACE_ENABLED=not args.quiet,
        VERBOSE_OUTPUT=args.verbose,
        TRANSIENT_TRACE=args.transient_trace and not args.verbose and not args.quiet,
        TOOL_TIMEOUT_SECONDS=args.tool_timeout,
    )
    if (result := handle_preflight_command(args)) is not None:
        return result
    memory_runtime = bootstrap_memory(args)
    if (result := handle_memory_command(args, memory_runtime)) is not None:
        return result
    policy = load_project_policy()
    if (result := handle_policy_command(args, policy)) is not None:
        return result
    runtime = bootstrap_runtime(args, memory_runtime, policy)
    return run_conversation(args, runtime)
```

Update `_CLI_IMPLEMENTATION_MODULES` and the legacy `_IMPLEMENTATION_MODULES` tuple
so historical monkeypatch propagation reaches the new owner modules.

- [ ] **Step 8: Verify CLI behavior and architecture**

Run:

```bash
pytest -q tests/test_cli_lifecycle.py tests/test_cli_package.py tests/test_netzoo_chat_launcher.py
python -m compileall -q scripts/netzoo_agent.py scripts/netzoo_agent_core/cli
pytest -q
```

Expected: all focused tests pass; the full suite passes with more than 316 passed
and 12 skipped.

- [ ] **Step 9: Commit the CLI extraction only**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/cli tests/test_cli_lifecycle.py tests/test_cli_package.py
git commit -m "refactor: deepen CLI lifecycle modules"
```

---

### Task 2: Convert memory into an owner-oriented package

**Files:**
- Create: `tests/test_memory_package.py`
- Delete: `scripts/netzoo_agent_core/memory.py`
- Create: `scripts/netzoo_agent_core/memory/__init__.py`
- Create: `scripts/netzoo_agent_core/memory/storage.py`
- Create: `scripts/netzoo_agent_core/memory/profiles.py`
- Create: `scripts/netzoo_agent_core/memory/normalization.py`
- Create: `scripts/netzoo_agent_core/memory/episodes.py`
- Modify: `scripts/netzoo_agent.py`
- Test: `tests/test_agent_gate.py`
- Test: `tests/test_agent_stability.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: the exact current 15-name `memory.__all__`, current store signatures,
  current on-disk Profile/Episode JSON, and the uncommitted UUID conversion in
  `_sanitize_json_payload`.
- Produces: an importable `netzoo_agent_core.memory` package whose facade objects
  are identical to their owner definitions.

- [ ] **Step 1: Add failing package, identity, and serialization tests**

Create `tests/test_memory_package.py`:

```python
from __future__ import annotations

import importlib
import inspect
import sys
import uuid
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent
import netzoo_agent_core.memory as memory

MEMORY_EXPORTS = [
    "_safe_memory_id", "_safe_json_text", "_sanitize_json_payload",
    "_ensure_private_directory", "_harden_private_tree", "_exclusive_file_lock",
    "_write_private_text", "_write_json_atomic", "UserProfileStore",
    "_episode_intent_type", "_meaningful_parameter_value",
    "normalize_episode_memory", "compact_episode_payload",
    "EpisodeCleanupReport", "EpisodeStore",
]


def test_memory_is_a_package_with_responsibility_owners():
    assert hasattr(memory, "__path__")
    for name in ("storage", "profiles", "normalization", "episodes"):
        importlib.import_module(f"netzoo_agent_core.memory.{name}")


def test_memory_surface_and_owner_identity_are_preserved():
    assert memory.__all__ == MEMORY_EXPORTS
    owners = {
        **{name: "storage" for name in MEMORY_EXPORTS[:8]},
        "UserProfileStore": "profiles",
        **{name: "normalization" for name in MEMORY_EXPORTS[9:13]},
        "EpisodeCleanupReport": "episodes",
        "EpisodeStore": "episodes",
    }
    for name, owner_name in owners.items():
        owner = importlib.import_module(f"netzoo_agent_core.memory.{owner_name}")
        assert getattr(memory, name) is getattr(owner, name)
        assert getattr(legacy_agent, name) is getattr(owner, name)


def test_uuid_json_sanitization_survives_package_conversion():
    value = uuid.uuid4()
    assert memory._sanitize_json_payload({"run_id": value}) == {"run_id": str(value)}


def test_store_signatures_are_preserved():
    assert str(inspect.signature(memory.UserProfileStore)) == "(root: 'Path | None' = None)"
    assert "max_episodes" in str(inspect.signature(memory.EpisodeStore))
```

- [ ] **Step 2: Run the package test and confirm it fails before conversion**

Run:

```bash
pytest -q tests/test_memory_package.py
```

Expected: failure because `memory` is still a module and has no package owners.

- [ ] **Step 3: Move storage primitives unchanged**

Create `memory/storage.py` from current lines 65–153. Preserve the UUID branch:

```python
def _sanitize_json_payload(value):
    if isinstance(value, str):
        return _safe_json_text(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {
            _safe_json_text(str(key)): _sanitize_json_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_json_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json_payload(item) for item in value]
    return value
```

Keep file modes, `fcntl` locking, `fsync`, random temporary naming, and atomic
`Path.replace` behavior exact.

- [ ] **Step 4: Move profile behavior unchanged**

Create `memory/profiles.py` containing `UserProfileStore`. Import storage helpers
from `.storage`, preference contracts from `..contracts.decisions` and
`..contracts.memory`, and paths from `..settings`. Preserve normalization,
confirmation, source truncation, deletion, and profile version checks exactly.

- [ ] **Step 5: Move normalization behavior unchanged**

Create `memory/normalization.py` containing `_episode_intent_type`,
`_meaningful_parameter_value`, `normalize_episode_memory`, and
`compact_episode_payload`. Import typed contracts directly from their owner modules
and constants from `settings`; perform no filesystem operations.

- [ ] **Step 6: Move episode repository behavior unchanged**

Create `memory/episodes.py` containing `EpisodeCleanupReport` and `EpisodeStore`.
Import filesystem operations from `.storage` and metadata construction from
`.normalization`. Preserve migration, quarantine, per-status retention, protected
workflow records, size/count pruning, scoring, record schema, and deletion exact.

- [ ] **Step 7: Build the stable memory facade and remove the old module**

Create `memory/__init__.py`:

```python
from . import episodes, normalization, profiles, storage
from .episodes import EpisodeCleanupReport, EpisodeStore
from .normalization import (
    _episode_intent_type,
    _meaningful_parameter_value,
    compact_episode_payload,
    normalize_episode_memory,
)
from .profiles import UserProfileStore
from .storage import (
    _ensure_private_directory,
    _exclusive_file_lock,
    _harden_private_tree,
    _safe_json_text,
    _safe_memory_id,
    _sanitize_json_payload,
    _write_json_atomic,
    _write_private_text,
)

_MEMORY_IMPLEMENTATION_MODULES = (storage, profiles, normalization, episodes)

__all__ = [
    "_safe_memory_id", "_safe_json_text", "_sanitize_json_payload",
    "_ensure_private_directory", "_harden_private_tree", "_exclusive_file_lock",
    "_write_private_text", "_write_json_atomic", "UserProfileStore",
    "_episode_intent_type", "_meaningful_parameter_value",
    "normalize_episode_memory", "compact_episode_payload",
    "EpisodeCleanupReport", "EpisodeStore",
]
```

Delete `memory.py`. Add `_MEMORY_IMPLEMENTATION_MODULES` to the legacy facade tuple
without exceeding the 150-line entrypoint constraint.

- [ ] **Step 8: Verify memory behavior and stored-data compatibility**

Run:

```bash
pytest -q tests/test_memory_package.py tests/test_agent_gate.py tests/test_agent_stability.py tests/test_graph_tracing.py
python -m compileall -q scripts/netzoo_agent.py scripts/netzoo_agent_core/memory
pytest -q
```

Expected: all focused and full tests pass; existing profile/episode tests require no
behavioral expectation changes.

- [ ] **Step 9: Commit only the memory conversion**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/memory.py scripts/netzoo_agent_core/memory tests/test_memory_package.py
git commit -m "refactor: package memory persistence"
```

---

### Task 3: Make the data dependency direction explicit

**Files:**
- Modify: `tests/test_data_package.py`
- Modify: `tests/test_agent_module_boundaries.py`
- Create: `scripts/netzoo_agent_core/data/discovery.py`
- Create: `scripts/netzoo_agent_core/data/tables.py`
- Create: `scripts/netzoo_agent_core/data/transforms.py`
- Create: `scripts/netzoo_agent_core/tool_adapters.py`
- Modify: `scripts/netzoo_agent_core/data/table_validation.py`
- Modify: `scripts/netzoo_agent_core/data/preparation.py`
- Modify: `scripts/netzoo_agent_core/data/bundles.py`
- Modify: `scripts/netzoo_agent_core/data/inspection.py`
- Modify: `scripts/netzoo_agent_core/data/__init__.py`
- Modify: `scripts/netzoo_agent_core/interpretation/discovery.py`
- Modify: `scripts/netzoo_agent_core/execution.py`
- Modify: `scripts/netzoo_agent_core/validation.py`
- Modify: `scripts/netzoo_agent_core/preparation.py`
- Modify: `scripts/netzoo_agent_core/compatibility.py`
- Modify: `scripts/netzoo_agent.py`

**Interfaces:**
- Consumes: current decorated tools and their exact signatures/outputs, current
  table helpers, current bundle-selection behavior, and mutable `EXECUTE_TOOLS`
  propagation through the legacy facade.
- Produces: pure `data.tables` and `data.transforms` owners, neutral
  `data.discovery`, decorated tools in `tool_adapters`, and unchanged compatibility
  import paths.

- [ ] **Step 1: Strengthen data owner, adapter, and forbidden-import tests**

Update `tests/test_data_package.py` to require:

```python
def test_data_has_pure_owners_and_external_tool_adapters():
    tables = importlib.import_module("netzoo_agent_core.data.tables")
    transforms = importlib.import_module("netzoo_agent_core.data.transforms")
    discovery = importlib.import_module("netzoo_agent_core.data.discovery")
    adapters = importlib.import_module("netzoo_agent_core.tool_adapters")

    assert validation.inspect_netzoo_inputs is adapters.inspect_netzoo_inputs
    assert preparation.format_expression_for_netzoo is adapters.format_expression_for_netzoo
    assert preparation.convert_expression_to_coexpression is adapters.convert_expression_to_coexpression
    assert not hasattr(tables.inspect_netzoo_inputs_report, "invoke")
    assert not hasattr(transforms.format_expression_for_netzoo_impl, "invoke")


def test_pure_data_owners_have_no_upward_or_framework_imports():
    forbidden = {
        "cli", "evaluation", "execution", "graph", "interpretation", "planning",
        "routing", "framework_compat", "tool_adapters",
    }
    for module_name in ("discovery", "tables", "transforms", "inspection", "bundles", "paths", "artifacts"):
        module = importlib.import_module(f"netzoo_agent_core.data.{module_name}")
        tree = ast.parse(inspect.getsource(module))
        dependencies = {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level >= 1
        }
        assert dependencies.isdisjoint(forbidden), (module_name, dependencies & forbidden)
```

Extend `test_data_layer_does_not_depend_on_orchestration_layers` so the forbidden
set includes `interpretation`, `routing`, and framework/tool adapter modules for the
pure owner list rather than compatibility facades.

- [ ] **Step 2: Run the strengthened tests and confirm the old direction fails**

Run:

```bash
pytest -q tests/test_data_package.py tests/test_agent_module_boundaries.py
```

Expected: failure because pure owners and `tool_adapters` do not exist and
`data.bundles` imports `interpretation`.

- [ ] **Step 3: Move neutral discovery primitives downward**

Create `data/discovery.py` and move `_candidate_keywords` and `_best_named_file`
from `interpretation/discovery.py`, plus the file scoring primitive currently in
`routing/discovery.py` when needed by `_best_named_file`. Keep scoring constants and
ordering exact. Update both interpretation discovery and bundle discovery to import
these primitives from `data.discovery`; `data.bundles` must no longer import
`interpretation`.

- [ ] **Step 4: Split pure table behavior from its historical facade**

Move `TableCheck` and all non-decorated parsing/validation functions from
`data/table_validation.py` to `data/tables.py`. Add the pure external function:

```python
def inspect_netzoo_inputs_report(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
) -> str:
    report, _, _ = _inspect_panda_inputs_impl(
        expression_file=expression_file,
        motif_file=motif_file,
        ppi_file=ppi_file,
        mirna_file=mirna_file,
    )
    return report
```

Make `data/table_validation.py` a facade re-exporting table helpers from `.tables`
and the decorated `inspect_netzoo_inputs` from `..tool_adapters`.

- [ ] **Step 5: Split pure transformations from execution-mode adaptation**

Move transformation implementations to `data/transforms.py` and add explicit write
arguments while preserving output strings:

The exact pure interfaces are
`format_expression_for_netzoo_impl(expression_file: str, output_file: str,
genes_axis: str = "auto", with_header: bool = False, *, execute: bool) -> str`
and `convert_expression_to_coexpression_impl(expression_file: str, output_file:
str, *, execute: bool) -> str`.

Replace reads of mutable `EXECUTE_TOOLS` inside these functions with the explicit
`execute` value. Do not change validation order, output paths, table orientation,
numeric calculation, dry-run wording, or write format.

- [ ] **Step 6: Create decorated tool adapters and compatibility facades**

Create `tool_adapters.py`:

```python
from . import settings
from .data.tables import inspect_netzoo_inputs_report
from .data.transforms import (
    convert_expression_to_coexpression_impl,
    format_expression_for_netzoo_impl,
)
from .framework_compat import tool


@tool
def inspect_netzoo_inputs(expression_file: str, motif_file: str, ppi_file: str, mirna_file: str = "") -> str:
    return inspect_netzoo_inputs_report(expression_file, motif_file, ppi_file, mirna_file)


@tool
def format_expression_for_netzoo(expression_file: str, output_file: str, genes_axis: str = "auto", with_header: bool = False) -> str:
    return format_expression_for_netzoo_impl(
        expression_file, output_file, genes_axis, with_header,
        execute=settings.EXECUTE_TOOLS,
    )


@tool
def convert_expression_to_coexpression(expression_file: str, output_file: str) -> str:
    return convert_expression_to_coexpression_impl(
        expression_file, output_file, execute=settings.EXECUTE_TOOLS,
    )


__all__ = [
    "inspect_netzoo_inputs",
    "format_expression_for_netzoo",
    "convert_expression_to_coexpression",
]
```

Make `data/preparation.py`, top-level `preparation.py`, and top-level `validation.py`
re-export these adapter objects while keeping their historical `__all__` order.
Re-export pure helper names from `data.tables` through validation facades.

- [ ] **Step 7: Update internal owners and runtime propagation**

Update:

- `execution.py` to import pure table helpers from `data.tables` and decorated
  transformation tools from `tool_adapters`;
- `data.inspection`, `data.bundles`, and `interpretation.discovery` to import pure
  owners;
- `compatibility.py` to keep using the stable validation facade;
- `data.__init__` to eagerly import only pure owner modules; compatibility facades
  remain importable by their full module paths but must not cause `import
  netzoo_agent_core.data` to load LangChain adapters;
- `scripts/netzoo_agent.py` to include `tool_adapters` in
  `_IMPLEMENTATION_MODULES`, ensuring `EXECUTE_TOOLS` monkeypatch behavior remains
  observable through the adapter's read of `settings.EXECUTE_TOOLS`.

Run `rg` to verify direction:

```bash
rg -n '^from \.\.(interpretation|routing|execution|planning|evaluation|graph|cli|framework_compat|tool_adapters)' scripts/netzoo_agent_core/data/discovery.py scripts/netzoo_agent_core/data/tables.py scripts/netzoo_agent_core/data/transforms.py scripts/netzoo_agent_core/data/inspection.py scripts/netzoo_agent_core/data/bundles.py scripts/netzoo_agent_core/data/paths.py scripts/netzoo_agent_core/data/artifacts.py
```

Expected: no matches.

- [ ] **Step 8: Verify adapter identity, output behavior, and dependency direction**

Run:

```bash
pytest -q tests/test_data_package.py tests/test_agent_module_boundaries.py tests/test_agent_gate.py tests/test_agent_artifacts.py tests/test_dataset_bundles.py tests/test_path_and_output_safety.py
python -m compileall -q scripts/netzoo_agent.py scripts/netzoo_agent_core
pytest -q
```

Expected: focused and full tests pass with no legacy output expectation changes.

- [ ] **Step 9: Commit only the data-direction work**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/data scripts/netzoo_agent_core/tool_adapters.py scripts/netzoo_agent_core/interpretation/discovery.py scripts/netzoo_agent_core/execution.py scripts/netzoo_agent_core/validation.py scripts/netzoo_agent_core/preparation.py scripts/netzoo_agent_core/compatibility.py tests/test_data_package.py tests/test_agent_module_boundaries.py
git commit -m "refactor: enforce data dependency direction"
```

---

### Task 4: Add a maintained code-reading path

**Files:**
- Create: `CODE_READING_GUIDE.md`
- Modify: `README.md`
- Modify: `NETZOO_HARNESS_ARCHITECTURE.md`
- Modify: `tests/test_agent_module_boundaries.py`

**Interfaces:**
- Consumes: final CLI, memory, data, planning, evaluation, graph, and execution owner
  paths from Tasks 1–3.
- Produces: a basic-Python orientation guide linked from maintained project entry
  documents and guarded against stale core paths.

- [ ] **Step 1: Add a failing documentation navigation assertion**

Add to `tests/test_agent_module_boundaries.py`:

```python
def test_code_reading_guide_points_to_current_owner_modules(self):
    guide = (PROJECT_ROOT / "CODE_READING_GUIDE.md").read_text(encoding="utf-8")
    required_paths = (
        "scripts/netzoo_agent.py",
        "scripts/netzoo_agent_core/cli/loop.py",
        "scripts/netzoo_agent_core/cli/conversation.py",
        "scripts/netzoo_agent_core/graph/topology.py",
        "scripts/netzoo_agent_core/planning/builder.py",
        "scripts/netzoo_agent_core/evaluation/plan_review.py",
        "scripts/netzoo_agent_core/execution.py",
        "scripts/netzoo_agent_core/memory/episodes.py",
        "scripts/netzoo_agent_core/data/tables.py",
    )
    for path in required_paths:
        self.assertIn(path, guide)
        self.assertTrue((PROJECT_ROOT / path).exists(), path)
```

- [ ] **Step 2: Run the assertion and confirm the guide is missing**

Run:

```bash
pytest -q tests/test_agent_module_boundaries.py::AgentModuleBoundaryTests::test_code_reading_guide_points_to_current_owner_modules
```

Expected: failure because `CODE_READING_GUIDE.md` does not exist.

- [ ] **Step 3: Write the 15-minute reading route**

Create `CODE_READING_GUIDE.md` for a basic-Python reader. Begin with this ordered
route and explain what question each file answers:

```text
1. scripts/netzoo_agent.py                         compatibility entrypoint
2. scripts/netzoo_agent_core/cli/loop.py           startup coordination
3. scripts/netzoo_agent_core/cli/conversation.py   one request/session lifecycle
4. scripts/netzoo_agent_core/graph/topology.py      legal state transitions
5. scripts/netzoo_agent_core/graph/routing_planning.py
6. scripts/netzoo_agent_core/planning/builder.py
7. scripts/netzoo_agent_core/evaluation/plan_review.py
8. scripts/netzoo_agent_core/graph/execution.py
9. scripts/netzoo_agent_core/execution.py
10. scripts/netzoo_agent_core/graph/response.py
```

Explicitly tell the reader to skip compatibility tuples, storage internals, trace
hashing, and archived plans on the first pass.

- [ ] **Step 4: Add a concrete PANDA request trace and state map**

Trace this example:

```text
Run PANDA using data/expression.tsv, data/motif.tsv, and data/ppi.tsv;
write outputs/panda.tsv.
```

At each stage name the input type, owner function, state fields changed, output
type, and next transition. Cover `HumanMessage`, `TaskDecision`, `WorkflowPlan`,
`PlanEvaluationResult`, `ToolExecutionResult`, `EvaluationResult`, memory
consolidation, and final response.

- [ ] **Step 5: Add debugging maps, change recipes, commands, and glossary**

Include:

- symptom-to-owner table for CLI, routing, missing inputs, table validation,
  execution, recovery, memory, tracing, and response;
- recipes for adding a workflow input, changing validation, changing a CLI flag,
  changing response rendering, and diagnosing recovery;
- focused `pytest` and `rg` commands using current paths;
- glossary entries for module, interface, seam, adapter, Router, Planner, Plan
  Evaluator, Executor, Result Evaluator, Graph state, and episode memory.

- [ ] **Step 6: Link maintained documents and remove the duplicate README row**

Add `CODE_READING_GUIDE.md` once to the README's main-document table, keep one
architecture row, and add a “Start reading the code” link near the architecture
section. Update the architecture tree for `cli`, `memory`, pure data owners, and
`tool_adapters.py`, then link back to the reading guide.

- [ ] **Step 7: Verify guide paths, docs, and full behavior**

Run:

```bash
pytest -q tests/test_agent_module_boundaries.py
rg -n 'CODE_READING_GUIDE.md' README.md NETZOO_HARNESS_ARCHITECTURE.md
git diff --check
pytest -q
```

Expected: every path assertion passes, each maintained document links to the guide,
no whitespace errors exist, and the full suite remains green.

- [ ] **Step 8: Commit documentation and navigation assertions**

```bash
git add CODE_READING_GUIDE.md README.md NETZOO_HARNESS_ARCHITECTURE.md tests/test_agent_module_boundaries.py
git commit -m "docs: add guided core reading path"
```

---

### Task 5: Final compatibility and architecture audit

**Files:**
- Verify: `scripts/netzoo_agent.py`
- Verify: `scripts/netzoo_agent_core/`
- Verify: `tests/`
- Verify: `CODE_READING_GUIDE.md`

**Interfaces:**
- Consumes: all four completed task commits.
- Produces: final evidence that behavior, legacy seams, dependency direction, and
  documentation agree.

- [ ] **Step 1: Run the complete verification suite on the final tree**

```bash
pytest -q
python -m compileall -q scripts/netzoo_agent.py scripts/netzoo_agent_core
git diff --check
```

Expected: more than 316 tests pass, 12 remain intentionally skipped, compileall and
diff checks exit `0`.

- [ ] **Step 2: Run the focused architecture and compatibility suites**

```bash
pytest -q tests/test_cli_package.py tests/test_cli_lifecycle.py tests/test_memory_package.py tests/test_data_package.py tests/test_agent_module_boundaries.py tests/test_legacy_facade.py
```

Expected: all pass.

- [ ] **Step 3: Audit dependency direction and navigation metrics**

```bash
rg -n '^from \.{1,3}contracts import' scripts/netzoo_agent_core/cli scripts/netzoo_agent_core/memory scripts/netzoo_agent_core/data scripts/netzoo_agent_core/tool_adapters.py
wc -l scripts/netzoo_agent.py scripts/netzoo_agent_core/cli/*.py scripts/netzoo_agent_core/memory/*.py scripts/netzoo_agent_core/data/*.py
git status --short
```

Expected: touched implementation files use direct owner imports except documented
compatibility facades; `run_cli` is short; memory responsibilities are distributed;
unrelated dirty-worktree entries remain present but uncommitted by this work.

- [ ] **Step 4: Review the complete commit range**

Review from the design commit through the documentation commit for:

- exact spec coverage;
- accidental output or schema changes;
- legacy facade identity;
- one-shot and interactive exit semantics;
- data-to-framework or data-to-orchestration regressions;
- stale reading-guide paths.

Fix any finding in the owning task's files, rerun its focused tests, then rerun the
complete suite before completion.
