from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.graph as graph  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticDiscriminator, SemanticPatch, SemanticReview,
)


PUBLIC_EXPORTS = ["build_graph", "invoke_graph_turn"]
BUILD_GRAPH_SIGNATURE = '(model_name: \'str\', temperature: \'float\', profile_id: \'str\' = \'default\', profile_store: \'UserProfileStore | None\' = None, episode_store: \'EpisodeStore | None\' = None, project_policy: \'ProjectPolicySnapshot | None\' = None, router_model_name: \'str | None\' = None, semantic_model_name: \'str | None\' = None, router_max_tokens: \'int\' = 1200, response_max_tokens: \'int\' = 800, task_token_budget: \'int\' = 30000, timeout_seconds: \'float\' = 30.0, trace_recorder: \'TraceRecorder | None\' = None, semantic_contract: "Literal[\'claims\', \'legacy\']" = \'legacy\', review_policy: "Literal[\'when_needed\', \'always\']" = \'when_needed\')'


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


def test_semantic_failure_recovers_explicit_workflow_guidance():
    router_invocation = importlib.import_module(
        "netzoo_agent_core.graph.router_invocation"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    task = (
        "Please write a script that performs high-order correlation batch correction "
        "and then uses the corrected co-expression result with Motif and PPI matrices "
        "in PANDA."
    )
    context = SimpleNamespace(
        project_policy=policy,
        recorder=legacy_agent.NullTraceRecorder(),
    )

    result = router_invocation._semantic_failure(
        context,
        {},
        task,
        legacy_agent.LLMUsage(budget_tokens=20_000),
        [],
        error=ValueError("semantic schema validation failed"),
        reason_code="semantic_fallback",
    )

    assert result.decision.action == "no_tool"
    assert result.decision.matched_actions == []
    assert result.decision.recommended_actions == []
    assert result.decision.requested_outcome is None  # Candidate capabilities are not the user's goal.


def test_semantic_failure_recovers_explicit_web_search_tool():
    router_invocation = importlib.import_module(
        "netzoo_agent_core.graph.router_invocation"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    task = "請使用 WEB-SEARCH 搜尋官方 NCBI Gene 資料：TP53。"
    context = SimpleNamespace(
        project_policy=policy,
        recorder=legacy_agent.NullTraceRecorder(),
    )

    result = router_invocation._semantic_failure(
        context,
        {},
        task,
        legacy_agent.LLMUsage(budget_tokens=20_000),
        [],
        error=ValueError("semantic schema validation failed"),
        reason_code="semantic_fallback",
    )

    assert result.decision.action == "web_search"
    assert result.decision.should_execute is True
    assert result.decision.web_query == task
    assert result.decision.matched_actions == ["web_search"]


def test_semantic_failure_recovers_chinese_panda_run_with_listed_inputs():
    router_invocation = importlib.import_module(
        "netzoo_agent_core.graph.router_invocation"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    dataset = "manual_tests/gene_existence/dataset_a"
    task = (
        f"用 {dataset}/expression.tsv {dataset}/motif.tsv {dataset}/ppi.tsv "
        "這三個檔案跑 PANDA，物種是 human，"
        "輸出到 outputs/gene_existence_a.tsv"
    )
    context = SimpleNamespace(
        project_policy=policy,
        recorder=legacy_agent.NullTraceRecorder(),
    )

    result = router_invocation._semantic_failure(
        context,
        {},
        task,
        legacy_agent.LLMUsage(budget_tokens=20_000),
        [],
        error=ValueError("semantic schema validation failed"),
        reason_code="semantic_fallback",
    )

    decision = result.decision
    assert decision.action == "run_panda"
    assert decision.should_execute is True
    assert decision.expression_file == f"{dataset}/expression.tsv"
    assert decision.motif_file == f"{dataset}/motif.tsv"
    assert decision.ppi_file == f"{dataset}/ppi.tsv"
    assert decision.taxon == "human"
    assert decision.output_file == "outputs/gene_existence_a.tsv"
    assert decision.output_dir is None
    assert decision.missing_inputs == []


def test_failed_web_search_is_not_rendered_as_a_negative_match():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="web_search",
        in_scope=True,
        should_execute=True,
        intent_type="answer_question",
        confidence=1.0,
        reason="direct retrieval",
        matched_actions=["web_search"],
        web_query="official NCBI Gene TP53 Homo sapiens",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="WEB-SEARCH",
        objective="retrieve official gene records",
        decision=decision.model_dump(),
        status="ready",
    )

    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [
                legacy_agent.HumanMessage(content="Search official NCBI Gene TP53.")
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [
                legacy_agent.ToolExecutionResult(
                    action="web_search",
                    status="failed",
                    summary="The tool or its validation failed.",
                    errors=["ImportError: MCP adapter is unavailable"],
                ).model_dump()
            ],
            "evaluation": {
                "status": "failed",
                "reason": "retrieval failed",
            },
        },
    )

    content = result["messages"][0].content
    assert "lookup failed" in content
    assert "not evidence that the requested record was not found" in content
    assert "未找到" not in content


def test_successful_authority_search_preserves_exact_ncbi_match():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="web_search",
        in_scope=True,
        should_execute=True,
        intent_type="answer_question",
        confidence=1.0,
        reason="direct retrieval",
        matched_actions=["web_search"],
        web_query="site:ncbi.nlm.nih.gov/gene TP53 Homo sapiens",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="WEB-SEARCH",
        objective="retrieve official gene records",
        decision=decision.model_dump(),
        status="ready",
    )
    raw = (
        "Websearch MCP result (external, untrusted reference content):\n"
        "- server: https://mcp.tavily.com/mcp\n\n"
        '{"results":[{"url":"https://www.ncbi.nlm.nih.gov/gene/7157",'
        '"title":"TP53 tumor protein p53 [Homo sapiens] - Gene",'
        '"content":"Official Symbol TP53 provided by HGNC Organism Homo sapiens GeneID 7157"}]}'
    )
    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [legacy_agent.HumanMessage(content="Search NCBI Gene TP53.")],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [
                legacy_agent.ToolExecutionResult(
                    action="web_search",
                    status="success",
                    summary="The tool completed and passed structured result checks.",
                    raw_output=raw,
                ).model_dump()
            ],
            "evaluation": {"status": "completed", "reason": "done"},
        },
    )

    content = result["messages"][0].content
    assert "exact trusted match" in content
    assert "canonical_id=7157" in content
    assert "https://www.ncbi.nlm.nih.gov/gene/7157" in content
    assert "Websearch 未找到" not in content


def test_large_websearch_result_stays_parseable_for_authority_report():
    retrieval = importlib.import_module("netzoo_agent_core.routing.retrieval")
    results_module = importlib.import_module("netzoo_agent_core.routing.results")
    rendering = importlib.import_module("netzoo_agent_core.evaluation.rendering")
    task = "請使用 WEB-SEARCH 搜尋官方 NCBI Gene 資料：TP53，物種為 Homo sapiens。"
    decision = legacy_agent.TaskDecision(
        action="web_search",
        in_scope=True,
        should_execute=True,
        intent_type="answer_question",
        confidence=1.0,
        reason="direct retrieval",
        matched_actions=["web_search"],
        web_query=task,
    )
    payload = {
        "query": "TP53",
        "results": [
            {
                "url": f"https://www.ncbi.nlm.nih.gov/gene/{7157 + index}",
                "title": "TP53 tumor protein p53 [Homo sapiens] - Gene",
                "content": "Official Symbol TP53 provided by HGNC " + "x" * 20_000,
            }
            for index in range(5)
        ],
    }
    raw = (
        "Websearch MCP result (external, untrusted reference content):\n"
        "- server: https://mcp.tavily.com/mcp\n"
        "- query: site:ncbi.nlm.nih.gov/gene TP53 Homo sapiens\n\n"
        + retrieval._bound_websearch_text(json.dumps(payload))
    )
    result = results_module.structure_tool_result("web_search", decision, raw)
    assert result.status == "success"
    assert len(result.raw_output) <= legacy_agent.TOOL_RAW_MAX_CHARS

    report = rendering.render_authority_search_response(task, decision, [result])
    assert report is not None
    assert "canonical_id=7157" in report
    assert "Websearch 未找到" not in report


def test_authority_report_requires_web_search_action():
    rendering = importlib.import_module("netzoo_agent_core.evaluation.rendering")
    decision = legacy_agent.TaskDecision(
        action="inspect_inputs",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=1.0,
        reason="input preflight",
        matched_actions=["inspect_inputs"],
    )
    result = legacy_agent.ToolExecutionResult(
        action="inspect_inputs",
        status="success",
        summary="Input validation passed.",
        raw_output="structured input inspection result",
    )

    report = rendering.render_authority_search_response(
        "請使用 NCBI/Ensembl 檢查 TP53。", decision, [result]
    )

    assert report is None


def test_input_preflight_does_not_call_authority_renderer(monkeypatch):
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="inspect_inputs",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=1.0,
        reason="input preflight",
        matched_actions=["inspect_inputs"],
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="INPUTS",
        objective="validate PANDA inputs",
        decision=decision.model_dump(),
        status="ready",
    )

    def fail_if_called(*_args, **_kwargs):
        pytest.fail("authority renderer must only run for web_search")

    monkeypatch.setattr(response_module, "render_authority_search_response", fail_if_called)
    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content="檢查 PANDA labels，並以 NCBI/Ensembl 作為 authority。"
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [
                legacy_agent.ToolExecutionResult(
                    action="inspect_inputs",
                    status="success",
                    summary="Input validation passed.",
                    raw_output="Input formats and identifier compatibility passed.",
                ).model_dump()
            ],
        },
    )

    content = result["messages"][0].content
    assert "Input formats and identifier compatibility passed" in content
    assert "Websearch" not in content


def test_direct_websearch_overrides_answer_intent_without_running_workflow(monkeypatch):
    router_invocation = importlib.import_module(
        "netzoo_agent_core.graph.router_invocation"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    task = (
        "請使用 WEB-SEARCH 搜尋官方 NCBI Gene 與 Ensembl：ENSG00000999999，"
        "物種為 Homo sapiens。只回報官方來源是否有精確匹配、查詢到的 URL 與證據摘要；"
        "若沒有精確匹配，請明確寫 Websearch 未找到，不要執行任何 workflow。"
    )
    interpretation = legacy_agent.SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="retrieve authoritative gene reference material",
        outcome_hypotheses=[
            legacy_agent.OutcomeHypothesis(
                outcome=legacy_agent.RequestedOutcome(
                    operation="unknown", artifact_type="unknown", granularity="unknown",
                ),
                confidence=0.5,
            )
        ],
    )
    monkeypatch.setattr(
        router_invocation,
        "_invoke_semantic_interpreter",
        lambda _context, _state, _task, usage: (
            interpretation, usage, [], None, frozenset()
        ),
    )
    monkeypatch.setattr(
        router_invocation,
        "_invoke_semantic_discriminator",
        lambda _context, _state, _task, current_interpretation, match, usage, warnings: (
            current_interpretation, match, usage, warnings
        ),
    )
    monkeypatch.setattr(
        router_invocation,
        "_invoke_intent_router",
        lambda _context, _state, _task, _interpretation, _match, usage, warnings: (
            legacy_agent.IntentDecision(mode="answer", confidence=0.95, reason="guidance"),
            usage,
            warnings,
            False,
        ),
    )
    context = SimpleNamespace(
        project_policy=policy,
        recorder=legacy_agent.NullTraceRecorder(),
        task_token_budget=20_000,
    )

    result = router_invocation.invoke_router(context, {"run_id": "direct-search"}, task)

    assert result.decision.action == "web_search"
    assert result.decision.should_execute is True
    assert result.decision.web_query == task
    assert result.decision.intent_type == "answer_question"


def test_semantic_failure_recovers_sambar_from_declared_scientific_signals():
    router_invocation = importlib.import_module(
        "netzoo_agent_core.graph.router_invocation"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    task = (
        "我想要對癌症病患的 DNA 體細胞突變資料做亞型分析，先校正基因長度與"
        "不同病患的腫瘤突變負荷，再把基因突變聚合成生物途徑分數，計算病患"
        "之間的距離並分群。"
    )
    context = SimpleNamespace(
        project_policy=policy,
        recorder=legacy_agent.NullTraceRecorder(),
    )

    result = router_invocation._semantic_failure(
        context,
        {},
        task,
        legacy_agent.LLMUsage(budget_tokens=20_000),
        [],
        error=ValueError("semantic evidence validation failed"),
        reason_code="semantic_fallback",
    )

    assert result.decision.action == "no_tool"
    assert result.decision.matched_actions == []
    assert result.decision.recommended_actions == []
    assert result.decision.requested_outcome is None
    assert result.decision.guidance_input_artifacts == []
    assert "failed validation" in result.decision.reason
    assert "router was unavailable" not in result.decision.reason


def test_semantic_failure_script_request_keeps_complete_cobra_panda_contract():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.35,
        reason="semantic fallback",
        matched_actions=["run_panda"],
        recommended_actions=["run_cobra", "run_panda"],
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Provide COBRA to PANDA script guidance.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content=(
                        "Write a script for high-order correlation batch correction "
                        "then PANDA using expression, motif, and PPI matrices."
                    )
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    content = result["messages"][0].content
    assert "**COBRA → PANDA**" in content
    assert "run-cobra" in content
    assert "run-panda-precomputed" in content
    assert "-e \"$expression_file\"" in content
    assert "-c \"$coexpression_file\"" in content
    assert "not a corrected expression matrix" in content


def test_response_reports_no_exact_workflow_for_glasso_bayesian_optimization():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    task = (
        "I have an expression matrix and priors. Use Graphical Lasso to estimate "
        "the inverse covariance precision matrix and Bayesian optimization to tune it."
    )
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="generic regulatory network interpretation",
        matched_actions=["run_panda"],
        recommended_actions=["run_panda"],
        capability_match_status="exact",
    )

    result = response_module.respond(
        SimpleNamespace(),
        {
            "messages": [legacy_agent.HumanMessage(content=task)],
            "decision": decision.model_dump(),
        },
    )

    content = result["messages"][0].content
    assert content.startswith("No registered netZooPy workflow implements")
    assert "DRAGON" in content
    assert "BONOBO" in content
    assert "not Graphical Lasso" in content
    assert "not Bayesian Optimization" in content
    assert "likely looking for" not in content
    assert "Selected path" not in content


def test_recovered_sambar_guidance_is_rendered_without_response_model_guessing():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.35,
        reason=(
            "Semantic interpretation failed validation; recovered a registered "
            "guidance candidate for SAMBAR from multiple declared scientific signals."
        ),
        matched_actions=["run_sambar"],
        recommended_actions=["run_sambar"],
        capability_match_status="fallback",
        match_basis="semantic_validation_recovery",
        requested_outcome=legacy_agent.RequestedOutcome(
            operation="analyze", input_artifacts=["mutation_matrix"],
            artifact_type="sample_cluster_assignment", entity_types=["sample"], granularity="aggregate",
        ),
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain the recovered SAMBAR match.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    class UnexpectedResponseModel:
        def invoke(self, _messages):
            raise AssertionError("recovered registry guidance must be deterministic")

    result = response_module.respond(
        SimpleNamespace(
            project_policy=policy,
            response_llm=UnexpectedResponseModel(),
        ),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content=(
                        "是否能把 WES 體細胞突變矩陣丟進 PANDA 與 LIONESS-PANDA？"
                        "矩陣非常稀疏，我想做基因長度與突變負荷校正、途徑分數、"
                        "病患距離與亞型分群。"
                    )
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    content = result["messages"][0].content
    assert "**SAMBAR**" in content
    assert "gene length normalization" in content.casefold()
    assert "patient mutation burden normalization" in content.casefold()
    assert "sample_distance_matrix" in content
    assert "sample_cluster_assignment" in content
    assert content.startswith("Do not use")
    assert "Do not use **PANDA**" in content
    assert "Do not use **LIONESS-PANDA**" in content
    assert "Fallback recommendation" in content
    assert "No files were inspected and no analysis ran." in content


def test_unresolved_router_fallback_does_not_let_response_model_guess_workflows():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="unknown",
        confidence=0.0,
        reason=(
            "The LLM router was unavailable, so no workflow was selected. "
            "(ValidationError)"
        ),
        clarification_question=(
            "Please restate the desired NetZoo result after the router is available."
        ),
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Clarify the requested result.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    class UnexpectedResponseModel:
        def invoke(self, _messages):
            raise AssertionError("response model must not guess after router failure")

    result = response_module.respond(
        SimpleNamespace(
            project_policy=policy,
            response_llm=UnexpectedResponseModel(),
        ),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content=(
                        "我有一批腫瘤病人的資料，想完成 somatic mutation pathway "
                        "分群與 covariate 校正後的 co-expression network。"
                    )
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    content = result["messages"][0].content
    assert "ValidationError" in content
    assert "Please restate" in content
    assert "No files were inspected and no analysis ran." in content
    assert "CONDOR" not in content
    assert "LIONESS-PANDA" not in content


def test_sample_specific_panda_advice_recommends_lioness_not_its_predecessor():
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="The registry selected the sample-specific TF workflow.",
        matched_actions=["run_lioness_panda"],
        recommended_actions=["run_panda", "run_lioness_panda"],
        requested_outcome=legacy_agent.RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["tf", "gene"],
            regulator_types=["tf"],
            target_types=["gene"],
            granularity="sample_specific",
        ),
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain the sample-specific TF workflow.",
        decision=decision.model_dump(),
        status="respond_only",
    )

    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [
                legacy_agent.HumanMessage(
                    content=(
                        "My lab has tumour RNA profiles from about 90 patients plus "
                        "binding-motif and protein-interaction reference files. I want "
                        "to know how the wiring between transcription factors and "
                        "their target genes differs from one patient to the next, so "
                        "each patient ends up with their own picture. What should I "
                        "use? Just advise."
                    )
                )
            ],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )

    content = result["messages"][0].content
    assert "For the sample-specific output you described, use **LIONESS-PANDA**." in content
    assert "I matched your goal to an aggregate and a sample-specific workflow." not in content
    assert "1. **PANDA**" not in content
    assert "**LIONESS-PANDA**" in content
    assert "lioness_output" in content
    assert "No files were inspected and no analysis ran." in content


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

    # 2026-09-06: the review pass gained a second binding. It is asked for a
    # SemanticPatch when the first pass parsed and can be repaired field by
    # field, and for a whole SemanticReview when there is nothing to patch onto.
    assert bound_schemas == [
        legacy_agent.SemanticInterpretation,
        SemanticReview,
        SemanticPatch,
        SemanticDiscriminator,
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
        # 2026-09-06: the patch binding must stay on the semantic model, not the
        # cheaper intent model. That is the point of this assertion.
        ("semantic", SemanticPatch),
        ("semantic", SemanticDiscriminator),
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


def test_ambiguous_guidance_uses_deterministic_clarification():
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

    assert not captured
    assert "Should the result be aggregate or sample-specific?" in result["messages"][0].content
    assert result["messages"][0].content.endswith(
        "No files were inspected and no analysis ran."
    )


@pytest.mark.parametrize(
    "task",
    [
        "我有兩組病人（癌症 vs. 正常）的 RNA-seq count 資料，想知道這兩組之間有沒有什麼"
        "關鍵的轉錄因子調控差異，但我以前沒用過網路分析，我該怎麼開始？",
        "I have RNA-seq count data from two patient groups (cancer vs. normal) and want "
        "to find differences in key transcription-factor regulation. I am new to network "
        "analysis. How should I get started?",
    ],
)
def test_beginner_group_network_guidance_does_not_ask_for_algorithm_assumptions(task):
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    requested = legacy_agent.RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
    )
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="The user asks how to begin comparing two groups.",
        requested_outcome=requested,
        capability_match_status="ambiguous",
        hypothesis_actions=["run_panda", "run_otter", "run_giraffe"],
        clarification_question=(
            "Which modeling assumption best matches your experiment: "
            "biologically informed matrix factorization; iterative message passing; "
            "continuous relaxed graph matching?"
        ),
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective="Give beginner guidance for a two-group regulatory comparison.",
        decision=decision.model_dump(),
        status="respond_only",
    )
    result = response_module.respond(
        SimpleNamespace(project_policy=policy),
        {
            "messages": [legacy_agent.HumanMessage(content=task)],
            "decision": decision.model_dump(),
            "plan": plan.model_dump(),
            "semantic_goal": {"request_mode": "guidance"},
            "tool_results": [],
        },
    )

    answer = result["messages"][0].content
    assert "cancer" in answer.casefold() and "normal" in answer.casefold()
    assert "PANDA" in answer and "LIONESS-PANDA" in answer
    assert "each group" in answer.casefold() and "paired" in answer.casefold()
    assert "Which modeling assumption" not in answer
    assert "No files were inspected and no analysis ran." in answer


def test_guidance_ambiguity_preserves_the_cli_clarification_follow_up():
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

    assert prompt.kind == "clarify_outcome"
    assert "aggregate or sample-specific" in prompt.question
    assert prompt.allow_workflow_continuation is False


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

    result = response_module.respond(
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

    assert captured == []  # Selected guidance is now code-owned, not free prose.
    answer = result["messages"][0].content
    assert "BONOBO" in answer
    assert "PUMA" not in answer
    assert "coexpression_network" in answer


def test_response_context_derives_handoff_producers_from_registry_capabilities():
    response_context = importlib.import_module(
        "netzoo_agent_core.graph.response_context"
    )
    policy = legacy_agent.ProjectPolicyLoader(legacy_agent.PROJECT_ROOT).load()
    outcome = legacy_agent.RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
        selection_tags=[
            "hospital_effect_assessment",
            "sequencing_batch_effect_assessment",
        ],
    )
    decision = legacy_agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="The user requests batch-effect guidance before network inference.",
        capability_match_status="exact",
        matched_actions=["run_panda"],
        requested_outcome=outcome,
    )

    context = response_context.validated_workflow_context(
        decision,
        policy,
        include_all=False,
        task="Remove hospital and sequencing batch effects before PANDA.",
    )

    actions = {item["action"] for item in context["workflows"]}
    assert {"run_panda", "run_cobra"}.issubset(actions)
    assert context["compositions"][0]["ordered_actions"] == [
        "run_cobra",
        "run_panda",
    ]

    outcome.selection_tags = []
    context_without_signal = response_context.validated_workflow_context(
        decision,
        policy,
        include_all=False,
    )
    assert {"run_panda", "run_cobra"}.issubset(
        {item["action"] for item in context_without_signal["workflows"]}
    )
    assert context_without_signal["compositions"][0]["ordered_actions"] == [
        "run_panda",
    ]


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
    cobra = {item["action"]: item for item in context["workflows"]}["run_cobra"]
    assert cobra["output_files"] == [
        "manifest.json",
        "components.npz",
        "summary.tsv",
        "adjusted_coexpression.tsv",
        "adjusted_coexpression.npz",
    ]
    cobra_to_panda = handoffs[("run_cobra", "run_panda")]
    assert cobra_to_panda["handoff_input_fields"] == ["coexpression_file"]
    assert "adjusted_coexpression.tsv" in cobra_to_panda["producer_output_files"]


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
        task_token_budget=legacy_agent.DEFAULT_TASK_TOKEN_BUDGET,
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
    assert '"action": "run_puma"' in response_input
    assert '"action": "run_bonobo"' in response_input


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
        "classify",
        "retrieve_memory",
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
        ("apply_project_policy", "classify"),
        ("classify", "retrieve_memory"),
        ("retrieve_memory", "plan"),
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
        "prompts": 125,
        # The response node also owns the fail-closed router fallback renderer.
        "response": 340,
        "response_context": 140,
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
