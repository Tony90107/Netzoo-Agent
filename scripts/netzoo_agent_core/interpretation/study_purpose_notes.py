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
- a workflow whose declared cell is "cannot" (Log 365: one result for all
  the samples, asked about individuals) says so after the others and names
  the per-sample workflow that takes the same data; when no listed workflow
  answers the question, that paragraph comes first, and a tie's lead says
  which of them cannot show it;
- a semantic fallback on a request stating such a conclusion is answered with
  the gap instead of "could not validate".

Every sentence is the registry's; the only words from the request are its
own quoted sentence.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, CLAIM_SUPPORT, UNSUPPORTED_CLAIMS, ClaimSupport

from ..presentation import _ui_text_with_user_data, user_data_token
from ..routing.study_purpose import StudyPurpose, study_purpose
from .inspected_answers import _NOT_INSPECTED, above_closing
from .outside_steps import _REPLY_KINDS, _asks

__all__ = [
    "CLAIM_LABELS",
    "purpose_from_state",
    "cannot_cells",
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


def cannot_cells(decision, purpose: StudyPurpose) -> list[tuple[str, ClaimSupport]]:
    """The listed workflows whose declared cell says they cannot answer the question (Log 365)."""
    return [(action, cell) for action, cell in claim_cells(decision, purpose) if cell.level == "cannot"]


def _gap_paragraphs(purpose: StudyPurpose, user_data: list[str]) -> list[str]:
    paragraphs = []
    for claim, quote in gap_claims(purpose):
        text, paired, _label, _reason = UNSUPPORTED_CLAIMS[claim]
        user_data.append(quote)
        addition = f" {paired}" if paired and purpose.design == "paired" else ""
        paragraphs.append(f'About "{user_data_token(len(user_data) - 1)}": {text}{addition}')
    return paragraphs


def _purpose_paragraph(cells, quote: str, user_data: list[str]) -> str:
    user_data.append(quote)
    lines = [f'For your question ("{user_data_token(len(user_data) - 1)}"):']
    # Workflows whose cell says the same thing share one line (PANDA and PUMA).
    by_text: dict[str, list[str]] = {}
    for action, cell in cells:
        if cell.level != "cannot":
            by_text.setdefault(cell.text, []).append(f"**{_name(action)}**")
    lines += [f"- {', '.join(names)} — {text}" for text, names in by_text.items()]
    lines += _cannot_lines(cells)
    caveats = dict.fromkeys(caveat for _, cell in cells for caveat in cell.caveats)
    lines += [f"Note: {caveat}" for caveat in caveats]
    return "\n".join(lines)


def _cannot_lines(cells) -> list[str]:
    """Log 365: after the workflows that answer it, those that cannot, one line per reason."""
    by_text: dict[str, list[str]] = {}
    for action, cell in cells:
        if cell.level == "cannot":
            by_text.setdefault(cell.text, []).append(action)
    lines = []
    for text, actions in by_text.items():
        one = len(actions) == 1
        instead = list(dict.fromkeys(other for action, cell in cells if cell.text == text
                                     and cell.level == "cannot" for other in cell.instead))
        lines.append(
            f"- {', '.join(f'**{_name(action)}**' for action in actions)} — {'does' if one else 'do'} not answer "
            f"this: {'it gives' if one else 'each gives'} {text}, so when each individual gives one sample (per "
            f"time point) there is no result for an individual. Per-sample "
            f"{'workflow' if len(instead) == 1 else 'workflows'} for the same data: "
            f"{', '.join(f'**{_name(action)}**' for action in instead)}.")
    return lines


def _reworded_lead(paragraph: str, purpose: StudyPurpose) -> str:
    cannot = " or ".join(_CANNOT[claim] for claim, _ in gap_claims(purpose))
    for lead in _TIE_LEADS:
        if paragraph.startswith(lead):
            return (f"These fit the result you described, but none can {cannot}; to choose among them, "
                    f"tell me:{paragraph[len(lead):]}")
    return paragraph


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _cannot_lead(paragraph: str, cannot: list[tuple[str, ClaimSupport]], claim: str) -> str:
    """Log 365: a tie's lead no longer says all fit when some cannot show what is asked."""
    names = _join([f"**{_name(action)}**" for action, _ in cannot])
    for lead in _TIE_LEADS:
        if paragraph.startswith(lead):
            return (f"These fit the result you described, but {names} cannot show {CLAIM_LABELS[claim]}; "
                    f"to choose, tell me:{paragraph[len(lead):]}")
    return paragraph


def with_study_purpose(text: str, decision, purpose: StudyPurpose) -> str:
    """The reply with the gap first and the purpose paragraph above its question."""
    if not text:
        return text
    user_data: list[str] = []
    gaps = _gap_paragraphs(purpose, user_data)
    cells = claim_cells(decision, purpose)
    question = question_claim(purpose)
    purpose_block = _purpose_paragraph(cells, question[1], user_data) if cells and question else ""
    if not gaps and not purpose_block:
        return text
    paragraphs = text.split("\n\n")
    if gaps:
        paragraphs = [*gaps, *(_reworded_lead(part, purpose) for part in paragraphs)]
    cannot = cannot_cells(decision, purpose) if purpose_block else []
    if cannot and not gaps:
        paragraphs = [_cannot_lead(part, cannot, question[0]) for part in paragraphs]
    if cannot and len(cannot) == len(cells):
        # No listed workflow answers the question: say so first, after any gap.
        paragraphs = [*paragraphs[:len(gaps)], purpose_block, *paragraphs[len(gaps):]]
    elif purpose_block:
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
        updated = with_study_purpose(text, TaskDecision.model_validate(state["decision"]), purpose)
    return result if not updated or updated == text else reply(updated, kind)
