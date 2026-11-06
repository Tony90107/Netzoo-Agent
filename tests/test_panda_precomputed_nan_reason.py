"""PANDA with a precomputed co-expression file does not use expression values."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.tables import _read_checked_table, _validate_expression


def _expression_with_nan(tmp_path):
    values = np.random.default_rng(0).normal(size=(6, 4))
    values[2, 1] = np.nan
    frame = pd.DataFrame(values, index=[f"G{i}" for i in range(6)], columns=list("ABCD"))
    path = tmp_path / "expr.tsv"
    frame.to_csv(path, sep="\t", index_label="gene")
    return str(path)


def test_missing_value_refused_with_the_pearson_reason_by_default(tmp_path):
    check = _validate_expression(_read_checked_table("expression", _expression_with_nan(tmp_path)))
    assert any("zero co-expression" in error for error in check.errors)


def test_missing_value_is_a_note_when_coexpression_is_precomputed(tmp_path):
    check = _validate_expression(
        _read_checked_table("expression", _expression_with_nan(tmp_path)),
        precomputed_coexpression=True,
    )
    assert not any("missing" in error for error in check.errors)
    assert any("precomputed co-expression file given" in note for note in check.notes)
