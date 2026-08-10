from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.progress_summaries import render_progress_summary  # noqa: E402
from netzoo_agent_core.cli.follow_up import (  # noqa: E402
    build_next_turn_prompt,
    resolve_next_turn_input,
)
from netzoo_agent_core.contracts import (  # noqa: E402
    RequestedOutcome,
    TaskDecision,
    WorkflowPlan,
)


def test_no_tool_summary_explains_source_and_safety():
    summary = render_progress_summary(
        "concept", {"source": "registered workflow specification"}
    )

    assert summary is not None
    assert "do not need to inspect files or run tools" in summary
    assert "registered workflow specification" in summary


def test_next_step_summary_explains_stable_guidance_without_tools():
    summary = render_progress_summary(
        "next_step", {"action": "no_tool", "in_scope": "true", "should_execute": "false"}
    )

    assert summary is not None
    assert "registered workflow information" in summary
    assert "without running an analysis" in summary


def test_next_step_summary_explains_analysis_preparation():
    summary = render_progress_summary(
        "next_step", {"action": "run_panda", "in_scope": "true", "should_execute": "true"}
    )

    assert summary is not None
    assert "prepare the matching registered workflow" in summary


def test_multiple_semantic_candidates_do_not_select_one_workflow():
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False,
        intent_type="answer_question", confidence=1.0, reason="guidance",
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL", objective="guidance", decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({
        "plan": plan.model_dump(),
        "semantic_goal": {
            "candidates": ["run_lioness_panda", "run_lioness_puma"],
            "relationship": "alternatives",
        },
    })

    assert prompt.continuation_action is None
    assert prompt.question == "Reply with the clarification above, or describe another NetZoo goal."


def test_workflow_composition_recommends_its_final_registered_action():
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False,
        intent_type="answer_question", confidence=1.0, reason="guidance",
        recommended_actions=["run_puma", "run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL", objective="guidance", decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({
        "plan": plan.model_dump(),
        "semantic_goal": {
            "candidates": ["run_puma", "run_lioness_puma"],
            "relationship": "composition",
        },
    })

    assert prompt.continuation_action == "run_lioness_puma"
    assert "recommended LIONESS-PUMA workflow" in prompt.question


def test_unsupported_outcome_offers_alternative_without_execution_continuation():
    outcome = RequestedOutcome(
        operation="acquire",
        artifact_type="measurement_dataset",
        entity_types=["mirna"],
        display_entities=["miRNA"],
        regulator_types=[],
        target_types=[],
        granularity="sample_specific",
        unresolved_dimensions=[],
    )
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="unsupported",
        requested_outcome=outcome,
        capability_match_status="unsupported",
        alternative_actions=["run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="unsupported",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.kind == "alternative_outcome"
    assert prompt.continuation_action is None
    assert prompt.alternative_action == "run_lioness_puma"
    continuation = resolve_next_turn_input(prompt, "yes")
    assert continuation.startswith("CONFIRMED_OUTCOME_ACTION=run_lioness_puma")
    assert "CONFIRMED_GRANULARITY=sample_specific" in continuation
    assert "PREVIOUS_ACTION" not in continuation


def test_ambiguous_outcome_asks_for_clarification_without_continuation():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="ambiguous",
        capability_match_status="ambiguous",
        clarification_question="Which result do you want?",
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="ambiguous",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.kind == "clarify_outcome"
    assert prompt.continuation_action is None
