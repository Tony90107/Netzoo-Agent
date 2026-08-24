"""Clarification and preference-confirmation interaction."""

from __future__ import annotations

import re
from pathlib import Path

from workflow_registry import ACTION_DEFINITIONS, registered_actions_for_family

from ..contracts import (
    ClarificationInputError,
    InputEvidence,
    LIONESS_MODE_QUESTION,
    TaskDecision,
    WorkflowPlan,
    _is_demo_request,
    _ui_text,
)
from ..interpretation import INPUT_LABELS


_FIELD_ASSIGNMENT = re.compile(
    r"(?:^|[\s,;])(?:"
    + "|".join(re.escape(field_name) for field_name in INPUT_LABELS)
    + r")\s*=",
    flags=re.IGNORECASE,
)

__all__ = [
    "_candidate_selection",
    "parse_clarification_assignments",
    "clarification_continuation",
    "bundle_clarification_continuation",
    "resolve_clarification",
    "clarification_prompt",
    "custom_clarification_prompt",
    "preference_confirmation_prompt",
    "preference_continuation",
]

def _candidate_selection(evidence: InputEvidence, value: str) -> str:
    cleaned = value.strip("'\".。")
    if not cleaned.isdigit():
        return cleaned
    index = int(cleaned) - 1
    if evidence.candidates and 0 <= index < len(evidence.candidates):
        return evidence.candidates[index]
    raise ClarificationInputError(
        f"{evidence.field} has no candidate numbered {cleaned}."
    )

def _action_for_registered_choice(value: str) -> str | None:
    normalized = value.casefold()
    for action in registered_actions_for_family("lioness"):
        definition = ACTION_DEFINITIONS[action]
        if definition.workflow.casefold() in normalized or action.casefold() in normalized:
            return action
    return None

def parse_clarification_assignments(
    plan: WorkflowPlan,
    answer: str,
    *,
    selected: dict[str, str] | None = None,
    target_field: str,
) -> dict[str, str]:
    """Parse one wizard response for its current missing field."""
    missing = [item for item in plan.evidence if item.status == "missing"]
    evidence_by_field = {item.field: item for item in missing}
    assignments = dict(selected or {})
    if target_field not in evidence_by_field:
        raise ClarificationInputError(
            "The current missing input could not be resolved."
        )
    stripped = answer.strip().strip("'\"")
    if stripped:
        if _FIELD_ASSIGNMENT.search(stripped):
            input_label = INPUT_LABELS.get(target_field, target_field)
            raise ClarificationInputError(
                f"Enter a candidate number or the full path for {input_label}; "
                "do not use field=value syntax."
            )
        assignments[target_field] = _candidate_selection(
            evidence_by_field[target_field],
            stripped,
        )
    return assignments

def clarification_continuation(
    plan: WorkflowPlan,
    assignments: dict[str, str],
) -> str:
    decision = TaskDecision.model_validate(plan.decision)
    carried = [
        item
        for item in plan.evidence
        if item.status == "discovered" and item.value and item.bundle_id
    ]
    selected_fields = [
        *[f"{item.field} is {item.value}" for item in carried],
        *[f"{field_name} is {value}" for field_name, value in assignments.items()],
    ]
    selected_markers = " ".join(
        f"SELECTED_FIELD={field_name}." for field_name in assignments
    )
    carried_markers = " ".join(
        f"CARRIED_DISCOVERED_FIELD={item.field}." for item in carried
    )
    return (
        f"PREVIOUS_ACTION={decision.action}. Continue the previous {plan.workflow} task; "
        "do not treat this as a new task. "
        "Selected input: " + "; ".join(selected_fields) + ". "
        f"{selected_markers} {carried_markers}".rstrip()
    )

def bundle_clarification_continuation(plan: WorkflowPlan, answer: str) -> str:
    """Apply one complete typed bundle atomically to the pending workflow."""
    cleaned = answer.strip().strip("'\".。")
    option = None
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(plan.input_bundle_options):
            option = plan.input_bundle_options[index]
    else:
        option = next(
            (
                item
                for item in plan.input_bundle_options
                if cleaned == item.directory or cleaned == item.bundle_id
            ),
            None,
        )
    if option is None:
        raise ClarificationInputError(
            f"The current plan has no complete bundle numbered {cleaned}."
        )
    missing_from_option = [
        field_name
        for field_name in plan.missing_inputs
        if field_name not in option.inputs
    ]
    if missing_from_option:
        raise ClarificationInputError(
            "The selected bundle is incomplete for: " + ", ".join(missing_from_option)
        )
    return (
        clarification_continuation(plan, option.inputs)
        + f" SELECTED_BUNDLE_ID={option.bundle_id}."
    )

def resolve_clarification(plan: WorkflowPlan, answer: str) -> str:
    """Convert paths or candidate numbers into a canonical continuation request."""
    missing = [item for item in plan.evidence if item.status == "missing"]
    mode_evidence = next(
        (item for item in missing if item.field == "lioness_mode"),
        None,
    )
    if mode_evidence is not None:
        stripped = answer.strip().strip("'\"")
        selected = _candidate_selection(mode_evidence, stripped)
        selected_action = _action_for_registered_choice(selected)
        if selected_action is None:
            return (
                "Continue the previous LIONESS task. The LIONESS base method is still "
                f"unresolved because the user answered: {answer}. Ask them to choose "
                "one of the registered LIONESS-compatible workflow options."
            )
        workflow_name = ACTION_DEFINITIONS[selected_action].workflow
        decision = TaskDecision.model_validate(plan.decision)
        known_fields = []
        for field_name in (
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "lioness_output",
        ):
            value = getattr(decision, field_name, None)
            if value:
                known_fields.append(f"{field_name} is {value}")
        demo_instruction = " as a demo/test" if _is_demo_request(plan.objective) else ""
        continuation = (
            f"PREVIOUS_ACTION={selected_action}. Continue the previous LIONESS task; "
            f"run {workflow_name}{demo_instruction}. "
            "Do not treat this mode selection as a new conceptual question."
        )
        if known_fields:
            continuation += " Confirmed inputs: " + "; ".join(known_fields) + "."
        return continuation

    unresolved = [item for item in missing if item.field != "lioness_mode"]
    if len(unresolved) != 1:
        raise ClarificationInputError(
            "Please answer the current missing input in the interactive wizard."
        )
    assignments = parse_clarification_assignments(
        plan,
        answer,
        target_field=unresolved[0].field,
    )
    return clarification_continuation(plan, assignments)

def _render_clarification_prompt(
    plan: WorkflowPlan,
    selected: dict[str, str] | None = None,
    *,
    custom: bool = False,
) -> str:
    mode_evidence = next(
        (
            item
            for item in plan.evidence
            if item.status == "missing" and item.field == "lioness_mode"
        ),
        None,
    )
    if mode_evidence is not None:
        lines = [_ui_text(LIONESS_MODE_QUESTION)]
        for index, candidate in enumerate(mode_evidence.candidates, 1):
            lines.append(f"{index}. {candidate}")
        lines.append(_ui_text("Selection > "))
        return "\n".join(lines)

    if plan.input_bundle_options and not custom:
        lines = [
            _ui_text(
                "Choose one complete input bundle, or enter custom to select files "
                "individually."
            )
        ]
        for index, option in enumerate(plan.input_bundle_options, 1):
            lines.append(f"{index}. {option.directory}/")
            lines.extend(
                f"   - {Path(value).name}" for value in option.inputs.values()
            )
        lines.append(_ui_text("Bundle selection > "))
        return "\n".join(lines)

    selected = selected or {}
    all_missing_items = [item for item in plan.evidence if item.status == "missing"]
    missing_items = [item for item in all_missing_items if item.field not in selected]
    if not missing_items:
        return _ui_text("No additional input is required.")

    current = missing_items[0]
    completed = len(all_missing_items) - len(missing_items)
    input_label = INPUT_LABELS.get(current.field, current.field)
    input_label = input_label[:1].upper() + input_label[1:]
    lines = []
    if custom:
        lines.extend(
            [
                _ui_text(
                    "Custom input composition: files may come from different bundles. "
                    "Compatibility validation is required before execution."
                ),
                "",
            ]
        )
    if not custom and not selected and plan.question:
        lines.extend([_ui_text(plan.question), ""])
    lines.extend(
        [
            _ui_text(
                f"Select input {completed + 1} of {len(all_missing_items)}: "
                f"{input_label} ({current.field})"
            ),
            _ui_text("Enter a candidate number or a full path."),
        ]
    )
    if selected:
        lines.append(_ui_text("Selections so far:"))
        for field_name, value in selected.items():
            lines.append(f"- {field_name}: {value}")
    if current.candidates:
        for candidate_index, candidate in enumerate(current.candidates, 1):
            lines.append(f"{candidate_index}. {candidate}")
    else:
        lines.append(_ui_text("Enter the full path."))
    lines.append(_ui_text("Selection > "))
    return "\n".join(lines)

def clarification_prompt(
    plan: WorkflowPlan,
    selected: dict[str, str] | None = None,
) -> str:
    """Render ordinary or complete-bundle clarification."""
    return _render_clarification_prompt(plan, selected, custom=False)

def custom_clarification_prompt(
    plan: WorkflowPlan,
    selected: dict[str, str] | None = None,
) -> str:
    """Render the explicitly requested per-field composition wizard."""
    return _render_clarification_prompt(plan, selected, custom=True)

def preference_confirmation_prompt(plan: WorkflowPlan) -> str:
    lines = [_ui_text("Save these long-term preferences? [y/N]")]
    for proposal in plan.preference_proposals:
        lines.append(f"- {proposal.key} = {proposal.value}")
    lines.append(_ui_text("Confirmation > "))
    return "\n".join(lines)

def preference_continuation(plan: WorkflowPlan, approved: bool) -> str:
    marker = (
        "PREFERENCE_CONFIRMATION_APPROVED"
        if approved
        else "PREFERENCE_CONFIRMATION_REJECTED"
    )
    decision = TaskDecision.model_validate(plan.decision)
    return (
        f"{marker}. Continue the previous {plan.workflow} task with action "
        f"{decision.action}. Do not propose these preference updates again in this turn."
    )
