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
from netzoo_agent_core.contracts import (  # noqa: E402
    PlanEvaluationResult,
    TaskDecision,
    WorkflowPlan,
    WorkflowStep,
)


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


def test_single_component_absolute_paths_are_answers_in_path_context():
    for user_input in ("/tmp", "/output"):
        result = handle_slash_command(user_input, allow_path_answer=True)
        assert result.handled is False
        assert result.message == ""


def test_known_commands_remain_commands_in_path_context():
    result = handle_slash_command("/status", allow_path_answer=True)

    assert result.handled is True
    assert result.message == "Current mode: Planning"


def test_execute_is_one_shot_and_leaves_planning_mode_enabled():
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"

    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
        expression_file="data/lioness-toy/expression.tsv",
        motif_file="data/lioness-toy/motif-panda.tsv",
        ppi_file="data/lioness-toy/ppi.tsv",
        output_file="outputs/panda.tsv",
    )
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="Run PANDA.",
        decision=decision.model_dump(),
        steps=[WorkflowStep(action="run_panda", purpose="Execute PANDA.")],
        status="ready",
    )
    evaluation = PlanEvaluationResult(status="approved", score=100, summary="Pass")
    execute = handle_slash_command(
        "/execute",
        execution_ready=True,
        current_plan=plan,
        current_plan_evaluation=evaluation,
    )
    assert execute.handled is True
    assert execute.execute_once is True
    assert "once" in execute.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"

    planning = handle_slash_command("/PLANNING")
    assert planning.handled is True
    assert "Planning mode enabled" in planning.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"


def test_execute_checks_the_current_plan_and_evaluation():
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
        expression_file="data/lioness-toy/expression.tsv",
        motif_file="data/lioness-toy/motif-panda.tsv",
        ppi_file="data/lioness-toy/ppi.tsv",
        output_file="outputs/panda.tsv",
    )
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="Run PANDA.",
        decision=decision.model_dump(),
        steps=[WorkflowStep(action="run_panda", purpose="Execute PANDA.")],
        status="ready",
    )
    evaluation = PlanEvaluationResult(status="approved", score=100, summary="Pass")

    result = handle_slash_command(
        "/execute",
        current_plan=plan,
        current_plan_evaluation=evaluation,
    )

    assert result.execute_once is True
    assert settings.EXECUTE_TOOLS is False

    not_ready = plan.model_copy(update={"status": "needs_confirmation"})
    blocked = handle_slash_command(
        "/execute",
        current_plan=not_ready,
        current_plan_evaluation=evaluation,
    )
    assert blocked.execute_once is False
    assert "not ready" in blocked.message


def test_execute_is_blocked_until_a_ready_plan_is_available():
    result = handle_slash_command("/execute")

    assert result.handled is True
    assert "no current Work Plan" in result.message
    assert settings.EXECUTE_TOOLS is False


def test_status_and_help_report_without_changing_mode():
    status = handle_slash_command("/status")
    assert status == type(status)(handled=True, message="Current mode: Planning")

    help_result = handle_slash_command("/help")
    assert help_result.handled is True
    assert "Press / at an empty prompt, then Enter, to use /execute." in help_result.message
    assert "Type after / to enter another slash command." in help_result.message
    for command in ("/planning", "/execute", "/status", "/help"):
        assert command in help_result.message
    assert "future workflow tasks" in help_result.message
    assert "interrupt" not in help_result.message.casefold()
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
