"""Explicit conversation state.

Every field here was a local variable inside ``cli.conversation.run_conversation``.
Naming them is the whole point of the extraction: a second driver cannot share
a state machine whose state only exists in one function's stack frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts import FollowUpContext
from ..contracts.interaction import WorkflowContinuation
from ..contracts.planning import WorkflowPlan
from ..contracts.state import NextTurnPrompt

__all__ = ["ConversationState", "PreviewState"]


@dataclass(slots=True)
class PreviewState:
    """The validated dry-run preview ``/execute`` is allowed to act on."""

    task: str
    workflow: str | None
    plan: WorkflowPlan
    plan_evaluation: dict | None


@dataclass(slots=True)
class ConversationState:
    """Loop-carried state for one interactive conversation."""

    session_id: str
    conversation: list
    pending_plan: WorkflowPlan | None
    active_usage: dict | None
    run_id: str | None
    next_prompt: NextTurnPrompt
    one_shot: bool

    queued_task: str | None = None
    follow_up_context: FollowUpContext | None = None
    preview: PreviewState | None = None
    clarification_selections: dict[str, str] = field(default_factory=dict)
    custom_input_selection: bool = False
    input_confirmation_correction: bool = False
    execution_confirmation_task: str | None = None
    run_paused: bool = False

    # Set once an input phase has produced a task; consumed by the turn phase.
    pending_task: str | None = None
    pending_execute_once: bool = False
    pending_continuation: WorkflowContinuation | None = None

    def clear_pending_turn(self) -> None:
        self.pending_task = None
        self.pending_execute_once = False
        self.pending_continuation = None

    def clear_preview(self) -> None:
        self.preview = None
