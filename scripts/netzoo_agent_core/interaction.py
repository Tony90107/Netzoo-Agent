"""Clarification, preference confirmation, and next-turn interaction."""

from __future__ import annotations

import re
from pathlib import Path


from workflow_registry import (
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from .contracts import (
    ClarificationInputError,
    InputEvidence,
    LIONESS_MODE_QUESTION,
    NextTurnPrompt,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
    _is_demo_request,
    _ui_text,
)

from .interpretation import (
    INPUT_LABELS,
    _candidate_keywords,
)
from .outcomes import effective_results, terminal_failed

__all__ = [
    "CLARIFICATION_FIELD_ALIASES",
    "_candidate_selection",
    "parse_clarification_assignments",
    "clarification_continuation",
    "resolve_clarification",
    "clarification_prompt",
    "preference_confirmation_prompt",
    "preference_continuation",
    "initial_next_turn_prompt",
    "build_next_turn_prompt",
    "follow_up_declined",
    "render_next_turn_prompt",
    "follow_up_returns_to_main",
    "resolve_next_turn_input",
]


CLARIFICATION_FIELD_ALIASES = {
    **{field_name: field_name for field_name in TaskDecision.model_fields},
    "expression": "expression_file",
    "motif": "motif_file",
    "prior": "motif_file",
    "ppi": "ppi_file",
    "mirna": "mirna_file",
    "network": "network_file",
    "output": "output_file",
}


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
    target_field: str | None = None,
    require_all: bool = True,
) -> dict[str, str]:
    """Parse one batch or one wizard step without invoking the graph."""
    missing = [item for item in plan.evidence if item.status == "missing"]
    evidence_by_field = {item.field: item for item in missing}
    assignments = dict(selected or {})

    for label, value in re.findall(
        r"([A-Za-z_]+)\s*[=:：]\s*([^\s，,；;]+)",
        answer,
    ):
        field_name = CLARIFICATION_FIELD_ALIASES.get(label.casefold())
        if not field_name or field_name not in evidence_by_field:
            continue
        assignments[field_name] = _candidate_selection(
            evidence_by_field[field_name],
            value,
        )

    stripped = answer.strip().strip("'\"")
    new_fields = set(assignments) - set(selected or {})
    unresolved = [item for item in missing if item.field not in assignments]
    choice_tokens = [token for token in re.split(r"[\s,，;；]+", stripped) if token]
    numeric_sequence = bool(choice_tokens) and all(
        token.isdigit() for token in choice_tokens
    )

    if not new_fields and numeric_sequence:
        if len(choice_tokens) == len(unresolved):
            for evidence, token in zip(unresolved, choice_tokens, strict=True):
                assignments[evidence.field] = _candidate_selection(evidence, token)
        elif target_field and len(choice_tokens) == 1:
            evidence = evidence_by_field[target_field]
            assignments[target_field] = _candidate_selection(
                evidence,
                choice_tokens[0],
            )
        else:
            fields = ", ".join(item.field for item in unresolved)
            raise ClarificationInputError(
                f"{len(unresolved)} inputs are still required ({fields}). "
                "Enter one candidate number for the current field, one number per "
                "remaining field in display order, or explicit field=number pairs."
            )
    elif not new_fields and stripped:
        if target_field:
            assignments[target_field] = _candidate_selection(
                evidence_by_field[target_field],
                stripped,
            )
        elif len(unresolved) == 1:
            assignments[unresolved[0].field] = _candidate_selection(
                unresolved[0],
                stripped,
            )
        else:
            lowered = Path(stripped).name.casefold()
            decision = TaskDecision.model_validate(plan.decision)
            for evidence in unresolved:
                keywords = _candidate_keywords(decision.action, evidence.field)
                if any(keyword in lowered for keyword in keywords):
                    assignments[evidence.field] = stripped
                    break

    if require_all:
        still_missing = [
            item.field for item in missing if item.field not in assignments
        ]
        if still_missing:
            raise ClarificationInputError(
                "The reply did not resolve every displayed input. Still missing: "
                + ", ".join(still_missing)
                + ". Enter one candidate number per field in order, or use "
                "explicit field=value pairs."
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

    assignments = parse_clarification_assignments(plan, answer)
    return clarification_continuation(plan, assignments)


def clarification_prompt(
    plan: WorkflowPlan,
    selected: dict[str, str] | None = None,
    *,
    batch: bool = False,
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

    if not batch:
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
            lines.append(f"{current.field}=<full path>")
        if len(all_missing_items) > 1:
            lines.append(
                _ui_text(
                    "Advanced: enter all remaining fields at once with "
                    "field=value pairs."
                )
            )
        lines.append(_ui_text("Selection > "))
        return "\n".join(lines)

    lines = [
        _ui_text("Provide all missing inputs in one reply."),
        _ui_text("Use field=value pairs separated by spaces or semicolons."),
    ]
    for item_index, item in enumerate(missing_items, 1):
        lines.append(f"{item_index}. {item.field}")
        if item.candidates:
            for candidate_index, candidate in enumerate(item.candidates, 1):
                lines.append(f"   {item.field}={candidate_index} → {candidate}")
        else:
            lines.append(f"   {item.field}=<full path>")
    if len(missing_items) == 1 and missing_items[0].candidates:
        lines.append(_ui_text("A single candidate number such as 1 is also accepted."))
    elif all(item.candidates for item in missing_items):
        example = " ".join("1" for _ in missing_items)
        lines.append(
            _ui_text(
                "Or enter one candidate number per field in the displayed order, "
                f"for example: {example}"
            )
        )
        lines.append(
            _ui_text(
                "A single number is ambiguous here and will not start the workflow."
            )
        )
    lines.append(_ui_text("Inputs > "))
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


def initial_next_turn_prompt() -> NextTurnPrompt:
    return NextTurnPrompt(
        kind="initial",
        question=_ui_text("What would you like to accomplish with NetZoo?"),
    )


def build_next_turn_prompt(state: dict) -> NextTurnPrompt:
    """Choose the next CLI question from the completed turn's structured outcome."""
    plan = WorkflowPlan.model_validate(state["plan"])
    decision = TaskDecision.model_validate(plan.decision)
    plan_evaluation = (
        PlanEvaluationResult.model_validate(state["plan_evaluation"])
        if state.get("plan_evaluation")
        else None
    )
    results = [
        ToolExecutionResult.model_validate(item)
        for item in state.get("tool_results", [])
    ]
    results = effective_results(results)
    result_evaluation = state.get("evaluation")

    if plan_evaluation and plan_evaluation.status == "rejected":
        return NextTurnPrompt(
            kind="plan_rejected",
            question=_ui_text(
                "Would you like to revise the rejected plan or describe a different deliverable?"
            ),
        )

    if decision.action == "no_tool" and decision.recommended_actions:
        action = decision.recommended_actions[-1]
        required_inputs = [
            field_name
            for field_name in REQUIRED_INPUTS.get(action, ())
            if field_name not in OUTPUT_ROLE_FIELDS
        ]
        expected_field = required_inputs[0] if required_inputs else None
        workflow = _workflow_name(action)
        field_hint = (
            f" or provide the {INPUT_LABELS.get(expected_field, expected_field)} path"
            if expected_field
            else ""
        )
        return NextTurnPrompt(
            kind="recommended_workflow",
            question=_ui_text(
                f"Would you like to continue with the recommended {workflow} workflow? "
                f"Reply yes to start{field_hint}, or type a new request."
            ),
            continuation_action=action,
            expected_field=expected_field,
        )

    if (
        terminal_failed(results, result_evaluation)
    ):
        return NextTurnPrompt(
            kind="failed",
            question=_ui_text(
                f"The {plan.workflow} workflow stopped. Would you like to correct "
                "its inputs or try a different workflow?"
            ),
        )

    if any(item.status == "dry_run" for item in results):
        return NextTurnPrompt(
            kind="dry_run",
            question=_ui_text(
                f"The {plan.workflow} command preview is ready. Would you like to "
                "adjust its inputs or explore another workflow? Use --execute on "
                "restart to perform the analysis."
            ),
        )

    if decision.action in {"query_context7", "web_search"}:
        return NextTurnPrompt(
            kind="retrieval",
            question=_ui_text(
                "Would you like to ask about these sources or connect them to a "
                "NetZoo workflow?"
            ),
        )

    if results and result_evaluation.get("status") == "completed":
        return NextTurnPrompt(
            kind="completed",
            question=_ui_text(
                f"The {plan.workflow} workflow is complete. Would you like to inspect "
                "or refine the result, or start another workflow?"
            ),
        )

    if decision.action == "no_tool" and not decision.in_scope:
        return NextTurnPrompt(
            kind="unsupported",
            question=_ui_text(
                "Would you like to see the supported capabilities or describe a "
                "different NetZoo deliverable?"
            ),
        )

    return NextTurnPrompt(
        kind="completed",
        question=_ui_text(
            "Would you like to ask a follow-up about this answer or describe another "
            "NetZoo goal?"
        ),
    )


def follow_up_declined(answer: str) -> bool:
    return answer.strip().casefold() in {
        "n",
        "no",
        "nope",
        "不用",
        "不要",
        "否",
        "先不要",
    }


def render_next_turn_prompt(prompt: NextTurnPrompt) -> str:
    """Render navigation help without repeating it inside every outcome template."""
    if prompt.kind == "initial":
        return prompt.question
    return "\n".join(
        [
            prompt.question,
            _ui_text("Controls: Enter/back = main prompt | exit = close"),
        ]
    )


def follow_up_returns_to_main(prompt: NextTurnPrompt, answer: str) -> bool:
    if prompt.kind == "initial":
        return False
    return answer.strip().casefold() in {
        "",
        "back",
        "menu",
        "new",
        "main",
        "返回",
        "主選單",
        "新任務",
    }


def resolve_next_turn_input(prompt: NextTurnPrompt, answer: str) -> str:
    """Turn a short acceptance or direct path into a resumable workflow request."""
    stripped = answer.strip()
    if not prompt.continuation_action:
        return stripped
    normalized = stripped.casefold()
    affirmative = normalized in {
        "y",
        "yes",
        "ok",
        "okay",
        "start",
        "continue",
        "好",
        "好的",
        "可以",
        "繼續",
        "開始",
        "要",
    }
    looks_like_path = bool(
        re.search(r"[/\\]|\.(?:tsv|tab|txt|csv|npy)$", stripped, flags=re.IGNORECASE)
    )
    if not affirmative and not looks_like_path:
        return stripped

    continuation = (
        f"PREVIOUS_ACTION={prompt.continuation_action}. Continue the recommended "
        f"{_workflow_name(prompt.continuation_action)} workflow. The user accepted "
        "the previous capability recommendation."
    )
    if looks_like_path and prompt.expected_field:
        continuation += f" {prompt.expected_field} is {stripped}."
    return continuation
