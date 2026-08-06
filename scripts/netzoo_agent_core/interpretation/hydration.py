"""Hydrate compact router output into the complete task decision."""

from __future__ import annotations

import re

from workflow_registry import REQUIRED_INPUTS

from ..contracts import RouterDecision, TaskDecision
from ..routing import _extract_named_path
from .extraction import (
    _task_path,
    documentation_library_for_task,
    extract_preference_proposals,
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
        decision = TaskDecision(
            action=route.action,
            in_scope=route.in_scope,
            should_execute=route.action != "no_tool",
            intent_type=route.intent_type,
            confidence=route.confidence,
            reason=route.reason,
            recommended_actions=route.recommended_actions,
        )

    for field_name in (
        "expression_file",
        "motif_file",
        "ppi_file",
        "mirna_file",
        "output_file",
        "lioness_output",
        "network_file",
        "output_dir",
    ):
        parsed = _task_path(task, field_name)
        if parsed:
            setattr(decision, field_name, parsed)

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
