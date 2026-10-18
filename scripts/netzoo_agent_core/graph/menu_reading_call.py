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
from ..interpretation.menu_decision import candidate_workflows, decide_menu
from ..interpretation.menu_focus import focus_model, focus_text, merge_focused
from ..interpretation.menu_intent import intent_model, intent_questions, intent_text, merge_intent
from ..interpretation.menu_requirements import apply_verdicts, requirement_model, requirement_pairs, requirement_text
from ..interpretation.semantic_repair import semantic_payload
from ..settings import ROUTER_CONTEXT_MAX_CHARS

__all__ = ["MAX_FOCUS", "MenuRead", "build_focused_messages", "build_menu_reading_messages", "menu_reading_system",
           "read_focused", "read_intent", "read_menu", "read_requirements"]

MAX_FOCUS = 6
"""More candidates than this means the result is still open: the focused re-read waits for it."""

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


_FOCUS_SHAPE = (
    "Return only the FocusedReading for the user's request. The workflows below are the candidates its first reading "
    "left. For each listed control, count, kind of data and data condition, give what the user's words say about "
    "it: stated (the value the words give), unsure (the user does not know, has not decided, or gives several "
    "possibilities: values), or not_mentioned. Every quote is the user's exact words, copied from the request."
)


_REQUIREMENT_SHAPE = (
    "Return only the RequirementVerdicts structure. Each numbered pair gives a requirement from the user's request "
    "and one registered workflow, whose contract is listed. For each pair, copy the clause of that workflow's "
    "contract that speaks to the requirement, in its exact words (empty when none does), then say whether the "
    "contract says the workflow's result meets the requirement, contradicts it, or does not address it."
)


_INTENT_SHAPE = (
    "Return only the IntentProbe structure. Each numbered question asks what the user's request says about one "
    "thing. For each, copy the request's exact words that say it (empty when nothing does), then give the option "
    "those words say, or not_said when the words do not say it."
)


def menu_reading_system() -> str:
    return f"{_SHAPE}\n\n{menu_text()}"


def build_menu_reading_messages(user_task: str) -> list:
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    return [SystemMessage(content=menu_reading_system()),
            HumanMessage(content=f"Request:\n{task}\n\n{layout_text(request_layout(task))}")]


def build_focused_messages(user_task: str, candidates: tuple[str, ...]) -> list:
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    return [SystemMessage(content=f"{_FOCUS_SHAPE}\n\n{focus_text(candidates)}"),
            HumanMessage(content=f"Request:\n{task}")]


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
    schema = schema or reader_model(len(layout.sentences), len(layout.numbers), layout.names)
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


def read_focused(user_task: str, first: MenuReading, llm) -> tuple[MenuRead | None, tuple[str, ...]]:
    """The focused re-read of the first reading's candidates (phase 1, step 4), merged into it.

    None when there is nothing to focus on: a failed first reading, a result still open (CLARIFY), no candidates or
    more than `MAX_FOCUS`. A failed focused call leaves the first reading as it was, with the error recorded.
    """
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    if first.status == "failed" or decide_menu(first, task).kind == "CLARIFY":
        return None, ()
    candidates = tuple(candidate_workflows(first, task))
    if not candidates or len(candidates) > MAX_FOCUS:
        return None, candidates
    read = read_menu(task, llm, messages=build_focused_messages(task, candidates), schema=focus_model(candidates),
                     convert=lambda data, words: merge_focused(first, data, words, candidates))
    if read.reading.status == "failed":
        read.reading = first
    return read, candidates


def read_requirements(user_task: str, reading: MenuReading, llm):
    """The requirement contract check (phase 1b, step 1): a verdict per (requirement, candidate workflow), merged into
    the reading. None when no thing asked carries a requirement or nothing is a candidate; a failed call leaves the
    reading as it was (every requirement not addressed, so asked)."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    if reading.status == "failed":
        return None, []
    pairs = requirement_pairs(reading, candidate_workflows(reading, task))
    if not pairs:
        return None, []
    messages = [SystemMessage(content=_REQUIREMENT_SHAPE), HumanMessage(content=requirement_text(task, pairs))]
    read = read_menu(task, llm, messages=messages, schema=requirement_model(len(pairs)),
                     convert=lambda data, words: apply_verdicts(reading, pairs, data))
    if read.reading.status == "failed":
        read.reading = reading
    return read, pairs


def read_intent(user_task: str, reading: MenuReading, llm):
    """The focused intent probe (phase 1b variant): one closed question per intent that changes the call, merged by
    `merge_intent`. None when no intent changes the call; a failed call leaves the reading as it was."""
    task = user_task[-ROUTER_CONTEXT_MAX_CHARS:]
    if reading.status == "failed":
        return None, []
    questions = intent_questions(reading, task)
    if not questions:
        return None, []
    messages = [SystemMessage(content=_INTENT_SHAPE), HumanMessage(content=intent_text(task, questions))]
    schema = intent_model(tuple((q.dimension, q.values) for q in questions))
    read = read_menu(task, llm, messages=messages, schema=schema,
                     convert=lambda data, words: merge_intent(reading, questions, data, words))
    if read.reading.status == "failed":
        read.reading = reading
    return read, questions
