"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import ValidationError

from ..contracts import RequestedOutcome, TaskDecision
from ..routing.outcome_matching import named_workflow_action
from .registry_guidance import preferred_registry_composition_actions

__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Fail closed when semantic routing is unavailable; never infer from text."""
    error_detail = f" ({type(error).__name__})" if error is not None else ""
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="unknown",
        confidence=0.0,
        reason="The LLM router was unavailable, so no workflow was selected." + error_detail,
        clarification_question=(
            "Please restate the desired NetZoo result after the router is available."
        ),
    )


def recover_registry_guidance(
    task: str,
    workflows: Mapping[str, object],
    error: BaseException | None = None,
) -> TaskDecision | None:
    """Recover safe guidance from an explicitly named registered workflow."""
    if not isinstance(error, (ValidationError, ValueError)):
        return None
    action = named_workflow_action(task)
    spec = workflows.get(action) if action else None
    if spec is None:
        return None
    capability = spec.output_capability
    granularities = set(capability.granularities)
    granularity = (
        next(iter(granularities)) if len(granularities) == 1 else "unknown"
    )
    outcome = RequestedOutcome(
        operation=capability.operation,
        artifact_type=capability.artifact_type,
        entity_types=sorted(capability.entity_types),
        regulator_types=sorted(capability.regulator_types),
        target_types=sorted(capability.target_types),
        granularity=granularity,
        unresolved_dimensions=["granularity"] if granularity == "unknown" else [],
    )
    provisional = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.35,
        reason="registry guidance composition",
        requested_outcome=outcome,
        capability_match_status="exact",
        matched_actions=[action],
        recommended_actions=[action],
    )
    recommended_actions = preferred_registry_composition_actions(
        task,
        provisional,
        workflows,
    )
    candidate_actions = [action, "no_tool"]
    reason = (
        "Semantic interpretation failed validation; recovered a registered "
        f"guidance candidate from the explicitly named {spec.workflow} workflow."
    )
    if len(recommended_actions) > 1:
        predecessor_spec = workflows[recommended_actions[-2]]
        candidate_actions = [*recommended_actions, "no_tool"]
        reason = (
            "Semantic interpretation failed validation; recovered the registered "
            f"{predecessor_spec.workflow} → {spec.workflow} handoff from the "
            "explicit request and declared registry signals."
        )
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.35,
        reason=reason,
        candidate_actions=candidate_actions,
        recommended_actions=recommended_actions,
        requested_outcome=outcome,
        capability_match_status="exact",
        matched_actions=[action],
    )


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
