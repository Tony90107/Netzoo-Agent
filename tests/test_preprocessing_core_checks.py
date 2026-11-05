"""Preprocessing checks that keep wrong-scale or wrong-shape data out of the networks (2026-11-05 review)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import TaskDecision  # noqa: E402
from netzoo_agent_core.data.bundles import _bundle_in_directory  # noqa: E402
from netzoo_agent_core.data.discovery import best_named_file, top_named_files  # noqa: E402
from netzoo_agent_core.data.lioness_dragon import standardize_dragon_layer  # noqa: E402
from netzoo_agent_core.data.normalization import normalization_input_report  # noqa: E402
from netzoo_agent_core.data.tables import _read_checked_table, _validate_expression  # noqa: E402
from netzoo_agent_core.data.transforms import format_expression_for_netzoo_impl  # noqa: E402
from netzoo_agent_core.execution import _gene_set_mode_note  # noqa: E402
from netzoo_agent_core.routing.dispatch import execute_selected_tool  # noqa: E402

RNG = np.random.default_rng(7)


def _expression(path: Path, frame: pd.DataFrame) -> Path:
    frame.to_csv(path, sep="\t", index_label="gene")
    return path


def _genes(count: int) -> list[str]:
    return [f"GENE{index}" for index in range(count)]


def _samples(count: int) -> list[str]:
    return [f"S{index}" for index in range(count)]


# PANDA/PUMA/LIONESS expression: netZooPy nan_to_num's a gene with any missing value to zero co-expression.

def test_expression_with_one_missing_value_is_refused(tmp_path):
    frame = pd.DataFrame(RNG.normal(8, 2, (40, 6)), index=_genes(40), columns=_samples(6)).astype(object)
    frame.iloc[0, 0] = "NA"
    check = _validate_expression(_read_checked_table("expression", str(_expression(tmp_path / "e.tsv", frame))))
    assert any("1 missing, non-numeric or infinite" in error and "GENE0" in error for error in check.errors)


def test_expression_with_infinite_value_is_refused(tmp_path):
    frame = pd.DataFrame(RNG.normal(8, 2, (40, 6)), index=_genes(40), columns=_samples(6)).astype(object)
    frame.iloc[5, 3] = "inf"
    check = _validate_expression(_read_checked_table("expression", str(_expression(tmp_path / "e.tsv", frame))))
    assert any("infinite" in error for error in check.errors)


def test_expression_with_duplicate_gene_ids_is_refused(tmp_path):
    frame = pd.DataFrame(RNG.normal(8, 2, (40, 6)), index=_genes(39) + ["GENE1"], columns=_samples(6))
    check = _validate_expression(_read_checked_table("expression", str(_expression(tmp_path / "e.tsv", frame))))
    assert any("duplicate gene ID" in error and "GENE1" in error for error in check.errors)


def test_constant_gene_is_named_in_a_warning_not_refused(tmp_path):
    frame = pd.DataFrame(RNG.normal(8, 2, (40, 6)), index=_genes(40), columns=_samples(6))
    frame.iloc[2, :] = 5.0
    check = _validate_expression(_read_checked_table("expression", str(_expression(tmp_path / "e.tsv", frame))))
    assert not check.errors
    assert any("constant across samples" in warning and "GENE2" in warning for warning in check.warnings)


# Normalization: the input must be counts, not log values and not already-normalized values.

def test_sparse_log2_counts_are_refused_as_log_scale(tmp_path):
    counts = RNG.negative_binomial(2, 0.05, (500, 8))
    counts[RNG.random(counts.shape) < 0.6] = 0
    path = _expression(tmp_path / "log.tsv", pd.DataFrame(np.log2(counts + 1), index=_genes(500), columns=_samples(8)))
    report, ok, _ = normalization_input_report(str(path), str(tmp_path / "out.tsv"), method="tmm")
    assert not ok
    assert "reads as log-scale data" in report


def test_tpm_is_refused_as_already_normalized(tmp_path):
    values = RNG.gamma(0.5, 200, (500, 8))
    tpm = values / values.sum(axis=0) * 1e6
    path = _expression(tmp_path / "tpm.tsv", pd.DataFrame(tpm, index=_genes(500), columns=_samples(8)))
    report, ok, _ = normalization_input_report(str(path), str(tmp_path / "out.tsv"), method="rle")
    assert not ok
    assert "already-normalized" in report


def test_tpm_is_accepted_for_quantile_normalization(tmp_path):
    """normalize.quantiles needs no counts; the already-normalized stop was a false refusal (review 2026-11-05)."""
    values = RNG.gamma(0.5, 200, (500, 8))
    tpm = values / values.sum(axis=0) * 1e6
    path = _expression(tmp_path / "tpm.tsv", pd.DataFrame(tpm, index=_genes(500), columns=_samples(8)))
    report, ok, _ = normalization_input_report(str(path), str(tmp_path / "out.tsv"), method="quantile")
    assert ok, report
    assert "already-normalized" not in report


def test_raw_and_expected_counts_still_pass(tmp_path):
    counts = RNG.negative_binomial(2, 0.01, (500, 8)).astype(float)
    counts[:, 1] *= 1.7  # a deeper sample
    raw = _expression(tmp_path / "raw.tsv", pd.DataFrame(counts, index=_genes(500), columns=_samples(8)))
    expected = _expression(
        tmp_path / "expected.tsv", pd.DataFrame(counts + RNG.random(counts.shape), index=_genes(500), columns=_samples(8))
    )
    for path in (raw, expected):
        _, ok, _ = normalization_input_report(str(path), str(tmp_path / "out.tsv"), method="rle")
        assert ok


def test_snail_warns_about_a_single_sample_group(tmp_path):
    counts = RNG.negative_binomial(2, 0.01, (200, 5)).astype(float)
    path = _expression(tmp_path / "raw.tsv", pd.DataFrame(counts, index=_genes(200), columns=_samples(5)))
    groups = tmp_path / "groups.tsv"
    groups.write_text("S0\tA\nS1\tA\nS2\tB\nS3\tB\nS4\tC\n", encoding="utf-8")
    report, ok, _ = normalization_input_report(str(path), str(tmp_path / "out.tsv"), str(groups))
    assert ok
    assert "1 group(s) have a single sample (C)" in report


# Orientation: transposing on shape alone is refused; Ensembl IDs settle the axis.

def test_small_gene_panel_in_many_samples_is_not_transposed_on_shape(tmp_path):
    frame = pd.DataFrame(RNG.normal(5, 1, (30, 200)), index=[f"TF{i}" for i in range(30)], columns=_samples(200))
    path = tmp_path / "panel.tsv"
    frame.to_csv(path, sep="\t", index_label="id")
    report = format_expression_for_netzoo_impl(str(path), str(tmp_path / "out.tsv"), execute=False)
    assert "gene orientation is ambiguous" in report


def test_genes_on_rows_by_shape_still_detected(tmp_path):
    frame = pd.DataFrame(RNG.normal(5, 1, (200, 30)), index=_genes(200), columns=_samples(30))
    path = tmp_path / "bulk.tsv"
    frame.to_csv(path, sep="\t", index_label="id")
    report = format_expression_for_netzoo_impl(str(path), str(tmp_path / "out.tsv"), execute=False)
    assert "- detected genes axis: rows" in report


def test_ensembl_ids_on_columns_set_the_gene_axis(tmp_path):
    genes = [f"ENSG{index:011d}.3" for index in range(20)]
    frame = pd.DataFrame(RNG.normal(5, 1, (50, 20)), index=_samples(50), columns=genes)
    path = tmp_path / "samples_by_genes.tsv"
    frame.to_csv(path, sep="\t", index_label="id")
    report = format_expression_for_netzoo_impl(str(path), str(tmp_path / "out.tsv"), execute=False)
    assert "- detected genes axis: columns" in report
    assert "- genes: 20" in report


# DRAGON: each layer is standardized before netZooPy, as its tutorial does.

def test_standardize_dragon_layer_gives_unit_variance_features():
    layer = np.column_stack([RNG.normal(1000, 50, 30), RNG.normal(0.5, 0.01, 30)])
    scaled = standardize_dragon_layer(layer)
    assert np.allclose(scaled.mean(axis=0), 0.0)
    assert np.allclose(scaled.std(axis=0), 1.0)


def test_run_dragon_passes_standardized_layers_to_netzoopy(tmp_path):
    ids = _samples(6)
    first = pd.DataFrame({"a": RNG.normal(1000, 50, 6), "b": RNG.normal(10, 3, 6)})
    first.insert(0, "sample_id", ids)
    first.to_csv(tmp_path / "layer1.tsv", sep="\t", index=False)
    second = pd.DataFrame({"m1": RNG.uniform(0, 1, 6)})
    second.insert(0, "sample_id", ids)
    second.to_csv(tmp_path / "layer2.tsv", sep="\t", index=False)
    seen = {}

    class FakeDragon:
        @staticmethod
        def estimate_penalty_parameters_dragon(x1, x2):
            seen["x1"], seen["x2"] = x1, x2
            return [0.2, 0.3], np.zeros((2, 2))

        @staticmethod
        def get_precision_matrix_dragon(x1, x2, lambdas):
            return np.eye(x1.shape[1] + x2.shape[1]), np.zeros(x1.shape[1] + x2.shape[1])

        @staticmethod
        def get_partial_correlation_dragon(x1, x2, lambdas):
            return np.zeros((x1.shape[1] + x2.shape[1], x1.shape[1] + x2.shape[1]))

    decision = TaskDecision(
        action="run_dragon", in_scope=True, should_execute=True, confidence=1.0, reason="Run DRAGON.",
        omics_layer_1=str(tmp_path / "layer1.tsv"), omics_layer_2=str(tmp_path / "layer2.tsv"),
        output_file=str(tmp_path / "network.tsv"),
    )
    with patch("netzoo_agent_core.execution.settings.EXECUTE_TOOLS", True), patch(
        "netzoo_agent_core.execution._load_dragon_api", return_value=FakeDragon
    ):
        result = execute_selected_tool(decision)
    assert "API execution completed" in result
    for layer in (seen["x1"], seen["x2"]):
        assert np.allclose(layer.mean(axis=0), 0.0)
        assert np.allclose(layer.std(axis=0), 1.0)


# Directory autofill: a co-expression matrix is never the expression file, and ties are not broken silently.

def test_coexpression_file_is_not_picked_as_expression(tmp_path):
    (tmp_path / "cobra_adjusted_coexpression.tsv").write_text("x\n", encoding="utf-8")
    (tmp_path / "expr_counts.tsv").write_text("x\n", encoding="utf-8")
    assert best_named_file(tmp_path, ("expression", "expr")).name == "expr_counts.tsv"


def test_equally_named_expression_files_are_left_for_the_user(tmp_path):
    for name in ("expression_raw.tsv", "expression_log.tsv", "panda_motif.tsv", "ppi.tsv"):
        (tmp_path / name).write_text("x\n", encoding="utf-8")
    assert len(top_named_files(tmp_path, ("expression", "expr"))) == 2
    bundle = _bundle_in_directory("run_panda", tmp_path, {})
    assert bundle is not None
    assert "expression_file" in bundle.missing_fields
    assert "Several files fit expression_file equally well" in bundle.reason


# PANDA/PUMA union mode: genes with no expression data are counted in the report.

def test_union_mode_note_counts_prior_only_genes(tmp_path):
    expression = _expression(
        tmp_path / "e.tsv", pd.DataFrame(RNG.normal(8, 2, (3, 4)), index=["G1", "G2", "G3"], columns=_samples(4))
    )
    motif = tmp_path / "motif.tsv"
    motif.write_text("TF1\tG1\t1\nTF1\tG2\t1\nTF2\tG4\t1\nTF2\tG5\t1\n", encoding="utf-8")
    note = _gene_set_mode_note(["run-puma"], str(expression), str(motif))
    assert "union mode (netZooPy default): 2 of 5 genes" in note
    assert "G4" in note
    assert _gene_set_mode_note(["run-puma", "--mode_process", "intersection"], str(expression), str(motif)) == (
        "\n- gene set: intersection mode"
    )


def test_sample_count_ignores_value_level_problems(tmp_path):
    from netzoo_agent_core.data.inspection import expression_sample_count

    frame = pd.DataFrame(RNG.normal(8, 2, (40, 6)), index=_genes(39) + ["GENE1"], columns=_samples(6)).astype(object)
    frame.iloc[0, 0] = "NA"
    count, _ = expression_sample_count(str(_expression(tmp_path / "e.tsv", frame)))
    assert count == 6
