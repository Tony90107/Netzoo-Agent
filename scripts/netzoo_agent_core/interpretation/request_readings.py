"""The capability check's request-level readings the core decision adds, each kept only with its words verified.

Moved out of `interpretation.capability_check` (module size limit): the goal (phase 1, CLARIFY), the words the
reading typed as stated (R4) and as uncertain (R1's second reader, phase 2), and the inputs the user rules out
(phase 4b).
"""

from __future__ import annotations

from ..contracts.capability_check import CONDITIONS
from .request_spans import _span

__all__ = ["only_inputs", "ruled_out_inputs", "stated_quotes", "uncertain_quotes", "verified_goal"]


_INDEFINITE = {"", "not_stated", "none", None}


def stated_quotes(task: str, proposal) -> list[str]:
    """Phase 2 R4: the request's words for each condition, method and setting the reading typed definitely."""
    conditions = getattr(proposal, "conditions", None)
    found = []
    for name in [*CONDITIONS, "named_method"]:
        quote = (getattr(conditions, f"{name}_quote", "") or "").strip()
        if getattr(conditions, name, None) not in _INDEFINITE and quote and (span := _span(task, quote)) is not None:
            found.append(task[span[0]:span[1]])
    for setting in getattr(conditions, "settings", None) or []:
        for quote in (getattr(setting, "quote", ""), getattr(setting, "value_quote", "")):
            if quote and quote.strip() and (span := _span(task, quote.strip())) is not None:
                found.append(task[span[0]:span[1]])
    return list(dict.fromkeys(found))


def uncertain_quotes(task: str, proposal) -> list[str]:
    """Phase 2 R1: the words of every unknown fact and open choice the reading found in the request."""
    conditions = getattr(proposal, "conditions", None)
    quotes = [fact.quote for fact in getattr(conditions, "unknown_facts", None) or ()]
    quotes += [choice.quote for choice in getattr(conditions, "open_choices", None) or ()]
    found = [task[span[0]:span[1]] for quote in quotes if quote and quote.strip()
             and (span := _span(task, quote.strip())) is not None]
    return list(dict.fromkeys(found))


def ruled_out_inputs(task: str, proposal) -> dict[str, str]:
    """Phase 4b: each input kind the user says they do not have, kept only when the words are in the request."""
    found = {}
    for item in getattr(getattr(proposal, "conditions", None), "ruled_out_inputs", None) or []:
        if item.quote.strip() and (span := _span(task, item.quote.strip())) is not None:
            found.setdefault(item.kind, task[span[0]:span[1]])
    return found


def verified_goal(task: str, proposal) -> tuple[str, str]:
    """Core decision spec, phase 1: the reading's goal and its words, kept only when the words are in the request."""
    conditions = getattr(proposal, "conditions", None)
    goal, quote = getattr(conditions, "goal", ""), (getattr(conditions, "goal_quote", "") or "").strip()
    span = _span(task, quote) if goal and quote else None
    return ("", "") if span is None else (goal, task[span[0]:span[1]])


def only_inputs(task: str, proposal) -> tuple[list[str], str]:
    """Phase 4b: the kinds the user says are their only inputs, kept only when the words are in the request."""
    conditions = getattr(proposal, "conditions", None)
    kinds = list(dict.fromkeys(getattr(conditions, "only_inputs", None) or []))
    quote = (getattr(conditions, "only_inputs_quote", "") or "").strip()
    span = _span(task, quote) if kinds and quote else None
    return ([], "") if span is None else (kinds, task[span[0]:span[1]])
