"""The hybrid gates' calls on the live path (options-first decision, 2026-10-18, step 7).

After `decide_core` makes a DO, `apply_hybrid_gates` reads the request once against the offered workflows' limits
and requirements (the study-purpose model, gpt-4o-mini; strict schema `menu_focus.gate_model`), checks any
requirement against those workflows' contracts (`menu_requirements`, verified clauses only), and lets
`interpretation.hybrid_gates.gated_core` change the call. Every call is priced against the turn's budget first and
recorded in its usage; a call that cannot be made or fails leaves the live call as it was (the gates never hold a
turn on their own failure). Set NETZOO_HYBRID_GATES=0 to turn them off.
"""

from __future__ import annotations

import os
import time

from ..contracts import HumanMessage, SystemMessage
from ..interpretation.hybrid_gates import gate_reading, gated_core
from ..interpretation.menu_decision import workflow_gate
from ..interpretation.menu_focus import focus_text, gate_model
from ..interpretation.menu_requirements import apply_verdicts, requirement_model, requirement_pairs, requirement_text
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..method_names import registered_workflows
from .context import preflight_budget, record_event
from .structured_calls import _serialized_structured_input

__all__ = ["apply_hybrid_gates"]

_GATE_SHAPE = (
    "Return only the GateReading for the user's request. The workflows below are the ones about to be offered. For "
    "each listed control, count, kind of data and data condition, give what the user's words say about it: stated "
    "(the value the words give), unsure (the user does not know, or gives several possibilities: values), or "
    "not_mentioned; list each setting the user asks to run with that no listed control is, and each requirement the "
    "user puts on the result, typed. Every quote is the user's exact words, copied from the request."
)
_REQUIREMENT_SHAPE = (
    "Return only the RequirementVerdicts structure. Each numbered pair gives a requirement from the user's request "
    "and one registered workflow, whose contract is listed. For each pair, copy the clause of that workflow's "
    "contract that speaks to the requirement, in its exact words (empty when none does), then say whether the "
    "contract says the workflow's result meets the requirement, contradicts it, or does not address it."
)


def _call(context, state, role, model, llm, messages, schema, usage, warnings):
    input_text = _serialized_structured_input(messages, schema)
    call_state = dict(state, token_usage=usage.model_dump(), budget_warnings=warnings)
    budget, warnings = preflight_budget(context, call_state, role=role, model=model, input_text=input_text,
                                        reserved_output_tokens=context.router_max_tokens, allow_reserve=False)
    if budget.status == "blocked":
        return None, usage, warnings, "blocked"
    started_ns, raw, data, output_text, status = time.monotonic_ns(), None, None, "", "failed"
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
        schema.model_validate(data)
        output_text, status = str(data), "success"
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "core.hybrid_gate_failed", "classify",
                     {"role": role, "error_type": type(error).__name__, "error_message": str(error)[:500]})
        data = None
    usage = append_llm_usage(usage, role=role, model=model, response=raw, input_text=input_text,
                             output_text=output_text, budget_tokens=context.task_token_budget,
                             duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000), status=status,
                             price_catalog=context.price_catalog)
    return data, usage, warnings, status


def apply_hybrid_gates(context, state, decision, core, user_task: str, usage, warnings):
    """(core, usage, warnings): the live DO judged by the hard gates; anything else is returned as it came."""
    if core.kind != "DO" or os.environ.get("NETZOO_HYBRID_GATES", "1") == "0":
        return core, usage, warnings
    known = registered_workflows()
    workflows = tuple(name for name in core.workflows if name in known)
    llm, model = getattr(context, "study_purpose_llm", None), getattr(context, "semantic_model_name", None)
    if not workflows or llm is None or usage.budget_exhausted:
        return core, usage, warnings
    messages = [SystemMessage(content=f"{_GATE_SHAPE}\n\n{focus_text(workflows)}"),
                HumanMessage(content=f"Request:\n{user_task}")]
    data, usage, warnings, status = _call(context, state, "hybrid_gate", model, llm, messages,
                                          gate_model(workflows), usage, warnings)
    if data is None:
        record_event(context, state, "core.hybrid_gate", "classify", {"status": status, "workflows": list(workflows)})
        return core, usage, warnings
    reading = gate_reading(data, user_task, workflows)
    pairs = requirement_pairs(reading, workflows)
    if pairs:
        messages = [SystemMessage(content=_REQUIREMENT_SHAPE), HumanMessage(content=requirement_text(user_task, pairs))]
        verdicts_payload, usage, warnings, _status = _call(context, state, "hybrid_requirement_check", model, llm,
                                                           messages, requirement_model(len(pairs)), usage, warnings)
        if verdicts_payload is not None:
            reading, _report = apply_verdicts(reading, pairs, verdicts_payload)
    verdicts = {name: workflow_gate(reading, name, user_task) for name in workflows}
    gated = gated_core(core, verdicts)
    record_event(context, state, "core.hybrid_gate", "classify", {
        "status": "checked", "workflows": list(workflows), "kind_before": core.kind, "kind_after": gated.kind,
        "verdicts": {name: {"reasons": v.reasons, "must_ask": v.must_ask, "unconfirmed": v.unconfirmed}
                     for name, v in verdicts.items()},
        "reading": reading.model_dump(mode="json", exclude_defaults=True)})
    return gated, usage, warnings
