"""Verdict layer items 1-2 (2026-10-14): a run the capability check did not approve is held, said and offered.

The engineering review of 923e493 reproduced two runs that went ahead against the check's own verdict: a run of a
workflow the check credited nothing to (`other_workflow`), and a run of a workflow that gives only part of what was
asked (`partial_gap`). Since 3578b00 only a full gap stopped a run. Now every verdict that does not approve a run holds
it: nothing is planned, the reply says what the run would and would not give, and the run -- or, when the user did
not name it, the workflow the check credits -- is offered for the user to confirm. A pick continues as a selected
workflow: planned and previewed, never run unasked. A part of the task is never run in place of the whole
(user decision 2026-10-14).
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS

from ..contracts import TaskDecision
from ..contracts.capability_check import RunVerdict

__all__ = ["HELD_KIND", "held_offers", "held_run_reply", "held_run_result", "hold_run"]

HELD_KIND = "run_held"
_CLOSING = "No files were inspected and no analysis ran."
_MAX_OFFERS = 3
_PREVIEW = "I will then find your input files and show a preview; nothing runs until you approve it."


def _name(action: str) -> str:
    return ACTION_DEFINITIONS[action].workflow


def _names(names: list[str], word: str = "or") -> str:
    names = list(dict.fromkeys(names))
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" {word} " + names[-1]


def _quotes(rows: list[dict]) -> str:
    return _names([f'"{row["quote"]}"' for row in rows], "and") if rows else "what you asked for"


def held_offers(verdict: RunVerdict) -> list[str]:
    """The workflows the held reply offers to plan, in order.

    The run itself, except when the check credits another workflow: then that workflow, and the run too only when the
    user named it (the conflict is said, the named workflow is never replaced unasked).
    """
    if verdict.verdict != "other_workflow":
        return [verdict.action]
    credited = verdict.credited or [action for row in verdict.results for action in row["credited"]]
    others = [action for action in dict.fromkeys(credited) if action in RUN_ACTIONS and action != verdict.action]
    return [*others[:_MAX_OFFERS - 1], verdict.action] if verdict.named else others[:_MAX_OFFERS]


def hold_run(decision: TaskDecision, verdict: RunVerdict) -> TaskDecision:
    """The run turned into a reply that offers it: nothing selected, nothing planned."""
    offers = held_offers(verdict)
    return decision.model_copy(update={
        "action": "no_tool", "should_execute": False, "intent_type": "answer_question", "execution_requested": True,
        "run_verdict": verdict.model_copy(update={"held": True}),
        "matched_actions": [], "hypothesis_actions": [], "alternative_actions": [], "recommended_actions": offers,
        "advisory_recommendation": None, "clarification_question": None,
        "reason": f"The run of {_name(verdict.action)} was not planned: the capability check did not approve it "
                  f"({verdict.verdict}).",
    })


def _why(verdict: RunVerdict, offers: list[str]) -> str:
    name, rows = _name(verdict.action), verdict.results
    others = [_name(action) for action in offers if action != verdict.action]
    gaps = [row for row in rows if row["status"] == "not_available"]
    if verdict.verdict == "other_workflow":
        missed = [row for row in rows if row["status"] != "not_available" and verdict.action not in row["credited"]]
        if verdict.named:
            does = "does" if len(others) == 1 else "do"
            source = f"; {_names(others)} {does}" if others else ""
            return (f"You asked me to run {name}, but {name} does not cover {_quotes(missed)}{source}. I have not "
                    f"planned {name}, and I have not put another workflow in its place.")
        gives = (f"{_names(others, 'and')} {'gives' if len(others) == 1 else 'give'} what you asked for"
                 if others else "No single registered workflow gives everything you asked for")
        rest = f", but no registered workflow covers {_quotes(gaps)}" if others and gaps else ""
        return f"You asked me to run this. {gives}{rest}, so I have not planned a run yet."
    if verdict.verdict == "partial_gap":
        given = [row for row in rows if row["status"] in ("available", "with_step")]
        parts = [row for row in rows if row["status"] == "partial"]
        what = f"It covers {_quotes(given)}" if given else "It covers part of what you asked for"
        rest = (f", but no registered workflow covers {_quotes(gaps)}" if gaps
                else f", but only part of {_quotes(parts)}")
        return (f"You asked me to run {name}. {what}{rest}, so the run would do only part of what you asked. "
                "I have not planned it.")
    if verdict.verdict == "outside_step":
        steps = [row for row in rows if row["status"] == "with_step"]
        return (f"You asked me to run {name}. {name} covers {_quotes(steps)} only with a step you run outside "
                "NetZoo afterwards (above), so the run alone would not do all of it. I have not planned it.")
    if verdict.verdict == "unread":
        return (f"You asked me to run {name}, but part of your request was not checked against what {name} gives "
                "(above). I have not planned the run.")
    return (f"You asked me to run {name}, but the capability check could not confirm this turn that {name} gives "
            "what you asked for. I have not planned the run.")


def _ask(verdict: RunVerdict, offers: list[str]) -> str:
    if not offers:
        return "Describe the result you want, and I will check it again."
    if len(offers) > 1:
        return f"Tell me which one to run, {_names([_name(action) for action in offers])}, and {_PREVIEW}"
    if offers == [verdict.action]:
        manner = " for the part it gives" if verdict.verdict in ("partial_gap", "outside_step") else " anyway"
        return f"Tell me to run {_name(verdict.action)}{manner}, and {_PREVIEW}"
    return f"Tell me to run {_name(offers[0])}, and {_PREVIEW}"


def held_run_reply(decision: TaskDecision, understood: str | None) -> str:
    """`understood`: what the check understood was asked for (`capability_check.understanding_paragraph`)."""
    verdict, offers = decision.run_verdict, list(decision.recommended_actions)
    return "\n\n".join(part for part in (understood, _why(verdict, offers), _ask(verdict, offers), _CLOSING) if part)


def held_run_result(state, reply, understanding) -> dict | None:
    """The whole reply when this turn's run was held, else None (called from `capability_check.whole_check_result`,
    which passes its `understanding_paragraph`)."""
    decision = TaskDecision.model_validate(state["decision"])
    if decision.action != "no_tool" or decision.run_verdict is None or not decision.run_verdict.held:
        return None
    check = decision.capability_check
    understood = understanding(check, offers_methods=False) if check is not None and not check.unavailable else None
    return reply(held_run_reply(decision, understood), HELD_KIND)
