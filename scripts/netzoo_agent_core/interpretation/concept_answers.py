"""Deterministic answers for basic registered-workflow concept questions."""

from __future__ import annotations

import re

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text
from ..routing.outcome_matching import (
    guidance_actions_for,
    has_granularity_only_ambiguity,
)

_PURPOSE_PATTERN = re.compile(
    r"\b(?:function|purpose|what\s+is|what\s+does)\b|(?:功能|用途|是什麼)",
    flags=re.IGNORECASE,
)

_OPERATION_VERBS = {
    "acquire": "acquire",
    "prepare": "prepare",
    "validate": "validate",
    "infer": "infer",
    "analyze": "analyze",
    "explain": "explain",
    "unknown": "produce",
}
_ARTIFACT_LABELS = {
    "measurement_dataset": "measurement data",
    "expression_matrix": "expression matrices",
    "regulatory_network": "regulatory networks",
    "coexpression_network": "co-expression networks",
    "community_assignment": "community assignments",
    "validation_report": "validation reports",
    "unknown": "the requested result",
}
_GRANULARITY_LABELS = {
    "aggregate": "aggregate",
    "sample_specific": "sample-specific",
    "not_applicable": "",
    "unknown": "",
}
_ENTITY_LABELS = {"tf": "TF", "mirna": "miRNA", "gene": "gene"}


def _outcome_phrase(outcome, *, include_granularity: bool = True) -> str:
    if outcome is None:
        return "the requested result"
    pieces = []
    granularity = (
        _GRANULARITY_LABELS[outcome.granularity] if include_granularity else ""
    )
    if granularity:
        pieces.append(granularity)
    entities = outcome.display_entities or [
        _ENTITY_LABELS.get(item, item)
        for item in outcome.entity_types
        if item != "unknown"
    ]
    if entities:
        pieces.append("/".join(entities))
    pieces.append(_ARTIFACT_LABELS[outcome.artifact_type])
    return " ".join(pieces)


def _requested_outcome_phrase(decision: TaskDecision) -> str:
    return _outcome_phrase(decision.requested_outcome)


def _capability_phrase(spec, decision: TaskDecision) -> str:
    capability = spec.output_capability
    requested_granularity = (
        decision.requested_outcome.granularity if decision.requested_outcome else None
    )
    granularity = (
        requested_granularity
        if requested_granularity in capability.granularities
        else capability.granularities[-1]
    )
    prefix = _GRANULARITY_LABELS[granularity]
    if capability.artifact_type == "regulatory_network":
        regulators = "/".join(
            _ENTITY_LABELS[item] for item in capability.regulator_types
        )
        targets = "/".join(_ENTITY_LABELS[item] for item in capability.target_types)
        relationship = f"{regulators}-to-{targets} " if regulators and targets else ""
        return f"{prefix} {relationship}regulatory networks".strip()
    return f"{prefix} {_ARTIFACT_LABELS[capability.artifact_type]}".strip()


def _workflow_sequence(
    action: str,
    policy: ProjectPolicySnapshot,
) -> str:
    names = []
    for item in guidance_actions_for(action):
        spec = policy.workflows.get(item)
        if spec is not None:
            names.append(spec.workflow)
    return " → ".join(names)


def _network_family_label(spec) -> str:
    capability = spec.output_capability
    if capability.artifact_type == "coexpression_network":
        return "Gene co-expression network"
    if capability.artifact_type == "regulatory_network":
        regulators = set(capability.regulator_types)
        if regulators == {"tf"}:
            return "TF-only regulatory network"
        labels = "/".join(_ENTITY_LABELS[item] for item in capability.regulator_types)
        return f"{labels} regulatory network"
    return _ARTIFACT_LABELS[capability.artifact_type].capitalize()


def render_outcome_clarification(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Explain compatible hypotheses before asking one validated clarification."""
    if (
        decision.capability_match_status != "ambiguous"
        or not decision.clarification_question
    ):
        return None
    if len(decision.hypothesis_actions) == 1:
        action = decision.hypothesis_actions[0]
        spec = policy.workflows.get(action)
        if spec is not None:
            granularity_ambiguous = has_granularity_only_ambiguity(
                decision.outcome_hypotheses
            )
            interpretation = (
                _outcome_phrase(
                    decision.outcome_hypotheses[0].outcome,
                    include_granularity=False,
                )
                if granularity_ambiguous
                else (
                    _requested_outcome_phrase(decision)
                    if decision.requested_outcome is not None
                    else _capability_phrase(spec, decision)
                )
            )
            return _ui_text(
                f"It sounds like you want {interpretation}.\n\n"
                "The compatible workflow composition is "
                f"{_workflow_sequence(action, policy)}.\n\n"
                f"{decision.clarification_question}\n\n"
                "No files were inspected and no analysis ran."
            )
    if len(decision.hypothesis_actions) > 1:
        options = []
        for action in decision.hypothesis_actions:
            spec = policy.workflows.get(action)
            if spec is None:
                continue
            options.append(
                (_network_family_label(spec), _workflow_sequence(action, policy))
            )
        if options:
            lines = "\n".join(
                f"- {label}: {sequence}"
                for label, sequence in sorted(options, key=lambda item: item[0])
            )
            return _ui_text(
                "I can map this to more than one compatible network result:\n"
                f"{lines}\n\n"
                f"{decision.clarification_question}\n\n"
                "No files were inspected and no analysis ran."
            )
    return _ui_text(
        "I cannot select a workflow until the requested result is clear. "
        f"{decision.clarification_question}\n\n"
        "No files were inspected and no analysis ran."
    )


def render_capability_gap(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Explain an unsupported deliverable without promoting a related workflow."""
    if decision.capability_match_status != "unsupported":
        return None
    operation = (
        _OPERATION_VERBS[decision.requested_outcome.operation]
        if decision.requested_outcome
        else "produce"
    )
    lines = [
        f"The registered NetZoo workflows do not {operation} "
        f"{_requested_outcome_phrase(decision)}."
    ]
    alternative = (
        decision.alternative_actions[0] if decision.alternative_actions else None
    )
    spec = policy.workflows.get(alternative) if alternative else None
    if spec is not None:
        lines.append(
            f"{spec.workflow} can instead {spec.output_capability.operation} "
            f"{_capability_phrase(spec, decision)}. Did you mean that supported result?"
        )
    else:
        supported = sorted(
            {
                _ARTIFACT_LABELS[item.output_capability.artifact_type]
                for item in policy.workflows.values()
            }
        )
        lines.append("Registered outputs are: " + ", ".join(supported) + ".")
    lines.append("No files were inspected and no analysis ran.")
    return _ui_text("\n\n".join(lines))


def render_spec_backed_concept_answer(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Return registered workflow facts for a basic no-tool purpose question."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and _PURPOSE_PATTERN.search(task)
    ):
        return None
    normalized = task.casefold()
    for spec in policy.workflows.values():
        if spec.workflow.casefold() not in normalized:
            continue
        inputs = ", ".join(spec.required_inputs) or "no registered required inputs"
        return _ui_text(
            f"{spec.workflow} {spec.description}\n\n"
            f"Registered required inputs: {inputs}.\n"
            "No files were inspected and no analysis ran."
        )
    return None


def render_ambiguous_workflow_guidance(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    semantic_goal: dict | None = None,
) -> str | None:
    """Explain multiple registered candidates without inventing a selection."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and len(decision.recommended_actions) > 1
        and (semantic_goal or {}).get("relationship") == "alternatives"
    ):
        return None
    specs = [policy.workflows.get(action) for action in decision.recommended_actions]
    registered = [spec for spec in specs if spec is not None]
    if len(registered) < 2:
        return None
    options = "\n".join(f"- {spec.workflow}: {spec.description}" for spec in registered)
    return _ui_text(
        "I can match your goal to more than one registered workflow:\n"
        f"{options}\n\n"
        "To recommend one workflow, please clarify which regulatory relationship "
        "you want to model. No files were inspected and no analysis ran."
    )


def render_workflow_composition_guidance(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    semantic_goal: dict | None = None,
) -> str | None:
    """Explain an ordered, registry-defined workflow composition."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and (semantic_goal or {}).get("relationship") == "composition"
        and decision.recommended_actions
    ):
        return None
    specs = [policy.workflows.get(action) for action in decision.recommended_actions]
    registered = [spec for spec in specs if spec is not None]
    if not registered:
        return None
    steps = "\n".join(f"- {spec.workflow}: {spec.description}" for spec in registered)
    return _ui_text(
        "I matched your goal to this registered workflow composition:\n"
        f"{steps}\n\n"
        f"The final workflow in this composition is {registered[-1].workflow}. "
        "No files were inspected and no analysis ran."
    )


__all__ = [
    "render_ambiguous_workflow_guidance",
    "render_capability_gap",
    "render_outcome_clarification",
    "render_spec_backed_concept_answer",
    "render_workflow_composition_guidance",
]
