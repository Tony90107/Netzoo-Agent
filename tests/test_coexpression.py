from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.data.coexpression import (  # noqa: E402
    adjusted_coexpression_from_cobra,
    read_coexpression_matrix,
    write_adjusted_coexpression,
)
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision  # noqa: E402


def test_cobra_intercept_component_is_a_labeled_correlation_artifact(tmp_path):
    q = np.eye(3)
    psi = np.asarray(
        [
            [2.0, 3.0, 4.0],  # intercept / adjusted component
            [0.5, 0.0, 0.0],  # modeled batch component
        ]
    )
    matrix = adjusted_coexpression_from_cobra(
        psi, q, ["G2", "G1", "G3"], ["intercept", "batch"]
    )

    assert list(matrix.index) == ["G2", "G1", "G3"]
    assert list(matrix.columns) == ["G2", "G1", "G3"]
    assert matrix.shape == (3, 3)
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 1.0)

    tsv, npz = write_adjusted_coexpression(matrix, tmp_path)
    restored = read_coexpression_matrix(str(tsv))
    assert np.allclose(restored.to_numpy(), matrix.to_numpy())
    arrays = np.load(npz, allow_pickle=False)
    assert arrays["matrix"].shape == (3, 3)
    assert list(arrays["gene_ids"]) == ["G2", "G1", "G3"]


def test_coexpression_reader_reorders_columns_and_checks_expected_ids(tmp_path):
    path = tmp_path / "coexpression.tsv"
    path.write_text(
        "gene_id\tG2\tG1\nG1\t0.5\t1\nG2\t1\t0.5\n",
        encoding="utf-8",
    )
    matrix = read_coexpression_matrix(str(path), expected_gene_ids=["G1", "G2"])
    assert list(matrix.index) == ["G1", "G2"]
    assert list(matrix.columns) == ["G1", "G2"]
    assert matrix.loc["G1", "G2"] == 0.5


@pytest.mark.parametrize(
    "frame, message",
    [
        (pd.DataFrame([["G1", 1.0], ["G2", 0.5]], columns=["gene_id", "G1"]), "row/column"),
        (pd.DataFrame([["G1", 1.0, 0.2], ["G2", 0.5, 1.0]], columns=["gene_id", "G1", "G2"]), "symmetric"),
    ],
)
def test_coexpression_reader_rejects_invalid_contract(tmp_path, frame, message):
    path = tmp_path / "bad.tsv"
    frame.to_csv(path, sep="\t", index=False)
    with pytest.raises(ValueError, match=message):
        read_coexpression_matrix(str(path))


def test_cobra_reconstruction_requires_an_intercept():
    with pytest.raises(ValueError, match="intercept"):
        adjusted_coexpression_from_cobra(
            np.ones((1, 2)), np.eye(2), ["G1", "G2"], ["batch"]
        )


def test_explicit_coexpression_path_is_hydrated_into_panda_decision():
    decision = TaskDecision(
        action="run_panda",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="precomputed PANDA",
    )
    hydrated = hydrate_router_decision(
        decision,
        "run PANDA with coexpression_file=outputs/cobra/adjusted_coexpression.tsv",
    )
    assert hydrated.coexpression_file == "outputs/cobra/adjusted_coexpression.tsv"
