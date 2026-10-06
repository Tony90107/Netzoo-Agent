"""The research purpose decides among the tools that fit (plan item 3, Log 379).

Log 378: the study purpose was read correctly in 27 of 27 sessions and used by
the decision in none -- routing chose the tools first and read the purpose
afterwards, for the reply only. This module puts the chain the registry
already declares into the decision:

    question (the verified quote) -> conclusion (claim, design)
      -> evidence each workflow gives toward it (CLAIM_SUPPORT, typed)
      -> the workflow whose evidence fits best.

The rules, each from a withdrawn round:
- Only a method tie with one reading and a conclusion a registered workflow
  can support; causation and prediction keep their gap (Log 342).
- Every candidate must have a declared cell: an undeclared one is not worse,
  it is unknown (CC1, Logs 288-289), so nothing is compared.
- Same quantity first (GIRAFFE's TF activity is not network wiring), then
  evidence: direct > tested > descriptive > one result.
- The pool adds only the per-sample workflow a candidate's own cell names as
  stronger; no candidate is removed.
- A workflow is recommended only when the inputs it needs beyond expression
  are stated (Log 371 B4): TF priors by the data-facts call or a binding,
  miRNA by a quoted regulator reading or a binding, a design matrix by a
  verified two-group design or a binding.
- It must be the single best, and better than at least one candidate:
  otherwise the purpose does not separate them and nothing changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from workflow_registry import CLAIM_SUPPORT, REQUIRED_INPUTS, UNSUPPORTED_CLAIMS, ClaimSupport

from ..contracts import TaskDecision
from ..contracts.outcomes import AdvisoryCondition, AdvisoryRecommendation

__all__ = [
    "EVIDENCE_RANK", "PurposeSelection", "purpose_applies", "select_by_purpose", "with_purpose_selection",
]

EVIDENCE_RANK = {"direct": 4, "tested": 3, "descriptive": 2, "one_result": 1}
_TF_PRIORS = frozenset({"motif_file", "ppi_file"})
# Expression is what every listed workflow reads; outputs are written, not needed.
_ALWAYS = frozenset({"expression_file", "output_file", "lioness_output", "output_dir"})


@dataclass(frozen=True)
class PurposeSelection:
    """The chain for one request: its conclusion, each workflow's fit, the pick."""

    claim: str
    design: str
    quote: str
    fits: tuple[dict[str, Any], ...]
    recommended: str | None
    reason: str

    def record(self) -> dict[str, Any]:
        return {
            "claim": self.claim, "design": self.design, "quote": self.quote,
            "fits": list(self.fits), "recommended": self.recommended, "reason": self.reason,
        }


def _cell(action: str, claim: str, design: str) -> ClaimSupport | None:
    return CLAIM_SUPPORT.get((action, claim, design)) or CLAIM_SUPPORT.get((action, claim, "*"))


def purpose_applies(decision: TaskDecision, purpose) -> tuple[str, str] | None:
    """(claim, quote) when the purpose may decide this decision, else None."""
    if purpose is None or decision.action != "no_tool":
        return None
    if decision.capability_match_status != "ambiguous" or len(decision.outcome_hypotheses) > 1:
        return None
    if len(set(decision.hypothesis_actions)) < 2:
        return None
    if decision.stated_hypotheses or decision.advisory_recommendation is not None:
        return None
    claims = list(purpose.claims)
    if not claims or any(claim in UNSUPPORTED_CLAIMS for claim, _ in claims):
        return None
    return claims[0]


def _needs(action: str) -> frozenset[str]:
    return frozenset(REQUIRED_INPUTS.get(action, ())) - _ALWAYS


def _mirna_read(decision: TaskDecision) -> bool:
    """A regulator reading of miRNA that the request quotes."""
    return any(
        item.dimension == "regulator_type" and item.value == "mirna" and item.source == "explicit"
        for hypothesis in decision.outcome_hypotheses for item in hypothesis.evidence
    )


def _available(action: str, *, decision, purpose, priors: str | None, stated: dict) -> bool:
    for field in _needs(action):
        if stated.get(field):
            continue
        if field in _TF_PRIORS and priors == "stated":
            continue
        if field == "mirna_file" and _mirna_read(decision):
            continue
        if field == "design_file" and purpose.design == "groups":
            continue
        return False
    return True


def needs_tf_priors(decision: TaskDecision, purpose) -> bool:
    """Whether reading the request's TF priors could change the selection."""
    question = purpose_applies(decision, purpose)
    if question is None:
        return False
    claim, design = question[0], purpose.design or "*"
    pool = _pool(decision, claim, design)
    return any(_needs(action) & _TF_PRIORS for action in pool)


def _pool(decision: TaskDecision, claim: str, design: str) -> list[str]:
    candidates = list(dict.fromkeys(decision.hypothesis_actions))
    stronger = [
        other for action in candidates
        if (cell := _cell(action, claim, design)) is not None
        for other in cell.stronger
    ]
    return list(dict.fromkeys([*candidates, *stronger]))


def select_by_purpose(
    decision: TaskDecision, purpose, *, priors: str | None, stated: dict | None = None,
) -> PurposeSelection | None:
    """The purpose's pick among the tied workflows, with every workflow's fit."""
    question = purpose_applies(decision, purpose)
    if question is None:
        return None
    claim, quote = question
    design = purpose.design or "*"
    candidates = list(dict.fromkeys(decision.hypothesis_actions))
    pool = _pool(decision, claim, design)
    cells = {action: _cell(action, claim, design) for action in pool}
    fits = tuple(
        {
            "action": action,
            "candidate": action in candidates,
            "evidence": cell.evidence if cell else None,
            "quantity": cell.quantity if cell else None,
            "available": _available(action, decision=decision, purpose=purpose,
                                    priors=priors, stated=stated or {}),
        }
        for action, cell in cells.items()
    )

    def score(action: str) -> tuple[bool, int]:
        cell = cells[action]
        return cell.quantity == "same", EVIDENCE_RANK[cell.evidence]

    def chosen(recommended, reason):
        return PurposeSelection(claim, design, quote, fits, recommended, reason)

    if any(cells[action] is None for action in candidates):
        return chosen(None, "a candidate has no declared cell for this conclusion")
    usable = [fit["action"] for fit in fits if fit["available"] and cells[fit["action"]] is not None]
    if not usable:
        return chosen(None, "no workflow's needed inputs are stated")
    best_score = max(score(action) for action in usable)
    best = [action for action in usable if score(action) == best_score]
    if len(best) != 1:
        return chosen(None, "more than one workflow fits the conclusion best")
    if not any(score(action) < best_score for action in candidates):
        return chosen(None, "the conclusion does not separate the candidates")
    return chosen(best[0], "fits the stated conclusion best")


def with_purpose_selection(decision: TaskDecision, selection: PurposeSelection | None) -> TaskDecision:
    """Recommend the purpose's pick; add it to the options when a cell named it."""
    if selection is None or selection.recommended is None:
        return decision
    action = selection.recommended
    evidence = next(fit["evidence"] for fit in selection.fits if fit["action"] == action)
    advice = AdvisoryRecommendation(
        action=action,
        conditions=[AdvisoryCondition(
            axis="study_purpose", value=f"{selection.claim}:{evidence}:{selection.design}",
            text_span=selection.quote,
        )],
        supporting_spans=[selection.quote],
    )
    return decision.model_copy(update={
        "advisory_recommendation": advice,
        "hypothesis_actions": list(dict.fromkeys([*decision.hypothesis_actions, action])),
    })
