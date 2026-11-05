"""COBRA-specific input validation and sample alignment."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .paths import _resolve_user_path

#: Samples COBRA needs; it also needs more genes than samples (`load_cobra_inputs`).
COBRA_MIN_SAMPLES = 2

__all__ = [
    "COBRA_MIN_SAMPLES",
    "gene_sample_error",
    "cobra_artifact_paths",
    "cobra_input_output_collisions",
    "inspect_cobra_inputs_impl",
    "load_cobra_inputs",
]


def gene_sample_error(genes: int, samples: int) -> str | None:
    """COBRA's covariance decomposition needs more genes than samples; shared by `load_cobra_inputs` and the
    request-level check (`workflow_conditions`, core decision phase 4a), so the rule lives in one place."""
    return "COBRA requires more genes than samples" if genes <= samples else None


_COBRA_ARTIFACT_NAMES = (
    "manifest.json",
    "components.npz",
    "summary.tsv",
    "adjusted_coexpression.tsv",
    "adjusted_coexpression.npz",
)


def cobra_artifact_paths(output_dir: str | Path) -> tuple[Path, ...]:
    """Resolve every fixed output produced by the COBRA wrapper."""
    root = _resolve_user_path(str(output_dir))
    return tuple((root / name).resolve() for name in _COBRA_ARTIFACT_NAMES)


def cobra_input_output_collisions(
    expression_file: str, design_file: str, output_dir: str | Path,
) -> tuple[Path, ...]:
    """Find declared inputs that COBRA would overwrite with a fixed artifact."""
    inputs = {_resolve_user_path(expression_file), _resolve_user_path(design_file)}
    return tuple(path for path in cobra_artifact_paths(output_dir) if path in inputs)


def _read_labeled_table(path: str, label: str) -> tuple[pd.DataFrame | None, list[str]]:
    resolved = _resolve_user_path(path)
    errors: list[str] = []
    try:
        frame = pd.read_csv(resolved, sep=None, engine="python", comment="#")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        return None, [f"{label} could not be read: {error}"]
    if frame.shape[1] < 2 or frame.empty:
        errors.append(f"{label} must have an ID column and at least one value column")
        return None, errors
    ids = frame.iloc[:, 0].astype(str).str.strip()
    if ids.eq("").any() or ids.duplicated().any():
        errors.append(f"{label} IDs in the first column must be non-empty and unique")
    return frame, errors


def _preview(names: list[str]) -> str:
    return ", ".join(names[:5]) + (f" (and {len(names) - 5} more)" if len(names) > 5 else "")


def _expression_value_errors(values: pd.DataFrame, gene_ids: pd.Series) -> list[str]:
    """Infinite values and constant genes, which upstream COBRA cannot standardize.

    netZooPy ``cobra`` centers each gene and divides it by its norm, so an
    infinite value poisons the co-expression and a constant gene divides 0 by 0.
    """
    array = values.to_numpy(dtype=float)
    ids = gene_ids.tolist()
    finite = np.isfinite(array)
    if not finite.all():
        bad = [ids[row] for row in np.flatnonzero(~finite.all(axis=1))]
        return [
            f"expression values must be finite: {int((~finite).sum())} infinite values in "
            f"{len(bad)} genes: {_preview(bad)}. Replace or remove them before running COBRA"
        ]
    constant = [ids[row] for row in np.flatnonzero(np.ptp(array, axis=1) == 0)] if array.shape[1] else []
    if constant:
        return [
            f"expression has {len(constant)} constant genes (zero variance across samples): "
            f"{_preview(constant)}. COBRA standardizes each gene by its spread, which is zero "
            "for these. Remove them before running COBRA"
        ]
    return []


def _design_value_errors(values: pd.DataFrame) -> list[str]:
    """The design checks run_cobra applies, surfaced at inspection time.

    run_cobra keeps an ``intercept`` column of ones (adding one when absent),
    so any other constant column is collinear with it.
    """
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array).all():
        return ["design covariate values must be finite"]
    errors: list[str] = []
    columns = [str(column).strip() for column in values.columns]
    if "intercept" in columns and not np.allclose(values.iloc[:, columns.index("intercept")], 1.0):
        errors.append("design intercept column must contain only ones")
    constant = [
        name for index, name in enumerate(columns)
        if name != "intercept" and np.ptp(array[:, index]) == 0
    ]
    if constant:
        errors.append(
            "design covariates must vary across samples; constant columns are collinear with "
            f"the intercept: {_preview(constant)}. Remove them (an intercept column of ones is "
            "allowed and is added automatically when absent)"
        )
    return errors


def load_cobra_inputs(expression_file: str, design_file: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return gene-by-sample expression and design aligned to expression columns."""
    expression, expression_errors = _read_labeled_table(expression_file, "expression")
    design, design_errors = _read_labeled_table(design_file, "design")
    errors = [*expression_errors, *design_errors]
    if expression is None or design is None:
        raise ValueError("; ".join(errors))
    expression_ids = expression.iloc[:, 0].astype(str).str.strip()
    sample_ids = [str(value).strip() for value in expression.columns[1:]]
    design_ids = design.iloc[:, 0].astype(str).str.strip()
    if len(set(sample_ids)) != len(sample_ids) or any(not value for value in sample_ids):
        errors.append("expression sample column names must be non-empty and unique")
    missing = sorted(set(sample_ids) - set(design_ids))
    extra = sorted(set(design_ids) - set(sample_ids))
    if missing or extra:
        errors.append(
            "design sample IDs must exactly match expression sample columns"
            + (f"; missing in design: {', '.join(missing[:5])}" if missing else "")
            + (f"; extra in design: {', '.join(extra[:5])}" if extra else "")
        )
    expression_values = expression.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    design_values = design.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    if expression_values.isna().any().any():
        errors.append("expression values must all be numeric")
    else:
        errors.extend(_expression_value_errors(expression_values, expression_ids))
    if design_values.isna().any().any():
        errors.append("design covariate values must all be numeric; encode categories first")
    else:
        errors.extend(_design_value_errors(design_values))
    if (error := gene_sample_error(*expression_values.shape)) is not None:
        errors.append(error)
    if expression_values.shape[1] < COBRA_MIN_SAMPLES:
        errors.append("COBRA requires at least two samples")
    if errors:
        raise ValueError("; ".join(errors))
    design_indexed = design_values.copy()
    design_indexed.index = design_ids
    aligned_design = design_indexed.loc[sample_ids].reset_index(drop=True)
    expression_values.index = expression_ids
    return expression_values, aligned_design


def inspect_cobra_inputs_impl(expression_file: str, design_file: str) -> tuple[str, bool]:
    """Validate the strict labelled matrix contract required by COBRA."""
    lines = ["COBRA input inspection:", f"- expression: {_resolve_user_path(expression_file)}", f"- design: {_resolve_user_path(design_file)}"]
    try:
        expression, design = load_cobra_inputs(expression_file, design_file)
    except ValueError as error:
        lines.extend(f"  error: {item.strip()}" for item in str(error).split(";"))
        return "\n".join(lines), False
    lines.extend(
        [
            "  sample IDs: expression columns and design rows match",
            f"  expression shape: {expression.shape[0]} genes x {expression.shape[1]} samples",
            f"  design shape: {design.shape[0]} samples x {design.shape[1]} covariates",
            "  note: run_cobra emits components plus an adjusted_coexpression.tsv/npz artifact.",
        ]
    )
    return "\n".join(lines), True
