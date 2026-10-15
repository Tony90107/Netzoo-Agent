"""Core decision spec, phase 2: the replies for the fact agent's facts (section 6).

An ASK call is the whole turn: each kept question, what each answer leads to, and the contract words that make it
decide; nothing is selected or run before the answer. A fact the workflow's own input check settles (R5) is never
asked: a DO reply says the check will settle it before anything runs.
"""

from __future__ import annotations

__all__ = ["ASK_KIND", "ask_result", "with_settled_notes"]

ASK_KIND = "ask_facts"


def _lead(outcome: str, workflow: str) -> str:
    if outcome == "supported":
        return f"{workflow} can do what you asked"
    if outcome.startswith("other_workflow:"):
        return f"{outcome.split(':', 1)[1]} does it instead of {workflow}"
    return "no registered workflow does it as you asked"


def ask_reply(core) -> str:
    asked = [fact for fact in core.facts if not fact.settled_by_input_check]
    lines = []
    for fact in asked:
        workflow = fact.workflows[0] if fact.workflows else "the workflow"
        lines.append(f"- {fact.question}\n  If yes: {_lead(fact.if_yes, workflow)}. If no: {_lead(fact.if_no, workflow)}. "
                     f"(You wrote: \"{fact.user_quote.rstrip('. ')}\". {workflow}'s contract: "
                     f"\"{fact.contract_quote.rstrip('. ')}\".)")
    return "\n\n".join([
        "Before I choose a workflow, please tell me:\n" + "\n".join(lines),
        "No workflow has been selected and nothing runs before you answer.\n\nNo files were inspected and no "
        "analysis ran.",
    ])


def ask_result(state, reply) -> dict | None:
    """The whole reply when the turn's core call is the fact agent's ASK, else None."""
    from ..contracts import TaskDecision

    core = TaskDecision.model_validate(state["decision"]).core
    if core is None or core.kind != "ASK" or core.basis != "fact_agent":
        return None
    return reply(ask_reply(core), ASK_KIND)


def with_settled_notes(result: dict, state, reply) -> dict:
    """R5: the facts a DO turn's input check will settle, said after the reply (never asked)."""
    from ..contracts import TaskDecision

    core = TaskDecision.model_validate(state["decision"]).core
    settled = [fact for fact in (core.facts if core is not None and core.kind == "DO" else [])
               if fact.settled_by_input_check]
    if not settled or not result.get("messages"):
        return result
    notes = "\n".join(f"- You wrote \"{fact.user_quote}\". Before it runs, "
                      f"{fact.workflows[0] if fact.workflows else 'the workflow'}'s input check verifies this from "
                      f"your files: \"{fact.contract_quote}\"; if they do not meet it, nothing runs." for fact in settled)
    text = f"{result['messages'][-1].content}\n\nChecked from your files before anything runs:\n{notes}"
    return {**reply(text, result["reply_kind"]),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}
