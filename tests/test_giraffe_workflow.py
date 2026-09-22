from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core import settings  # noqa: E402
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


def test_giraffe_plan_is_ready_only_after_explicit_valid_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TEST_DATA_MODE", True)
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


def _asymmetric_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Three genes and two TFs, so a transposed prior cannot hide.

    The fixture above uses two of each, which makes the prior square -- and a
    square prior makes an orientation error invisible. That is how the
    transposition below survived: netZooPy's GIRAFFE takes the prior gene-by-TF,
    the adapter builds it TF-by-gene, and the call was made without converting,
    so every request with unequal gene and TF counts failed inside the API.
    """
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene_id\ts1\ts2\ts3\n"
        "g1\t1\t2\t3\n"
        "g2\t3\t2\t1\n"
        "g3\t2\t3\t1\n",
        encoding="utf-8",
    )
    motif = tmp_path / "motif.tsv"
    motif.write_text(
        "source\ttarget\tweight\n"
        "TF1\tg1\t1\nTF1\tg2\t0.5\nTF1\tg3\t0.25\n"
        "TF2\tg1\t0.25\nTF2\tg2\t1\nTF2\tg3\t0.5\n",
        encoding="utf-8",
    )
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("source\ttarget\tweight\nTF1\tTF2\t0.5\n", encoding="utf-8")
    return expression, motif, ppi


def test_giraffe_passes_the_prior_gene_by_tf_and_writes_tf_by_gene(tmp_path):
    """The API's orientation and the workflow's output orientation differ."""
    expression, motif, ppi = _asymmetric_inputs(tmp_path)
    output = tmp_path / "giraffe.tsv"
    seen: dict[str, tuple[int, ...]] = {}

    class FakeGiraffe:
        def __init__(self, expression_array, prior, ppi_array):
            seen["expression"] = expression_array.shape
            seen["prior"] = prior.shape
            seen["ppi"] = ppi_array.shape

        def get_regulation(self):
            # netZooPy documents this as gene-by-TF ("Size (G, TF)").
            return np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])

        def get_tfa(self):
            return np.array([[1.0, 1.1, 1.2], [2.0, 2.1, 2.2]])

    decision = _decision(expression, motif, ppi, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution._load_giraffe_api",
        return_value=(FakeGiraffe, "0.11.0"),
    ):
        raw = run_giraffe.invoke(executor_arguments("run_giraffe", decision))

    assert "API execution completed" in raw, raw
    assert seen["expression"] == (3, 3)
    assert seen["prior"] == (3, 2), "the API must receive the prior gene-by-TF"
    assert seen["ppi"] == (2, 2)

    written = output.read_text(encoding="utf-8").splitlines()
    assert written[0].split("\t") == ["tf_id", "g1", "g2", "g3"]
    assert written[1].split("\t")[0] == "TF1"
    assert [row.split("\t")[0] for row in written[1:]] == ["TF1", "TF2"]


def test_giraffe_accepts_a_labelled_square_ppi_matrix(tmp_path):
    """The registry documents this format; it used to be unreachable.

    Detection required `rows == columns - 1` while also requiring an ID token in
    the first cell, which implies a header row and therefore `rows == columns`.
    The two conditions could not hold together, so every labelled square matrix
    fell through to the edge-list branch and was rejected.
    """
    expression, motif, _ = _asymmetric_inputs(tmp_path)
    ppi = tmp_path / "ppi_matrix.tsv"
    ppi.write_text("tf\tTF1\tTF2\nTF1\t1\t0.5\nTF2\t0.5\t1\n", encoding="utf-8")

    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))

    assert bundle.ppi.shape == (2, 2)
    assert bundle.ppi[0, 1] == 0.5 and bundle.ppi[1, 0] == 0.5
    assert bundle.ppi[0, 0] == 1.0 and bundle.ppi[1, 1] == 1.0


def test_giraffe_still_reads_a_three_column_edge_list_whose_header_starts_with_tf(tmp_path):
    """The widened dense check must not swallow a small edge list.

    A three-column edge list with header `tf/gene/weight` and two data rows is
    3x3 and starts with an ID token, so shape alone cannot tell it apart from a
    two-TF labelled matrix; the header is matched against the TF set instead.
    """
    expression, motif, _ = _asymmetric_inputs(tmp_path)
    ppi = tmp_path / "ppi_edges.tsv"
    ppi.write_text("tf\tgene\tweight\nTF1\tTF2\t0.5\n", encoding="utf-8")

    bundle = load_giraffe_inputs(str(expression), str(motif), str(ppi))

    assert bundle.ppi.shape == (2, 2)
    assert bundle.ppi[0, 1] == 0.5
