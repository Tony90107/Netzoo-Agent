from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.reply_resolution import (  # noqa: E402
    ContextualReplyResolver,
)
from netzoo_agent_core.contracts import (  # noqa: E402
    FollowUpContext,
    ReplyIntentDecision,
)


def _context(*, continuation_action=None):
    return FollowUpContext(
        prior_user_goal="Which tools produce sample-specific miRNA networks?",
        prompt_kind="completed",
        prompt_question="Enter a follow-up question or describe another NetZoo goal.",
        candidate_actions=["run_puma", "run_lioness_puma"],
        continuation_action=continuation_action,
        expected_field=None,
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
        "Current follow-up: What format should the motif prior use?"
    )


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


def test_navigation_does_not_create_a_scientific_task():
    model = Mock()
    model.invoke.return_value = _decision("navigation")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "take me back", None, "run-1"
    )

    assert result.resolution.kind == "navigation"
    assert result.resolution.resolved_task is None


def test_model_failure_fails_safe_and_records_failed_usage():
    model = Mock()
    model.invoke.side_effect = RuntimeError("provider unavailable")

    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "certainly", None, "run-1"
    )

    assert result.resolution.kind == "needs_detail"
    assert result.usage.calls[-1].role == "follow_up"
    assert result.usage.calls[-1].status == "failed"
