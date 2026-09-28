"""Normalize an unambiguous provider nesting error without changing any value."""

from collections.abc import Mapping
from copy import deepcopy


def nest_unresolved_dimensions(payload):
    """Move hypothesis metadata to its declared outcome field, then validate as usual.

    Do not resolve conflicts, discard unknown keys or correct biological values.
    A conflicting pair is deliberately left malformed for strict validation.
    """
    if not isinstance(payload, Mapping):
        return payload, []
    result = deepcopy(dict(payload))
    hypotheses = result.get("outcome_hypotheses")
    if not isinstance(hypotheses, list):
        single = result.get("outcome_hypothesis")
        hypotheses = [single] if isinstance(single, Mapping) else []
    notes = []
    for index, item in enumerate(hypotheses):
        if not isinstance(item, dict) or "unresolved_dimensions" not in item:
            continue
        outcome = item.get("outcome")
        if not isinstance(outcome, dict):
            continue
        value = item["unresolved_dimensions"]
        if "unresolved_dimensions" in outcome and outcome["unresolved_dimensions"] != value:
            continue
        outcome["unresolved_dimensions"] = item.pop("unresolved_dimensions")
        notes.append({"hypothesis_index": index, "field": "unresolved_dimensions",
                      "from": "hypothesis", "to": "outcome"})
    return result, notes
