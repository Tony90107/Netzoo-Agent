"""Deterministic routing when the configured provider cannot respond."""

from __future__ import annotations

from ..contracts import TaskDecision

__all__: list[str] = []


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Fail closed when semantic routing is unavailable; never infer from text."""
    error_detail = f" ({type(error).__name__})" if error is not None else ""
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="unknown",
        confidence=0.0,
        reason="The LLM router was unavailable, so no workflow was selected." + error_detail,
        clarification_question=(
            "Please restate the desired NetZoo result after the router is available."
        ),
    )


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))
