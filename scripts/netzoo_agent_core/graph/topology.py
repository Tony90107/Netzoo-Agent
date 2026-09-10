"""Exact LangGraph node registration, instrumentation, and edge topology."""

from __future__ import annotations

from functools import partial

from ..contracts import AgentState, END, HumanMessage, START, StateGraph, SystemMessage
from .context import _GraphContext
from .execution import evaluate_plan, evaluate_result, execute_tool, recover
from .policy_memory import (
    apply_project_policy,
    consolidate_memory,
    retrieve_memory,
)
from .response import respond
from .routing_planning import classify_task, plan_task
from .transitions import route_evaluation, route_plan_evaluation

__all__: list[str] = []


def ensure_graph_dependencies() -> None:
    if StateGraph is None or HumanMessage is None or SystemMessage is None:
        raise RuntimeError(
            "LangChain/LangGraph dependencies are required to run the LLM agent. "
            "Install the project environment or use the Docker image."
        )


def compile_graph(context: _GraphContext, *, graph_cls=StateGraph):
    graph = graph_cls(AgentState)
    nodes = (
        ("apply_project_policy", apply_project_policy),
        ("classify", classify_task),
        ("retrieve_memory", retrieve_memory),
        ("plan", plan_task),
        ("evaluate_plan", evaluate_plan),
        ("execute_tool", execute_tool),
        ("evaluate", evaluate_result),
        ("recover", recover),
        ("consolidate_memory", consolidate_memory),
        ("respond", respond),
    )
    for name, node in nodes:
        graph.add_node(
            name,
            context.recorder.instrument_node(name, partial(node, context)),
        )

    graph.add_edge(START, "apply_project_policy")
    graph.add_edge("apply_project_policy", "classify")
    graph.add_edge("classify", "retrieve_memory")
    graph.add_edge("retrieve_memory", "plan")
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
