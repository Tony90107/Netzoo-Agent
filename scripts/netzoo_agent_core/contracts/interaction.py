"""Typed contracts for contextual CLI reply resolution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from workflow_registry import Granularity, RUN_ACTIONS, RecommendedAction

from ..settings import ROUTER_CONTEXT_MAX_CHARS

ReplyIntent = Literal[
    "follow_up",
    "new_goal",
    "accept_workflow",
    "needs_detail",
    "navigation",
]


class WorkflowConversationFact(BaseModel):
    """Bounded registry facts that may anchor a contextual follow-up."""

    action: RecommendedAction
    workflow: str = Field(min_length=1, max_length=80)
    required_inputs: list[str] = Field(default_factory=list, max_length=20)
    granularities: list[Granularity] = Field(default_factory=list, max_length=4)


class FollowUpContext(BaseModel):
    """Trusted prior-turn facts supplied to the conversational reply resolver."""

    prior_user_goal: str = Field(min_length=1, max_length=4_000)
    prompt_kind: str = Field(min_length=1, max_length=40)
    prompt_question: str = Field(min_length=1, max_length=600)
    candidate_actions: list[RecommendedAction] = Field(default_factory=list)
    candidate_workflows: list[WorkflowConversationFact] = Field(default_factory=list)
    continuation_action: RecommendedAction | None = None
    expected_field: str | None = Field(default=None, max_length=80)
    required_fields: list[str] = Field(default_factory=list, max_length=20)
    alternative_action: RecommendedAction | None = None


class ReplyIntentDecision(BaseModel):
    """Small LLM-facing classification with no workflow authority."""

    kind: ReplyIntent
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=240)
    selected_action: RecommendedAction | None = None
    selected_granularity: Granularity | None = None


class ContextualReplyResolution(BaseModel):
    """Validated conversational outcome consumed by the interactive CLI."""

    kind: ReplyIntent
    resolved_task: str | None = Field(default=None, max_length=8_000)
    reason: str = Field(min_length=1, max_length=240)
    selected_action: RecommendedAction | None = None
    selected_granularity: Granularity | None = None


class WorkflowContinuation(BaseModel):
    """CLI-selected workflow for one planning turn, never execution permission.

    Passed outside message text and bound to the current task so neither quoted
    markers nor a previous turn can supply a continuation for a new request.
    """

    model_config = ConfigDict(extra="forbid")

    action: RecommendedAction
    task: str = Field(min_length=1, max_length=ROUTER_CONTEXT_MAX_CHARS)

    @field_validator("action")
    @classmethod
    def local_workflow_only(cls, action: str) -> str:
        if action not in RUN_ACTIONS:
            raise ValueError("Only registered local workflows can be continued.")
        return action


__all__ = [
    "ContextualReplyResolution",
    "FollowUpContext",
    "ReplyIntent",
    "ReplyIntentDecision",
    "WorkflowConversationFact",
    "WorkflowContinuation",
]
