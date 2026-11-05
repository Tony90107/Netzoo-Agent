"""COBRA inspection rejects values upstream cobra cannot standardize and constant covariates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.cobra import inspect_cobra_inputs_impl, load_cobra_inputs  # noqa: E402

TOY = Path(__file__).parents[1] / "data" / "cobra-toy"
SAMPLES = ["S1", "S2", "S3", "S4"]


def _expression(tmp_path: Path, rows: dict[str, list[str]]) -> str:
    path = tmp_path / "expression.tsv"
    path.write_text("gene\t" + "\t".join(SAMPLES) + "\n" + "".join(
        f"{gene}\t" + "\t".join(values) + "\n" for gene, values in rows.items()), encoding="utf-8")
    return str(path)


def _design(tmp_path: Path, header: list[str], columns: list[list[str]]) -> str:
    path = tmp_path / "design.tsv"
    path.write_text("sample\t" + "\t".join(header) + "\n" + "".join(
        sample + "\t" + "\t".join(column[index] for column in columns) + "\n"
        for index, sample in enumerate(SAMPLES)), encoding="utf-8")
    return str(path)


GOOD = {f"G{g}": [str((g + 1) * (s + 2) % 11 + 0.5) for s in range(4)] for g in range(6)}


def test_infinite_expression_values_are_rejected(tmp_path):
    rows = dict(GOOD, G2=["1", "inf", "3", "4"])
    design = _design(tmp_path, ["batch"], [["0", "1", "0", "1"]])
    with pytest.raises(ValueError, match=r"expression values must be finite: 1 infinite values in 1 genes: G2"):
        load_cobra_inputs(_expression(tmp_path, rows), design)


def test_constant_genes_are_rejected_by_name(tmp_path):
    rows = dict(GOOD, G3=["5", "5", "5", "5"])
    report, ok = inspect_cobra_inputs_impl(_expression(tmp_path, rows), _design(tmp_path, ["batch"], [["0", "1", "0", "1"]]))
    assert not ok
    assert "error: expression has 1 constant genes (zero variance across samples): G3. COBRA standardizes" in report


def test_constant_covariate_is_rejected_but_intercept_is_allowed(tmp_path):
    expression = _expression(tmp_path, GOOD)
    report, ok = inspect_cobra_inputs_impl(
        expression, _design(tmp_path, ["intercept", "batch", "site"], [["1"] * 4, ["0", "1", "0", "1"], ["2"] * 4]))
    assert not ok and "constant columns are collinear with the intercept: site" in report
    _, ok = inspect_cobra_inputs_impl(expression, _design(tmp_path, ["intercept", "batch"], [["1"] * 4, ["0", "1", "0", "1"]]))
    assert ok


def test_intercept_column_must_be_ones(tmp_path):
    report, ok = inspect_cobra_inputs_impl(
        _expression(tmp_path, GOOD), _design(tmp_path, ["intercept", "batch"], [["2"] * 4, ["0", "1", "0", "1"]]))
    assert not ok and "design intercept column must contain only ones" in report


def test_cobra_toy_bundle_still_passes():
    _, ok = inspect_cobra_inputs_impl(str(TOY / "expression.tsv"), str(TOY / "design.tsv"))
    assert ok


def test_large_offset_covariate_is_not_called_constant(tmp_path):
    """np.allclose's relative tolerance called 20200101..20200104 constant (review 2026-11-05)."""
    report, _ = inspect_cobra_inputs_impl(
        _expression(tmp_path, GOOD),
        _design(tmp_path, ["collection_date"], [["20200101", "20200102", "20200103", "20200104"]]),
    )
    assert "collinear with the intercept" not in report
