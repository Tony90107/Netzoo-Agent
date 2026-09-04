from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.planning as planning  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    InputEvidence,
    TaskDecision,
    WorkflowPlan,
)


def _plan_digest(plan) -> str:
    payload = json.dumps(
        plan.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = payload.replace(str(SCRIPTS_DIR.parent), "<PROJECT_ROOT>")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


PLANNING_CASES = (
    (
        "respond_only",
        TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            confidence=0.99,
            reason="Explain PANDA.",
        ),
        "Explain PANDA.",
        "0d1c1314b2aed2406558f886e1d9bbdb24c08cc4ac80978a9ca79a2c9fe3f703",
    ),
    (
        "retrieval",
        TaskDecision(
            action="web_search",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Find current PANDA references.",
            web_query="current PANDA references",
        ),
        "Search the web for current PANDA references.",
        "7b23d409d688efb1da37faf47d9f58058328f0bc7fcee0d1d332350be0e6494f",
    ),
    (
        "explicit_panda",
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=0.99,
            reason="Run supplied PANDA inputs.",
        ),
        (
            "Run PANDA with expression_file=data/study/expression.tsv "
            "motif_file=data/study/motif.tsv ppi_file=data/study/ppi.tsv "
            "output_file=outputs/study/panda.tsv"
        ),
        "2512eb74ffc976bb3a0ccad47cc7cfa3dbbe56d7bc732345ce6e7e600f9cb181",
    ),
)


def test_ordinary_evidence_serialization_omits_empty_derived_source():
    evidence = InputEvidence(
        field="expression_file",
        status="missing",
        reason="Expression input is required.",
    )

    payload = evidence.model_dump()

    assert "derived_from" not in payload
    assert payload["value"] is None
    assert payload["bundle_id"] is None


def test_derived_evidence_serialization_retains_exact_source():
    evidence = InputEvidence(
        field="expression_file",
        status="derived",
        value="outputs/expression.puma-expression.tsv",
        reason="Created by bounded header-removal recovery.",
        derived_from="inputs/expression.tsv",
    )

    payload = evidence.model_dump()

    assert payload["derived_from"] == "inputs/expression.tsv"


def test_nested_evidence_serialization_conditionally_includes_derived_source():
    plan = WorkflowPlan(
        workflow="PUMA",
        objective="serialize recovery provenance",
        decision={},
        evidence=[
            InputEvidence(
                field="motif_file",
                status="provided",
                value="inputs/motif.tsv",
                reason="Provided by the user.",
            ),
            InputEvidence(
                field="expression_file",
                status="derived",
                value="outputs/expression.puma-expression.tsv",
                reason="Created by bounded header-removal recovery.",
                derived_from="inputs/expression.tsv",
            ),
        ],
        status="ready",
    )

    payload = plan.model_dump()

    assert "derived_from" not in payload["evidence"][0]
    assert payload["evidence"][1]["derived_from"] == "inputs/expression.tsv"
    assert payload["question"] is None


@pytest.mark.parametrize(("case_name", "decision", "task", "expected"), PLANNING_CASES)
def test_planning_model_dump_is_characterized(case_name, decision, task, expected):
    before = decision.model_dump(mode="json")
    plan = planning.build_workflow_plan(decision, task)

    assert _plan_digest(plan) == expected, case_name
    assert decision.model_dump(mode="json") == before


PUBLIC_EXPORTS = ["build_workflow_plan", "render_plan"]


def test_planning_is_responsibility_oriented_package():
    assert hasattr(planning, "__path__")
    for module_name in ("builder", "rendering"):
        importlib.import_module(f"netzoo_agent_core.planning.{module_name}")


def test_planning_public_surface_is_preserved():
    assert planning.__all__ == PUBLIC_EXPORTS
    for name in PUBLIC_EXPORTS:
        assert getattr(legacy_agent, name) is getattr(planning, name)


def test_context_stage_returns_early_response_plan():
    context_module = importlib.import_module("netzoo_agent_core.planning.context")
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=0.99,
        reason="Explain PANDA.",
    )

    result = context_module._prepare_planning_context(
        decision,
        "Explain PANDA.",
        None,
        None,
        None,
    )

    assert result.status == "respond_only"
    assert decision.action == "no_tool"


def test_context_stage_prepares_local_workflow_state():
    context_module = importlib.import_module("netzoo_agent_core.planning.context")
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=0.99,
        reason="Run PANDA.",
    )

    result = context_module._prepare_planning_context(
        decision,
        "Run PANDA.",
        None,
        None,
        None,
    )

    assert isinstance(result, context_module._PlanningContext)
    assert result.action == "run_panda"
    assert result.workflow == "PANDA"
    assert result.required == [
        "expression_file",
        "motif_file",
        "ppi_file",
        "output_file",
    ]


def test_evidence_stage_is_importable_and_internal():
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    assert evidence_module.__all__ == []
    assert not hasattr(planning, "_build_evidence_ledger")


def test_legacy_candidate_patch_reaches_evidence_child():
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    original = legacy_agent._find_candidate_files
    calls = []

    def replacement(keywords, root):
        calls.append((keywords, root))
        return []

    try:
        legacy_agent._find_candidate_files = replacement
        assert evidence_module._find_candidate_files is replacement
        plan = legacy_agent.build_workflow_plan(
            TaskDecision(
                action="run_condor",
                in_scope=True,
                should_execute=True,
                confidence=0.99,
                reason="Run CONDOR.",
            ),
            "Run CONDOR with research data.",
        )
        assert plan.status == "needs_input"
        assert calls
    finally:
        legacy_agent._find_candidate_files = original


def test_project_root_override_reaches_evidence_child(tmp_path):
    evidence_module = importlib.import_module("netzoo_agent_core.planning.evidence")
    original = legacy_agent.PROJECT_ROOT
    try:
        legacy_agent.PROJECT_ROOT = tmp_path
        assert evidence_module.PROJECT_ROOT == tmp_path
    finally:
        legacy_agent.PROJECT_ROOT = original


def test_assembly_stage_is_importable_and_internal():
    assembly_module = importlib.import_module("netzoo_agent_core.planning.assembly")
    assert assembly_module.__all__ == []
    assert not hasattr(planning, "_assemble_workflow_plan")


def test_builder_is_a_small_pipeline_orchestrator():
    builder_module = importlib.import_module("netzoo_agent_core.planning.builder")
    source = inspect.getsource(builder_module)

    assert len(source.splitlines()) <= 80
    assert "_prepare_planning_context" in source
    assert "_build_evidence_ledger" in source
    assert "_assemble_workflow_plan" in source
    assert "discover_coherent_bundle" not in source
    assert "_find_candidate_files" not in source


def test_internal_planning_helpers_do_not_leak_from_facade():
    for name in (
        "_PlanningContext",
        "_prepare_planning_context",
        "_build_evidence_ledger",
        "_assemble_workflow_plan",
    ):
        assert not hasattr(planning, name)
