"""Picking an option of a reply card resolves without the reply classifier.

A card's options come from the previous turn's own decision, so each one maps
to text the machine already accepts: a confirmed-outcome marker, a workflow
continuation, a follow-up that restates the goal, or a command. These tests
drive the real machine (and the socket driver) with only the graph faked.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core import session as session_module  # noqa: E402
from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, LLMUsage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.engine import ConversationMachine, Prompt, Turn  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402

from test_cli_lifecycle import _fake_cli_runtime, _workflow_result  # noqa: E402
from test_server_driver import _Harness  # noqa: E402

ROOT = Path(__file__).parents[1]
POLICY = ProjectPolicyLoader(ROOT).load()
TASK = "I want one TF-gene regulatory network for the whole cohort. Which method? Advice only."
TIE = ["run_panda", "run_otter", "run_giraffe"]


@pytest.fixture(autouse=True)
def _planning_mode():
    previous = {name: getattr(settings, name) for name in ("EXECUTE_TOOLS", "TEST_DATA_MODE", "PRESENTATION_MODE")}
    configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False, PRESENTATION_MODE="state_machine")
    yield
    configure_runtime(**previous)


def _tie_result(task: str = TASK) -> dict:
    decision = TaskDecision.model_validate({
        "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.9, "reason": "Scripted.",
        "capability_match_status": "ambiguous", "hypothesis_actions": TIE,
        "clarification_question": "Which modeling assumption best matches your experiment?",
        "outcome_hypotheses": [{
            "outcome": {"operation": "infer", "input_artifacts": ["expression_matrix"],
                        "artifact_type": "regulatory_network", "entity_types": ["tf", "gene"],
                        "regulator_types": ["tf"], "target_types": ["gene"], "granularity": "aggregate"},
            "confidence": 0.8, "evidence": [],
        }],
    })
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(),
             "messages": [HumanMessage(content=task)], "tool_results": [], "evaluation": None}
    out = response_module.respond(SimpleNamespace(project_policy=POLICY), state)
    return {**state, "messages": [HumanMessage(content=task), out["messages"][-1]],
            "reply_kind": out["reply_kind"], "token_usage": LLMUsage().model_dump()}


def _machine(results, **runtime_fields):
    runtime = _fake_cli_runtime(invoke_error=list(results))
    runtime.project_policy = POLICY
    for name, value in runtime_fields.items():
        setattr(runtime, name, value)
    return runtime, ConversationMachine(SimpleNamespace(task=None, keep_session=False), runtime)


def _run_until_prompt(machine):
    events = []
    while True:
        action = machine.next_action()
        if isinstance(action, Turn):
            events.extend(machine.run_turn())
            continue
        return action, events


def _after_tie(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    runtime, machine = _machine([_tie_result(), _tie_result()])
    _run_until_prompt(machine)
    machine.submit(TASK)
    prompt, events = _run_until_prompt(machine)
    return runtime, machine, prompt, events


def test_the_reply_message_carries_its_card_and_the_prompt_its_options(tmp_path, monkeypatch):
    _, _, prompt, events = _after_tie(tmp_path, monkeypatch)
    message = next(event for event in events if event.kind == "message")
    assert "OTTER" in message.text  # the full reply is unchanged
    assert message.card["kind"] == "method_choice"
    assert isinstance(prompt, Prompt) and prompt.kind == "main"
    assert [option["label"] for option in prompt.card["choices"]["options"]] == ["PANDA", "OTTER", "GIRAFFE"]


def test_picking_a_method_confirms_it_without_the_reply_classifier(tmp_path, monkeypatch):
    runtime, machine, _, _ = _after_tie(tmp_path, monkeypatch)
    machine.submit("Use OTTER")
    assert machine.state.pending_task.startswith("CONFIRMED_OUTCOME_ACTION=run_otter.")
    assert "Do not execute it yet." in machine.state.pending_task
    assert runtime.reply_resolver.resolve.call_count == 0
    assert machine.state.pending_execute_once is False


def test_a_number_picks_the_option_shown_with_it(tmp_path, monkeypatch):
    _, machine, _, _ = _after_tie(tmp_path, monkeypatch)
    machine.submit("3")
    assert machine.state.pending_task.startswith("CONFIRMED_OUTCOME_ACTION=run_giraffe.")


def test_start_a_new_task_returns_to_the_first_question(tmp_path, monkeypatch):
    _, machine, prompt, _ = _after_tie(tmp_path, monkeypatch)
    new = next(step for step in prompt.card["next_steps"] if step["key"] == "new-task")
    machine.submit(new["answer"])
    assert machine.state.next_prompt.kind == "initial"
    assert machine.state.reply_card is None
    assert machine.next_action().card is None


def test_free_text_still_goes_to_the_reply_classifier(tmp_path, monkeypatch):
    runtime, machine, _, _ = _after_tie(tmp_path, monkeypatch)
    runtime.reply_resolver.resolve.side_effect = RuntimeError("classifier reached")
    with pytest.raises(RuntimeError, match="classifier reached"):
        machine.submit("How do these differ for single-cell data?")


def test_no_option_grants_execution(tmp_path, monkeypatch):
    for index in range(1, 4):
        _, machine, prompt, _ = _after_tie(tmp_path, monkeypatch)
        machine.submit(str(index))
        assert machine.state.pending_execute_once is False
        assert "Do not execute it yet." in machine.state.pending_task
        assert settings.EXECUTE_TOOLS is False


def test_a_workflow_option_outside_the_turns_offer_is_refused(tmp_path, monkeypatch):
    _, machine, _, _ = _after_tie(tmp_path, monkeypatch)
    card = machine.state.reply_card
    # A next step naming a workflow that neither the decision's candidates nor
    # the card's own question offered cannot resolve.
    card["next_steps"] = [{"key": "plan-run_sambar", "label": "Plan SAMBAR", "description": "",
                           "answer": "Start planning SAMBAR", "available": True, "reason": "",
                           "action": "run_sambar", "resolution": "plan_workflow", "paths": []}]
    card["choices"] = None
    events = machine.submit("Start planning SAMBAR")
    assert machine.state.pending_task is None
    assert "no longer matches" in events[0].text


def test_execute_option_asks_for_the_same_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    dry_run = {**_workflow_result("run it", status="dry_run"), "reply_kind": "execution"}
    runtime, machine = _machine([dry_run])
    _run_until_prompt(machine)
    configure_runtime(TEST_DATA_MODE=True)
    machine.submit("run it")
    prompt, _ = _run_until_prompt(machine)
    assert prompt.card["kind"] == "plan_ready"
    execute = next(step for step in prompt.card["next_steps"] if step["key"] == "execute")
    machine.submit(execute["answer"])
    confirmation = machine.next_action()
    assert confirmation.kind == "execution_confirmation"
    assert settings.EXECUTE_TOOLS is False


def test_the_socket_driver_sends_the_card_with_the_message_and_the_view(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    runtime = _fake_cli_runtime(invoke_error=[_tie_result()])
    runtime.project_policy = POLICY
    with _Harness(runtime) as harness:
        harness.next("view")
        harness.answer(TASK)
        message = harness.next("message")
        assert message.payload["card"]["kind"] == "method_choice"
        view = harness.next("view")
        assert view.payload["card"]["choices"]["options"][0]["answer"] == "Use PANDA"
        harness.answer("exit")
        harness.next("stopped")


def test_a_finished_turn_records_the_sessions_models_output_folder_and_brief_reply(tmp_path, monkeypatch):
    from netzoo_agent_core.session_meta import card_for, load_meta

    monkeypatch.setattr(session_module, "SESSION_ROOT", tmp_path / "sessions")
    runtime, machine = _machine([_tie_result()])
    runtime.session_models = {"response": "openai/gpt-4o-mini", "router": "openai/gpt-4o-mini"}
    _run_until_prompt(machine)
    machine.submit(TASK)
    _run_until_prompt(machine)
    meta = load_meta("test-session", sessions_root=tmp_path / "sessions")
    assert meta["models"] == {"response": "openai/gpt-4o-mini", "router": "openai/gpt-4o-mini"}
    assert meta["output_dir"] == "outputs/sessions/test-session"
    reply = _tie_result()["messages"][-1].content
    assert card_for(meta, reply)["kind"] == "method_choice"
    assert (tmp_path / "session_meta" / "test-session.json").exists()


def test_a_turn_plans_default_outputs_inside_the_sessions_folder():
    from netzoo_agent_core.session_outputs import session_output_dir, session_output_scope

    assert session_output_dir() is None
    with session_output_scope("a1b2c3d4"):
        assert session_output_dir() == "outputs/sessions/a1b2c3d4"
    with session_output_scope("../escape"):
        assert session_output_dir() is None
    assert session_output_dir() is None


def test_a_plan_inside_a_session_writes_its_defaults_to_that_sessions_folder():
    import netzoo_agent as agent
    from netzoo_agent_core.session_outputs import session_output_scope

    decision = agent.TaskDecision(
        action="run_cobra", in_scope=True, should_execute=True, confidence=0.95, reason="Run COBRA.",
        expression_file="data/cobra-toy/expression.tsv", design_file="data/cobra-toy/design.tsv",
    )
    with session_output_scope("a1b2c3d4"):
        plan = agent.build_workflow_plan(decision, "Run COBRA on the demo data")
    assert plan.decision["output_dir"] == "outputs/sessions/a1b2c3d4"
    explicit = decision.model_copy(update={"output_dir": "outputs/my-run"})
    with session_output_scope("a1b2c3d4"):
        plan = agent.build_workflow_plan(explicit, "Run COBRA; write to outputs/my-run")
    assert plan.decision["output_dir"] == "outputs/my-run"
