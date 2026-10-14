"""M2 B (2026-10-14): a message that changes the run a turn planned or held is that run, checked again.

a24b K02: after "Can you run DRAGON on our liver proteomics and phosphoproteomics tables?" started the input wizard,
"I just checked: the phospho data come from a different set of 25 mice than the proteomics." continued it as a wizard
answer and the run kept its approval. K09: after the GPU run was held, "Never mind the GPU - CPU is fine, just use
single precision." was answered as guidance and no run was planned. K06: the lambdas the check verified never reached
the run's controls.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.cli.reply_resolution import ReplyResolutionResult  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage, ContextualReplyResolution, HumanMessage, LLMUsage, TaskDecision, WorkflowPlan,
)
from netzoo_agent_core.contracts.capability_check import RunVerdict  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine, Turn  # noqa: E402
from netzoo_agent_core.engine.recheck import _is_question, _wizard_answer, recheck_task  # noqa: E402

K02_GOAL = "Can you run DRAGON on our liver proteomics and phosphoproteomics tables?"
K02_REPLY = "I just checked: the phospho data come from a different set of 25 mice than the proteomics."
K09_GOAL = "Run OTTER on the GPU for our 120 samples; motif prior, PPI and expression are attached."
K09_REPLY = "Never mind the GPU - CPU is fine, just use single precision."


def test_what_answers_an_input_question():
    for text in ("2", "custom", "yes", "data/x/layer1.tsv", "omics_layer_1=a.tsv omics_layer_2=b.tsv", "/proj/x",
                 "expr.tsv", "use /data/my/layer1.tsv please"):
        assert _wizard_answer(text), text
    for text in (K02_REPLY, K09_REPLY, "Actually the samples are single cells from one 10x run."):
        assert not _wizard_answer(text), text
    assert _is_question("Why can OTTER not use the GPU?") and not _is_question(K09_REPLY)


def test_the_rechecked_request_keeps_the_goal_and_every_change():
    conversation = [HumanMessage(content=K02_GOAL), AIMessage(content="Select input 1 of 2"),
                    HumanMessage(content="PREVIOUS_ACTION=run_dragon. Continue ...")]
    first = recheck_task(conversation, K02_REPLY)
    assert first == f"Previous NetZoo goal: {K02_GOAL}\nUser follow-up: {K02_REPLY}"
    second = recheck_task([*conversation, HumanMessage(content=first)], "Use only the 20 matched mice.")
    assert second == f"{first}\nUser follow-up: Use only the 20 matched mice."


def _runtime(*, conversation, pending_plan=None, resumed_turn=None, resolver=None):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    recorder = Mock()
    recorder.start_run.return_value = "run-2"
    return bootstrap.CliRuntime(
        memory=SimpleNamespace(profile_id="p", profile_store=Mock(), episode_store=Mock()),
        project_policy=Mock(), session_id="s", resume_id="s", conversation=conversation,
        pending_plan=pending_plan, active_usage=None, run_id="run-2", recorder=recorder, trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None, app=object(), input_func=Mock(), invoke_graph_turn_func=Mock(),
        reply_resolver=resolver or Mock(), resumed_turn=resumed_turn,
    )


def _wizard_plan() -> WorkflowPlan:
    decision = TaskDecision(action="run_dragon", in_scope=True, should_execute=True, confidence=1.0, reason="r",
                            run_verdict=RunVerdict(action="run_dragon", verdict="no_result"))
    return WorkflowPlan(workflow="DRAGON", objective=K02_GOAL, decision=decision.model_dump(), status="needs_input",
                        missing_inputs=["omics_layer_1", "omics_layer_2"])


def test_k02_a_condition_after_the_wizard_rechecks_the_run():
    machine = ConversationMachine(SimpleNamespace(task=K02_REPLY), _runtime(
        conversation=[HumanMessage(content=K02_GOAL), AIMessage(content="Select input 1 of 2")],
        pending_plan=_wizard_plan()))
    action = machine.next_action()
    assert isinstance(action, Turn) and action.task == f"Previous NetZoo goal: {K02_GOAL}\nUser follow-up: {K02_REPLY}"
    continuation = machine.state.pending_continuation
    assert continuation.action == "run_dragon" and continuation.recheck
    assert machine.state.pending_plan is None


def test_a_path_after_the_wizard_still_answers_it():
    machine = ConversationMachine(SimpleNamespace(task="data/dragon-toy/layer1.tsv"), _runtime(
        conversation=[HumanMessage(content=K02_GOAL)], pending_plan=_wizard_plan()))
    machine.next_action()
    assert machine.state.pending_continuation is None or not machine.state.pending_continuation.recheck


def _held_turn() -> dict:
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="held",
                            execution_requested=True, recommended_actions=["run_otter"],
                            run_verdict=RunVerdict(action="run_otter", verdict="gap", held=True))
    plan = WorkflowPlan(workflow="NO-TOOL", objective=K09_GOAL, decision=decision.model_dump(), status="respond_only")
    return {"plan": plan.model_dump(), "tool_results": [], "evaluation": None}


def _resolver(reply):
    resolver = Mock()
    resolver.resolve.return_value = ReplyResolutionResult(ContextualReplyResolution(
        kind="follow_up", reason="r", resolved_task=f"Previous NetZoo goal: {K09_GOAL}\nUser follow-up: {reply}"),
        LLMUsage(budget_tokens=1000))
    return resolver


def test_k09_a_change_to_the_held_run_rechecks_it_and_a_question_does_not():
    machine = ConversationMachine(SimpleNamespace(task=K09_REPLY), _runtime(
        conversation=[HumanMessage(content=K09_GOAL), AIMessage(content="Tell me to run OTTER anyway")],
        resumed_turn=_held_turn(), resolver=_resolver(K09_REPLY)))
    assert machine.state.next_prompt.held_run
    action = machine.next_action()
    assert isinstance(action, Turn) and action.task.endswith(K09_REPLY)
    assert machine.state.pending_continuation.action == "run_otter" and machine.state.pending_continuation.recheck

    question = "Why can OTTER not use the GPU here?"
    machine = ConversationMachine(SimpleNamespace(task=question), _runtime(
        conversation=[HumanMessage(content=K09_GOAL), AIMessage(content="Tell me to run OTTER anyway")],
        resumed_turn=_held_turn(), resolver=_resolver(question)))
    machine.next_action()
    assert machine.state.pending_continuation is None


def test_a_recheck_continuation_is_not_approved_as_selected():
    from netzoo_agent_core.contracts.interaction import WorkflowContinuation
    from netzoo_agent_core.graph.continuation_invocation import continue_workflow

    task = f"Previous NetZoo goal: {K02_GOAL}\nUser follow-up: {K02_REPLY}"
    context = SimpleNamespace(project_policy=SimpleNamespace(workflows={"run_dragon": object()}), recorder=Mock())
    for recheck, verdict in ((False, "user_selected"), (True, None)):
        state = {"workflow_continuation": WorkflowContinuation(action="run_dragon", task=task, recheck=recheck)
                 .model_dump(), "budget_warnings": []}
        result = continue_workflow(context, state, task, LLMUsage(budget_tokens=1000))
        assert result.decision.action == "run_dragon"
        assert (result.decision.run_verdict.verdict if result.decision.run_verdict else None) == verdict


def test_k02_unmatched_samples_hold_a_named_run_with_no_ask():
    task = f"Previous NetZoo goal: {K02_GOAL}\nUser follow-up: {K02_REPLY}"
    from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions
    from netzoo_agent_core.interpretation.capability_check import build_capability_check, request_sentences
    from netzoo_agent_core.interpretation.run_check import run_check_verdict

    count = len(request_sentences(task))
    readings = {f"s{index}": {"role": "methods_question", "has": [], "about_methods": [], "asks": []}
                for index in range(1, count + 1)}
    readings["s1"]["about_methods"] = [K02_GOAL]
    readings["conditions"] = {**unstated_conditions(), "named_method": "DRAGON", "named_method_quote": "DRAGON",
                              "samples_matched": "different_samples",
                              "samples_matched_quote": "the phospho data come from a different set of 25 mice"}
    check, _ = build_capability_check(task, proposal_model(count).model_validate(readings))
    [result] = check.results()
    assert result.status == "not_available" and "cannot run on this data" in result.limits[0]
    assert run_check_verdict(check, "run_dragon")["verdict"] == "gap"


def test_k06_verified_settings_become_the_runs_controls():
    from test_method_conditions import K06_TURN2, _ask, _check

    from netzoo_agent_core.interpretation.method_conditions import verified_controls

    check = _check(K06_TURN2, _ask(
        "give it to me as an edge list, with fixed lambdas of 0.2 and 0.6", ["dragon.two_layer_network"],
        omics_layers=2, settings=[("DRAGON.output_format", "as an edge list", "an edge list"),
                                  ("DRAGON.lambda1", "fixed lambdas", "0.2"), ("DRAGON.lambda2", "fixed lambdas", "0.6")]))
    assert verified_controls(check, "run_dragon") == {"output_format": "edge_list", "lambda1": 0.2, "lambda2": 0.6}
    assert verified_controls(check, "run_otter") == {}
