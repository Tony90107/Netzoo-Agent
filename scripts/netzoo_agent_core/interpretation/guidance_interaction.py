"""One interaction policy for fallback answers, progress and follow-up controls."""
from dataclasses import dataclass

from ..contracts import TaskDecision


@dataclass(frozen=True)
class GuidanceInteraction:
    status: str
    progress: str
    explanation: str
    next_step: str
    question: str | None = None


def guidance_interaction(decision: TaskDecision) -> GuidanceInteraction | None:
    if decision.action != "no_tool" or decision.should_execute:
        return None
    if decision.capability_match_status != "fallback" and decision.match_basis not in {"semantic_validation_recovery", "provider_unavailable", "unverified_evidence"}:
        return None
    if decision.match_basis == "unverified_evidence":
        # Say the thing that actually happened. The message this replaces on
        # this path called routing "unavailable" and advised retrying "when
        # available" -- while routing had run, twice, and the wording it could
        # not match was still in the request, so an unchanged retry was certain
        # to fail again the same way.
        return GuidanceInteraction(
            "unverified_interpretation",
            "! Interpretation kept, but its quotes could not be matched to your wording",
            "The request was interpreted and a candidate was found, but at least one "
            "quote supporting that reading could not be located in your text -- often "
            "a spelling or rephrasing difference, sometimes a detail the reading added. "
            "So this is shown as a candidate rather than a verified match, and nothing "
            "will run from it. Please check that the reading matches what you meant.",
            "Rephrase the part that matters most, or confirm the reading above and "
            "restate your goal with the inputs you have. Repeating the request unchanged "
            "will reach the same result.",
        )
    question = decision.clarification_question
    if question:
        if decision.capability_match_status == "fallback":
            return GuidanceInteraction(
                "clarification_required",
                "? Clarification needed — Fallback recommendation is not an exact semantic match",
                "This is registry-based guidance, not an exact semantic match. " + question,
                "Answer the clarification above, ask a follow-up question, or describe another NetZoo goal.",
                question,
            )
        return GuidanceInteraction(
            "clarification_required", "? Clarification needed",
            "The requested result is not specific enough to select a workflow. "
            "No workflow has been selected. " + question,
            "Specify the requested result type and whether it should be aggregate "
            "or sample-specific. The workflow will be selected only after the result "
            "is clear; the captured inputs will be carried forward, and nothing will run yet.", question,
        )
    if not decision.recommended_actions and not decision.matched_actions:
        return GuidanceInteraction(
            "routing_unavailable", "! Semantic routing unavailable",
            "The system could not validate its interpretation. This is not evidence that your question is unclear.",
            "Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.",
        )
    return GuidanceInteraction(
        "fallback_guidance", "! Fallback recommendation — not an exact semantic match",
        "This is registry-based guidance, not an exact semantic match. "
        "The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. "
        "No clarification is required to read this recommendation, and no executable plan has been selected.",
        "Ask a follow-up question, or explicitly request a plan with your intended deliverable and inputs. "
        "A new request will be validated before planning; this candidate is not ready to start.",
    )
