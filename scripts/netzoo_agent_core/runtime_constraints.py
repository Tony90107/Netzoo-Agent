"""Current harness restrictions on otherwise registry-valid workflow controls.

The workflow registry describes what an algorithm supports.  This module
describes the narrower set the current execution runtime can actually honor.
Guidance and preflight share this seam so they cannot drift into contradictory
claims.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeControlConstraint:
    """Unavailable values for one workflow control in the current runtime."""

    unavailable_values: frozenset[str]
    message: str
    fallback: str | None = None

    def issue(self, value: object) -> str | None:
        return self.message if str(value).casefold() in self.unavailable_values else None


_CONSTRAINTS: dict[str, dict[str, RuntimeControlConstraint]] = {
    "run_otter": {
        "computing": RuntimeControlConstraint(
            unavailable_values=frozenset({"gpu"}),
            message=(
                "OTTER computing=gpu is not enabled by this Docker runtime; "
                "use computing=cpu."
            ),
            fallback="cpu",
        ),
    },
}


def runtime_control_constraints(
    action: str,
) -> dict[str, RuntimeControlConstraint]:
    """Return a copy of the current-runtime control policy for one action."""
    return dict(_CONSTRAINTS.get(action, {}))


__all__ = ["RuntimeControlConstraint", "runtime_control_constraints"]
