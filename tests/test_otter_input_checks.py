"""OTTER co-expression must be a correlation matrix; edge headers are detected, not guessed."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.otter import inspect_otter_inputs_impl, load_otter_inputs  # noqa: E402


def _edges(tmp_path: Path) -> tuple[str, str]:
    motif = tmp_path / "motif.tsv"
    motif.write_text("TF1\tG1\t1\nTF1\tG2\t0\nTF2\tG2\t1\nTF2\tG3\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("TF1\tTF2\t1\n", encoding="utf-8")
    return str(motif), str(ppi)


def _matrix(tmp_path: Path, values: np.ndarray, genes=("G1", "G2", "G3")) -> str:
    path = tmp_path / "coexpression.tsv"
    path.write_text("gene\t" + "\t".join(genes) + "\n" + "".join(
        f"{gene}\t" + "\t".join(repr(float(v)) for v in row) + "\n" for gene, row in zip(genes, values)), encoding="utf-8")
    return str(path)


def test_covariance_matrix_is_rejected_as_not_a_correlation(tmp_path):
    expression = np.random.default_rng(0).normal(size=(3, 8)) * 3.0
    motif, ppi = _edges(tmp_path)
    report, ok = inspect_otter_inputs_impl(coexpression_file=_matrix(tmp_path, np.cov(expression)), motif_file=motif, ppi_file=ppi)
    assert not ok
    assert "co-expression must be a correlation matrix" in report
    assert "3 diagonal values differ from 1" in report and "looks like a covariance" in report


def test_values_outside_unit_range_are_rejected(tmp_path):
    values = np.array([[1.0, 1.5, 0.0], [1.5, 1.0, 0.0], [0.0, 0.0, 1.0]])
    motif, ppi = _edges(tmp_path)
    with pytest.raises(ValueError, match=r"2 values fall outside \[-1, 1\]"):
        load_otter_inputs(coexpression_file=_matrix(tmp_path, values), motif_file=motif, ppi_file=ppi)


def test_correlation_matrix_is_accepted(tmp_path):
    values = np.corrcoef(np.random.default_rng(1).normal(size=(3, 8)))
    motif, ppi = _edges(tmp_path)
    bundle = load_otter_inputs(coexpression_file=_matrix(tmp_path, values), motif_file=motif, ppi_file=ppi)
    assert bundle.C.shape == (3, 3)


def test_first_edge_with_one_token_like_gene_name_is_kept(tmp_path):
    motif = tmp_path / "motif.tsv"
    motif.write_text("TF1\tTarget\t1\nTF1\tG2\t0\nTF2\tG2\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("TF1\tTF2\t1\n", encoding="utf-8")
    values = np.corrcoef(np.random.default_rng(2).normal(size=(2, 8)))
    bundle = load_otter_inputs(
        coexpression_file=_matrix(tmp_path, values, genes=("Target", "G2")), motif_file=str(motif), ppi_file=str(ppi))
    assert bundle.gene_ids == ("Target", "G2")
    assert bundle.W[0, 0] == 1.0


def test_real_headers_are_still_dropped(tmp_path):
    motif = tmp_path / "motif.tsv"
    motif.write_text("source\ttarget\tweight\nTF1\tG1\t1\nTF1\tG2\t0\nTF2\tG2\t1\nTF2\tG3\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("tf\tgene\t1\nTF1\tTF2\t1\n", encoding="utf-8")
    values = np.corrcoef(np.random.default_rng(3).normal(size=(3, 8)))
    bundle = load_otter_inputs(coexpression_file=_matrix(tmp_path, values), motif_file=str(motif), ppi_file=str(ppi))
    assert bundle.tf_ids == ("TF1", "TF2")


def test_float32_rounding_noise_is_accepted(tmp_path):
    # A correlation exported in float32 can carry 1.0000001 on or off the diagonal.
    values = np.array([[1.0000001, 1.0000001, 0.2], [1.0000001, 1.0, 0.2], [0.2, 0.2, 0.9999999]])
    motif, ppi = _edges(tmp_path)
    bundle = load_otter_inputs(coexpression_file=_matrix(tmp_path, values), motif_file=motif, ppi_file=ppi)
    assert bundle.C.shape == (3, 3)
