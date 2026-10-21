"""ROUND-21 (R21-A, collab/ROUND-21-PLAN.md): a full gap no reason can be given for is read once more.

Replayed over the 757 labelled readings, a full-gap DECLINE that states a reason code can verify (ROUND-20) was right
85 times in 87; one that states none ("not matched to any registered workflow") was gold CLARIFY 24 times and gold
DECLINE 18 times (C22's filtered VCF ten times). The two groups carry the same typed fields -- both are blank readings,
nearly all `goal=result_named` -- and differ in whether the request names a result at all: "a network analysis",
"a systems-level view", "Which one should I run?" against "give me a filtered VCF".

So only such a gap is read again, in another shape (ExtractConf: one question over the whole request, not the check's
sentence-by-sentence entries), triggered by code (GraphRAG gleaning, Kamoi 2024). The model quotes the words saying
what the user wants and says whether they name a result; it is never asked whether the request is ambiguous (CLAMBER).
Code keeps the answer only when the quoted words are in the request, and then the turn is CLARIFY. Any other answer,
or none, leaves the DECLINE as it was. A guard that kept words naming one registered workflow declined (added for the
unlabelled ve-m3 N21, "Can PUMA convert its signed edge weights into experimentally proven ... labels") was removed
after the live check: gold-CLARIFY M33, "What could GIRAFFE tell me about our T-cell exhaustion time course? ... I'm not
sure what question to put to it", was read correctly and then declined by it.
"""

from __future__ import annotations

from ..contracts.capability_check import CapabilityCheck, GoalRead
from .request_spans import _span

__all__ = ["GOAL_READ_INSTRUCTIONS", "needs_goal_read", "with_goal_read"]

GOAL_READ_INSTRUCTIONS = (
    "Return only the GoalRead structure. You are given a user's request to an assistant that runs registered "
    "bioinformatics network workflows. Copy the words of the request that say what the user wants from the analysis, "
    "then say whether those words name a particular result."
)


def needs_goal_read(check: CapabilityCheck | None, decision=None, task: str = "") -> bool:
    """A full gap whose results all say only that they matched no registered workflow, on a confirmed check whose
    goal is not already unclear and whose fact agent asks nothing (CLARIFY and ASK come first)."""
    if check is None or not check.full_gap or check.unconfirmed() or check.open_goal_quote:
        return False
    agent = getattr(decision, "fact_check", None)
    if agent is not None and agent.status == "checked" and (agent.accepted or agent.open_results):
        return False
    from .capability_check import _why_not
    from .core_decision import goal_unclear

    if goal_unclear(check, decision, task):
        return False
    return not any(_why_not(item, check) for item in check.results())


def with_goal_read(check: CapabilityCheck, task: str, read: GoalRead | None) -> CapabilityCheck:
    """The check with the request's words for an open goal when the read says they name no result."""
    words = (read.asked_words or "").strip() if read is not None else ""
    if read is None or read.result != "names_no_result" or not words or (span := _span(task, words)) is None:
        return check
    return check.model_copy(update={"open_goal_quote": task[span[0]:span[1]]})
