"""The closed-menu reading call (spec 2026-10-18, section 3.1; phase 1): one structured call that fills `MenuReading`.

The system message describes the output shape and shows the closed menu (`interpretation.menu_reader.menu_text`).
The user message is the request, then its sentences and the numbers in it as code finds them; the strict schema has
one field per sentence and per number, so none is skipped. Code checks every quote and builds the reading
(`menu_reader.to_menu_reading`). A call that fails or does not decode gives a reading with status `failed`, which
`decide_menu` turns into UNCHECKED.

Phase 1: offline only. Nothing in the graph calls this module.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..contracts import HumanMessage, SystemMessage
from ..contracts.menu_reading import MenuReading
from ..interpretation.menu_reader import (
    ReadReport, layout_text, menu_text, reader_model, request_layout, to_menu_reading,
)
from ..interpretation.semantic_repair import semantic_payload
from ..settings import ROUTER_CONTEXT_MAX_CHARS

__all__ = ["MenuRead", "build_menu_reading_messages", "menu_reading_system", "read_menu"]

_SHAPE = (
    "Return only the MenuReadingWire for the user's request: what the user said, field by field, read against the "
    "closed menu below. It records what the words say, never whether anything can be done.\n\n"
    "Each field has a status: stated -- the user says it outright (basis explicit), or words as clear as saying it "
    "imply it (basis implied, quoting those words); not_stated -- nothing in the words says it (value null, values "
    "empty, quote empty); unsure -- the user says they do not know or have not decided (values: the options the "
    "words leave open); conflicting -- the words say two different things (values: both). Every quote and "
    "outside_name is the user's exact words, copied from the request. sentences.sN and numbers.nN answer for the "
    "sentences and numbers listed after the request, one each."
)


def menu_reading_system() -> str:
    return f"{_SHAPE}\n\n{menu_text()}"


def build_menu_reading_messages(user_task: str) -> list:
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    return [SystemMessage(content=menu_reading_system()),
            HumanMessage(content=f"Request:\n{task}\n\n{layout_text(request_layout(task))}")]


@dataclass
class MenuRead:
    """One reading call: the reading code built, what code dropped, and what the provider sent."""

    reading: MenuReading
    report: ReadReport = field(default_factory=ReadReport)
    payload: dict | None = None
    seconds: float = 0.0
    error: str = ""
    raw: object = None


def read_menu(user_task: str, llm, *, messages=None, schema=None, convert=None) -> MenuRead:
    """Read the request once. `llm` is a chat model (gpt-4o-mini by default, through `llm.build_llm`); `messages`,
    `schema` and `convert` default to this module's (the focused re-read passes its own)."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    layout = request_layout(task)
    schema = schema or reader_model(len(layout.sentences), len(layout.numbers))
    messages = messages or build_menu_reading_messages(task)
    convert = convert or (lambda data, words: to_menu_reading(data, words, layout))
    started = time.time()
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
        schema.model_validate(data)
    except Exception as error:  # a call that fails or does not decode is a failed reading, never a guess
        return MenuRead(reading=MenuReading(status="failed"), seconds=round(time.time() - started, 1),
                        error=f"{type(error).__name__}: {str(error)[:200]}")
    reading, report = convert(data, task)
    return MenuRead(reading=reading, report=report, payload=data, seconds=round(time.time() - started, 1), raw=raw)
