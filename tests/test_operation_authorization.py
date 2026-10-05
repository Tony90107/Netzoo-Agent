"""Tool suitability and operation authority are separate (diagnostics F1/F2/F7).

Which registered tool fits a request is the registry's question. Whether the
user asked for an operation now, and which ones they forbade, is read from the
request's own words. Deterministic promotions read only authority-bearing text,
and a forbidding clause vetoes execution from any source, all the way to the
plan evaluator and the executor.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path[:0] = [str(Path(__file__).parents[1] / "scripts"), str(Path(__file__).parent)]

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage, HumanMessage, IntentDecision, LLMUsage, TaskDecision,
)
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.evaluation import evaluate_workflow_plan  # noqa: E402
from netzoo_agent_core.framework_compat import StateGraph  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.context import _GraphContext  # noqa: E402
from netzoo_agent_core.graph.routing_planning import classify_task  # noqa: E402
from netzoo_agent_core.graph.topology import compile_graph  # noqa: E402
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision  # noqa: E402
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore  # noqa: E402
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.routing.authorization import (  # noqa: E402
    enforce_operation_authorization, forbidding_reason, read_operation_authorization,
)
from netzoo_agent_core.routing.capability import (  # noqa: E402
    apply_input_preflight_intent, has_direct_execution_intent, has_direct_retrieval_request,
    has_explicit_execution_request, reconcile_request_mode,
)
from netzoo_agent_core.routing.request_scope import operation_scope  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.tracing import NullTraceRecorder  # noqa: E402
from test_routing_evaluation import TASK, hypothesis  # noqa: E402


FORBIDDEN_SEARCH = (
    "Do not use WEB-SEARCH to search for PANDA papers. " + TASK,
    "不要用 WEB-SEARCH 搜尋 PANDA 文獻。 " + TASK,
)
POSITIVE_SEARCH = "請使用 WEB-SEARCH 搜尋官方 NCBI Gene 資料：TP53。不要執行 PANDA。"
EXPLAIN_ONLY = (
    "Only explain input preflight; do not inspect anything. expression_file=demo.tsv",
    "不要執行分析，expression_file=demo.tsv，只要解釋 PANDA。",
)
INSPECT_NOT_ANALYZE = (
    "Check my input files expression_file=e.tsv motif_file=m.tsv ppi_file=p.tsv for PANDA, "
    "but do not run the analysis.",
    "幫我檢查輸入檔案 expression_file=e.tsv motif_file=m.tsv ppi_file=p.tsv，但不要執行分析。",
)


def _kinds(task: str) -> list[tuple[str, tuple[str, ...]]]:
    return [(ban.kind, ban.tools) for ban in operation_scope(task).bans]


# --- reading the request's own words ---------------------------------------

@pytest.mark.parametrize(("task", "expected"), [
    (FORBIDDEN_SEARCH[0], [("retrieve", ())]),
    (FORBIDDEN_SEARCH[1], [("retrieve", ())]),
    ("Only explain input preflight; do not inspect anything.", [("inspect", ())]),
    ("不要執行分析，只要解釋 PANDA。", [("run", ())]),
    ("請執行 PANDA input preflight。只回報驗證結果，不要執行 PANDA。", [("run", ("panda",))]),
    ("Please don't run LIONESS; run PANDA on the pooled cohort.", [("run", ("lioness",))]),
    ("Do not execute anything; explain only.", [("any", ())]),
    ("不要直接跑 PANDA，先告訴我需要什麼。", [("run", ("panda",))]),
    # Not bans: the negation is about something else.
    ("Don't forget to run PANDA on all samples.", []),
    ("Don't use the test data, use my files and run PANDA.", []),
    ("Run PUMA instead of PANDA.", []),
    ("Can I run PANDA without a motif prior?", []),
    # Quoted and historical text is not the user's instruction.
    ('The tutorial says "do not run PANDA without priors". Please run PANDA.', []),
    ("Last month I did not run the inspection, now run PUMA.", []),
])
def test_bans_name_the_operation_their_own_negation_reaches(task, expected):
    assert _kinds(task) == expected


@pytest.mark.parametrize("task", [
    "My advisor told me to run PANDA on everything, but I only want to understand it.",
    "老師說「請執行 PANDA」，這是什麼意思？",
    "我上個月已經跑完 PANDA 了，這次只想了解結果怎麼讀。",
])
def test_quoted_reported_or_past_commands_grant_no_authority(task):
    assert not has_explicit_execution_request(task)
    assert not has_direct_execution_intent(task)
    assert reconcile_request_mode(task, "guidance") == "guidance"


@pytest.mark.parametrize("task", ["請執行PANDA", "請執行 PANDA"])
def test_a_space_after_a_chinese_verb_does_not_change_authority(task):
    """F7: both helpers and the reconciliation agree with or without a space."""
    assert has_explicit_execution_request(task)
    assert has_direct_execution_intent(task)
    assert reconcile_request_mode(task, "answer") == "execute"


def test_cjk_boundary_fix_does_not_read_nouns_as_commands():
    assert not has_explicit_execution_request("測試資料在哪裡？")


# --- F1: a forbidden search is never selected, at any stage ----------------

def _route(task: str, *, request_mode="guidance", intent_mode="answer"):
    """Script only the model boundaries; routing, gates and planning are real."""
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    context = SimpleNamespace(project_policy=policy, recorder=NullTraceRecorder(),
                              task_token_budget=30000, selection_condition_llm=None)
    interpretation = SemanticInterpretation.model_validate({
        "request_mode": request_mode, "semantic_goal": "Cohort grouping",
        "outcome_hypotheses": [hypothesis()],
    })
    usage = LLMUsage(budget_tokens=30000)
    with patch.object(router_invocation, "_invoke_semantic_interpreter",
                      return_value=(interpretation, usage, [], None, frozenset())), \
         patch.object(router_invocation, "_invoke_semantic_discriminator",
                      side_effect=lambda c, s, t, i, m, u, w: (i, m, u, w)), \
         patch.object(router_invocation, "_invoke_intent_router",
                      return_value=(IntentDecision(mode=intent_mode, confidence=1, reason="scripted"),
                                    usage, [], False)):
        routed = classify_task(context, {"messages": [HumanMessage(content=task)]})
    decision = TaskDecision.model_validate(routed["decision"])
    plan = build_workflow_plan(decision, task, project_policy=policy)
    return decision, plan, evaluate_workflow_plan(plan, task, policy)


@pytest.mark.parametrize("task", FORBIDDEN_SEARCH)
def test_forbidden_search_is_not_selected_planned_or_approved(task):
    assert not has_direct_retrieval_request(task)
    assert reconcile_request_mode(task, "guidance") == "guidance"

    decision, plan, review = _route(task)

    assert decision.action != "web_search"
    assert decision.should_execute is False
    assert plan.status != "ready"
    assert review.status != "approved"
    assert [ban.kind for ban in decision.operation_authorization.forbidden] == ["retrieve"]
    # Suitability is kept: the reply can still name the tool that fits.
    assert decision.matched_actions == ["run_sambar"]


def test_a_requested_search_with_an_unrelated_ban_still_runs():
    decision, plan, review = _route(POSITIVE_SEARCH)

    assert decision.action == "web_search"
    assert decision.should_execute is True
    assert plan.status == "ready"
    assert review.status == "approved"


def test_a_model_proposed_execution_of_a_forbidden_kind_is_refused():
    """The ban vetoes execution whoever proposed it, keeping the matched tool.

    The request names SAMBAR, so the older name check passes; without the gate
    the scripted execute reading would run it.
    """
    task = TASK + " I think it is SAMBAR; do not run it yet."
    decision, plan, review = _route(task, request_mode="execute", intent_mode="execute")

    assert decision.action == "no_tool"
    assert decision.should_execute is False
    assert decision.matched_actions == ["run_sambar"]
    assert decision.operation_authorization.blocked_action == "run_sambar"
    assert plan.status != "ready"
    assert review.status != "approved"


# --- F2: explain only / do not inspect / inspect but do not analyze --------

def _no_tool() -> TaskDecision:
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                        confidence=1, reason="Explanation only")


@pytest.mark.parametrize("task", EXPLAIN_ONLY)
def test_explain_only_requests_are_not_promoted_to_input_inspection(task):
    decision = apply_input_preflight_intent(hydrate_router_decision(_no_tool(), task), task)

    assert decision.action == "no_tool"
    assert decision.should_execute is False


@pytest.mark.parametrize("task", INSPECT_NOT_ANALYZE)
def test_inspect_but_do_not_analyze_inspects_and_refuses_analysis(task):
    decision = apply_input_preflight_intent(hydrate_router_decision(_no_tool(), task), task)
    authorization = read_operation_authorization(task)

    assert decision.action == "inspect_inputs"
    assert decision.should_execute is True
    assert enforce_operation_authorization(decision, task).should_execute is True
    assert forbidding_reason(authorization, "inspect_inputs") is None
    assert forbidding_reason(authorization, "run_panda") is not None


def test_explain_only_refuses_operations_it_does_not_also_ask_for():
    task = "Just explain what PANDA would produce from expression_file=e.tsv."
    decision = TaskDecision(action="run_panda", in_scope=True, should_execute=True,
                            confidence=1, reason="model misread", matched_actions=["run_panda"])

    gated = enforce_operation_authorization(decision, task)

    assert gated.action == "no_tool"
    assert gated.should_execute is False
    assert gated.matched_actions == ["run_panda"]
    assert gated.operation_authorization.explain_only == "Just explain"


# --- the plan evaluator re-reads the request independently -----------------

def test_plan_evaluator_rejects_a_ready_plan_for_a_forbidden_operation():
    """Even if every routing stage were bypassed, the evaluator refuses."""
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    task = FORBIDDEN_SEARCH[0]
    decision = TaskDecision(action="web_search", in_scope=True, should_execute=True,
                            confidence=1, reason="promoted upstream", web_query="PANDA papers")
    plan = build_workflow_plan(decision, task, project_policy=policy)
    assert plan.status == "ready"

    review = evaluate_workflow_plan(plan, task, policy)

    item = next(item for item in review.rubric if item.criterion == "operation_authorization")
    assert review.status == "rejected"
    assert item.result == "fail"
    assert "Do not use WEB-SEARCH" in item.detail


def test_plan_evaluator_passes_an_operation_the_request_does_not_forbid():
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    decision = TaskDecision(action="web_search", in_scope=True, should_execute=True,
                            confidence=1, reason="search", web_query=POSITIVE_SEARCH)
    plan = build_workflow_plan(decision, POSITIVE_SEARCH, project_policy=policy)

    review = evaluate_workflow_plan(plan, POSITIVE_SEARCH, policy)

    item = next(item for item in review.rubric if item.criterion == "operation_authorization")
    assert item.result == "pass"
    assert review.status == "approved"


# --- end to end: the dispatcher is never reached for a forbidden search -----

@pytest.fixture
def graph_app(tmp_path, request):
    if StateGraph is None:
        pytest.skip("Run in the project Docker environment.")
    changes = {
        "PROJECT_ROOT": tmp_path, "SESSION_ROOT": tmp_path / "sessions",
        "TRACE_ROOT": tmp_path / "traces", "TOOL_LOG_ROOT": tmp_path / "tool_logs",
        "EXECUTE_TOOLS": False, "TRACE_ENABLED": False, "TRANSIENT_TRACE": False,
    }
    previous = {key: getattr(settings, key) for key in changes}
    request.addfinalizer(lambda: configure_runtime(**previous))
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    configure_runtime(**changes)
    recorder = Mock(append=Mock(), instrument_node=lambda _name, node: node)
    context = _GraphContext(
        profile_id="default",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        project_policy=policy, recorder=recorder,
        price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=None, semantic_reviewer=None,
        intent_router=None, input_content_mapper=None,
        response_llm=Mock(invoke=Mock(return_value=AIMessage(content="Reply."))),
        semantic_model_name="fake", router_model_name="fake", response_model_name="fake",
        semantic_prompt="Interpret.", intent_prompt="Classify.", response_prompt="Explain.",
        router_max_tokens=1200, response_max_tokens=800, task_token_budget=30_000,
    )
    return SimpleNamespace(app=compile_graph(context), recorder=recorder)


def _run_graph(graph_app, task: str):
    interpretation = SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "Cohort grouping",
        "outcome_hypotheses": [hypothesis()],
    })
    search = Mock(return_value="Search results: TP53 official gene record.")
    with patch.object(router_invocation, "_invoke_semantic_interpreter",
                      side_effect=lambda c, s, t, u: (interpretation, u, [], None, frozenset())), \
         patch.object(router_invocation, "_invoke_semantic_discriminator",
                      side_effect=lambda c, s, t, i, m, u, w: (i, m, u, w)), \
         patch.object(router_invocation, "_invoke_intent_router",
                      side_effect=lambda c, s, t, i, m, u, w: (
                          IntentDecision(mode="answer", confidence=1, reason="scripted"), u, w, False)), \
         patch("netzoo_agent_core.routing.dispatch.query_web_search", search):
        result = graph_app.app.invoke({"messages": [HumanMessage(content=task)]})
    events = [call.args[1] for call in graph_app.recorder.append.call_args_list]
    return result, search, events


@pytest.mark.parametrize("task", FORBIDDEN_SEARCH)
def test_graph_never_dispatches_a_forbidden_search(graph_app, task):
    result, search, events = _run_graph(graph_app, task)

    search.assert_not_called()
    assert result.get("tool_results", []) == []
    assert "tool.started" not in events
    assert "routing.operation_restrictions_read" in events


def test_graph_still_dispatches_a_requested_search(graph_app):
    """Positive control: the mocked dispatcher is reachable on this path."""
    result, search, events = _run_graph(graph_app, POSITIVE_SEARCH)

    search.assert_called_once()
    assert "tool.started" in events
    assert [item["action"] for item in result["tool_results"]] == ["web_search"]


# --- a run ban beside a preview request means "not now" ---------------------

# Both are recorded requests (docs/research-log manual gene-validation and
# preview trials). The CLI's /execute re-routes this same text with execution
# on, so refusing the preview here would also refuse the later /execute.
PREVIEW_NOT_NOW = (
    "請為這組檔案準備 PANDA aggregate TF-to-gene regulatory network 的 dry-run plan。\n"
    "建立 plan 前先自動執行 input preflight。\n"
    "不要執行實際 PANDA 分析，也不要要求我輸入 `/execute`。\n"
    "expression_file=e.tsv\nmotif_file=m.tsv\nppi_file=p.tsv",
    "請建立 PANDA workflow preview。\nexpression_file=e.tsv\nmotif_file=m.tsv\nppi_file=p.tsv\n"
    "先建立 workflow preview，不要直接執行 PANDA，\n並明確告訴我是否可以輸入 /execute。",
)


@pytest.mark.parametrize("task", PREVIEW_NOT_NOW)
def test_a_run_ban_beside_a_preview_request_keeps_the_preview(task):
    authorization = read_operation_authorization(task)

    assert authorization.preview_requested
    assert forbidding_reason(authorization, "run_panda") is None


def test_a_cli_command_name_is_not_a_forbidden_operation():
    task = "請執行 PANDA 的 dry-run。僅產生 dry-run；不要輸入 /execute。"

    assert read_operation_authorization(task).forbidden == []
    assert reconcile_request_mode(task, "guidance") == "execute"


@pytest.mark.parametrize("task", [
    "My data has many zeros. Which workflow should I use? Do not run it.",
    "Please provide guidance only; do not execute the analysis.",
])
def test_a_run_ban_without_a_preview_refuses_the_run(task):
    assert forbidding_reason(read_operation_authorization(task), "run_panda") is not None


def test_guidance_only_is_an_explain_only_request():
    task = "Which netZooPy workflow is the closest match? Guidance only, please."
    authorization = read_operation_authorization(task)

    assert authorization.explain_only == "Guidance only"
    assert forbidding_reason(authorization, "run_dragon") is not None


@pytest.mark.parametrize("task", [
    "We just want one regulatory network for the epileptic rats and one for the controls, "
    "without testing anything.",
    "We simply want a co-expression network for each biopsy to browse, without any comparison or test.",
])
def test_a_statistical_test_is_not_a_forbidden_operation(task):
    assert read_operation_authorization(task).forbidden == []


def test_a_preview_never_lifts_a_search_or_inspection_ban():
    """Searches and input checks act within the turn; preview mode does not hold them."""
    task = "Prepare the PANDA dry-run preview. Do not search the web and do not inspect anything."
    authorization = read_operation_authorization(task)

    assert forbidding_reason(authorization, "run_panda") is None
    assert forbidding_reason(authorization, "web_search") is not None
    assert forbidding_reason(authorization, "inspect_inputs") is not None


# --- the CLI: "preview, not yet" keeps the preview path --------------------

from test_workflow_continuation import GOAL, runtime, write_bundle  # noqa: E402,F401
from netzoo_agent_core.cli.conversation import run_conversation  # noqa: E402


def _converse(runtime, reply):  # noqa: F811
    write_bundle(runtime.root)
    runtime.cli.input_func.side_effect = [GOAL, reply, "/execute", "yes", "exit"]
    assert run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli) == 0
    return runtime.results


def test_not_now_preview_reply_keeps_the_input_and_preview_path(runtime):  # noqa: F811
    """The same conversation as the unbanned one: confirm inputs, approved preview."""
    results = _converse(runtime, "Prepare the LIONESS-PUMA preview with the data that I have, "
                                 "but do not run it yet.")

    assert [result["plan"]["status"] for result in results] == [
        "respond_only", "needs_confirmation", "ready",
    ]
    assert results[-1]["plan_evaluation"]["status"] == "approved"
    assert [(item["action"], item["status"]) for item in results[-1]["tool_results"]] == [
        ("inspect_inputs", "success"), ("run_lioness_puma", "dry_run"),
    ]
    assert settings.EXECUTE_TOOLS is False


def test_a_reply_that_forbids_the_run_without_a_preview_gets_no_plan(runtime):  # noqa: F811
    """Control: the model accepted the workflow, but the user's words refuse the run."""
    results = _converse(runtime, "That is the right workflow, but do not run it.")

    assert results[1]["plan"]["status"] == "respond_only"
    assert results[1]["plan"]["decision"]["operation_authorization"]["blocked_action"] == (
        "run_lioness_puma"
    )
    assert all(result["tool_results"] == [] for result in results)


def test_a_ban_cut_from_the_routing_text_still_stops_the_search(graph_app):
    """F3 is item 2's; until then the evaluator re-reads the whole message.

    Routing reads only the last 6,000 characters, so it never sees the opening
    ban and plans the search the tail asks for. The plan evaluator reads the
    full message and refuses it, so the dispatcher is never reached.
    """
    task = ("Do not search the web or run anything; explain only.\n" + "x" * 6100
            + "\nPlease use WEB-SEARCH to search for the official TP53 record.")

    result, search, events = _run_graph(graph_app, task)

    search.assert_not_called()
    assert "plan.rejected" in events
    rubric = {item["criterion"]: item["result"] for item in result["plan_evaluation"]["rubric"]}
    assert rubric["operation_authorization"] == "fail"
