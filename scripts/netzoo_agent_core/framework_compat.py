"""Optional LangChain and LangGraph imports with local test fallbacks."""

from __future__ import annotations

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.tools import tool
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages
except ImportError:
    from inspect import Parameter, signature
    from typing import Any, get_type_hints

    from pydantic import create_model

    END = START = StateGraph = None

    class _LocalMessage:
        type = "message"

        def __init__(self, content: str):
            self.content = content

    class AIMessage(_LocalMessage):
        type = "ai"

    class HumanMessage(_LocalMessage):
        type = "human"

    class SystemMessage(_LocalMessage):
        type = "system"

    def add_messages(messages):
        return messages

    class _LocalTool:
        def __init__(self, func):
            self.func = func
            self.name = func.__name__
            self.description = func.__doc__ or ""
            hints = get_type_hints(func)
            fields: dict[str, tuple[object, object]] = {}
            for name, parameter in signature(func).parameters.items():
                if parameter.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
                    continue
                annotation = hints.get(name, Any)
                default = (
                    ...
                    if parameter.default is Parameter.empty
                    else parameter.default
                )
                fields[name] = (annotation, default)
            self.args_schema = create_model(f"{self.name.title()}Input", **fields)

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        def invoke(self, arguments):
            if isinstance(arguments, dict):
                return self.func(**arguments)
            return self.func(arguments)

    def tool(func):
        return _LocalTool(func)

__all__ = [
    "AIMessage",
    "HumanMessage",
    "SystemMessage",
    "tool",
    "END",
    "START",
    "StateGraph",
    "add_messages",
]
