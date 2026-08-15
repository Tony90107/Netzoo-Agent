"""Registry-derived capability context for response generation."""

from __future__ import annotations

from ..contracts import OUTPUT_ROLE_FIELDS, ProjectPolicySnapshot, TaskDecision
from ..interpretation import INPUT_LABELS

__all__: list[str] = []


def validated_workflow_context(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> dict[str, list[dict]]:
    """Return ordered compositions and workflow facts from validated policy only."""
    seed_actions = list(
        dict.fromkeys(
            [
                *decision.matched_actions,
                *decision.hypothesis_actions,
                *decision.recommended_actions,
                *decision.alternative_actions,
            ]
        )
    )
    relevant_actions = []
    compositions = []
    for action in seed_actions:
        spec = policy.workflows.get(action)
        if spec is None:
            continue
        predecessors = spec.output_capability.guidance_predecessors
        relevant_actions.extend(predecessors)
        relevant_actions.append(action)
        if predecessors:
            ordered_actions = [*predecessors, action]
            compositions.append(
                {
                    "ordered_actions": ordered_actions,
                    "ordered_workflows": [
                        policy.workflows[item].workflow
                        for item in ordered_actions
                        if item in policy.workflows
                    ],
                    "final_action": action,
                }
            )

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
                "role_labels": {
                    item: INPUT_LABELS.get(item, item)
                    for item in [*spec.required_inputs, *spec.optional_inputs]
                },
                "output_capability": spec.output_capability.model_dump(),
            }
        )
    return {"compositions": compositions, "workflows": workflows}
