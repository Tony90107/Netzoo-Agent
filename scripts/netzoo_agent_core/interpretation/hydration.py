"""Hydrate compact router output into the complete task decision."""

from __future__ import annotations

import re

from workflow_registry import REQUIRED_INPUTS

from ..contracts import RouterDecision, TaskDecision
from ..routing import _extract_named_path
from ..settings import PARAMETER_FIELDS
from .input_bindings import request_input_bindings
from .extraction import (
    _task_path,
    documentation_library_for_task,
    extract_preference_proposals,
)
from .outcome_consistency import select_primary_hypothesis
from .request_parameters import (
    extract_explicit_request_parameters,
)

__all__: list[str] = []


def hydrate_router_decision(
    raw_decision: RouterDecision | TaskDecision | dict,
    task: str,
) -> TaskDecision:
    """Hydrate the small Router interface with deterministic task details."""
    if isinstance(raw_decision, TaskDecision):
        decision = raw_decision.model_copy(deep=True)
    else:
        route = RouterDecision.model_validate(raw_decision)
        primary = select_primary_hypothesis(route.outcome_hypotheses, user_task=task)
        selected_action = route.selected_action or route.action
        candidates = list(dict.fromkeys([*route.candidate_actions, selected_action]))
        decision = TaskDecision(
            action=selected_action,
            in_scope=route.in_scope,
            should_execute=selected_action != "no_tool",
            intent_type=route.intent_type,
            confidence=route.confidence,
            reason=route.reason,
            candidate_actions=candidates,
            clarification_question=route.clarification_question,
            requested_outcome=primary.outcome if primary else None,
            outcome_hypotheses=route.outcome_hypotheses,
            matched_actions=[],
            recommended_actions=[],
            alternative_actions=[],
        )

    for field_name, parsed in request_input_bindings(task).values.items():
        setattr(decision, field_name, parsed)

    for field_name in (
        "output_file",
        "lioness_output",
        "output_dir",
    ):
        parsed = _task_path(task, field_name)
        if parsed:
            setattr(decision, field_name, parsed)

    explicit_parameters = extract_explicit_request_parameters(task)
    parameter_updates = {
        field_name: value
        for field_name, value in explicit_parameters.items()
        if field_name in PARAMETER_FIELDS
    }
    if parameter_updates:
        decision = TaskDecision.model_validate({
            **decision.model_dump(),
            **parameter_updates,
        })
    if output_file := explicit_parameters.get("output_file"):
        decision.output_file = str(output_file)
        if "output_dir" not in explicit_parameters:
            decision.output_dir = None
    elif output_dir := explicit_parameters.get("output_dir"):
        decision.output_dir = str(output_dir)

    prefix = _extract_named_path(task, ("prefix", "前綴"))
    if prefix:
        decision.prefix = prefix
    if re.search(
        r"(with[_ -]?header|include .{0,8}header|包含.{0,4}標頭)", task, re.IGNORECASE
    ):
        decision.with_header = True
    if re.search(r"(genes?|基因).{0,12}(rows?|列)", task, re.IGNORECASE):
        decision.genes_axis = "rows"
    elif re.search(r"(genes?|基因).{0,12}(columns?|cols?|欄)", task, re.IGNORECASE):
        decision.genes_axis = "columns"

    if decision.action == "query_context7":
        decision.library_name = documentation_library_for_task(task)
        decision.library_id = None
        decision.docs_query = task[:2_000]
    elif decision.action == "web_search":
        decision.web_query = task[:2_000]

    parsed_preferences = extract_preference_proposals(task)
    if parsed_preferences:
        existing = {proposal.key for proposal in decision.preference_updates}
        decision.preference_updates.extend(
            proposal for proposal in parsed_preferences if proposal.key not in existing
        )

    if decision.action in REQUIRED_INPUTS:
        decision.missing_inputs = [
            field_name
            for field_name in REQUIRED_INPUTS[decision.action]
            if not getattr(decision, field_name, None)
        ]
    decision.should_execute = decision.action != "no_tool"
    return decision
