"""On a tie, lead with the workflows the stated question and the named data favour (Log 370).

A tie listed every workflow that produces the requested kind of result -- up
to eleven -- and asked the user to choose, so a request that had said what it
wanted to conclude and what data it had read as if only its inputs had been
looked at. The verified study purpose (Log 355) and the declared
``CLAIM_SUPPORT`` cells rank the tied candidates instead:

- a candidate needing an input the request never mentions, that the others do
  not need (`choices._differential_missing`), is not recommended;
- when the request names two omics layers, only the workflows that use both
  are recommended (the others use one of them; Log 363 measured the same);
- a workflow that models miRNA regulators is recommended only when the request
  mentions miRNAs (a request naming no input says nothing about which it lacks,
  so the input check above cannot tell);
- among the rest, a direct answer comes first, then an output the question can
  be tested from, then one that only describes it, then one that answers for
  another quantity (``answers``), then an undeclared cell, then one result for
  all the samples when the question asks about individuals; nothing is
  recommended unless the best at least describes the answer;
- the best of them are recommended (up to three); when one is best, its
  aggregate base comes with it as the descriptive option (LIONESS-PANDA, then
  PANDA), and only when this separates the candidates.

Every candidate stays in the reply: the others follow on one line each, with
the reason they come later. Each recommended line says why it fits the
question (its cell) -- the registry's words, never the model's; at the user's
request the lines do not explain the algorithms. Nothing here changes the
decision; a request without a verified conclusion keeps its reply.
"""

from __future__ import annotations

from typing import NamedTuple

from workflow_registry import CLAIM_SUPPORT, OUTPUT_CAPABILITIES, ClaimSupport

from ..routing.study_purpose import StudyPurpose

__all__ = ["Ranked", "intent_reply", "intent_shortlist"]


_MULTI_OMIC = frozenset({"run_dragon", "run_lioness_dragon"})
_ONE_LAYER = "uses one of the two data types you named, not both"
_MIRNA_TOOLS = frozenset({"run_puma", "run_lioness_puma"})
_NO_MIRNA = "models miRNA regulators, which your request does not mention"


class Ranked(NamedTuple):
    action: str
    cell: ClaimSupport | None
    rank: int
    missing: tuple[str, ...]
    one_layer: bool = False
    unnamed_mirna: bool = False


_RANKS = {"test": 4, "describe": 3, "other": 2}
_DESCRIBES = 3


def _rank(cell: ClaimSupport | None, quote: str = "") -> int:
    if cell is None:
        return 1
    if cell.level == "one_result":
        return 0
    if cell.level == "direct":
        return 5
    if cell.answers == "other" and _names_quantity(cell, quote):
        return _RANKS["test"]
    return _RANKS[cell.answers]


def _names_quantity(cell: ClaimSupport, quote: str) -> bool:
    """The question itself names the quantity an "other" cell answers for (its axis witness)."""
    import re

    from workflow_registry import SELECTION_AXES

    witness = SELECTION_AXES.get(cell.quantity_axis, {}).get("witness") if cell.quantity_axis else None
    return bool(witness and isinstance(witness, str) and re.search(witness, quote, re.I))


def _question(purpose: StudyPurpose) -> tuple[str, str] | None:
    """The first stated conclusion a registered workflow can work toward (as study_purpose_notes.question_claim)."""
    from workflow_registry import UNSUPPORTED_CLAIMS

    return next(((claim, quote) for claim, quote in purpose.claims if claim not in UNSUPPORTED_CLAIMS), None)


def intent_shortlist(decision, purpose: StudyPurpose, task: str) -> tuple[list[Ranked], list[Ranked]] | None:
    """(recommended, the rest) for a tie with a verified question, or None."""
    from workflow_registry import UNSUPPORTED_CLAIMS

    from ..reply_cards.choices import _differential_missing
    from ..routing.capability_compatibility import input_availability

    question = _question(purpose)
    if (decision.capability_match_status != "ambiguous" or question is None
            or any(claim in UNSUPPORTED_CLAIMS for claim, _ in purpose.claims)
            or len(decision.outcome_hypotheses) > 1):
        return None
    candidates = [action for action in dict.fromkeys(decision.hypothesis_actions) if action in OUTPUT_CAPABILITIES]
    if len(candidates) < 2:
        return None
    claim, design = question[0], purpose.design or "*"
    # Only what the request's own words name: a reading's input list is the router's, not the user's.
    missing = _differential_missing(candidates, frozenset(input_availability(task).present), task)
    from ..routing.reading_selection import READING_WITNESSES

    import re

    two_layers = bool(READING_WITNESSES["multi_omic_network"].search(task)) and any(
        action in _MULTI_OMIC for action in candidates)
    mirna = bool(re.search(r"mi(?:cro)?-?RNAs?|\bmiR-|small[- ]?RNA", task, re.I))
    ranked = [Ranked(action, cell, _rank(cell, question[1]), tuple(missing[action]),
                     two_layers and action not in _MULTI_OMIC, action in _MIRNA_TOOLS and not mirna)
              for action in candidates
              for cell in [CLAIM_SUPPORT.get((action, claim, design)) or CLAIM_SUPPORT.get((action, claim, "*"))]]
    fitting = [item for item in ranked if not item.missing and not item.one_layer and not item.unnamed_mirna]
    best = max((item.rank for item in fitting), default=0)
    if best < _DESCRIBES:  # nothing that answers this question among the workflows the named data fit
        return None
    recommended = [item for item in fitting if item.rank == best][:3]
    if len(recommended) == 1:
        bases = OUTPUT_CAPABILITIES[recommended[0].action].guidance_predecessors
        recommended += [item for item in fitting if item.action in bases and _DESCRIBES <= item.rank < best]
    if len(recommended) >= len(candidates):
        return None
    chosen = {item.action for item in recommended}
    return recommended, [item for item in ranked if item.action not in chosen]


def _name(action: str) -> str:
    from workflow_registry import ACTION_DEFINITIONS

    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def _names(actions) -> str:
    names = [f"**{_name(action)}**" for action in actions]
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _recommended_line(item: Ranked) -> str:
    return f"- **{_name(item.action)}** — {item.cell.text}"


def _article(label: str) -> str:
    return ("an " if label[:1].lower() in "aeiou" else "a ") + label


def _reason(item: Ranked) -> str:
    """Why a candidate comes after the recommended ones, in the registry's words."""
    from ..reply_cards.method_notes import gives

    if item.missing:
        return f"needs {' and '.join(_article(label) for label in item.missing)}, which your request does not mention"
    if item.one_layer:
        return _ONE_LAYER
    if item.unnamed_mirna:
        return _NO_MIRNA
    if item.cell is None:
        offered = gives(item.action)
        offered = offered[:1].lower() + offered[1:] if offered else ""
        return (f"gives {offered.rstrip('.')}; " if offered else "") + "the registry does not say how it answers this question"
    if item.cell.level == "one_result":
        return (f"gives {item.cell.text}; with one sample per individual that says nothing about a single "
                "individual")
    if item.cell.limit:
        return item.cell.limit
    first = item.cell.text.split(". ", 1)[0].rstrip(".")
    return "also fits, after the recommended: " + first[:1].lower() + first[1:]


def intent_reply(text: str, decision, purpose: StudyPurpose, task: str) -> str | None:
    """A tie's reply led by the recommended workflows, every candidate kept (Log 370), or None."""
    from ..presentation import _ui_text_with_user_data, user_data_token
    from ..reply_cards.choices import _stated_reasons
    from .inspected_answers import _NOT_INSPECTED

    ranked = intent_shortlist(decision, purpose, task)
    if ranked is None or not text:
        return None
    recommended, others = ranked
    user_data = [_question(purpose)[1]]
    lines = [f'For your question ("{user_data_token(0)}"), these fit best, and here is why:',
             *(_recommended_line(item) for item in recommended)]
    caveats = dict.fromkeys(caveat for item in recommended for caveat in item.cell.caveats)
    lines += [f"Note: {caveat}" for caveat in caveats]
    advice = decision.advisory_recommendation
    later = ["The other registered options, and why they come later:"]
    by_reason: dict[str, list[str]] = {}
    for item in others:
        reason = _reason(item)
        if advice is not None and advice.action == item.action and _stated_reasons(advice):
            reason += "; it was suggested because " + "; ".join(_stated_reasons(advice))
        shared = item.missing or item.one_layer or item.unnamed_mirna
        by_reason.setdefault(reason if shared else f"{item.action}:{reason}", []).append(item.action)
    for key, actions in by_reason.items():
        reason = key.split(":", 1)[1] if ":" in key and key.split(":", 1)[0] in actions else key
        if len(actions) > 1:
            for singular in ("needs ", "uses ", "gives ", "models "):
                if reason.startswith(singular):
                    reason = singular[:-2] + " " + reason[len(singular):]
        later.append(f"- {_names(actions)} — {reason}.")
    names = _names([item.action for item in recommended])
    question = f"Should I plan {names.replace(' and ', ' or ')}, or do you need one of the others?"
    kept = [part for part in text.split("\n\n")
            if part.startswith(("Assumptions behind", "Unconfirmed assumptions")) or _NOT_INSPECTED in part]
    block = "\n\n".join(["\n".join(lines), "\n".join(later), question])
    _ui_text_with_user_data(block, user_data)
    return "\n\n".join([block.replace(user_data_token(0), user_data[0]), *kept])
