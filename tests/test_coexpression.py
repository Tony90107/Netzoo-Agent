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


def test_cobra_reconstruction_refuses_an_indefinite_intercept_component():
    # psi = [1, -0.9] on a Hadamard basis used to yield a "correlation" of 19.
    q = np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2.0)
    psi = np.array([[1.0, -0.9], [0.2, 0.1]])
    with pytest.raises(ValueError, match="positive semidefinite"):
        adjusted_coexpression_from_cobra(psi, q, ["G1", "G2"], ["intercept", "age"])


def test_cobra_reconstruction_correlations_stay_in_range():
    rng = np.random.default_rng(0)
    q, _ = np.linalg.qr(rng.normal(size=(6, 4)))
    psi = np.vstack([rng.uniform(0.1, 2.0, size=4), rng.normal(size=4)])
    matrix = adjusted_coexpression_from_cobra(psi, q, [f"G{i}" for i in range(6)], ["intercept", "x"])
    assert np.abs(matrix.to_numpy()).max() <= 1.0


def test_run_cobra_passes_covariates_uncentered(tmp_path):
    import json
    import os
    import subprocess

    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene\ts1\ts2\ts3\ts4\nTP53\t1\t3\t2\t5\nEGFR\t2\t1\t4\t3\nMYC\t5\t2\t1\t4\n"
        "BRAF\t3\t5\t2\t1\nKRAS\t2\t4\t5\t3\n"
    )
    design = tmp_path / "design.tsv"
    design.write_text("sample\tage\tgroup\ns1\t40\t0\ns2\t50\t1\ns3\t60\t0\ns4\t70\t1\n")
    fake = tmp_path / "fake" / "netZooPy"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text("")
    seen = tmp_path / "design_seen.npy"
    (fake / "cobra.py").write_text(
        "import numpy as np\n"
        f"def cobra(X, G):\n    np.save({str(seen)!r}, X)\n"
        "    g = G.shape[0]\n"
        "    return np.ones((X.shape[1], g)), np.eye(g), np.ones(g), G\n"
    )
    out = tmp_path / "out"
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(fake.parent), str(SCRIPTS_DIR)))}
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "run_cobra.py"), "-e", str(expression), "-d", str(design), "-o", str(out)],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    x = np.load(seen)
    assert np.allclose(x[:, 0], 1.0)
    # Centered covariates would make the intercept component the unadjusted correlation (review 2026-11-05).
    assert np.allclose(x[:, 1], [40, 50, 60, 70])
    assert np.allclose(x[:, 2], [0, 1, 0, 1])
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["adjustment"]["covariates_centered"] is False
    assert "covariate_means" not in manifest["adjustment"]


def test_cobra_intercept_component_is_adjusted_only_without_centering():
    """psi = n (X'X)^-1 X' (G'Q)^2: with centered covariates the intercept row is the eigenvalues."""
    rng = np.random.default_rng(0)
    n = 40
    batch = np.r_[np.zeros(20), np.ones(20)]
    g = rng.normal(size=(30, n))
    g[:10, batch == 1] += 2.0
    g = g - g.mean(axis=1, keepdims=True)
    g = g / np.linalg.norm(g, axis=1, keepdims=True)
    d, q = np.linalg.eigh(g @ g.T)

    def intercept_psi(x):
        return (n * np.linalg.solve(x.T @ x, x.T @ (g.T @ q) ** 2))[0]

    raw = np.c_[np.ones(n), batch]
    centered = np.c_[np.ones(n), batch - batch.mean()]
    assert np.allclose(intercept_psi(centered), d)
    assert not np.allclose(intercept_psi(raw), d)


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
