"""The answer turn of an agent question (docs/research-log/agent-answer-anchor-2026-10-29).

Off by default: NETZOO_AGENT_ANSWERS=shadow records `core.agent_answer` only, =on applies it. When the task asked an
agent question (fact agent or Jev agent) whose quoted contract line code anchors (`interpretation.answer_anchor`), Jev
reads the user's reply against that line with the guard's frozen `judge_answer`, and the guard's `answered_core` turns
only a DO into DECLINE `jev_answer` on a confident `fails`. Any failure leaves the call as it came.
"""
from __future__ import annotations

import os

__all__ = ["agent_answer_mode", "apply_agent_answer", "asked_agent_question"]


def agent_answer_mode() -> str:
    mode = os.environ.get("NETZOO_AGENT_ANSWERS", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def asked_agent_question(task_state) -> dict | None:
    """The agent question this task asked with an anchored contract line: still pending, or answered this turn."""
    from ..interpretation.answer_anchor import anchored

    state = task_state or {}
    asked = [item for item in state.get("pending") or [] if item.get("status", "asked") == "asked"]
    asked += [item for item in state.get("facts") or [] if item.get("turn") == state.get("turns")]
    for item in asked:
        labels = item.get("labels") or {}
        if item.get("source") == "agent" and labels.get("contract"):
            workflow = anchored(labels["contract"], item.get("workflows") or [labels.get("workflow")])
            if workflow:
                return {**item, "labels": {**labels, "workflow": workflow}}
    return None


def apply_agent_answer(context, state, core, user_task: str):
    from ..llm import latest_user_message
    from .context import record_event
    from .jev_guard_call import answered_core, judge_answer

    mode = agent_answer_mode()
    question = asked_agent_question(state.get("task_state")) if mode != "off" and core.kind == "DO" else None
    if question is None:
        return core
    # Only the reply: a follow-up turn's message also carries the previous goal (live aa1: the line quoted it all).
    answer = latest_user_message(state.get("messages") or []).rsplit("User follow-up:", 1)[-1].strip()
    try:
        judged = judge_answer(question["labels"]["contract"], question.get("user_quote", ""),
                              question.get("question", ""), answer)
    except Exception as exc:  # noqa: BLE001 -- the call as it came, and says so
        judged = {"answer": f"not_run:{type(exc).__name__}", "confidence": 0.0}
    after, action = answered_core(core, question, answer, judged)
    record_event(context, state, "core.agent_answer", "classify", {
        "mode": mode, "action": action, "kind_before": core.kind, "basis_before": core.basis,
        "would_have": {"kind": after.kind, "basis": after.basis}, "judged": judged,
        "contract": question["labels"]["contract"], "workflow": question["labels"]["workflow"]})
    return after if mode == "on" else core
