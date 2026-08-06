from __future__ import annotations

import importlib
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.evaluation as evaluation  # noqa: E402


HISTORICAL_EXPORTS = [
    "_path_literal_in_task",
    "_evidence_contract_failures",
    "_path_hygiene_failures",
    "_expected_plan_steps",
    "evaluate_workflow_plan",
    "render_plan_evaluation",
    "render_plan_rejection_response",
    "render_verbose_execution_response",
    "_compact_field_label",
    "_extract_command_preview",
    "_compact_validation_highlights",
    "render_compact_execution_response",
    "render_execution_response",
    "render_needs_input_response",
    "render_preference_confirmation_response",
    "evaluate_step_result",
    "recover_workflow_plan",
]


def test_evaluation_is_responsibility_oriented_package():
    assert hasattr(evaluation, "__path__")
    for module_name in (
        "plan_rules",
        "plan_review",
        "step_results",
        "recovery",
        "rendering",
    ):
        importlib.import_module(f"netzoo_agent_core.evaluation.{module_name}")


def test_historical_evaluation_surface_is_preserved():
    assert evaluation.__all__ == HISTORICAL_EXPORTS
    for name in HISTORICAL_EXPORTS:
        assert hasattr(evaluation, name), name


def test_legacy_facade_uses_package_exports():
    for name in HISTORICAL_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(evaluation, name)


def test_runtime_overrides_reach_evaluation_child_modules():
    step_results = importlib.import_module(
        "netzoo_agent_core.evaluation.step_results"
    )
    rendering = importlib.import_module("netzoo_agent_core.evaluation.rendering")
    original_execute = legacy_agent.EXECUTE_TOOLS
    original_verbose = legacy_agent.VERBOSE_OUTPUT
    try:
        legacy_agent.EXECUTE_TOOLS = not original_execute
        legacy_agent.VERBOSE_OUTPUT = not original_verbose
        assert step_results.EXECUTE_TOOLS is (not original_execute)
        assert rendering.VERBOSE_OUTPUT is (not original_verbose)
    finally:
        legacy_agent.EXECUTE_TOOLS = original_execute
        legacy_agent.VERBOSE_OUTPUT = original_verbose


def test_compact_response_labels_derived_input():
    decision = legacy_agent.TaskDecision(
        action="run_puma",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="recovered PUMA",
        expression_file="outputs/expression.puma-expression.tsv",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="PUMA",
        objective=decision.reason,
        decision=decision.model_dump(),
        evidence=[
            legacy_agent.InputEvidence(
                field="expression_file",
                status="derived",
                value="outputs/expression.puma-expression.tsv",
                reason="Created by bounded header-removal recovery.",
            )
        ],
        steps=[
            legacy_agent.WorkflowStep(
                action="run_puma",
                purpose="Retry PUMA.",
            )
        ],
        status="ready",
    )

    response = evaluation.render_compact_execution_response(
        plan,
        [],
        legacy_agent.EvaluationResult(status="completed", reason="done"),
    )

    assert "[derived input]" in response
