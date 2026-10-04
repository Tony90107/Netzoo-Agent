"""Public graph construction from validated runtime dependencies."""

from __future__ import annotations

from typing import Literal

from ..contracts import (
    AgentTurnInterrupted,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_MAX_TOKENS,
    DEFAULT_ROUTER_MAX_TOKENS,
    DEFAULT_ROUTER_MODEL,
    DEFAULT_TASK_TOKEN_BUDGET,
    PROJECT_ROOT,
    ProjectPolicySnapshot,
    IntentDecision,
    StateGraph,
)
from ..llm import build_llm, validate_response_model, validate_router_model
from ..contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
from ..contracts.outcomes import SemanticDiscriminator, SemanticInterpretation, SemanticReview, SemanticPatch
from ..memory import EpisodeStore, UserProfileStore
from ..policy import ProjectPolicyLoader
from ..pricing import PriceCatalog
from ..tracing import NullTraceRecorder, TraceRecorder
from .context import _GraphContext
from .prompts import build_graph_prompts
from .topology import compile_graph, ensure_graph_dependencies

__all__ = ["build_graph", "invoke_graph_turn"]


def build_graph(
    model_name: str,
    temperature: float,
    profile_id: str = "default",
    profile_store: UserProfileStore | None = None,
    episode_store: EpisodeStore | None = None,
    project_policy: ProjectPolicySnapshot | None = None,
    router_model_name: str | None = None,
    semantic_model_name: str | None = None,
    router_max_tokens: int = DEFAULT_ROUTER_MAX_TOKENS,
    response_max_tokens: int = DEFAULT_RESPONSE_MAX_TOKENS,
    task_token_budget: int = DEFAULT_TASK_TOKEN_BUDGET,
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS,
    trace_recorder: TraceRecorder | None = None,
    semantic_contract: Literal["claims", "legacy"] = "legacy",
    review_policy: Literal["when_needed", "always"] = "when_needed",
):
    if semantic_contract not in {"claims", "legacy"}:
        raise ValueError("Unknown semantic contract")
    if review_policy not in {"when_needed", "always"}:
        raise ValueError("Unknown review policy")
    ensure_graph_dependencies()
    profile_store = profile_store or UserProfileStore()
    episode_store = episode_store or EpisodeStore()
    project_policy = project_policy or ProjectPolicyLoader(PROJECT_ROOT).load()
    recorder = trace_recorder or NullTraceRecorder()
    price_catalog = PriceCatalog.from_environment()
    ProjectPolicyLoader._validate_against_code(project_policy.workflows)
    router_model_name = validate_router_model(router_model_name or DEFAULT_ROUTER_MODEL)
    semantic_model_name = validate_router_model(
        semantic_model_name or router_model_name
    )
    model_name = validate_response_model(model_name)
    router_llm = build_llm(
        router_model_name,
        0.0,
        max_output_tokens=router_max_tokens,
        timeout_seconds=timeout_seconds,
    )
    semantic_llm = (
        router_llm
        if semantic_model_name == router_model_name
        else build_llm(
            semantic_model_name,
            0.0,
            max_output_tokens=router_max_tokens,
            timeout_seconds=timeout_seconds,
        )
    )
    response_llm = build_llm(
        model_name,
        temperature,
        max_output_tokens=response_max_tokens,
        timeout_seconds=timeout_seconds,
    )
    semantic_options = {"method": "function_calling", "include_raw": True}
    if semantic_contract == "claims":
        semantic_options["strict"] = True
    semantic_interpreter = semantic_llm.with_structured_output(
        SemanticClaims if semantic_contract == "claims" else SemanticInterpretation,
        **semantic_options,
    )
    semantic_reviewer = semantic_llm.with_structured_output(
        SemanticClaims if semantic_contract == "claims" else SemanticReview,
        **semantic_options,
    )
    semantic_patcher = semantic_llm.with_structured_output(  # the patch is strict (Log 208)
        SemanticClaimRepair if semantic_contract == "claims" else SemanticPatch,
        **{**semantic_options, "strict": True},
    )
    semantic_discriminator = semantic_llm.with_structured_output(SemanticDiscriminator, method="function_calling", include_raw=True)
    intent_router = router_llm.with_structured_output(
        IntentDecision,
        method="function_calling",
        include_raw=False,
    )
    # Content mapping binds the structured schema lazily, only when a workflow
    # has unresolved file roles. This keeps the graph's stable router contract
    # unchanged while still making a real LLM call for the fallback.
    input_content_mapper = router_llm
    prompts = build_graph_prompts(project_policy)
    context = _GraphContext(
        profile_id=profile_id,
        profile_store=profile_store,
        episode_store=episode_store,
        project_policy=project_policy,
        recorder=recorder,
        price_catalog=price_catalog,
        semantic_interpreter=semantic_interpreter,
        semantic_reviewer=semantic_reviewer,
        semantic_patcher=semantic_patcher,
        semantic_discriminator=semantic_discriminator,
        selection_condition_llm=semantic_llm,
        study_purpose_llm=semantic_llm,
        semantic_claims=semantic_contract == "claims",
        review_policy=review_policy,
        intent_router=intent_router,
        input_content_mapper=input_content_mapper,
        response_llm=response_llm,
        semantic_model_name=semantic_model_name,
        router_model_name=router_model_name,
        response_model_name=model_name,
        semantic_prompt=prompts.semantic,
        intent_prompt=prompts.intent,
        response_prompt=prompts.response,
        router_max_tokens=router_max_tokens,
        response_max_tokens=response_max_tokens,
        task_token_budget=task_token_budget,
    )
    return compile_graph(context, graph_cls=StateGraph)


def invoke_graph_turn(app, invocation: dict):
    """Invoke one graph turn without leaking a Ctrl-C traceback to the CLI."""
    try:
        return app.invoke(invocation)
    except KeyboardInterrupt as error:
        raise AgentTurnInterrupted from error
