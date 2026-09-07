"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import ValidationError

from ..contracts import TaskDecision
__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Fail closed when semantic routing is unavailable; never infer from text."""
    error_detail = f" ({type(error).__name__})" if error is not None else ""
    if isinstance(error, (ValidationError, ValueError)):
        reason = (
            "Semantic routing output failed validation, so no workflow was selected."
            + error_detail
        )
    else:
        reason = (
            "The LLM router was unavailable, so no workflow was selected."
            + error_detail
        )
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="unknown",
        confidence=0.0,
        reason=reason,
        match_basis="semantic_validation_recovery" if isinstance(error, (ValidationError, ValueError)) else "provider_unavailable",
    )


def recover_registry_guidance(
    task: str,
    workflows: Mapping[str, object],
    error: BaseException | None = None,
) -> TaskDecision | None:
    """Compatibility entry point: failed semantics never selects a tool from text."""
    return None


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
