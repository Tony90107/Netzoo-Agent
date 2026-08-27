"""Strict co-expression artifacts shared by COBRA and network runners.

The COBRA implementation returns a spectral decomposition rather than a
gene-by-gene matrix.  This module is the explicit boundary between those two
representations: it reconstructs the intercept (covariate-adjusted) component
and persists it with row and column gene identifiers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .paths import _resolve_user_path

__all__ = [
    "adjusted_coexpression_from_cobra",
    "read_expression_gene_ids",
    "read_coexpression_matrix",
    "write_adjusted_coexpression",
]


def _normalise_ids(values: object, label: str) -> list[str]:
    ids = [str(value).strip() for value in values]
    if not ids or any(not value for value in ids):
        raise ValueError(f"{label} must contain non-empty identifiers")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{label} must contain unique identifiers")
    return ids


def _validate_coexpression_frame(
    frame: pd.DataFrame,
    *,
    expected_gene_ids: list[str] | None = None,
    label: str = "co-expression matrix",
) -> pd.DataFrame:
    if frame.empty or frame.shape[1] < 2:
        raise ValueError(f"{label} must have an ID column and a non-empty matrix")
    row_ids = _normalise_ids(frame.iloc[:, 0], f"{label} row IDs")
    column_ids = _normalise_ids(frame.columns[1:], f"{label} column IDs")
    if set(row_ids) != set(column_ids):
        missing_columns = sorted(set(row_ids) - set(column_ids))
        missing_rows = sorted(set(column_ids) - set(row_ids))
        raise ValueError(
            f"{label} row/column gene IDs must match exactly; "
            f"missing columns={missing_columns[:5]}, missing rows={missing_rows[:5]}"
        )
    values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError(f"{label} values must all be finite and numeric")
    values.index = row_ids
    values.columns = column_ids
    values = values.loc[row_ids, row_ids]
    matrix = values.to_numpy(dtype=float)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{label} must be square")
    if not np.allclose(matrix, matrix.T, rtol=1e-7, atol=1e-8):
        raise ValueError(f"{label} must be symmetric")
    if expected_gene_ids is not None:
        expected = _normalise_ids(expected_gene_ids, "expected gene IDs")
        if set(row_ids) != set(expected):
            raise ValueError(
                f"{label} gene IDs must exactly match the expression gene IDs"
            )
        matrix = values.loc[expected, expected].to_numpy(dtype=float)
        values = pd.DataFrame(matrix, index=expected, columns=expected)
    return values


def read_coexpression_matrix(
    path: str,
    *,
    expected_gene_ids: list[str] | None = None,
) -> pd.DataFrame:
    """Read and strictly validate a labeled gene-by-gene co-expression TSV."""
    resolved = _resolve_user_path(path)
    try:
        frame = pd.read_csv(resolved, sep=None, engine="python", comment="#")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"co-expression matrix could not be read: {error}") from error
    return _validate_coexpression_frame(
        frame, expected_gene_ids=expected_gene_ids, label="co-expression matrix"
    )


def read_expression_gene_ids(path: str, *, with_header: bool = False) -> list[str]:
    """Read the row-axis IDs from a NetZoo expression matrix."""
    resolved = _resolve_user_path(path)
    try:
        frame = pd.read_csv(
            resolved,
            sep=None,
            engine="python",
            header=0 if with_header else None,
            comment="#",
        )
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"expression matrix could not be read: {error}") from error
    if frame.empty or frame.shape[1] < 2:
        raise ValueError("expression matrix must have an ID column and sample values")
    return _normalise_ids(frame.iloc[:, 0], "expression gene IDs")


def adjusted_coexpression_from_cobra(
    psi: np.ndarray,
    q: np.ndarray,
    gene_ids: list[str],
    design_columns: list[str],
    *,
    intercept_column: str = "intercept",
) -> pd.DataFrame:
    """Reconstruct COBRA's adjusted correlation component.

    COBRA represents each covariance component as ``Q diag(Psi[k, :]) Q.T``.
    With an intercept column, the intercept component is the covariance left
    after removing the modeled covariate-associated components.  We convert it
    to a correlation matrix because PANDA's expression-derived network input
    is a correlation network, then preserve the gene IDs at both axes.
    """
    psi = np.asarray(psi, dtype=float)
    q = np.asarray(q, dtype=float)
    genes = _normalise_ids(gene_ids, "COBRA gene IDs")
    columns = _normalise_ids(design_columns, "COBRA design columns")
    if psi.ndim != 2 or q.ndim != 2:
        raise ValueError("COBRA psi and Q must both be 2D arrays")
    if q.shape[0] != len(genes):
        raise ValueError("COBRA Q rows must equal the number of gene IDs")
    if psi.shape[0] != len(columns):
        raise ValueError("COBRA psi rows must equal the number of design columns")
    if psi.shape[1] != q.shape[1]:
        raise ValueError("COBRA psi and Q must have the same component count")
    if intercept_column not in columns:
        raise ValueError(
            f"COBRA design must contain an '{intercept_column}' column to reconstruct "
            "the adjusted co-expression component"
        )
    if not np.isfinite(psi).all() or not np.isfinite(q).all():
        raise ValueError("COBRA psi and Q must contain only finite values")

    intercept_index = columns.index(intercept_column)
    covariance = q @ np.diag(psi[intercept_index, :]) @ q.T
    covariance = (covariance + covariance.T) / 2.0
    diagonal = np.diag(covariance)
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0):
        raise ValueError(
            "COBRA adjusted covariance must have strictly positive gene variances"
        )
    scale = np.sqrt(np.outer(diagonal, diagonal))
    correlation = covariance / scale
    correlation = (correlation + correlation.T) / 2.0
    np.fill_diagonal(correlation, 1.0)
    return pd.DataFrame(correlation, index=genes, columns=genes)


def write_adjusted_coexpression(
    matrix: pd.DataFrame,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Persist the labeled TSV and an NPZ companion for a COBRA handoff."""
    checked = _validate_coexpression_frame(
        matrix.reset_index(names="gene_id"), label="adjusted co-expression matrix"
    )
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    tsv_path = root / "adjusted_coexpression.tsv"
    npz_path = root / "adjusted_coexpression.npz"
    output = checked.copy()
    output.insert(0, "gene_id", output.index)
    output.to_csv(tsv_path, sep="\t", index=False, float_format="%.12g")
    np.savez_compressed(
        npz_path,
        matrix=checked.to_numpy(dtype=float),
        gene_ids=np.asarray(checked.index.astype(str).tolist(), dtype="U"),
    )
    return tsv_path, npz_path
