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


def list_valued_assumptions(payload):
    """Wrap a single assumption the model wrote as a string into the declared list (Log 323).

    Like the move above, nothing is resolved or invented: the text is kept as
    the list's only item. A string here failed the whole first pass on schema,
    so the second call rewrote the interpretation from scratch instead of
    patching what was wrong; Test 2 then fell back where its successful runs,
    with the same semantic gaps, were patched.
    """
    if not isinstance(payload, Mapping):
        return payload, []
    result = deepcopy(dict(payload))
    notes = []
    if isinstance(result.get("assumptions"), str):
        result["assumptions"] = [result["assumptions"]]
        notes.append({"field": "assumptions", "from": "string", "to": "list"})
    for key in ("outcome_hypotheses", "outcome_hypothesis"):
        items = result.get(key)
        for index, item in enumerate(items if isinstance(items, list) else [items]):
            if isinstance(item, dict) and isinstance(item.get("assumptions"), str):
                item["assumptions"] = [item["assumptions"]]
                notes.append({"hypothesis_index": index, "field": "assumptions", "from": "string", "to": "list"})
    return result, notes


def normalize_semantic_shape(payload):
    """Every lossless shape fix, in order, with one record."""
    payload, moved = nest_unresolved_dimensions(payload)
    payload, wrapped = list_valued_assumptions(payload)
    return payload, [*moved, *wrapped]
