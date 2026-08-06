"""Dispatch one authorized action to an allow-listed implementation."""

from __future__ import annotations

from workflow_registry import executor_arguments

from ..contracts import TaskDecision
from ..execution import LOCAL_TOOL_EXECUTORS
from .retrieval import query_context7_docs, query_web_search

__all__ = ["execute_selected_tool"]


def execute_selected_tool(decision: TaskDecision) -> str:
    """Invoke exactly one allow-listed tool after the capability gate passes."""
    executor = LOCAL_TOOL_EXECUTORS.get(decision.action)
    if executor is not None:
        return executor.invoke(executor_arguments(decision.action, decision))
    if decision.action == "query_context7":
        return query_context7_docs(
            library_name=decision.library_name,
            query=decision.docs_query,
            library_id=decision.library_id,
        )
    if decision.action == "web_search":
        return query_web_search(decision.web_query)
    raise ValueError(f"Unsupported tool action: {decision.action}")
