"""Core decision spec, phase 2: the replies for the fact agent's facts (section 6).

An ASK call is the whole turn: each kept question, with the user's words and the contract words that make it
decide (open item 1: not what each answer leads to); nothing is selected or run before the answer. A fact the
workflow's own input check could settle is asked too (ROUND-21, user decision: R5 withdrawn).
"""

from __future__ import annotations

__all__ = ["ASK_KIND", "CONFIRM_ASKING", "CONFIRM_PLACED", "CONFIRM_UNPLACED", "REASK", "YES_OR_NO", "ask_result",
           "contract_clause"]

ASK_KIND = "ask_facts"

# The guard's data confirm (graph.jev_guard_call): the words its questions are built from, kept here so an exhausted
# reply (task_answers.exhausted_body) lists the same question as a missing confirmation, never asks it a third time.
CONFIRM_PLACED = "Before I go ahead, could you confirm this about your data?"
CONFIRM_UNPLACED = "Before I go ahead, please confirm: "
YES_OR_NO = " (yes or no)"
REASK = "I need a yes or no to go on: "
CONFIRM_ASKING = ((REASK, ""), (YES_OR_NO, ""), (CONFIRM_PLACED, "A confirmation about your data."),
                  (CONFIRM_UNPLACED, "A confirmation: "))


def contract_clause(workflow: str, line: str) -> str:
    """How a reply says a contract line: prose in quotes; a typed field from the guard's data rule as a plain sentence
    (j4 S32: "SAMBAR incompatible_input_artifacts: expression_matrix" read as code)."""
    line = line.rstrip(". ")
    for field, sentence in ((" incompatible_input_artifacts: ", "lists {} among the inputs it cannot take"),
                            (" input_artifacts: ", "takes only {} as input")):
        name, found, value = line.partition(field)
        if found and name == workflow:
            return f"{workflow}'s contract {sentence.format(value)}"
    return f"{workflow}'s contract: \"{line}\""


def ask_reply(core) -> str:
    """Each kept question with the user's words and the contract's words that make it matter.

    Open item 1 (2026-10-16, spec change log): what a yes or a no leads to is not said. The agent writes those
    outcomes and code cannot check their direction in general (p2b C06 "If no: PUMA does it instead", C36 "If no:
    no registered workflow"; p2 C31 had the yes-branch inverted). They stay on the fact for R3 and the trace.
    """
    lines = []
    for fact in core.facts:
        if fact.by_code:  # phase 5b: each candidate count was judged in code, so what it leads to is said
            from .count_alternatives import count_outcome_lines

            lines.append(f"- {fact.question}\n  You wrote: \"{fact.user_quote.rstrip('. ')}\".\n"
                         + "\n".join(f"  - {line}" for line in count_outcome_lines(fact.outcomes, fact.notes)))
            continue
        workflow = fact.workflows[0] if fact.workflows else "the workflow"
        contract = (f" {contract_clause(workflow, fact.contract_quote)}." if fact.contract_quote
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
                                                                "contract_veto_fact", "jev_fact", "jev_link", "jev_condition"):
        return None
    return reply(ask_reply(core), ASK_KIND)

