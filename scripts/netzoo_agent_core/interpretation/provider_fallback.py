"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import ValidationError

from ..contracts import TaskDecision
from ..routing.method_rejections import rejected_methods_for
from ..routing.outcome_matching import (
    explicit_input_artifacts,
    match_registry_guidance_features,
    named_workflow_action,
)
from .registry_guidance import preferred_registry_composition_actions

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
    """Recover safe registry guidance after semantic output fails validation."""
    if not isinstance(error, (ValidationError, ValueError)):
        return None

    capabilities = {
        action: spec.output_capability for action, spec in workflows.items()
    }
    feature_match = match_registry_guidance_features(task, capabilities)
    action = (
        feature_match.matched_actions[0]
        if feature_match is not None
        else named_workflow_action(task)
    )
    spec = workflows.get(action) if action else None
    if spec is None:
        return None
    capability = spec.output_capability
    if feature_match is None and (
        explicit_input_artifacts(task)
        & frozenset(capability.incompatible_input_artifacts)
    ):
        return None
    # Lexical input observations help scope candidate compatibility, but cannot
    # manufacture the desired output, entities or granularity from the registry.
    inputs = sorted(explicit_input_artifacts(task) & set(capability.input_artifacts))
    provisional = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.35,
        reason="registry guidance composition",
        guidance_input_artifacts=inputs,
        capability_match_status="fallback",
        match_basis="semantic_validation_recovery",
        matched_actions=[action],
        recommended_actions=[action],
    )
    recommended_actions = preferred_registry_composition_actions(
        task,
        provisional,
        workflows,
    )
    candidate_actions = [action, "no_tool"]
    if feature_match is not None:
        reason = (
            "Semantic interpretation failed validation; recovered a registered "
            f"guidance candidate for {spec.workflow} from multiple declared "
            "scientific signals."
        )
    else:
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
        guidance_input_artifacts=inputs,
        capability_match_status="fallback",
        match_basis="semantic_validation_recovery",
        rejected_methods=rejected_methods_for(task, inputs),
        matched_actions=[action],
    )


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
