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
    intent_router: Any
    response_llm: Any
    router_model_name: str
    response_model_name: str
    semantic_prompt: str
    intent_prompt: str
    response_prompt: str
    router_max_tokens: int
    response_max_tokens: int
    task_token_budget: int


def record_event(
    context: _GraphContext,
    state: AgentState,
    event_type: str,
    node: str,
    payload: dict,
) -> None:
    context.recorder.append(state.get("run_id"), event_type, node, payload)


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
