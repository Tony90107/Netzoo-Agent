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
    if decision.capability_match_status != "fallback" and decision.match_basis not in {"semantic_validation_recovery", "provider_unavailable"}:
        return None
    question = decision.clarification_question
    if question:
        return GuidanceInteraction(
            "clarification_required", "! Fallback recommendation — not an exact semantic match",
            "This is registry-based guidance, not an exact semantic match. " + question,
            "Answer the clarification above, ask a follow-up question, or describe another NetZoo goal.", question,
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
