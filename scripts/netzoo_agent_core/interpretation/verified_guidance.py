"""Code-owned scientific recommendation rendering.

Capability recommendations are assertions, not stylistic prose. Their polarity,
scope and artifact definitions must not be rewritten by an unconstrained model.
Other conceptual/retrieval answers retain the response-model path.
"""
from __future__ import annotations

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _NON_ENGLISH
from ..routing.capability_compatibility import input_availability
from ..routing.method_rejections import rejected_methods_for
from ..routing.clarification_planner import algorithmic_assumptions_for
from ..runtime_constraints import runtime_control_constraints
from ..settings import INPUT_ROLE_FIELDS
from workflow_registry import OTHER_READING_NOTES, REQUEST_CONCERNS, get_controls
from .extraction import INPUT_LABELS
from .guidance_interaction import guidance_interaction
from .scientific_explanations import scientific_explanations
from .method_philosophy import method_philosophies_for, question_fit_for
from .request_parameters import extract_explicit_request_parameters, render_request_parameters


from .scientific_guidance import _TECHNICAL
import re as _re

_OPERATIONAL = _re.compile(_TECHNICAL.pattern + r"|\b(?:controls?|settings?)\b", _re.I)


def guidance_contract(decision: TaskDecision, policy: ProjectPolicySnapshot, task: str) -> dict:
    """Recompute trusted response assertions; model-supplied reasons are not facts."""
    semantic_inputs = (
        decision.requested_outcome.input_artifacts
        if decision.requested_outcome
        else decision.guidance_input_artifacts
    )
    inputs = sorted(set(semantic_inputs) - {"unknown"})
    stated_input_availability = input_availability(task)
    actions = list(dict.fromkeys([*decision.matched_actions, *decision.recommended_actions]))
    rejections = rejected_methods_for(
        task, inputs, actions=[*actions, *(item.action for item in decision.rejected_methods)],
        capabilities={action: spec.output_capability for action, spec in policy.workflows.items()},
        names={action: spec.workflow for action, spec in policy.workflows.items()},
    )
    return {
        "input_compatibility": (
            "assessed"
            if inputs or stated_input_availability.present or stated_input_availability.absent
            else "not_assessed"
        ),
        "explanations": scientific_explanations(
            task, [policy.workflows[action].output_capability.model_dump(exclude={"prefer_when"}) for action in actions
                   if action in policy.workflows and action not in {item.action for item in rejections}],
            [item.model_dump() for item in rejections],
        ),
        "match_status": decision.capability_match_status, "match_basis": decision.match_basis,
        "rejected_methods": [item.model_dump() for item in rejections],
        "artifact_definitions": {artifact: rule.description for artifact, rule in ARTIFACT_SEMANTICS.items()},
        "requested_parameters": extract_explicit_request_parameters(task),
        # An explicit request for controls, parameters or defaults (Log 256's pattern).
        "operational_request": bool(_OPERATIONAL.search(task)),
        "addressed_concerns": addressed_concern_facts(decision),
        "workflows": [dict(action=action, workflow=policy.workflows[action].workflow,
                           description=policy.workflows[action].description,
                           required_inputs=[
                               field
                               for field in policy.workflows[action].required_inputs
                               if field in INPUT_ROLE_FIELDS
                           ],
                           required_input_groups=[
                               [field for field in group if field in INPUT_ROLE_FIELDS]
                               for group in policy.workflows[action].required_input_groups
                           ],
                           optional_inputs=list(policy.workflows[action].optional_inputs),
                           controls=[
                               control.model_dump(mode="json")
                               for control in get_controls(action, registry=policy.workflows)
                           ],
                           role_labels={
                                field: INPUT_LABELS.get(field, field.replace("_", " "))
                                for field in dict.fromkeys(
                                    [
                                        *policy.workflows[action].required_inputs,
                                        *(
                                            field
                                            for group in policy.workflows[action].required_input_groups
                                            for field in group
                                        ),
                                    ]
                                )
                                if field in INPUT_ROLE_FIELDS
                            },
                           output_capability=policy.workflows[action].output_capability.model_dump(exclude={"prefer_when"}))
                      for action in actions if action in policy.workflows],
    }


def addressed_concern_facts(decision: TaskDecision) -> list[dict]:
    """Each quoted concern with the registry's note, controls and outputs (Log 223)."""
    facts = []
    for item in decision.addressed_concerns:
        declared = next(
            (entry for entry in REQUEST_CONCERNS.get(item.action, ()) if entry.concern == item.concern),
            None,
        )
        if declared is not None:
            facts.append(dict(
                action=item.action, concern=item.concern, text_span=item.text_span,
                note=declared.note, controls=list(declared.controls),
                artifacts=list(declared.artifacts),
            ))
    return facts


def render_verified_guidance(decision: TaskDecision, facts: dict) -> str | None:
    if decision.action != "no_tool" or decision.should_execute:
        return None
    rejected = facts["rejected_methods"]
    rejected_actions = {item["action"] for item in rejected}
    selected = list(dict.fromkeys(decision.recommended_actions or decision.matched_actions))
    selected = [action for action in selected if action not in rejected_actions]
    requested_tags = set(
        decision.requested_outcome.selection_tags
        if decision.requested_outcome is not None
        else ()
    )
    if not rejected and not (selected and decision.capability_match_status in {"exact", "fallback"}):
        return None
    lines = []
    assumptions = list(dict.fromkeys(
        " ".join(assumption.split())
        for hypothesis in decision.outcome_hypotheses
        for assumption in hypothesis.assumptions
        # Model-written text in another language is not shown (Log 207).
        if assumption.strip() and not _NON_ENGLISH.search(assumption)
    ))
    if assumptions:
        lines.append(
            "Assumptions behind this recommendation (not confirmed facts):\n\n"
            + "\n".join(f"- {item}" for item in assumptions[:6])
        )
    if facts.get("input_compatibility") == "not_assessed":
        lines.append("Input compatibility has not been assessed because no current input is established.")
    for item in rejected:
        artifacts = ", ".join(item["input_artifacts"])
        lines.append(
            f"Do not use **{item['workflow']}** with the current `{artifacts}` input. "
            f"{item['reason']} This restriction concerns this registered workflow and "
            "these inputs, not every possible use of the method."
        )
    workflows = {item["action"]: item for item in facts["workflows"]}
    selected = [action for action in selected if action in workflows]
    concerns = [item for item in facts.get("addressed_concerns", []) if item["action"] in selected]
    # AGENTS.md: a conceptual answer is prose; controls, defaults and parameter
    # lists expand only when the request is operational (Log 283).
    concern_controls_all = {name for concern in concerns for name in concern["controls"]}
    detailed = bool(
        rejected or facts.get("requested_parameters") or facts.get("operational_request") or concern_controls_all
        or decision.intent_type == "run_analysis"
        or any(set(control.get("selection_tags", [])) & requested_tags
               for action in selected for control in workflows[action].get("controls", []))
    )
    if selected and not detailed:
        _render_compact(lines, decision, selected, workflows, facts, concerns)
    elif selected:
        names = " → ".join(workflows[action]["workflow"] for action in selected)
        if decision.capability_match_status == "fallback":
            interaction = guidance_interaction(decision)
            lines.append(f"Fallback recommendation: **{names}**. {interaction.explanation}")
        else:
            lines.append(f"Selected path: **{names}**.")
        if len(selected) == 1:
            action = selected[0]
            fit = question_fit_for(
                decision.requested_outcome, workflows[action]["workflow"],
                workflows[action]["output_capability"],
                qualified=decision.capability_match_status == "exact",
            )
            if fit:
                lines.append(fit)
        requested_parameters = facts.get("requested_parameters") or {}
        if requested_parameters:
            lines.append(render_request_parameters(requested_parameters))
        explanations = facts.get("explanations", [])
        if explanations:
            lines.append("Why this recommendation:\n\n" + "\n\n".join(explanations))
        concerns = [item for item in facts.get("addressed_concerns", []) if item["action"] in selected]
        if concerns:
            named = len(selected) > 1
            lines.append("What you asked about:\n\n" + "\n".join(
                "- "
                + (f"**{workflows[item['action']]['workflow']}** · " if named else "")
                + f"\"{' '.join(item['text_span'].split())}\" — {item['note']}"
                for item in concerns
            ))
        for action in selected:
            item = workflows[action]
            capability = item["output_capability"]
            modalities = capability["accepted_input_modalities"] or capability["input_artifacts"]
            lines.append(f"**{item['workflow']}**: {item['description']}\n\n"
                         f"Routing-level input modality: {', '.join(value.replace('_', ' ') for value in modalities)}.")
            premises = algorithmic_assumptions_for(capability["selection_tags"])
            if premises:
                lines.append("Method premise: " + "; ".join(premises) + ".")
            lines.extend(method_philosophies_for(capability["selection_tags"]))
            guidance_notes = capability.get("guidance_notes", [])
            if guidance_notes:
                lines.append(
                    "Workflow-specific scientific notes:\n\n"
                    + "\n".join(f"- {note}" for note in guidance_notes)
                )
            required_inputs = item.get("required_inputs", [])
            if required_inputs:
                role_labels = item.get("role_labels", {})
                lines.append("Required workflow inputs:\n\n" + "\n".join(
                    f"- `{field}`: {role_labels.get(field, field.replace('_', ' '))}"
                    for field in required_inputs
                ))
            for group in item.get("required_input_groups", []):
                if group:
                    role_labels = item.get("role_labels", {})
                    lines.append(
                        "Required alternative (provide one):\n\n"
                        + "\n".join(
                            f"- `{field}`: {role_labels.get(field, field.replace('_', ' '))}"
                            for field in group
                        )
                    )
            # Only a control whose registry tags meet the request's tags, or that a
            # quoted concern points to (Log 223), is matched to it; the rest are
            # declared but not claimed as relevant (Log 221).
            controls = item.get("controls", [])
            concern_controls = {
                name for concern in concerns if concern["action"] == action
                for name in concern["controls"]
            }
            matched_controls = [
                control for control in controls
                if set(control.get("selection_tags", [])) & requested_tags
                or control["name"] in concern_controls
            ]
            other_controls = [control for control in controls if control not in matched_controls]
            if matched_controls:
                lines.append(
                    "Controls matching this request:\n\n"
                    + "\n".join(
                        _render_control(action, control) for control in matched_controls
                    )
                )
            if other_controls:
                lines.append(
                    "Other declared controls (not matched to this request; defaults apply "
                    "unless you set them): "
                    + ", ".join(_render_control_default(control) for control in other_controls)
                    + "."
                )
            runtime_limits = [
                limit for control in other_controls
                if (limit := _runtime_limit(action, control)) is not None
            ]
            if runtime_limits:
                lines.append("Runtime limits:\n\n" + "\n".join(runtime_limits))
            conditional_outputs = capability.get("conditional_outputs", [])
            for conditional in conditional_outputs:
                if not conditional.get("valid", True):
                    continue
                conditions = " and ".join(
                    f"`{name}={value}`" for name, value in conditional["when"].items()
                )
                lines.append(
                    f"When {conditions}: {conditional['semantics']}."
                )
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
            if action in OTHER_READING_NOTES:  # Log 219's other reading, always named (Log 283)
                lines.append(OTHER_READING_NOTES[action])
    elif rejected:
        lines.append("No compatible workflow has been selected for execution.")
    lines.append("This is workflow guidance only; no execution was authorized. "
                 "No files were inspected and no analysis ran.")
    return "\n\n".join(lines)


def _render_compact(lines, decision, selected, workflows, facts, concerns) -> None:
    """The workflow in prose: why it fits, how it works, what it needs and gives."""
    names = " → ".join(workflows[action]["workflow"] for action in selected)
    if decision.capability_match_status == "fallback":
        lines.append(f"Fallback recommendation: **{names}**. {guidance_interaction(decision).explanation}")
    else:
        lines.append(f"Selected path: **{names}**.")
    if len(selected) == 1:
        action = selected[0]
        fit = question_fit_for(
            decision.requested_outcome, workflows[action]["workflow"], workflows[action]["output_capability"],
            qualified=decision.capability_match_status == "exact", mechanism=False,
        )
        if fit:
            lines.append(fit)
    if explanations := facts.get("explanations", []):
        lines.append("Why this recommendation:\n\n" + "\n\n".join(explanations))
    if concerns:
        named = len(selected) > 1
        lines.append("What you asked about:\n\n" + "\n".join(
            "- " + (f"**{workflows[item['action']]['workflow']}** · " if named else "")
            + f"\"{' '.join(item['text_span'].split())}\" — {item['note']}"
            for item in concerns
        ))
    for action in selected:
        item = workflows[action]
        capability = item["output_capability"]
        mechanism = " ".join(method_philosophies_for(capability["selection_tags"]))
        lines.append(f"**{item['workflow']}** — {item['description']}" + (f" {mechanism}" if mechanism else ""))
        # The registry's input roles and outputs stay listed: they are short and
        # they are what the user needs to act on the answer.
        labels = item.get("role_labels", {})
        if item.get("required_inputs"):
            lines.append("Required workflow inputs:\n\n" + "\n".join(
                f"- `{f}`: {labels.get(f, f.replace('_', ' '))}" for f in item["required_inputs"]))
        for group in item.get("required_input_groups", []):
            if group:
                lines.append("Required alternative (provide one):\n\n" + "\n".join(
                    f"- `{f}`: {labels.get(f, f.replace('_', ' '))}" for f in group))
        artifacts = capability["produced_artifacts"] or [capability["artifact_type"]]
        lines.append("Outputs:\n\n" + "\n".join(
            f"- `{a}`: {facts['artifact_definitions'][a]}." for a in sorted(artifacts)))
        if guidance_notes := capability.get("guidance_notes", []):
            lines.append("Workflow-specific scientific notes:\n\n" + "\n".join(f"- {note}" for note in guidance_notes))
        if action in OTHER_READING_NOTES:
            lines.append(OTHER_READING_NOTES[action])
        for conditional in capability.get("conditional_outputs", []):
            if conditional.get("valid", True):
                conditions = " and ".join(f"`{n}={v}`" for n, v in conditional["when"].items())
                lines.append(f"When {conditions}: {conditional['semantics']}.")
        # A limit of this runtime prevents a failed run; it stays in the short form.
        limits = [limit for control in item.get("controls", []) if (limit := _runtime_limit(action, control))]
        if limits:
            lines.append("Runtime limits:\n\n" + "\n".join(limits))
    lines.append("Ask for the workflow's controls and defaults if you want to set them.")


def _render_control(action: str, control: dict) -> str:
    """Render only metadata declared by the workflow registry."""
    details = [f"type={control.get('type', control.get('control_type'))}"]
    if "default" in control:
        details.append(f"default={control['default']}")
    if control.get("allowed_values"):
        details.append("allowed=" + ", ".join(map(str, control["allowed_values"])))
    if control.get("minimum") is not None or control.get("maximum") is not None:
        details.append(
            f"range={control.get('minimum', '-∞')}..{control.get('maximum', '∞')}"
        )
    description = control.get("description")
    suffix = f" — {description}" if description else ""
    limit = _runtime_limit_text(action, control)
    if limit is not None:
        suffix += " — " + limit
    return f"- `{control['name']}` ({'; '.join(details)}){suffix}"


def _render_control_default(control: dict) -> str:
    """Name and registry default only, for a control not matched to the request."""
    if control.get("default") is None:
        return f"`{control['name']}`"
    return f"`{control['name']}`={control['default']}"


def _runtime_limit(action: str, control: dict) -> str | None:
    limit = _runtime_limit_text(action, control)
    return None if limit is None else f"- `{control['name']}`: {limit}"


def _runtime_limit_text(action: str, control: dict) -> str | None:
    constraint = runtime_control_constraints(action).get(control["name"])
    if constraint is None:
        return None
    unavailable = sorted(
        set(map(str, control.get("allowed_values", [])))
        & set(constraint.unavailable_values)
    )
    if not unavailable:
        return None
    fallback = (
        f"; use `{control['name']}={constraint.fallback}`"
        if constraint.fallback is not None
        else ""
    )
    return "current runtime unavailable: " + ", ".join(unavailable) + fallback + "."
