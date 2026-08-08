"""Compatibility bridge for the few process-wide CLI settings.

New code should pass dependencies explicitly.  This bridge exists so the historical
``netzoo_agent`` facade and its tests can still override dry-run, trace, and storage
locations without knowing which internal module owns an implementation.
"""

from __future__ import annotations

import sys
from types import ModuleType


MUTABLE_RUNTIME_NAMES = frozenset(
    {
        "EXECUTE_TOOLS",
        "TRACE_ENABLED",
        "VERBOSE_OUTPUT",
        "TRANSIENT_TRACE",
        "PRESENTATION_MODE",
        "TRANSIENT_TRACE_MIN_SECONDS",
        "TOOL_TIMEOUT_SECONDS",
        "PROJECT_ROOT",
        "SESSION_ROOT",
        "TOOL_LOG_ROOT",
        "TRACE_ROOT",
        "PROFILE_ROOT",
        "EPISODE_ROOT",
    }
)


def set_runtime_value(name: str, value: object) -> None:
    """Set one legacy runtime value in every loaded implementation module."""
    if name not in MUTABLE_RUNTIME_NAMES:
        raise AttributeError(f"{name!r} is not a mutable NetZoo runtime setting")
    for module_name, module in tuple(sys.modules.items()):
        if module is None:
            continue
        if module_name == "netzoo_agent" or module_name.startswith(
            "netzoo_agent_core."
        ):
            if name in vars(module):
                ModuleType.__setattr__(module, name, value)


def configure_runtime(**values: object) -> None:
    """Apply a coherent group of CLI runtime settings."""
    unknown = set(values) - MUTABLE_RUNTIME_NAMES
    if unknown:
        raise AttributeError(
            "Unknown NetZoo runtime setting(s): " + ", ".join(sorted(unknown))
        )
    for name, value in values.items():
        set_runtime_value(name, value)


__all__ = ["MUTABLE_RUNTIME_NAMES", "configure_runtime", "set_runtime_value"]
