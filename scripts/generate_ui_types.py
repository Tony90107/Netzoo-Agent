#!/usr/bin/env python3
"""Emit the desktop UI's TypeScript types from the Pydantic contracts.

The window and the agent have to agree on the shape of a plan, a view and a
trace event. Writing those twice meant they only agreed until someone forgot,
and during M3 three fields had to be mirrored by hand.

This walks the models rather than their JSON Schema. ``RequestedOutcome``
installs a ``__get_pydantic_json_schema__`` hook that expands into one
conditional branch per artifact type, which is the right thing for steering a
provider and the wrong thing to turn into an interface.

Run ``python scripts/generate_ui_types.py`` after changing a contract;
``tests/test_ui_contract_sync.py`` fails if the committed file is stale.
"""

from __future__ import annotations

import datetime as dt
import sys
import types
import typing
import uuid
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pydantic import BaseModel  # noqa: E402

from netzoo_agent_core.contracts.decisions import PreferenceProposal  # noqa: E402
from netzoo_agent_core.contracts.planning import (  # noqa: E402
    InputBundleOption,
    InputEvidence,
    WorkflowPlan,
    WorkflowStep,
)
from netzoo_agent_core.contracts.state import LLMUsage, NextTurnPrompt  # noqa: E402
from netzoo_agent_core.server.protocol import ViewPayload  # noqa: E402
from netzoo_agent_core.trace_contracts import TraceEvent  # noqa: E402

OUTPUT = (
    SCRIPTS_DIR.parent / "desktop" / "src" / "generated" / "contracts.ts"
)

# Roots only; everything they reference is emitted with them.
ROOTS: tuple[type[BaseModel], ...] = (
    ViewPayload,
    WorkflowPlan,
    InputEvidence,
    InputBundleOption,
    WorkflowStep,
    PreferenceProposal,
    NextTurnPrompt,
    LLMUsage,
    TraceEvent,
)

_SCALARS: dict[object, str] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    uuid.UUID: "string",
    dt.datetime: "string",
    dt.date: "string",
    type(None): "null",
    typing.Any: "unknown",
}


class Unsupported(TypeError):
    """A contract used a shape this emitter cannot express honestly."""


def _literal(annotation: object) -> str:
    values = typing.get_args(annotation)
    return " | ".join(
        "null" if value is None else f'"{value}"' if isinstance(value, str) else str(value)
        for value in values
    )


def _render(annotation: object, collected: list[type[BaseModel]]) -> str:
    if annotation in _SCALARS:
        return _SCALARS[annotation]
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        _collect(annotation, collected)
        return annotation.__name__
    if isinstance(annotation, type) and issubclass(annotation, dt.datetime):
        return "string"

    # A bare `dict` or `list` carries no element type. Say `unknown` rather
    # than inventing one: these are the free-form payloads (`decision`,
    # `arguments`, a trace event's `payload`) whose shape varies by node.
    if annotation is dict:
        return "Record<string, unknown>"
    if annotation is list:
        return "unknown[]"

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Literal:
        return _literal(annotation)
    if origin in (typing.Union, types.UnionType):
        parts = [_render(arg, collected) for arg in args]
        # Keep `| null` last so the common case reads first.
        ordered = [p for p in parts if p != "null"] + [p for p in parts if p == "null"]
        return " | ".join(dict.fromkeys(ordered))
    if origin in (list, set, frozenset, tuple):
        if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
            args = (args[0],)
        inner = " | ".join(dict.fromkeys(_render(arg, collected) for arg in args))
        return f"({inner})[]" if "|" in inner else f"{inner}[]"
    if origin is dict:
        key, value = args
        if _render(key, collected) != "string":
            raise Unsupported(f"dict keys must be strings, got {key!r}")
        return f"Record<string, {_render(value, collected)}>"

    raise Unsupported(f"cannot express {annotation!r} in TypeScript")


def _collect(model: type[BaseModel], collected: list[type[BaseModel]]) -> None:
    if model in collected:
        return
    collected.append(model)


def _interface(model: type[BaseModel], collected: list[type[BaseModel]]) -> str:
    lines: list[str] = []
    doc = (model.__doc__ or "").strip().splitlines()
    if doc:
        lines.append("/** " + doc[0].strip() + " */")
    lines.append(f"export type {model.__name__} = {{")
    hints = typing.get_type_hints(model)
    for name, field in model.model_fields.items():
        rendered = _render(hints[name], collected)
        description = (field.description or "").strip().splitlines()
        if description:
            lines.append(f"  /** {description[0].strip()} */")
        lines.append(f"  {name}: {rendered};")
    lines.append("};")
    return "\n".join(lines)


def generate() -> str:
    collected: list[type[BaseModel]] = []
    for root in ROOTS:
        _collect(root, collected)

    # _interface appends newly referenced models, so walk by index.
    bodies: list[str] = []
    index = 0
    while index < len(collected):
        bodies.append(_interface(collected[index], collected))
        index += 1

    header = (
        "/**\n"
        " * Generated from the Pydantic contracts. Do not edit.\n"
        " *\n"
        " * Regenerate with `python scripts/generate_ui_types.py`;\n"
        " * `tests/test_ui_contract_sync.py` fails if this file is stale.\n"
        " */\n"
    )
    return header + "\n" + "\n\n".join(bodies) + "\n"


def main() -> int:
    text = generate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"{'unchanged' if previous == text else 'wrote'} {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
