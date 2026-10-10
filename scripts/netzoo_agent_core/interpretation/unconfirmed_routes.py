"""The reply when this turn's capability check confirmed nothing (Log 403).

Logs 394 and 401 kept routing's candidates when the check could not run or only
the backup model read the request, and said so in one note above the usual
reply. The usual reply then still presented them as the answer -- "These all
fit", "Selected path" -- and the simulated outage (o10) stayed at 31 of 54
dishonest replies with the note in place. Here the candidates are kept, so
nothing is refused for a provider failure, but they are listed as what routing
matched to the words, each with the result its executor writes, and none is
presented as fitting, selected or recommended.
"""

from __future__ import annotations

from ..capability_sheet import sheet_entries

__all__ = ["UNCONFIRMED_KIND", "unconfirmed_actions", "unconfirmed_reply", "unconfirmed_result"]

UNCONFIRMED_KIND = "capability_unconfirmed"
_NOT_INSPECTED = "No files were inspected and no analysis ran."


def unconfirmed_actions(decision, policy) -> list[str]:
    """Routing's candidates, in its order, when the check confirmed nothing; else []."""
    check = decision.capability_check
    if decision.action != "no_tool" or check is None or not check.unconfirmed() or check.full_gap:
        return []
    advice = decision.advisory_recommendation
    # The workflows the backup reading credited come first: they were read against the request.
    credited = [entry.action for item in check.results() for key in item.delivered_by
                if (entry := sheet_entries().get(key)) is not None]
    listed = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions,
              *([advice.action] if advice is not None else []),
              *(item.basis for item in decision.stated_hypotheses)]
    listed = [action for action in dict.fromkeys(listed) if action in policy.workflows]
    return [*[action for action in dict.fromkeys(credited) if action in listed],
            *[action for action in listed if action not in credited]]


def _produces(action: str) -> str:
    texts = [item.text for item in sheet_entries().values()
             if item.kind == "produces" and item.action == action and item.level == "direct"]
    return " ".join(texts[:2])


def unconfirmed_reply(decision, policy) -> str | None:
    actions = unconfirmed_actions(decision, policy)
    if not actions:
        return None
    lines = ["Routing matched these registered workflows to your words, but the capability check did not "
             "confirm that any of them gives what you asked for:"]
    for action in actions:
        produces = _produces(action)
        lines.append(f"- **{policy.workflows[action].workflow}**" + (f" — produces: {produces}" if produces else ""))
    return "\n\n".join([
        "\n".join(lines),
        "Compare what each produces with what you asked for. Ask again to re-run the check, or say which "
        "result you want and from which workflow.",
        _NOT_INSPECTED,
    ])


def unconfirmed_result(context, state, reply) -> dict | None:
    """The whole reply body when the check confirmed nothing and routing listed workflows, else None."""
    from ..contracts import TaskDecision

    if state.get("tool_results"):
        return None
    policy = getattr(context, "project_policy", None)
    if policy is None:
        return None
    text = unconfirmed_reply(TaskDecision.model_validate(state["decision"]), policy)
    return None if text is None else reply(text, UNCONFIRMED_KIND)
