"""An open choice between registered methods that give different results, as goal evidence (CLARIFY)."""
from __future__ import annotations

import re

from workflow_registry import OUTPUT_CAPABILITIES, workflow_name

from ..method_names import registered_workflows, workflows_in


def source_granularity_choice(task: str) -> list[str]:
    """A current method choice cannot settle an unstated aggregate/per-sample result.

    Two registered methods joined by "or" in a current clause, giving the same kind of result at different scales,
    with no scale stated: the choice is the user's, even when a reader credits both workflows or omits the choice.
    It does not infer an output from input provenance, historical names, or a choice with a stated output scale.
    """
    from .request_integrity import _NEGATED, _scoped_clauses, granularity_left_open, granularity_mentions

    task = task.rsplit("User follow-up:", 1)[-1]
    scales = {item.granularity for item in granularity_mentions(task)}
    if len(scales) == 1 and not granularity_left_open(task):
        return []
    known = registered_workflows()
    for sentence in re.split(r"[。！？!?;；\n]|\.(?:\s|$)", task):
        for clause, scope in _scoped_clauses(sentence):
            names = [name for name in workflows_in(clause) if name in known]
            if scope != "current" or len(names) < 2 or not re.search(r"\bor\b", clause, re.I):
                continue
            if _NEGATED.search(clause[:clause.find(names[0])]):  # "not DRAGON or ..." rules a method out
                continue
            signatures = [OUTPUT_CAPABILITIES[known[name]] for name in names]
            if len({item.artifact_type for item in signatures}) == 1 and len({
                    item.granularities for item in signatures}) > 1:
                return names
    return []


def _considered(check, decision) -> set[str]:
    """The workflows this turn weighs for the request: routing's picks and the check's credits. Methods named only as
    where inputs came from ("Our inputs came from DRAGON or LIONESS-DRAGON ... Run CONDOR") are none of them."""
    from ..capability_sheet import entry

    if decision is None:
        return set()
    actions = {decision.action, *decision.matched_actions, *decision.hypothesis_actions,
               *decision.recommended_actions, *decision.alternative_actions}
    names = {workflow_name(action) for action in actions if action and action.startswith("run_")}
    return names | {entry(key).workflow for row in check.results() for key in row.delivered_by if entry(key)}


def method_choice(check, decision=None, task: str = "") -> list[str]:
    """Positive evidence of an open choice between different results, not a generic unmatched-row escape."""
    if check is None or check.unconfirmed():
        return []
    rows = check.results()
    if any(row.not_by or row.violations or row.limits and row.method.get("named") != "unregistered" for row in rows):
        return []
    if not check.full_gap and not any(row.status == "not_available" for row in rows):
        if (choices := source_granularity_choice(task)) and set(choices) <= _considered(check, decision):
            return choices
    if check.goal != "purpose_only" and any(row.status in ("available", "with_step", "partial", "needs_fact") for row in rows):
        return []  # a concrete result already read constrains the method choice
    # An unmatched result is vague only when the independent outcome reading agrees that its artifact is unknown.
    # Concrete off-menu outcomes (including L17, differential modularity and prediction) remain gaps.
    outcomes = [hypothesis.outcome for hypothesis in decision.outcome_hypotheses] if decision is not None else []
    unknown_result = bool(outcomes and all(outcome.artifact_type == "unknown" for outcome in outcomes))
    if check.goal == "result_named" and not unknown_result:
        return []
    choices = [check.goal_quote, *check.uncertain_quotes,
               *(row.method.get("named_quote", "") for row in rows)]
    known = registered_workflows()
    for quote in choices:
        names = [name for name in workflows_in(quote) if name in known]
        if len(names) < 2 or not re.search(r"\b(?:or|either|versus|vs)\b", quote, re.I):
            continue
        signatures = {(OUTPUT_CAPABILITIES[known[name]].artifact_type,
                       OUTPUT_CAPABILITIES[known[name]].granularities) for name in names}
        if len(signatures) > 1:
            return names
    return []
