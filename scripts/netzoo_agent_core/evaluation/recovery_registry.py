"""Code-owned recovery strategy registry and stable strategy interface."""

from __future__ import annotations

from types import MappingProxyType
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ..contracts import EvaluationResult, TaskDecision, WorkflowPlan

__all__ = [
    "RECOVERY_STRATEGIES",
    "RecoveryStrategy",
    "RecoveryValidation",
    "get_recovery_strategy",
]


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


from .recovery_strategies.puma_headerless import (  # noqa: E402
    PumaHeaderlessExpressionRecovery,
)


_puma_headerless = PumaHeaderlessExpressionRecovery()
RECOVERY_STRATEGIES = MappingProxyType({_puma_headerless.name: _puma_headerless})


def get_recovery_strategy(name: str | None) -> RecoveryStrategy | None:
    """Return a code-registered strategy; unknown data grants no authority."""
    if not name:
        return None
    return RECOVERY_STRATEGIES.get(name)
