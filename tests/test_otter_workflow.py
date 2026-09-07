from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.data.artifacts import validate_output_artifacts  # noqa: E402
from netzoo_agent_core.data.inspection import inspect_condor_inputs_impl  # noqa: E402
from netzoo_agent_core.data.bundles import discover_coherent_bundles  # noqa: E402
from netzoo_agent_core.data.otter import (  # noqa: E402
    inspect_otter_inputs_impl,
    load_otter_inputs,
    validate_otter_output,
)
from netzoo_agent_core.execution import run_otter  # noqa: E402
from netzoo_agent_core.cli.slash_commands import handle_slash_command  # noqa: E402
from netzoo_agent_core.contracts import PlanEvaluationResult  # noqa: E402
from netzoo_agent_core.routing.dispatch import execute_selected_tool  # noqa: E402
from workflow_registry import (  # noqa: E402
    ACTION_DEFINITIONS,
    OUTPUT_CAPABILITIES,
    executor_arguments,
)


def _inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    expression = root / "expression.tsv"
    pd.DataFrame(
        {
            "gene": ["G1", "G2", "G3"],
            "s1": [1.0, 2.0, 5.0],
            "s2": [2.0, 1.0, 4.0],
            "s3": [3.0, 4.0, 3.0],
            "s4": [5.0, 3.0, 2.0],
        }
    ).to_csv(expression, sep="\t", index=False)
    coexpression = root / "coexpression.tsv"
    pd.DataFrame(
        [["G1", 1.0, 0.1, -0.2], ["G2", 0.1, 1.0, 0.3], ["G3", -0.2, 0.3, 1.0]],
        columns=["gene", "G1", "G2", "G3"],
    ).to_csv(coexpression, sep="\t", index=False)
    motif = root / "otter_seed.tsv"
    motif.write_text(
        "TF1\tG1\t1\nTF1\tG2\t0\nTF2\tG2\t1\nTF2\tG3\t1\n",
        encoding="utf-8",
    )
    ppi = root / "ppi.tsv"
    ppi.write_text("TF1\tTF2\t1\n", encoding="utf-8")
    return expression, coexpression, motif, ppi


def _decision(output: Path, **values: str | float | int) -> TaskDecision:
    return TaskDecision(
        action="run_otter",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run OTTER.",
        output_file=str(output),
        **values,
    )


def test_expression_and_ppi_build_exact_otter_w_p_c_shapes(tmp_path):
    expression, _, motif, ppi = _inputs(tmp_path)
    report, ok = inspect_otter_inputs_impl(str(expression), "", str(motif), str(ppi))
    assert ok, report
    bundle = load_otter_inputs(str(expression), "", str(motif), str(ppi))
    assert bundle.W.shape == (2, 3)
    assert bundle.P.shape == (2, 2)
    assert bundle.C.shape == (3, 3)
    assert bundle.source == "expression-derived co-expression"
    assert "TF-by-gene" in report and "gene-by-gene" in report


def test_precomputed_coexpression_and_ppi_are_supported_without_expression(tmp_path):
    _, coexpression, motif, ppi = _inputs(tmp_path)
    report, ok = inspect_otter_inputs_impl("", str(coexpression), str(motif), str(ppi))
    assert ok, report
    bundle = load_otter_inputs("", str(coexpression), str(motif), str(ppi))
    assert bundle.sample_count is None
    assert bundle.source == "precomputed co-expression"
    assert tuple(bundle.gene_ids) == ("G1", "G2", "G3")


def test_otter_rejects_role_and_intersection_contract_violations(tmp_path):
    expression, coexpression, motif, ppi = _inputs(tmp_path)
    bad_ppi = tmp_path / "bad_ppi.tsv"
    bad_ppi.write_text("TF1\tGeneX\t1\n", encoding="utf-8")
    _, ok = inspect_otter_inputs_impl(str(expression), "", str(motif), str(bad_ppi))
    assert not ok

    bad_order = tmp_path / "bad_order.tsv"
    pd.DataFrame(
        [["G2", 1.0, 0.1, 0.3], ["G1", 0.1, 1.0, -0.2], ["G3", 0.3, -0.2, 1.0]],
        columns=["gene", "G2", "G1", "G3"],
    ).to_csv(bad_order, sep="\t", index=False)
    _, ok = inspect_otter_inputs_impl(str(expression), str(bad_order), str(motif), str(ppi))
    assert not ok

    reordered_expression = tmp_path / "reordered_expression.tsv"
    expression_frame = pd.read_csv(expression, sep="\t").iloc[[1, 0, 2]]
    expression_frame.to_csv(reordered_expression, sep="\t", index=False)
    _, ok = inspect_otter_inputs_impl(str(reordered_expression), str(coexpression), str(motif), str(ppi))
    assert not ok

    bad_motif = tmp_path / "bad_motif.tsv"
    bad_motif.write_text("TF1\tG1\t1\nTF1\tG1\t1\n", encoding="utf-8")
    _, ok = inspect_otter_inputs_impl(str(expression), "", str(bad_motif), str(ppi))
    assert not ok

    na_expression = tmp_path / "na_expression.tsv"
    expression_text = expression.read_text(encoding="utf-8").replace("2.0", "NA", 1)
    na_expression.write_text(expression_text, encoding="utf-8")
    _, ok = inspect_otter_inputs_impl(str(na_expression), "", str(motif), str(ppi))
    assert not ok

    empty_row = tmp_path / "empty_row.tsv"
    empty_row.write_text(
        "gene\ts1\ts2\ts3\nG1\t1\t2\t3\nG2\t\t\t\nG3\t3\t2\t1\n",
        encoding="utf-8",
    )
    _, ok = inspect_otter_inputs_impl(str(empty_row), "", str(motif), str(ppi))
    assert not ok


def test_otter_parameters_are_allow_listed_and_dry_run_does_not_write(tmp_path):
    expression, _, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "otter.tsv"
    decision = _decision(
        output,
        expression_file=str(expression),
        motif_file=str(motif),
        ppi_file=str(ppi),
        lam=0.2,
        gamma=0.5,
        iterations=7,
        eta=0.01,
        bexp=1.5,
    )
    arguments = executor_arguments("run_otter", decision)
    assert set(arguments) == set(ACTION_DEFINITIONS["run_otter"].executor_fields)
    assert "sample_metadata" not in arguments
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", False):
        result = run_otter.invoke(arguments)
    assert "OTTER Python API preview" in result
    assert "lam=0.2" in result and "gamma=0.5" in result
    assert "Iter=7" in result and "eta=0.01" in result and "bexp=1.5" in result
    assert "no analysis was executed" in result
    assert not output.exists()


def test_otter_execute_writes_and_validates_matrix_and_edge_list(tmp_path):
    expression, _, motif, ppi = _inputs(tmp_path)

    class FakeOtter:
        @staticmethod
        def otter(W, P, C, **kwargs):
            assert W.shape == (2, 3)
            assert P.shape == (2, 2)
            assert C.shape == (3, 3)
            assert kwargs == {"lam": 0.2, "gamma": 0.5, "Iter": 7, "eta": 0.01, "bexp": 1.5}
            return np.full((2, 3), 0.25)

    for suffix, output_format in ((".tsv", "matrix"), (".csv", "edge_list")):
        output = tmp_path / f"result{suffix}"
        decision = _decision(
            output,
            expression_file=str(expression),
            motif_file=str(motif),
            ppi_file=str(ppi),
            output_format=output_format,
            lam=0.2,
            gamma=0.5,
            iterations=7,
            eta=0.01,
            bexp=1.5,
        )
        with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
            "netzoo_agent_core.execution._load_otter_api", return_value=FakeOtter
        ):
            result = execute_selected_tool(decision)
        assert "OTTER API execution completed" in result
        bundle = load_otter_inputs(str(expression), "", str(motif), str(ppi))
        assert validate_otter_output(str(output), output_format, bundle.tf_ids, bundle.gene_ids)[0]
        artifact = validate_output_artifacts("run_otter", decision)
        assert artifact.ok, artifact.errors
        if output_format == "edge_list":
            condor_report, condor_ok = inspect_condor_inputs_impl(str(output))
            assert condor_ok, condor_report


def test_otter_output_rejects_non_bipartite_or_incomplete_edge_artifacts(tmp_path):
    invalid = tmp_path / "invalid.csv"
    invalid.write_text(
        "source,target,weight\nTF1,G1,0.2\nG1,TF2,0.3\n",
        encoding="utf-8",
    )
    ok, errors, _ = validate_otter_output(str(invalid), "edge_list", ("TF1", "TF2"), ("G1",))
    assert not ok
    assert any("bipartite" in error or "source IDs" in error or "grid" in error for error in errors)


def test_otter_plans_expression_and_precomputed_variants_and_declares_handoffs(tmp_path):
    expression, coexpression, motif, ppi = _inputs(tmp_path)
    expression_plan = build_workflow_plan(
        _decision(
            tmp_path / "expression-result.tsv",
            expression_file=str(expression), motif_file=str(motif), ppi_file=str(ppi),
        ),
        f"Run OTTER with expression_file={expression} motif_file={motif} ppi_file={ppi}",
    )
    assert expression_plan.status == "ready"

    coexpression_plan = build_workflow_plan(
        _decision(
            tmp_path / "coexpression-result.tsv",
            coexpression_file=str(coexpression), motif_file=str(motif), ppi_file=str(ppi),
        ),
        f"Run OTTER with coexpression_file={coexpression} motif_file={motif} ppi_file={ppi}",
    )
    assert coexpression_plan.status == "ready"

    capability = OUTPUT_CAPABILITIES["run_otter"]
    assert capability.handoff_targets == ("run_condor",)
    assert "PPI and co-expression are never PANDA motif priors" in capability.handoff_contract
    assert "run_lioness_otter" not in ACTION_DEFINITIONS
    assert "sparsity" not in ACTION_DEFINITIONS["run_otter"].executor_fields
    cobra = OUTPUT_CAPABILITIES["run_cobra"]
    assert "run_otter" in cobra.handoff_targets
    assert "identifier/order" in cobra.handoff_contract


def test_otter_execute_slash_requires_a_ready_approved_plan(tmp_path):
    expression, _, motif, ppi = _inputs(tmp_path)
    output = tmp_path / "result.tsv"
    plan = build_workflow_plan(
        _decision(
            output,
            expression_file=str(expression), motif_file=str(motif), ppi_file=str(ppi),
        ),
        f"Run OTTER with expression_file={expression} motif_file={motif} ppi_file={ppi} output_file={output}",
    )
    assert plan.status == "ready"
    blocked = handle_slash_command(
        "/execute",
        current_plan=plan,
        current_plan_evaluation=PlanEvaluationResult(status="deferred", score=50, summary="review"),
    )
    assert blocked.execute_once is False
    confirmed = handle_slash_command(
        "/execute",
        current_plan=plan,
        current_plan_evaluation=PlanEvaluationResult(status="approved", score=100, summary="approved"),
    )
    assert confirmed.execute_once is True
    assert "Confirm" in confirmed.message


def test_otter_plan_requires_one_conditional_coexpression_source(tmp_path):
    expression, coexpression, motif, ppi = _inputs(tmp_path)
    expression.unlink()
    coexpression.unlink()
    plan = build_workflow_plan(
        _decision(tmp_path / "result.tsv", motif_file=str(motif), ppi_file=str(ppi)),
        f"Run OTTER with motif_file={motif} ppi_file={ppi}",
    )
    assert plan.status == "needs_input"
    assert "expression_file" in plan.missing_inputs


def test_otter_bundle_discovery_never_mixes_two_complete_directories(tmp_path):
    first = tmp_path / "study-a"
    second = tmp_path / "study-b"
    _inputs(first)
    _inputs(second)
    bundles = discover_coherent_bundles("run_otter", tmp_path, {})
    assert len(bundles) == 2
    assert {bundle.bundle_id for bundle in bundles} == {
        f"directory:{first.resolve()}",
        f"directory:{second.resolve()}",
    }


def test_ppi_edge_declared_absent_does_not_project_as_present(tmp_path):
    """A PPI edge listed with weight 0 must project to 0, not to 1.

    The registry promises a binary adjacency projection. The adapter previously
    assigned 1.0 to every listed pair regardless of its weight, so a file that
    spelled out a non-interaction turned it into an interaction -- and a dense
    grid of pairs became a fully connected PPI network. Measured on upstream's
    own OTTER toy data (661 TFs): of the 436,260 off-diagonal cells, 350,312 are
    genuinely absent and 85,948 present, so writing that P out as an edge list
    and reading it back fabricated 80.3% of the network as interacting.
    """
    expression, _, motif, ppi = _inputs(tmp_path)
    ppi.write_text("TF1\tTF2\t0\n", encoding="utf-8")

    bundle = load_otter_inputs(str(expression), "", str(motif), str(ppi))

    assert bundle.P[0, 1] == 0.0
    assert bundle.P[1, 0] == 0.0
    assert bundle.P[0, 0] == 1.0 and bundle.P[1, 1] == 1.0


def test_ppi_projection_is_binary_and_does_not_carry_confidences(tmp_path):
    """Distinct positive weights project alike: P holds adjacency, not scores."""
    expression, _, motif, ppi = _inputs(tmp_path)
    projections = []
    for weight in ("0.01", "0.99"):
        ppi.write_text(f"TF1\tTF2\t{weight}\n", encoding="utf-8")
        projections.append(
            load_otter_inputs(str(expression), "", str(motif), str(ppi)).P.copy()
        )

    assert np.array_equal(*projections)
    assert set(np.unique(projections[0]).tolist()) <= {0.0, 1.0}
    assert projections[0][0, 1] == 1.0


def test_ppi_projection_does_not_depend_on_row_order(tmp_path):
    """Both directions listed with different weights must not race on order."""
    expression, _, motif, ppi = _inputs(tmp_path)
    projections = []
    for rows in ("TF1\tTF2\t0\nTF2\tTF1\t0.9\n", "TF2\tTF1\t0.9\nTF1\tTF2\t0\n"):
        ppi.write_text(rows, encoding="utf-8")
        projections.append(
            load_otter_inputs(str(expression), "", str(motif), str(ppi)).P.copy()
        )

    assert np.array_equal(*projections)
    assert projections[0][0, 1] == projections[0][1, 0] == 1.0
