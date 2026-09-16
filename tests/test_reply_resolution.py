from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.reply_resolution import (  # noqa: E402
    ContextualReplyResolver,
    build_reply_resolution_messages,
)
from netzoo_agent_core.cli.follow_up import resolve_next_turn_input  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    ContextualReplyResolution,
    FollowUpContext,
    NextTurnPrompt,
    ReplyIntentDecision,
    WorkflowConversationFact,
)
from netzoo_agent_core.interpretation.extraction import (  # noqa: E402
    is_versioned_documentation_request,
)


def _context(*, continuation_action=None, expected_field=None):
    return FollowUpContext(
        prior_user_goal="Which tools produce sample-specific miRNA networks?",
        prompt_kind="completed",
        prompt_question="Enter a follow-up question or describe another NetZoo goal.",
        candidate_actions=["run_puma", "run_lioness_puma"],
        continuation_action=continuation_action,
        expected_field=expected_field,
        alternative_action=None,
    )


def _outcome_clarification_context():
    context = _context()
    context.prompt_kind = "clarify_outcome"
    context.prompt_question = "Should the result be aggregate or sample-specific?"
    context.candidate_actions = ["run_panda", "run_lioness_panda"]
    context.candidate_workflows = [
        WorkflowConversationFact(
            action="run_panda",
            workflow="PANDA",
            required_inputs=["expression_file", "motif_file", "ppi_file"],
            granularities=["aggregate"],
        ),
        WorkflowConversationFact(
            action="run_lioness_panda",
            workflow="LIONESS-PANDA",
            required_inputs=["expression_file", "motif_file", "ppi_file"],
            granularities=["sample_specific"],
        ),
    ]
    return context


def _decision(
    kind: str,
    *,
    confidence: float = 0.98,
    selected_action: str | None = None,
    selected_granularity: str | None = None,
) -> ReplyIntentDecision:
    return ReplyIntentDecision(
        kind=kind,
        confidence=confidence,
        reason="Test classification.",
        selected_action=selected_action,
        selected_granularity=selected_granularity,
    )


def test_acknowledgement_without_offered_continuation_needs_detail():
    model = Mock()
    model.invoke.return_value = _decision("needs_detail")
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(_context(), "certainly", None, "run-1")

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None
    rendered_input = "\n".join(
        message.content for message in model.invoke.call_args.args[0]
    )
    assert "Which tools produce sample-specific miRNA networks?" in rendered_input
    assert "Enter a follow-up question" in rendered_input
    assert "certainly" in rendered_input


def test_llm_can_accept_trusted_recommended_workflow_without_repeating_guidance():
    model = Mock()
    model.invoke.return_value = _decision(
        "accept_workflow",
        selected_action="run_lioness_puma",
    )
    context = _context(continuation_action="run_lioness_puma")
    context.prompt_kind = "recommended_workflow"
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        context, "can you run this with the data that i have?", None, "run-1"
    )

    assert result.resolution.kind == "accept_workflow"
    assert result.resolution.selected_action == "run_lioness_puma"
    model.invoke.assert_called_once()
    rendered = "\n".join(
        message.content for message in model.invoke.call_args.args[0]
    )
    assert "using data already in their workspace" in " ".join(rendered.split())


def test_llm_may_select_only_a_workflow_from_trusted_completed_context():
    model = Mock()
    model.invoke.return_value = _decision(
        "accept_workflow",
        selected_action="run_lioness_puma",
    )
    context = _context()
    context.candidate_workflows = [
        WorkflowConversationFact(
            action="run_lioness_puma",
            workflow="LIONESS-PUMA",
            required_inputs=["expression_file", "motif_file", "ppi_file", "mirna_file"],
            granularities=["aggregate", "sample_specific"],
        )
    ]
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        context, "can you run this with the data that i have?", None, "run-1"
    )

    assert result.resolution.kind == "accept_workflow"
    assert result.resolution.selected_action == "run_lioness_puma"
    model.invoke.assert_called_once()


def test_llm_cannot_select_workflow_outside_trusted_context():
    model = Mock()
    model.invoke.return_value = _decision(
        "accept_workflow",
        selected_action="run_panda",
    )
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _context(continuation_action="run_lioness_puma"),
        "Use whatever workflow you think is appropriate.",
        None,
        "run-1",
    )

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.selected_action is None


def test_accepted_contextual_workflow_enters_planning_instead_of_guidance():
    prompt = NextTurnPrompt(
        kind="completed",
        question="Enter a follow-up question.",
    )
    resolution = ContextualReplyResolution(
        kind="accept_workflow",
        selected_action="run_lioness_puma",
        reason="The user asked to run the selected trusted workflow.",
    )

    task = resolve_next_turn_input(
        prompt,
        resolution,
        "can you run this with the data that i have?",
    )

    assert task is not None
    assert "PREVIOUS_ACTION=run_lioness_puma" in task
    assert "CONFIRMED_OUTCOME_ACTION" not in task


def test_outcome_clarification_accepts_aggregate_from_trusted_context():
    model = Mock()
    model.invoke.return_value = _decision(
        "accept_workflow",
        selected_action="run_panda",
        selected_granularity="aggregate",
    )
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _outcome_clarification_context(),
        "aggregate",
        None,
        "run-1",
    )

    assert result.resolution.kind == "accept_workflow"
    assert result.resolution.selected_action == "run_panda"
    assert result.resolution.selected_granularity == "aggregate"
    model.invoke.assert_called_once()


def test_model_acceptance_is_downgraded_without_concrete_continuation():
    model = Mock()
    model.invoke.return_value = _decision("accept_workflow")
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(_context(), "sounds good", None, "run-1")

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None


def test_substantive_follow_up_becomes_bounded_self_contained_task():
    model = Mock()
    model.invoke.return_value = _decision("follow_up")
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _context(), "What format should the motif prior use?", None, "run-1"
    )

    assert result.resolution.kind == "follow_up"
    assert result.resolution.resolved_task == (
        "Previous NetZoo goal: Which tools produce sample-specific miRNA networks?\n"
        "User follow-up: What format should the motif prior use?"
    )


def test_context_wrapper_does_not_invent_a_current_documentation_request():
    model = Mock()
    model.invoke.return_value = _decision("follow_up")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "What format should the motif prior use?", None, "run-1"
    )

    assert is_versioned_documentation_request(result.resolution.resolved_task) is False


def test_reply_prompt_treats_questions_about_trusted_workflow_facts_as_follow_ups():
    context = _context()
    context.candidate_workflows = [
        WorkflowConversationFact(
            action="run_puma",
            workflow="PUMA",
            required_inputs=["expression_file", "motif_file", "ppi_file"],
            granularities=["aggregate"],
        )
    ]

    messages = build_reply_resolution_messages(
        context,
        "What format should that prior input use?",
    )
    rendered = "\n".join(message.content for message in messages)

    assert '"workflow":"PUMA"' in rendered
    assert '"motif_file"' in rendered
    normalized = " ".join(rendered.split())
    assert "input, output, local resource, or workflow in trusted context" in normalized
    assert "does not need to restate the prior goal" in normalized

    model = Mock()
    model.invoke.return_value = _decision("follow_up")
    resolved = ContextualReplyResolver.for_test(model).resolve(
        context, "What format should that prior input use?", None, "run-1"
    )
    assert "Registered workflow context: PUMA" in resolved.resolution.resolved_task


def test_low_confidence_resolution_fails_safe():
    model = Mock()
    model.invoke.return_value = _decision("new_goal", confidence=0.60)

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "do something", None, "run-1"
    )

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None


def test_new_goal_preserves_original_user_text():
    model = Mock()
    model.invoke.return_value = _decision("new_goal")
    reply = "Inspect data/expression.tsv"

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), reply, None, "run-1"
    )

    assert result.resolution.kind == "new_goal"
    assert result.resolution.resolved_task == reply
    assert result.usage.calls[-1].role == "follow_up"
    assert result.usage.calls[-1].status == "success"


def test_navigation_does_not_create_a_scientific_task():
    model = Mock()
    model.invoke.return_value = _decision("navigation")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "take me back", None, "run-1"
    )

    assert result.resolution.kind == "navigation"
    assert result.resolution.resolved_task is None


def test_explicit_path_for_offered_input_bypasses_model():
    model = Mock()
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _context(
            continuation_action="run_lioness_puma",
            expected_field="expression_file",
        ),
        "data/patient/expression.tsv",
        None,
        "run-1",
    )

    assert result.resolution.kind == "accept_workflow"
    assert result.resolution.resolved_task == "data/patient/expression.tsv"
    model.invoke.assert_not_called()


def test_model_failure_fails_safe_and_records_failed_usage():
    model = Mock()
    model.invoke.side_effect = RuntimeError("provider unavailable")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "certainly", None, "run-1"
    )

    assert result.resolution.kind == "needs_detail"
    assert result.usage.calls[-1].role == "follow_up"
    assert result.usage.calls[-1].status == "failed"


def _context_without_candidates():
    """The turn a routing failure produces: a question, but nothing to pick."""
    return FollowUpContext(
        prior_user_goal="Run PANDA on three local files for human.",
        prompt_kind="clarification",
        prompt_question=(
            "Specify the requested result type and whether it should be "
            "aggregate or sample-specific."
        ),
        candidate_actions=[],
        continuation_action=None,
        alternative_action=None,
    )


def test_an_answer_is_revalidated_when_the_turn_carries_no_candidate():
    """Asking which result, then refusing the answer, is not a safe default."""
    model = Mock()
    model.invoke.return_value = _decision("accept_workflow", selected_action="run_panda")
    reply = "PANDA 的 aggregate TF-gene 調控網路"

    result = ContextualReplyResolver.for_test(model).resolve(
        _context_without_candidates(), reply, None, "run-1"
    )

    assert result.resolution.kind == "follow_up"
    assert result.resolution.selected_action is None
    assert reply in result.resolution.resolved_task
    assert "Run PANDA on three local files" in result.resolution.resolved_task


def test_revalidation_authorizes_nothing_by_itself():
    model = Mock()
    model.invoke.return_value = _decision("accept_workflow", selected_action="run_sambar")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context_without_candidates(), "run sambar", None, "run-1"
    )

    # The named action is carried as text for routing to judge, never as a
    # selection this turn made.
    assert result.resolution.selected_action is None
    assert result.resolution.kind == "follow_up"


def test_an_action_outside_a_populated_trusted_set_is_still_refused():
    """The empty-set allowance must not become a way around the trusted set."""
    model = Mock()
    model.invoke.return_value = _decision("accept_workflow", selected_action="run_sambar")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "run sambar instead", None, "run-1"
    )

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None
