"""jev-first-links phase A: the frozen Jev question and menu (ROUND.md). Never reworded after a run."""
from __future__ import annotations

INSTRUCTIONS = ("Which registered result gives what the quoted part of the request asks for, as it asks it? Choose "
                "the one listed result that gives it; choose none when no listed result gives it.")
NONE = {"none": "None of these registered results gives what the quoted part asks for."}


def menu() -> tuple[dict[str, str], dict[str, str]]:
    """(option -> text, option -> sheet entry id): one option per produces entry of the capability sheet."""
    from netzoo_agent_core.capability_sheet import sheet_entries

    produces = [found for found in sheet_entries().values() if found.kind == "produces"]
    options = {f"e{index}": f"{found.workflow}: {found.text}" for index, found in enumerate(produces, 1)}
    ids = {f"e{index}": found.id for index, found in enumerate(produces, 1)}
    return options | NONE, ids


def state(task: str, quote: str) -> str:
    return f"User request:\n{task}\n\nThe part that asks for the result: {quote}"
