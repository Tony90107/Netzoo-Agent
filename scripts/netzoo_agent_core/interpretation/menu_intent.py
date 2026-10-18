"""The focused intent probe (closed-menu phase 1b variant; the user's decision, 2026-10-18).

The user's words: an intent field that changes the call is found by code, the model answers one small question about
it with the request's own words, and when the two reads disagree the user is asked. Measured as its own arm, beside
the first read and the first read with the focused limit re-read.

After the first read and the focused re-read, `menu_decision.deciding_intents` finds the intents -- result (or a choice
between workflows), integration, granularity, regulators, layers -- whose menu values lead a thing asked to different
calls. Each becomes one closed question whose options are that intent's menu values (with the defaults table's
user-facing labels) and `not_said`; the answer quotes the request, and code checks the quote. `merge_intent` (pure
code) then sets each probed intent:

- the probe agrees with a stated value -> kept;
- it names another value, gives no verified words, or says not_said where the first read stated a value -> unclear:
  conflicting with both values in play (with no second value, every value of the intent; for the result, the result
  is left open), so the user is asked -- an intent is never assumed;
- the first read did not state it and the probe gives a value with verified words -> that value, basis explicit.

Phase 1b: offline only; nothing in the live path calls it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..contracts.menu_reading import MenuReading, Said, Wanted
from ..judgment_defaults import judgment_defaults
from .menu_decision import deciding_intents, intent_values
from .menu_reader import ReadReport, _strict, quote_in

__all__ = ["NOT_SAID", "IntentQuestion", "intent_model", "intent_questions", "intent_text", "merge_intent"]

NOT_SAID = "not_said"
CHOICE = "choice_between_workflows"
"""A result-question option: the user is choosing between workflows and names no result (step 2's value)."""
_FORBID = ConfigDict(extra="forbid")
_TOPIC = {
    "artifact": "Which result the user asks for",
    "integration": "Whether the user wants one network joining the omics layers or a separate one per layer",
    "granularity": "Whether the user wants one result for all samples, one per group, or one per sample",
    "regulators": "Which regulators the user wants in the network",
    "layers": "How many omics layers the user wants modeled together",
}
_LAYERS = {"two": "Exactly two omics layers in one model.",
           "three_or_more_jointly": "Three or more omics layers, all in one model."}


@dataclass(frozen=True, slots=True)
class IntentQuestion:
    item: int
    dimension: str
    values: tuple[str, ...]
    quote: str = ""
    """The words of the thing asked, shown with the question when the request asks for more than one thing."""


def _label(dimension: str, value: str) -> str:
    table = judgment_defaults()
    if dimension == "artifact":
        if value in table.artifacts:
            return table.artifacts[value].means
        if value in table.generic:
            return f"Only a kind of result, \"{value}\", without saying which."
        if value == CHOICE:
            return "The user is choosing between workflows and names no result."
        return "A result NetZoo does not give."
    if dimension == "layers":
        return _LAYERS.get(value, value)
    options = table.dimensions[dimension].options
    return options.get(value) or ("Something NetZoo does not give." if value == "off_menu" else value)


def intent_questions(reading: MenuReading, task: str) -> list[IntentQuestion]:
    """One question per intent that changes the call."""
    found = []
    for item, dimension in deciding_intents(reading, task):
        quote = reading.wanted[item].quote if item < len(reading.wanted) else ""
        values = (*intent_values(dimension), CHOICE) if dimension == "artifact" else intent_values(dimension)
        found.append(IntentQuestion(item, dimension, values, quote))
    return found


def intent_text(task: str, questions: list[IntentQuestion]) -> str:
    several = len({q.item for q in questions}) > 1
    lines = [f"Request:\n{task}", "", "Questions:"]
    for n, question in enumerate(questions, 1):
        about = f' (about: "{question.quote}")' if several and question.quote else ""
        lines.append(f"q{n}. {_TOPIC[question.dimension]}{about}. Options:")
        lines += [f"  - {value}: {_label(question.dimension, value)}" for value in question.values]
        lines.append(f"  - {NOT_SAID}: the words do not say it.")
    return "\n".join(lines)


@lru_cache(maxsize=64)
def intent_model(questions: tuple[tuple[str, tuple[str, ...]], ...]) -> type[BaseModel]:
    """One field per question: the request's words, then one of its options (strict mode)."""
    fields = {}
    for n, (dimension, values) in enumerate(questions, 1):
        answer = create_model(
            f"IntentAnswer{n}", __config__=_FORBID,
            quote=(str, Field(description="The request's exact words that say it; empty when nothing does.")),
            answer=(Literal[(*values, NOT_SAID)], Field(description="The option those words say; not_said when the "  # type: ignore[valid-type]
                                                                    "words do not say it.")),
        )
        fields[f"q{n}"] = (answer, Field(description=_TOPIC[dimension]))
    return _strict(create_model("IntentProbe", __config__=_FORBID, **fields))


def _all_values(dimension: str, first: str) -> list[str]:
    return list(dict.fromkeys([first, *intent_values(dimension)]))


def merge_intent(reading: MenuReading, questions: list[IntentQuestion], payload, task: str
                 ) -> tuple[MenuReading, ReadReport]:
    """The reading with each probed intent kept, made unclear, or filled (see the module docstring); report lines
    start with `agree`, `unclear` or `adopted`, or `kept not stated`."""
    raw = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else dict(payload)
    report = ReadReport()
    wanted = [item.model_copy(deep=True) for item in reading.wanted]
    for n, question in enumerate(questions, 1):
        answer = raw.get(f"q{n}") or {}
        value, quote = answer.get("answer") or NOT_SAID, answer.get("quote") or ""
        verified = value != NOT_SAID and quote_in(quote, task)
        if question.item >= len(wanted):  # the result the request left unnamed: filled only by verified words
            if not verified:
                report.filled.append(f"kept not stated: q{n} {question.dimension}")
                continue
            wanted.append(Wanted(quote=quote))
        item = wanted[question.item]
        first: Said = getattr(item, question.dimension)
        where = f"q{n} {question.dimension}"
        if question.dimension == "artifact" and value == CHOICE and verified:
            # A choice between workflows leaves the result open: asked as the goal, whatever the first read said.
            said = Said(status="unsure", values=[], quotes=[quote])
            report.filled.append(f"{'unclear' if first.status == 'stated' else 'adopted'}: {where} = {CHOICE}"
                                 + (f" (first {first.value})" if first.status == "stated" else ""))
        elif first.status == "stated":
            if verified and value == first.value:
                report.filled.append(f"agree: {where} = {value}")
                continue
            if question.dimension == "artifact" and not (verified and value != first.value):
                said = Said(status="unsure", values=[], quotes=first.quotes)  # the result is left open and asked
            else:
                values = [first.value, value] if verified else _all_values(question.dimension, first.value)
                said = Said(status="conflicting", values=values, quotes=[*first.quotes, *([quote] if verified else [])])
            report.filled.append(f"unclear: {where} first {first.value}, probe {value}"
                                 f"{'' if verified or value == NOT_SAID else ' (words not in the request)'}")
        elif verified:
            said = Said(status="stated", value=value, basis="explicit", quotes=[quote])
            report.filled.append(f"adopted: {where} = {value}")
        else:
            report.filled.append(f"kept not stated: {where}" + ("" if value == NOT_SAID else
                                                                 f" (probe {value}, words not in the request)"))
            continue
        wanted[question.item] = item.model_copy(update={question.dimension: said})
    return reading.model_copy(update={"wanted": wanted}), report
