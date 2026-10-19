"""The slim reading calls (spec docs/superpowers/specs/2026-10-19-slim-reading-fields-design.md, section 2).

Step 1 reads A1-A4 and the stated C and D facts (`core_model`); step 2 is code (`slim_needs`); step 3 reads only the
B fields step 2 chose (`focus_model`), and runs only when it chose any. Each field is read once. Code checks every
quote and value (`from_core`, `merge_focus`). A core call that fails or does not decode gives a reading with status
`failed` (UNCHECKED); a failed focused call leaves the core reading, its B fields unread (asked, never refused).

Offline: nothing in the graph calls this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts import HumanMessage, SystemMessage
from ..contracts.slim_reading import SlimReading
from ..interpretation.menu_reader import ReadReport, name_key, request_layout
from ..interpretation.slim_reader import (
    Needs, core_model, core_text, focus_model, focus_text, from_core, merge_focus, slim_needs,
)
from ..settings import ROUTER_CONTEXT_MAX_CHARS
from .menu_reading_call import read_menu

__all__ = ["SlimRead", "build_core_messages", "build_focus_messages", "read_slim"]

_CORE_SHAPE = (
    "Return only the SlimCoreWire for the user's request: what the user said, read against the menu below. Write only "
    "what the words say; nothing is written for what they do not. Every quote and outside_name is the user's exact "
    "words, copied from the request."
)
_FOCUS_SHAPE = (
    "Return only the SlimFocusWire for the user's request. Each field below was chosen from the candidate workflows' "
    "contracts: give what the user's words say about it -- stated (the value), unsure (the user does not know, or "
    "gives several: values), or not_said. settings and counts list only what the words give. Every quote is the "
    "user's exact words, copied from the request."
)


def build_core_messages(user_task: str) -> list:
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    layout = request_layout(task)
    names = "\n".join(["Registered names in the request (names.<NAME>):",
                       *(f"- {name_key(name)} = {name}" for name in layout.names)]) if layout.names else ""
    return [SystemMessage(content=f"{_CORE_SHAPE}\n\n{core_text()}"),
            HumanMessage(content=f"Request:\n{task}" + (f"\n\n{names}" if names else ""))]


def build_focus_messages(user_task: str, slim: SlimReading, needs: Needs) -> list:
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    return [SystemMessage(content=f"{_FOCUS_SHAPE}\n\n{focus_text(needs, slim)}"),
            HumanMessage(content=f"Request:\n{task}")]


@dataclass
class SlimRead:
    """The two reads of one request: the reading code built, what code dropped, and what each call sent."""

    reading: SlimReading
    needs: Needs = field(default_factory=Needs)
    report: ReadReport = field(default_factory=ReadReport)
    focus_report: ReadReport = field(default_factory=ReadReport)
    core_payload: dict | None = None
    focus_payload: dict | None = None
    seconds: float = 0.0
    error: str = ""
    focus_error: str = ""
    raws: list = field(default_factory=list)


def read_slim(user_task: str, llm) -> SlimRead:
    """Step 1, step 2, and step 3 when step 2 chose any B field."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    layout = request_layout(task)
    core = read_menu(task, llm, messages=build_core_messages(task), schema=core_model(layout.names),
                     convert=lambda data, words: from_core(data, words, layout))
    if core.error:
        return SlimRead(reading=SlimReading(status="failed"), seconds=core.seconds, error=core.error)
    read = SlimRead(reading=core.reading, report=core.report, core_payload=core.payload, seconds=core.seconds,
                    raws=[core.raw])
    read.needs = slim_needs(core.reading, task)
    if not read.needs.runs:
        return read
    focus = read_menu(task, llm, messages=build_focus_messages(task, core.reading, read.needs),
                      schema=focus_model(read.needs),
                      convert=lambda data, words: merge_focus(core.reading, data, words, read.needs))
    read.seconds = round(read.seconds + focus.seconds, 1)
    read.raws.append(focus.raw)
    if focus.error:
        read.focus_error = focus.error
        return read
    read.reading, read.focus_report, read.focus_payload = focus.reading, focus.report, focus.payload
    return read
