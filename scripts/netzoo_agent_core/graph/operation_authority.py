"""Apply the request's own operation bans to the routed decision."""

from __future__ import annotations

from dataclasses import replace

from ..contracts import AgentState
from ..contracts.requirements import RequestRequirements
from ..routing.authorization import enforce_operation_authorization
from .context import _GraphContext, record_event
from .invocation_types import RouterInvocation

__all__ = ["with_operation_authority"]


def with_operation_authority(
    context: _GraphContext,
    state: AgentState,
    requirements: RequestRequirements,
    invocation: RouterInvocation,
) -> RouterInvocation:
    """Refuse what the request forbids, after every routing path.

    Every routing stage (model intent, deterministic reconciliation, fallbacks,
    continuations) may propose execution; none may run what the request's own
    words forbid. This only removes authority, so it is safe after any path,
    and it leaves the capability match (which tool fits) as it was. The bans
    come from the turn's requirements, read from the full message, so one
    beyond the routing window still holds (F3).
    """
    decision = enforce_operation_authorization(
        invocation.decision, "", authorization=requirements.operations,
    )
    authorization = decision.operation_authorization
    if authorization is None:
        return invocation
    if authorization.blocked_action is not None:
        record_event(context, state, "routing.operation_forbidden", "classify", {
            "blocked_action": authorization.blocked_action,
            "forbidden": [item.model_dump() for item in authorization.forbidden],
            "explain_only": authorization.explain_only,
        })
    elif authorization.forbidden or authorization.explain_only:
        record_event(context, state, "routing.operation_restrictions_read", "classify", {
            "forbidden": [item.model_dump() for item in authorization.forbidden],
            "explain_only": authorization.explain_only,
        })
    return replace(invocation, decision=decision)
