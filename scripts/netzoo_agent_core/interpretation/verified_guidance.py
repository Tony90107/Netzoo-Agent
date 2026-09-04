"""Code-owned scientific recommendation rendering.

Capability recommendations are assertions, not stylistic prose. Their polarity,
scope and artifact definitions must not be rewritten by an unconstrained model.
Other conceptual/retrieval answers retain the response-model path.
"""
from __future__ import annotations

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..routing.method_rejections import rejected_methods_for
from .guidance_interaction import guidance_interaction
from .scientific_explanations import scientific_explanations


def guidance_contract(decision: TaskDecision, policy: ProjectPolicySnapshot, task: str) -> dict:
    """Recompute trusted response assertions; model-supplied reasons are not facts."""
    inputs = decision.requested_outcome.input_artifacts if decision.requested_outcome else decision.guidance_input_artifacts
    actions = list(dict.fromkeys([*decision.matched_actions, *decision.recommended_actions]))
    rejections = rejected_methods_for(
        task, inputs, actions=[*actions, *(item.action for item in decision.rejected_methods)],
        capabilities={action: spec.output_capability for action, spec in policy.workflows.items()},
        names={action: spec.workflow for action, spec in policy.workflows.items()},
    )
    return {
        "explanations": scientific_explanations(
            task, [policy.workflows[action].output_capability.model_dump() for action in actions
                   if action in policy.workflows and action not in {item.action for item in rejections}],
            [item.model_dump() for item in rejections],
        ),
        "match_status": decision.capability_match_status, "match_basis": decision.match_basis,
        "rejected_methods": [item.model_dump() for item in rejections],
        "artifact_definitions": {artifact: rule.description for artifact, rule in ARTIFACT_SEMANTICS.items()},
        "workflows": [dict(action=action, workflow=policy.workflows[action].workflow,
                           description=policy.workflows[action].description,
                           output_capability=policy.workflows[action].output_capability.model_dump())
                      for action in actions if action in policy.workflows],
    }


def render_verified_guidance(decision: TaskDecision, facts: dict) -> str | None:
    if decision.action != "no_tool" or decision.should_execute:
        return None
    rejected = facts["rejected_methods"]
    rejected_actions = {item["action"] for item in rejected}
    selected = list(dict.fromkeys(decision.recommended_actions or decision.matched_actions))
    selected = [action for action in selected if action not in rejected_actions]
    if not rejected and not (selected and decision.capability_match_status in {"exact", "fallback"}):
        return None
    lines = []
    for item in rejected:
        artifacts = ", ".join(item["input_artifacts"])
        lines.append(
            f"Do not use **{item['workflow']}** with the current `{artifacts}` input. "
            f"{item['reason']} This restriction concerns this registered workflow and "
            "these inputs, not every possible use of the method."
        )
    workflows = {item["action"]: item for item in facts["workflows"]}
    selected = [action for action in selected if action in workflows]
    if selected:
        names = " → ".join(workflows[action]["workflow"] for action in selected)
        if decision.capability_match_status == "fallback":
            interaction = guidance_interaction(decision)
            lines.append(f"Fallback recommendation: **{names}**. {interaction.explanation}")
        else:
            lines.append(f"Selected path: **{names}**.")
        explanations = facts.get("explanations", [])
        if explanations:
            lines.append("Why this recommendation:\n\n" + "\n\n".join(explanations))
        for action in selected:
            item = workflows[action]
            capability = item["output_capability"]
            modalities = capability["accepted_input_modalities"] or capability["input_artifacts"]
            lines.append(f"**{item['workflow']}**: {item['description']}\n\n"
                         f"Accepted inputs: {', '.join(value.replace('_', ' ') for value in modalities)}.")
            transformations = capability["transformations"]
            if transformations and not explanations:
                lines.append("Declared transformations:\n\n" + "\n".join(
                    f"- {value.replace('_', ' ')}" for value in transformations
                ))
            artifacts = capability["produced_artifacts"] or [capability["artifact_type"]]
            lines.append("Distinct declared output artifacts (availability depends on workflow options):\n\n" + "\n".join(
                f"- `{artifact}`: {facts['artifact_definitions'][artifact]}."
                for artifact in sorted(artifacts)
            ))
    elif rejected:
        lines.append("No compatible workflow has been selected for execution.")
    lines.append("This is workflow guidance only; no execution was authorized. "
                 "No files were inspected and no analysis ran.")
    return "\n\n".join(lines)
