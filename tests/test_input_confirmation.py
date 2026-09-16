from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.cli.clarification import (  # noqa: E402
    input_confirmation_continuation,
)
from netzoo_agent_core.cli.follow_up import (  # noqa: E402
    build_next_turn_prompt,
    render_next_turn_prompt,
)
from netzoo_agent_core.interpretation import hydrate_router_decision  # noqa: E402
from workflow_registry import executor_arguments  # noqa: E402


def _panda_decision() -> TaskDecision:
    return TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
    )


def test_filename_paths_are_checked_then_require_confirmation():
    task = (
        "Run PANDA using data/official-toy/ToyExpressionData.txt, "
        "data/official-toy/ToyMotifData.txt, and "
        "data/official-toy/ToyPPIData.txt"
    )
    plan = build_workflow_plan(_panda_decision(), task)

    assert plan.status == "needs_confirmation"
    assert {
        item.field
        for item in plan.evidence
        if item.reason.startswith("Role inferred from the filename")
    } == {"expression_file", "motif_file", "ppi_file"}
    assert plan.steps == []
    assert all(
        item.status == "discovered"
        for item in plan.evidence
        if item.field in {"expression_file", "motif_file", "ppi_file"}
    )


def test_rejected_input_confirmation_accepts_corrected_role_paths():
    task = (
        "Run PANDA using data/official-toy/ToyExpressionData.txt, "
        "data/official-toy/ToyMotifData.txt, and "
        "data/official-toy/ToyPPIData.txt"
    )
    plan = build_workflow_plan(_panda_decision(), task)

    continuation = input_confirmation_continuation(
        plan,
        "expression_file=local/expression.tsv motif_file=local/prior.tsv",
        approved=False,
    )
    replanned = build_workflow_plan(_panda_decision(), continuation)

    assert replanned.status == "needs_input"
    assert replanned.decision["expression_file"] == "local/expression.tsv"
    assert replanned.decision["motif_file"] == "local/prior.tsv"
    assert "ppi_file" in replanned.missing_inputs


def test_accepted_input_confirmation_preserves_output_and_taxon():
    task = (
        "Run PANDA using data/official-toy/ToyExpressionData.txt, "
        "data/official-toy/ToyMotifData.txt, and "
        "data/official-toy/ToyPPIData.txt; species is human; "
        "output_file=outputs/gene_existence_a.tsv"
    )
    decision = _panda_decision().model_copy(
        update={
            "taxon": "human",
            "output_file": "outputs/gene_existence_a.tsv",
        }
    )
    plan = build_workflow_plan(decision, task)

    continuation = input_confirmation_continuation(plan, "y", approved=True)
    hydrated = hydrate_router_decision(_panda_decision(), continuation)
    replanned = build_workflow_plan(hydrated, continuation)

    assert replanned.decision["taxon"] == "human"
    assert replanned.decision["output_file"] == "outputs/gene_existence_a.tsv"


def test_optional_coexpression_argument_is_normalized_for_strict_tools():
    decision = _panda_decision().model_copy(
        update={
            "expression_file": "expression.tsv",
            "motif_file": "motif.tsv",
            "ppi_file": "ppi.tsv",
            "output_file": "out.tsv",
        }
    )
    arguments = executor_arguments("run_panda", decision)

    assert arguments["coexpression_file"] == ""


def test_input_confirmation_and_ready_prompts_keep_input_on_a_new_line():
    plan = build_workflow_plan(
        _panda_decision(),
        (
            "Run PANDA using data/official-toy/ToyExpressionData.txt, "
            "data/official-toy/ToyMotifData.txt, and "
            "data/official-toy/ToyPPIData.txt"
        ),
    )
    assert plan.status == "needs_confirmation"
    confirmed = plan
    state = {
        "plan": confirmed.model_dump(),
        "decision": confirmed.decision,
        "tool_results": [
            {
                "action": "run_panda",
                "status": "dry_run",
                "summary": "preview",
                "raw_output": "Dry run only.",
            }
        ],
        "evaluation": {"status": "completed", "reason": "preview"},
    }
    prompt = render_next_turn_prompt(build_next_turn_prompt(state))
    assert "validated workflow.\nOr describe" in prompt
