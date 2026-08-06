"""LangGraph orchestration across policy, planning, execution, and evaluation."""

from __future__ import annotations

import json
import time
from functools import partial


from workflow_registry import (
    LOCAL_EXECUTION_ACTIONS,
)

from ..contracts import (
    AIMessage,
    AgentState,
    AgentTurnInterrupted,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_MAX_TOKENS,
    DEFAULT_ROUTER_MAX_TOKENS,
    DEFAULT_ROUTER_MODEL,
    DEFAULT_TASK_TOKEN_BUDGET,
    END,
    EXECUTE_TOOLS,
    EvaluationResult,
    HumanMessage,
    LLMUsage,
    MAX_RECOVERY_ATTEMPTS,
    PROJECT_ROOT,
    PlanEvaluationResult,
    ProjectPolicySnapshot,
    RouterDecision,
    START,
    StateGraph,
    SystemMessage,
    TaskDecision,
    ToolExecutionResult,
    UserProfile,
    WorkflowPlan,
    _trace,
    _ui_text,
    strip_cli_owned_follow_up_question,
)

from ..memory import (
    EpisodeStore,
    UserProfileStore,
)

from ..routing import (
    execute_selected_tool,
    structure_tool_result,
)

from ..policy import (
    ProjectPolicyLoader,
)

from ..interpretation import (
    _is_fatal_exception,
    deterministic_router_fallback,
    hydrate_router_decision,
    repair_router_decision,
)

from ..planning import (
    build_workflow_plan,
    render_plan,
)

from ..evaluation import (
    evaluate_step_result,
    evaluate_workflow_plan,
    recover_workflow_plan,
    render_execution_response,
    render_needs_input_response,
    render_plan_evaluation,
    render_plan_rejection_response,
    render_preference_confirmation_response,
)

from ..llm import (
    append_llm_usage,
    build_llm,
    build_response_messages,
    build_router_messages,
    latest_user_task,
    structured_result_payload,
    validate_response_model,
    validate_router_model,
)
from ..outcomes import supersede_triggering_failure
from ..pricing import PriceCatalog
from ..tracing import NullTraceRecorder, TraceRecorder
from .context import _GraphContext, preflight_budget, record_event
from .execution import evaluate_plan, evaluate_result, execute_tool, recover
from .policy_memory import (
    apply_project_policy,
    consolidate_memory,
    retrieve_memory,
)
from .prompts import build_graph_prompts
from .response import respond
from .routing_planning import classify_task, plan_task
from .transitions import route_evaluation, route_plan_evaluation

__all__ = [
    "build_graph",
    "invoke_graph_turn",
]


def build_graph(
    model_name: str,
    temperature: float,
    profile_id: str = "default",
    profile_store: UserProfileStore | None = None,
    episode_store: EpisodeStore | None = None,
    project_policy: ProjectPolicySnapshot | None = None,
    router_model_name: str | None = None,
    router_max_tokens: int = DEFAULT_ROUTER_MAX_TOKENS,
    response_max_tokens: int = DEFAULT_RESPONSE_MAX_TOKENS,
    task_token_budget: int = DEFAULT_TASK_TOKEN_BUDGET,
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS,
    trace_recorder: TraceRecorder | None = None,
):
    if StateGraph is None or HumanMessage is None or SystemMessage is None:
        raise RuntimeError(
            "LangChain/LangGraph dependencies are required to run the LLM agent. "
            "Install the project environment or use the Docker image."
        )

    profile_store = profile_store or UserProfileStore()
    episode_store = episode_store or EpisodeStore()
    project_policy = project_policy or ProjectPolicyLoader(PROJECT_ROOT).load()
    recorder = trace_recorder or NullTraceRecorder()
    price_catalog = PriceCatalog.from_environment()
    ProjectPolicyLoader._validate_against_code(project_policy.workflows)
    router_model_name = validate_router_model(router_model_name or DEFAULT_ROUTER_MODEL)
    model_name = validate_response_model(model_name)
    router_llm = build_llm(
        router_model_name,
        0.0,
        max_output_tokens=router_max_tokens,
        timeout_seconds=timeout_seconds,
    )
    response_llm = build_llm(
        model_name,
        temperature,
        max_output_tokens=response_max_tokens,
        timeout_seconds=timeout_seconds,
    )
    router = router_llm.with_structured_output(
        RouterDecision,
        method="function_calling",
        include_raw=False,
    )

    prompts = build_graph_prompts(project_policy)
    routing_prompt = prompts.routing
    response_prompt = prompts.response
    context = _GraphContext(
        profile_id=profile_id,
        profile_store=profile_store,
        episode_store=episode_store,
        project_policy=project_policy,
        recorder=recorder,
        price_catalog=price_catalog,
        router=router,
        response_llm=response_llm,
        router_model_name=router_model_name,
        response_model_name=model_name,
        routing_prompt=routing_prompt,
        response_prompt=response_prompt,
        router_max_tokens=router_max_tokens,
        response_max_tokens=response_max_tokens,
        task_token_budget=task_token_budget,
    )

    graph = StateGraph(AgentState)
    graph.add_node(
        "apply_project_policy",
        recorder.instrument_node(
            "apply_project_policy", partial(apply_project_policy, context)
        ),
    )
    graph.add_node(
        "retrieve_memory",
        recorder.instrument_node(
            "retrieve_memory", partial(retrieve_memory, context)
        ),
    )
    graph.add_node(
        "classify",
        recorder.instrument_node("classify", partial(classify_task, context)),
    )
    graph.add_node(
        "plan",
        recorder.instrument_node("plan", partial(plan_task, context)),
    )
    graph.add_node(
        "evaluate_plan",
        recorder.instrument_node(
            "evaluate_plan", partial(evaluate_plan, context)
        ),
    )
    graph.add_node(
        "execute_tool",
        recorder.instrument_node("execute_tool", partial(execute_tool, context)),
    )
    graph.add_node(
        "evaluate",
        recorder.instrument_node("evaluate", partial(evaluate_result, context)),
    )
    graph.add_node(
        "recover",
        recorder.instrument_node("recover", partial(recover, context)),
    )
    graph.add_node(
        "consolidate_memory",
        recorder.instrument_node(
            "consolidate_memory", partial(consolidate_memory, context)
        ),
    )
    graph.add_node(
        "respond",
        context.recorder.instrument_node("respond", partial(respond, context)),
    )
    graph.add_edge(START, "apply_project_policy")
    graph.add_edge("apply_project_policy", "retrieve_memory")
    graph.add_edge("retrieve_memory", "classify")
    graph.add_edge("classify", "plan")
    graph.add_edge("plan", "evaluate_plan")
    graph.add_conditional_edges(
        "evaluate_plan",
        route_plan_evaluation,
        {"execute_tool": "execute_tool", "consolidate_memory": "consolidate_memory"},
    )
    graph.add_edge("execute_tool", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        route_evaluation,
        {
            "execute_tool": "execute_tool",
            "recover": "recover",
            "consolidate_memory": "consolidate_memory",
        },
    )
    graph.add_edge("recover", "evaluate_plan")
    graph.add_edge("consolidate_memory", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


def invoke_graph_turn(app, invocation: dict):
    """Invoke one graph turn without leaking a Ctrl-C traceback to the CLI."""
    try:
        return app.invoke(invocation)
    except KeyboardInterrupt as error:
        raise AgentTurnInterrupted from error
