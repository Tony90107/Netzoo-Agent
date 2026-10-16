"""Graph-lifetime dependencies, trace recording, and budget preflight."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contracts import AgentState, ProjectPolicySnapshot
from ..llm import _estimated_tokens, evaluate_budget_call
from ..memory import EpisodeStore, UserProfileStore
from ..pricing import PriceCatalog
from ..tracing import NullTraceRecorder, TraceRecorder

__all__: list[str] = []


@dataclass(frozen=True, slots=True)
class _GraphContext:
    profile_id: str
    profile_store: UserProfileStore
    episode_store: EpisodeStore
    project_policy: ProjectPolicySnapshot
    recorder: TraceRecorder | NullTraceRecorder
    price_catalog: PriceCatalog
    semantic_interpreter: Any
    semantic_reviewer: Any
    intent_router: Any
    input_content_mapper: Any
    response_llm: Any
    semantic_model_name: str
    router_model_name: str
    response_model_name: str
    semantic_prompt: str
    intent_prompt: str
    response_prompt: str
    router_max_tokens: int
    response_max_tokens: int
    task_token_budget: int
    # Optional: when absent the review returns a whole SemanticReview, which
    # is also the path taken whenever the first pass was not schema-valid.
    semantic_patcher: Any = None
    semantic_claims: bool = False
    # Historical replay defaults to its original always-review behavior.
    # The production factory explicitly selects when_needed.
    review_policy: str = "always"
    semantic_discriminator: Any = None
    # Log 139: the semantic model, bound to SelectionConditionClaims lazily and
    # only when a method tie occurs, so graph construction binds nothing new.
    # Log 198 binds it the same way to a per-call strict evidence-supply schema.
    selection_condition_llm: Any = None
    # Log 355: the model bound per call to StudyPurposeProposal; None (tests, the
    # routing harness) keeps the word witnesses as the only reading.
    study_purpose_llm: Any = None


def record_event(
    context: _GraphContext,
    state: AgentState,
    event_type: str,
    node: str,
    payload: dict,
) -> None:
    context.recorder.append(state.get("run_id"), event_type, node, payload)


def record_core_view(context: _GraphContext, state: AgentState, result: dict) -> dict:
    """Core decision spec, phase 0: record the reply that answered beside the turn's core call (`core.view`)."""
    if getattr(context, "recorder", None) is not None:  # reply-only test contexts carry no recorder
        from ..interpretation.core_views import ALLOWED

        core = (state.get("decision") or {}).get("core") or {}
        kind = result.get("reply_kind") or ""
        record_event(context, state, "core.view", "respond", {
            "reply_kind": kind, "core_kind": core.get("kind"), "basis": core.get("basis"),
            # Phase 3: the convergence check -- a renderer that is not one of its call's.
            "mismatch": bool(core.get("kind")) and kind not in ALLOWED.get(core.get("kind"), frozenset())})
    return result


def preflight_budget(
    context: _GraphContext,
    state: AgentState,
    *,
    role: str,
    model: str,
    input_text: str,
    reserved_output_tokens: int,
    allow_reserve: bool,
):
    decision = evaluate_budget_call(
        state.get("token_usage"),
        estimated_input_tokens=_estimated_tokens(input_text),
        reserved_output_tokens=reserved_output_tokens,
        budget_tokens=context.task_token_budget,
        allow_reserve=allow_reserve,
    )
    emitted = list(state.get("budget_warnings", []))
    if decision.status in {"warning_70", "warning_85"}:
        if decision.status not in emitted:
            record_event(
                context,
                state,
                "budget.warning",
                role,
                {
                    "role": role,
                    "model": model,
                    **decision.model_dump(),
                },
            )
            emitted.append(decision.status)
    elif decision.status == "blocked":
        record_event(
            context,
            state,
            "budget.blocked",
            role,
            {
                "role": role,
                "model": model,
                **decision.model_dump(),
            },
        )
    return decision, emitted
