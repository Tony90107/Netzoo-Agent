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

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text_with_user_data, user_data_token
from ..routing.outcome_matching import match_semantic_request
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


def _result_line(outcome) -> str:
    inputs = [_artifact_label(value) for value in outcome.input_artifacts if value != "unknown"]
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
            outputs = ", ".join(sorted(_artifact_label(a) for a in capability.produced_artifacts))
            found.append(f"**{spec.workflow}** ({outputs})")
    return sorted(set(found))


def _covered(decision: TaskDecision, routes: list[tuple]) -> bool:
    shown = set(decision.hypothesis_actions)
    return (
        decision.capability_match_status == "ambiguous"
        and len(shown) >= 2
        and all(actions and set(actions) <= shown for _, actions in routes)
    )


def render_hypothesis_routes(
    decision: TaskDecision, policy: ProjectPolicySnapshot, *, task: str,
) -> str | None:
    """The per-reading reply, or None when there is one reading or the reply covers all."""
    if decision.action != "no_tool":
        return None
    readings = _readings(decision, policy)
    if len(readings) < 2:
        return None
    # Only a no-tool reply reaches here, so every reading is matched as guidance.
    routes = [(reading, _candidates(task, reading, "guidance")) for reading in readings]
    if _covered(decision, routes):
        return None
    user_data: list[str] = []
    sections = [
        "Your request describes more than one scientific reading. Each is listed with "
        "the registered workflows that fit it, their algorithmic premises and inputs:"
    ]
    choices = []
    for number, (reading, actions) in enumerate(routes, start=1):
        quote = _quote(reading, [other for other in readings if other is not reading], task)
        if quote is not None:
            user_data.append(quote)
            title = f'Reading {number} -- "{user_data_token(len(user_data) - 1)}"'
        else:
            granularity = _GRANULARITY_LABELS.get(reading.outcome.granularity, "")
            title = f"Reading {number} -- " + " ".join(
                part for part in (granularity, _artifact_label(reading.outcome.artifact_type)) if part
            )
        lines = [f"**{title}**", _result_line(reading.outcome)]
        specs = [(action, policy.workflows[action]) for action in actions if action in policy.workflows]
        if specs:
            for action, spec in specs:
                lines.extend(_candidate_details(action, spec, policy))
            names = " or ".join(spec.workflow for _, spec in specs)
        else:
            lines.append(
                "No registered workflow produces this result from these inputs."
            )
            accepting = _accepting_workflows(reading.outcome, policy)
            if accepting:
                lines.append(
                    "Registered workflows that accept these inputs, and what they produce "
                    "instead: " + "; ".join(accepting) + "."
                )
            names = "no registered workflow"
        sections.append("\n".join(lines))
        choices.append(f"{number} ({names})")
    sections.append(
        "Which reading should we start with: " + ", ".join(choices) + "? "
        "If a reading should use different data, say which."
    )
    sections.append(_NOT_INSPECTED)
    return _ui_text_with_user_data("\n\n".join(sections), user_data)
