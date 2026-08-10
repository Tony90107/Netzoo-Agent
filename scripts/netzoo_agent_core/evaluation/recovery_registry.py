"""Code-owned recovery strategy registry and stable strategy interface."""

from __future__ import annotations

from types import MappingProxyType

from .recovery_contracts import RecoveryStrategy, RecoveryValidation

__all__ = [
    "RECOVERY_STRATEGIES",
    "RecoveryStrategy",
    "RecoveryValidation",
    "get_recovery_strategy",
]

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
