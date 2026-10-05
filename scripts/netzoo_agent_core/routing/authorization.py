"""Operation authority: may the request's own words have this tool run now?

Tool suitability and operation authority are separate facts. The registry
match says which workflow produces the requested result; this module reads
whether the user asked for an operation now and which ones they forbade. Only
a forbidding clause or an explain-only request changes anything here, and only
by removing execution: suitability (matched and recommended actions) is kept.
"""

from __future__ import annotations

from workflow_registry import ActionName

from ..contracts import TaskDecision
from ..contracts.authorization import ForbiddenOperation, OperationAuthorization
from .capability import requested_operation_kinds
from .request_scope import operation_scope

__all__ = [
    "action_operation_kind",
    "enforce_operation_authorization",
    "forbidding_reason",
    "read_operation_authorization",
]

_RETRIEVAL_ACTIONS = frozenset({"web_search", "query_context7"})
_TRANSFORM_ACTIONS = frozenset({"format_expression"})


def action_operation_kind(action: str) -> str | None:
    """The operation an action performs; ``None`` for answering without a tool."""
    if action == "no_tool":
        return None
    if action in _RETRIEVAL_ACTIONS:
        return "retrieve"
    if action == "download_string":
        return "acquire"
    if action.startswith("inspect_"):
        return "inspect"
    if action in _TRANSFORM_ACTIONS:
        return "transform"
    return "run"


def read_operation_authorization(task: str) -> OperationAuthorization:
    """Read operation authority from the request's own words (no model call)."""
    scope = operation_scope(task)
    return OperationAuthorization(
        requested=list(requested_operation_kinds(task)),
        forbidden=[
            ForbiddenOperation(kind=ban.kind, tools=list(ban.tools), quote=ban.quote)
            for ban in scope.bans
        ],
        explain_only=scope.explain_only,
        preview_requested=scope.preview_requested,
    )


# Local analyses act only after the separate /execute confirmation; in a normal
# turn their plan is a preview. Searches, input checks and downloads act within
# the turn.
_DEFERRED_KINDS = frozenset({"run", "transform"})


def _forbidding_ban(
    authorization: OperationAuthorization, action: str,
) -> ForbiddenOperation | None:
    kind = action_operation_kind(action)
    if kind is None:
        return None
    if kind in _DEFERRED_KINDS and authorization.preview_requested:
        # "Prepare the PANDA dry-run plan; do not run the actual analysis":
        # the ban means not now. Refusing the plan would also refuse the
        # /execute the user may give later, which re-reads this request.
        return None
    for ban in authorization.forbidden:
        if ban.kind == "any":
            return ban
        if ban.kind == kind and (
            not ban.tools or any(tool in action.split("_") for tool in ban.tools)
        ):
            return ban
    return None


def forbidding_reason(authorization: OperationAuthorization, action: str) -> str | None:
    """Why the request's own words do not permit *action* now, or ``None``.

    A ban forbids its kind (or, for a run ban naming workflows, those
    workflows); beside a preview request a run ban means "not now" and leaves
    the preview. An explain-only request forbids every operation it does not
    also positively ask for elsewhere.
    """
    kind = action_operation_kind(action)
    if kind is None:
        return None
    if ban := _forbidding_ban(authorization, action):
        return f"The request forbids this operation: “{ban.quote}”."
    if authorization.explain_only and not (
        kind in authorization.requested
        or (kind in _DEFERRED_KINDS and ("run" in authorization.requested
                                         or authorization.preview_requested))
    ):
        return f"The request asks only for an explanation: “{authorization.explain_only}”."
    return None


def enforce_operation_authorization(
    decision: TaskDecision, task: str,
    authorization: OperationAuthorization | None = None,
) -> TaskDecision:
    """Refuse an execution the request's words forbid; never grant one.

    The capability fields (matched, recommended and candidate actions) are left
    as they are, so the reply can still say which tool fits; only the authority
    to run it now is removed.
    """
    authorization = authorization or read_operation_authorization(task)
    if authorization.is_empty:
        return decision
    reason = (
        forbidding_reason(authorization, decision.action)
        if decision.should_execute
        else None
    )
    if reason is None:
        return decision.model_copy(update={"operation_authorization": authorization})
    blocked: ActionName = decision.action
    return decision.model_copy(update={
        "action": "no_tool",
        "should_execute": False,
        "intent_type": "answer_question",
        "reason": f"{reason} No tool was run.",
        "missing_inputs": [],
        "operation_authorization": authorization.model_copy(
            update={"blocked_action": blocked}
        ),
    })
