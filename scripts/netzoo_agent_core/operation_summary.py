"""A plain-English description of one agent turn, built only from what the turn recorded.

The Activity view shows events; this module says what they add up to: the request, how the agent read it, the
method and steps it chose, what ran, what it produced and what happens next. Every sentence is filled from a
recorded field (decision, plan, tool results, evaluation, reply). Nothing is inferred, so a field that was not
recorded is left out rather than guessed.
"""

from __future__ import annotations

import re
from typing import Any

from .result_meaning import describe_files, meaning_for, next_analyses


__all__ = ["action_label", "build_operation_summary", "record_operation_summary", "SUMMARY_EVENT"]

SUMMARY_EVENT = "operation.summary"
_REQUEST_CHARS = 600
_REPLY_CHARS = 900
_LIST_ITEMS = 12

_KIND_SENTENCES = {
    "DO": "The agent read this as a request it can carry out with an available workflow.",
    "ASK": "The agent needed a fact it could not check from the request or the data, so it asked before running anything.",
    "CLARIFY": "The request did not say clearly enough which result is wanted, so the agent asked which one you mean.",
    "DECLINE": "The agent found no available workflow that produces what was asked, so it did not plan a run.",
    "UNCHECKED": "The agent could not confirm from the workflow descriptions that this can be done as asked.",
}
_EVIDENCE_WORDS = {
    "provided": "given in the request",
    "confirmed": "confirmed by you",
    "selected": "selected by you",
    "discovered": "found in the workspace",
    "derived": "derived from another input",
    "demo_bundle": "from a demo bundle",
    "defaulted": "default",
    "missing": "missing",
}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split()) if limit <= _REQUEST_CHARS else text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _strings(value: Any) -> list[str]:
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def action_label(action: str) -> str:
    """The same reading of an action name the desktop Activity view uses."""
    if action == "inspect_inputs":
        return "Inspect input data"
    if action.startswith("inspect_") and action.endswith("_inputs"):
        return f"Inspect {action[8:-7].replace('_', '-').upper()} inputs"
    if action.startswith("run_"):
        return f"Run {action[4:].replace('_', '-').upper()}"
    return action.replace("_", " ")


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message.get("content") if isinstance(message, dict) else "")
    return content if isinstance(content, str) else ""


_CONTINUATIONS = (
    ("DATA_CONFIRMATION_APPROVED", "You confirmed the input files the agent found."),
    ("DATA_CONFIRMATION_CORRECTED", "You corrected the input files the agent found."),
    ("accepted the previous capability recommendation", "You accepted the recommended workflow."),
    ("Selected input:", "You selected the inputs to use."),
)


def _continuation(text: str) -> str:
    """A reply the app turned into a typed continuation (``PREVIOUS_ACTION=...``), said the way the user gave it."""
    return next((said for marker, said in _CONTINUATIONS if marker in text), "You answered the agent's question.")


def _request(state: dict) -> tuple[str, str]:
    """The request and, on a follow-up turn, the user's reply to the agent.

    A follow-up arrives as "Previous NetZoo goal: ...\nUser follow-up: ..."; a confirmed choice arrives as a typed
    continuation (``PREVIOUS_ACTION=...``) whose request is the user's earlier message.
    """
    humans = [
        _message_text(message) for message in state.get("messages") or []
        if (getattr(message, "type", None) or (message.get("type") if isinstance(message, dict) else None)) == "human"
    ]
    reply = ""
    for text in reversed(humans):
        if "PREVIOUS_ACTION=" in text:
            reply = reply or _continuation(text)
            continue
        goal = re.match(r"^Previous NetZoo goal:\s*(.*?)\nUser follow-up:(.*)$", text, re.DOTALL)
        if goal:
            return _clip(goal.group(1), _REQUEST_CHARS), reply or _clip(goal.group(2), _REQUEST_CHARS)
        return _clip(text, _REQUEST_CHARS), reply
    return "", reply


def _latest_human(state: dict) -> str:
    for message in reversed(state.get("messages") or []):
        if (getattr(message, "type", None) or (message.get("type") if isinstance(message, dict) else None)) == "human":
            return _message_text(message)
    return ""


def _candidate_label(action: str) -> str:
    return "No workflow (answer in the conversation)" if action == "no_tool" else action_label(action)


def _usage(usage: Any) -> dict:
    if not isinstance(usage, dict):
        return {}
    calls = [call for call in usage.get("calls") or [] if isinstance(call, dict)]
    costs = [call.get("cost_micro_usd") for call in calls]
    known = [cost for cost in costs if isinstance(cost, int)]
    summary: dict[str, Any] = {"llm_calls": len(calls), "total_tokens": int(usage.get("total_tokens") or 0)}
    if known:
        summary["cost_usd"] = round(sum(known) / 1_000_000, 6)
        summary["cost_complete"] = len(known) == len(costs)
    models = sorted({str(call.get("model")) for call in calls if call.get("model")})
    if models:
        summary["models"] = models
    return summary


def _tools(state: dict) -> list[dict]:
    tools = []
    for raw in state.get("tool_results") or []:
        if not isinstance(raw, dict) or not _text(raw.get("action")):
            continue
        tools.append({
            "action": raw["action"],
            "label": action_label(raw["action"]),
            "status": _text(raw.get("status")) or "unknown",
            "summary": _text(raw.get("summary")),
            "superseded": raw.get("superseded") is True,
            "artifacts": _strings(raw.get("artifacts"))[:_LIST_ITEMS * 4],
            "warnings": _strings(raw.get("warnings"))[:_LIST_ITEMS],
            "errors": _strings(raw.get("errors"))[:_LIST_ITEMS],
        })
    return tools


# What a reply that ran nothing was, read from the renderer that wrote it (`reply_kind`, graph/response.py).
_REPLY_OUTCOMES = {
    "outcome_clarification": "choice", "research_choices": "choice", "hypothesis_routes": "choice",
    "needs_fact": "asked", "ask_facts": "asked", "clarify_goal": "clarify",
    "decline": "declined", "capability_check_gap": "declined", "capability_gap": "declined",
    "run_held": "held", "capability_unconfirmed": "held", "unchecked": "held", "unresolved": "held",
    "plan_rejected": "rejected", "preference_confirmation": "needs_confirmation",
    "input_confirmation": "needs_confirmation", "needs_input": "needs_input",
}
_RAN = {"executed", "preview", "failed", "inspected"}


def _outcome(core_kind: str, plan_status: str, evaluation: str, current: list[dict], analysis: list[dict],
             reply_kind: str = "") -> str:
    if evaluation == "failed" or any(tool["status"] == "failed" for tool in current):
        return "failed"
    if plan_status in {"needs_input", "needs_confirmation"}:
        return plan_status
    if analysis and all(tool["status"] == "dry_run" for tool in analysis):
        return "preview"
    if analysis and any(tool["status"] == "success" for tool in analysis):
        return "executed"
    if current:
        return "inspected"
    if reply_kind in _REPLY_OUTCOMES:
        return _REPLY_OUTCOMES[reply_kind]
    return {"ASK": "asked", "CLARIFY": "clarify", "DECLINE": "declined"}.get(core_kind, "answered")


def _headline(outcome: str, workflow: str, outputs: int, missing: list[str]) -> str:
    named = workflow or "The workflow"
    return {
        "executed": f"{named} ran and finished; {_plural(outputs, 'output file')} recorded."
        if outputs else f"{named} ran and finished; no output files were recorded.",
        "preview": f"{named} was checked and previewed as a dry run; the analysis has not run yet.",
        "failed": f"{named} did not finish: a step failed.",
        "needs_input": "The agent is waiting for inputs it needs before it can plan the run"
        + (f" ({_join(missing)})." if missing else "."),
        "needs_confirmation": "The agent is waiting for you to confirm the plan before it continues.",
        "inspected": "The agent inspected the inputs; no analysis was run.",
        "asked": "The agent asked a question; nothing was run.",
        "clarify": "The agent asked which result you want; nothing was run.",
        "choice": f"More than one method fits ({workflow}); the agent asked you to choose. Nothing was run."
        if workflow else "The agent offered choices and asked you to pick one; nothing was run.",
        "held": "The agent could not confirm that this run is possible as asked, so it held the run; nothing was run.",
        "rejected": "The plan did not pass its checks, so nothing was run.",
        "declined": "The agent did not plan a run for this request.",
        "answered": "The agent answered in the conversation; no workflow was run.",
    }[outcome]


def _questions(plan: dict, core: dict) -> list[str]:
    """The questions the turn recorded asking: the plan's own, the fact questions, the clarification."""
    asked = [_text(plan.get("question"))]
    asked += [_text(fact.get("question")) for fact in core.get("facts") or [] if isinstance(fact, dict)]
    asked.append(_text((core.get("clarify") or {}).get("question")))
    return [_clip(question, 500) for question in dict.fromkeys(question for question in asked if question)][:4]


def _next_step(outcome: str, workflow: str) -> str:
    if outcome == "preview":
        return f"Approve the checked plan to run {workflow or 'the workflow'}, or change the request."
    if outcome == "failed":
        return "Open Results in Activity for the error and suggested repair, fix the cause, then ask again."
    if outcome == "needs_confirmation":
        return "Confirm what the agent found (for example the input files), or answer no and give the correct ones."
    if outcome == "needs_input":
        return "Give the missing inputs in the conversation."
    if outcome in {"asked", "clarify"}:
        return "Answer the agent's question in the conversation."
    if outcome == "choice":
        return "Pick one of the offered options in the conversation, or say which result you need."
    if outcome in {"held", "rejected"}:
        return "Read the agent's reply for what blocked the run, then adjust the request or the inputs."
    if outcome == "executed":
        return "Open the recorded outputs from Results or the Outputs tab."
    return ""


_SYNTHETIC = "Synthetic Test mode"
_MAX_MEANINGS = 4


def _meanings(outcome: str, tools: list[dict], workflows: list[str], plan: dict, policy,
              core_kind: str = "") -> tuple[list, list]:
    """What the result means (per workflow that ran or was considered) and every output file, described."""
    evidence = [item for item in plan.get("evidence") or [] if isinstance(item, dict)]
    ran = list(dict.fromkeys(tool["action"] for tool in tools
                             if not tool["superseded"] and not tool["action"].startswith("inspect")))
    if outcome in {"answered", "declined"}:
        return [], []
    if not ran and outcome not in {"choice", "asked", "clarify", "held", "needs_input", "needs_confirmation"}:
        return [], []
    keys = [found for action in ran if (found := meaning_for(action))]
    if not keys:
        keys = [found for name in workflows if (found := meaning_for(name))]
    role = {"executed": "ran", "failed": "ran", "inspected": "ran", "preview": "previewed"}.get(outcome, "")
    if not role:  # a run waiting on its inputs has its method chosen; a question or a choice only considers one
        chosen = outcome in {"needs_input", "needs_confirmation"} and core_kind in {"DO", ""} and len(keys) == 1
        role = "selected" if chosen else "considered"
    meanings, files = [], []
    for action, meaning in keys[:_MAX_MEANINGS]:
        meanings.append({
            "workflow": meaning.name, "role": role, "about": meaning.about, "read": meaning.read,
            "limits": meaning.limits, "sources": [{"title": title, "url": url} for title, url in meaning.sources],
            "next": next_analyses(action, policy),
        })
        mine = [tool for tool in tools if tool["action"] == action and not tool["superseded"]]
        written = list(dict.fromkeys(path for tool in mine if tool["status"] == "success" for path in tool["artifacts"]))
        if written:
            files += describe_files(action, written, evidence, planned=False)
        elif outcome == "preview" and any(tool["status"] == "dry_run" for tool in mine):
            files += describe_files(action, [], evidence, planned=True)
    return meanings, files


def build_operation_summary(state: dict, result: dict | None = None, policy=None) -> dict:
    """Describe the turn in *state* (plus the respond node's *result*) as structured, readable English."""
    result = result or {}
    decision = state.get("decision") or {}
    core = decision.get("core") or {}
    plan = state.get("plan") or {}
    evaluation = state.get("evaluation") or {}
    core_kind = _text(core.get("kind"))
    plan_status = _text(plan.get("status"))
    workflow = _text(plan.get("workflow")) if plan_status and plan_status != "respond_only" else ""
    if workflow.casefold() in {"none", "no_tool", "unknown"}:
        workflow = ""

    tools = _tools(state)
    current = [tool for tool in tools if not tool["superseded"]]
    analysis = [tool for tool in current if not tool["action"].startswith("inspect")]
    outputs = sorted({path for tool in current if tool["status"] == "success" for path in tool["artifacts"]})
    planned = sorted({path for tool in current if tool["status"] == "dry_run" for path in tool["artifacts"]})
    warnings = list(dict.fromkeys(warning for tool in current for warning in tool["warnings"]))
    errors = list(dict.fromkeys(error for tool in current for error in tool["errors"]))
    missing = _strings(plan.get("missing_inputs"))[:_LIST_ITEMS]
    reply_kind = _text(result.get("reply_kind"))
    outcome = _outcome(core_kind, plan_status, _text(evaluation.get("status")), current, analysis, reply_kind)

    workflows = _strings(core.get("workflows")) or ([workflow] if workflow else [])
    candidates = [_candidate_label(action) for action in _strings(decision.get("candidate_actions"))]
    declined = [
        {"quote": _text(part.get("quote")), "reasons": _strings(part.get("reasons"))[:4],
         "line": _clip(_text(part.get("line")), 400)}
        for part in core.get("declined") or [] if isinstance(part, dict) and _text(part.get("quote"))
    ][:_LIST_ITEMS]
    steps = [
        {"action": _text(step.get("action")), "label": action_label(_text(step.get("action"))),
         "purpose": _text(step.get("purpose"))}
        for step in plan.get("steps") or [] if isinstance(step, dict) and _text(step.get("action"))
    ]
    confirmed = {field.casefold() for field in re.findall(r"CONFIRMED_INPUT_([a-z_]+)=", _latest_human(state), re.I)}
    inputs = [
        {"field": _text(item.get("field")), "value": _text(item.get("value")),
         "status": "confirmed" if _text(item.get("field")).casefold() in confirmed else _text(item.get("status"))}
        for item in plan.get("evidence") or [] if isinstance(item, dict) and _text(item.get("field"))
    ][:_LIST_ITEMS * 2]

    request, reply_to_agent = _request(state)
    narrative: list[str] = []
    if request:
        narrative.append(f"You asked: “{request}”" + (
            "" if not reply_to_agent else f" {reply_to_agent}" if reply_to_agent.startswith("You ")
            else f" Then you replied: “{reply_to_agent}”"))
    reading = _KIND_SENTENCES.get(core_kind, "")
    if core_kind == "DO" and core.get("partial"):
        reading += " Part of the request is outside what that workflow does, and that part was not run."
    if workflows and outcome not in {"answered", "declined"}:
        if outcome in _RAN or (len(workflows) == 1 and core_kind in {"DO", ""} and outcome != "held"):
            label = "Selected method"
        else:
            label = "Methods that fit" if len(workflows) > 1 else "Method being considered"
        reading += f" {label}: {_join(workflows)}."
    elif not reading:
        reading = "The agent handled this in the conversation and did not select a workflow."
    narrative.append(reading.strip())
    if declined:
        narrative.append("Not done: " + "; ".join(
            part["line"] or f"“{part['quote']}”" + (f" ({_join(part['reasons'])})" if part["reasons"] else "")
            for part in declined).rstrip(".") + ".")
    if steps:
        narrative.append(f"Plan for {workflow or 'this request'}: " + "; then ".join(
            step["label"] for step in steps) + ".")
    if missing:
        narrative.append(f"Still missing: {_join(missing)}.")
    if current:
        parts = []
        for tool in current:
            status = {"success": "completed", "dry_run": "previewed (dry run, not executed)",
                      "failed": "failed"}.get(tool["status"], tool["status"])
            parts.append(f"{tool['label']} {status}")
        narrative.append("What ran: " + "; ".join(parts) + ".")
        retried = len(tools) - len(current)
        if retried:
            narrative.append(f"{_plural(retried, 'earlier attempt')} was replaced after a recovery step.")
    if outputs:
        narrative.append(f"Outputs: {_plural(len(outputs), 'file')} recorded.")
    if errors:
        narrative.append(f"Error: {errors[0]}")
    headline = _headline(outcome, workflow or _join(workflows), len(outputs), missing)
    questions = _questions(plan, core)
    next_step = _next_step(outcome, workflow)

    reply = ""
    messages = result.get("messages") or []
    if messages:
        reply = _clip(_message_text(messages[-1]), _REPLY_CHARS)

    meanings, files = _meanings(outcome, tools, workflows, plan, policy, core_kind)
    caveats = []
    if any(_SYNTHETIC in warning for warning in warnings):
        for item in files:
            if item["written"]:
                item["tags"] = [*item.get("tags", []), "mode:synthetic test"]
        caveats.append("Synthetic Test mode was on: unrecognised gene labels were accepted as test-only identifiers. "
                       "These results are for software testing, not biological evidence.")
    if outcome == "preview":
        caveats.append("Dry run: the files listed are where the run will write; nothing has been written yet.")

    return {
        "version": 1,
        "outcome": outcome,
        "headline": headline,
        "request": request,
        "follow_up": reply_to_agent or None,
        "narrative": narrative,
        "decision": {
            "kind": core_kind or None,
            "action": _text(decision.get("action")) or None,
            "reason": _clip(_text(decision.get("reason")), 400) or None,
            "workflows": workflows,
            "candidates": candidates,
            "partial": bool(core.get("partial")),
            "declined": declined,
        },
        "method": {"workflow": workflow or None, "objective": _clip(_text(plan.get("objective")), 400) or None,
                   "plan_status": plan_status or None, "steps": steps},
        "inputs": [{**item, "source": _EVIDENCE_WORDS.get(item["status"], item["status"])} for item in inputs],
        "missing_inputs": missing,
        "tools": [{key: tool[key] for key in ("label", "status", "summary", "superseded")} for tool in tools],
        "outputs": outputs[:_LIST_ITEMS * 4],
        "planned_outputs": planned[:_LIST_ITEMS * 4],
        "warnings": warnings[:_LIST_ITEMS],
        "errors": errors[:_LIST_ITEMS],
        "evaluation": _clip(_text(evaluation.get("reason")), 400) or None,
        "questions": questions,
        "next_step": next_step or None,
        "reply_excerpt": reply or None,
        "reply_kind": reply_kind or None,
        "usage": _usage(result.get("token_usage") or state.get("token_usage")),
        "meaning": meanings,
        "files": files,
        "caveats": caveats,
    }


def record_operation_summary(record, state, result: dict, policy=None) -> None:
    """Record the turn's summary (`operation.summary`) and the auto tags of the files it wrote.

    Observability only: a summary or tag store that fails never changes the reply. *record* is
    ``record(event_type, payload)`` bound to the respond node.
    """
    try:
        summary = build_operation_summary(dict(state), result, policy)
    except Exception as error:  # noqa: BLE001 -- the reply must stand whatever the summary does
        summary = {"version": 1, "unavailable": type(error).__name__}
    record(SUMMARY_EVENT, summary)
    if summary.get("files"):  # only files the run wrote and that exist are tagged
        from .output_tags import record_auto_tags

        try:
            record_auto_tags(summary["files"], session_id=str(state.get("session_id") or ""), run_id=str(state.get("run_id") or ""))
        except Exception:  # noqa: BLE001
            pass
