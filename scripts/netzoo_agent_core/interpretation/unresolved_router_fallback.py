"""Safe final rendering when semantic routing cannot produce a decision."""

from __future__ import annotations

from ..contracts import TaskDecision
from .guidance_interaction import guidance_interaction
from .request_parameters import render_explicit_request_parameters

__all__: list[str] = []


def render_unresolved_router_fallback(decision: TaskDecision, task: str) -> str:
    interaction = guidance_interaction(decision)
    if interaction:
        parameter_echo = render_explicit_request_parameters(task)
        explanation = interaction.explanation
        if parameter_echo:
            explanation += "\n\n" + parameter_echo
        return (
            f"{decision.reason}\n\n{explanation}\n\n{interaction.next_step}\n\n"
            "No files were inspected and no analysis ran."
        )
    reason = decision.reason.strip()
    clarification = (
        decision.clarification_question.strip()
        if decision.clarification_question
        else "Please restate the desired NetZoo result after the router is available."
    )
    return f"{reason}\n\n{clarification}\n\nNo files were inspected and no analysis ran."
