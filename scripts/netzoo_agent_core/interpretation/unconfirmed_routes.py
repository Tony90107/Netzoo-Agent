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

import re
from functools import lru_cache

from ..capability_sheet import produced_text, sheet_entries

__all__ = ["UNCONFIRMED_KIND", "checked_body_result", "checked_no_result", "confirms_nothing", "unconfirmed_actions",
           "unconfirmed_reply", "unconfirmed_result"]

UNCONFIRMED_KIND = "capability_unconfirmed"
_NOT_INSPECTED = "No files were inspected and no analysis ran."


@lru_cache(maxsize=1)
def _workflow_names() -> re.Pattern:
    """The registered workflow names and their parts (LIONESS, PANDA, ...), as whole words."""
    parts = {part for item in sheet_entries().values() if item.workflow for part in item.workflow.split("-")}
    return re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, parts), key=len, reverse=True)) + r")\b", re.I)


def checked_no_result(check) -> bool:
    """The check's own model read the request and found no result in it (Log 404).

    Nothing routing matched was then checked against anything: heldout11 VN5q ("Is there a
    method that models how each TF-gene edge ... depends on the edges at the previous time
    point?") was read as a question about methods and four TF-network workflows were said to
    "all fit"; VT2's "each gene should be allowed to sit in several communities" was read as
    a constraint and CONDOR "fits that result". A question about how a named registered
    workflow works is answered by that workflow's own description, so it is not counted.
    """
    if check is None or check.unconfirmed() or check.full_gap or check.results():
        return False
    return not any(_workflow_names().search(item.quote) for item in check.requirements if item.kind == "about_methods")


def confirms_nothing(check) -> bool:
    """No workflow routing matched was confirmed: the check did not run, only the backup read it, or it read no result."""
    return check is not None and (check.unconfirmed() or checked_no_result(check))


def unconfirmed_actions(decision, policy) -> list[str]:
    """Routing's candidates, in its order, when the check confirmed nothing; else []."""
    check = decision.capability_check
    if decision.action != "no_tool" or not confirms_nothing(check) or check.full_gap:
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


_produces = produced_text


def unconfirmed_reply(decision, policy) -> str | None:
    actions = unconfirmed_actions(decision, policy)
    if not actions:
        return None
    no_result = checked_no_result(decision.capability_check)
    lines = [("Routing matched these registered workflows to your words, but the capability check found no result "
              "in your request to check them against, so none is confirmed to give what you asked for:")
             if no_result else
             ("Routing matched these registered workflows to your words, but the capability check did not "
              "confirm that any of them gives what you asked for:")]
    for action in actions:
        produces = _produces(action)
        lines.append(f"- **{policy.workflows[action].workflow}**" + (f" — produces: {produces}" if produces else ""))
    return "\n\n".join([
        "\n".join(lines),
        ("Compare what each produces with what you asked for, or describe the result you want from your data "
         "and it is checked against what each workflow produces.") if no_result else
        ("Compare what each produces with what you asked for. Ask again to re-run the check, or say which "
         "result you want and from which workflow."),
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


def checked_body_result(context, state, reply) -> dict | None:
    """The reply body the check's verdicts decide on their own, else None (Log 403).

    A request routing could not map to any registered result comes first (part D,
    `unmapped_routes`); then a turn the check confirmed nothing for.
    """
    from .unmapped_routes import unmapped_result

    return unmapped_result(context, state, reply) or unconfirmed_result(context, state, reply)
