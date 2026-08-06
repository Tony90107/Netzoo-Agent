"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

import re

from workflow_registry import REQUIRED_INPUTS

from ..contracts import TaskDecision, _is_demo_request
from ..routing import (
    has_direct_execution_intent,
    infer_advisory_capabilities,
    infer_goal_capabilities,
    inferred_execution_action,
    is_workflow_information_request,
    validate_task_text,
)
from .extraction import (
    _task_path,
    documentation_library_for_task,
    is_versioned_documentation_request,
)

__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Classify obvious local run intents when the provider/router fails."""
    normalized = task.casefold()
    recommendations = infer_goal_capabilities(task)
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
    if is_workflow_information_request(task):
        recommendations = infer_advisory_capabilities(task)
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=1.0,
            reason=(
                "The request asks for workflow requirements or usage information, "
                "not local execution."
            ),
            recommended_actions=recommendations,
        )

    run_intent = has_direct_execution_intent(task) or re.search(
        r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not run_intent:
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason="The provider failed and no deterministic local workflow intent was found.",
            recommended_actions=recommendations,
        )

    action = (
        inferred_execution_action(task) if has_direct_execution_intent(task) else None
    )
    if "lioness" in normalized:
        if "panda" in normalized:
            action = "run_lioness_panda"
        elif "puma" in normalized:
            action = "run_lioness_puma"
        elif re.search(
            r"(co[- _]?expression|coexpression|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        ):
            action = "run_lioness_coexpression"
        else:
            return TaskDecision(
                action="no_tool",
                in_scope=True,
                should_execute=False,
                intent_type="demo_run" if _is_demo_request(task) else "run_analysis",
                confidence=1.0,
                reason="A LIONESS run was requested, but its base method is ambiguous.",
                missing_inputs=["lioness_mode"],
            )
    elif action is None and "panda" in normalized:
        action = "run_panda"
    elif action is None and "puma" in normalized:
        action = "run_puma"
    elif action is None and "condor" in normalized:
        action = "run_condor"

    if action is None:
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason=(
                "The provider failed and the task did not identify an allow-listed "
                "workflow by either name or objective."
            ),
            recommended_actions=recommendations,
        )

    values = {
        "action": action,
        "in_scope": True,
        "should_execute": True,
        "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
        "confidence": 1.0,
        "reason": reason,
        "recommended_actions": recommendations,
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
