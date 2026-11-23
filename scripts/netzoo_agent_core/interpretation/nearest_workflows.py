"""couldn't-match-2026-11-18: on a refusal, the nearest of the six main workflows, by code.

The user (2026-11-18) works with six packages -- PANDA, LIONESS, SCORPION, SPONGE, PORCUPINE, SNAIL -- and asked that
a full gap name the closest of them, so a misread refusal (live r1 B3: per-patient TF networks refused, the reading
had linked LIONESS-PANDA) still leads back to the workflow. SPONGE and SNAIL are preparation steps, not workflows a
request is checked against, so the run workflows are PANDA, the LIONESS family, SCORPION and PORCUPINE.

Every sentence is built in code and says only what the system did: which workflow the reading linked the user's words
to before the check (which did not confirm it), or which takes the kind of data the user described, and what that
workflow produces in its own registry words. The call is never changed and nothing is credited.
"""

from __future__ import annotations

import re

__all__ = ["CONFIRMED_CHOICE", "MAIN_WORKFLOWS", "is_main", "nearest_line", "reading_links"]

MAIN_WORKFLOWS = ("PANDA", "SCORPION", "PORCUPINE")  # plus every LIONESS-X
# repeat-questions-2026-11-18: the task a picked option becomes (`engine.choices.confirmed_outcome_task`). The user
# chose that workflow, so the turn is a choice, not a new request: no capability check, study purpose or Jev read of
# the marker text (3 of 4 recorded such turns asked "Did you mean X's result?" right after the user picked X).
CONFIRMED_CHOICE = "CONFIRMED_OUTCOME_ACTION="
MAX_NAMED = 3


def is_main(workflow: str) -> bool:
    return workflow in MAIN_WORKFLOWS or workflow.startswith("LIONESS-")


def reading_links(proposal) -> dict[str, list[str]]:
    """{asked sentence: sheet entries the reading linked it to}, from the proposal's sentence readings."""
    links: dict[str, list[str]] = {}
    data = proposal.model_dump() if hasattr(proposal, "model_dump") else dict(proposal or {})
    for key, value in data.items():
        if not re.fullmatch(r"s\d+", key) or not isinstance(value, dict):
            continue
        for ask in value.get("asks") or []:
            entries = [entry for entry in ask.get("delivered_by") or [] if entry]
            if ask.get("quote") and entries:
                links.setdefault(ask["quote"], [])
                links[ask["quote"]] += [entry for entry in entries if entry not in links[ask["quote"]]]
    return links


def _workflow(entry_key: str) -> str | None:
    """The workflow a produces entry belongs to; a near-miss entry ("panda.no_sign": what PANDA does not give) names
    none (live ns R03 had listed PANDA for a sign request through it)."""
    from ..capability_sheet import sheet_entries

    found = sheet_entries().get(entry_key)
    return found.workflow if found is not None and found.kind == "produces" else None


def _gives(name: str) -> str:
    """What the workflow produces: its first direct produces entry, verbatim, cut at a word boundary."""
    from ..capability_sheet import sheet_entries
    from ..method_names import registered_workflows
    from ..reply_cards.phrases import clip

    action = registered_workflows().get(name)
    texts = [item.text for item in sheet_entries().values()
             if item.kind == "produces" and item.action == action and item.level == "direct"]
    text = clip(texts[0], 160).rstrip(".") if texts else ""
    return f" ({text[:1].lower()}{text[1:]})" if text else ""


def _linked_main(check) -> list[str]:
    """Main workflows the reading linked an unavailable result's words to (the check did not confirm them)."""
    if check is None or not check.linked:
        return []
    unavailable = [item.quote for item in check.results() if item.status == "not_available"]
    names = []
    for quote, entries in check.linked.items():
        if not any(quote in asked or asked in quote for asked in unavailable):
            continue
        for key in entries:  # several entries of one workflow name it once (live ns R03: "PANDA ...; PANDA ...")
            if (name := _workflow(key)) and is_main(name) and name not in names:
                names.append(name)
    return names[:MAX_NAMED]


def _data_main(decision) -> list[str]:
    """Main workflows that take the kind of data the request describes (the reading's input types)."""
    from workflow_registry import OUTPUT_CAPABILITIES, workflow_name

    stated = {*decision.guidance_input_artifacts,
              *(artifact for hypothesis in decision.outcome_hypotheses for artifact in hypothesis.outcome.input_artifacts)}
    stated -= {"unknown"}
    if not stated:
        return []
    names = [workflow_name(action) for action, capability in OUTPUT_CAPABILITIES.items()
             if capability.input_artifacts & stated]
    return [name for name in dict.fromkeys(names) if is_main(name)][:MAX_NAMED]


def nearest_line(decision) -> str:
    """The nearest-main-workflow sentence for a refusal's reply, or "" when code finds none."""
    if decision is None:
        return ""
    linked = _linked_main(decision.capability_check)
    if linked:
        named = "; ".join(f"**{name}**{_gives(name)}" for name in linked)
        return (f"Nearest of NetZoo's main workflows: {named}. Your words were first linked to "
                f"{'it' if len(linked) == 1 else 'them'}, but the check did not confirm that "
                f"{'it gives' if len(linked) == 1 else 'they give'} what you asked. If that is what you meant, say so "
                "and I will check it against your request.")
    by_data = _data_main(decision)
    if by_data:
        named = "; ".join(f"**{name}**{_gives(name)}" for name in by_data)
        return (f"Nearest of NetZoo's main workflows, by the kind of data you described: {named}. Tell me if one of "
                "them gives what you meant.")
    return ""
