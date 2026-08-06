from __future__ import annotations

import hashlib
import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.graph as graph  # noqa: E402


PUBLIC_EXPORTS = ["build_graph", "invoke_graph_turn"]
BUILD_GRAPH_SIGNATURE = (
    "(model_name: 'str', temperature: 'float', profile_id: 'str' = 'default', "
    "profile_store: 'UserProfileStore | None' = None, episode_store: "
    "'EpisodeStore | None' = None, project_policy: 'ProjectPolicySnapshot | None' "
    "= None, router_model_name: 'str | None' = None, router_max_tokens: 'int' "
    "= 500, response_max_tokens: 'int' = 800, task_token_budget: 'int' = 20000, "
    "timeout_seconds: 'float' = 30.0, trace_recorder: 'TraceRecorder | None' = None)"
)


def test_graph_public_surface_is_characterized():
    assert graph.__all__ == PUBLIC_EXPORTS
    assert str(inspect.signature(graph.build_graph)) == BUILD_GRAPH_SIGNATURE
    assert str(inspect.signature(graph.invoke_graph_turn)) == "(app, invocation: 'dict')"
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(graph, name)


def test_invoke_graph_turn_translates_keyboard_interrupt():
    class InterruptedApp:
        def invoke(self, invocation):
            raise KeyboardInterrupt

    with pytest.raises(legacy_agent.AgentTurnInterrupted):
        graph.invoke_graph_turn(InterruptedApp(), {"messages": []})


def test_graph_is_a_package_with_factory_child():
    assert hasattr(graph, "__path__")
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    assert factory.build_graph is graph.build_graph
    assert factory.invoke_graph_turn is graph.invoke_graph_turn


def test_graph_package_exports_only_public_entrypoints():
    assert graph.__all__ == PUBLIC_EXPORTS
