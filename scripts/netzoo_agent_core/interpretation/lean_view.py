"""The reply for a lean-decider call (2026-11-20): ASK, DECLINE and EXPLAIN from the call itself; DO by the plan.

`classify_lean` (graph/lean_call.py) keeps what the reply needs in `core.evidence["lean"]`: the question, the reply
line, the EXPLAIN answer (written by the second call from the contracts only) and a DO's plan notes.
"""

from __future__ import annotations

__all__ = ["DECLINE_KIND", "lean_view", "with_lean_notes"]

DECLINE_KIND = "decline"  # core_views.DECLINE_KIND; core_views imports this module, so it is not imported back


def _lean(core) -> dict:
    return (core.evidence or {}).get("lean") or {}


def lean_view(core, reply) -> dict | None:
    """The whole reply for a lean ASK, DECLINE or EXPLAIN; None for DO (the plan renderers answer it)."""
    from .task_answers import EXHAUSTED_NOTE, exhausted

    found = _lean(core)
    text = (found.get("reply") or "").strip()
    if core.kind == "DO":
        return None
    if core.kind == "EXPLAIN":
        return reply(text, "lean_explain")
    if core.kind == "DECLINE":  # a verified refusal (R2, R3, R5); core_view answers the model's own
        return reply(core.declined[0].line if core.declined else text, DECLINE_KIND)
    question = (found.get("question") or "").strip()
    if question and question not in text:
        text = f"{text}\n\n{question}" if text else question
    if exhausted(core):  # harness repair P3: a third round is not asked
        text = f"{EXHAUSTED_NOTE}\n\nStill missing: {question or text}"
    return reply(text, "lean_ask")


def with_lean_notes(result: dict, state: dict, reply) -> dict:
    """A lean DO's reply with the plan details under it: settings applied from the request, defaults, file checks,
    and steps that run as separate requests."""
    core = (state.get("decision") or {}).get("core") or {}
    notes = ((core.get("evidence") or {}).get("lean") or {}).get("notes") or []
    if core.get("basis") != "lean" or core.get("kind") != "DO" or not notes or not result.get("messages"):
        return result
    content = str(result["messages"][-1].content).rstrip()
    content += "\n\nPlan details:\n" + "\n".join(f"- {note}" for note in notes)
    return {**reply(content, result.get("reply_kind") or ""),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}
