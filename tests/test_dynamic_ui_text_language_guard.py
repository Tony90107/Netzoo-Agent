"""Log 192: dynamic UI text quoting user paths may carry non-English names.

Log 180 fixed the two advisory renderers. The same crash class remained where
text assembled elsewhere, with a user's folder or file names in it, was handed
to `_ui_text` whole: the clarification wizard's discovered-bundle question, the
failed-validation follow-up, and the `--timeline` input and evaluation blocks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, ToolExecutionResult, WorkflowPlan  # noqa: E402
from netzoo_agent_core.presentation import _render_timeline_block, _ui_text_quoting  # noqa: E402


def test_quoted_values_may_be_non_english_and_nothing_else_escapes():
    assert _ui_text_quoting("Found `data/研究/` here.", ["data/研究/"]) == "Found `data/研究/` here."
    with pytest.raises(ValueError, match="must be English"):
        _ui_text_quoting("找到 `data/研究/`.", ["data/研究/"])
    with pytest.raises(ValueError, match="must be English"):
        _ui_text_quoting("Found 研究.", ["data/other/"])


def test_the_discovered_bundle_question_quotes_a_non_english_folder(tmp_path):
    study = tmp_path / "data" / "研究"
    study.mkdir(parents=True)
    (study / "expression.tsv").write_text("GeneA\t1\t2\t3\nGeneB\t3\t2\t1\n", encoding="utf-8")
    (study / "prior-puma.tsv").write_text("TF1\tGeneA\t1\nTF2\tGeneB\t1\nmiR-1\tGeneA\t1\n", encoding="utf-8")
    (study / "ppi.tsv").write_text("TF1\tTF2\t1\nTF2\tTF1\t1\n", encoding="utf-8")
    decision = TaskDecision(
        action="run_lioness_puma", in_scope=True, should_execute=True, intent_type="run_analysis",
        confidence=1.0, reason="Use locally available inputs.",
        recommended_actions=["run_puma", "run_lioness_puma"],
    )
    with patch.object(agent.settings, "TEST_DATA_MODE", True), patch(
        "netzoo_agent_core.planning.evidence.PROJECT_ROOT", tmp_path,
    ):
        plan = agent.build_workflow_plan(decision, "Continue the trusted workflow using available local data.")

    assert plan.status == "needs_input" and "研究" in plan.question
    rendered = agent.clarification_prompt(plan)

    assert "I found this partial input bundle" in rendered
    assert "研究" in rendered


def test_a_failed_validation_follow_up_quotes_the_error_verbatim():
    decision = TaskDecision(
        action="run_panda", in_scope=True, should_execute=True, intent_type="run_analysis",
        confidence=1.0, reason="run",
    )
    plan = WorkflowPlan(workflow="PANDA", objective="run", decision=decision.model_dump(), status="ready")
    failure = ToolExecutionResult(
        action="inspect_panda_inputs", status="failed", summary="Input validation failed.",
        errors=["expression_file file does not exist: data/研究/表現.tsv"],
    )

    prompt = build_next_turn_prompt({
        "plan": plan.model_dump(), "tool_results": [failure.model_dump()],
        "evaluation": {"status": "failed", "reason": "input validation failed"},
    })

    assert prompt.kind == "failed"
    assert "data/研究/表現.tsv" in prompt.question


def test_timeline_input_and_evaluation_blocks_quote_paths_as_data():
    block = _render_timeline_block(
        "input", "The Planner requires additional input", "I found this partial input bundle: data/研究/",
    )
    assert block.startswith("[Input required]") and "data/研究/" in block

    block = _render_timeline_block("evaluate", "Evaluator: failed", "Missing output: outputs/輸出/S1.tsv")
    assert block.startswith("[Evaluating result]") and "outputs/輸出/S1.tsv" in block
