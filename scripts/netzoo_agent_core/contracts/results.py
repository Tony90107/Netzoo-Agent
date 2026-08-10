"""Plan-evaluation and tool-execution result contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PUMA_EXPRESSION_HEADER_UNSUPPORTED = "PUMA_EXPRESSION_HEADER_UNSUPPORTED"

class EvaluationResult(BaseModel):
    status: Literal["continue", "completed", "needs_input", "replan", "failed"]
    reason: str
    recovery_action: str | None = None
    recovery_error_code: str | None = None

class PlanRubricItem(BaseModel):
    """One machine-readable pre-execution planning criterion."""

    criterion: str
    required: bool = True
    result: Literal["pass", "fail", "not_applicable"]
    detail: str

class PlanEvaluationResult(BaseModel):
    """Code-enforced verdict produced before any workflow tool may execute."""

    status: Literal["approved", "deferred", "rejected"]
    score: int = Field(ge=0, le=100)
    summary: str
    rubric: list[PlanRubricItem] = Field(default_factory=list)

class ArtifactValidationResult(BaseModel):
    """Structural verification outcome for files produced by one workflow."""

    ok: bool
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)

class ToolExecutionResult(BaseModel):
    """Stable contract between Executor and Evaluator."""

    action: str
    status: Literal["success", "dry_run", "failed"]
    summary: str
    attempt_id: int = Field(default=0, ge=0)
    superseded: bool = False
    superseded_reason: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    error_code: str | None = None
    retryable: bool = False
    recovery_hint: str | None = None
    log_file: str | None = None
    raw_output: str = ""

__all__ = ['EvaluationResult', 'PlanRubricItem', 'PlanEvaluationResult', 'ArtifactValidationResult', 'ToolExecutionResult']
