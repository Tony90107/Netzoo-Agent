"""The OpenAI strict-mode form of a pydantic JSON schema (Log 208).

In non-strict function calling gpt-4o-mini treats a JSON schema as advice:
Log 197 found schema-required fields left out 12 of 12 times, and the fallbacks
left under the current code were mostly second-call replies that broke the
schema -- explicit evidence without a quote, an evidence dimension spelled
`input_artifacts`, an out-of-vocabulary `unresolved_dimensions` entry. Strict
mode makes the provider emit only what the schema allows, but it requires
every object to list all of its properties as required, forbid extra ones and
carry no defaults.

`strict_json_schema` rewrites a schema that way without changing what
validation accepts: an optional field whose default is None becomes a
required, nullable field (null means the same as omitting it), any other
default becomes a required field of its own type, and `OutcomeEvidence`
becomes the two shapes it already validates as -- explicit with a quote, or
inferred without one -- as the claims contract's `Support` does.

Only the patch schema uses it (Log 208). The review schema was left
non-strict: strict mode rejects `RequestedOutcome`'s properties-beside-branches
form (the provider returned an empty object), and restating every field in
each of its 17 artifact branches more than doubled the review's input.
"""

from __future__ import annotations

import copy

__all__ = ["strict_json_schema"]

_MISSING = object()


def _nullable(prop: dict) -> dict:
    variants = prop.get("anyOf")
    if variants is not None:
        if not any(item.get("type") == "null" for item in variants):
            variants.append({"type": "null"})
        return prop
    return {"anyOf": [prop, {"type": "null"}]}


def _strict_objects(node) -> None:
    if isinstance(node, list):
        for item in node:
            _strict_objects(item)
        return
    if not isinstance(node, dict):
        return
    properties = node.get("properties")
    if isinstance(properties, dict):
        required = set(node.get("required", []))
        for name, prop in list(properties.items()):
            default = prop.pop("default", _MISSING)
            if name not in required and default is None:
                properties[name] = _nullable(prop)
        node["required"] = list(properties)
        node["additionalProperties"] = False
    node.pop("default", None)
    for value in node.values():
        _strict_objects(value)


def _evidence_variants(definition: dict) -> dict:
    """Explicit evidence carries a quote; inferred evidence carries none."""
    fields = {name: dict(prop) for name, prop in definition["properties"].items()}
    quote = {key: value for key, value in fields.pop("text_span").items() if key not in {"anyOf", "default"}}
    quote.update({"type": "string", "minLength": 1, "maxLength": 160})
    common = {name: prop for name, prop in fields.items() if name != "source"}

    def variant(source: str, extra: dict) -> dict:
        properties = {**common, "source": {"enum": [source], "type": "string"}, **extra}
        return {"type": "object", "properties": properties, "required": list(properties),
                "additionalProperties": False}

    return {
        "title": definition.get("title", "OutcomeEvidence"),
        "description": definition.get("description", ""),
        "anyOf": [variant("explicit", {"text_span": quote}), variant("inferred", {})],
    }


def strict_json_schema(schema: dict) -> dict:
    """A strict-mode copy of `schema` (a pydantic `model_json_schema()` result)."""
    schema = copy.deepcopy(schema)
    definitions = schema.get("$defs", {})
    evidence = definitions.pop("OutcomeEvidence", None)
    _strict_objects(schema)
    if evidence is not None:
        definitions["OutcomeEvidence"] = _evidence_variants(evidence)
    return schema
