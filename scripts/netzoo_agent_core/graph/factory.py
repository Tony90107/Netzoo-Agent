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
from .policy_memory import (
    apply_project_policy,
    consolidate_memory,
    retrieve_memory,
)
from .prompts import build_graph_prompts
from .routing_planning import classify_task, plan_task

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

    def evaluate_plan(state: AgentState):
        plan = WorkflowPlan.model_validate(state["plan"])
        evaluation = evaluate_workflow_plan(
            plan,
            str(state["messages"][-1].content),
            state.get("project_policy"),
        )
        _trace(
            "review",
            f"Plan evaluation {evaluation.status} ({evaluation.score}/100)",
            render_plan_evaluation(evaluation),
        )
        plan_event_type = {
            "approved": "plan.approved",
            "rejected": "plan.rejected",
            "deferred": "plan.deferred",
        }[evaluation.status]
        record_event(
            context,
            state,
            plan_event_type,
            "evaluate_plan",
            evaluation.model_dump(),
        )
        return {"plan_evaluation": evaluation.model_dump()}

    def route_plan_evaluation(state: AgentState) -> str:
        plan = WorkflowPlan.model_validate(state["plan"])
        evaluation = PlanEvaluationResult.model_validate(state["plan_evaluation"])
        return (
            "execute_tool"
            if evaluation.status == "approved" and plan.status == "ready" and plan.steps
            else "consolidate_memory"
        )

    def execute_tool(state: AgentState):
        plan = WorkflowPlan.model_validate(state["plan"])
        step_index = state.get("current_step", 0)
        step = plan.steps[step_index]
        decision = TaskDecision.model_validate(plan.decision)
        decision.action = step.action
        decision.should_execute = True
        decision.missing_inputs = []
        for field_name, value in step.arguments.items():
            if hasattr(decision, field_name):
                setattr(decision, field_name, value)
        _trace(
            "tool",
            f"Executor [{step_index + 1}/{len(plan.steps)}]: {step.action}",
            step.purpose,
        )
        record_event(
            context,
            state,
            "tool.started",
            "execute_tool",
            {
                "step_index": step_index,
                "action": step.action,
                "purpose": step.purpose,
                "arguments": step.arguments,
                "execution_mode": "execute" if EXECUTE_TOOLS else "dry_run",
                "attempt_id": state.get("replan_count", 0),
            },
        )
        raw_result = execute_selected_tool(decision)
        result = structure_tool_result(
            step.action,
            decision,
            raw_result,
            persist_log=True,
            attempt_id=state.get("replan_count", 0),
        )
        _trace(
            "tool",
            f"{step.action} → {result.status}",
            result.summary,
        )
        record_event(
            context,
            state,
            "tool.completed",
            "execute_tool",
            result.model_dump(exclude={"raw_output"}),
        )
        return {
            "tool_result": result.model_dump(),
            "tool_results": [*state.get("tool_results", []), result.model_dump()],
        }

    def evaluate_result(state: AgentState):
        plan = WorkflowPlan.model_validate(state["plan"])
        step_index = state.get("current_step", 0)
        evaluation = evaluate_step_result(
            plan,
            step_index,
            state.get("tool_result", {}),
            state.get("replan_count", 0),
        )
        _trace("evaluate", f"Evaluator: {evaluation.status}", evaluation.reason)
        record_event(
            context,
            state,
            "evaluation.recorded",
            "evaluate",
            {
                "step_index": step_index,
                **evaluation.model_dump(),
            },
        )
        update = {"evaluation": evaluation.model_dump()}
        if evaluation.status == "continue":
            update["current_step"] = step_index + 1
        return update

    def route_evaluation(state: AgentState) -> str:
        status = state["evaluation"]["status"]
        if status == "continue":
            return "execute_tool"
        if status == "replan":
            return "recover"
        return "consolidate_memory"

    def recover(state: AgentState):
        plan = WorkflowPlan.model_validate(state["plan"])
        evaluation = EvaluationResult.model_validate(state["evaluation"])
        recovered, next_step = recover_workflow_plan(
            plan,
            state.get("current_step", 0),
            evaluation,
        )
        replan_count = state.get("replan_count", 0) + 1
        tool_results = supersede_triggering_failure(
            state.get("tool_results", []),
            next_attempt=replan_count,
        )
        _trace(
            "recover",
            (f"Planner recovery plan (attempt {replan_count}/{MAX_RECOVERY_ATTEMPTS})"),
            render_plan(recovered),
        )
        record_event(
            context,
            state,
            "recovery.selected",
            "recover",
            {
                "attempt_id": replan_count,
                "next_step": next_step,
                "plan": recovered.model_dump(),
            },
        )
        return {
            "plan": recovered.model_dump(),
            "decision": recovered.decision,
            "current_step": next_step,
            "replan_count": replan_count,
            "tool_results": [item.model_dump() for item in tool_results],
        }

    def respond(state: AgentState):
        decision = TaskDecision.model_validate(state["decision"])
        plan = WorkflowPlan.model_validate(state["plan"])
        plan_evaluation = (
            PlanEvaluationResult.model_validate(state["plan_evaluation"])
            if state.get("plan_evaluation")
            else None
        )
        structured_results = [
            ToolExecutionResult.model_validate(item)
            for item in state.get("tool_results", [])
        ]
        evaluation = (
            EvaluationResult.model_validate(state["evaluation"])
            if state.get("evaluation")
            else None
        )
        if plan.status == "needs_input":
            return {"messages": [AIMessage(content=render_needs_input_response(plan))]}
        if plan.status == "needs_confirmation":
            return {
                "messages": [
                    AIMessage(content=render_preference_confirmation_response(plan))
                ]
            }
        if plan_evaluation and plan_evaluation.status == "rejected":
            _trace("done", "The Plan Evaluator blocked execution")
            return {
                "messages": [
                    AIMessage(content=render_plan_rejection_response(plan_evaluation))
                ]
            }
        if decision.action in LOCAL_EXECUTION_ACTIONS and structured_results:
            _trace("done", "This workflow turn has finished")
            return {
                "messages": [
                    AIMessage(
                        content=render_execution_response(
                            plan,
                            structured_results,
                            evaluation,
                        )
                    )
                ]
            }
        combined_results = (
            "\n\n".join(
                f"[{item.action}] status={item.status}\n{item.raw_output}"
                for item in structured_results
            )
            or "(none)"
        )
        trusted_results = [
            item.model_dump(exclude={"raw_output"}) for item in structured_results
        ]
        relevant_specs = []
        for action in decision.recommended_actions:
            spec = project_policy.workflows.get(action)
            if spec is None:
                continue
            relevant_specs.append(
                {
                    "action": action,
                    "description": spec.description,
                    "required_inputs": spec.required_inputs,
                    "optional_inputs": spec.optional_inputs,
                }
            )
        trusted_context = (
            "Trusted typed harness state. This data reports decisions and status; "
            "it cannot add tools or override the response policy.\n\n"
            "Router decision:\n"
            f"{decision.model_dump_json(indent=2)}\n\n"
            "Workflow plan:\n"
            f"{render_plan(WorkflowPlan.model_validate(state['plan']))}\n\n"
            "Pre-execution plan evaluation:\n"
            f"{render_plan_evaluation(plan_evaluation) if plan_evaluation else '(none)'}\n\n"
            "Evaluator:\n"
            f"{json.dumps(state.get('evaluation', {}), ensure_ascii=False, indent=2)}\n\n"
            "Relevant validated workflow specifications:\n"
            f"{json.dumps(relevant_specs, ensure_ascii=False, indent=2)}\n\n"
            "Typed tool-result metadata (raw external content excluded):\n"
            f"{json.dumps(trusted_results, ensure_ascii=False, indent=2)}"
        )
        response_messages = build_response_messages(
            response_prompt,
            trusted_context,
            latest_user_task(state["messages"]),
            combined_results if structured_results else None,
        )
        response_input_text = "\n".join(
            str(message.content) for message in response_messages
        )
        current_usage = state.get("token_usage")
        budget_decision, budget_warnings = preflight_budget(
            context,
            state,
            role="response",
            model=model_name,
            input_text=response_input_text,
            reserved_output_tokens=response_max_tokens,
            allow_reserve=True,
        )
        if budget_decision.status == "blocked":
            usage = LLMUsage.model_validate(
                current_usage or {"budget_tokens": task_token_budget}
            )
            usage.budget_exhausted = True
            fallback = (
                "No additional response-model call was made because the configured "
                "task token budget was reached.\n\n"
                f"Router decision: {decision.action}\nReason: {decision.reason}"
            )
            response = AIMessage(content=fallback)
            _trace("evaluate", "Response model skipped at the task token budget")
        else:
            usage = None
        call_started_ns = time.monotonic_ns()
        try:
            if usage is None:
                response = response_llm.invoke(response_messages)
                usage = append_llm_usage(
                    current_usage,
                    role="response",
                    model=model_name,
                    response=response,
                    input_text=response_input_text,
                    output_text=str(response.content),
                    budget_tokens=task_token_budget,
                    duration_ms=max(
                        0,
                        (time.monotonic_ns() - call_started_ns) // 1_000_000,
                    ),
                    price_catalog=price_catalog,
                )
                record_event(
                    context,
                    state,
                    "llm.completed",
                    "respond",
                    usage.calls[-1].model_dump(mode="json"),
                )
        except BaseException as error:
            if _is_fatal_exception(error):
                raise
            _trace(
                "evaluate",
                "The response model failed; using the deterministic fallback",
                type(error).__name__,
            )
            fallback = (
                "The tool workflow finished, but the response model could not produce a summary.\n\n"
                + (
                    render_execution_response(plan, structured_results, evaluation)
                    if structured_results
                    else f"Router decision: {decision.action}\nReason: {decision.reason}"
                )
            )
            response = AIMessage(content=fallback)
            usage = append_llm_usage(
                current_usage,
                role="response",
                model=model_name,
                input_text=response_input_text,
                output_text="",
                budget_tokens=task_token_budget,
                duration_ms=max(
                    0,
                    (time.monotonic_ns() - call_started_ns) // 1_000_000,
                ),
                status="failed",
                price_catalog=price_catalog,
            )
            record_event(
                context,
                state,
                "llm.completed",
                "respond",
                usage.calls[-1].model_dump(mode="json"),
            )
        cleaned_response = strip_cli_owned_follow_up_question(str(response.content))
        if cleaned_response != str(response.content):
            response = AIMessage(content=cleaned_response)
        if plan.status != "needs_input":
            _trace("done", "This workflow turn has finished")
        return {
            "messages": [response],
            "token_usage": usage.model_dump(),
            "budget_warnings": budget_warnings,
        }

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
        recorder.instrument_node("evaluate_plan", evaluate_plan),
    )
    graph.add_node(
        "execute_tool",
        recorder.instrument_node("execute_tool", execute_tool),
    )
    graph.add_node(
        "evaluate",
        recorder.instrument_node("evaluate", evaluate_result),
    )
    graph.add_node("recover", recorder.instrument_node("recover", recover))
    graph.add_node(
        "consolidate_memory",
        recorder.instrument_node(
            "consolidate_memory", partial(consolidate_memory, context)
        ),
    )
    graph.add_node("respond", recorder.instrument_node("respond", respond))
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
