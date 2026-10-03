"""Advisory matching of the practical concerns a request states (Log 223).

Once a workflow is selected, its guidance reply was a fixed specification sheet:
"it last ran out of memory and took forever to stop iterating" got OTTER's eight
controls listed with their defaults and no word on which of them answers it.
The registry now declares, per workflow, the concerns it can answer
(``REQUEST_CONCERNS``: an id, a label a user could state, a registry-owned note
and the controls or outputs it points to). This stage offers those concerns
and asks the model which ones the request states, with a quote, in a strict
schema whose concern ids are exactly the offered ones. The deterministic part
decides: every claim must be offered and its quote grounded in the request.

The result is advice for the reply. It never changes ``action``,
``should_execute``, ``capability_match_status`` or ``matched_actions``, and the
reply text is the registry's, never the model's.

Log 336: a later analysis the request states in words is a downstream_use
concern even when the model claims none. Test 10 ("we want a network for each
patient so we can model associations with disease stage and survival") got no
claim in 7 of 7 local rounds, so the registry's notes on relating per-sample
scores to survival were never shown. The quote is the request's own sentence.
"""

from __future__ import annotations

import re
import time
from typing import Literal

from pydantic import BaseModel, Field, create_model
from workflow_registry import REQUEST_CONCERNS

from ..contracts import AgentState, LLMUsage, TaskDecision
from ..contracts.outcomes import AddressedConcern, ConcernClaim, StatedConcernClaims
from ..contracts.strict_schema import strict_json_schema
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_request_concern_messages
from .condition_recommender import _quote_grounded, _sentence_at
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = [
    "addressed_from_claims",
    "witnessed_downstream_use",
    "concern_options",
    "concern_schema",
    "invoke_concern_matcher",
    "selected_guidance_actions",
]


def selected_guidance_actions(decision: TaskDecision) -> list[str]:
    """The workflows a guidance reply presents, as `render_verified_guidance` picks them."""
    return list(dict.fromkeys(decision.recommended_actions or decision.matched_actions))


def concern_options(actions: list[str]) -> list[tuple[str, str]]:
    """(concern id, label) declared by any of the actions, in declaration order."""
    options: dict[str, str] = {}
    for action in actions:
        for concern in REQUEST_CONCERNS.get(action, ()):
            options.setdefault(concern.concern, concern.label)
    return list(options.items())


class _StrictStatedConcernClaims(StatedConcernClaims):
    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        """The provider sees the strict-mode form; validation is unchanged (Log 208)."""
        return strict_json_schema(super().model_json_schema(*args, **kwargs))


def concern_schema(options: list[tuple[str, str]]) -> type[BaseModel]:
    """The claims schema for one call, its concern ids restricted to the offered ones."""
    offered = tuple(concern for concern, _ in options)
    claim = create_model(
        "ConcernClaim", __base__=ConcernClaim,
        concern=(Literal[offered], Field(description="One concern id exactly as offered in the option list.")),
    )
    return create_model(
        "StatedConcernClaims", __base__=_StrictStatedConcernClaims, __doc__=StatedConcernClaims.__doc__,
        claims=(list[claim], Field(default_factory=list, max_length=6)),
    )


# A later analysis of the result, in the request's words (Log 336): relating it
# to survival, stage, outcome or clinical variables, or a survival model.
_DOWNSTREAM_USE_WITNESS = re.compile(
    r"\b(?:model|test|relate|relating|associat\w*|correlat\w*|link)\b[^.;?!]{0,40}?\b(?:with|to|against)\b"
    r"[^.;?!]{0,30}?\b(?:survival|stages?|outcomes?|clinical|phenotypes?|grades?|prognos\w*|covariates?)\b"
    r"|\bCox\b|\bsurvival\s+analys\w*|\bprognos\w*",
    re.I,
)


def witnessed_downstream_use(user_task: str) -> str | None:
    """The request's sentence that states a downstream analysis, or None."""
    match = _DOWNSTREAM_USE_WITNESS.search(user_task)
    return _sentence_at(user_task, match.start(), match.end()) if match else None


def addressed_from_claims(
    user_task: str,
    claims: StatedConcernClaims,
    actions: list[str],
) -> tuple[list[AddressedConcern], list[dict]]:
    """Grounded, offered claims for each action declaring them, and every rejected claim.

    A downstream use the request states in words is added when no claim names it.
    """
    offered = {concern for concern, _ in concern_options(actions)}
    addressed: list[AddressedConcern] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for claim in claims.claims:
        if claim.concern not in offered:
            rejected.append({"concern": claim.concern, "reason": "not_offered"})
        elif not _quote_grounded(user_task, claim.text_span):
            rejected.append({"concern": claim.concern, "reason": "quote_not_in_request"})
        elif claim.concern not in seen:
            seen.add(claim.concern)
            addressed.extend(
                AddressedConcern(action=action, concern=claim.concern, text_span=claim.text_span)
                for action in actions
                if any(item.concern == claim.concern for item in REQUEST_CONCERNS.get(action, ()))
            )
    if "downstream_use" in offered and "downstream_use" not in seen:
        if span := witnessed_downstream_use(user_task):
            addressed.extend(
                AddressedConcern(action=action, concern="downstream_use", text_span=span)
                for action in actions
                if any(item.concern == "downstream_use" for item in REQUEST_CONCERNS.get(action, ()))
            )
    return addressed[:6], rejected


def invoke_concern_matcher(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    decision: TaskDecision,
    usage: LLMUsage,
    budget_warnings: list[str],
):
    """Attach the quoted concerns a selected workflow's guidance reply answers."""
    llm = getattr(context, "selection_condition_llm", None)
    if (
        llm is None
        or getattr(context, "semantic_claims", False)
        or decision.action != "no_tool"
        or decision.should_execute
        or decision.capability_match_status not in {"exact", "fallback"}
        or any(call.role == "hypothesis_bases" for call in usage.calls)
    ):
        return decision, usage, budget_warnings
    actions = selected_guidance_actions(decision)
    options = concern_options(actions)
    if not options:
        return decision, usage, budget_warnings
    messages = build_request_concern_messages(user_task, options)
    input_text = _serialized_structured_input(messages, StatedConcernClaims)
    semantic_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, semantic_state, role="request_concerns",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return decision, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    try:
        record_event(context, state, "routing.request_concerns_started", "classify", {
            "selected_actions": actions,
            "offered_concerns": [concern for concern, _ in options],
        })
        adapter = llm.with_structured_output(
            concern_schema(options), method="function_calling", include_raw=True, strict=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        claims = StatedConcernClaims.model_validate(payload)
        output_text = claims.model_dump_json()
        call_status = "success"
        addressed, rejected = addressed_from_claims(user_task, claims, actions)
        record_event(context, state, "routing.request_concerns_matched", "classify", {
            "claims": [item.model_dump() for item in claims.claims],
            "addressed": [item.model_dump() for item in addressed],
            "rejected": rejected,
        })
        if not addressed:
            return decision, usage, budget_warnings
        return decision.model_copy(update={"addressed_concerns": addressed}), usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.request_concerns_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
            "selected_actions": actions,
        })
        return decision, usage, budget_warnings
    finally:
        usage = append_llm_usage(
            usage, role="request_concerns", model=context.semantic_model_name,
            response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status=call_status, price_catalog=context.price_catalog,
        )
