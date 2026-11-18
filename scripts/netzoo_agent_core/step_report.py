"""The terminal's step list: each step printed as it finishes, with what it found and on what basis.

The window shows the same thing (desktop TurnActivity.tsx); both read only the run's trace events,
never a model's prose, and follow the same rules:

* a step is named in words ("Read your request", "Ran PANDA") with its duration;
* each check gives its finding and basis (the workflows that deliver a result, the questions the
  code held back and by which rule, the contract line a question rests on, what is not possible);
* the reading routing accepted is shown with the user's own words each value rests on;
* a bare "not available" with no basis, the early intent reading and bookkeeping nodes are left
  out, since the decision line is where the turn's outcome is stated.

Quotes are the user's own words and may be in any language; everything else is English.
"""

from __future__ import annotations

import re
from collections.abc import Callable

__all__ = ["StepReporter", "stage_lines"]

QUIET_NODES = {"apply_project_policy", "retrieve_memory", "consolidate_memory", "cli"}

STEP_LABELS = {
    "classify": "Read your request",
    "plan": "Built a plan",
    "evaluate_plan": "Checked the plan",
    "evaluate": "Checked the result",
    "recover": "Chose a recovery",
    "respond": "Wrote the reply",
    "input_content_mapper": "Matched file contents to inputs",
    "follow_up": "Read your follow-up",
}

ARTIFACT_WORDS = {
    "regulatory_network": "a regulatory network",
    "coexpression_network": "a co-expression network",
    "regulatory_network_and_tf_activity": "a regulatory network with TF activity",
    "signed_regulatory_effect_network": "a signed regulatory network",
    "multi_omic_network": "a network across omics layers",
    "tf_activity_matrix": "TF activity per sample",
    "expression_matrix": "an expression matrix",
    "measurement_dataset": "a dataset",
    "pvalue_matrix": "a p-value matrix",
    "mutation_matrix": "a mutation matrix",
    "pathway_mutation_matrix": "pathway mutation scores",
    "gene_mutation_scores": "gene mutation scores",
    "sample_distance_matrix": "distances between samples",
    "sample_cluster_assignment": "sample clusters",
    "community_assignment": "network communities",
    "validation_report": "a validation report",
    "pathway_heterogeneity_table": "pathways that vary between patients",
}
GRANULARITY_WORDS = {"aggregate": "one for all samples", "sample_specific": "one per sample"}
REGULATOR_WORDS = {"tf": "TFs", "mirna": "miRNAs"}
OPERATION_WORDS = {"infer": "build it", "analyze": "analyze it", "explain": "explain it",
                   "acquire": "get the data", "prepare": "prepare the data", "validate": "check it"}


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _short(value, limit: int = 280) -> str:
    text = _text(value)
    return text if len(text) <= limit else text[: limit - 3] + "…"


def _spelled(value) -> str:
    return str(value).replace("_", " ")


def _action_label(action: str) -> str:
    if action == "inspect_inputs":
        return "Inspect input data"
    if action.startswith("run_"):
        return "Run " + action[4:].replace("_", "-").upper()
    return _spelled(action)


def _seconds(ms) -> str:
    if not isinstance(ms, (int, float)):
        return ""
    if ms < 1000:
        return "<1 s"
    if ms < 60_000:
        return f"{ms / 1000:.1f} s" if ms < 10_000 else f"{ms / 1000:.0f} s"
    return f"{int(ms // 60_000)} min {round((ms % 60_000) / 1000)} s"


def _value_words(dimension: str, value: str) -> str:
    if dimension == "operation":
        return f"you want to {OPERATION_WORDS.get(value, _spelled(value))}"
    if dimension == "input_artifact":
        return f"input: {ARTIFACT_WORDS.get(value, _spelled(value))}"
    if dimension == "artifact_type":
        return ARTIFACT_WORDS.get(value, _spelled(value))
    if dimension == "granularity":
        return GRANULARITY_WORDS.get(value, _spelled(value))
    if dimension == "regulator_type":
        return f"regulators: {REGULATOR_WORDS.get(value, value)}"
    if dimension == "target_type":
        return f"targets: {'genes' if value == 'gene' else _spelled(value)}"
    if dimension == "entity_type":
        return f"about: {_spelled(value)}"
    if dimension == "selection_tag":
        return f"method feature: {_spelled(value)}"
    return _spelled(value)


def _reading_lines(reading) -> list[str]:
    if not isinstance(reading, list) or not reading:
        return []
    lines = []
    several = len(reading) > 1
    if several:
        lines.append(f"Understood {len(reading)} possible readings:")
    for index, item in enumerate(reading):
        if not isinstance(item, dict):
            continue
        regulators = [REGULATOR_WORDS[r] for r in item.get("regulator_types") or [] if r in REGULATOR_WORDS]
        what = ", ".join(part for part in (
            ARTIFACT_WORDS.get(_text(item.get("artifact_type")), ""),
            GRANULARITY_WORDS.get(_text(item.get("granularity")), ""),
            f"regulators: {' and '.join(regulators)}" if regulators else "",
        ) if part)
        asked = " (to be explained, not run)" if item.get("operation") == "explain" else ""
        lines.append(f"{f'{index + 1}. ' if several else 'Understood: '}{what or 'no specific result'}{asked}")
        for stated in item.get("stated") or []:
            if isinstance(stated, dict) and _text(stated.get("quote")):
                words = _value_words(_text(stated.get("dimension")), _text(stated.get("value")))
                lines.append(f"  “{_short(stated['quote'])}” → {words}")
        inferred = list(dict.fromkeys(
            _value_words(_text(row.get("dimension")), _text(row.get("value")))
            for row in item.get("inferred") or [] if isinstance(row, dict)))
        if inferred:
            lines.append(f"  Not stated, inferred: {', '.join(inferred)}")
        if item.get("unresolved"):
            lines.append(f"  Not clear from the request: {', '.join(_spelled(v) for v in item['unresolved'])}")
    return lines


def _delivered_by(value) -> str:
    workflow, _, result = str(value).partition(".")
    name = workflow.replace("_", "-").upper()
    return f"{name} ({_spelled(result)})" if result else name


def _capability_lines(check) -> list[str]:
    lines = []
    for item in (check or {}).get("requirements") or [] if isinstance(check, dict) else []:
        if not isinstance(item, dict) or item.get("kind") != "result" or not _text(item.get("quote")):
            continue
        quote = f"  “{_short(item['quote'])}”"
        delivered = item.get("delivered_by") or []
        by = ", ".join(_delivered_by(v) for v in delivered[:4])
        more = f" and {len(delivered) - 4} more" if len(delivered) > 4 else ""
        status = item.get("status")
        if status == "available" and by:
            lines.append(f"{quote} → {by}{more}")
        elif status == "with_step" and by:
            lines.append(f"{quote} → with an extra step: {by}{more}")
        elif status == "needs_fact" and by:
            lines.append(f"{quote} → {by}{more}, once a fact is confirmed")
        elif status == "not_available":
            limits = [_short(v) for v in item.get("limits") or [] if _text(v)]
            not_by = [_spelled(v) for v in item.get("not_by") or []]
            if limits:
                lines.append(f"{quote} → not available: {limits[0]}")
            elif not_by:
                lines.append(f"{quote} → not available: no workflow does {', '.join(not_by)}")
    return lines


def _fact_check_lines(payload: dict) -> list[str]:
    lines = []
    candidates = [_text(v) for v in payload.get("candidates") or [] if _text(v)]
    if candidates:
        lines.append(f"  Methods weighed: {', '.join(candidates)}")
    rejected = payload.get("rejected") or []
    rules = list(dict.fromkeys(
        re.sub(r"^R\d+[a-z]?\s+", "", _text(item.get("rule")), flags=re.IGNORECASE)
        for item in rejected if isinstance(item, dict) and _text(item.get("rule"))))
    if rejected:
        noun = "question" if len(rejected) == 1 else "questions"
        lines.append(f"  {len(rejected)} possible {noun} not asked" + (f": {'; '.join(rules)}" if rules else ""))
    accepted = len(payload.get("accepted") or [])
    if accepted:
        lines.append(f"  {accepted} {'fact' if accepted == 1 else 'facts'} to confirm with you")
    return lines


def _guard_line(payload: dict) -> str:
    jev = payload.get("jev") or {}
    read = _text(jev.get("kind"))
    confidence = f" ({round(jev['confidence'] * 100)}%)" if isinstance(jev.get("confidence"), (int, float)) else ""
    reading = f"it read the request as {read}{confidence}" if read else ""
    action = payload.get("action")
    if action == "clarify":
        return "Independent check changed the decision to asking what you want" + (f": {reading}" if reading else "")
    if action == "ask":
        return "Independent check changed the decision to asking you first" + (f": {reading}" if reading else "")
    if action == "agrees_or_unsure":
        return "Independent check: decision kept" + (f"; {reading}" if reading else "")
    return ""


def _purpose_line(payload: dict) -> str:
    design = _text(payload.get("design"))
    claims = [str(c[0]) if isinstance(c, (list, tuple)) and c else _text(c) for c in payload.get("claims") or []]
    parts = [p for p in (f"design: {_spelled(design)}" if design else "",
                         f"aims: {_spelled(', '.join(c for c in claims if c))}" if any(claims) else "") if p]
    if not parts:
        return "Read the study purpose: none stated"
    quote = f" (“{_short(payload.get('design_quote'))}”)" if _text(payload.get("design_quote")) else ""
    return f"Read the study purpose: {'; '.join(parts)}{quote}"


def _decision_lines(payload: dict) -> list[str]:
    workflows = [w for w in payload.get("workflows") or [] if isinstance(w, str) and w != "NO-TOOL"]
    names = ", ".join(workflows)
    part = " (part of what you asked)" if payload.get("partial") else ""
    kind, basis = payload.get("kind"), payload.get("basis")
    head = ""
    if kind == "DO":
        if basis == "run":
            head = f"Decision: prepare a run of {names or 'the workflow'}{part}"
        elif basis == "run_held":
            head = f"Decision: hold the run of {names or 'the workflow'} for now{part}"
        elif names:
            head = f"Decision: {names} can give what you asked for{part}"
    elif kind == "ASK":
        head = "Decision: ask you for what is still missing"
    elif kind == "CLARIFY":
        head = "Decision: ask what you want to get"
    elif kind == "DECLINE":
        head = "Decision: not possible with the available methods"
    lines = [head] if head else []
    clarify = payload.get("clarify")
    if isinstance(clarify, dict) and _text(clarify.get("question")):
        lines.append(f"  Will ask: “{_short(clarify['question'])}”")
        candidates = [_text(c) for c in clarify.get("candidates") or [] if _text(c)]
        if candidates:
            extra = f" and {len(candidates) - 8} more" if len(candidates) > 8 else ""
            lines.append(f"  Possible methods: {', '.join(candidates[:8])}{extra}")
    for fact in (payload.get("facts") or [])[:4]:
        if isinstance(fact, dict) and _text(fact.get("question")):
            lines.append(f"  Will ask: “{_short(fact['question'])}”")
            if _text(fact.get("contract_quote")):
                lines.append(f"    Rule: “{_short(fact['contract_quote'])}”")
    for declined in (payload.get("declined") or [])[:4]:
        if isinstance(declined, dict) and _text(declined.get("line")):
            lines.append(f"  Not possible: {_short(declined['line'])}")
    return lines


def _model_call_line(calls: list[dict]) -> str:
    if not calls:
        return ""
    models = list(dict.fromkeys(_text(c.get("model")).split("/")[-1] for c in calls if _text(c.get("model"))))
    from .model_call_labels import role_label

    roles: dict[str, int] = {}
    for call in calls:
        role = _text(call.get("role"))
        if role:
            roles[role] = roles.get(role, 0) + 1
    # The finished form of each role's words ("read the request"), as the window shows it.
    role_text = ", ".join(_past(role_label(role)) + (f" ×{count}" if count > 1 else "") for role, count in roles.items())
    tokens = sum(int(c.get("total_tokens") or 0) for c in calls)
    failed = sum(1 for c in calls if c.get("status") == "failed")
    parts = [", ".join(models) or "Model",
             f"{len(calls)} {'call' if len(calls) == 1 else 'calls'}" + (f" ({role_text})" if role_text else ""),
             f"{tokens:,} tokens" if tokens else "", f"{failed} retried" if failed else ""]
    return " · ".join(p for p in parts if p)


def _past(label: str) -> str:
    """'reading the request' -> 'read the request' (the window's wording for a finished call)."""
    first, _, rest = label.partition(" ")
    irregular = {"reading": "read", "getting": "get", "writing": "write", "telling": "tell", "routing": "route"}
    if first in irregular:
        verb = irregular[first]
    elif first.endswith("ing"):
        stem = first[:-3]
        verb = stem + "e" if stem.endswith(("c", "v", "z", "s", "r", "at")) and not stem.endswith("ss") else stem
    else:
        verb = first
    return f"{verb} {rest}".strip()


def _step_label(node: str, rows: list[dict]) -> str:
    if node == "execute_tool":
        actions = list(dict.fromkeys(_text(r["payload"].get("action")) for r in rows
                                     if r["type"] == "tool.started" and _text(r["payload"].get("action"))))
        if actions == ["inspect_inputs"]:
            return "Checked the input files"
        names = [(lambda label: label[4:] if label.startswith("Run ") else label[:1].lower() + label[1:])(_action_label(a))
                 for a in actions]
        what = "the workflow" if not names else names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
        return f"Ran {what}"
    return STEP_LABELS.get(node, _spelled(node))


def stage_lines(node: str, rows: list[dict]) -> list[str]:
    """The finding-and-basis lines for one finished step, from its events in order."""
    details: list[str] = []
    for index, row in enumerate(rows):
        details.extend(event_lines(row["type"], row["payload"], rows[:index]))
    if line := _model_call_line([r["payload"] for r in rows if r["type"] == "llm.completed"]):
        details.append(line)
    return details


def event_lines(kind: str, payload: dict, earlier: list[dict]) -> list[str]:
    """The lines one event adds to its step; `earlier` is the step's events before it."""
    details: list[str] = []
    has_decision = any(r["type"] == "core.decision" for r in earlier)
    if kind == "routing.semantic_interpretation_retried":
        details.append("The first reading was incomplete; reading again")
    elif kind == "routing.semantic_interpretation_accepted":
        details.extend(_reading_lines(payload.get("reading")) or ["Read what you asked for"])
    elif kind == "routing.registry_match_completed":
        hypotheses = [_action_label(a).removeprefix("Run ") for a in payload.get("hypothesis_actions") or [] if isinstance(a, str)][:8]
        matched = [_action_label(a).removeprefix("Run ") for a in payload.get("matched_actions") or [] if isinstance(a, str)][:8]
        if hypotheses:
            details.append(f"Candidate workflows: {', '.join(hypotheses)}")
        if matched:
            details.append(f"Registry matched: {', '.join(matched)}")
        elif payload.get("status") == "ambiguous":
            details.append("Registry result: ambiguous; no workflow selected")
    elif kind == "routing.selection_conditions_unresolved":
        details.append("The stated preferences did not resolve the workflow choice")
    elif kind == "routing.study_purpose_detected":
        details.append(_purpose_line(payload))
    elif kind == "routing.capability_checked":
        details.extend(["Checked what the methods can do", *_capability_lines(payload.get("check"))])
    elif kind == "core.fact_check":
        details.extend(["Checked the stated facts", *_fact_check_lines(payload)])
    elif kind == "core.jev_guard":
        if line := _guard_line(payload):
            details.append(line)
    elif kind == "routing.request_concerns_matched":
        details.append("Noted your stated concerns")
    elif kind == "core.decision":
        details.extend(_decision_lines(payload))
    elif kind == "decision.recorded":
        if payload.get("action") == "no_tool":
            details.append("Reply in the conversation; no workflow is run")
        elif _text(payload.get("action")) and not has_decision:
            details.append(f"Selected {_action_label(_text(payload['action']))}")
    elif kind == "plan.created":
        if payload.get("status") == "respond_only":
            details.append("Response path: no workflow execution planned")
        else:
            details.append(f"Plan: {_text(payload.get('workflow')) or 'workflow'} · {_spelled(_text(payload.get('status')) or 'prepared')}")
            for item in payload.get("evidence") or []:
                if isinstance(item, dict) and _text(item.get("field")) and _text(item.get("status")) not in ("", "missing"):
                    status = _spelled(_text(item["status"]))
                    details.append(f"Input · {item['field']}: {_short(item.get('value')) or status} ({status})")
    elif kind == "tool.started":
        action = _text(payload.get("action"))
        purpose = f": {_short(payload.get('purpose'))}" if _text(payload.get("purpose")) else ""
        details.append(f"{_action_label(action) if action else 'Tool'} started{purpose}")
    elif kind == "tool.completed":
        summary = f": {_short(payload.get('summary'))}" if _text(payload.get("summary")) else ""
        details.append(f"Tool {_spelled(_text(payload.get('status')) or 'finished')}{summary}")
        errors = [_short(e) for e in payload.get("errors") or [] if _text(e)]
        details.extend(f"  Problem: {e}" for e in errors[:3])
        if len(errors) > 3:
            details.append(f"  …and {len(errors) - 3} more problems (see the log)")
        details.extend(f"  Output: {_text(f)}" for f in (payload.get("artifacts") or [])[:5] if _text(f))
        if _text(payload.get("log_file")):
            details.append(f"  Log: {payload['log_file']}")
    elif kind == "evaluation.recorded":
        reason = f": {_short(payload.get('reason'))}" if _text(payload.get("reason")) else ""
        details.append(f"Result {_spelled(_text(payload.get('status')) or 'reviewed')}{reason}")
    elif kind == "error.recorded":
        details.append(f"Error: {_short(payload.get('message'))}" if _text(payload.get("message")) else "Error")
    return details


DOING_LABELS = {
    "classify": "Reading your request",
    "plan": "Building a plan",
    "evaluate_plan": "Checking the plan",
    "execute_tool": "Running a tool",
    "evaluate": "Checking the result",
    "recover": "Choosing a recovery",
    "respond": "Writing the reply",
    "input_content_mapper": "Matching file contents to inputs",
    "follow_up": "Reading your follow-up",
}


def _failed(rows: list[dict]) -> bool:
    for row in rows:
        payload = row["payload"]
        if row["type"] == "error.recorded" or (
                row["type"] in ("tool.completed", "evaluation.recorded") and payload.get("status") == "failed"):
            return True
    return False


class StepReporter:
    """Print each step as it happens: its findings line by line, then a ✓ or ✗ with its duration.

    A step's heading is printed with its first finding, so a step with nothing to report takes one
    line ("✓ Checked the plan  (<1 s)"). Bookkeeping nodes are printed only when they fail.
    """

    def __init__(self, emit: Callable[[list[str]], None]):
        self._emit = emit
        self._open: dict[tuple[str, str], list[dict]] = {}
        self._headed: set[tuple[str, str]] = set()
        self._worked_ms: dict[str, float] = {}
        self._steps: dict[str, int] = {}
        self._calls: dict[str, int] = {}

    def __call__(self, event: dict) -> None:
        try:
            self._receive(event)
        except Exception:  # noqa: BLE001 - the step list is a view; it must never break a turn
            return

    def _receive(self, event: dict) -> None:
        run, node, kind = str(event.get("run_id")), str(event.get("node")), str(event.get("event_type"))
        payload = event.get("payload") or {}
        key = (run, node)
        if kind == "llm.started":
            return  # the live line names the call in progress; finished calls are summarised per step
        if kind == "node.started":
            self._open[key] = []
            self._headed.discard(key)
            return
        if kind == "node.finished":
            self._finish(key, payload)
            return
        if kind in ("run.finished", "run.paused", "run.interrupted"):
            self._close_run(run, kind, payload)
            return
        rows = self._open.get(key)
        if rows is None:
            return
        lines = event_lines(kind, payload, rows)
        rows.append({"type": kind, "payload": payload})
        if lines and node not in QUIET_NODES:
            heading = [] if key in self._headed else [f"▸ {DOING_LABELS.get(node, _spelled(node))}"]
            self._headed.add(key)
            self._emit([*heading, *(f"    {line}" for line in lines)])

    def _finish(self, key: tuple[str, str], payload: dict) -> None:
        run, node = key
        rows = self._open.pop(key, [])
        duration = payload.get("duration_ms")
        self._worked_ms[run] = self._worked_ms.get(run, 0) + (duration if isinstance(duration, (int, float)) else 0)
        calls = [r["payload"] for r in rows if r["type"] == "llm.completed"]
        self._calls[run] = self._calls.get(run, 0) + len(calls)
        failed = _failed(rows)
        headed = key in self._headed
        self._headed.discard(key)
        if node in QUIET_NODES and not failed:
            return
        self._steps[run] = self._steps.get(run, 0) + 1
        took = _seconds(duration)
        done = f"{'✗' if failed else '✓'} {_step_label(node, rows)}" + (f"  ({took})" if took else "")
        lines = []
        if node in QUIET_NODES:  # a failed bookkeeping step: its findings were held until now
            lines = [f"    {line}" for row_index, row in enumerate(rows)
                     for line in event_lines(row["type"], row["payload"], rows[:row_index])]
        if model := _model_call_line(calls):
            lines.append(f"    {model}")
        self._emit([*lines, f"  {done}" if headed else done])

    def _close_run(self, run: str, kind: str, payload: dict) -> None:
        steps, calls = self._steps.pop(run, 0), self._calls.pop(run, 0)
        worked = _seconds(self._worked_ms.pop(run, 0)) if run in self._worked_ms else ""
        for key in [k for k in self._open if k[0] == run]:
            self._open.pop(key, None)
            self._headed.discard(key)
        if not steps:
            return
        lead = {"run.paused": "Waiting for you", "run.interrupted": "Interrupted"}.get(kind) or (
            "Failed" if payload.get("status") == "failed" else "Worked")
        counts = " · ".join(p for p in (worked, f"{steps} {'step' if steps == 1 else 'steps'}",
                                        f"{calls} model {'call' if calls == 1 else 'calls'}" if calls else "") if p)
        self._emit([f"── {lead} · {counts}"])
