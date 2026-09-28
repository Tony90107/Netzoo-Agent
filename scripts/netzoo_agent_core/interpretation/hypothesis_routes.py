"""One section per reading when a request's readings would collapse (Log 248).

A request that states two hypotheses can reach the reply with both readings
validated and still be answered with one workflow: the matcher returns the one
exact capability both readings accept, or the only reading that has a workflow
(Log 245). The readings are then listed on their own, each with the registered
workflows that fit it -- their algorithmic premises and inputs -- and the reply
asks which to start with. Nothing here routes: every candidate list is the
registry's deterministic match of one validated reading, and a tie reply that
already covers every reading is left exactly as it was.
"""

from __future__ import annotations

from workflow_registry import GUIDANCE_COMPOSITIONS

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text_with_user_data, user_data_token
from ..routing.method_rejections import rejected_methods_for
from ..routing.outcome_matching import match_requested_outcome, match_semantic_request
from .concept_answers import _GRANULARITY_LABELS, _artifact_label, _candidate_details

__all__ = ["render_hypothesis_routes"]

_NOT_INSPECTED = "No files were inspected and no analysis ran."
# Evidence that says what a reading is about, in the order it is quoted.
_QUOTED_DIMENSIONS = ("artifact_type", "granularity", "regulator_type", "operation", "input_artifact")


def _input_only_artifacts(policy: ProjectPolicySnapshot) -> frozenset[str]:
    consumed, produced = set(), set()
    for spec in policy.workflows.values():
        capability = spec.output_capability
        consumed.update(capability.input_artifacts)
        produced.update(capability.produced_artifacts)
        produced.add(capability.artifact_type)
    return frozenset(consumed - produced)


def _signature(outcome):
    return (outcome.artifact_type, frozenset(outcome.regulator_types), outcome.granularity)


def _readings(decision: TaskDecision, policy: ProjectPolicySnapshot) -> list:
    """Distinct scientific readings: not an input restated as the result, not a
    reading that only lacks inputs another reading of the same result states."""
    excluded = _input_only_artifacts(policy) | {"unknown"}
    candidates = [
        item for item in decision.outcome_hypotheses
        if item.outcome.artifact_type not in excluded
    ]
    readings = []
    for item in candidates:
        inputs = set(item.outcome.input_artifacts)
        if any(
            other is not item
            and _signature(other.outcome) == _signature(item.outcome)
            and inputs < set(other.outcome.input_artifacts)
            for other in candidates
        ):
            continue
        key = (_signature(item.outcome), frozenset(inputs))
        if key not in {(_signature(r.outcome), frozenset(r.outcome.input_artifacts)) for r in readings}:
            readings.append(item)
    return readings


def _candidates(task: str, reading, request_mode: str) -> list[str]:
    match = match_semantic_request(task, [reading], request_mode=request_mode)
    if match.status in {"exact", "fallback"}:
        return list(match.matched_actions)
    if match.status == "ambiguous":
        return list(match.hypothesis_actions or match.matched_actions)
    return []


def _spans(reading, task: str) -> list[str]:
    """The reading's explicit quotes that the request really contains, in order."""
    folded = task.casefold()
    spans = []
    for dimension in _QUOTED_DIMENSIONS:
        for item in reading.evidence:
            span = (item.text_span or "").strip()
            if (item.dimension == dimension and item.source == "explicit" and span
                    and span.casefold() in folded and span not in spans):
                spans.append(span)
    return spans


def _quote(reading, others, task: str) -> str | None:
    """A quote only this reading gives, so two titles never read the same."""
    shared = {span for other in others for span in _spans(other, task)}
    return next((span for span in _spans(reading, task) if span not in shared), None)


def _input_label(value: str) -> str:
    return value.replace("_", " ")


def _result_line(outcome) -> str:
    inputs = [_input_label(value) for value in outcome.input_artifacts if value != "unknown"]
    granularity = _GRANULARITY_LABELS.get(outcome.granularity, "")
    line = "Result: " + _artifact_label(outcome.artifact_type)
    if granularity:
        line += f" ({granularity})"
    line += ", from " + (" and ".join(inputs) if inputs else "inputs the request does not state")
    return line + "."


def _accepting_workflows(outcome, policy: ProjectPolicySnapshot) -> list[str]:
    inputs = {value for value in outcome.input_artifacts if value != "unknown"}
    if not inputs:
        return []
    found = []
    for spec in policy.workflows.values():
        capability = spec.output_capability
        if inputs <= set(capability.input_artifacts):
            produced = capability.produced_artifacts or {capability.artifact_type}
            outputs = ", ".join(sorted(_artifact_label(a) for a in produced))
            found.append(f"**{spec.workflow}** ({outputs})")
    return sorted(set(found))


def _covered(decision: TaskDecision, routes: list[tuple]) -> bool:
    shown = set(decision.hypothesis_actions)
    return (
        decision.capability_match_status == "ambiguous"
        and len(shown) >= 2
        and all(actions and set(actions) <= shown for _, actions in routes)
    )


def _alone_candidates(task: str, reading, value: str) -> list[str]:
    """The registry's match for one input, minus methods rejected for that input.

    `match_semantic_request` checks every current input the request states, so
    SAMBAR is rejected for "mutations or expression" as a whole; what one input
    supports on its own is the capability match alone.
    """
    match = match_requested_outcome(reading.outcome)
    actions = (
        list(match.matched_actions) if match.status in {"exact", "fallback"}
        else list(match.hypothesis_actions or match.matched_actions) if match.status == "ambiguous"
        else []
    )
    rejected = {item.action for item in rejected_methods_for(task, [value], actions=actions)}
    return [action for action in actions if action not in rejected]


def _splits(task: str, reading) -> list[tuple[str, list[str]]]:
    """Log 250: each stated input on its own, when no workflow takes them together.

    Only a reading with no candidate and two or more inputs is split, and only
    when some input alone has a candidate -- otherwise the split says nothing
    the reading does not. The inputs are the reading's own; none is added.
    """
    inputs = [value for value in reading.outcome.input_artifacts if value != "unknown"]
    if len(inputs) < 2:
        return []
    def alone(value):
        # The other inputs' evidence goes with them, or the match reads it as
        # an input the outcome dropped.
        return reading.model_copy(update={
            "outcome": reading.outcome.model_copy(update={"input_artifacts": [value]}),
            "evidence": [item for item in reading.evidence
                         if item.dimension != "input_artifact" or item.value == value],
        }, deep=True)
    splits = [(value, _alone_candidates(task, alone(value), value)) for value in inputs]
    # An input that has a workflow first; otherwise the reading's own order.
    splits.sort(key=lambda item: not item[1])
    return splits if any(actions for _, actions in splits) else []


def _composition(outcome):
    """The Log 252 composition for a one-input result no workflow produces, if any."""
    inputs = [value for value in outcome.input_artifacts if value != "unknown"]
    if len(inputs) != 1:
        return None
    return GUIDANCE_COMPOSITIONS.get((outcome.artifact_type, inputs[0]))


def _composition_lines(composition, policy) -> tuple[list[str], str]:
    lines = [composition.lead]
    names = []
    for action, gives in composition.sources:
        spec = policy.workflows.get(action)
        if spec is None:
            continue
        names.append(spec.workflow)
        lines.append(f"- **{spec.workflow}** gives {gives}.")
        # The premise and inputs of each source, as every other candidate shows them.
        lines.extend(
            line for line in _candidate_details(action, spec, policy)
            if line.startswith(("  - Method premise:", "  - Required inputs:"))
        )
    lines.append(composition.outside_step)
    lines.extend(composition.notes)
    return lines, "a profile from " + " / ".join(names) + ", then clustering outside NetZoo"


def _option_lines(outcome, actions, policy, *, single_input: bool) -> tuple[list[str], str]:
    specs = [(action, policy.workflows[action]) for action in actions if action in policy.workflows]
    if specs:
        lines = [line for action, spec in specs for line in _candidate_details(action, spec, policy)]
        return lines, " or ".join(spec.workflow for _, spec in specs)
    composition = _composition(outcome)
    if composition is not None:
        return _composition_lines(composition, policy)
    lines = ["No registered workflow produces this result from "
             + ("this input." if single_input else "these inputs.")]
    accepting = _accepting_workflows(outcome, policy)
    if accepting:
        lines.append(
            "Registered workflows that accept " + ("it" if single_input else "these inputs")
            + ", and what they produce instead: " + "; ".join(accepting) + "."
        )
    return lines, "no registered workflow"


def _title(number, reading, readings, task, user_data) -> str:
    quote = _quote(reading, [other for other in readings if other is not reading], task)
    if quote is not None:
        user_data.append(quote)
        return f'Reading {number} -- "{user_data_token(len(user_data) - 1)}"'
    granularity = _GRANULARITY_LABELS.get(reading.outcome.granularity, "")
    return f"Reading {number} -- " + " ".join(
        part for part in (granularity, _artifact_label(reading.outcome.artifact_type)) if part
    )


def render_hypothesis_routes(
    decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str,
) -> str | None:
    """The per-reading reply, or None when the existing reply already covers every reading."""
    if decision.action != "no_tool":
        return None
    readings = _readings(decision, policy)
    if not readings:
        return None
    # Only a no-tool reply reaches here, so every reading is matched as guidance.
    routes = [(reading, _candidates(task, reading, "guidance")) for reading in readings]
    splits = [_splits(task, reading) if not actions else [] for reading, actions in routes]
    several = len(readings) >= 2 and not _covered(decision, routes)
    # Log 252: one reading with no workflow of its own but a registered composition.
    composed = any(not actions and _composition(reading.outcome) for reading, actions in routes)
    if not several and not any(splits) and not composed:
        return None
    user_data: list[str] = []
    sections = [
        "Your request describes more than one scientific reading. Each is listed with "
        "the registered workflows that fit it, their algorithmic premises and inputs:"
        if len(readings) >= 2 else
        "No single registered workflow produces this result from all the stated inputs "
        "together. Each stated input is listed on its own, with the registered workflows "
        "that fit it, their algorithmic premises and inputs:"
        if any(splits) else
        "Here is how registered workflows can reach this result, with their algorithmic "
        "premises and inputs:"
    ]
    choices = []
    for number, ((reading, actions), split) in enumerate(zip(routes, splits), start=1):
        lines = [f"**{_title(number, reading, readings, task, user_data)}**"] if len(readings) >= 2 else []
        lines.append(_result_line(reading.outcome))
        prefix = f"{number}: " if len(readings) >= 2 else ""
        if split:
            lines.append("Each stated input on its own:")
            for value, input_actions in split:
                single = reading.outcome.model_copy(update={"input_artifacts": [value]})
                option, names = _option_lines(single, input_actions, policy, single_input=True)
                lines.append(f"- From the {_input_label(value)}:")
                lines.extend("  " + line for line in option)
                choices.append(f"{prefix}the {_input_label(value)} ({names})")
        else:
            option, names = _option_lines(reading.outcome, actions, policy, single_input=False)
            lines.extend(option)
            choices.append(f"{number} ({names})")
        sections.append("\n".join(lines))
    if len(readings) >= 2:
        question = ("Which reading should we start with: " + ", ".join(choices)
                    + "? If a reading should use different data, say which.")
    elif any(splits):
        question = ("Which should we start with: " + ", ".join(choices)
                    + "? If you meant a different result for one of the inputs, say which.")
    else:
        sources = [policy.workflows[action].workflow
                   for action, _ in _composition(readings[0].outcome).sources
                   if action in policy.workflows]
        question = ("Which per-sample profile should we start with: "
                    + ", ".join(sources[:-1]) + " or " + sources[-1] + "?")
    sections.append(question)
    sections.append(_NOT_INSPECTED)
    return _ui_text_with_user_data("\n\n".join(sections), user_data)
