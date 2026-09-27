"""CLI-owned slash commands for interactive execution authority."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .. import settings
from ..contracts import PlanEvaluationResult, TaskDecision, WorkflowPlan
from ..data.preflight import validate_workflow_inputs
from ..runtime import configure_runtime
from ..environment import render_environment_report

__all__ = [
    "SlashCommandResult",
    "current_mode_label",
    "handle_slash_command",
    "render_mode_prompt",
]

_COMMAND_TOKEN = re.compile(r"^/[A-Za-z][A-Za-z0-9_-]*(?:\s+.*)?$")
_KNOWN_COMMANDS = frozenset({"/test", "/planning", "/execute", "/status", "/help", "/doctor"})


@dataclass(frozen=True, slots=True)
class SlashCommandResult:
    handled: bool
    message: str = ""
    execute_once: bool = False


def current_mode_label() -> str:
    if settings.TEST_DATA_MODE:
        return "Test"
    return "Execute" if settings.EXECUTE_TOOLS else "Planning"


def render_mode_prompt(prompt: str) -> str:
    if settings.TEST_DATA_MODE:
        return f"[Test] {prompt}"
    return f"[Execute] {prompt}" if settings.EXECUTE_TOOLS else prompt


def handle_slash_command(
    user_input: str,
    *,
    allow_path_answer: bool = False,
    execution_ready: bool | None = None,
    execution_block_reason: str = "",
    current_plan: WorkflowPlan | dict | None = None,
    current_plan_evaluation: PlanEvaluationResult | dict | None = None,
) -> SlashCommandResult:
    stripped = user_input.strip()
    if not _COMMAND_TOKEN.fullmatch(stripped):
        return SlashCommandResult(handled=False)

    command, *arguments = stripped.split(maxsplit=1)
    normalized = command.casefold()
    if normalized not in _KNOWN_COMMANDS:
        if allow_path_answer and not arguments:
            return SlashCommandResult(handled=False)
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
        if current_plan is None:
            ready = False
            reason = (
                "Execution is blocked because there is no current Work Plan. "
                "no approved, ready workflow plan is available. "
                "Create a Planning-mode preview first."
            )
        else:
            ready, reason = _check_current_workflow_plan(
                current_plan,
                current_plan_evaluation,
            )
        if not ready:
            return SlashCommandResult(
                handled=True,
                message=(
                    reason
                    or "Execution is unavailable because there is no approved, "
                    "ready workflow plan. Continue providing the required inputs."
                ),
            )
        return SlashCommandResult(
            handled=True,
            message=(
                "The current Work Plan is approved and ready. "
                "Confirm below to execute it once."
            ),
            execute_once=True,
        )
    if normalized == "/planning":
        configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False)
        return SlashCommandResult(
            handled=True,
            message="Planning mode enabled. Future workflow tasks will only create previews.",
        )
    if normalized == "/test":
        configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=True)
        return SlashCommandResult(
            handled=True,
            message=(
                "Synthetic Test mode enabled. Future workflow tasks will still require "
                "the explicit /execute confirmation, while unresolved gene labels are "
                "accepted as test-only identifiers. Schema, numeric, and cross-file "
                "compatibility checks remain enforced.\n"
                "Results from this mode are for software testing only and are not "
                "biological evidence."
            ),
        )
    if normalized == "/status":
        return SlashCommandResult(
            handled=True,
            message=f"Current mode: {current_mode_label()}",
        )
    if normalized == "/doctor":
        return SlashCommandResult(handled=True, message=render_environment_report())
    return SlashCommandResult(
        handled=True,
        message=(
            "Press / at an empty prompt, then Enter, to use /execute.\n"
            "Type after / to enter another slash command.\n"
            "Slash commands:\n"
            "  /test     Allow synthetic labels for test-only previews and execution.\n"
            "  /planning Return to strict, preview-only Planning mode.\n"
            "  /execute  Execute the current approved Work Plan once.\n"
            "  /status   Show the current execution mode.\n"
            "  /doctor   Check the running Docker and netZooPy environment.\n"
            "  /help     Show this help."
        ),
    )


def _check_current_workflow_plan(
    plan: WorkflowPlan | dict,
    evaluation: PlanEvaluationResult | dict | None,
) -> tuple[bool, str]:
    """Check the cached plan before /execute grants one-shot authority."""
    try:
        validated_plan = WorkflowPlan.model_validate(plan)
    except Exception:
        return False, "Execution is blocked because the current Work Plan is invalid."
    if validated_plan.status != "ready":
        if validated_plan.missing_inputs:
            return (
                False,
                "Execution is blocked because the current Work Plan is not ready. "
                "It still needs: "
                + ", ".join(validated_plan.missing_inputs)
                + ".",
            )
        return (
            False,
            "Execution is blocked because the current Work Plan is not ready. "
            f"Current status: {validated_plan.status}.",
        )
    if not validated_plan.steps:
        return False, "Execution is blocked because the Work Plan has no steps."
    if validated_plan.missing_inputs:
        return (
            False,
            "Execution is blocked because the Work Plan still needs: "
            + ", ".join(validated_plan.missing_inputs)
            + ".",
        )
    try:
        decision = TaskDecision.model_validate(validated_plan.decision)
    except Exception:
        return False, "Execution is blocked because the Work Plan decision is invalid."
    if not decision.should_execute or decision.missing_inputs:
        return (
            False,
            "Execution is blocked because the Work Plan is not authorized for "
            "execution or still contains missing inputs.",
        )
    if evaluation is None:
        return False, "Execution is blocked because the Work Plan has not passed evaluation."
    try:
        validated_evaluation = PlanEvaluationResult.model_validate(evaluation)
    except Exception:
        return False, "Execution is blocked because the Work Plan evaluation is invalid."
    if validated_evaluation.status != "approved":
        return (
            False,
            "Execution is blocked because the Work Plan evaluation is not approved. "
            f"Current evaluation: {validated_evaluation.status}.",
        )
    preflight_errors = validate_workflow_inputs(decision.action, decision)
    if preflight_errors:
        return (
            False,
            "Execution is blocked because final input validation failed:\n"
            + "\n".join(f"- {error}" for error in preflight_errors),
        )
    return True, ""
