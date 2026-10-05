"""On a tie, lead with the workflows the stated question favours, and ask about data it depends on (Logs 370-372).

A tie listed every workflow that produces the requested kind of result -- up
to eleven -- and asked the user to choose, so a request that had said what it
wanted to conclude read as if only its inputs had been looked at. The verified
study purpose (Log 355) and the declared ``CLAIM_SUPPORT`` cells rank the tied
candidates instead: a direct answer first, then an output the question can be
tested from, then one that only describes it, then one that answers for
another quantity (``answers``), then an undeclared cell, then one result for
all the samples when the question asks about individuals. Nothing is
recommended unless the best at least describes the answer; the best (up to
three) are recommended, with the aggregate base of a single best one as its
descriptive option (LIONESS-PANDA, then PANDA).

What the user has is a fact, not an intent, and is never guessed (Log 371: a
request naming no prior got motif workflows recommended; requiring a mention
instead would miss every other wording). For the TF motif prior and PPI
network:

- named in the request: the workflows that need them can be recommended;
- ruled out ("expression only", "nothing else", "no priors"): they are not;
- not mentioned: when that changes what is recommended, the reply gives both
  answers -- if you have them, and with only the data you named -- and the
  card asks which it is; otherwise nothing is asked.

A miRNA workflow is recommended only when miRNAs are mentioned, and when two
omics layers are named only the workflows that use both are (Log 363). When
several are recommended, each says when to pick it first, from its registered
conditions -- the agent never infers them (Log 315). Every candidate stays in
the reply with the reason it comes later; each line says why it fits the
question, never how the algorithm works (user decision, Log 370). Nothing here
changes the decision; a request without a verified conclusion keeps its reply.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from workflow_registry import CLAIM_SUPPORT, OUTPUT_CAPABILITIES, ClaimSupport

from ..routing.study_purpose import StudyPurpose

__all__ = ["Ranked", "Shortlist", "intent_reply", "intent_shortlist"]

_MULTI_OMIC = frozenset({"run_dragon", "run_lioness_dragon"})
_MIRNA_TOOLS = frozenset({"run_puma", "run_lioness_puma"})
_PRIOR_FIELDS = frozenset({"motif_file", "ppi_file"})
_MIRNA = re.compile(r"mi(?:cro)?-?RNAs?|\bmiR-|small[- ]?RNA", re.I)
_PRIORS = re.compile(r"motif|\bpriors?\b|\bPPI\b|protein[- ](?:protein\s+)?interaction|binding[- ]sites?", re.I)
# Log 363: what the request rules out, in its own words.
_NO_PRIORS = re.compile(
    r"expression\s+(?:data\s+|matrix\s+)?only|only\s+(?:have\s+)?(?:the\s+)?(?:expression|counts?|count\s+matrix|"
    r"RNA-?seq)|(?:expression|counts?)\s+(?:data\s+|matrix\s+)?(?:is|are)\s+all\s+we\s+have|"
    r"\bno\s+(?:other\s+data|(?:TF\s+|regulatory\s+)?priors?|motif|protein)|without\s+(?:any\s+)?(?:priors?|motif)|"
    r"nothing\s+else|that\s+is\s+all|and\s+nothing\s+more", re.I)
PRIORS_LABEL = "a TF motif prior and a PPI network"

_ONE_LAYER = "uses one of the two data types you named, not both"
_NO_MIRNA = "models miRNA regulators, which your request does not mention"
_RULED_OUT = f"needs {PRIORS_LABEL}, which you said you do not have"
_UNNAMED = f"needs {PRIORS_LABEL}, which your request does not mention"


class Ranked(NamedTuple):
    action: str
    cell: ClaimSupport | None
    rank: int
    needs_priors: bool
    blocked: str = ""  # why it is never recommended for this request, or ""


class Shortlist(NamedTuple):
    """The recommended workflows and the rest; ``without`` is set when they need unmentioned priors."""

    recommended: list[Ranked]
    others: list[Ranked]
    # Only when the priors are not mentioned and change the answer: what is recommended without them
    # (possibly nothing), and the card asks.
    without: list[Ranked] | None = None


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
    from workflow_registry import SELECTION_AXES

    witness = SELECTION_AXES.get(cell.quantity_axis, {}).get("witness") if cell.quantity_axis else None
    return bool(witness and isinstance(witness, str) and re.search(witness, quote, re.I))


def _question(purpose: StudyPurpose) -> tuple[str, str] | None:
    """The first stated conclusion a registered workflow can work toward (as study_purpose_notes.question_claim)."""
    from workflow_registry import UNSUPPORTED_CLAIMS

    return next(((claim, quote) for claim, quote in purpose.claims if claim not in UNSUPPORTED_CLAIMS), None)


def _needs_priors(action: str) -> bool:
    from ..reply_cards.method_notes import input_fields

    required, groups = input_fields(action)
    return bool(_PRIOR_FIELDS & set(required)) or any(set(group) <= _PRIOR_FIELDS for group in groups)


def _pick(pool: list[Ranked]) -> list[Ranked]:
    """The best of a pool (up to three), with a single best one's aggregate base; [] when none answers."""
    best = max((item.rank for item in pool), default=0)
    if best < _DESCRIBES:
        return []
    recommended = [item for item in pool if item.rank == best][:3]
    if len(recommended) == 1:
        bases = OUTPUT_CAPABILITIES[recommended[0].action].guidance_predecessors
        recommended += [item for item in pool if item.action in bases and _DESCRIBES <= item.rank < best]
    return recommended


def priors_status(task: str) -> str:
    """"named", "ruled_out" or "unknown": what the request's own words say about a motif prior and PPI.

    A mention inside the words that rule them out ("expression only, no priors") is no mention.
    """
    rest = _NO_PRIORS.sub(" ", task)
    if _PRIORS.search(rest):
        return "named"
    return "ruled_out" if rest != task else "unknown"


def intent_shortlist(decision, purpose: StudyPurpose, task: str) -> Shortlist | None:
    """The shortlist for a tie with a verified question, or None."""
    from workflow_registry import UNSUPPORTED_CLAIMS

    from ..routing.reading_selection import READING_WITNESSES

    question = _question(purpose)
    if (decision.capability_match_status != "ambiguous" or question is None
            or any(claim in UNSUPPORTED_CLAIMS for claim, _ in purpose.claims)
            or len(decision.outcome_hypotheses) > 1):
        return None
    candidates = [action for action in dict.fromkeys(decision.hypothesis_actions) if action in OUTPUT_CAPABILITIES]
    if len(candidates) < 2:
        return None
    claim, design = question[0], purpose.design or "*"
    two_layers = bool(READING_WITNESSES["multi_omic_network"].search(task)) and any(
        action in _MULTI_OMIC for action in candidates)
    mirna = bool(_MIRNA.search(task))
    priors = priors_status(task)
    ranked = []
    for action in candidates:
        cell = CLAIM_SUPPORT.get((action, claim, design)) or CLAIM_SUPPORT.get((action, claim, "*"))
        needs = _needs_priors(action)
        blocked = (_ONE_LAYER if two_layers and action not in _MULTI_OMIC
                   else _NO_MIRNA if action in _MIRNA_TOOLS and not mirna
                   else _RULED_OUT if needs and priors == "ruled_out" else "")
        ranked.append(Ranked(action, cell, _rank(cell, question[1]), needs, blocked))
    open_pool = [item for item in ranked if not item.blocked]
    with_priors = _pick(open_pool)
    without = _pick([item for item in open_pool if not item.needs_priors]) if priors == "unknown" else None
    if without is not None and [i.action for i in without] == [i.action for i in with_priors]:
        without = None  # the priors do not change the answer: nothing to ask
    if not with_priors and not without:
        return None
    if without is None and len(with_priors) >= len(candidates):
        return None
    shown = {item.action for item in (*with_priors, *(without or ()))}
    return Shortlist(with_priors, [item for item in ranked if item.action not in shown], without)


def _name(action: str) -> str:
    from workflow_registry import ACTION_DEFINITIONS

    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def _names(actions) -> str:
    names = [f"**{_name(action)}**" for action in actions]
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _when(item: Ranked, among: list[Ranked]) -> str:
    """When to pick it first, from its registered conditions the others do not share (Log 315: never inferred)."""
    from ..reply_cards.method_notes import condition_phrase

    own = OUTPUT_CAPABILITIES[item.action].prefer_when
    shared = set.intersection(*(set(OUTPUT_CAPABILITIES[other.action].prefer_when) for other in among))
    phrases = [phrase for condition in own if condition not in shared and (phrase := condition_phrase(condition))]
    return f" Pick it first if {' or '.join(phrases)}." if phrases and len(among) > 1 else ""


def _recommended_lines(items: list[Ranked]) -> list[str]:
    return [f"- **{_name(item.action)}** — {item.cell.text}{_when(item, items)}" for item in items]


def _reason(item: Ranked) -> str:
    """Why a candidate comes after the recommended ones, in the registry's words."""
    from ..reply_cards.method_notes import gives

    if item.blocked:
        return item.blocked
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
    """A tie's reply led by the recommended workflows, every candidate kept (Logs 370-372), or None."""
    from ..presentation import _ui_text_with_user_data, user_data_token
    from ..reply_cards.choices import _stated_reasons
    from .inspected_answers import _NOT_INSPECTED

    shortlist = intent_shortlist(decision, purpose, task)
    if shortlist is None or not text:
        return None
    recommended, others, without = shortlist
    user_data = [_question(purpose)[1]]
    lead = f'For your question ("{user_data_token(0)}")'
    if without is None:
        lines = [f"{lead}, these fit best, and here is why:", *_recommended_lines(recommended)]
        shown = recommended
    else:
        lines = [f"{lead}, which workflow fits depends on whether you have {PRIORS_LABEL}; your request does "
                 "not mention them."]
        if recommended:
            lines += [f"If you have {PRIORS_LABEL}:", *_recommended_lines(recommended)]
        lines += ["With only the data you named:", *(
            _recommended_lines(without) if without else
            ["- None of the workflows suggested for this result answers it without "
             f"{PRIORS_LABEL}."])]
        shown = [*recommended, *without]
    caveats = dict.fromkeys(caveat for item in shown for caveat in item.cell.caveats)
    lines += [f"Note: {caveat}" for caveat in caveats]
    advice = decision.advisory_recommendation
    later = ["The other registered options, and why they come later:"]
    by_reason: dict[str, list[str]] = {}
    for item in others:
        reason = _reason(item)
        if advice is not None and advice.action == item.action and _stated_reasons(advice):
            reason += "; it was suggested because " + "; ".join(_stated_reasons(advice))
        by_reason.setdefault(reason if item.blocked else f"{item.action}:{reason}", []).append(item.action)
    for key, actions in by_reason.items():
        reason = key.split(":", 1)[1] if ":" in key and key.split(":", 1)[0] in actions else key
        if len(actions) > 1:
            for singular in ("needs ", "uses ", "gives ", "models "):
                if reason.startswith(singular):
                    reason = singular[:-2] + " " + reason[len(singular):]
        later.append(f"- {_names(actions)} — {reason}.")
    if without is None:
        names = _names([item.action for item in recommended])
        ask = f"Should I plan {names.replace(' and ', ' or ')}, or do you need one of the others?"
    else:
        ask = f"Do you have {PRIORS_LABEL}? Tell me, and I will narrow this down."
    kept = [part for part in text.split("\n\n")
            if part.startswith(("Assumptions behind", "Unconfirmed assumptions")) or _NOT_INSPECTED in part]
    block = "\n\n".join(["\n".join(lines), *(["\n".join(later)] if len(later) > 1 else []), ask])
    _ui_text_with_user_data(block, user_data)
    return "\n\n".join([block.replace(user_data_token(0), user_data[0]), *kept])
