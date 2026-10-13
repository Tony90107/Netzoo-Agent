"""Verdict layer step 1: a run the user asked for, tied between workflows, asks which one to run.

r17 (run17 = heldout17 as run commands) PL1, PQ1, PQ2: "Run the analysis now: build a cohort-wide TF-to-gene
network ..." tied PANDA and OTTER (both fit, per gold). The reply described each method and when to pick it, but
never asked which to run, and picking one on the card only explained it, so the run the user asked for was lost.
Here the reply closes with that question, and the card's options plan the picked workflow (`plan_workflow`).
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS

from ..contracts import TaskDecision
from ..reply_cards.contracts import MAX_OPTIONS

__all__ = ["run_choice_actions", "run_choice_line", "with_run_choice_reply"]

_WHOLE_TURN = {None, "execution", "needs_input", "input_confirmation", "preference_confirmation", "plan_rejected",
               "capability_check_gap"}
_CLOSING = "No files were inspected and no analysis ran."


def run_choice_actions(decision: TaskDecision) -> list[str]:
    """The tied workflows of a guidance turn whose user asked for a run, or [] when there is no such choice."""
    if decision.action != "no_tool" or not decision.execution_requested:
        return []
    if decision.capability_check is not None and decision.capability_check.full_gap:
        return []
    tied = [action for action in dict.fromkeys(decision.hypothesis_actions) if action in RUN_ACTIONS]
    return tied if 2 <= len(tied) <= MAX_OPTIONS else []


def _names(names: list[str]) -> str:
    return " and ".join(names) if len(names) == 2 else ", ".join(names[:-1]) + " and " + names[-1]


def run_choice_line(actions: list[str]) -> str:
    names = [ACTION_DEFINITIONS[action].workflow for action in actions]
    fit = "both fit" if len(names) == 2 else "all fit"
    return (f"You asked me to run this, and {_names(names)} {fit} it. Tell me which one to run; I will then find "
            "your input files and show a preview, and nothing runs until you approve it.")


def with_run_choice_reply(result: dict, state, reply) -> dict:
    """Close a tied reply to a run request with the question of which workflow to run."""
    decision = TaskDecision.model_validate(state["decision"])
    actions = run_choice_actions(decision)
    if not actions or result.get("reply_kind") in _WHOLE_TURN:
        return result
    text = str(result["messages"][-1].content).rstrip()
    line = run_choice_line(actions)
    if text.endswith(_CLOSING):
        text = f"{text[:-len(_CLOSING)].rstrip()}\n\n{line}\n\n{_CLOSING}"
    else:
        text = f"{text}\n\n{line}"
    return {**reply(text, result["reply_kind"]),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}
