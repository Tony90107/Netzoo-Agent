"""Typed contracts for contextual CLI reply resolution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import Granularity, RecommendedAction

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


__all__ = [
    "ContextualReplyResolution",
    "FollowUpContext",
    "ReplyIntent",
    "ReplyIntentDecision",
    "WorkflowConversationFact",
]
