from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.data.dragon import (  # noqa: E402
    inspect_dragon_inputs_impl,
    load_and_align_dragon_layers,
    validate_dragon_output,
    write_dragon_edge_list,
    write_dragon_matrix,
)
from netzoo_agent_core.execution import run_dragon  # noqa: E402
from netzoo_agent_core.routing.dispatch import execute_selected_tool  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, executor_arguments  # noqa: E402


def _layer(path: Path, ids=("s1", "s2", "s3", "s4"), features=("a", "b")) -> Path:
    frame = pd.DataFrame(
        [[index + offset for offset in range(len(features))] for index in range(len(ids))],
        columns=features,
    )
    frame.insert(0, "sample_id", ids)
    frame.to_csv(path, sep="\t", index=False)
    return path


def _decision(layer1: Path, layer2: Path, output: Path, **kwargs) -> TaskDecision:
    return TaskDecision(
        action="run_dragon",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="Run DRAGON.",
        omics_layer_1=str(layer1),
        omics_layer_2=str(layer2),
        output_file=str(output),
        **kwargs,
    )


def test_dragon_layers_align_by_exact_sample_ids_and_reorder_second_layer(tmp_path):
    first = _layer(tmp_path / "layer1.tsv")
    second = _layer(tmp_path / "layer2.tsv", ids=("s4", "s2", "s1", "s3"), features=("m1",))
    layer1, layer2, errors = load_and_align_dragon_layers(str(first), str(second))
    assert not errors
    assert list(layer1.index) == ["s1", "s2", "s3", "s4"]
    assert list(layer2.index) == ["s1", "s2", "s3", "s4"]


def test_dragon_rejects_sample_id_mismatch_duplicate_features_non_numeric_and_missing(tmp_path):
    first = _layer(tmp_path / "layer1.tsv")
    mismatch = _layer(tmp_path / "mismatch.tsv", ids=("s1", "s2", "s3", "other"))
    _, ok = inspect_dragon_inputs_impl(str(first), str(mismatch))
    assert not ok
    duplicate = tmp_path / "duplicate.tsv"
    duplicate.write_text("sample_id\ta\ta\n s1\t1\t2\n s2\t2\t3\n s3\t3\t4\n", encoding="utf-8")
    _, ok = inspect_dragon_inputs_impl(str(duplicate), str(first))
    assert not ok
    non_numeric = tmp_path / "non-numeric.tsv"
    non_numeric.write_text("sample_id\ta\n s1\tbad\n s2\t2\n s3\t3\n", encoding="utf-8")
    _, ok = inspect_dragon_inputs_impl(str(non_numeric), str(first))
    assert not ok
    missing = tmp_path / "missing.tsv"
    missing.write_text("sample_id\ta\n s1\t1\n s2\tNA\n s3\t3\n", encoding="utf-8")
    _, ok = inspect_dragon_inputs_impl(str(missing), str(first))
    assert not ok


def test_dragon_requires_two_layers_and_rejects_more_than_two_without_pairwise_contract(tmp_path):
    first = _layer(tmp_path / "layer1.tsv")
    second = _layer(tmp_path / "layer2.tsv", features=("m1",))
    plan = build_workflow_plan(
        _decision(first, second, tmp_path / "out.tsv"),
        f"Run DRAGON with omics_layer_1={first} omics_layer_2={second}; I also have three omics layers.",
    )
    assert plan.status == "needs_input"
    assert "exactly two" in (plan.question or "")
    missing = build_workflow_plan(
        TaskDecision(
            action="run_dragon", in_scope=True, should_execute=True,
            confidence=1.0, reason="Run DRAGON.",
        ),
        "Run DRAGON.",
    )
    assert missing.status == "needs_input"
    assert {"omics_layer_1", "omics_layer_2"}.issubset(missing.missing_inputs)
    assert any(item.field == "output_file" and item.status == "defaulted" for item in missing.evidence)


def test_dragon_output_matrix_and_edge_list_contracts(tmp_path):
    node_ids = ["layer1::a", "layer2::m1"]
    partial = np.array([[0.0, 0.25], [0.25, 0.0]])
    precision = np.array([[1.0, -0.5], [-0.5, 1.0]])
    matrix_path = write_dragon_matrix(str(tmp_path / "network.tsv"), partial, node_ids)
    edge_path = write_dragon_edge_list(str(tmp_path / "network.csv"), partial, precision, node_ids)
    assert validate_dragon_output(matrix_path, "matrix")[0]
    assert validate_dragon_output(edge_path, "edge_list")[0]
    assert list(pd.read_csv(edge_path).columns) == ["source", "target", "partial_correlation", "precision"]


def test_dragon_dry_run_is_api_preview_and_omits_unset_optional_values(tmp_path):
    first = _layer(tmp_path / "layer1.tsv")
    second = _layer(tmp_path / "layer2.tsv", features=("m1",))
    output = tmp_path / "network.tsv"
    decision = _decision(first, second, output)
    arguments = executor_arguments("run_dragon", decision)
    assert "lambda1" not in arguments and "lambda2" not in arguments
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", False):
        result = run_dragon.invoke(arguments)
    assert "Python API preview" in result
    assert "no analysis was executed" in result
    assert not output.exists()


def test_dragon_execute_uses_verified_api_and_validates_matrix_output(tmp_path):
    first = _layer(tmp_path / "layer1.tsv")
    second = _layer(tmp_path / "layer2.tsv", features=("m1",))
    output = tmp_path / "network.tsv"

    class FakeDragon:
        @staticmethod
        def estimate_penalty_parameters_dragon(x1, x2):
            assert x1.shape[0] == x2.shape[0] == 4
            return [0.2, 0.3], np.zeros((2, 2))

        @staticmethod
        def get_precision_matrix_dragon(x1, x2, lambdas):
            return np.eye(x1.shape[1] + x2.shape[1]), np.zeros(x1.shape[1] + x2.shape[1])

        @staticmethod
        def get_partial_correlation_dragon(x1, x2, lambdas):
            return np.zeros((x1.shape[1] + x2.shape[1], x1.shape[1] + x2.shape[1]))

    decision = _decision(first, second, output)
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution._load_dragon_api", return_value=FakeDragon
    ):
        result = execute_selected_tool(decision)
    assert "API execution completed" in result
    assert validate_dragon_output(str(output), "matrix")[0]


def test_dragon_has_no_direct_handoff_to_other_net_zoo_workflows():
    definition = ACTION_DEFINITIONS["run_dragon"]
    capability = OUTPUT_CAPABILITIES["run_dragon"]
    assert definition.required_inputs == ("omics_layer_1", "omics_layer_2", "output_file")
    assert capability.handoff_targets == ()
    assert "not a causal" in capability.handoff_contract
    assert "measurement_dataset" in capability.input_artifacts
