"""A request routing could not map to any registered result is not a tie of every workflow (Log 403, part D).

The routing model names the asked-for result from a fixed vocabulary that has no
"none of these", so a request for a phylogenetic tree, a protein structure or gene
fusions is read as artifact `unknown`. The matcher reads `unknown` as "this
dimension does not constrain", so every workflow whose inputs are not contradicted
passed -- 11 to 13 of them -- and `research_choices` listed the whole registry when
it had none (Log 403 replay: 64 recorded replies named eight or more workflows for
such readings; 15 of them on turns the check could not confirm).

Here such a reading offers no workflow for the request as a whole. The capability
check, which reads the request itself, decides what is said: the parts it found a
workflow for are offered with that workflow, and nothing else is. Only a request
that asks for no result at all -- the check found only questions about the
methods, and it was confirmed -- keeps the listing, since "which methods are
there?" is answered by the list.
"""

from __future__ import annotations

from ..capability_sheet import entry, produced_text

__all__ = ["UNMAPPED_KIND", "credited_actions", "fully_credited", "is_unmapped", "offers_nothing", "unmapped_reply", "unmapped_result",
           "without_unmapped_candidates", "confirmed_partial_tie"]

UNMAPPED_KIND = "unmapped_request"
_NOT_INSPECTED = "No files were inspected and no analysis ran."


def is_unmapped(decision) -> bool:
    """Whether every routing reading of this no-tool turn left the result `unknown`.

    Only the typed-reading path counts: a workflow the user named, a confirmed earlier
    context or stated hypotheses decide candidates without the result vocabulary.
    """
    if decision.action != "no_tool" or decision.stated_hypotheses or decision.match_basis != "semantic":
        return False
    readings = [item.outcome for item in decision.outcome_hypotheses]
    if not readings and decision.requested_outcome is not None:
        readings = [decision.requested_outcome]
    return bool(readings) and all(outcome.artifact_type == "unknown" for outcome in readings)


def _asks_only_about_methods(check) -> bool:
    return (check is not None and not check.unconfirmed() and not check.results()
            and any(item.kind == "about_methods" for item in check.requirements))


def offers_nothing(decision) -> bool:
    """An `unknown` reading whose turn the check neither gapped nor read as a question about the methods."""
    check = decision.capability_check
    return is_unmapped(decision) and not (check is not None and check.full_gap) and not _asks_only_about_methods(check)


def without_unmapped_candidates(decision):
    """The decision without routing's unconstrained tie, so every reader sees the same (part D).

    Renderers, the study-purpose and outside-step notes, applicability and cards all read the
    candidate lists; the Log 403 replay found the purpose note still listing all 13 workflows
    under a reply that offered none.
    """
    if not offers_nothing(decision):
        return decision
    return decision.model_copy(update={"matched_actions": [], "hypothesis_actions": [], "recommended_actions": [],
                                       "alternative_actions": [], "advisory_recommendation": None})


def credited_actions(check, policy) -> list[tuple[str, str]]:
    """(workflow action, the request words) for each part the check found a workflow for."""
    found = []
    for item in check.results() if check is not None else []:
        if item.status not in ("available", "with_step", "partial"):
            continue
        for key in item.delivered_by:
            action = entry(key).action
            if action in policy.workflows and action not in {a for a, _ in found}:
                found.append((action, item.quote))
    return found


def fully_credited(check) -> bool:
    """The check confirmed every requested result, with no unchecked sentences."""
    return bool(check is not None and not check.unconfirmed() and not check.unchecked and check.results()
                and all(item.status in ("available", "with_step") and item.delivered_by for item in check.results()))


def confirmed_partial_tie(decision) -> bool:
    """A confirmed supported result beside a gap is not a choice of interchangeable outputs.

    A live run (tests/partial_tie_c10_decision.json): routing offered BONOBO's
    gene-gene p-values as an alternative to per-patient two-layer partial
    correlations, after the check correctly refused p-values for those
    two-layer networks. Report
    the confirmed parts without changing routing or selecting an execution.
    Explicit method comparisons and uncertain readings keep their own advice.
    """
    check = decision.capability_check
    if check is None:
        return False
    supported = {entry(key).action for item in check.results()
                 if item.status in ("available", "with_step") for key in item.delivered_by}
    refused = {entry(key).action for item in check.results()
               if item.status == "not_available" for key in item.not_by}
    return bool(decision.action == "no_tool" and not decision.should_execute
                and decision.capability_match_status == "ambiguous" and decision.match_basis == "semantic"
                and len(set(decision.hypothesis_actions)) > 1 and not decision.stated_hypotheses
                and not is_unmapped(decision) and not check.unconfirmed() and not check.unchecked
                and (supported & refused) - {None})


def unmapped_reply(decision, policy) -> str | None:
    # A turn without a check (a follow-up, or no check model configured) is read the same way:
    # an `unknown` reading still claims no workflow.
    check = decision.capability_check
    partial_tie = confirmed_partial_tie(decision)
    if not offers_nothing(decision) and not partial_tie:
        return None
    credited = credited_actions(check, policy)
    if credited:
        unconfirmed = " They were not confirmed." if check.unconfirmed() else ""  # credited implies a check
        lines = (["Only part of your request is supported. These workflows provide the confirmed part; "
                  "no registered workflow supplies the whole request:"] if partial_tie else
                 ["The capability check identified workflows for every result you asked for:"]
                 if fully_credited(check) else ["I could not tell which registered result your request as a whole asks for, so no workflow is "
                 "offered for all of it. These apply only to the part they were found for:" + unconfirmed]
                 )
        lines += [f'- **{policy.workflows[action].workflow}** — for "{words}"; produces: {produced_text(action)}'
                  for action, words in credited]
        closing = ("Ask about the supported part, or describe a different result for the unavailable part." if partial_tie else
                   "Choose a result to discuss with its workflow." if fully_credited(check) else
                   "Say which part to start with, or describe the rest as the result you want from your data.")
    else:
        lines = ["I could not tell which registered result you are asking for, so no workflow is offered for it."]
        if check is not None and check.unavailable:
            lines.append("The capability check could not run this turn either; asking again re-runs it.")
        closing = ("If a registered workflow should give part of it, describe that result from your data, and it "
                   "is checked against what the workflows produce.")
    return "\n\n".join(["\n".join(lines), closing, _NOT_INSPECTED])


def unmapped_result(context, state, reply) -> dict | None:
    from ..contracts import TaskDecision

    policy = getattr(context, "project_policy", None)
    if policy is None or state.get("tool_results"):
        return None
    decision = TaskDecision.model_validate(state["decision"])
    text = unmapped_reply(decision, policy)
    kind = "capability_partial" if confirmed_partial_tie(decision) else UNMAPPED_KIND
    return None if text is None else reply(text, kind)
