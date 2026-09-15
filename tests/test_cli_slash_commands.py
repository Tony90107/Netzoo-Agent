from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.slash_commands import (  # noqa: E402
    current_mode_label,
    handle_slash_command,
    render_mode_prompt,
)
from netzoo_agent_core.data.gene_validation import (  # noqa: E402
    GeneCache,
    GeneRecord,
)
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    PlanEvaluationResult,
    TaskDecision,
    WorkflowPlan,
    WorkflowStep,
)


@pytest.fixture(autouse=True)
def seeded_gene_authority(monkeypatch, tmp_path):
    """Seed the genes used by data/auto-check-valid into an isolated cache.

    These tests are about the /execute gate, not about gene resolution, but the
    gate deliberately re-runs full input validation. Without seeded records the
    axes come back unverified and the gate blocks for the wrong reason.
    """
    cache_path = tmp_path / "gene.sqlite3"
    GeneCache(cache_path).upsert(
        [
            GeneRecord(
                identifier=identifier,
                normalized_identifier=identifier.casefold(),
                namespace=namespace,
                canonical_id=canonical_id,
                symbol=identifier,
                taxon="",
                status="valid",
                authority="NCBI Gene",
                source="test",
            )
            for identifier, namespace, canonical_id in (
                ("ENSG00000141510", "ensembl_gene", "ensembl_gene:ENSG00000141510"),
                ("ENSG00000012048", "ensembl_gene", "ensembl_gene:ENSG00000012048"),
                ("ENSG00000146648", "ensembl_gene", "ensembl_gene:ENSG00000146648"),
                ("MYC", "symbol_like", "ncbi_gene:4609"),
                ("SOX2", "symbol_like", "ncbi_gene:6657"),
            )
        ]
    )
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))


@pytest.fixture(autouse=True)
def restore_execution_mode():
    previous = settings.EXECUTE_TOOLS
    previous_test_mode = settings.TEST_DATA_MODE
    configure_runtime(EXECUTE_TOOLS=False, TEST_DATA_MODE=False)
    yield
    configure_runtime(EXECUTE_TOOLS=previous, TEST_DATA_MODE=previous_test_mode)


def test_natural_language_and_absolute_paths_are_not_slash_commands():
    for user_input in (
        "run PANDA",
        "/work/data/expression.tsv",
        "/expression.tsv",
        "expression_file=/data/expression.tsv",
    ):
        result = handle_slash_command(user_input)
        assert result.handled is False
        assert result.message == ""


def test_single_component_absolute_paths_are_answers_in_path_context():
    for user_input in ("/tmp", "/output"):
        result = handle_slash_command(user_input, allow_path_answer=True)
        assert result.handled is False
        assert result.message == ""


def test_known_commands_remain_commands_in_path_context():
    result = handle_slash_command("/status", allow_path_answer=True)

    assert result.handled is True
    assert result.message == "Current mode: Planning"


def test_execute_is_one_shot_and_leaves_planning_mode_enabled():
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"

    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
        expression_file="data/auto-check-valid/expression.tsv",
        motif_file="data/auto-check-valid/motif.tsv",
        ppi_file="data/auto-check-valid/ppi.tsv",
        output_file="outputs/panda.tsv",
    )
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="Run PANDA.",
        decision=decision.model_dump(),
        steps=[WorkflowStep(action="run_panda", purpose="Execute PANDA.")],
        status="ready",
    )
    evaluation = PlanEvaluationResult(status="approved", score=100, summary="Pass")
    execute = handle_slash_command(
        "/execute",
        execution_ready=True,
        current_plan=plan,
        current_plan_evaluation=evaluation,
    )
    assert execute.handled is True
    assert execute.execute_once is True
    assert "once" in execute.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"

    planning = handle_slash_command("/PLANNING")
    assert planning.handled is True
    assert "Planning mode enabled" in planning.message
    assert settings.EXECUTE_TOOLS is False
    assert current_mode_label() == "Planning"
    assert render_mode_prompt("Question") == "Question"


def test_execute_checks_the_current_plan_and_evaluation():
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
        expression_file="data/auto-check-valid/expression.tsv",
        motif_file="data/auto-check-valid/motif.tsv",
        ppi_file="data/auto-check-valid/ppi.tsv",
        output_file="outputs/panda.tsv",
    )
    plan = WorkflowPlan(
        workflow="PANDA",
        objective="Run PANDA.",
        decision=decision.model_dump(),
        steps=[WorkflowStep(action="run_panda", purpose="Execute PANDA.")],
        status="ready",
    )
    evaluation = PlanEvaluationResult(status="approved", score=100, summary="Pass")

    result = handle_slash_command(
        "/execute",
        current_plan=plan,
        current_plan_evaluation=evaluation,
    )

    assert result.execute_once is True
    assert settings.EXECUTE_TOOLS is False

    not_ready = plan.model_copy(update={"status": "needs_confirmation"})
    blocked = handle_slash_command(
        "/execute",
        current_plan=not_ready,
        current_plan_evaluation=evaluation,
    )
    assert blocked.execute_once is False
    assert "not ready" in blocked.message


def test_execute_is_blocked_until_a_ready_plan_is_available():
    result = handle_slash_command("/execute")

    assert result.handled is True
    assert "no current Work Plan" in result.message
    assert settings.EXECUTE_TOOLS is False


def test_status_and_help_report_without_changing_mode():
    status = handle_slash_command("/status")
    assert status == type(status)(handled=True, message="Current mode: Planning")

    help_result = handle_slash_command("/help")
    assert help_result.handled is True
    assert "Press / at an empty prompt, then Enter, to use /execute." in help_result.message
    assert "Type after / to enter another slash command." in help_result.message
    for command in ("/test", "/planning", "/execute", "/status", "/help"):
        assert command in help_result.message
    assert "test-only" in help_result.message
    assert "interrupt" not in help_result.message.casefold()
    assert settings.EXECUTE_TOOLS is False


def test_test_enables_synthetic_mode_and_planning_disables_it():
    configure_runtime(EXECUTE_TOOLS=True)

    result = handle_slash_command("/test")

    assert result.handled is True
    assert result.execute_once is False
    assert "Synthetic Test mode enabled" in result.message
    assert "test-only identifiers" in result.message
    assert settings.EXECUTE_TOOLS is False
    assert settings.TEST_DATA_MODE is True
    assert current_mode_label() == "Test"
    assert render_mode_prompt("Question") == "[Test] Question"

    planning = handle_slash_command("/planning")
    assert planning.handled is True
    assert settings.TEST_DATA_MODE is False
    assert current_mode_label() == "Planning"


def test_unknown_command_and_trailing_arguments_are_consumed_locally():
    unknown = handle_slash_command("/exec")
    assert unknown.handled is True
    assert "Unknown slash command: /exec" in unknown.message
    assert "/help" in unknown.message

    arguments = handle_slash_command("/execute run PANDA")
    assert arguments.handled is True
    assert "Enter /execute by itself" in arguments.message
    assert settings.EXECUTE_TOOLS is False
