"""Plumbing shared by every structured provider call in the routing pipeline.

Both the semantic interpreter and the intent router have to price a call before
making it and describe a Pydantic failure afterwards without echoing what the
provider sent. Holding these here is what lets those two stages live in separate
modules: each imports this, and neither imports the other.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import re

__all__: list[str] = []


def _serialized_structured_input(messages, schema_model) -> str:
    text = "\n".join(str(message.content) for message in messages)
    return text + json.dumps(
        schema_model.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )


# A rejected ontology literal is model vocabulary worth recording; free text may
# quote the request, so only identifier-shaped values are retained.
_IDENTIFIER_VALUE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")


def _validation_issue_types(error: BaseException) -> list[dict[str, object]]:
    """Return non-sensitive Pydantic issue locations, codes and shapes.

    The rejected value's type name records what shape a provider actually sent,
    which the September traces could not answer. Its content is kept only when it
    is a bare canonical-looking identifier, never as arbitrary request text.
    """
    errors = getattr(error, "errors", None)
    if not callable(errors):
        return []
    issues = []
    for issue in errors():
        value = issue.get("input")
        recorded = {
            "location": [str(item) for item in issue.get("loc", ())],
            "type": str(issue.get("type", "unknown")),
            "input_type": type(value).__name__,
        }
        if isinstance(value, str) and _IDENTIFIER_VALUE.fullmatch(value):
            recorded["input_value"] = value
        if isinstance(value, Mapping):
            # Field names an object was built from are model-chosen schema terms,
            # so they name the wrong shape without retaining any request content.
            recorded["input_keys"] = sorted(
                key for key in value
                if isinstance(key, str) and _IDENTIFIER_VALUE.fullmatch(key)
            )[:8]
        issues.append(recorded)
    return issues[:8]
