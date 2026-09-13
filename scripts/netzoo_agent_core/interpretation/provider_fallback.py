"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

from collections.abc import Mapping
import re

from pydantic import ValidationError

from ..contracts import TaskDecision
from ..routing.capability import MIN_TOOL_CONFIDENCE, has_direct_execution_intent
from ..routing.named_labels import solely_named_run_action
from ..routing.outcome_matching import guidance_actions_for
from .request_parameters import has_explicit_request_parameters
__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Fail closed when semantic routing is unavailable; never infer from text."""
    error_detail = f" ({type(error).__name__})" if error is not None else ""
    if isinstance(error, (ValidationError, ValueError)):
        reason = (
            "Semantic routing output failed validation, so no workflow was selected."
            + error_detail
        )
    else:
        reason = (
            "The LLM router was unavailable, so no workflow was selected."
            + error_detail
        )
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="unknown",
        confidence=0.0,
        reason=reason,
        match_basis="semantic_validation_recovery" if isinstance(error, (ValidationError, ValueError)) else "provider_unavailable",
    )


def recover_registry_guidance(
    task: str,
    workflows: Mapping[str, object],
    error: BaseException | None = None,
) -> TaskDecision | None:
    """Compatibility entry point: failed semantics never selects a tool from text."""
    return None


def recover_ambiguous_input(
    task: str,
    error: BaseException | None = None,
) -> TaskDecision | None:
    """Turn a validated-input-only request into a safe result clarification.

    This is deliberately narrower than workflow recovery: explicit paths and
    controls are echoed, but no scientific outcome or workflow is inferred.
    Requests without those concrete witnesses continue to use the generic
    provider/validation failure boundary.
    """
    if not isinstance(error, (ValidationError, ValueError)):
        return None
    if not has_explicit_request_parameters(task):
        return None
    if not re.search(
        r"(?:analy[sz]e|infer|run|execute|produce|generate|分析|估計|推估|產生|執行|跑)",
        task,
        flags=re.IGNORECASE,
    ):
        return None
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.0,
        reason=(
            "The request provides input parameters but does not specify the "
            "requested NetZoo result, so no workflow was selected."
        ),
        clarification_question=(
            "Which registered NetZoo result should I produce from these inputs? "
            "Please specify the result type and whether it should be aggregate or sample-specific."
        ),
        match_basis="semantic_validation_recovery",
    )


def recover_explicit_run(
    task: str,
    workflows: Mapping[str, object],
    error: BaseException | None = None,
) -> TaskDecision | None:
    """Keep an unambiguous run command when only semantic validation failed.

    This does not infer a scientific goal or guess a workflow.  It accepts only
    one currently scoped registry label plus a direct execution instruction;
    transport failures, informational questions, historical mentions and
    multi-workflow requests still fail closed.  Planning and input validation
    remain downstream gates, so this recovery cannot execute a file unchecked.
    """
    if not isinstance(error, (ValidationError, ValueError)):
        return None
    if not has_direct_execution_intent(task):
        return None
    action = solely_named_run_action(task)
    if action is None or action not in workflows:
        return None
    return TaskDecision(
        action=action,
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=MIN_TOOL_CONFIDENCE,
        reason=(
            "Semantic output failed validation, but the request directly and "
            "unambiguously names this registered workflow."
        ),
        match_basis="workflow_name",
        capability_match_status="exact",
        matched_actions=[action],
        recommended_actions=guidance_actions_for(action),
    )


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
