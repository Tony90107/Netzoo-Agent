"""Typed interface shared by recovery registries and strategy adapters."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ..contracts import EvaluationResult, TaskDecision, WorkflowPlan

__all__ = ["RecoveryStrategy", "RecoveryValidation"]


class RecoveryValidation(BaseModel):
    """One registered strategy's validation of recovery provenance and steps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ok: bool
    detail: str
    failures: list[str] = Field(default_factory=list)
    expected_steps: list[str] = Field(default_factory=list)


class RecoveryStrategy(Protocol):
    """Apply and validate one bounded, code-authorized plan transformation."""

    name: str
    applicable_actions: frozenset[str]
    accepted_error_codes: frozenset[str]

    def accepts(self, *, action: str, error_code: str | None) -> bool: ...

    def apply(
        self,
        plan: WorkflowPlan,
        step_index: int,
        evaluation: EvaluationResult,
    ) -> tuple[WorkflowPlan, int]: ...

    def validate_evidence(
        self,
        plan: WorkflowPlan,
        decision: TaskDecision,
    ) -> list[str]: ...

    def validate(
        self,
        plan: WorkflowPlan,
        decision: TaskDecision,
        normal_steps: list[str],
    ) -> RecoveryValidation: ...
