"""Exercise the actual terminal renderer and follow-up controls without tools."""
from contextlib import contextmanager, redirect_stdout
from io import StringIO

from .. import presentation
from ..cli.follow_up import build_next_turn_prompt, render_next_turn_prompt


@contextmanager
def capture_progress():
    """Isolated single-threaded CLI capture; restore every presentation global."""
    settings = dict(TRACE_ENABLED=True, PRESENTATION_MODE="state_machine", VERBOSE_OUTPUT=False, TRANSIENT_TRACE=False,
                    _PROGRESS_STATE=None, _PROGRESS_RENDERED_LINES=0,
                    _PROGRESS_LAST_TEXT=None, _COMMITTED_ACTIVITY_KEYS=set())
    saved = {key: getattr(presentation, key) for key in settings}
    stream = StringIO()
    try:
        for key, value in settings.items():
            setattr(presentation, key, value)
        with redirect_stdout(stream):
            yield stream
    finally:
        for key, value in saved.items():
            setattr(presentation, key, value)


def score_surface(decision, state, progress: str, answer: str) -> dict:
    prompt = build_next_turn_prompt(state)
    errors = []
    if "Clarification needed" in progress and not decision.clarification_question:
        errors.append("interaction: progress requests clarification without a question")
    if decision.capability_match_status == "fallback":
        if "Fallback recommendation" not in progress or "✓ Workflow —" in progress:
            errors.append("interaction: fallback presented as an exact match")
        if prompt.allow_workflow_continuation or prompt.continuation_action or prompt.expected_field or prompt.required_fields:
            errors.append("interaction: fallback exposes an unvalidated continuation")
        if "not an exact semantic match" not in answer:
            errors.append("interaction: answer hides fallback provenance")
        if "to start the recommended" in prompt.question:
            errors.append("interaction: next step starts an unvalidated candidate")
    if decision.clarification_question and decision.capability_match_status == "fallback":
        if decision.clarification_question not in answer or prompt.kind != "clarify_outcome":
            errors.append("interaction: genuine clarification is inconsistent")
    return {"progress": progress, "next_step": prompt.model_dump(), "next_step_text": render_next_turn_prompt(prompt),
            "interaction_passed": not errors, "interaction_errors": errors}
