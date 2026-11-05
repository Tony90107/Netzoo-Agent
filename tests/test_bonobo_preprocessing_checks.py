"""BONOBO preprocessing declarations are checked against the values, not only the wording."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.bonobo import inspect_bonobo_inputs_impl, load_bonobo_inputs  # noqa: E402

TOY = Path(__file__).parents[1] / "data" / "bonobo-toy" / "expression.tsv"


def _write(path: Path, values: np.ndarray) -> str:
    samples = [f"s{index}" for index in range(values.shape[1])]
    rows = ["gene_id\t" + "\t".join(samples)]
    rows += [f"g{row}\t" + "\t".join(repr(float(v)) for v in values[row]) for row in range(values.shape[0])]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


def test_raw_counts_declared_log_transformed_are_refused_with_the_numbers(tmp_path):
    counts = np.random.default_rng(0).poisson(400, size=(20, 6)).astype(float)
    path = _write(tmp_path / "counts.tsv", counts)
    with pytest.raises(ValueError, match=r"look like raw counts: all 120 values are non-negative, 100\.0% are whole"):
        load_bonobo_inputs(path, log_transformed=True, centered=True)
    report, ok = inspect_bonobo_inputs_impl(path, log_transformed=True, centered=True)
    assert not ok
    assert "log2(count + 1)" in report and f"maximum is {counts.max():g}" in report


def test_log_scale_values_pass_the_count_check(tmp_path):
    logged = np.log2(np.random.default_rng(1).poisson(400, size=(20, 6)) + 1.0)
    centered = logged - logged.mean(axis=1, keepdims=True)
    path = _write(tmp_path / "log.tsv", centered)
    bundle = load_bonobo_inputs(path, log_transformed=True, centered=True)
    assert len(bundle.gene_ids) == 20
    report, ok = inspect_bonobo_inputs_impl(path, log_transformed=True, centered=True)
    assert ok and "warning: expression is declared centered" not in report


def test_uncentered_values_declared_centered_are_reported_not_refused(tmp_path):
    # Upstream BONOBO subtracts each gene's mean itself, so this is a warning with the numbers.
    values = np.log2(np.random.default_rng(2).poisson(400, size=(20, 6)) + 1.0)
    path = _write(tmp_path / "uncentered.tsv", values)
    report, ok = inspect_bonobo_inputs_impl(path, log_transformed=True, centered=True)
    assert ok
    assert "warning: expression is declared centered, but per-gene means are not near zero" in report
    assert "median |gene mean| is" in report and "BONOBO subtracts each gene's mean itself" in report


def test_toy_demo_bundle_still_inspects_cleanly():
    _, ok = inspect_bonobo_inputs_impl(str(TOY), log_transformed=True, centered=True)
    assert ok
