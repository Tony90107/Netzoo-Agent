# Interactive Execution Mode Slash Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the NetZoo CLI's startup `--execute` flag with persistent, explicit `/test` and `/execute` session commands plus `/status` and `/help`.

**Architecture:** A focused `cli/slash_commands.py` module will parse CLI-owned control input, change the existing process-wide `EXECUTE_TOOLS` setting through `configure_runtime`, and render the active mode. The conversation coordinator will intercept handled commands at every interactive input boundary before trace creation or graph invocation; non-interactive `--task` runs will always start test-only.

**Tech Stack:** Python 3, argparse, dataclasses, pytest, unittest.mock, existing NetZoo runtime compatibility bridge.

## Global Constraints

- `./netzoo-chat` always starts in `TEST` mode.
- `/execute` and `/test` persist until another mode command changes the current process.
- `/status` and `/help` never become tasks, traces, Router calls, or response-model calls.
- Slash commands are available at the main, clarification, and preference-confirmation prompts.
- Absolute paths such as `/work/data/expression.tsv` and `/expression.tsv` remain valid inputs.
- The legacy `--execute` argument is removed; non-interactive `--task` remains test-only.
- Planner, Plan Evaluator, validation, allowlists, output safety, and timeouts remain unchanged.
- User-visible output remains English.
- Preserve unrelated dirty-worktree changes and do not edit archived historical documents.

## File Map

- Create `scripts/netzoo_agent_core/cli/slash_commands.py`: parse CLI control input, change/read execution mode, and render prompt mode labels.
- Create `tests/test_cli_slash_commands.py`: focused unit tests for parsing, path disambiguation, mode changes, help, status, and error text.
- Modify `scripts/netzoo_agent_core/cli/conversation.py`: intercept slash commands at every interactive input boundary and show the current mode.
- Modify `scripts/netzoo_agent_core/cli/arguments.py`: remove `--execute`.
- Modify `scripts/netzoo_agent_core/cli/loop.py`: reset every CLI process to test mode without reading `args.execute`.
- Modify `scripts/netzoo_agent_core/cli/__init__.py`: register the new responsibility module without expanding the stable top-level CLI export surface.
- Modify `tests/test_cli_lifecycle.py`: prove handled commands do not invoke the graph or trace recorder and preserve pending prompts.
- Modify `tests/test_cli_package.py`: prove the module boundary exists and argparse rejects `--execute`.
- Modify `scripts/netzoo_agent_core/cli/follow_up.py`, `scripts/netzoo_agent_core/evaluation/rendering.py`, `scripts/netzoo_agent_core/command.py`, and `scripts/netzoo_agent_core/data/transforms.py`: replace restart/flag guidance with interactive slash-command guidance.
- Modify `tests/test_agent_gate.py` and `tests/test_command_processes.py`: update dry-run guidance assertions and exercise `_run_command` directly.
- Modify `AGENTS.md`, `README.md`, and `AGENT_USAGE.md`: document the new authorization boundary and commands.

---

### Task 1: Slash-command parser and runtime mode controller

**Files:**
- Create: `scripts/netzoo_agent_core/cli/slash_commands.py`
- Create: `tests/test_cli_slash_commands.py`
- Modify: `scripts/netzoo_agent_core/cli/__init__.py`
- Modify: `tests/test_cli_package.py`

**Interfaces:**
- Consumes: `netzoo_agent_core.runtime.configure_runtime(**values)` and `netzoo_agent_core.settings.EXECUTE_TOOLS`.
- Produces: `SlashCommandResult(handled: bool, message: str)`, `handle_slash_command(user_input: str) -> SlashCommandResult`, `current_mode_label() -> str`, and `render_mode_prompt(prompt: str) -> str`.

- [ ] **Step 1: Write failing parser and package-boundary tests**

Create `tests/test_cli_slash_commands.py` with deterministic runtime cleanup:

```python
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.slash_commands import (  # noqa: E402
    current_mode_label,
    handle_slash_command,
    render_mode_prompt,
)
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402


@pytest.fixture(autouse=True)
def restore_execution_mode():
    previous = settings.EXECUTE_TOOLS
    configure_runtime(EXECUTE_TOOLS=False)
    yield
    configure_runtime(EXECUTE_TOOLS=previous)


def test_natural_language_and_absolute_paths_are_not_slash_commands():
    for user_input in (
        "run PANDA",
        "/work/data/expression.tsv",
        "/expression.tsv",
        "expression_file=/data/expression.tsv",
    ):
        result = handle_slash_command(user_input)
        assert result.handled is False
        assert result.message == ""


def test_execute_and_test_switch_the_process_mode_persistently():
    execute = handle_slash_command("/execute")
    assert execute.handled is True
    assert "Execution mode enabled" in execute.message
    assert settings.EXECUTE_TOOLS is True
    assert current_mode_label() == "EXECUTE"
    assert render_mode_prompt("Question") == "[EXECUTE] Question"

    test = handle_slash_command("/TEST")
    assert test.handled is True
    assert "Test mode enabled" in test.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "TEST"


def test_status_and_help_report_without_changing_mode():
    status = handle_slash_command("/status")
    assert status == type(status)(handled=True, message="Current mode: TEST")

    help_result = handle_slash_command("/help")
    assert help_result.handled is True
    for command in ("/test", "/execute", "/status", "/help"):
        assert command in help_result.message
    assert settings.EXECUTE_TOOLS is False


def test_unknown_command_and_trailing_arguments_are_consumed_locally():
    unknown = handle_slash_command("/exec")
    assert unknown.handled is True
    assert "Unknown slash command: /exec" in unknown.message
    assert "/help" in unknown.message

    arguments = handle_slash_command("/execute run PANDA")
    assert arguments.handled is True
    assert "Enter /execute by itself" in arguments.message
    assert settings.EXECUTE_TOOLS is False
```

In `tests/test_cli_package.py`, add `slash_commands` to the module-import loop without adding it to `CLI_EXPORTS`:

```python
for name in (
    "arguments",
    "trace_commands",
    "clarification",
    "commands",
    "conversation",
    "follow_up",
    "loop",
    "main",
    "slash_commands",
):
    importlib.import_module(f"netzoo_agent_core.cli.{name}")
```

- [ ] **Step 2: Run focused tests and verify the missing module fails**

Run:

```bash
python -m pytest tests/test_cli_slash_commands.py tests/test_cli_package.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'netzoo_agent_core.cli.slash_commands'`.

- [ ] **Step 3: Implement the focused slash-command module**

Create `scripts/netzoo_agent_core/cli/slash_commands.py`:

```python
"""CLI-owned slash commands for interactive execution authority."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .. import settings
from ..runtime import configure_runtime

__all__ = [
    "SlashCommandResult",
    "current_mode_label",
    "handle_slash_command",
    "render_mode_prompt",
]

_COMMAND_TOKEN = re.compile(r"^/[A-Za-z][A-Za-z0-9_-]*(?:\s+.*)?$")
_KNOWN_COMMANDS = frozenset({"/test", "/execute", "/status", "/help"})


@dataclass(frozen=True, slots=True)
class SlashCommandResult:
    handled: bool
    message: str = ""


def current_mode_label() -> str:
    return "EXECUTE" if settings.EXECUTE_TOOLS else "TEST"


def render_mode_prompt(prompt: str) -> str:
    return f"[{current_mode_label()}] {prompt}"


def handle_slash_command(user_input: str) -> SlashCommandResult:
    stripped = user_input.strip()
    if not _COMMAND_TOKEN.fullmatch(stripped):
        return SlashCommandResult(handled=False)

    command, *arguments = stripped.split(maxsplit=1)
    normalized = command.casefold()
    if normalized not in _KNOWN_COMMANDS:
        return SlashCommandResult(
            handled=True,
            message=(
                f"Unknown slash command: {command}. "
                "Enter /help to list available commands."
            ),
        )
    if arguments:
        return SlashCommandResult(
            handled=True,
            message=f"Slash commands do not accept arguments. Enter {normalized} by itself.",
        )
    if normalized == "/execute":
        configure_runtime(EXECUTE_TOOLS=True)
        return SlashCommandResult(
            handled=True,
            message=(
                "Execution mode enabled. Future workflow tasks will run commands."
            ),
        )
    if normalized == "/test":
        configure_runtime(EXECUTE_TOOLS=False)
        return SlashCommandResult(
            handled=True,
            message=(
                "Test mode enabled. Future workflow tasks will only create previews."
            ),
        )
    if normalized == "/status":
        return SlashCommandResult(
            handled=True,
            message=f"Current mode: {current_mode_label()}",
        )
    return SlashCommandResult(
        handled=True,
        message=(
            "Slash commands:\n"
            "  /test     Preview validated workflow commands without running them.\n"
            "  /execute  Run validated workflow commands for future tasks.\n"
            "  /status   Show the current execution mode.\n"
            "  /help     Show this help."
        ),
    )
```

Modify `scripts/netzoo_agent_core/cli/__init__.py` so the package owns the module while `CLI_EXPORTS` stays unchanged:

```python
from . import (
    arguments,
    bootstrap,
    clarification,
    commands,
    conversation,
    follow_up,
    loop,
    slash_commands,
    trace_commands,
)
```

Do not add slash-command symbols to `cli.__all__` or the historical `netzoo_agent` facade.

- [ ] **Step 4: Run focused tests and verify they pass**

Run:

```bash
python -m pytest tests/test_cli_slash_commands.py tests/test_cli_package.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the parser boundary**

```bash
git add scripts/netzoo_agent_core/cli/slash_commands.py scripts/netzoo_agent_core/cli/__init__.py tests/test_cli_slash_commands.py tests/test_cli_package.py
git commit -m "feat: add interactive execution slash commands"
```

---

### Task 2: Interactive lifecycle integration and legacy flag removal

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/conversation.py`
- Modify: `scripts/netzoo_agent_core/cli/arguments.py`
- Modify: `scripts/netzoo_agent_core/cli/loop.py`
- Modify: `tests/test_cli_lifecycle.py`
- Modify: `tests/test_cli_package.py`

**Interfaces:**
- Consumes: `handle_slash_command(answer)`, `render_mode_prompt(prompt)`, and `configure_runtime(EXECUTE_TOOLS=False)`.
- Produces: command interception before exit/task processing at all three interactive prompt types; every process starts in test mode; `parse_args()` has no `execute` attribute.

- [ ] **Step 1: Write failing lifecycle and argparse tests**

Change `_fake_cli_runtime` in `tests/test_cli_lifecycle.py` so the two injected callables are mocks that tests can inspect:

```python
def _fake_cli_runtime(*, invoke_error, interactive_answers=()):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    input_func = Mock(side_effect=interactive_answers)
    invoke_graph_turn_func = Mock(side_effect=invoke_error)

    recorder = Mock()
    recorder.start_run.return_value = "test-run"
    return bootstrap.CliRuntime(
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
```

Add imports for `configure_runtime`, `settings`, `InputEvidence`, `PreferenceProposal`, `TaskDecision`, and `WorkflowPlan`, then add these lifecycle tests:

```python
def _decision() -> TaskDecision:
    return TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
    )


def test_main_prompt_commands_switch_mode_without_graph_or_trace(capsys):
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=False)
        runtime = _fake_cli_runtime(
            invoke_error=AssertionError("graph must not run"),
            interactive_answers=["/execute", "/status", "/test", "exit"],
        )

        result = conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        )

        assert result == 0
        runtime.invoke_graph_turn_func.assert_not_called()
        runtime.recorder.start_run.assert_not_called()
        prompts = [call.args[0] for call in runtime.input_func.call_args_list]
        assert prompts[0].startswith("\n[TEST]")
        assert prompts[1].startswith("\n[EXECUTE]")
        assert "Execution mode enabled" in capsys.readouterr().out
        assert settings.EXECUTE_TOOLS is False
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_slash_command_does_not_consume_missing_input_state():
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="run PANDA",
        decision=_decision().model_dump(),
        evidence=[
            InputEvidence(
                field="expression_file",
                status="missing",
                reason="required",
                candidates=["data/expression.tsv"],
            )
        ],
        missing_inputs=["expression_file"],
        status="needs_input",
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/status", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.invoke_graph_turn_func.assert_not_called()
    prompts = [call.args[0] for call in runtime.input_func.call_args_list]
    assert sum("expression_file" in prompt for prompt in prompts) == 2


def test_slash_command_does_not_confirm_preference():
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="remember preference",
        decision=TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=1.0,
            reason="test",
        ).model_dump(),
        status="needs_confirmation",
        preference_proposals=[
            PreferenceProposal(
                key="reuse_last_inputs",
                value="true",
                reason="explicit request",
            )
        ],
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/help", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.memory.profile_store.confirm.assert_not_called()
    runtime.invoke_graph_turn_func.assert_not_called()
```

Add this argparse regression to `tests/test_cli_package.py`:

```python
def test_execute_startup_flag_is_removed(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["netzoo_agent.py", "--execute"])

    with pytest.raises(SystemExit) as error:
        cli.parse_args()

    assert error.value.code == 2
```

- [ ] **Step 2: Run lifecycle tests and verify they fail for the intended reasons**

Run:

```bash
python -m pytest tests/test_cli_lifecycle.py tests/test_cli_package.py -q
```

Expected: slash inputs reach the graph, prompts lack mode markers, and argparse still accepts `--execute`.

- [ ] **Step 3: Intercept commands at all interactive boundaries**

In `scripts/netzoo_agent_core/cli/conversation.py`, import the handler:

```python
from .slash_commands import handle_slash_command, render_mode_prompt
```

Add a private helper beside `run_conversation`:

```python
def _handle_interactive_control(answer: str) -> bool:
    result = handle_slash_command(answer)
    if not result.handled:
        return False
    print(_ui_text(result.message))
    return True
```

Change the startup message to expose mode and discovery:

```python
print(
    _ui_text(
        "NetZoo agent started. Current mode: TEST. "
        "Enter /help for controls, or exit or quit to stop."
    )
)
```

Wrap each of the three prompt strings with `render_mode_prompt(...)`. Immediately
after each `input_func(...).strip()` and before exit, yes/no, path, or task
handling, add:

```python
if _handle_interactive_control(answer):
    continue
```

For the main prompt, render:

```python
answer = input_func(
    f"\n{render_mode_prompt(render_next_turn_prompt(next_prompt))}\n> "
).strip()
```

For preference confirmation and clarification, pass their complete existing
prompt strings through `render_mode_prompt` before `input_func`. Do not move
`recorder.start_run`; keeping command interception above task construction is
what guarantees no trace is created.

- [ ] **Step 4: Remove startup execution authority**

Delete the complete `parser.add_argument("--execute", ...)` block from
`scripts/netzoo_agent_core/cli/arguments.py`.

In `scripts/netzoo_agent_core/cli/loop.py`, replace:

```python
EXECUTE_TOOLS=args.execute,
```

with:

```python
EXECUTE_TOOLS=False,
```

This reset must happen before preflight commands and runtime bootstrap so a
second `run_cli` call in the same Python process cannot inherit execute mode.

- [ ] **Step 5: Run lifecycle and parser tests**

Run:

```bash
python -m pytest tests/test_cli_slash_commands.py tests/test_cli_lifecycle.py tests/test_cli_package.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the interactive integration**

```bash
git add scripts/netzoo_agent_core/cli/conversation.py scripts/netzoo_agent_core/cli/arguments.py scripts/netzoo_agent_core/cli/loop.py tests/test_cli_lifecycle.py tests/test_cli_package.py
git commit -m "feat: switch execution mode inside netzoo chat"
```

---

### Task 3: Replace legacy execution guidance and document the workflow

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/follow_up.py`
- Modify: `scripts/netzoo_agent_core/evaluation/rendering.py`
- Modify: `scripts/netzoo_agent_core/command.py`
- Modify: `scripts/netzoo_agent_core/data/transforms.py`
- Modify: `tests/test_agent_gate.py`
- Modify: `tests/test_command_processes.py`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`

**Interfaces:**
- Consumes: the four slash commands and persistent session semantics from Tasks 1 and 2.
- Produces: all current operational guidance points users to `/execute` inside `./netzoo-chat`; archived documents remain historical and unchanged.

- [ ] **Step 1: Change assertions to require slash-command guidance**

Update `test_dry_run_gets_command_preview_follow_up` in
`tests/test_agent_gate.py`:

```python
self.assertIn("/execute", prompt.question)
self.assertNotIn("--execute", prompt.question)
```

Update `test_compact_execution_renderer_keeps_only_material_result_details`:

```python
self.assertIn("enter /execute", rendered)
self.assertNotIn("rerun with --execute", rendered)
```

Add a focused test to `tests/test_command_processes.py`:

```python
def test_dry_run_points_to_interactive_slash_command(self):
    previous_execute = agent.EXECUTE_TOOLS
    agent.EXECUTE_TOOLS = False
    try:
        output = agent._run_command(["run-panda", "--help"])
    finally:
        agent.EXECUTE_TOOLS = previous_execute

    self.assertIn("interactive `./netzoo-chat` session", output)
    self.assertIn("`/execute`", output)
    self.assertNotIn("--execute", output)
```

- [ ] **Step 2: Run focused agent-gate tests and verify old text fails**

Run:

```bash
python -m pytest tests/test_agent_gate.py -q
```

Expected: the updated dry-run guidance assertions fail because runtime text still mentions `--execute`.

- [ ] **Step 3: Replace every current runtime instruction**

Use these exact messages:

In `scripts/netzoo_agent_core/cli/follow_up.py`:

```python
question=_ui_text(
    f"The {plan.workflow} command preview is ready. Would you like to "
    "adjust its inputs or explore another workflow? Enter /execute to "
    "enable execution in this session."
),
```

In `scripts/netzoo_agent_core/evaluation/rendering.py`:

```python
lines.extend(
    ["", "Next: enter /execute, then submit the task again to perform the analysis."]
)
```

In `scripts/netzoo_agent_core/command.py`:

```python
"Enter `/execute` in an interactive `./netzoo-chat` session before "
"submitting the task to run the tool."
```

In `scripts/netzoo_agent_core/data/transforms.py`:

```python
"- dry run only; validation passed but no output file was written. "
"Enter /execute in an interactive ./netzoo-chat session before submitting "
"the task to write it."
```

- [ ] **Step 4: Update policy and operational documentation**

In `AGENTS.md`, replace the startup-flag rule with:

```markdown
- `./netzoo-chat` 啟動時只能建立 command preview；只有使用者在目前互動 session
  明確輸入 `/execute` 後才能執行，輸入 `/test` 會撤銷該授權。
```

In `README.md`, replace the non-interactive `--execute --task` example with:

````markdown
真的執行必須進入互動模式，明確切換後再輸入任務：

```bash
./netzoo-chat
```

```text
[TEST] What would you like to accomplish with NetZoo?
> /execute
Execution mode enabled. Future workflow tasks will run commands.
[EXECUTE] What would you like to accomplish with NetZoo?
> 我要跑 PUMA，expression 是 data/expression.tsv，motif 是 data/motif.tsv，PPI 是 data/ppi.tsv，miRNA 是 data/mir.tsv，輸出 outputs/puma.tsv
```

`--task` 是非互動 preview-only 介面，不接受 `--execute`。
````

In `AGENT_USAGE.md`:

- replace security-boundary references to `--execute` with `/execute` and `/test`;
- update the outcome table so dry runs suggest `/execute` in the current session;
- replace the restart paragraph with persistent session semantics;
- replace executable one-shot examples with the interactive transcript above;
- replace the standalone `--execute` safety block with:

```text
/execute
/status
/test
```

Keep archived files under `docs/archive/` unchanged because they record historical
behavior rather than current operating instructions.

- [ ] **Step 5: Verify current code and docs contain no legacy flag guidance**

Run:

```bash
rg -n --glob '!docs/archive/**' --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**' -- '--execute' AGENTS.md README.md AGENT_USAGE.md scripts tests
```

Expected: no matches.

Then run:

```bash
python -m pytest tests/test_agent_gate.py tests/test_data_package.py tests/test_command_processes.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit user-facing guidance**

```bash
git add AGENTS.md README.md AGENT_USAGE.md scripts/netzoo_agent_core/cli/follow_up.py scripts/netzoo_agent_core/evaluation/rendering.py scripts/netzoo_agent_core/command.py scripts/netzoo_agent_core/data/transforms.py tests/test_agent_gate.py tests/test_command_processes.py
git commit -m "docs: explain interactive NetZoo execution mode"
```

---

### Task 4: Full regression and manual CLI verification

**Files:**
- Verify only; modify the smallest owning file and its focused test if a failure exposes a regression.

**Interfaces:**
- Consumes: all implementation and documentation changes from Tasks 1 through 3.
- Produces: evidence that slash commands preserve the full NetZoo test suite and launcher behavior.

- [ ] **Step 1: Run static diff checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intended files or pre-existing unrelated user changes appear.

- [ ] **Step 2: Run the launcher and CLI regression groups**

Run:

```bash
python -m pytest tests/test_netzoo_chat_launcher.py tests/test_cli_package.py tests/test_cli_lifecycle.py tests/test_cli_slash_commands.py -q
```

Expected: all tests pass and the launcher still forwards unrelated CLI arguments.

- [ ] **Step 3: Run the full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass with no new failures.

- [ ] **Step 4: Exercise argument rejection without provider access**

Run:

```bash
python scripts/netzoo_agent.py --execute
```

Expected: exit code `2` and argparse reports `unrecognized arguments: --execute` before provider or runtime bootstrap.

- [ ] **Step 5: Exercise parser behavior without Docker or provider access**

Run:

```bash
PYTHONPATH=scripts python -c 'from netzoo_agent_core.cli.slash_commands import handle_slash_command; print(handle_slash_command("/status").message); print(handle_slash_command("/work/data.tsv").handled)'
```

Expected:

```text
Current mode: TEST
False
```

- [ ] **Step 6: Commit only if verification required a repair**

If a regression required a code change, stage only the repaired owning file and
its focused test, then commit with:

```bash
git commit -m "fix: preserve NetZoo CLI regression behavior"
```

If no repair was needed, do not create an empty commit.
