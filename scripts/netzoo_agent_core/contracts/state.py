"""Graph state, usage, prompt, and interruption contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from ..framework_compat import add_messages
from ..settings import DEFAULT_TASK_TOKEN_BUDGET
from ..trace_contracts import LLMCallUsage

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    decision: NotRequired[dict]
    plan: NotRequired[dict]
    plan_evaluation: NotRequired[dict]
    current_step: NotRequired[int]
    tool_result: NotRequired[dict]
    tool_results: NotRequired[list[dict]]
    evaluation: NotRequired[dict]
    replan_count: NotRequired[int]
    profile: NotRequired[dict]
    retrieved_episodes: NotRequired[list[dict]]
    project_policy: NotRequired[dict]
    token_usage: NotRequired[dict]
    run_id: NotRequired[str]
    budget_warnings: NotRequired[list[str]]
    semantic_goal: NotRequired[dict]

class AgentTurnInterrupted(Exception):
    """Raised when the user interrupts an in-flight graph turn."""

class ClarificationInputError(ValueError):
    """Raised when one reply cannot unambiguously resolve every displayed field."""

class LLMUsage(BaseModel):
    """Per-task token telemetry with explicit estimated/actual provenance."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: list[LLMCallUsage] = Field(default_factory=list)
    budget_tokens: int = DEFAULT_TASK_TOKEN_BUDGET
    budget_exhausted: bool = False

class NextTurnPrompt(BaseModel):
    """Outcome-aware CLI prompt plus optional workflow continuation context."""

    kind: Literal[
        "initial",
        "recommended_workflow",
        "dry_run",
        "completed",
        "failed",
        "plan_rejected",
        "unsupported",
        "retrieval",
    ]
    question: str
    continuation_action: str | None = None
    expected_field: str | None = None

__all__ = ['AgentState', 'AgentTurnInterrupted', 'ClarificationInputError', 'LLMUsage', 'NextTurnPrompt']
