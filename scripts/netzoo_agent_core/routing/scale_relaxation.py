"""An unstated scale must not rule out every workflow for a produced result (Log 281).

"For the same individuals I have expression and methylation" names matched
samples, yet the reading sometimes became a per-sample multi-omic network. No
registered workflow produces one, so a validated reading matched nothing and
the request got no workflow at all, although DRAGON produces exactly that
result for the cohort. When the request states no scale, the reading's scale is
an interpretation: it is dropped, the registered scale is said as an
assumption, and the match is guidance only (fallback, never exact). A scale
the request does state keeps the reading unsupported.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES

from ..contracts.outcomes import CapabilityMatch
from ..interpretation.request_integrity import granularity_mentions
from .requested_outcome_matching import match_requested_outcome

_SCALE_PHRASES = {"aggregate": "one result for the whole cohort", "sample_specific": "one result per sample"}


def _scale_note(actions) -> str:
    produced = "; ".join(
        f"{ACTION_DEFINITIONS[a].workflow} gives "
        + " or ".join(_SCALE_PHRASES[g] for g in sorted(OUTPUT_CAPABILITIES[a].granularities) if g in _SCALE_PHRASES)
        for a in actions
    )
    note = f"No scale was stated; {produced}."  # an assumption holds at most 160 characters
    return note if len(note) <= 160 else (
        "No scale was stated, so the assumed one was dropped; check what each listed workflow produces.")


def note_unstated_scale(task, decision):
    """Any path: never attribute an unstated scale that no chosen workflow produces.

    A validation failure reaches the workflow through the registry fallback,
    whose reply said "Your question asks for a per-sample multi-omic network"
    for a request that states no scale; DRAGON produces only a cohort result.
    """
    outcome = decision.requested_outcome
    actions = [a for a in (decision.matched_actions or decision.hypothesis_actions) if a in OUTPUT_CAPABILITIES]
    if (outcome is None or outcome.granularity not in _SCALE_PHRASES or not actions
            or any(outcome.granularity in OUTPUT_CAPABILITIES[a].granularities for a in actions)
            or granularity_mentions(task)):
        return decision
    relaxed = outcome.model_copy(update={"granularity": "unknown"})
    note = _scale_note(actions)
    hypotheses = [
        item.model_copy(update={
            "outcome": relaxed,
            "evidence": [e for e in item.evidence if e.dimension != "granularity"],
            "assumptions": list(dict.fromkeys([*item.assumptions, note])),
        }) if item.outcome == outcome else item
        for item in decision.outcome_hypotheses
    ]
    return decision.model_copy(update={"requested_outcome": relaxed, "outcome_hypotheses": hypotheses})


def relax_unstated_scale(task, interpretation, match):
    hypotheses = interpretation.outcome_hypotheses
    # No candidate at all: `unsupported`, or (guidance mode) `ambiguous` with an
    # empty list. A recorded mismatch (an input rejection, Log 250) is left alone.
    if (match.status not in {"unsupported", "ambiguous"} or match.matched_actions
            or match.hypothesis_actions or match.mismatch_dimensions or len(hypotheses) != 1):
        return interpretation, match
    hypothesis = hypotheses[0]
    outcome = hypothesis.outcome
    if outcome.granularity not in _SCALE_PHRASES or granularity_mentions(task):
        return interpretation, match
    relaxed = outcome.model_copy(update={"granularity": "unknown"})
    strict = match_requested_outcome(relaxed)
    actions = list(dict.fromkeys(strict.matched_actions or strict.hypothesis_actions))
    if not actions:
        return interpretation, match
    note = _scale_note(actions)
    kept = hypothesis.model_copy(update={
        "outcome": relaxed,
        "evidence": [item for item in hypothesis.evidence if item.dimension != "granularity"],
        "assumptions": [*hypothesis.assumptions, note],
    })
    return (
        interpretation.model_copy(update={"outcome_hypotheses": [kept]}),
        CapabilityMatch(
            status="fallback", match_basis="assumed_outcome",
            matched_actions=actions if len(actions) == 1 else [],
            hypothesis_actions=actions,
            clarification_question=None if len(actions) == 1 else strict.clarification_question,
            rejected_methods=match.rejected_methods,
        ),
    )
