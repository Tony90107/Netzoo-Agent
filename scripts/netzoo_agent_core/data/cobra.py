"""COBRA-specific input validation and sample alignment."""

from __future__ import annotations

from pathlib import Path

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
    if design_values.isna().any().any():
        errors.append("design covariate values must all be numeric; encode categories first")
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
