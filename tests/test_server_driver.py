"""The socket driver must reach the same states as the terminal driver.

These tests run the real ``ConversationMachine`` against the real
``WorkerDriver``, with only the graph invocation faked — the same seam
``test_cli_lifecycle`` uses.  What is being checked is that the second driver
asks the same questions in the same order, and that the one place it
deliberately differs (execution approval naming its plan) is strict.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import WorkflowPlan  # noqa: E402
from netzoo_agent_core.engine import ConversationMachine  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.server.channel import local_channel_pair  # noqa: E402
from netzoo_agent_core.server.driver import WorkerDriver  # noqa: E402
from netzoo_agent_core.server.protocol import Envelope, plan_hash  # noqa: E402

from test_cli_lifecycle import (  # noqa: E402
    _complete_bundle_choice_plan,
    _fake_cli_runtime,
    _guidance_result,
    _workflow_result,
)

TIMEOUT = 10.0
GOAL = "explain the difference between PANDA and PUMA"
RUN_TASK = "run the selected LIONESS-PUMA bundle"


class _Harness:
    """Run a driver on its own thread and talk to it from the test."""

    def __init__(self, runtime, *, pending_plan=None):
        if pending_plan is not None:
            runtime.pending_plan = pending_plan
        self.runtime = runtime
        self.client, worker_side = local_channel_pair()
        self.machine = ConversationMachine(
            SimpleNamespace(task=None, keep_session=False), runtime
        )
        self.driver = WorkerDriver(self.machine, worker_side, session_id="test-session")
        self.exit_code: int | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        self.exit_code = self.driver.run()

    def __enter__(self) -> "_Harness":
        self._thread.start()
        return self

    def __exit__(self, *exception) -> None:
        self._thread.join(timeout=TIMEOUT)
        assert not self._thread.is_alive(), "driver did not finish"

    def next(self, *types: str) -> Envelope:
        """Return the next envelope, skipping ones the test does not assert on."""
        while True:
            envelope = self.client.receive(timeout=TIMEOUT)
            assert envelope is not None, f"timed out waiting for {types or 'anything'}"
            if not types or envelope.type in types:
                return envelope

    def send(self, message_type: str, **payload) -> None:
        self.client.send(Envelope(type=message_type, payload=payload))

    def answer(self, text: str) -> None:
        self.send("answer", text=text)


@pytest.fixture(autouse=True)
def _planning_mode():
    previous = {
        name: getattr(settings, name)
        for name in ("EXECUTE_TOOLS", "TEST_DATA_MODE", "PRESENTATION_MODE")
    }
    configure_runtime(
        EXECUTE_TOOLS=False,
        TEST_DATA_MODE=False,
        PRESENTATION_MODE="state_machine",
    )
    yield
    configure_runtime(**previous)


def test_first_view_is_the_main_prompt_with_the_planning_banner():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))
    with _Harness(runtime) as harness:
        assert harness.next("ready").payload["session_id"] == "test-session"
        banner = harness.next("notice")
        assert "started in Planning mode" in banner.payload["text"]
        view = harness.next("view")
        assert view.payload["prompt_kind"] == "main"
        assert view.payload["mode"] == "Planning"
        assert "What would you like to accomplish with NetZoo?" in view.payload["text"]
        harness.answer("exit")
        assert harness.next("stopped").payload["exit_code"] == 0


def test_a_guidance_turn_publishes_the_answer_and_returns_to_a_prompt():
    runtime = _fake_cli_runtime(invoke_error=[_guidance_result(GOAL)])
    with _Harness(runtime) as harness:
        harness.next("view")
        harness.answer(GOAL)
        started = harness.next("turn_started")
        assert started.payload["task"] == GOAL
        assert started.payload["execute_once"] is False
        assert "PUMA" in harness.next("message").payload["text"]
        harness.next("turn_finished")
        assert harness.next("view").payload["prompt_kind"] == "main"
        harness.answer("exit")
        harness.next("stopped")


def test_clarification_view_carries_the_pending_plan():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))
    plan = _complete_bundle_choice_plan()
    with _Harness(runtime, pending_plan=plan) as harness:
        view = harness.next("view")
        assert view.payload["prompt_kind"] == "clarification"
        assert view.payload["plan"]["workflow"] == "LIONESS-PUMA"
        assert view.payload["plan"]["status"] == "needs_input"
        assert view.payload["plan_hash"] == plan_hash(plan)
        harness.answer("exit")
        harness.next("stopped")


def _dry_run_harness():
    runtime = _fake_cli_runtime(
        invoke_error=[
            _workflow_result(RUN_TASK, status="dry_run"),
            _workflow_result(RUN_TASK, status="success"),
        ]
    )
    return runtime, plan_hash(
        WorkflowPlan.model_validate(_workflow_result(RUN_TASK, status="dry_run")["plan"])
    )


def _reach_execution_prompt(harness) -> Envelope:
    # The shared fixture bundle only passes final input validation as a
    # synthetic one, the same way ``test_cli_lifecycle`` reaches this prompt.
    harness.next("view")
    harness.answer("/test")
    harness.next("notice")
    assert harness.next("view").payload["mode"] == "Test"
    harness.answer(RUN_TASK)
    harness.next("turn_started")
    harness.next("turn_finished")
    assert harness.next("view").payload["prompt_kind"] == "main"
    harness.answer("/execute")
    harness.next("notice")
    return harness.next("view")


def test_execution_needs_a_preview_then_an_approval_naming_that_plan():
    runtime, expected_hash = _dry_run_harness()
    with _Harness(runtime) as harness:
        view = _reach_execution_prompt(harness)
        assert view.payload["prompt_kind"] == "execution_confirmation"
        assert view.payload["plan_hash"] == expected_hash

        harness.send("approve_execution", plan_hash=expected_hash)
        started = harness.next("turn_started")
        assert started.payload["execute_once"] is True
        harness.next("turn_finished")
        harness.next("view")
        harness.answer("exit")
        harness.next("stopped")

    assert runtime.invoke_graph_turn_func.call_count == 2
    submitted = [
        call.args[1]["messages"][-1].content
        for call in runtime.invoke_graph_turn_func.call_args_list
    ]
    assert submitted == [RUN_TASK, RUN_TASK]
    assert settings.EXECUTE_TOOLS is False


def test_a_stale_plan_hash_is_refused_and_nothing_runs():
    runtime, expected_hash = _dry_run_harness()
    with _Harness(runtime) as harness:
        _reach_execution_prompt(harness)
        harness.send("approve_execution", plan_hash="0" * 64)
        error = harness.next("error")
        assert error.payload["error_type"] == "StalePlanHash"
        assert error.payload["expected_plan_hash"] == expected_hash
        harness.send("decline_execution")
        assert "cancelled" in harness.next("notice").payload["text"]
        harness.next("view")
        harness.answer("exit")
        harness.next("stopped")

    assert runtime.invoke_graph_turn_func.call_count == 1


def test_a_plain_answer_cannot_confirm_execution():
    runtime, _ = _dry_run_harness()
    with _Harness(runtime) as harness:
        _reach_execution_prompt(harness)
        harness.answer("yes")
        error = harness.next("error")
        assert error.payload["error_type"] == "ExecutionApprovalRequired"
        harness.send("decline_execution")
        harness.next("notice")
        harness.next("view")
        harness.answer("exit")
        harness.next("stopped")

    assert runtime.invoke_graph_turn_func.call_count == 1


def test_cancel_at_a_prompt_ends_the_session():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))
    with _Harness(runtime) as harness:
        harness.next("view")
        harness.send("cancel")
        assert harness.next("stopped").payload["exit_code"] == 0


def test_an_unparsable_message_is_reported_without_ending_the_session():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))
    with _Harness(runtime) as harness:
        harness.next("view")
        harness.client.send(Envelope(type="answer", payload={"nonsense": 1}))
        assert harness.next("error").payload["error_type"] == "InvalidMessage"
        harness.answer("exit")
        harness.next("stopped")


def test_a_failed_turn_is_reported_and_the_session_continues():
    runtime = _fake_cli_runtime(invoke_error=RuntimeError("provider unavailable"))
    with _Harness(runtime) as harness:
        harness.next("view")
        harness.answer("first request")
        harness.next("turn_started")
        assert "could not finish" in harness.next("notice").payload["text"]
        assert "RuntimeError" in harness.next("notice").payload["text"]
        harness.next("turn_finished")
        assert harness.next("view").payload["prompt_kind"] == "main"
        harness.answer("exit")
        harness.next("stopped")
