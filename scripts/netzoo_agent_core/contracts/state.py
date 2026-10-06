"""Graph state, usage, prompt, and interruption contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from ..framework_compat import add_messages
from ..settings import DEFAULT_TASK_TOKEN_BUDGET
from ..trace_contracts import LLMCallUsage
from workflow_registry import Granularity, RecommendedAction

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
    requested_outcome: NotRequired[dict]
    outcome_hypotheses: NotRequired[list[dict]]
    capability_match: NotRequired[dict]
    workflow_continuation: NotRequired[dict | None]
    method_comparison: NotRequired[dict | None]
    # Plan item 2: what this turn's request states and forbids, read once from
    # the full message; planning and plan evaluation read it too.
    request_requirements: NotRequired[dict]
    # Which deterministic renderer wrote the reply; display metadata only.
    reply_kind: NotRequired[str]
    # Log 355: the verified study purpose of this turn's request (design, claims, source).
    study_purpose: NotRequired[dict | None]
    # Log 380 (plan item 4): what the request says about its TF priors and miRNA data.
    data_facts: NotRequired[dict | None]

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
        "clarify_outcome",
        "alternative_outcome",
    ]
    question: str
    allow_workflow_continuation: bool = True
    continuation_action: str | None = None
    expected_field: str | None = None
    required_fields: list[str] = Field(default_factory=list, max_length=20)
    alternative_action: RecommendedAction | None = None
    alternative_granularity: Granularity | None = None

__all__ = ['AgentState', 'AgentTurnInterrupted', 'ClarificationInputError', 'LLMUsage', 'NextTurnPrompt']
