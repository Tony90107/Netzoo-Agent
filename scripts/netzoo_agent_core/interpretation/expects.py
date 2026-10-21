"""ROUND-14: what each workflow takes its input to be already (the capability sheet's `expects`), one line each from its
own contract, and the one judgement code makes from them.

Words naming a single boolean control an expectation is tied to, by the control's own name, and stating its opposite
value ("raw counts, not log-transformed" for BONOBO) do not meet that workflow: the condition check's answer is
violates, given by code and never asked. Words naming none, or several, are left to the check; code never says one is
met (a sentence may add demands no expectation covers).

Measured and not adopted (research-log usage-fields-2026-10-21): showing these lines to the condition check, and each
workflow's near misses to the second opinion. On 185 recorded calls re-asked of gpt-4o-mini, the lines moved answers
toward refusal (second opinion all->part 34, part->none 31, the reverse 11; condition satisfies->violates 10, the
reverse 4), against unrelated words too ("all using the same gene symbols" violated PANDA's "Normalization and batch
correction are done before PANDA"); decisions right on 130 labelled readings: 101 without, 99 with.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import yaml

from workflow_registry import ACTION_DEFINITIONS

from ..capability_sheet import SHEET_PATH

__all__ = ["Expectation", "code_answer", "expectations", "stated_opposite"]


@dataclass(frozen=True, slots=True)
class Expectation:
    id: str
    action: str
    workflow: str
    state: str
    source: str
    control: str | None = None
    value: bool | None = None


@lru_cache(maxsize=1)
def _all() -> dict[str, tuple[Expectation, ...]]:
    data = yaml.safe_load(SHEET_PATH.read_text(encoding="utf-8"))
    found: dict[str, tuple[Expectation, ...]] = {}
    seen: set[str] = set()
    for workflow, spec in (data.get("workflows") or {}).items():
        action = spec.get("action")
        items = []
        for raw in spec.get("expects") or []:
            key, state, source = raw.get("id"), " ".join(str(raw.get("state", "")).split()), raw.get("source")
            if not key or key in seen or not state or not source:
                raise ValueError(f"capability sheet: expectation {key!r} needs a unique id, a state and a source")
            seen.add(key)
            control, value = raw.get("control"), raw.get("value")
            if control is not None:
                controls = {item.name: item for item in ACTION_DEFINITIONS[action].controls}
                if control not in controls or controls[control].control_type != "boolean" or not isinstance(value, bool):
                    raise ValueError(f"capability sheet: expectation {key} names no boolean control of {workflow} "
                                     f"with a true/false value")
            items.append(Expectation(key, action, workflow, state, str(source), control, value))
        if items:
            found[action] = tuple(items)
    return found


def expectations(action: str) -> tuple[Expectation, ...]:
    return _all().get(action, ())


def stated_opposite(action: str, words: str) -> Expectation | None:
    """The expectation the words state the opposite of, by the name of the one control they name; None otherwise."""
    from ..workflow_conditions import _tokens, conditions_for, control_boolean_value

    tied = [item for item in expectations(action) if item.control is not None]
    if not tied or not words.strip():
        return None
    conditions = conditions_for(tied[0].workflow)
    tokens = _tokens(words)
    named = [item for item in tied
             if {token for token in _tokens(item.control.replace("_", " ")) if len(token) > 3} & tokens]
    if len(named) != 1 or conditions is None:
        return None
    item = named[0]
    value = control_boolean_value(conditions.settings[item.control], words, words)
    return item if value is not None and value != item.value else None


def code_answer(workflow: str, stated: str) -> str | None:
    """The condition check's answer code gives for (workflow, stated requirement): violates, or None to ask."""
    action = next((items[0].action for items in _all().values() if items[0].workflow == workflow), None)
    return "violates" if action and stated_opposite(action, stated) else None
