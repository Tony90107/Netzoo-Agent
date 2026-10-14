"""The methods and settings a request can name, as the registry registers them (M1, 2026-10-14).

The capability check's schema offers these as enums (`contracts.capability_check`), so this module depends on the
registry alone; the limits each workflow is held to are `workflow_conditions`'.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS

__all__ = ["LIONESS_FAMILY", "UNREGISTERED", "method_names", "named_workflows", "registered_workflows",
           "setting_names"]

LIONESS_FAMILY = "LIONESS"
"""A named method that stands for every registered LIONESS-X workflow."""

UNREGISTERED = "unregistered"
"""A named method or setting that no registered workflow has."""


def registered_workflows() -> dict[str, str]:
    """Each registered run workflow's action, by workflow name."""
    return {ACTION_DEFINITIONS[action].workflow: action for action in sorted(RUN_ACTIONS)}


def method_names() -> tuple[str, ...]:
    """The methods a request can name: each registered workflow, and the LIONESS family."""
    return (*sorted(registered_workflows()), LIONESS_FAMILY)


def named_workflows(method: str) -> frozenset[str]:
    """The registered workflows a named method stands for: itself and its LIONESS-X version, if registered.

    LIONESS stands for every LIONESS-X. An unregistered name stands for none -- so a LIONESS version of a method
    that has none here (LIONESS-OTTER) is never another workflow.
    """
    known = registered_workflows()
    if method == LIONESS_FAMILY:
        return frozenset(name for name in known if name.startswith(f"{LIONESS_FAMILY}-"))
    if method not in known:
        return frozenset()
    return frozenset(name for name in (method, f"{LIONESS_FAMILY}-{method}") if name in known)


def setting_names() -> tuple[str, ...]:
    """Every setting a request can give, as WORKFLOW.control."""
    return tuple(f"{workflow}.{control.name}" for workflow, action in sorted(registered_workflows().items())
                 for control in ACTION_DEFINITIONS[action].controls)
