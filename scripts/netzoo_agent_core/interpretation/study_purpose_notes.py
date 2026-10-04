"""Say what each listed workflow gives toward the question the request states (Log 342).

Log 341 (minimal pairs): the same data with different purpose sentences got
the same reply. "Does the regulatory network change after treatment across
the cohort?" was answered like "one network summarizing all 48 samples";
"show that the treatment itself causes changes" got "These all fit"; and
"predict whether a new patient will respond" got "could not validate".

`study_purpose` reads the stated comparison design and kind of conclusion
from the request's words. This module adds to the reply, never to the
decision:

- a conclusion no registered workflow supports (causation, prediction) is
  said first, once, from ``UNSUPPORTED_CLAIMS``; a tie's "These all fit" lead
  then says what none of them can do;
- for any other stated conclusion, each listed workflow with a declared
  ``CLAIM_SUPPORT`` cell says what it gives toward it and the step after it,
  above the reply's question. A workflow without a cell says nothing: a
  missing declaration is never a gap (CC1, Logs 288-289);
- a semantic fallback on a request stating such a conclusion is answered with
  the gap instead of "could not validate".

Every sentence is the registry's; the only words from the request are its
own quoted sentence.
"""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS, CLAIM_SUPPORT, UNSUPPORTED_CLAIMS, ClaimSupport

from ..presentation import _ui_text_with_user_data, user_data_token
from ..routing.study_purpose import StudyPurpose, study_purpose
from .inspected_answers import _NOT_INSPECTED, above_closing
from .outside_steps import _REPLY_KINDS, _asks

__all__ = [
    "CLAIM_LABELS",
    "recommended_actions",
    "purpose_from_state",
    "claim_cells",
    "gap_claims",
    "question_claim",
    "unresolved_gap_reply",
    "with_study_purpose",
    "with_study_purpose_reply",
]

# The question a stated conclusion asks, as a card point names it.
CLAIM_LABELS = {
    "group_difference": "whether the groups or time points differ",
    "individual_change": "which individuals change or stand out",
    "regulator_change": "which regulators change most",
}
# What none of the listed workflows can do, in a tie's lead sentence.
_CANNOT = {
    "causal": "show that one thing causes another",
    "prediction": "predict outcomes for new samples",
}
# What a registered workflow can still give, after a semantic fallback.
_FALLBACK_NEXT = {
    "causal": "If you want to describe what differs or changes, say which comparison you mean and the data you have.",
    "prediction": (
        "If you want per-sample results to use as features, say which result you need -- per-sample "
        "networks, TF activities or subtypes -- and the data you have."
    ),
}
_TIE_LEADS = ("These all fit; to choose, tell me:", "Both fit; to choose, tell me:")


def _name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def _listed(decision) -> list[str]:
    """The workflows the reply presents, in the order it presents them."""
    advice = decision.advisory_recommendation
    return list(dict.fromkeys([
        *([advice.action] if advice is not None else []),
        *decision.recommended_actions, *decision.matched_actions, *decision.hypothesis_actions,
    ]))


def purpose_from_state(state, task: str) -> StudyPurpose:
    """This turn's verified study purpose (Log 355), or the word witnesses' reading.

    The study-purpose call writes it to state after routing; a state without it
    (a follow-up turn, a context without the call, an older session) falls back
    to the request's own words as read since Log 342.
    """
    entry = (state or {}).get("study_purpose")
    if not entry:
        return study_purpose(task)
    return StudyPurpose(entry.get("design"), entry.get("design_quote") or "",
                        tuple((claim, quote) for claim, quote in entry.get("claims") or ()))


def gap_claims(purpose: StudyPurpose) -> list[tuple[str, str]]:
    """(claim, quote) for each stated conclusion no registered workflow supports."""
    return [(claim, quote) for claim, quote in purpose.claims if claim in UNSUPPORTED_CLAIMS]


def question_claim(purpose: StudyPurpose) -> tuple[str, str] | None:
    """The first stated conclusion a registered workflow can work toward."""
    return next(((claim, quote) for claim, quote in purpose.claims if claim not in UNSUPPORTED_CLAIMS), None)


def claim_cells(decision, purpose: StudyPurpose) -> list[tuple[str, ClaimSupport]]:
    """Each listed workflow's declared cell for the question, when the request has one reading."""
    question = question_claim(purpose)
    if question is None or len(decision.outcome_hypotheses) > 1:
        return []
    claim, design = question[0], purpose.design or "*"
    cells = []
    for action in _listed(decision):
        cell = CLAIM_SUPPORT.get((action, claim, design)) or CLAIM_SUPPORT.get((action, claim, "*"))
        if cell is not None:
            cells.append((action, cell))
    return cells


# Log 363 (a''): the data a request names, read narrowly. input_availability missed "no
# motif or protein interaction data" and "miRNA-target priors", so these only decide whom
# to recommend -- never which workflows are listed.
_MIRNA_DATA = re.compile(r"mi(?:cro)?-?RNAs?|\bmiR-|small[- ]?RNA", re.I)
_PRIORS = re.compile(r"motif|\bpriors?\b|\bPPI\b|protein[- ](?:protein\s+)?interaction|binding[- ]sites?", re.I)
_NO_PRIORS = re.compile(
    r"expression\s+(?:data\s+|matrix\s+)?only|only\s+(?:have\s+)?(?:the\s+)?(?:expression|counts?|count\s+matrix|RNA-?seq)"
    r"|(?:expression|counts?)\s+(?:data\s+|matrix\s+)?(?:is|are)\s+all\s+we\s+have"
    r"|\bno\s+(?:other\s+data|(?:TF\s+|regulatory\s+)?priors?|motif|protein)|without\s+(?:any\s+)?(?:priors?|motif)"
    r"|nothing\s+else", re.I)
_MIRNA_TOOLS = frozenset({"run_puma", "run_lioness_puma"})
_PRIOR_TOOLS = frozenset({"run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma", "run_otter", "run_giraffe"})
_MULTI_OMIC_TOOLS = frozenset({"run_dragon", "run_lioness_dragon"})


def recommended_actions(decision, purpose: StudyPurpose, task: str) -> list[str]:
    """The tied workflows that answer the stated question with the data the request names (Log 363).

    Only a tie, only a question some but not all candidates have a declared
    cell for (the question separates them; the named data only narrows), and never beside a causal or predictive claim. A miRNA workflow
    needs miRNA data named, a prior-based one needs priors named and not
    ruled out ("expression only"), and two named omics layers prefer the
    multi-omic workflows. An empty list recommends nothing.
    """
    from ..routing.reading_selection import READING_WITNESSES

    candidates = list(dict.fromkeys(decision.hypothesis_actions))
    question = question_claim(purpose)
    if (decision.capability_match_status != "ambiguous" or len(candidates) < 2 or question is None
            or gap_claims(purpose) or len(decision.outcome_hypotheses) > 1):
        return []
    claim, design = question[0], purpose.design or "*"
    declared = [action for action in candidates
                if CLAIM_SUPPORT.get((action, claim, design)) or CLAIM_SUPPORT.get((action, claim, "*"))]
    # The question itself must separate the candidates; the named data only narrows its choice.
    if not declared or len(declared) == len(candidates):
        return []
    priors = bool(_PRIORS.search(task)) and not _NO_PRIORS.search(task)
    mirna = bool(_MIRNA_DATA.search(task))
    fit = [action for action in declared
           if (action not in _PRIOR_TOOLS or priors) and (action not in _MIRNA_TOOLS or mirna)]
    multi_omic = [action for action in fit if action in _MULTI_OMIC_TOOLS]
    if multi_omic and READING_WITNESSES["multi_omic_network"].search(task):
        fit = multi_omic
    return fit if fit and len(fit) < len(candidates) else []


def _gap_paragraphs(purpose: StudyPurpose, user_data: list[str]) -> list[str]:
    paragraphs = []
    for claim, quote in gap_claims(purpose):
        text, paired, _label, _reason = UNSUPPORTED_CLAIMS[claim]
        user_data.append(quote)
        addition = f" {paired}" if paired and purpose.design == "paired" else ""
        paragraphs.append(f'About "{user_data_token(len(user_data) - 1)}": {text}{addition}')
    return paragraphs


def _purpose_paragraph(cells, quote: str, user_data: list[str], recommended: list[str] = ()) -> str:
    user_data.append(quote)
    lines = [f'For your question ("{user_data_token(len(user_data) - 1)}"):']
    if recommended:
        names = " or ".join(f"**{_name(action)}**" for action in recommended)
        lines.append(f"Start with {names}: with the data you named, these answer it, as below.")
        cells = sorted(cells, key=lambda item: item[0] not in recommended)
    # Workflows whose cell says the same thing share one line (PANDA and PUMA).
    by_text: dict[str, list[str]] = {}
    for action, cell in cells:
        by_text.setdefault(cell.text, []).append(f"**{_name(action)}**")
    lines += [f"- {', '.join(names)} — {text}" for text, names in by_text.items()]
    caveats = dict.fromkeys(caveat for _, cell in cells for caveat in cell.caveats)
    lines += [f"Note: {caveat}" for caveat in caveats]
    return "\n".join(lines)


def _reworded_lead(paragraph: str, purpose: StudyPurpose) -> str:
    cannot = " or ".join(_CANNOT[claim] for claim, _ in gap_claims(purpose))
    for lead in _TIE_LEADS:
        if paragraph.startswith(lead):
            return (f"These fit the result you described, but none can {cannot}; to choose among them, "
                    f"tell me:{paragraph[len(lead):]}")
    return paragraph


def _recommending_lead(paragraph: str, recommended: list[str]) -> str:
    names = " or ".join(f"**{_name(action)}**" for action in recommended)
    for lead in _TIE_LEADS:
        if paragraph.startswith(lead):
            return (f"These fit the result you described; for your question, start with {names}. To choose "
                    f"otherwise, tell me:{paragraph[len(lead):]}")
    return paragraph


def with_study_purpose(text: str, decision, purpose: StudyPurpose, task: str = "") -> str:
    """The reply with the gap first and the purpose paragraph above its question."""
    if not text:
        return text
    user_data: list[str] = []
    gaps = _gap_paragraphs(purpose, user_data)
    cells = claim_cells(decision, purpose)
    question = question_claim(purpose)
    recommended = recommended_actions(decision, purpose, task) if task else []
    purpose_block = _purpose_paragraph(cells, question[1], user_data, recommended) if cells and question else ""
    if not gaps and not purpose_block:
        return text
    paragraphs = text.split("\n\n")
    if gaps:
        paragraphs = [*gaps, *(_reworded_lead(part, purpose) for part in paragraphs)]
    if recommended and purpose_block:
        paragraphs = [_recommending_lead(part, recommended) for part in paragraphs]
    if purpose_block:
        closing = next((i for i, part in enumerate(paragraphs) if _NOT_INSPECTED in part), None)
        if closing is not None and closing > 1 and _asks(paragraphs[closing - 1]):
            paragraphs = [*paragraphs[:closing - 1], purpose_block, *paragraphs[closing - 1:]]
        else:
            paragraphs = above_closing("\n\n".join(paragraphs), purpose_block).split("\n\n")
    added = "\n\n".join(paragraphs)
    # Only the added template is checked as agent-authored; the reply was checked by its renderer.
    _ui_text_with_user_data("\n\n".join([*gaps, purpose_block]), user_data)
    for index, value in enumerate(user_data):
        added = added.replace(user_data_token(index), value)
    return added


def unresolved_gap_reply(purpose: StudyPurpose) -> str | None:
    """A semantic fallback's reply when the request states a conclusion no workflow supports."""
    gaps = gap_claims(purpose)
    if not gaps:
        return None
    user_data: list[str] = []
    paragraphs = [*_gap_paragraphs(purpose, user_data), _FALLBACK_NEXT[gaps[0][0]], _NOT_INSPECTED]
    return _ui_text_with_user_data("\n\n".join(paragraphs), user_data)


def with_study_purpose_reply(result: dict, state, reply) -> dict:
    """`respond()`'s last step: the same reply, with the purpose's paragraphs when they apply."""
    from ..contracts import TaskDecision
    from ..llm import latest_user_task

    kind = result.get("reply_kind")
    if kind not in _REPLY_KINDS | {"unresolved"}:
        return result
    purpose = purpose_from_state(state, latest_user_task(state["messages"]))
    if purpose.design is None and not purpose.claims:
        return result
    text = str(result["messages"][-1].content)
    if kind == "unresolved":
        updated = unresolved_gap_reply(purpose)
    else:
        updated = with_study_purpose(text, TaskDecision.model_validate(state["decision"]), purpose,
                                     latest_user_task(state["messages"]))
    return result if not updated or updated == text else reply(updated, kind)
