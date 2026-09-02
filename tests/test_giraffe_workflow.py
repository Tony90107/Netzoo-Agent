from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.data.giraffe import (  # noqa: E402
    inspect_giraffe_inputs_impl,
    load_giraffe_inputs,
    validate_giraffe_output,
)
from netzoo_agent_core.execution import run_giraffe  # noqa: E402
from netzoo_agent_core.routing.results import structure_tool_result  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, executor_arguments  # noqa: E402


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene_id\ts1\ts2\ts3\n"
        "g1\t1\t2\t3\n"
        "g2\t3\t2\t1\n",
        encoding="utf-8",
    )
    motif = tmp_path / "motif.tsv"
    motif.write_text(
        "source\ttarget\tweight\n"
        "TF1\tg1\t1\n"
        "TF1\tg2\t0.5\n"
        "TF2\tg1\t0.25\n"
        "TF2\tg2\t1\n",
        encoding="utf-8",
    )
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text(
        "source\ttarget\tweight\n"
        "TF1\tTF2\t0.5\n",
        encoding="utf-8",
    )
    return expression, motif, ppi


def _decision(expression: Path, motif: Path, ppi: Path, output: Path) -> TaskDecision:
    return TaskDecision(
        action="run_giraffe",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run netZooPy GIRAFFE.",
        expression_file=str(expression),
        motif_file=str(motif),
        ppi_file=str(ppi),
        output_file=str(output),
    )


def test_giraffe_input_adapter_validates_and_aligns_source_matrices(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    report, ok = inspect_giraffe_inputs_impl(str(expression), str(motif), str(ppi))
    assert ok, report
    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))
    assert bundle.expression.shape == (2, 3)
    assert bundle.prior.shape == (2, 2)
    assert bundle.ppi.tolist() == [[1.0, 0.5], [0.5, 1.0]]
    assert bundle.gene_ids == ("g1", "g2")
    assert bundle.tf_ids == ("TF1", "TF2")
    assert bundle.sample_ids == ("s1", "s2", "s3")


def test_giraffe_rejects_identifier_and_ppi_contract_mismatches(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    motif.write_text("TF1\tg1\t1\nTF1\tother\t1\n", encoding="utf-8")
    _, ok = inspect_giraffe_inputs_impl(str(expression), str(motif), str(ppi))
    assert not ok

    expression, motif, ppi = _inputs(tmp_path)
    ppi.write_text("source\ttarget\tweight\nTF1\tUNKNOWN\t1\n", encoding="utf-8")
    report, ok = inspect_giraffe_inputs_impl(str(expression), str(motif), str(ppi))
    assert not ok
    assert "PPI" in report
    assert "unknown" in report.casefold()


def test_giraffe_plan_is_ready_only_after_explicit_valid_inputs(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "giraffe.tsv"
    decision = _decision(expression, motif, ppi, output)
    plan = build_workflow_plan(
        decision,
        f"Run GIRAFFE expression_file={expression} motif_file={motif} ppi_file={ppi} output_file={output}",
    )
    assert plan.status == "ready"
    assert [step.action for step in plan.steps] == [
        "inspect_giraffe_inputs",
        "run_giraffe",
    ]

    missing = build_workflow_plan(
        TaskDecision(
            action="run_giraffe",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="Run GIRAFFE.",
        ),
        "Run GIRAFFE.",
    )
    assert missing.status == "needs_input"
    assert {"motif_file", "ppi_file"}.issubset(missing.missing_inputs)


def test_giraffe_dry_run_does_not_import_or_write(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "giraffe.tsv"
    decision = _decision(expression, motif, ppi, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", False), patch(
        "netzoo_agent_core.execution._load_giraffe_api",
        side_effect=AssertionError("dry-run must not import GIRAFFE"),
    ):
        result = run_giraffe.invoke(executor_arguments("run_giraffe", decision))
    assert "Python API preview" in result
    assert "no analysis was executed" in result
    assert not output.exists()


def test_giraffe_execute_uses_verified_api_and_validates_both_outputs(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "giraffe.tsv"

    class FakeGiraffe:
        def __init__(self, expression_array, prior, ppi_array):
            assert expression_array.shape == (2, 3)
            assert prior.shape == (2, 2)
            assert ppi_array.shape == (2, 2)

        def get_regulation(self):
            return np.array([[0.1, 0.2], [0.3, 0.4]])

        def get_tfa(self):
            return np.array([[1.0, 1.1, 1.2], [2.0, 2.1, 2.2]])

    decision = _decision(expression, motif, ppi, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution._load_giraffe_api",
        return_value=(FakeGiraffe, "0.11.0"),
    ):
        raw = run_giraffe.invoke(executor_arguments("run_giraffe", decision))
    assert "API execution completed" in raw
    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))
    assert validate_giraffe_output(str(output), bundle)[0]
    assert "giraffe.tfa.tsv" in raw


def test_giraffe_missing_runtime_is_typed_and_actionable(tmp_path):
    expression, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "giraffe.tsv"
    decision = _decision(expression, motif, ppi, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution._load_giraffe_api",
        side_effect=ModuleNotFoundError("No module named 'netZooPy.giraffe'"),
    ):
        raw = run_giraffe.invoke(executor_arguments("run_giraffe", decision))
    result = structure_tool_result("run_giraffe", decision, raw)
    assert result.status == "failed"
    assert result.error_code == "GIRAFFE_NETZOOPY_MISSING"
    assert "Docker" in raw


def test_giraffe_registry_contract_declares_verified_api_and_no_direct_handoff():
    definition = ACTION_DEFINITIONS["run_giraffe"]
    capability = OUTPUT_CAPABILITIES["run_giraffe"]
    assert definition.required_inputs == (
        "expression_file",
        "motif_file",
        "ppi_file",
        "output_file",
    )
    assert definition.executor_fields == definition.required_inputs
    assert capability.handoff_targets == ()
    assert "netZooPy.giraffe.Giraffe" in definition.memory_metadata["api"]
    assert "not a direct CONDOR" in capability.handoff_contract
