"""Core decision spec, phase 2: the replies for the fact agent's facts (section 6).

An ASK call is the whole turn: each kept question, with the user's words and the contract words that make it
decide (open item 1: not what each answer leads to); nothing is selected or run before the answer. A fact the workflow's own input check settles (R5) is never
asked: a DO reply says the check will settle it before anything runs.
"""

from __future__ import annotations

__all__ = ["ASK_KIND", "ask_result", "with_settled_notes"]

ASK_KIND = "ask_facts"


def ask_reply(core) -> str:
    """Each kept question with the user's words and the contract's words that make it matter.

    Open item 1 (2026-10-16, spec change log): what a yes or a no leads to is not said. The agent writes those
    outcomes and code cannot check their direction in general (p2b C06 "If no: PUMA does it instead", C36 "If no:
    no registered workflow"; p2 C31 had the yes-branch inverted). They stay on the fact for R3 and the trace.
    """
    asked = [fact for fact in core.facts if not fact.settled_by_input_check]
    lines = []
    for fact in asked:
        if fact.by_code:  # phase 5b: each candidate count was judged in code, so what it leads to is said
            from .count_alternatives import count_outcome_lines

            lines.append(f"- {fact.question}\n  You wrote: \"{fact.user_quote.rstrip('. ')}\".\n"
                         + "\n".join(f"  - {line}" for line in count_outcome_lines(fact.outcomes, fact.notes)))
            continue
        workflow = fact.workflows[0] if fact.workflows else "the workflow"
        contract = (f" {workflow}'s contract: \"{fact.contract_quote.rstrip('. ')}\"." if fact.contract_quote
                    else "")  # the hybrid gate's requirement questions quote no clause: none addresses it
        wrote = f"\n  You wrote: \"{fact.user_quote.rstrip('. ')}\"." if fact.user_quote else ""  # core data: none said
        lines.append(f"- {fact.question}{wrote}{contract}" if wrote or contract else f"- {fact.question}")
    return "\n\n".join([
        "Before I choose a workflow, please tell me:\n" + "\n".join(lines),
        "No workflow has been selected and nothing runs before you answer.\n\nNo files were inspected and no "
        "analysis ran.",
    ])


def ask_result(state, reply) -> dict | None:
    """The whole reply when the turn's core call is the fact agent's ASK, else None."""
    from ..contracts import TaskDecision

    core = TaskDecision.model_validate(state["decision"]).core
    if core is None or core.kind != "ASK" or core.basis not in ("fact_agent", "count_fact", "hybrid_requirement",
                                                                "contract_veto_fact"):
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
