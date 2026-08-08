from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.progress_summaries import render_progress_summary  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402


def test_no_tool_summary_explains_source_and_safety():
    summary = render_progress_summary(
        "concept", {"source": "registered workflow specification"}
    )

    assert summary is not None
    assert "do not need to inspect files or run tools" in summary
    assert "registered workflow specification" in summary


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
