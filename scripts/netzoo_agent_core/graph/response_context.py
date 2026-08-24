"""Registry-derived capability context for response generation."""

from __future__ import annotations

import re

from ..contracts import OUTPUT_ROLE_FIELDS, ProjectPolicySnapshot, TaskDecision
from ..interpretation import INPUT_LABELS

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
) -> dict[str, list[dict]]:
    """Return registry facts without granting them execution authority.

    Guidance turns may need to explain a multi-stage request whose first semantic
    interpretation points at an unsupported final artifact. Include the complete
    validated catalog for those turns so the response model can map the user's
    stages to capabilities. Execution still uses the exact action selected by the
    matcher and never consumes this catalog as authorization.
    """
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
    if include_all:
        seed_actions.extend(
            action for action in policy.workflows if action not in seed_actions
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
                "conventions": spec.conventions,
                "role_labels": {
                    item: INPUT_LABELS.get(item, item)
                    for item in [*spec.required_inputs, *spec.optional_inputs]
                },
                "output_capability": spec.output_capability.model_dump(),
            }
        )
    return {"compositions": compositions, "workflows": workflows, "sample_references": _sample_references(task)}
