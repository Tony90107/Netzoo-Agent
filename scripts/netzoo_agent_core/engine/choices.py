"""Turn a picked option of the last reply into the text its prompt accepts.

A card's options were derived from the same typed decision as the prompt, so
picking one needs no reply classifier: each maps to a string the machine
already handles -- a confirmed-outcome marker, a workflow continuation, a
follow-up restating the previous goal, or a command. Trust is checked here
again rather than assumed from the card: a workflow option must name a
workflow the previous turn itself offered.
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, RUN_ACTIONS

from ..contracts import ContextualReplyResolution, FollowUpContext
from ..contracts.state import NextTurnPrompt

__all__ = ["chosen_option", "confirmed_outcome_task", "follow_up_task", "selectable_options", "trusted_actions"]


def selectable_options(card: dict | None) -> list[dict]:
    """Options in display order: the question's first, then the next steps."""
    if not card:
        return []
    picks = list((card.get("choices") or {}).get("options") or [])
    return [
        option for option in (*picks, *(card.get("next_steps") or []))
        if option.get("available", True) and option.get("resolution") != "none"
    ]


def _normal(text: str) -> str:
    return " ".join(text.split()).casefold()


def chosen_option(card: dict | None, answer: str) -> dict | None:
    """The option an answer picks: its exact text, or its number in display order."""
    options = selectable_options(card)
    text = _normal(answer)
    if not options or not text:
        return None
    if text.isdigit():
        index = int(text) - 1
        return options[index] if 0 <= index < len(options) else None
    return next((option for option in options if option.get("answer") and _normal(option["answer"]) == text), None)


def trusted_actions(card: dict | None, prompt: NextTurnPrompt, context: FollowUpContext | None) -> set[str]:
    """Workflows the previous turn offered: its candidates, its continuation, its alternative."""
    trusted = {prompt.continuation_action, prompt.alternative_action}
    if context is not None:
        trusted.update(context.candidate_actions)
        trusted.update((context.continuation_action, context.alternative_action))
    # The card's question options come from the same decision's candidate lists
    # (ties, stated hypotheses, readings, alternatives), which the follow-up
    # context only partly carries. Next steps add nothing: each names the
    # prompt's own continuation or alternative, already counted above.
    choices = (card or {}).get("choices") or {}
    for option in choices.get("options") or []:
        if option.get("action"):
            trusted.add(option["action"])
    return {action for action in trusted if action in RUN_ACTIONS}


def confirmed_outcome_task(action: str, granularity: str | None = None) -> str:
    """The marker `resolve_next_turn_input` writes for a confirmed outcome."""
    capability = OUTPUT_CAPABILITIES.get(action)
    suffix = (
        f" CONFIRMED_GRANULARITY={granularity}."
        if granularity and capability is not None and granularity in capability.granularities
        else ""
    )
    return (
        f"CONFIRMED_OUTCOME_ACTION={action}.{suffix} "
        "Explain the confirmed supported outcome and recommend its workflow. "
        "Do not execute it yet."
    )


def follow_up_task(context: FollowUpContext | None, answer: str) -> str:
    """The follow-up form the reply resolver writes: the previous goal, then the reply."""
    if context is None:
        return answer
    return f"Previous NetZoo goal: {context.prior_user_goal}\nUser follow-up: {answer}"


def accepted(action: str) -> ContextualReplyResolution:
    return ContextualReplyResolution(
        kind="accept_workflow",
        selected_action=action,
        reason="The user chose this workflow from the offered options.",
    )
