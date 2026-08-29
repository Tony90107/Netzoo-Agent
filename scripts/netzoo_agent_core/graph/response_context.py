"""Registry-derived capability context for response generation."""

from __future__ import annotations

import re

from ..contracts import OUTPUT_ROLE_FIELDS, ProjectPolicySnapshot, TaskDecision
from ..interpretation import INPUT_LABELS
from ..interpretation.registry_guidance import build_registry_selection_constraints, decision_with_registry_signals, related_registry_actions

__all__: list[str] = []


_SAMPLE_REFERENCE_PATTERNS = (
    re.compile(
        r"\b(?:patient|sample|subject|case)(?:[\s_-]*(?:id|no|number))?"
        r"[\s:#_-]*(?P<identifier>\d+|[A-Za-z0-9._-]*\d[A-Za-z0-9._-]*)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?:第\s*[A-Za-z0-9._-]*\d[A-Za-z0-9._-]*\s*號\s*"
        r"(?:病患|病人|個案|樣本|受試者)|(?:病患|病人|個案|樣本|受試者)"
        r"[\s:#_-]*(?:\d+|[A-Za-z0-9._-]*\d[A-Za-z0-9._-]*))"
    ),
)


def _sample_references(task: str) -> list[str]:
    references = []
    for pattern in _SAMPLE_REFERENCE_PATTERNS:
        for match in pattern.finditer(task):
            reference = match.group(0).strip(" ，,。.;；:")
            if reference and reference not in references:
                references.append(reference)
    return references


def validated_workflow_context(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    *,
    include_all: bool = False,
    task: str = "",
) -> dict[str, object]:
    """Return registry facts without granting execution authority."""
    seed_actions = list(dict.fromkeys([*decision.matched_actions, *decision.hypothesis_actions,
                                       *decision.recommended_actions, *decision.alternative_actions]))
    if include_all:
        seed_actions.extend(action for action in policy.workflows if action not in seed_actions)
    seed_actions = related_registry_actions(list(dict.fromkeys(seed_actions)), policy.workflows)
    relevant_actions = []
    compositions = []
    handoffs = []
    for action in seed_actions:
        spec = policy.workflows.get(action)
        if spec is None:
            continue
        predecessors = spec.output_capability.guidance_predecessors
        relevant_actions.extend(predecessors)
        relevant_actions.append(action)
        if predecessors:
            ordered = [*predecessors, action]
            compositions.append({
                "ordered_actions": ordered,
                "ordered_workflows": [policy.workflows[item].workflow for item in ordered if item in policy.workflows],
                "final_action": action,
            })
        for target in spec.output_capability.handoff_targets:
            target_spec = policy.workflows.get(target)
            if target_spec is None:
                continue
            handoffs.append({
                "from_action": action, "from_workflow": spec.workflow,
                "from_output": spec.output_capability.artifact_type,
                "to_action": target, "to_workflow": target_spec.workflow,
                "to_inputs": target_spec.output_capability.input_artifacts,
                "selection_tags": sorted(spec.output_capability.selection_tags),
                "handoff_contract": spec.output_capability.handoff_contract,
            })

    workflows = []
    for action in dict.fromkeys(relevant_actions):
        spec = policy.workflows.get(action)
        if spec is None:
            continue
        workflows.append(
            {
                "action": action,
                "workflow": spec.workflow,
                "description": spec.description,
                "required_inputs": [
                    item
                    for item in spec.required_inputs
                    if item not in OUTPUT_ROLE_FIELDS
                ],
                "output_roles": [
                    item
                    for item in spec.required_inputs
                    if item in OUTPUT_ROLE_FIELDS
                ],
                "optional_inputs": spec.optional_inputs,
                "conventions": spec.conventions,
                "role_labels": {
                    item: INPUT_LABELS.get(item, item)
                    for item in [*spec.required_inputs, *spec.optional_inputs]
                },
                "output_capability": spec.output_capability.model_dump(),
            }
        )
    guidance_decision = decision_with_registry_signals(decision, task, policy.workflows)
    selection_constraints = build_registry_selection_constraints(guidance_decision, workflows)
    return {
        "compositions": selection_constraints["preferred_compositions"] or compositions,
        "handoffs": handoffs,
        "workflows": workflows,
        "selection_constraints": selection_constraints,
        "sample_references": _sample_references(task),
    }
