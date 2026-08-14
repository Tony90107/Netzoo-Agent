"""Clarification and preference-confirmation interaction."""

from __future__ import annotations

import re

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
    "resolve_clarification",
    "clarification_prompt",
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
    selected_fields = [
        f"{field_name} is {value}" for field_name, value in assignments.items()
    ]
    selected_markers = " ".join(
        f"SELECTED_FIELD={field_name}." for field_name in assignments
    )
    return (
        f"PREVIOUS_ACTION={decision.action}. Continue the previous {plan.workflow} task; "
        "do not treat this as a new task. "
        "Selected input: " + "; ".join(selected_fields) + ". "
        f"{selected_markers}"
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
        selected = ""
        if stripped.isdigit():
            index = int(stripped) - 1
            if 0 <= index < len(mode_evidence.candidates):
                selected = mode_evidence.candidates[index]
        else:
            normalized = stripped.casefold()
            if "panda" in normalized:
                selected = mode_evidence.candidates[0]
            elif "puma" in normalized:
                selected = mode_evidence.candidates[1]
            elif re.search(
                r"(co[- _]?expression|coexpression|共表現|共同表現)",
                normalized,
                flags=re.IGNORECASE,
            ):
                selected = mode_evidence.candidates[2]
        if not selected:
            return (
                "Continue the previous LIONESS task. The LIONESS base method is still "
                f"unresolved because the user answered: {answer}. Ask them to choose "
                "LIONESS PANDA, LIONESS PUMA, or LIONESS co-expression."
            )

        if "panda" in selected.casefold():
            workflow_name = "LIONESS PANDA"
            selected_action = "run_lioness_panda"
        elif "puma" in selected.casefold():
            workflow_name = "LIONESS PUMA"
            selected_action = "run_lioness_puma"
        else:
            workflow_name = "LIONESS co-expression"
            selected_action = "run_lioness_coexpression"
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

def clarification_prompt(
    plan: WorkflowPlan,
    selected: dict[str, str] | None = None,
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

    selected = selected or {}
    all_missing_items = [item for item in plan.evidence if item.status == "missing"]
    missing_items = [item for item in all_missing_items if item.field not in selected]
    if not missing_items:
        return _ui_text("No additional input is required.")

    current = missing_items[0]
    completed = len(all_missing_items) - len(missing_items)
    input_label = INPUT_LABELS.get(current.field, current.field)
    input_label = input_label[:1].upper() + input_label[1:]
    lines = [
        _ui_text(
            f"Select input {completed + 1} of {len(all_missing_items)}: "
            f"{input_label} ({current.field})"
        ),
        _ui_text("Enter a candidate number or a full path."),
    ]
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
