"""Shared return type for graph routing invocations."""

from dataclasses import dataclass

from ..contracts import LLMUsage, TaskDecision


@dataclass(frozen=True, slots=True)
class RouterInvocation:
    decision: TaskDecision
    routing_state: dict
    usage: LLMUsage
    budget_warnings: list[str]
    reason_code: str
