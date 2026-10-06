"""Read one request's requirements once, from its full text (plan item 2).

Every stage used to re-read the request on its own: routing and the reply
read the last 6,000 characters, the planner and plan evaluator the whole
message, and a continuation turn only its own synthetic text. A value stated
at the start of a long request, or in the request a continuation carries on,
was therefore seen by some stages and not others. This module reads it once.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from ..contracts import TaskDecision
from ..contracts.requirements import RequestRequirements, StatedValue
from ..routing.authorization import read_operation_authorization
from ..routing_window import routing_window_parts
from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS, PARAMETER_FIELDS
from .input_bindings import request_input_bindings
from .request_parameters import extract_explicit_request_parameters

__all__ = [
    "carried_parameters", "read_request_requirements", "stated_in_text", "stated_path", "with_routing",
]


_SENTENCE_END = ".。,，;；:："


def stated_path(value: Any) -> Any:
    """A stated path as the planner reads it: no closing sentence punctuation."""
    return value.strip().rstrip(_SENTENCE_END) if isinstance(value, str) else value


def stated_in_text(text: str) -> dict[str, Any]:
    """Values the text states for request fields: labelled inputs, outputs, controls.

    The same parsers a CLI continuation uses for the request it carries, so a
    value is "stated" by one definition on every turn.
    """
    bindings = request_input_bindings(text)
    values: dict[str, Any] = {field: bindings.values[field] for field in bindings.explicit_fields}
    values.update(extract_explicit_request_parameters(text))
    return {
        field: stated_path(value) if field in INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS else value
        for field, value in values.items()
    }


def _span(text: str, value: Any) -> tuple[int, int] | None:
    if isinstance(value, str) and value and (start := text.find(value)) >= 0:
        return start, start + len(value)
    return None


def read_request_requirements(
    text: str, *, carried: Mapping[str, Any] | None = None,
) -> RequestRequirements:
    """Read *text* (the full message) plus values carried from the request it continues.

    A value this turn states replaces the carried one for the same field: the
    later statement is the user's correction.
    """
    window, omitted = routing_window_parts(text)
    this_turn = stated_in_text(text)
    stated = [
        StatedValue(field=field, value=value, origin="this_turn", span=_span(text, value))
        for field, value in this_turn.items()
    ]
    stated.extend(
        StatedValue(field=field, value=value, origin="earlier_turn")
        for field, value in (carried or {}).items()
        if field not in this_turn
    )
    return RequestRequirements(
        source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source_chars=len(text),
        routed_chars=len(window),
        omitted_chars=omitted,
        stated=stated,
        operations=read_operation_authorization(text),
    )


def with_routing(
    requirements: RequestRequirements, decision: TaskDecision, routing_state: Mapping[str, Any],
) -> RequestRequirements:
    """Record what routing read the goal to be and what it left open."""
    goal = (routing_state.get("semantic_goal") or {}).get("goal") or None
    outcome = decision.requested_outcome
    open_conditions = [
        *(f"unresolved:{dimension}" for dimension in (outcome.unresolved_dimensions if outcome else [])),
        *([f"question:{decision.clarification_question}"] if decision.clarification_question else []),
    ]
    return requirements.model_copy(update={
        "goal": goal, "open_conditions": open_conditions,
        "data_facts": decision.data_facts,
        "applicability": [item.model_dump() for item in decision.applicability],
        "data_plan": decision.data_plan.model_dump() if decision.data_plan is not None else None,
    })


def carried_parameters(requirements: Mapping[str, Any] | None) -> dict[str, Any]:
    """The stated values a continuation of this request carries, this turn first.

    Only request fields a WorkflowContinuation may hold; a value this turn
    states replaces one it had itself carried.
    """
    parameters: dict[str, Any] = {}
    for item in (requirements or {}).get("stated") or ():
        if item["field"] in INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS | PARAMETER_FIELDS and (
            item["origin"] == "this_turn" or item["field"] not in parameters
        ):
            parameters[item["field"]] = item["value"]
    return parameters
