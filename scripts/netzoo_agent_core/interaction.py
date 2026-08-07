"""Compatibility facade for CLI interaction helpers."""

from .cli.clarification import (
    CLARIFICATION_FIELD_ALIASES,
    _candidate_selection,
    clarification_continuation,
    clarification_prompt,
    parse_clarification_assignments,
    preference_confirmation_prompt,
    preference_continuation,
    resolve_clarification,
)
from .cli.follow_up import (
    build_next_turn_prompt,
    follow_up_declined,
    follow_up_returns_to_main,
    initial_next_turn_prompt,
    render_next_turn_prompt,
    resolve_next_turn_input,
)

__all__ = [
    "CLARIFICATION_FIELD_ALIASES",
    "_candidate_selection",
    "parse_clarification_assignments",
    "clarification_continuation",
    "resolve_clarification",
    "clarification_prompt",
    "preference_confirmation_prompt",
    "preference_continuation",
    "initial_next_turn_prompt",
    "build_next_turn_prompt",
    "follow_up_declined",
    "render_next_turn_prompt",
    "follow_up_returns_to_main",
    "resolve_next_turn_input",
]
