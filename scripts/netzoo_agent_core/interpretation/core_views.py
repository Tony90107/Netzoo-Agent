"""Core decision spec, phase 3 (sections 4.3 and 7): the reply follows the turn's core call.

`core_view` is the one entry for every call that is not DO. CLARIFY, ASK, DECLINE and UNCHECKED are answered here
from the `CoreDecision`, before any other renderer can decide. DO keeps its renderers (a plan, a workflow's
guidance, a tie, a held run) as the details of one call. `ALLOWED` is the convergence check: `record_core_view`
marks a reply whose renderer is not one of its call's.

Round p1/p2 (2026-10-15/16): one DECLINE call was answered by five different renderers, one UNCHECKED call by
five, and a DO call once by "capability unconfirmed".
"""

from __future__ import annotations

__all__ = ["ALLOWED", "core_view", "decline_reply", "unchecked_reply"]

DECLINE_KIND = "decline"
UNCHECKED_KIND = "unchecked"
ALLOWED = {
    "CLARIFY": frozenset({"clarify_goal", "prep_concept"}),
    "ASK": frozenset({"ask_facts", "needs_fact", "prep_concept", "lean_ask"}),
    "EXPLAIN": frozenset({"lean_explain"}),
    "DECLINE": frozenset({DECLINE_KIND, "capability_check_gap", "prep_concept"}),
    "UNCHECKED": frozenset({UNCHECKED_KIND, "run_held", "capability_unconfirmed", "unresolved", "prep_concept"}),
    "DO": frozenset({
        "needs_input", "input_confirmation", "preference_confirmation", "plan_rejected", "execution",
        "verified_guidance", "scientific_guidance", "workflow_contract", "handoff_script", "outcome_clarification",
        "composition", "hypothesis_routes", "research_choices", "run_held", "capability_partial", "response_model",
        "retrieval_failure", "authority_report", "",
    }),
}
_CLOSING = "No files were inspected and no analysis ran."


def decline_reply(core, options: str = "") -> str:
    """DECLINE, from the call alone: each part that cannot be done as asked, why, and what can be done instead.
    `options`: the registered workflows that take the kind of data the request describes, said with a layer-2
    closing."""
    if core.basis in ("algorithm_boundary", "cobra_boundary"):
        return core.declined[0].line if core.declined else ""
    if core.basis in ("jev_answer", "jev_stated", "count_answer"):  # the user's own words and the contract line only
        return "\n\n".join(["\n".join(part.line for part in core.declined), _CLOSING])
    if core.basis == "contract_veto":  # hybrid spec 4: "cannot, because <contract words>", then the nearest options
        nearest = list(dict.fromkeys(w for part in core.declined for w in part.alternatives))
        tail = (f"The nearest options NetZoo can run: {', '.join(nearest)}." if nearest
                else "No registered workflow can do this as you asked.")
        return "\n\n".join(["\n".join(part.line for part in core.declined), tail, _CLOSING])
    lines = [f"{index}. {part.line or chr(34) + part.quote + chr(34) + ' -- not available here as asked.'}"
             for index, part in enumerate(core.declined, 1)]
    from .reason_layers import is_unmatched

    head = ["What I understood you are asking for:", *lines] if lines else [  # ROUND-21: no row says why
        "I couldn't match what you asked for to a result any registered NetZoo workflow produces."]
    many = len(core.declined) > 1
    # P2: a "no registered workflow" closing only when every part has a verified reason; else layer 2
    layer_two = not lines or any(is_unmatched(part.line) for part in core.declined)
    if layer_two:
        closing = (f"I couldn't match {'these' if many else 'this'} to a result any registered NetZoo workflow "
                   "produces, so none is offered." if lines else "So none is offered.")
    else:
        closing = f"No registered workflow can give {'these' if many else 'this'} as you asked, so none is offered as asked."
    return "\n\n".join(["\n".join(head), closing, *([options] if options and layer_two else []), _CLOSING])


def unchecked_reply(core) -> str:
    """UNCHECKED, from the call alone: the check could not confirm the turn, so nothing is selected or run."""
    named = (f" Workflows matched to your words, not confirmed: {', '.join(core.workflows)}."
             if core.workflows else "")
    return "\n\n".join([f"The capability check could not confirm this turn what a registered workflow gives you, so "
                        f"nothing was selected and nothing runs.{named}", "Ask again to re-run the check.", _CLOSING])


def _with_background(result: dict, core, reply) -> dict:
    """couldn't-match-2026-11-18: the refusal with its labelled general background, when the call recorded one."""
    from .general_background import with_background

    text = ((core.evidence or {}).get("general_background") or {}).get("text")
    if not text:
        return result
    content = with_background(str(result["messages"][-1].content), text, _CLOSING)
    return {**reply(content, result["reply_kind"]),
            **{key: value for key, value in result.items() if key not in ("messages", "reply_kind")}}


def core_view(context, state, reply) -> dict | None:
    """The whole reply for a CLARIFY, ASK, DECLINE or UNCHECKED call; None for DO (its renderers answer it)."""
    from ..contracts import TaskDecision
    from ..llm import latest_user_task
    from .ask_facts import ask_result
    from .capability_check import full_gap_result, needed_fact_reply, understanding_paragraph
    from .clarify_goal import clarify_result
    from .outside_steps import with_outside_steps
    from .run_hold import held_run_result
    from .unconfirmed_routes import unconfirmed_result

    if state.get("tool_results"):
        return None
    decision = TaskDecision.model_validate(state["decision"])
    task = latest_user_task(state.get("messages") or [])
    if decision.core is None:  # a decision made before the core call (older sessions, direct calls): only the
        from ..contracts.core_decision import CoreDecision, DeclinedPart  # text boundaries, which no longer reply
        from .core_decision import _boundary                               # on their own, still answer it

        if (found := _boundary(decision, task)) is None:
            return None
        core = CoreDecision(kind="DECLINE", basis=found[0], declined=[DeclinedPart(quote="", line=found[1])])
        return reply(decline_reply(core), DECLINE_KIND)
    core = decision.core
    if core.basis == "lean":  # the lean decider's call answers itself (2026-11-20)
        from .lean_view import lean_view

        if core.kind == "DECLINE" and not ((core.evidence or {}).get("lean") or {}).get("verified"):
            # The model's own refusal: the user's words and "not matched", never the model's reason (layer 2).
            return reply(decline_reply(core.model_copy(update={"basis": "lean_unverified"})), DECLINE_KIND)
        return lean_view(core, reply)
    if core.kind == "DO":
        return None
    from .prep_concepts import prep_concept_result

    # A question about a preparation step (SNAIL, SPONGE): no workflow gives it, so no call but DO can answer it.
    if (concept := prep_concept_result(task, reply)) is not None:
        return concept
    from .task_answers import EXHAUSTED_NOTE, exhausted, exhausted_body

    if core.kind in ("ASK", "CLARIFY") and exhausted(core):  # harness repair P3: a third round is not asked
        asking = reply

        def reply(content, kind):  # noqa: F811 -- the same reply, opened by the note
            return asking(f"{EXHAUSTED_NOTE}\n\n{exhausted_body(content) if core.kind == 'ASK' else content}", kind)
    if core.kind == "CLARIFY":
        return clarify_result(state, reply)
    if core.kind == "ASK":
        check = decision.capability_check
        if core.basis == "needs_fact" and check is not None and check.needed_facts():
            return reply(needed_fact_reply(check, understanding_paragraph(check) or ""), "needs_fact")
        return ask_result(state, reply)
    if core.kind == "DECLINE":
        if core.basis == "full_gap" and (gap := full_gap_result(state, reply)) is not None:
            return _with_background(gap, core, reply)
        from .reason_layers import nearest_or_options

        return _with_background(
            reply(with_outside_steps(decline_reply(core, nearest_or_options(decision)), decision, task), DECLINE_KIND),
            core, reply)
    if core.basis == "routing_failed":  # the system's own failure: never reported as an unclear question
        from .unresolved_router_fallback import render_unresolved_router_fallback

        return reply(render_unresolved_router_fallback(decision, task), "unresolved")
    if core.basis.startswith("run_held") and (held := held_run_result(state, reply, understanding_paragraph)):
        return held
    if core.basis == "check_unconfirmed" and (found := unconfirmed_result(context, state, reply)) is not None:
        return found
    return reply(unchecked_reply(core), UNCHECKED_KIND)
