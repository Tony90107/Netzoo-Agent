"""One verdict per requirement decides which workflow the reply offers (Logs 405, 409).

Routing and the capability check read the request independently. Until Log 409 the
check wrote only the "What I understood" lines, and the body, the card and the next
step followed routing, so the two could name different workflows for the same words.

Log 405 (heldout12 b12 KP2, 6 of 6): routing fell back to BONOBO for "a p-value for
each edge" while the check credited DRAGON; the reply said "available from DRAGON"
above "Fallback recommendation: BONOBO". Across n11 and b12 every turn where routing
made no claim and a confirmed check credited one workflow for every result had the
check right (12 of 12), so that workflow became the match.

Log 409 widens the same rule to every conflict, using the five labelled rounds (856
sessions). Where routing's exact match or tie and the check's credit named disjoint
workflows, the check was right 17 times and routing 2 (recent arms: 7 to 0). Examples:
- heldout15 PS1/PS3 "per-patient TF targeting scores": "available from LIONESS-PANDA",
  "Selected path: GIRAFFE".
- MX6: PANDA, then GIRAFFE.
The results the check found unavailable no longer block the rule (MX2: a per-sample
two-layer network credited to LIONESS-DRAGON beside per-sample p-values nothing
gives, under "Fallback recommendation: DRAGON"); they stay reported as unavailable.

Routing's offer stands when:
- it is the upstream step of a credited workflow, or the reverse (heldout11 VM4s:
  "modules" from expression is PANDA, then CONDOR);
- the user named the workflow;
- the two share any workflow;
- the check credited more than one workflow for the results.

Routing's typed reading of the result goes with its match. When the adopted workflow
does not produce that reading, the reading is dropped, so the reply describes what
the workflow produces instead. Before, heldout15 PS1-1 (already under Log 405) said
"Your question asks for a cohort-level TF activity matrix. **LIONESS-PANDA** fits
that result and scale."
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES

from ..capability_sheet import entry
from ..routing.capability_compatibility import _supported_artifacts
from .unmapped_routes import is_unmapped

__all__ = ["CHECK_MATCH_BASIS", "checked_match", "credited_workflows"]

CHECK_MATCH_BASIS = "capability_check"
_CLAIMS = ("exact", "ambiguous")
# How routing reached its match; a workflow the user named, or an earlier turn confirmed, is not overruled.
_USER_CHOSEN = ("workflow_name", "confirmed_context")


def credited_workflows(check) -> list[str] | None:
    """The workflows that deliver every result the check found available, in the first one's order.

    None when no result was found available, or one was read two ways (`partial`) or with
    no delivering entry; results found unavailable are left out (they stay gaps).
    """
    common = None
    for item in check.results():
        if item.status == "not_available":
            continue
        if item.status not in ("available", "with_step") or not item.delivered_by:
            return None
        actions = list(dict.fromkeys(entry(key).action for key in item.delivered_by if entry(key).action))
        common = actions if common is None else [action for action in common if action in actions]
    return common


def _offered(decision) -> set[str]:
    advice = decision.advisory_recommendation
    return {*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions,
            *([advice.action] if advice is not None else [])}


def _chained(one: str, other: str) -> bool:
    """Whether one workflow's output is the other's registered input (a two-step answer)."""
    return any(target in (capability.handoff_targets if (capability := OUTPUT_CAPABILITIES.get(source)) else ())
               for source, target in ((one, other), (other, one)))


def _produces_readings(action: str, decision) -> bool:
    """Whether the workflow produces every typed reading routing gave the result, at its scale."""
    capability = OUTPUT_CAPABILITIES.get(action)
    readings = [*([decision.requested_outcome] if decision.requested_outcome is not None else []),
                *(item.outcome for item in decision.outcome_hypotheses)]
    return all(capability is not None and outcome.artifact_type in _supported_artifacts(capability) and (
        outcome.granularity not in ("aggregate", "sample_specific") or outcome.granularity in capability.granularities)
               for outcome in readings)


def checked_match(decision, workflows) -> object:
    """The decision with the check's single credited workflow as its match, or the decision unchanged."""
    check = decision.capability_check
    if (decision.action != "no_tool" or check is None or check.unconfirmed() or check.full_gap or check.unchecked
            or decision.stated_hypotheses or is_unmapped(decision) or decision.match_basis in _USER_CHOSEN):
        return decision
    rejected = {item.action for item in decision.rejected_methods}
    common = [action for action in credited_workflows(check) or [] if action in workflows and action not in rejected]
    if len(common) != 1:
        return decision
    action = common[0]
    offered = _offered(decision)
    adopted = decision.match_basis == CHECK_MATCH_BASIS and decision.matched_actions == [action]  # idempotent
    if not adopted and decision.capability_match_status in _CLAIMS and (
            action in offered or any(_chained(action, other) for other in offered)):
        return decision
    reading = {} if _produces_readings(action, decision) else {
        "requested_outcome": None, "outcome_hypotheses": []}
    matched = decision.model_copy(update={
        "matched_actions": [action], "recommended_actions": [action], "hypothesis_actions": [],
        "alternative_actions": [], "advisory_recommendation": None, "clarification_question": None,
        "capability_match_status": "exact", "match_basis": CHECK_MATCH_BASIS, **reading,
        "reason": (f"The capability check credited {workflows[action].workflow} for every result the request asks "
                   "for that a registered workflow gives."),
    })
    return decision if matched == decision else matched
