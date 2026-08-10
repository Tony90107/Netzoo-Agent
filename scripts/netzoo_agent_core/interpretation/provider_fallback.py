"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

import re

from workflow_registry import REQUIRED_INPUTS

from ..contracts import TaskDecision, _is_demo_request
from ..routing import (
    has_direct_execution_intent,
    is_workflow_information_request,
    validate_task_text,
)
from ..routing.outcome_matching import guidance_actions_for, named_workflow_action
from .extraction import (
    _task_path,
    documentation_library_for_task,
    is_versioned_documentation_request,
)

__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Handle explicit workflow names but never guess an unnamed scientific goal."""
    normalized = task.casefold()
    reason = (
        "The LLM router failed, so the agent used a deterministic fallback for an "
        "explicit local workflow request."
    )
    if error is not None:
        reason += f" Provider error: {type(error).__name__}."

    documentation_library = documentation_library_for_task(task)
    if is_versioned_documentation_request(task) and documentation_library:
        return TaskDecision(
            action="query_context7",
            in_scope=True,
            should_execute=True,
            intent_type="answer_question",
            confidence=1.0,
            reason="Deterministic routing selected current package documentation.",
            library_name=documentation_library,
            docs_query=task[:2_000],
        )

    rejection = validate_task_text(task, "no_tool")
    if rejection:
        return TaskDecision(
            action="no_tool",
            in_scope=False,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason=rejection,
        )

    action = named_workflow_action(task)
    information_request = is_workflow_information_request(task)
    run_intent = bool(
        has_direct_execution_intent(task)
        or re.search(
            r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
            normalized,
            flags=re.IGNORECASE,
        )
    )

    if action and (information_request or not run_intent):
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question" if information_request else "unknown",
            confidence=1.0,
            reason=(
                "The request names a registered workflow, but does not authorize "
                "local execution."
            ),
            capability_match_status="exact",
            matched_actions=[action],
            recommended_actions=guidance_actions_for(action),
        )

    if not action:
        if "lioness" in normalized and run_intent:
            return TaskDecision(
                action="no_tool",
                in_scope=True,
                should_execute=False,
                intent_type="demo_run" if _is_demo_request(task) else "run_analysis",
                confidence=1.0,
                reason="A LIONESS run was requested, but its base method is ambiguous.",
                missing_inputs=["lioness_mode"],
                clarification_question=(
                    "Which LIONESS base method should be used: PANDA, PUMA, or "
                    "co-expression?"
                ),
            )
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question" if information_request else "unknown",
            confidence=1.0,
            reason=(
                "The provider failed and the requested outcome could not be "
                "normalized safely."
            ),
            clarification_question=(
                "What result do you want NetZoo to produce: a regulatory network, "
                "a co-expression network, or community assignments?"
            ),
        )

    values = {
        "action": action,
        "in_scope": True,
        "should_execute": True,
        "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
        "confidence": 1.0,
        "reason": reason,
        "capability_match_status": "exact",
        "matched_actions": [action],
        "recommended_actions": guidance_actions_for(action),
        "missing_inputs": [
            field_name
            for field_name in REQUIRED_INPUTS[action]
            if field_name not in {"output_file", "lioness_output", "output_dir"}
        ],
    }
    for field_name in REQUIRED_INPUTS[action]:
        parsed = _task_path(task, field_name)
        if parsed:
            values[field_name] = parsed
    return TaskDecision(**values)


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
