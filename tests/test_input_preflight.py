from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.cli.slash_commands import handle_slash_command  # noqa: E402
from netzoo_agent_core.contracts import PlanEvaluationResult  # noqa: E402


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _panda_decision() -> TaskDecision:
    return TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
    )


def _valid_panda_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    expression = _write(
        tmp_path / "expression.tsv",
        "gene\ts1\ts2\nG1\t1\t2\nG2\t2\t1\n",
    )
    motif = _write(tmp_path / "motif.tsv", "TF1\tG1\t1\nTF2\tG2\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")
    return expression, motif, ppi


def test_correct_filenames_are_still_rejected_when_content_is_invalid(tmp_path):
    expression, motif, ppi = _valid_panda_files(tmp_path)
    motif.write_text("not an edge list\n", encoding="utf-8")

    plan = build_workflow_plan(
        _panda_decision(),
        f"Run PANDA using {expression}, {motif}, and {ppi}.",
    )

    assert plan.status == "needs_input"
    assert "preflight failed" in (plan.question or "")
    assert "motif" in (plan.question or "").casefold()


def test_valid_explicit_inputs_pass_preflight_and_execute_rechecks_contents(tmp_path):
    expression, motif, ppi = _valid_panda_files(tmp_path)
    plan = build_workflow_plan(
        _panda_decision(),
        (
            "Run PANDA with "
            f"expression_file={expression} motif_file={motif} ppi_file={ppi}"
        ),
    )

    assert plan.status == "ready"
    assert plan.steps

    motif.write_text("broken\n", encoding="utf-8")
    result = handle_slash_command(
        "/execute",
        current_plan=plan,
        current_plan_evaluation=PlanEvaluationResult(
            status="approved", score=100, summary="approved"
        ),
    )

    assert result.execute_once is False
    assert "final input validation failed" in result.message
    assert "motif" in result.message.casefold()
