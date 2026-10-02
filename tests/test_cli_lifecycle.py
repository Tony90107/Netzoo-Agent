from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage,
    ContextualReplyResolution,
    HumanMessage,
    FollowUpContext,
    InputBundleOption,
    InputEvidence,
    LLMUsage,
    NextTurnPrompt,
    PlanEvaluationResult,
    PreferenceProposal,
    TaskDecision,
    WorkflowPlan,
    WorkflowStep,
)
from netzoo_agent_core.cli.reply_resolution import ReplyResolutionResult  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.settings import PROJECT_ROOT  # noqa: E402
from netzoo_agent_core.tracing import NullTraceRecorder  # noqa: E402


def _fake_cli_runtime(*, invoke_error, interactive_answers=(), reply_resolver=None):
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    input_func = Mock(side_effect=interactive_answers)
    invoke_graph_turn_func = Mock(side_effect=invoke_error)

    recorder = Mock()
    recorder.start_run.return_value = "test-run"
    return bootstrap.CliRuntime(
        memory=SimpleNamespace(
            profile_id="test-profile",
            profile_store=Mock(),
            episode_store=Mock(),
        ),
        project_policy=Mock(),
        session_id="test-session",
        resume_id=None,
        conversation=[],
        pending_plan=None,
        active_usage=None,
        run_id=None,
        recorder=recorder,
        trace_store=Mock(),
        ensure_trace_sync=lambda _run_id: None,
        app=object(),
        input_func=input_func,
        invoke_graph_turn_func=invoke_graph_turn_func,
        reply_resolver=reply_resolver or Mock(),
    )


def test_invalid_prior_workflow_control_keeps_cli_at_current_prompt():
    runtime = _fake_cli_runtime(invoke_error=AssertionError("unexpected graph turn"))
    machine = ConversationMachine(SimpleNamespace(task=None), runtime)
    prompt = NextTurnPrompt(
        kind="recommended_workflow", question="Continue?", continuation_action="run_otter",
    )
    machine.state.next_prompt = prompt
    machine.state.follow_up_context = FollowUpContext(
        prior_user_goal="Use OTTER with precision=invalid",
        prompt_kind=prompt.kind, prompt_question=prompt.question,
        candidate_actions=["run_otter"], continuation_action="run_otter",
    )

    events = machine._submit_option({
        "resolution": "plan_workflow", "action": "run_otter", "answer": "Use OTTER",
    })

    assert len(events) == 1 and events[0].kind == "notice"
    assert "parameter is invalid" in events[0].text
    assert machine.state.pending_continuation is None
    assert machine.state.pending_task is None
    assert machine.state.next_prompt is prompt


def _guidance_result(goal: str) -> dict:
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="Guidance requested.",
        hypothesis_actions=["run_puma", "run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective=goal,
        decision=decision.model_dump(),
        status="respond_only",
    )
    return {
        "messages": [
            HumanMessage(content=goal),
            AIMessage(content="Use PUMA followed by LIONESS-PUMA."),
        ],
        "plan": plan.model_dump(),
        "tool_results": [],
        "evaluation": None,
        "token_usage": LLMUsage().model_dump(),
    }


def _workflow_result(goal: str, *, status: str) -> dict:
    action = "run_lioness_puma"
    decision = TaskDecision(
        action=action,
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
        expression_file="data/lioness-toy/expression.tsv",
        motif_file="data/lioness-toy/prior-puma.tsv",
        ppi_file="data/lioness-toy/ppi.tsv",
        mirna_file="data/lioness-toy/mirna.txt",
        output_file="outputs/aggregate.tsv",
        lioness_output="outputs/lioness.tsv",
    )
    plan = WorkflowPlan(
        workflow="LIONESS-PUMA",
        objective=goal,
        decision=decision.model_dump(),
        steps=[WorkflowStep(action=action, purpose="test")],
        status="ready",
    )
    return {
        "messages": [HumanMessage(content=goal), AIMessage(content=status)],
        "plan": plan.model_dump(),
        "tool_results": [
            {"action": action, "status": status, "summary": status}
        ],
        "evaluation": {"status": "completed", "reason": "done"},
        "plan_evaluation": PlanEvaluationResult(
            status="approved", score=100, summary="test"
        ).model_dump(),
        "token_usage": LLMUsage().model_dump(),
    }


def _rendered_guidance_result(goal: str) -> dict:
    response_module = importlib.import_module("netzoo_agent_core.graph.response")
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.95,
        reason="Guidance requested.",
        hypothesis_actions=["run_puma", "run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective=goal,
        decision=decision.model_dump(),
        status="respond_only",
    )

    class GuidanceResponse:
        def invoke(self, messages):
            return AIMessage(
                content=(
                    "Use PUMA followed by LIONESS-PUMA.\n\n"
                    "No tools were executed, and no files were inspected. "
                    "If you need to start, provide the required files."
                )
            )

    context = SimpleNamespace(
        project_policy=ProjectPolicyLoader(PROJECT_ROOT).load(),
        response_llm=GuidanceResponse(),
        response_prompt="Use only validated workflow facts.",
        response_model_name="fake",
        response_max_tokens=800,
        task_token_budget=20_000,
        price_catalog=PriceCatalog.from_environment(),
        recorder=NullTraceRecorder(),
    )
    state = {
        "messages": [HumanMessage(content=goal)],
        "decision": decision.model_dump(),
        "plan": plan.model_dump(),
        "tool_results": [],
    }
    response = response_module.respond(context, state)
    return {
        **state,
        **response,
        "messages": [state["messages"][0], response["messages"][0]],
        "evaluation": None,
    }


def _resolved_reply(kind: str):
    resolver = Mock()

    def resolve(context, reply, current_usage, run_id):
        resolved_task = None
        if kind == "follow_up":
            resolved_task = (
                f"Previous NetZoo goal: {context.prior_user_goal}\n"
                f"User follow-up: {reply}"
            )
        elif kind == "new_goal":
            resolved_task = reply
        return ReplyResolutionResult(
            ContextualReplyResolution(
                kind=kind,
                resolved_task=resolved_task,
                reason="Test resolution.",
            ),
            (
                LLMUsage.model_validate(current_usage)
                if current_usage is not None
                else LLMUsage()
            ),
        )

    resolver.resolve.side_effect = resolve
    return resolver


def _resolved_reply_sequence(*kinds: str):
    resolver = Mock()
    remaining = iter(kinds)

    def resolve(context, reply, current_usage, run_id):
        kind = next(remaining)
        resolved_task = None
        if kind == "follow_up":
            resolved_task = (
                f"Previous NetZoo goal: {context.prior_user_goal}\n"
                f"User follow-up: {reply}"
            )
        return ReplyResolutionResult(
            ContextualReplyResolution(
                kind=kind,
                resolved_task=resolved_task,
                reason="Test resolution.",
            ),
            (
                LLMUsage.model_validate(current_usage)
                if current_usage is not None
                else LLMUsage()
            ),
        )

    resolver.resolve.side_effect = resolve
    return resolver


def _accepted_workflow(action: str):
    resolver = Mock()

    def resolve(context, reply, current_usage, run_id):
        return ReplyResolutionResult(
            ContextualReplyResolution(
                kind="accept_workflow",
                selected_action=action,
                reason="The user asked to run a trusted candidate workflow.",
            ),
            (
                LLMUsage.model_validate(current_usage)
                if current_usage is not None
                else LLMUsage()
            ),
        )

    resolver.resolve.side_effect = resolve
    return resolver


def _decision() -> TaskDecision:
    return TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
    )


def test_cli_lifecycle_modules_define_the_intended_seams():
    commands = importlib.import_module("netzoo_agent_core.cli.commands")
    bootstrap = importlib.import_module("netzoo_agent_core.cli.bootstrap")
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")

    assert str(inspect.signature(commands.handle_preflight_command)) == (
        "(args) -> 'int | None'"
    )
    assert str(inspect.signature(bootstrap.bootstrap_memory)) == (
        "(args) -> 'MemoryRuntime'"
    )
    assert str(inspect.signature(conversation.run_conversation)) == (
        "(args, runtime: 'CliRuntime') -> 'int'"
    )


def test_one_shot_ordinary_failure_returns_one():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(invoke_error=RuntimeError("provider unavailable"))

    result = conversation.run_conversation(
        SimpleNamespace(task="run PANDA", keep_session=False),
        runtime,
    )

    assert result == 1


def test_one_shot_failed_tool_result_returns_one():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    task = "run the selected LIONESS-PUMA bundle"
    failed = _workflow_result(task, status="failed")
    failed["evaluation"] = {"status": "failed", "reason": "Tool failed."}
    runtime = _fake_cli_runtime(invoke_error=[failed])

    assert conversation.run_conversation(
        SimpleNamespace(task=task, keep_session=False), runtime,
    ) == 1
    assert runtime.recorder.finish_run.call_args.args[1] == "failed"


def test_interactive_ordinary_failure_can_continue():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("provider unavailable"),
        interactive_answers=["first request", "exit"],
    )

    result = conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False),
        runtime,
    )

    assert result == 0


def test_interrupt_remains_130():
    state_contracts = importlib.import_module("netzoo_agent_core.contracts.state")
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=state_contracts.AgentTurnInterrupted(),
    )

    result = conversation.run_conversation(
        SimpleNamespace(task="run PANDA", keep_session=False),
        runtime,
    )

    assert result == 130


def test_main_prompt_blocks_execute_without_a_ready_plan(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=False)
        runtime = _fake_cli_runtime(
            invoke_error=AssertionError("graph must not run"),
            interactive_answers=["/execute", "/status", "exit"],
        )

        result = conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        )

        assert result == 0
        runtime.invoke_graph_turn_func.assert_not_called()
        runtime.recorder.start_run.assert_not_called()
        prompts = [call.args[0] for call in runtime.input_func.call_args_list]
        assert prompts[0].startswith("\nWhat would you like to accomplish with NetZoo?")
        assert not prompts[0].startswith("\n[")
        assert prompts[1].startswith("\nWhat would you like to accomplish with NetZoo?")
        assert prompts[2].startswith("\nWhat would you like to accomplish with NetZoo?")
        output = capsys.readouterr().out
        assert "NetZoo agent started in Planning mode" in output
        assert "no approved, ready workflow plan" in output
        assert "Current mode: Planning" in output
        assert settings.EXECUTE_TOOLS is False
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_execute_after_preview_confirms_and_reuses_the_validated_task(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    task = "run the selected LIONESS-PUMA bundle"
    runtime = _fake_cli_runtime(
        invoke_error=[
            _workflow_result(task, status="dry_run"),
            _workflow_result(task, status="success"),
        ],
        interactive_answers=["/test", task, "/execute", "yes", "exit"],
    )
    previous = settings.EXECUTE_TOOLS
    previous_test_mode = settings.TEST_DATA_MODE
    try:
        configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False)

        assert conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        ) == 0

        assert runtime.invoke_graph_turn_func.call_count == 2
        submitted = [
            call.args[1]["messages"][-1].content
            for call in runtime.invoke_graph_turn_func.call_args_list
        ]
        assert submitted == [task, task]
        output = capsys.readouterr().out
        assert "execute it once" in output
        prompts = [call.args[0] for call in runtime.input_func.call_args_list]
        assert any("Your LIONESS-PUMA plan is ready" in prompt for prompt in prompts)
        assert any(
            "Run the validated LIONESS-PUMA workflow now? [y/N]" in prompt
            for prompt in prompts
        )
    finally:
        configure_runtime(
            EXECUTE_TOOLS=previous,
            TEST_DATA_MODE=previous_test_mode,
        )


def test_mode_menu_selection_blocks_execute_without_graph_or_trace(
    monkeypatch, capsys
):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    reader.read.side_effect = ["/execute", "exit"]
    monkeypatch.setattr(conversation, "TerminalInputReader", Mock(return_value=reader))
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=(),
    )
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=False)

        assert conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        ) == 0

        runtime.invoke_graph_turn_func.assert_not_called()
        runtime.recorder.start_run.assert_not_called()
        assert "no approved, ready workflow plan" in capsys.readouterr().out
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_slash_command_does_not_consume_missing_input_state():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="run PANDA",
        decision=_decision().model_dump(),
        evidence=[
            InputEvidence(
                field="expression_file",
                status="missing",
                reason="required",
                candidates=["data/expression.tsv"],
            )
        ],
        missing_inputs=["expression_file"],
        status="needs_input",
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/status", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.invoke_graph_turn_func.assert_not_called()
    prompts = [call.args[0] for call in runtime.input_func.call_args_list]
    assert sum("expression_file" in prompt for prompt in prompts) == 2


def test_execute_reports_missing_inputs_and_keeps_planning_mode(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="run PANDA",
        decision=_decision().model_dump(),
        evidence=[
            InputEvidence(
                field="expression_file",
                status="missing",
                reason="required",
            )
        ],
        missing_inputs=["expression_file"],
        status="needs_input",
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/execute", "exit"],
    )
    runtime.pending_plan = plan

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    assert "It still needs: expression_file" in capsys.readouterr().out
    assert settings.EXECUTE_TOOLS is False


def _condor_missing_output_plan() -> WorkflowPlan:
    return WorkflowPlan(
        workflow="CONDOR",
        objective="run CONDOR",
        decision=TaskDecision(
            action="run_condor",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="test",
            network_file="data/network.tsv",
        ).model_dump(),
        evidence=[
            InputEvidence(
                field="output_dir",
                status="missing",
                reason="required",
            )
        ],
        missing_inputs=["output_dir"],
        status="needs_input",
    )


def _complete_bundle_choice_plan() -> WorkflowPlan:
    fields = ("expression_file", "motif_file", "ppi_file", "mirna_file")
    first = {
        field_name: f"data/study-a/{field_name}.tsv" for field_name in fields
    }
    second = {
        field_name: f"data/study-b/{field_name}.tsv" for field_name in fields
    }
    return WorkflowPlan(
        workflow="LIONESS-PUMA",
        objective="run LIONESS-PUMA",
        decision=TaskDecision(
            action="run_lioness_puma",
            in_scope=True,
            should_execute=False,
            confidence=1.0,
            reason="test",
        ).model_dump(),
        evidence=[
            InputEvidence(
                field=field_name,
                status="missing",
                reason="Choose one complete validated input bundle.",
                candidates=[first[field_name], second[field_name]],
            )
            for field_name in fields
        ],
        input_bundle_options=[
            InputBundleOption(
                bundle_id="directory:data/study-a",
                directory="data/study-a",
                inputs=first,
            ),
            InputBundleOption(
                bundle_id="directory:data/study-b",
                directory="data/study-b",
                inputs=second,
            ),
        ],
        missing_inputs=list(fields),
        status="needs_input",
    )


def test_complete_bundle_selection_submits_all_inputs_atomically():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("captured continuation"),
        interactive_answers=["1", "exit"],
    )
    runtime.pending_plan = _complete_bundle_choice_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    invocation = runtime.invoke_graph_turn_func.call_args.args[1]
    submitted = invocation["messages"][-1].content
    for field_name in (
        "expression_file",
        "motif_file",
        "ppi_file",
        "mirna_file",
    ):
        assert f"{field_name} is data/study-a/{field_name}.tsv" in submitted
        assert f"SELECTED_FIELD={field_name}" in submitted
        assert f"data/study-b/{field_name}.tsv" not in submitted


def test_custom_bundle_mode_opens_field_wizard_and_allows_explicit_composition():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("captured continuation"),
        interactive_answers=["custom", "1", "2", "1", "2", "exit"],
    )
    runtime.pending_plan = _complete_bundle_choice_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    prompts = [call.args[0] for call in runtime.input_func.call_args_list]
    assert any("Custom input composition" in prompt for prompt in prompts)
    submitted = runtime.invoke_graph_turn_func.call_args.args[1]["messages"][-1].content
    assert "expression_file is data/study-a/expression_file.tsv" in submitted
    assert "motif_file is data/study-b/motif_file.tsv" in submitted
    assert "ppi_file is data/study-a/ppi_file.tsv" in submitted
    assert "mirna_file is data/study-b/mirna_file.tsv" in submitted


def _preference_confirmation_plan() -> WorkflowPlan:
    return WorkflowPlan(
        workflow="NO-TOOL",
        objective="remember preference",
        decision=TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=1.0,
            reason="test",
        ).model_dump(),
        status="needs_confirmation",
        preference_proposals=[
            PreferenceProposal(
                key="reuse_last_inputs",
                value="true",
                reason="explicit request",
            )
        ],
    )


def test_single_component_absolute_path_resolves_clarification():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("stop after captured continuation"),
        interactive_answers=["/output", "exit"],
    )
    runtime.pending_plan = _condor_missing_output_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.invoke_graph_turn_func.assert_called_once()
    invocation = runtime.invoke_graph_turn_func.call_args.args[1]
    assert "output_dir is /output" in invocation["messages"][-1].content


def test_path_clarification_disables_immediate_menu(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    reader.read.side_effect = ["/output", "exit"]
    reader_factory = Mock(return_value=reader)
    monkeypatch.setattr(conversation, "TerminalInputReader", reader_factory)
    runtime = _fake_cli_runtime(
        invoke_error=RuntimeError("captured continuation"),
        interactive_answers=(),
    )
    runtime.pending_plan = _condor_missing_output_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    assert reader.read.call_args_list[0].kwargs["menu_enabled"] is False
    assert "output_dir is /output" in runtime.invoke_graph_turn_func.call_args.args[1][
        "messages"
    ][-1].content


def test_recommended_follow_up_without_path_enables_immediate_menu(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    reader.read.return_value = "exit"
    monkeypatch.setattr(conversation, "TerminalInputReader", Mock(return_value=reader))
    monkeypatch.setattr(
        conversation,
        "initial_next_turn_prompt",
        lambda: conversation.NextTurnPrompt(
            kind="recommended_workflow",
            question="Continue with the recommended workflow?",
            expected_field=None,
        ),
    )
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=(),
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    assert reader.read.call_args_list[0].kwargs["menu_enabled"] is True


def test_slash_command_does_not_confirm_preference():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=["/help", "exit"],
    )
    runtime.pending_plan = _preference_confirmation_plan()

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    runtime.memory.profile_store.confirm.assert_not_called()
    runtime.invoke_graph_turn_func.assert_not_called()


def test_inline_menu_collapse_does_not_answer_preference_confirmation(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    reader = Mock()
    # The inline selector collapses inside TerminalInputReader; conversation
    # receives only the next submitted line, never a synthetic no answer.
    reader.read.side_effect = ["exit"]
    monkeypatch.setattr(conversation, "TerminalInputReader", Mock(return_value=reader))
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=(),
    )
    runtime.pending_plan = _preference_confirmation_plan()
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=True)

        assert conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        ) == 0

        assert settings.EXECUTE_TOOLS is True
        assert reader.read.call_count == 1
        assert "Save these long-term preferences?" in reader.read.call_args.args[0]
        runtime.memory.profile_store.confirm.assert_not_called()
        runtime.invoke_graph_turn_func.assert_not_called()
        assert runtime.recorder.mock_calls == []
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_menu_cancellation_preserves_outcome_prompt_and_mode(monkeypatch):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    outcome_prompt = conversation.NextTurnPrompt(
        kind="completed",
        question="Would you like to refine the completed result?",
    )
    monkeypatch.setattr(conversation, "initial_next_turn_prompt", lambda: outcome_prompt)
    reader = Mock()
    reader.read.side_effect = [None, "exit"]
    monkeypatch.setattr(conversation, "TerminalInputReader", Mock(return_value=reader))
    runtime = _fake_cli_runtime(
        invoke_error=AssertionError("graph must not run"),
        interactive_answers=(),
    )
    previous = settings.EXECUTE_TOOLS
    try:
        configure_runtime(EXECUTE_TOOLS=False)

        assert conversation.run_conversation(
            SimpleNamespace(task=None, keep_session=False), runtime
        ) == 0

        assert settings.EXECUTE_TOOLS is False
        assert reader.read.call_count == 2
        assert all(
            "Would you like to refine the completed result?" in call.args[0]
            for call in reader.read.call_args_list
        )
        runtime.memory.profile_store.confirm.assert_not_called()
        runtime.invoke_graph_turn_func.assert_not_called()
        assert runtime.recorder.mock_calls == []
    finally:
        configure_runtime(EXECUTE_TOOLS=previous)


def test_underspecified_follow_up_does_not_reinvoke_scientific_graph(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which tools produce sample-specific miRNA networks?"
    runtime = _fake_cli_runtime(
        invoke_error=[_guidance_result(goal)],
        interactive_answers=[goal, "certainly", "exit"],
        reply_resolver=_resolved_reply("needs_detail"),
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    assert runtime.invoke_graph_turn_func.call_count == 1
    assert "Please enter a concrete follow-up question" not in capsys.readouterr().out


def test_substantive_follow_up_reaches_graph_with_prior_goal_context():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which tools produce sample-specific miRNA networks?"
    follow_up = "What format should the motif prior use?"
    second_result = _guidance_result(follow_up)
    runtime = _fake_cli_runtime(
        invoke_error=[_guidance_result(goal), second_result],
        interactive_answers=[goal, follow_up, "exit"],
        reply_resolver=_resolved_reply("follow_up"),
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    second_invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    submitted = second_invocation["messages"][-1].content
    assert "Previous NetZoo goal:" in submitted
    assert "User follow-up: What format" in submitted


def test_run_follow_up_enters_selected_workflow_planning_without_reclassification():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which tools produce sample-specific miRNA networks?"
    follow_up = "can you run this with the data that i have?"
    runtime = _fake_cli_runtime(
        invoke_error=[_guidance_result(goal), _guidance_result(follow_up)],
        interactive_answers=[goal, follow_up, "exit"],
        reply_resolver=_accepted_workflow("run_lioness_puma"),
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    second_invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    submitted = second_invocation["messages"][-1].content
    assert "PREVIOUS_ACTION=run_lioness_puma" in submitted
    assert "CONFIRMED_OUTCOME_ACTION" not in submitted


def test_sample_specific_guidance_transcript_preserves_context_and_single_owner_output(
    capsys,
):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which tools produce sample-specific miRNA networks?"
    follow_up = "What format should the motif prior use?"
    resolver = _resolved_reply_sequence("needs_detail", "follow_up")
    runtime = _fake_cli_runtime(
        invoke_error=[
            _rendered_guidance_result(goal),
            _rendered_guidance_result(follow_up),
        ],
        interactive_answers=[goal, "certainly", follow_up, "exit"],
        reply_resolver=resolver,
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    output = capsys.readouterr().out
    assert output.index("PUMA") < output.index("LIONESS-PUMA")
    assert output.count("No files were inspected and no analysis ran.") == 2
    assert "If you need to start" not in output
    assert "Please enter a concrete follow-up question" not in output
    assert runtime.invoke_graph_turn_func.call_count == 2
    assert resolver.resolve.call_count == 2
    second_invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    submitted = second_invocation["messages"][-1].content
    assert "Previous NetZoo goal:" in submitted
    assert f"User follow-up: {follow_up}" in submitted
    prompts = [call.args[0] for call in runtime.input_func.call_args_list]
    assert any("Enter a follow-up question" in prompt for prompt in prompts)
    assert all("Reply yes" not in prompt for prompt in prompts)
