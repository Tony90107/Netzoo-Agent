from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.reply_resolution import (  # noqa: E402
    ContextualReplyResolver,
    build_reply_resolution_messages,
)
from netzoo_agent_core.contracts import (  # noqa: E402
    FollowUpContext,
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


def _decision(kind: str, *, confidence: float = 0.98) -> ReplyIntentDecision:
    return ReplyIntentDecision(
        kind=kind,
        confidence=confidence,
        reason="Test classification.",
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


def test_model_acceptance_is_downgraded_without_concrete_continuation():
    model = Mock()
    model.invoke.return_value = _decision("accept_workflow")
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(_context(), "sounds good", None, "run-1")

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None


def test_substantive_follow_up_preserves_text_and_typed_context():
    model = Mock()
    model.invoke.return_value = _decision("follow_up")
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _context(), "What format should the motif prior use?", None, "run-1"
    )

    assert result.resolution.kind == "follow_up"
    assert result.resolution.resolved_task == "What format should the motif prior use?"
    assert result.resolution.interaction_context == _context()


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
    assert "entity, input, output, or workflow in trusted context" in normalized
    assert "does not need to restate the prior goal" in normalized

    model = Mock()
    model.invoke.return_value = _decision("follow_up")
    resolved = ContextualReplyResolver.for_test(model).resolve(
        context, "What format should that prior input use?", None, "run-1"
    )
    assert resolved.resolution.resolved_task == "What format should that prior input use?"
    assert resolved.resolution.interaction_context.candidate_workflows[0].workflow == "PUMA"


def test_resource_availability_question_is_a_substantive_follow_up():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="follow_up",
        confidence=0.91,
        reason="Requests local resource discovery.",
    )
    reply = "Could you check whether this workspace already has compatible inputs?"

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), reply, None, "run-1"
    )

    assert result.resolution.resolved_task == reply
    assert result.resolution.interaction_context.candidate_actions
    prompt = " ".join(
        str(message.content) for message in model.invoke.call_args.args[0]
    )
    for semantic_category in (
        "availability",
        "inventory",
        "local resources",
        "example datasets",
        "reusing existing data",
        "suitable",
    ):
        assert semantic_category in prompt


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
