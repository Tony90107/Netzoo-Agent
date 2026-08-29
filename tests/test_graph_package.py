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
from netzoo_agent_core.contracts.outcomes import SemanticReview  # noqa: E402


PUBLIC_EXPORTS = ["build_graph", "invoke_graph_turn"]
BUILD_GRAPH_SIGNATURE = (
    "(model_name: 'str', temperature: 'float', profile_id: 'str' = 'default', "
    "profile_store: 'UserProfileStore | None' = None, episode_store: "
    "'EpisodeStore | None' = None, project_policy: 'ProjectPolicySnapshot | None' "
    "= None, router_model_name: 'str | None' = None, semantic_model_name: "
    "'str | None' = None, router_max_tokens: 'int' "
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


def test_graph_binds_interpreter_and_reviewer_before_narrow_intent_router(monkeypatch):
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    bound_schemas = []

    class RoutingProvider:
        def with_structured_output(self, schema, **_kwargs):
            bound_schemas.append(schema)
            return SimpleNamespace()

    models = iter([RoutingProvider(), SimpleNamespace()])
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    monkeypatch.setattr(factory, "ensure_graph_dependencies", lambda: None)
    monkeypatch.setattr(factory, "StateGraph", object())
    monkeypatch.setattr(factory, "build_llm", lambda *_args, **_kwargs: next(models))
    monkeypatch.setattr(factory, "compile_graph", lambda context, **_kwargs: context)

    factory.build_graph("fake", 0.0, router_model_name="fake")

    assert bound_schemas == [
        legacy_agent.SemanticInterpretation,
        SemanticReview,
        legacy_agent.IntentDecision,
    ]


def test_graph_can_assign_semantics_to_a_stronger_model_than_intent(monkeypatch):
    factory = importlib.import_module("netzoo_agent_core.graph.factory")
    bindings = []

    class Provider:
        def __init__(self, role):
            self.role = role

        def with_structured_output(self, schema, **_kwargs):
            bindings.append((self.role, schema))
            return SimpleNamespace()

    providers = iter([Provider("intent"), Provider("semantic"), SimpleNamespace()])
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "cheap,strong")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    monkeypatch.setattr(factory, "ensure_graph_dependencies", lambda: None)
    monkeypatch.setattr(factory, "StateGraph", object())
    monkeypatch.setattr(factory, "build_llm", lambda *_args, **_kwargs: next(providers))
    monkeypatch.setattr(factory, "compile_graph", lambda context, **_kwargs: context)

    context = factory.build_graph(
        "fake",
        0.0,
        router_model_name="cheap",
        semantic_model_name="strong",
    )

    assert bindings == [
        ("semantic", legacy_agent.SemanticInterpretation),
        ("semantic", SemanticReview),
        ("intent", legacy_agent.IntentDecision),
    ]
    assert context.semantic_model_name == "strong"
    assert context.router_model_name == "cheap"


def test_response_prompt_preserves_guidance_authority_boundaries(monkeypatch):
    prompts = importlib.import_module("netzoo_agent_core.graph.prompts")
    monkeypatch.setattr(prompts, "EXECUTE_TOOLS", False)
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()

    result = prompts.build_graph_prompts(policy)

    assert "Never ask the user to choose a value already supplied" in result.response
    assert "hypothesis_actions are advisory candidates" in result.response
    assert "ask only the smallest unresolved scientific question" in result.response
    assert "Cross-check every claimed workflow output" in result.response
    assert "Never transfer the final workflow's granularity" in result.response
    assert "attribute each capability to the exact workflow" in result.response
    assert "Do not offer to proceed" in result.response
    assert "Do not mention whether" in result.response
    assert "preserve that order as a composition" in result.response
    assert "leave-one-out construction" in result.response
    assert "N_without_7" not in result.response
    assert "sample 7" not in result.response
    assert "source-target-weight bipartite edge list" in result.response
    assert "bootstrap or leave-one-hospital-out" in result.response
    assert "not completely confounded" in result.response
    assert "Never describe an output role" in result.response
    assert "input file" in result.response
    assert "registered final action" in result.response
    assert "must issue separate commands" in result.response
    assert "may be a LIONESS workflow" in result.response
    assert "A guidance_predecessor is a conceptual predecessor" in result.response
    assert "never claim that a PANDA/PUMA predecessor output is its sole input" in result.response
    assert "produces sample-specific networks for the" in result.response
    assert "If handoff_targets is empty, do not render predecessor output as the next required input" in result.response
    assert "select the requested sample afterward" in result.response
    assert "reproduce the validated equation" in result.response
    assert "define every symbol" in result.response
    assert "Do not hardcode a sample index" in result.response
    assert "Selected path:" in result.response
    assert "required_inputs with their role labels" in result.response
    assert "inferred associations, not causal or clinical conclusions" in result.response
    assert "without an explicit sample-specific request" not in result.response
    assert result.routing == legacy_agent.build_routing_prompt(policy)


def test_cobra_to_panda_boundary_response_reads_latest_message():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="Explain the workflow input boundary.",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain whether COBRA output can feed PANDA.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    result = response_module.respond(
        SimpleNamespace(),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content="請將 COBRA 的結果直接當成 expression input 跑 PANDA。"
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    assert "cannot be used directly as PANDA expression input" in result["messages"][0].content


def test_ambiguous_guidance_reaches_response_model():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="The Router returned competing granularities.",
        capability_match_status="ambiguous",
        hypothesis_actions=["run_lioness_puma"],
        clarification_question="Should the result be aggregate or sample-specific?",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Answer a workflow guidance question.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    captured = []
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()

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
    assert '"action": "run_bonobo"' not in response_input
    assert '"ordered_actions"' in response_input
    composition = response_input.split(
        "Authoritative ordered workflow compositions:", maxsplit=1
    )[1].split("Authoritative validated workflow specifications:", maxsplit=1)[0]
    assert composition.index('"run_puma"') < composition.index('"run_lioness_puma"')
    assert '"required_inputs": [' in response_input
    assert '"output_roles": [' in response_input
    assert '"conventions": [' in response_input


def test_guidance_ambiguity_does_not_force_a_cli_clarification_follow_up():
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="The Router returned competing granularities.",
        capability_match_status="ambiguous",
        hypothesis_actions=["run_puma", "run_lioness_puma"],
        clarification_question="Should the result be aggregate or sample-specific?",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Answer a workflow guidance question.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = legacy_agent.build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "request_mode": "guidance",
                "relationship": "alternatives",
                "candidates": ["run_puma", "run_lioness_puma"],
            },
        }
    )

    assert prompt.kind == "completed"
    assert "Enter a follow-up question" in prompt.question


def test_no_tool_response_context_follows_validated_actions_without_name_rules():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="Guidance requested.",
        capability_match_status="exact",
        matched_actions=["run_bonobo"],
        recommended_actions=["run_bonobo"],
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain the selected workflow.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    captured = []

    class GuidanceResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return legacy_agent.AIMessage(content="The selected workflow is available.")

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

    response_module.respond(
        context,
        {
            "messages": [
                legacy_agent.HumanMessage(content="Explain the selected workflow")
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    response_input = "\n".join(str(message.content) for message in captured)
    assert '"action": "run_bonobo"' in response_input
    assert '"action": "run_puma"' not in response_input
    assert '"action": "run_lioness_puma"' not in response_input


def test_pipeline_guidance_context_carries_qc_handoff_and_sample_specific_rules():
    response_context = importlib.import_module(
        "netzoo_agent_core.graph.response_context"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=False,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="pipeline guidance",
        capability_match_status="unsupported",
    )

    context = response_context.validated_workflow_context(
        decision,
        policy,
        include_all=True,
    )
    by_action = {item["action"]: item for item in context["workflows"]}

    assert any(
        "confounded" in item
        for item in by_action["run_panda"]["conventions"]
    )
    assert any(
        "N_without_7" not in item and "N_without_k" in item
        for item in by_action["run_lioness_panda"]["conventions"]
    )
    assert any(
        "source-target-weight" in item
        for item in by_action["run_condor"]["conventions"]
    )
    handoffs = {
        (item["from_action"], item["to_action"]): item
        for item in context["handoffs"]
    }
    assert ("run_cobra", "run_panda") in handoffs
    assert ("run_cobra", "run_puma") in handoffs
    assert ("run_panda", "run_condor") in handoffs
    assert handoffs[("run_cobra", "run_panda")]["from_output"] == "coexpression_network"
    assert "adjusted" in handoffs[("run_cobra", "run_panda")]["handoff_contract"]
    assert "coexpression_file" in handoffs[("run_cobra", "run_puma")]["handoff_contract"]
    assert "regulatory_network" in handoffs[("run_panda", "run_condor")]["to_inputs"]


def test_guidance_response_removes_model_owned_status_and_cta_before_footer():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="Guidance requested.",
        hypothesis_actions=["run_lioness_puma"],
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain sample-specific miRNA network tools.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    class GuidanceResponse:
        def invoke(self, messages):
            return legacy_agent.AIMessage(
                content=(
                    "Use PUMA followed by LIONESS-PUMA.\n\n"
                    "No tools were executed, and no files were inspected. "
                    "If you need to start, provide the required files."
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
    result = response_module.respond(
        context,
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content="Which tools produce sample-specific miRNA networks?"
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    assert result["messages"][0].content == (
        "Use PUMA followed by LIONESS-PUMA.\n\n"
        "No files were inspected and no analysis ran."
    )


def test_unsupported_guidance_receives_full_validated_catalog_for_pipeline_mapping():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=False,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="The final requested artifact is not a direct workflow output.",
        capability_match_status="unsupported",
        alternative_actions=["run_condor"],
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain an ordered scientific pipeline.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    captured = []

    class GuidanceResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return legacy_agent.AIMessage(
                content="The requested pipeline needs conceptual workflow mapping."
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
    result = response_module.respond(
        context,
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content=(
                        "First build a regulatory network, then estimate the "
                        "network for patient 7, and finally inspect modules."
                    )
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    response_input = "\n".join(str(message.content) for message in captured)
    assert '"action": "run_panda"' in response_input
    assert '"action": "run_lioness_panda"' in response_input
    assert '"action": "run_condor"' in response_input
    assert "N_k = n * N_all - (n - 1) * N_without_k" in response_input
    assert '"patient 7"' in response_input
    assert result["messages"][0].content.endswith(
        "No files were inspected and no analysis ran."
    )


def test_unsupported_non_pipeline_guidance_does_not_expand_full_catalog():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=False,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="The requested result is not currently matched.",
        capability_match_status="unsupported",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain the capability boundary.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    captured = []

    class GuidanceResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return legacy_agent.AIMessage(content="Please clarify the requested result.")

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
    response_module.respond(
        context,
        {
            "messages": [
                legacy_agent.HumanMessage(content="Can NetZoo produce this result?")
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    response_input = "\n".join(str(message.content) for message in captured)
    assert '"action": "run_puma"' not in response_input
    assert '"action": "run_bonobo"' not in response_input


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
