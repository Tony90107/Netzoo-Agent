"""When routing made no claim and the check credited one workflow for everything asked, it is the match (Log 405).

heldout12 b12 KP2 (both arms, 6 of 6): routing read "a p-value for each edge" only by
partial evidence and fell back to BONOBO, while the check credited DRAGON; the reply said
"available from DRAGON" above "Fallback recommendation: BONOBO ... not an exact semantic
match". BP1, BP6 and heldout11 VC7s: routing's output failed validation ("no workflow was
selected") under a check that credited CONDOR, SAMBAR or LIONESS-PANDA for every result.
Across the n11 and b12 recordings every such turn -- routing without an exact or tied
claim, a confirmed check crediting all results to one workflow -- had the check right
(12 of 12). Routing's own exact match or tie is never replaced here: when they conflict,
who is right varies (n11 VT1-2: routing right, the check wrong).
"""

from __future__ import annotations

from ..capability_sheet import entry
from .unmapped_routes import is_unmapped

__all__ = ["CHECK_MATCH_BASIS", "checked_match"]

CHECK_MATCH_BASIS = "capability_check"


def _common_workflow(check) -> list[str]:
    """The workflows that deliver every requested result, in the first result's order."""
    common = None
    for item in check.results():
        if item.status not in ("available", "with_step") or not item.delivered_by:
            return []
        actions = list(dict.fromkeys(entry(key).action for key in item.delivered_by if entry(key).action))
        common = actions if common is None else [action for action in common if action in actions]
    return common or []


def checked_match(decision, workflows) -> object:
    """The decision with the check's single credited workflow as its match, or the decision unchanged."""
    check = decision.capability_check
    if (decision.action != "no_tool" or check is None or check.unconfirmed() or check.full_gap or check.unchecked
            or decision.capability_match_status in ("exact", "ambiguous") or decision.stated_hypotheses
            or is_unmapped(decision)):
        return decision
    common = [action for action in _common_workflow(check) if action in workflows]
    if len(common) != 1:
        return decision
    action = common[0]
    return decision.model_copy(update={
        "matched_actions": [action], "recommended_actions": [action], "hypothesis_actions": [],
        "alternative_actions": [], "advisory_recommendation": None, "clarification_question": None,
        "capability_match_status": "exact", "match_basis": CHECK_MATCH_BASIS,
        "reason": (f"The capability check credited {workflows[action].workflow} for every result the request asks "
                   "for; routing had no exact match."),
    })
