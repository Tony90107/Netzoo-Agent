"""Jev's link of each asked result to one capability-sheet entry (docs/research-log/jev-links-first-2026-10-29): the
pure part.

The reading (gpt-4o-mini) links each ask to the entries that deliver it (`delivered_by`), and most of the remaining
errors were that link (X10/W20 to LIONESS, h5's registry linking). Jev picks one entry from a closed menu of the
sheet's produces entries; phase A (`jev-first-links-2026-10-29`, 433 recorded readings) took the pick when Jev was at
least 0.7 confident: gold-DO results credited right 101 -> 120 of 168, false accepts 40 -> 42, confident picks right
184/194. Jev only links: every condition is still judged by code and the checks after it, as before.

This module holds the frozen question, the menu and the rule. The call (I/O, flag, record) is
`graph.jev_links_first_call`.
"""
from __future__ import annotations

__all__ = ["INSTRUCTIONS", "NONE", "THRESHOLD", "linked", "menu", "pick", "state"]

# Frozen with phase A (jev-first-links-2026-10-29/jev_link_menu.py); never reworded after a run.
INSTRUCTIONS = ("Which registered result gives what the quoted part of the request asks for, as it asks it? Choose "
                "the one listed result that gives it; choose none when no listed result gives it.")
NONE = {"none": "None of these registered results gives what the quoted part asks for."}
THRESHOLD = 0.7
"""Jev's pick replaces the reading's link at this confidence or above (phase A: 184/194 right)."""


def menu() -> tuple[dict[str, str], dict[str, str]]:
    """(option -> text, option -> sheet entry id): one option per produces entry of the capability sheet."""
    from ..capability_sheet import sheet_entries

    produces = [found for found in sheet_entries().values() if found.kind == "produces"]
    options = {f"e{index}": f"{found.workflow}: {found.text}" for index, found in enumerate(produces, 1)}
    ids = {f"e{index}": found.id for index, found in enumerate(produces, 1)}
    return options | NONE, ids


def state(task: str, quote: str) -> str:
    return f"User request:\n{task}\n\nThe part that asks for the result: {quote}"


def pick(read: dict) -> list[str] | None:
    """The entries a read links (none -> []), or None when the read is an error or under the threshold."""
    if "error" in read or read.get("confidence", 0) < THRESHOLD:
        return None
    ids = menu()[1]
    return [ids[read["choice"]]] if read.get("choice") in ids else []


def linked(proposal, reads: dict[str, dict]):
    """The reading with each ask's `delivered_by` replaced by Jev's confident pick (`reads`: ask quote -> read)."""
    updates = {}
    for name in type(proposal).model_fields:
        sentence = getattr(proposal, name)
        if not name[1:].isdigit() or not getattr(sentence, "asks", None):
            continue
        asks = [ask.model_copy(update={"delivered_by": found}) if (found := pick(reads.get(ask.quote, {"error": ""})))
                is not None else ask for ask in sentence.asks]
        if asks != list(sentence.asks):
            updates[name] = sentence.model_copy(update={"asks": asks})
    return proposal.model_copy(update=updates) if updates else proposal
