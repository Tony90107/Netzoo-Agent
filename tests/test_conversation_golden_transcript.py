"""Byte-exact transcripts of the interactive loop, captured before the M0 refactor.

The desktop UI work extracts the conversation state machine out of
``cli/conversation.py`` so a GUI adapter can drive the same transitions.  That
extraction is only allowed to move code, never to change what a terminal user
sees.  These snapshots are the enforcement: each scenario drives
``run_conversation`` through the one public seam it is allowed to keep (an
``args`` namespace plus a ``CliRuntime``) and records every byte that reaches
the user, both printed output and the prompt strings handed to ``input_func``.

Deliberately no monkeypatching of module internals.  A golden test that reached
inside ``cli.conversation`` would have to be rewritten by the very refactor it
is supposed to police, which would defeat the point.

Regenerate with ``NETZOO_UPDATE_GOLDEN=1 python -m pytest tests/test_conversation_golden_transcript.py``.
"""

from __future__ import annotations

import importlib
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import presentation  # noqa: E402
from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts.state import AgentTurnInterrupted  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402

from test_cli_lifecycle import (  # noqa: E402
    _complete_bundle_choice_plan,
    _condor_missing_output_plan,
    _fake_cli_runtime,
    _guidance_result,
    _preference_confirmation_plan,
    _workflow_result,
)

GOLDEN_DIR = Path(__file__).parent / "golden" / "conversation"
MAX_INTERACTIONS = 60

# The presentation layer keeps module-level render bookkeeping.  Reset it per
# scenario so a transcript never depends on which scenario ran before it.
_PRESENTATION_RESET = {
    "_PROGRESS_RENDERED_LINES": 0,
    "_PROGRESS_LAST_TEXT": None,
}


class _TranscriptRecorder:
    """Record printed output and prompts in the order the user would see them."""

    def __init__(self, answers):
        self._answers = list(answers)
        self._index = 0
        self._pending = []
        self.events: list[str] = []

    # -- stdout side ---------------------------------------------------
    def write(self, text: str) -> int:
        self._pending.append(text)
        return len(text)

    def flush(self) -> None:
        return None

    def _drain(self) -> None:
        text = "".join(self._pending)
        self._pending.clear()
        if text:
            self.events.append(_block("OUT", text))

    # -- input side ----------------------------------------------------
    def input_func(self, prompt: str = "") -> str:
        self._drain()
        self.events.append(_block("PROMPT", prompt))
        if self._index >= MAX_INTERACTIONS:
            raise AssertionError(
                "scenario exceeded the interaction cap; the loop is not converging"
            )
        if self._index < len(self._answers):
            answer = self._answers[self._index]
        else:
            # Exhaustion must show up as extra transcript lines rather than a
            # StopIteration traceback, so divergence stays readable in a diff.
            answer = "exit"
        self._index += 1
        self.events.append(_block("ANSWER", answer))
        return answer

    def finish(self, exit_code: int) -> str:
        self._drain()
        self.events.append(f"--- EXIT {exit_code} ---")
        return "\n".join(self.events) + "\n"


def _block(label: str, text: str) -> str:
    body = "\n".join(f"  | {line}" for line in text.split("\n"))
    return f"--- {label} ---\n{body}"


def _run_scenario(*, answers, invoke_error, pending_plan=None, task=None) -> str:
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    recorder = _TranscriptRecorder(answers)
    runtime = _fake_cli_runtime(invoke_error=invoke_error)
    runtime.input_func = recorder.input_func
    if pending_plan is not None:
        runtime.pending_plan = pending_plan

    with redirect_stdout(recorder):
        exit_code = conversation.run_conversation(
            SimpleNamespace(task=task, keep_session=False),
            runtime,
        )
    return recorder.finish(exit_code)


# ---------------------------------------------------------------------------
# Scenarios.  Each one exercises a distinct branch of the loop that the
# extraction has to preserve.
# ---------------------------------------------------------------------------

GOAL = "explain the difference between PANDA and PUMA"
RUN_TASK = "run the selected LIONESS-PUMA bundle"


def _scenario_blocked_execute():
    return dict(
        answers=["/execute", "/status", "exit"],
        invoke_error=AssertionError("graph must not run"),
    )


def _scenario_mode_slash_commands():
    return dict(
        answers=["/help", "/test", "/status", "/planning", "/status", "exit"],
        invoke_error=AssertionError("graph must not run"),
    )


def _scenario_guidance_then_exit():
    return dict(
        answers=[GOAL, "exit"],
        invoke_error=[_guidance_result(GOAL)],
    )


def _scenario_preview_then_execute():
    return dict(
        answers=["/test", RUN_TASK, "/execute", "yes", "exit"],
        invoke_error=[
            _workflow_result(RUN_TASK, status="dry_run"),
            _workflow_result(RUN_TASK, status="success"),
        ],
    )


def _scenario_preview_then_decline_execution():
    return dict(
        answers=[RUN_TASK, "/execute", "n", "exit"],
        invoke_error=[_workflow_result(RUN_TASK, status="dry_run")],
    )


def _scenario_missing_input_blocks_execute():
    return dict(
        answers=["/execute", "/status", "exit"],
        invoke_error=AssertionError("graph must not run"),
        pending_plan=_condor_missing_output_plan(),
    )


def _scenario_path_clarification():
    return dict(
        answers=["/output", "exit"],
        invoke_error=RuntimeError("captured continuation"),
        pending_plan=_condor_missing_output_plan(),
    )


def _scenario_bundle_selection():
    return dict(
        answers=["1", "exit"],
        invoke_error=RuntimeError("captured continuation"),
        pending_plan=_complete_bundle_choice_plan(),
    )


def _scenario_custom_bundle_wizard():
    return dict(
        answers=["custom", "1", "2", "1", "2", "exit"],
        invoke_error=RuntimeError("captured continuation"),
        pending_plan=_complete_bundle_choice_plan(),
    )


def _scenario_preference_confirmation_declined():
    return dict(
        answers=["n", "exit"],
        invoke_error=RuntimeError("captured continuation"),
        pending_plan=_preference_confirmation_plan(),
    )


def _scenario_interactive_failure_continues():
    return dict(
        answers=["first request", "exit"],
        invoke_error=RuntimeError("provider unavailable"),
    )


def _scenario_one_shot_failure():
    return dict(
        answers=[],
        invoke_error=RuntimeError("provider unavailable"),
        task="run PANDA",
    )


def _scenario_one_shot_interrupt():
    return dict(
        answers=[],
        invoke_error=AgentTurnInterrupted(),
        task="run PANDA",
    )


SCENARIOS = {
    "blocked_execute": _scenario_blocked_execute,
    "mode_slash_commands": _scenario_mode_slash_commands,
    "guidance_then_exit": _scenario_guidance_then_exit,
    "preview_then_execute": _scenario_preview_then_execute,
    "preview_then_decline_execution": _scenario_preview_then_decline_execution,
    "missing_input_blocks_execute": _scenario_missing_input_blocks_execute,
    "path_clarification": _scenario_path_clarification,
    "bundle_selection": _scenario_bundle_selection,
    "custom_bundle_wizard": _scenario_custom_bundle_wizard,
    "preference_confirmation_declined": _scenario_preference_confirmation_declined,
    "interactive_failure_continues": _scenario_interactive_failure_continues,
    "one_shot_failure": _scenario_one_shot_failure,
    "one_shot_interrupt": _scenario_one_shot_interrupt,
}


@pytest.fixture(autouse=True)
def _deterministic_cli_runtime():
    """Pin the runtime to what ``run_cli`` selects when no display flag is given."""
    previous = {
        name: getattr(settings, name)
        for name in (
            "EXECUTE_TOOLS",
            "TEST_DATA_MODE",
            "TRACE_ENABLED",
            "VERBOSE_OUTPUT",
            "PRESENTATION_MODE",
            "TRANSIENT_TRACE",
        )
    }
    previous_presentation = {
        name: getattr(presentation, name) for name in _PRESENTATION_RESET
    }
    configure_runtime(
        EXECUTE_TOOLS=False,
        TEST_DATA_MODE=False,
        TRACE_ENABLED=True,
        VERBOSE_OUTPUT=False,
        PRESENTATION_MODE="state_machine",
        TRANSIENT_TRACE=False,
    )
    for name, value in _PRESENTATION_RESET.items():
        setattr(presentation, name, value)
    try:
        yield
    finally:
        configure_runtime(**previous)
        for name, value in previous_presentation.items():
            setattr(presentation, name, value)


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_interactive_transcript_is_unchanged(name):
    transcript = _run_scenario(**SCENARIOS[name]())
    snapshot = GOLDEN_DIR / f"{name}.txt"

    if os.environ.get("NETZOO_UPDATE_GOLDEN") == "1":
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(transcript, encoding="utf-8")
        return

    assert snapshot.exists(), (
        f"missing golden transcript {snapshot}; regenerate with "
        "NETZOO_UPDATE_GOLDEN=1"
    )
    assert transcript == snapshot.read_text(encoding="utf-8")


def test_every_scenario_has_a_committed_snapshot():
    """A scenario without a snapshot would silently police nothing."""
    recorded = {path.stem for path in GOLDEN_DIR.glob("*.txt")}
    assert recorded == set(SCENARIOS)
