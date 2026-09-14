from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.cli.slash_commands import handle_slash_command  # noqa: E402
from netzoo_agent_core.cli.clarification import (  # noqa: E402
    clarification_prompt,
    input_confirmation_continuation,
)
from netzoo_agent_core.contracts import PlanEvaluationResult  # noqa: E402
from netzoo_agent_core.data.tables import _inspect_panda_inputs_impl  # noqa: E402
from netzoo_agent_core.tool_adapters import inspect_netzoo_inputs  # noqa: E402
from workflow_registry import executor_arguments  # noqa: E402


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


def test_preflight_errors_are_shown_by_interactive_clarification_prompt(tmp_path):
    expression, motif, ppi = _valid_panda_files(tmp_path)
    motif.write_text("not an edge list\n", encoding="utf-8")

    plan = build_workflow_plan(
        _panda_decision(),
        f"Run PANDA using {expression}, {motif}, and {ppi}.",
    )

    prompt = clarification_prompt(plan)

    assert plan.status == "needs_input"
    assert plan.missing_inputs == []
    assert "Input preflight failed" in prompt
    assert "motif" in prompt.casefold()
    assert "Correction >" in prompt
    assert "No additional input is required." not in prompt


def test_preflight_error_accepts_corrected_input_assignments(tmp_path):
    expression, motif, ppi = _valid_panda_files(tmp_path)
    motif.write_text("not an edge list\n", encoding="utf-8")

    plan = build_workflow_plan(
        _panda_decision(),
        f"Run PANDA using {expression}, {motif}, and {ppi}.",
    )

    continuation = input_confirmation_continuation(
        plan,
        f"motif_file={motif}",
        approved=False,
    )

    assert "CORRECTED_INPUT_motif_file=" in continuation


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


def test_expression_header_and_identifier_namespace_are_code_owned_observations(tmp_path):
    expression = _write(
        tmp_path / "expression.tsv",
        "gene_id\ts1\ts2\nENSG00000141510\t1\t2\nENSG00000139618\t2\t1\n",
    )
    motif = _write(
        tmp_path / "motif.tsv",
        "TF1\tENSG00000141510\t1\nTF2\tENSG00000139618\t1\n",
    )
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")

    report, ok, inferred_header = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert ok, report
    assert inferred_header is True
    assert "gene-axis header label observed: 'gene_id'" in report
    assert "gene ID namespace observed: ensembl_gene" in report


def test_sample_axis_header_is_rejected_for_gene_by_sample_expression(tmp_path):
    expression = _write(
        tmp_path / "expression.tsv",
        "sample_id\ts1\ts2\ng1\t1\t2\ng2\t2\t1\n",
    )
    motif = _write(tmp_path / "motif.tsv", "TF1\tg1\t1\nTF2\tg2\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert not ok
    assert "labels a sample axis" in report


def test_cross_file_namespace_mismatch_is_reported_without_online_lookup(tmp_path):
    expression = _write(
        tmp_path / "expression.tsv",
        "gene_id\ts1\ts2\nENSG00000141510\t1\t2\nENSG00000139618\t2\t1\n",
    )
    motif = _write(tmp_path / "motif.tsv", "TF1\tTP53\t1\nTF2\tBRCA2\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert not ok
    assert "identifier namespaces differ" in report


def test_taxon_reaches_inspect_tool_and_executor_payload(tmp_path, monkeypatch):
    expression = _write(
        tmp_path / "expression.tsv",
        "gene_id\ts1\ts2\nQSOX1\t1\t2\n",
    )
    motif = _write(tmp_path / "motif.tsv", "TF1\tQSOX1\t1\nTF2\tQSOX1\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")

    report = inspect_netzoo_inputs.invoke(
        {
            "expression_file": str(expression),
            "motif_file": str(motif),
            "ppi_file": str(ppi),
            "taxon": "Homo sapiens",
        }
    )

    assert "authority validation for taxon 'Homo sapiens'" in report


def test_taxon_is_forwarded_to_panda_executor_arguments():
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run PANDA.",
        expression_file="expression.tsv",
        motif_file="motif.tsv",
        ppi_file="ppi.tsv",
        output_file="output.tsv",
        taxon="Homo sapiens",
    )

    arguments = executor_arguments("run_panda", decision)

    assert arguments["taxon"] == "Homo sapiens"
