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
    "= 1200, response_max_tokens: 'int' = 800, task_token_budget: 'int' = 20000, "
    "timeout_seconds: 'float' = 30.0, trace_recorder: 'TraceRecorder | None' = None)"
)
RESPONSE_PROMPT_SHA256 = "7a93cdf9d10628fcb8de5c7b6c292bb40c6b7b97da0e924e858fa805f9f6a8a0"


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


def test_response_prompt_is_byte_characterized(monkeypatch):
    prompts = importlib.import_module("netzoo_agent_core.graph.prompts")
    monkeypatch.setattr(prompts, "EXECUTE_TOOLS", False)
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()

    result = prompts.build_graph_prompts(policy)

    assert (
        hashlib.sha256(result.response.encode("utf-8")).hexdigest()
        == RESPONSE_PROMPT_SHA256
    )
    assert result.routing == legacy_agent.build_routing_prompt(policy)


def test_record_event_uses_run_id_and_exact_payload():
    context_module = importlib.import_module("netzoo_agent_core.graph.context")
    calls = []
    runtime = SimpleNamespace(
        recorder=SimpleNamespace(
            append=lambda run_id, event_type, node, payload: calls.append(
                (run_id, event_type, node, payload)
            )
        )
    )

    context_module.record_event(
        runtime,
        {"run_id": "run-1"},
        "plan.created",
        "plan",
        {"status": "ready"},
    )

    assert calls == [("run-1", "plan.created", "plan", {"status": "ready"})]


def test_policy_memory_and_routing_planning_modules_are_internal():
    policy_memory = importlib.import_module("netzoo_agent_core.graph.policy_memory")
    routing_planning = importlib.import_module(
        "netzoo_agent_core.graph.routing_planning"
    )
    assert policy_memory.__all__ == []
    assert routing_planning.__all__ == []
    assert not hasattr(graph, "classify_task")
    assert not hasattr(graph, "plan_task")


def test_legacy_plan_patch_reaches_routing_planning_child():
    routing_planning = importlib.import_module(
        "netzoo_agent_core.graph.routing_planning"
    )
    original = legacy_agent.build_workflow_plan

    def replacement(
        raw_decision,
        task,
        profile=None,
        retrieved_episodes=None,
        project_policy=None,
    ):
        raise AssertionError("patch propagation sentinel")

    try:
        legacy_agent.build_workflow_plan = replacement
        assert routing_planning.build_workflow_plan is replacement
    finally:
        legacy_agent.build_workflow_plan = original


def test_execution_and_transition_modules_are_internal():
    execution = importlib.import_module("netzoo_agent_core.graph.execution")
    transitions = importlib.import_module("netzoo_agent_core.graph.transitions")
    assert execution.__all__ == []
    assert transitions.__all__ == []
    assert not hasattr(graph, "execute_tool")
    assert not hasattr(graph, "route_evaluation")


def test_legacy_executor_patch_reaches_graph_execution_child():
    execution = importlib.import_module("netzoo_agent_core.graph.execution")
    original = legacy_agent.execute_selected_tool

    def replacement(decision):
        return "patch propagation sentinel"

    try:
        legacy_agent.execute_selected_tool = replacement
        assert execution.execute_selected_tool is replacement
    finally:
        legacy_agent.execute_selected_tool = original


def test_response_module_is_internal():
    response = importlib.import_module("netzoo_agent_core.graph.response")
    assert response.__all__ == []
    assert not hasattr(graph, "respond")


def test_legacy_response_helper_patch_reaches_response_child():
    response = importlib.import_module("netzoo_agent_core.graph.response")
    original = legacy_agent.build_response_messages

    def replacement(system_prompt, trusted_context, user_task, tool_result):
        return []

    try:
        legacy_agent.build_response_messages = replacement
        assert response.build_response_messages is replacement
    finally:
        legacy_agent.build_response_messages = original


class _FakeRecorder:
    def __init__(self):
        self.instrumented = []

    def instrument_node(self, name, function):
        self.instrumented.append(name)
        return function


class _FakeStateGraph:
    instance = None

    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = []
        self.edges = []
        self.conditionals = []
        _FakeStateGraph.instance = self

    def add_node(self, name, function):
        self.nodes.append(name)

    def add_edge(self, source, target):
        self.edges.append((source, target))

    def add_conditional_edges(self, source, router, mapping):
        self.conditionals.append((source, router.__name__, mapping))

    def compile(self):
        return self


def test_topology_is_exact_and_fully_instrumented(monkeypatch):
    topology = importlib.import_module("netzoo_agent_core.graph.topology")
    recorder = _FakeRecorder()
    runtime = SimpleNamespace(recorder=recorder)
    monkeypatch.setattr(topology, "START", "START")
    monkeypatch.setattr(topology, "END", "END")

    compiled = topology.compile_graph(runtime, graph_cls=_FakeStateGraph)

    expected_nodes = [
        "apply_project_policy",
        "retrieve_memory",
        "classify",
        "plan",
        "evaluate_plan",
        "execute_tool",
        "evaluate",
        "recover",
        "consolidate_memory",
        "respond",
    ]
    assert compiled.nodes == expected_nodes
    assert recorder.instrumented == expected_nodes
    assert compiled.edges == [
        ("START", "apply_project_policy"),
        ("apply_project_policy", "retrieve_memory"),
        ("retrieve_memory", "classify"),
        ("classify", "plan"),
        ("plan", "evaluate_plan"),
        ("execute_tool", "evaluate"),
        ("recover", "evaluate_plan"),
        ("consolidate_memory", "respond"),
        ("respond", "END"),
    ]
    assert compiled.conditionals == [
        (
            "evaluate_plan",
            "route_plan_evaluation",
            {
                "execute_tool": "execute_tool",
                "consolidate_memory": "consolidate_memory",
            },
        ),
        (
            "evaluate",
            "route_evaluation",
            {
                "execute_tool": "execute_tool",
                "recover": "recover",
                "consolidate_memory": "consolidate_memory",
            },
        ),
    ]


def test_factory_is_dependency_assembly_only():
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    source = inspect.getsource(factory)
    assert len(source.splitlines()) <= 150
    assert "_GraphContext(" in source
    assert "compile_graph(" in source
    assert "def classify_task" not in source
    assert "def respond" not in source
    assert "add_edge" not in source


def test_graph_children_remain_responsibility_sized():
    maximum_lines = {
        "context": 140,
        "execution": 230,
        "factory": 150,
        "policy_memory": 150,
        "prompts": 120,
        "response": 260,
        "routing_planning": 230,
        "topology": 130,
        "transitions": 70,
    }
    for module_name, maximum in maximum_lines.items():
        module = importlib.import_module(f"netzoo_agent_core.graph.{module_name}")
        assert len(inspect.getsource(module).splitlines()) <= maximum, module_name


def test_graph_internal_helpers_do_not_leak():
    for name in (
        "_GraphContext",
        "apply_project_policy",
        "classify_task",
        "execute_tool",
        "respond",
        "route_evaluation",
        "compile_graph",
    ):
        assert not hasattr(graph, name)
