from __future__ import annotations

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


def test_response_prompt_preserves_guidance_authority_boundaries(monkeypatch):
    prompts = importlib.import_module("netzoo_agent_core.graph.prompts")
    monkeypatch.setattr(prompts, "EXECUTE_TOOLS", False)
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()

    result = prompts.build_graph_prompts(policy)

    assert "Never ask the user to choose a value already supplied" in result.response
    assert "hypothesis_actions are advisory candidates" in result.response
    assert "ask only the smallest unresolved scientific question" in result.response
    assert "Cross-check every claimed workflow output" in result.response
    assert "Do not offer to proceed" in result.response
    assert "Never describe an output role" in result.response
    assert "input file" in result.response
    assert result.routing == legacy_agent.build_routing_prompt(policy)


def test_ambiguous_guidance_reaches_response_model():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="The Router returned competing granularities.",
        capability_match_status="ambiguous",
        hypothesis_actions=["run_lioness_puma"],
        clarification_question=None,
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Answer a workflow guidance question.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    captured = []

    class GuidanceResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return legacy_agent.AIMessage(
                content=(
                    "Use PUMA followed by LIONESS-PUMA for one network per sample."
                )
            )

    context = SimpleNamespace(
        project_policy=policy,
        response_llm=GuidanceResponse(),
        response_prompt="Use only validated workflow facts.",
        response_model_name="fake",
        response_max_tokens=800,
        task_token_budget=20_000,
        price_catalog=legacy_agent.PriceCatalog.from_environment(),
        recorder=legacy_agent.NullTraceRecorder(),
    )
    request = (
        "if i want to get sample specific mi-RNA network data,what tools do i need?"
    )

    result = response_module.respond(
        context,
        {
            "messages": [legacy_agent.HumanMessage(content=request)],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    assert captured
    assert "PUMA followed by LIONESS-PUMA" in result["messages"][0].content
    assert result["messages"][0].content.endswith(
        "No files were inspected and no analysis ran."
    )
    response_input = "\n".join(str(message.content) for message in captured)
    assert request in response_input
    assert '"action": "run_puma"' in response_input
    assert '"action": "run_lioness_puma"' in response_input
    assert '"ordered_actions"' in response_input
    composition = response_input.split(
        "Authoritative ordered workflow compositions:", maxsplit=1
    )[1].split("Authoritative validated workflow specifications:", maxsplit=1)[0]
    assert composition.index('"run_puma"') < composition.index('"run_lioness_puma"')
    assert '"required_inputs": [' in response_input
    assert '"output_roles": [' in response_input


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
        "response_context": 120,
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
