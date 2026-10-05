"""One request's requirements, read once and shared by every stage (plan item 2).

Long messages and stage transitions used to lose what the user stated:
routing read the last 6,000 characters while planning read the whole message,
and a continuation turn's planner cleared every path its own synthetic text
did not repeat, so files and outputs named in the original request were
replaced by defaults or a bundle question.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path[:0] = [str(Path(__file__).parents[1] / "scripts"), str(Path(__file__).parent)]

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.conversation import run_conversation  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, IntentDecision, LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.evaluation import evaluate_workflow_plan  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.routing_planning import classify_task  # noqa: E402
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision  # noqa: E402
from netzoo_agent_core.interpretation.request_requirements import read_request_requirements  # noqa: E402
from netzoo_agent_core.llm import latest_user_message, latest_user_task  # noqa: E402
from netzoo_agent_core.planning import build_workflow_plan  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.capability import reconcile_request_mode  # noqa: E402
from netzoo_agent_core.routing_window import HEAD_CHARS, routing_window, routing_window_parts  # noqa: E402
from netzoo_agent_core.settings import ROUTER_CONTEXT_MAX_CHARS  # noqa: E402
from netzoo_agent_core.tracing import NullTraceRecorder  # noqa: E402
from test_routing_evaluation import TASK, hypothesis  # noqa: E402
from test_workflow_continuation import GOAL, runtime, write_bundle  # noqa: E402,F401


def _text(chars: int) -> str:
    head = "HEAD-" + "h" * (HEAD_CHARS - 5)
    return head + "m" * (chars - HEAD_CHARS - 5) + "-TAIL"


# --- the routing window -----------------------------------------------------

@pytest.mark.parametrize("chars", [5_999, 6_000])
def test_a_request_within_the_budget_is_routed_whole(chars):
    text = _text(chars)

    assert routing_window(text) == text
    assert routing_window_parts(text)[1] == 0


@pytest.mark.parametrize("chars", [6_001, 6_100, 60_000])
def test_an_over_long_request_keeps_its_opening_and_its_end(chars):
    text = _text(chars)
    window, omitted = routing_window_parts(text)

    assert len(window) <= ROUTER_CONTEXT_MAX_CHARS
    assert window.startswith("HEAD-") and window.endswith("-TAIL")
    assert f"[... {omitted} characters of this request omitted ...]" in window
    assert len(window) - len(window.split("\n[... ")[0]) > 0
    assert HEAD_CHARS + omitted + len(window.rsplit("omitted ...]\n", 1)[1]) == chars


def test_every_stage_reads_the_same_window_of_the_latest_message():
    text = _text(7_000)
    messages = [HumanMessage(content="an earlier turn"), HumanMessage(content=text)]

    assert latest_user_message(messages) == text
    assert latest_user_task(messages) == routing_window(text)


# --- a long request keeps what its opening says ----------------------------

LONG_COMMAND = (
    "Run PANDA with expression_file=data/x/expression.tsv motif_file=data/x/motif.tsv "
    "ppi_file=data/x/ppi.tsv output_file=outputs/keep-me.tsv\n"
    + "Background notes. " * 400 + "\nPlease go ahead."
)


def test_an_opening_command_and_its_files_reach_routing():
    routed = latest_user_task([HumanMessage(content=LONG_COMMAND)])
    hydrated = hydrate_router_decision(
        TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=1, reason="x"),
        routed,
    )

    assert "Run PANDA with expression_file=" in routed
    assert hydrated.expression_file == "data/x/expression.tsv"
    assert hydrated.output_file == "outputs/keep-me.tsv"


def test_an_opening_prohibition_wins_over_a_closing_command():
    text = "Do not execute anything; explain only.\n" + "x" * 6_100 + "\nRun PANDA"
    requirements = read_request_requirements(text)

    assert [ban.kind for ban in requirements.operations.forbidden] == ["any"]
    assert requirements.operations.explain_only == "explain only"
    assert reconcile_request_mode(latest_user_task([HumanMessage(content=text)]), "answer") == "answer"


# --- the record ------------------------------------------------------------

def test_the_record_keeps_source_identity_stated_values_and_their_origin():
    text = "Run PANDA with expression_file=data/x.tsv output_file=out/p.tsv. Do not search the web."
    requirements = read_request_requirements(
        text, carried={"motif_file": "data/m.tsv", "expression_file": "data/old.tsv"},
    )
    stated = {(item.field, item.origin): item for item in requirements.stated}

    assert requirements.source_sha256 == hashlib.sha256(text.encode()).hexdigest()
    assert requirements.omitted_chars == 0
    # This turn's own statement replaces the carried one; the period ends the sentence.
    assert requirements.stated_value("expression_file") == "data/x.tsv"
    assert requirements.stated_value("output_file") == "out/p.tsv"
    assert ("expression_file", "earlier_turn") not in stated
    assert stated[("motif_file", "earlier_turn")].value == "data/m.tsv"
    assert text[slice(*stated[("expression_file", "this_turn")].span)] == "data/x.tsv"
    assert [ban.kind for ban in requirements.operations.forbidden] == ["retrieve"]


def test_classify_records_the_routed_goal_beside_the_users_words():
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    context = SimpleNamespace(project_policy=policy, recorder=NullTraceRecorder(),
                              task_token_budget=30000, selection_condition_llm=None)
    interpretation = SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "Cohort grouping",
        "outcome_hypotheses": [hypothesis()],
    })
    usage = LLMUsage(budget_tokens=30000)
    with patch.object(router_invocation, "_invoke_semantic_interpreter",
                      return_value=(interpretation, usage, [], None, frozenset())), \
         patch.object(router_invocation, "_invoke_semantic_discriminator",
                      side_effect=lambda c, s, t, i, m, u, w: (i, m, u, w)), \
         patch.object(router_invocation, "_invoke_intent_router",
                      return_value=(IntentDecision(mode="answer", confidence=1, reason="s"), usage, [], False)):
        routed = classify_task(context, {"messages": [HumanMessage(content=TASK)]})

    requirements = routed["request_requirements"]
    assert requirements["goal"] == "Cohort grouping"
    assert requirements["source_sha256"] == hashlib.sha256(TASK.encode()).hexdigest()


# --- the planner trusts what the user stated, and only that ----------------

CONTINUATION = (
    "PREVIOUS_ACTION=run_panda. Continue the recommended PANDA workflow. "
    "The user accepted the previous capability recommendation.\nUser reply: yes"
)


def _carried_decision(**fields) -> TaskDecision:
    return hydrate_router_decision(
        TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=1,
                     reason="continuation", **fields),
        CONTINUATION,
    )


def test_the_planner_keeps_a_path_stated_in_the_request_a_continuation_carries():
    carried = {"output_file": "outputs/stated.tsv"}
    plan = build_workflow_plan(
        _carried_decision(**carried), CONTINUATION,
        requirements=read_request_requirements(CONTINUATION, carried=carried),
    )

    evidence = {item.field: item for item in plan.evidence}
    assert plan.decision["output_file"] == "outputs/stated.tsv"
    assert evidence["output_file"].status == "provided"


def test_a_path_nobody_stated_is_still_cleared():
    """The router-path guard stands: only the user's words are trusted."""
    plan = build_workflow_plan(
        _carried_decision(output_file="outputs/guessed.tsv"), CONTINUATION,
        requirements=read_request_requirements(CONTINUATION, carried={"output_file": "outputs/stated.tsv"}),
    )

    assert plan.decision["output_file"] != "outputs/guessed.tsv"


# --- the plan evaluator checks the plan against the record -----------------

def _ready_search_plan(task: str):
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    decision = TaskDecision(action="web_search", in_scope=True, should_execute=True,
                            confidence=1, reason="search", web_query=task)
    return build_workflow_plan(decision, task, project_policy=policy), policy


def _item(review, criterion):
    return next(item for item in review.rubric if item.criterion == criterion)


def test_the_evaluator_refuses_a_plan_that_replaces_a_stated_output():
    task = "Please use WEB-SEARCH to search for TP53."
    plan, policy = _ready_search_plan(task)
    plan.decision["output_file"] = "outputs/sessions/default.tsv"
    requirements = read_request_requirements(task, carried={"output_file": "outputs/mine.tsv"})

    review = evaluate_workflow_plan(plan, task, policy, requirements=requirements)

    assert review.status == "rejected"
    assert "the user stated outputs/mine.tsv" in _item(review, "request_requirements").detail


def test_the_evaluator_refuses_a_plan_for_a_different_request():
    task = "Please use WEB-SEARCH to search for TP53."
    plan, policy = _ready_search_plan(task)

    review = evaluate_workflow_plan(plan, task, policy,
                                    requirements=read_request_requirements(task + " Also BRCA1."))

    assert review.status == "rejected"
    assert "different request" in _item(review, "request_requirements").detail


def test_the_evaluator_passes_a_plan_that_keeps_the_record():
    task = "Please use WEB-SEARCH to search for TP53."
    plan, policy = _ready_search_plan(task)

    review = evaluate_workflow_plan(plan, task, policy, requirements=read_request_requirements(task))

    assert review.status == "approved"
    assert _item(review, "request_requirements").result == "pass"


# --- CLI transitions keep what the original request stated ------------------

REPLY = "can you execute this workflow for me with the data that i have?"


def _converse(runtime, *answers):  # noqa: F811
    runtime.cli.input_func.side_effect = [*answers, "exit"]
    assert run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli) == 0
    return runtime.results


def test_outputs_stated_in_the_goal_survive_acceptance_and_confirmation(runtime):  # noqa: F811
    write_bundle(runtime.root)
    goal = GOAL + " output_file=outputs/my-net.tsv lioness_output=outputs/my-lioness.tsv"

    results = _converse(runtime, goal, REPLY, "yes")

    for result in results[1:]:
        assert result["plan"]["decision"]["output_file"] == "outputs/my-net.tsv"
        assert result["plan"]["decision"]["lioness_output"] == "outputs/my-lioness.tsv"
    assert results[-1]["plan"]["status"] == "ready"
    assert results[-1]["plan_evaluation"]["status"] == "approved"


STUDY_B = (" expression_file=data/study-b/expression.tsv motif_file=data/study-b/prior-puma.tsv"
           " ppi_file=data/study-b/ppi.tsv mirna_file=data/study-b/mirna.txt")


def test_inputs_stated_in_the_goal_are_used_instead_of_asking_for_a_bundle(runtime):  # noqa: F811
    write_bundle(runtime.root, "study-a")
    write_bundle(runtime.root, "study-b")

    results = _converse(runtime, GOAL + STUDY_B, REPLY)

    plan = results[-1]["plan"]
    assert plan["status"] == "ready"
    assert results[-1]["plan_evaluation"]["status"] == "approved"
    assert plan["decision"]["expression_file"] == "data/study-b/expression.tsv"
    assert {item["status"] for item in plan["evidence"] if item["field"] != "output_file"
            and item["field"] != "lioness_output"} == {"provided"}
    assert not plan.get("input_bundle_options")


def test_a_long_goal_carries_its_opening_files_into_the_continuation(runtime):  # noqa: F811
    """The follow-up context keeps only the last 4,000 characters of the goal."""
    write_bundle(runtime.root, "study-a")
    write_bundle(runtime.root, "study-b")
    goal = STUDY_B.strip() + "\n" + "Study background. " * 300 + "\n" + GOAL

    results = _converse(runtime, goal, REPLY)

    assert len(goal) > 4_000
    assert results[-1]["plan"]["decision"]["expression_file"] == "data/study-b/expression.tsv"
    assert results[-1]["plan"]["status"] == "ready"
    assert results[-1]["plan_evaluation"]["status"] == "approved"


def test_execute_re_routes_the_preview_with_the_values_the_user_stated(runtime):  # noqa: F811
    """/execute re-plans the preview's own text, which does not repeat the files."""
    write_bundle(runtime.root, "study-a")
    write_bundle(runtime.root, "study-b")
    executed = Mock(return_value="Execution completed.")

    with patch("netzoo_agent_core.graph.execution.execute_selected_tool", executed):
        results = _converse(runtime, GOAL + STUDY_B, REPLY, "/execute", "yes")

    preview, run = results[-2:]
    assert preview["plan"]["status"] == "ready"
    assert preview["plan_evaluation"]["status"] == "approved"
    assert run["plan"]["status"] == "ready"
    assert run["plan_evaluation"]["status"] == "approved"
    assert run["plan"]["decision"]["expression_file"] == "data/study-b/expression.tsv"
    assert [call.args[0].action for call in executed.call_args_list][-1] == "run_lioness_puma"
    assert settings.EXECUTE_TOOLS is False
