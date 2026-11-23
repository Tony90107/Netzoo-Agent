"""The lean decider in the graph (2026-11-20; user: replace the existing system with this lean version).

With NETZOO_LEAN_DECIDER=on, `classify_task` hands a request to `classify_lean`: one model call and the lean rules
(`netzoo_agent_core.lean`), turned into the decision the planner and the reply already read.

- DO: the first step's action. A preparation step first (SPONGE priors, normalization) carries the next analysis
  step as `then_action` (the plan shows it under "Then"); every other later step is said in the plan notes as its
  own later request. Settings the request
  gives (their words found in it) are set on the decision when the decision accepts them; the notes say which were
  not. A `contract_rules` run verdict for this request approves the run; the plan's file checks still decide whether
  it can start.
- ASK, DECLINE, EXPLAIN: no workflow is selected; `interpretation.lean_view` replies from the call.

The old path keeps what only it handles: /execute continuations, method comparisons, a picked choice card and a
recommended-workflow continuation. If the lean call fails, the old path answers the turn.
"""

from __future__ import annotations

import os
import time
from typing import Any, get_args, get_origin

__all__ = ["LEAN_FLAG", "classify_lean", "lean_applies", "lean_enabled"]

LEAN_FLAG = "NETZOO_LEAN_DECIDER"
_PREVIOUS_ACTION = "PREVIOUS_ACTION="  # cli/follow_up.py: a recommended workflow the user continues


def lean_enabled() -> bool:
    return os.environ.get(LEAN_FLAG, "").strip().lower() in {"1", "on", "true", "yes"}


def lean_applies(state: dict, task: str) -> bool:
    """The flag is on and the turn is not one only the old path handles."""
    from ..interpretation.nearest_workflows import CONFIRMED_CHOICE

    return (lean_enabled() and not state.get("workflow_continuation") and not state.get("method_comparison")
            and CONFIRMED_CHOICE not in task and _PREVIOUS_ACTION not in task)


def _client(context):
    if (client := getattr(context, "lean_client", None)) is not None:  # tests give a fake one
        return client
    from openai import OpenAI

    from ..provider_config import llm_api_key, llm_base_url

    return OpenAI(api_key=llm_api_key(), base_url=llm_base_url(), timeout=90, max_retries=1)


def _action(step: str | None) -> str | None:
    from workflow_registry import ACTION_DEFINITIONS, workflow_name

    return next((action for action in ACTION_DEFINITIONS if step and workflow_name(action) == step), None)


def _value(field: str, value: str) -> Any:
    """A setting's words as the decision field takes them (a list field gets the comma-separated items)."""
    from ..contracts import TaskDecision

    annotation = TaskDecision.model_fields[field].annotation
    kinds = get_args(annotation) or (annotation,)
    if any(get_origin(kind) is list for kind in kinds):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value.strip()


def _with_settings(task: str, raw: dict, decision, step: str, later: list[str]):
    """The decision with each stated setting of `step` it accepts; notes for the ones it does not and for those read
    as a later step's. A setting read as a workflow outside the steps is the model's misreading and is left out."""
    from pydantic import ValidationError

    from ..contracts import TaskDecision
    from ..lean import _found
    from ..method_names import UNREGISTERED

    applied, notes = [], []
    for item in raw.get("settings") or []:
        if not _found(task, item.get("quote", "")):
            continue
        if item.get("setting") == UNREGISTERED:
            applied.append(item)  # plan_notes says it is not applied
            continue
        workflow, _, field = item["setting"].partition(".")
        if workflow in later:
            notes.append(f'Not applied now: "{item["quote"]}" (read as a {workflow} setting; {workflow} is not part '
                         "of this run).")
        if workflow != step:
            continue
        try:
            decision = TaskDecision.model_validate({**decision.model_dump(), field: _value(field, item["value"])})
            applied.append(item)
        except (ValidationError, KeyError):
            notes.append(f'"{item["quote"]}" could not be set as {item["setting"]} (value "{item["value"]}"), so the '
                         "default is used.")
    return decision, applied, notes


def _do_decision(task: str, found, raw: dict, requirements):
    from ..contracts import TaskDecision
    from ..contracts.capability_check import RunVerdict
    from ..contracts.normalization import NormalizationChoice
    from ..lean import plan_notes, prep_steps
    from ..normalization_request import build_normalization_decision, method_named
    from ..prior_request import build_prior_decision

    steps = found.steps
    first = steps[0]
    later = steps[1:]
    then = next((step for step in later if step not in prep_steps()), None) if first in prep_steps() else None
    then_action = _action(then)
    if first == "SPONGE-PRIORS":
        decision = build_prior_decision(task, then_action)
    elif first == "NORMALIZE-EXPRESSION":
        method = method_named(task)
        decision = build_normalization_decision(task, method or "snail",
                                                NormalizationChoice(source="named" if method else "default"))
        decision = decision.model_copy(update={"then_action": then_action})
    else:
        action = _action(first)
        decision = TaskDecision(action=action, in_scope=True, should_execute=True, intent_type="run_analysis",
                                confidence=1.0, reason=f"Run {first} (lean decider).", capability_match_status="exact",
                                matched_actions=[action], execution_requested=True)
    decision, applied, setting_notes = _with_settings(task, raw, decision, first, later)
    notes = plan_notes(task, [first], applied, raw) + setting_notes
    notes += [f"This plan runs {first} only. {step} comes next: ask for it once {first} has finished."
              for step in later if step != then]  # the plan's own "Then" line says the step it carries
    return decision.model_copy(update={"run_verdict": RunVerdict(
        action=decision.action, verdict="contract_rules", request_sha256=requirements.source_sha256,
        credited=list(steps))}), notes


REASONING_MODELS = ("particle-ai/particle-1",)
"""Models that reason before answering; the reasoning counts against max_tokens (2026-11-23: particle-1 used 500-850
output tokens for a ~200-token form, and an EXPLAIN answer hit a 1200 cap)."""


def lean_max_tokens(model: str) -> int:
    """The output cap for a lean call: 6000 for free and reasoning models (the cap is a ceiling, only used tokens are
    billed), 1200 otherwise."""
    return 6000 if model.endswith(":free") or model.split(":")[0] in REASONING_MODELS else 1200


VERIFIED_RULES = frozenset({"R2", "R3", "R5", "R7", "R8", "R9", "R10"})
"""Rules whose refusal reason the code writes from the contracts (2026-11-22: R8-R10 were missing, so their refusals
reached the user with no reason). R6 is not here: its pick is the model's reading, so it names the user's words only."""


def _declined(task: str, found, raw: dict, verified: bool) -> list:
    """A verified refusal keeps its reason line; the model's own refusal keeps only the request's words it names
    (found in the request), so the reply says what could not be matched, never why."""
    from ..contracts.core_decision import DeclinedPart
    from ..lean import _found

    quote = found.decline_quote or raw.get("decline_quote", "")  # R6 names the result it found no workflow for
    quote = quote if _found(task, quote) else ""
    if verified:
        return [DeclinedPart(quote=quote, line=found.reply)]
    from ..interpretation.reason_layers import UNMATCHED

    return [DeclinedPart(quote=quote, line=f'"{quote}" -- {UNMATCHED}')] if quote else []


def _decision(task: str, found, raw: dict, requirements, task_state):
    from ..contracts import TaskDecision
    from ..contracts.core_decision import CoreDecision, DeclinedPart, FactQuestion
    from ..interpretation.task_answers import clarification_rounds
    from ..lean import _found, latest_words

    evidence = {"lean": {"rules": found.rules, "reply": found.reply, "question": found.question,
                         "steps": found.steps, "model": (found.calls[0]["model"] if found.calls else ""),
                         # A refusal R2, R3, R5 or R7 made: its reason is code's, from the contract and the user's
                         # words. Any other refusal (the model's, or R6's, which rests on the blind reading) never
                         # shows a reason (never a wrong reason).
                         "verified": found.kind == "DECLINE" and any(rule.split(":", 1)[0] in VERIFIED_RULES
                                                                      for rule in found.rules)}}
    if found.kind == "DO":
        decision, notes = _do_decision(task, found, raw, requirements)
        evidence["lean"]["notes"] = notes
        core = CoreDecision(kind="DO", workflows=found.steps, run_allowed=True, basis="lean", evidence=evidence)
        return decision.model_copy(update={"core": core})
    asking = found.kind == "ASK"
    decision = TaskDecision(
        action="no_tool", in_scope=found.kind != "DECLINE", should_execute=False, intent_type="answer_question",
        confidence=1.0, capability_match_status={"ASK": "ambiguous", "DECLINE": "unsupported"}.get(found.kind),
        clarification_question=(found.question or found.reply)[:300] if asking else None,
        reason={"ASK": "A question is asked before any workflow is chosen.",
                "DECLINE": "The request cannot be done as stated; the reply says why.",
                "EXPLAIN": "A question about the methods, answered from the workflow descriptions."}[found.kind])
    unsure = raw.get("unsure_quote", "")
    core = CoreDecision(
        kind=found.kind, basis="lean", workflows=found.steps, evidence=evidence,
        facts=[FactQuestion(question=found.question or found.reply, workflows=found.steps,
                            user_quote=unsure if _found(latest_words(task), unsure) else "")] if asking else [],
        declined=_declined(task, found, raw, evidence["lean"]["verified"]) if found.kind == "DECLINE" else [])
    if asking:
        core = clarification_rounds(core, task_state)
    return decision.model_copy(update={"core": core})


def _usage(state, calls: list[dict], context):
    from ..contracts import LLMUsage
    from ..trace_contracts import LLMCallUsage

    usage = LLMUsage.model_validate(state.get("token_usage") or {})
    for call in calls:
        usage.calls.append(LLMCallUsage(
            role="lean_decider", model=call["model"], input_tokens=call["input_tokens"],
            output_tokens=call["output_tokens"], total_tokens=call["input_tokens"] + call["output_tokens"],
            usage_provenance="actual", cost_provenance="actual" if call["cost_usd"] else "unavailable",
            cost_micro_usd=int(round(call["cost_usd"] * 1e6)) if call["cost_usd"] else None,
            duration_ms=call["duration_ms"], status="success"))
        usage.input_tokens += call["input_tokens"]
        usage.output_tokens += call["output_tokens"]
        usage.total_tokens += call["input_tokens"] + call["output_tokens"]
    return usage


def classify_lean(context, state: dict, user_task: str) -> dict | None:
    """The classify node's result from the lean decider, or None when its call fails (the old path then answers)."""
    from .. import lean
    from ..interpretation.request_requirements import read_request_requirements
    from ..llm import latest_user_message
    from ..provider_config import llm_base_url
    from .context import record_event

    requirements = read_request_requirements(latest_user_message(state["messages"]))
    model = context.router_model_name
    started = time.time()
    try:
        found, raw, cost = lean.decide(
            user_task, _client(context), model, max(getattr(context, "router_max_tokens", 0) or 0, lean_max_tokens(model)),
            usage_extra="openrouter.ai" in llm_base_url(), plan_details=False)
    except Exception as error:  # noqa: BLE001 - recorded; the old path answers the turn
        record_event(context, state, "lean.failed", "classify", {
            "model": model, "error": f"{type(error).__name__}: {error}"[:300],
            "seconds": round(time.time() - started, 2)})
        return None
    decision = _decision(user_task, found, raw, requirements, state.get("task_state"))
    usage = _usage(state, found.calls, context)
    record_event(context, state, "lean.decision", "classify", {
        "kind": found.kind, "steps": found.steps, "rules": found.rules, "form": raw, "model": model,
        "cost_micro_usd": int(round(cost * 1e6)), "seconds": round(time.time() - started, 2)})
    record_event(context, state, "core.decision", "classify", decision.core.model_dump(mode="json"))
    for call in usage.calls[len((state.get("token_usage") or {}).get("calls") or []):]:
        record_event(context, state, "llm.completed", "classify", call.model_dump(mode="json"))
    record_event(context, state, "decision.recorded", "classify", {
        "action": decision.action, "confidence": decision.confidence, "in_scope": decision.in_scope,
        "reason": decision.reason, "reason_code": "lean_decider",
        "recommended_actions": decision.recommended_actions})
    return {
        "decision": decision.model_dump(),
        "request_requirements": requirements.model_dump(mode="json"),
        "workflow_continuation": None,
        "method_comparison": None,
        "token_usage": usage.model_dump(),
        "budget_warnings": state.get("budget_warnings") or [],
        "semantic_goal": {},
        "requested_outcome": None,
        "outcome_hypotheses": [],
        "capability_match": {},
        "study_purpose": None,
    }
