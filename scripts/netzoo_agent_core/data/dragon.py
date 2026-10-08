"""Strict file and artifact contracts for the two-layer DRAGON workflow."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from .paths import _resolve_user_path

DRAGON_OUTPUT_FORMATS = ("matrix", "edge_list")
EDGE_COLUMNS = ["source", "target", "partial_correlation", "precision"]
PVALUE_COLUMNS = ["p_value", "adj_p_value"]


def _delimiter(path: Path) -> str:
    return "," if path.suffix.casefold() == ".csv" else "\t"


def _read_layer(path_value: str, label: str) -> tuple[pd.DataFrame | None, list[str]]:
    errors: list[str] = []
    if not path_value:
        return None, [f"{label} is missing."]
    path = _resolve_user_path(path_value)
    if path.suffix.casefold() not in {".csv", ".tsv", ".tab", ".txt"}:
        errors.append(f"{label} must be a CSV/TSV/TAB/TXT table: {path}")
        return None, errors
    if not path.is_file():
        return None, [f"{label} is missing or not a regular file: {path}"]
    try:
        frame = pd.read_csv(path, sep=_delimiter(path), header=0, dtype=object)
    except Exception as error:  # noqa: BLE001 - parse failures are typed validation data.
        return None, [f"{label} could not be parsed with a header: {error}"]
    if frame.empty or frame.shape[1] < 2:
        return None, [f"{label} must have a sample ID column and at least one feature column."]

    sample_column = str(frame.columns[0]).strip()
    feature_ids = [str(value).strip() for value in frame.columns[1:]]
    if not sample_column or sample_column.casefold().startswith("unnamed"):
        errors.append(f"{label} must have a named first sample-ID column.")
    if any(not value or value.casefold() in {"nan", "none"} for value in feature_ids):
        errors.append(f"{label} has an empty feature identifier in its header.")
    duplicated_features = sorted({value for value in feature_ids if feature_ids.count(value) > 1})
    if duplicated_features:
        errors.append(
            f"{label} contains duplicate feature IDs: {', '.join(duplicated_features[:5])}."
        )
    numeric_feature_ids = pd.to_numeric(feature_ids, errors="coerce")
    if feature_ids and bool(np.isfinite(numeric_feature_ids).all()):
        errors.append(f"{label} appears to have no feature header; feature IDs must be column names.")

    sample_ids = frame.iloc[:, 0].astype(str).str.strip()
    invalid_samples = sample_ids.isin({"", "nan", "none", "null"})
    if invalid_samples.any():
        errors.append(f"{label} contains empty sample identifiers.")
    duplicated_samples = sorted(sample_ids[sample_ids.duplicated()].unique().tolist())
    if duplicated_samples:
        errors.append(
            f"{label} contains duplicate sample IDs: {', '.join(duplicated_samples[:5])}."
        )

    values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        errors.append(
            f"{label} contains missing or non-numeric values; DRAGON requires complete continuous data."
        )
    elif not np.isfinite(values.to_numpy(dtype=float)).all():
        errors.append(f"{label} contains non-finite values; use finite continuous measurements.")
    elif (values.var(axis=0, ddof=0) == 0).any():
        errors.append(f"{label} contains zero-variance features; remove them before DRAGON.")
    if len(frame) < 3:
        errors.append(f"{label} must contain at least three samples for covariance estimation.")
    if errors:
        return None, errors
    values.index = sample_ids
    values.columns = feature_ids
    values.index.name = sample_column
    return values, []


def load_and_align_dragon_layers(
    layer1_path: str,
    layer2_path: str,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, list[str]]:
    """Load two sample-by-feature tables and align layer 2 to layer 1 samples."""
    layer1, errors1 = _read_layer(layer1_path, "omics_layer_1")
    layer2, errors2 = _read_layer(layer2_path, "omics_layer_2")
    errors = [*errors1, *errors2]
    if layer1 is None or layer2 is None:
        return layer1, layer2, errors
    ids1, ids2 = set(layer1.index), set(layer2.index)
    if ids1 != ids2:
        only1 = ", ".join(sorted(ids1 - ids2)[:5]) or "none"
        only2 = ", ".join(sorted(ids2 - ids1)[:5]) or "none"
        errors.append(
            "omics layers must have exactly the same sample IDs; "
            f"only in layer 1: {only1}; only in layer 2: {only2}."
        )
        return layer1, layer2, errors
    return layer1, layer2.loc[layer1.index], errors


def inspect_dragon_inputs_impl(layer1_path: str, layer2_path: str) -> tuple[str, bool]:
    """Return a side-effect-free, DRAGON-specific input report."""
    layer1, layer2, errors = load_and_align_dragon_layers(layer1_path, layer2_path)
    lines = [
        "DRAGON input contract:",
        "- two independent sample-by-feature CSV/TSV tables with a header",
        "- first column: unique sample IDs; remaining column names: unique feature IDs",
        "- all measurement cells must be finite continuous numeric values; no missing values",
        "- layer 2 is reordered to layer 1 sample order only after exact ID-set validation",
        "- sample metadata, motif, PPI, expression, and three-or-more-layer inputs are not consumed",
    ]
    if layer1 is not None:
        lines.append(f"- omics_layer_1: {layer1.shape[0]} samples x {layer1.shape[1]} features")
    if layer2 is not None:
        lines.append(f"- omics_layer_2: {layer2.shape[0]} samples x {layer2.shape[1]} features")
    if errors:
        lines.extend(f"  error: {error}" for error in errors)
    else:
        lines.append("- status: both layers are valid and sample-aligned")
    return "\n".join(lines), not errors


def _output_separator(path: Path) -> str:
    return "," if path.suffix.casefold() == ".csv" else "\t"


def _node_ids(layer1: pd.DataFrame, layer2: pd.DataFrame) -> list[str]:
    return [f"layer1::{value}" for value in layer1.columns] + [
        f"layer2::{value}" for value in layer2.columns
    ]


def write_dragon_matrix(output_path: str, matrix: np.ndarray, node_ids: list[str]) -> str:
    path = _resolve_user_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(matrix, index=node_ids, columns=node_ids)
    frame.index.name = "node_id"
    frame.to_csv(path, sep=_output_separator(path), float_format="%.12g")
    return str(path)


def dragon_pvalue_paths(output_path: str) -> tuple[Path, Path]:
    """Where a matrix-format run writes its raw and adjusted p-value matrices (Log 386)."""
    path = _resolve_user_path(output_path)
    return (path.with_name(f"{path.stem}.pvalues{path.suffix}"),
            path.with_name(f"{path.stem}.adj_pvalues{path.suffix}"))


def estimate_dragon_pvalues(api, partial, x1, x2, lambdas):
    """Edge p-values and BH-adjusted p-values, or why there are none (Log 386).

    netZooPy estimates the null's degrees of freedom (kappa) from simulated data,
    which fails when the features far outnumber the samples; the network is still
    written then, and the run says why it has no p-values.
    """
    try:
        adjusted, pvalues = api.estimate_p_values_dragon(
            partial, x1.shape[0], x1.shape[1], x2.shape[1], lambdas
        )
    except Exception as error:  # noqa: BLE001 - p-values are optional; the network stands.
        return None, None, f"p-values: not estimated ({type(error).__name__}: {error})"
    return pvalues, adjusted, (
        "p-values: written; adjusted with Benjamini-Hochberg separately within layer 1, "
        "within layer 2 and across the layers"
    )


def write_dragon_pvalue_matrices(
    output_path: str, pvalues: np.ndarray, adjusted: np.ndarray, node_ids: list[str]
) -> list[str]:
    """Labeled p-value matrices beside the network; the diagonal is not an edge and is left empty."""
    written = []
    for path, matrix in zip(dragon_pvalue_paths(output_path), (pvalues, adjusted)):
        values = np.array(matrix, dtype=float)
        np.fill_diagonal(values, np.nan)
        frame = pd.DataFrame(values, index=node_ids, columns=node_ids)
        frame.index.name = "node_id"
        frame.to_csv(path, sep=_output_separator(path), float_format="%.12g")
        written.append(str(path))
    return written


def write_dragon_edge_list(
    output_path: str,
    partial: np.ndarray,
    precision: np.ndarray,
    node_ids: list[str],
    pvalues: np.ndarray | None = None,
    adjusted: np.ndarray | None = None,
) -> str:
    path = _resolve_user_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with_p = pvalues is not None and adjusted is not None
    columns = EDGE_COLUMNS + (PVALUE_COLUMNS if with_p else [])
    rows = [
        {
            "source": node_ids[left],
            "target": node_ids[right],
            "partial_correlation": float(partial[left, right]),
            "precision": float(precision[left, right]),
            **({"p_value": float(pvalues[left, right]),
                "adj_p_value": float(adjusted[left, right])} if with_p else {}),
        }
        for left, right in combinations(range(len(node_ids)), 2)
    ]
    pd.DataFrame(rows, columns=columns).to_csv(
        path, sep=_output_separator(path), index=False, float_format="%.12g"
    )
    return str(path)


def write_dragon_outputs(output_path, output_format, partial, precision, node_ids, pvalues, adjusted) -> str:
    """The network in the requested format, with its p-values when they were estimated (Log 386)."""
    if output_format != "matrix":
        return write_dragon_edge_list(output_path, partial, precision, node_ids, pvalues, adjusted)
    written = [write_dragon_matrix(output_path, partial, node_ids)]
    if pvalues is not None:
        written += write_dragon_pvalue_matrices(output_path, pvalues, adjusted, node_ids)
    return ", ".join(written)


def _pvalues_in_range(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all() and (values >= 0).all() and (values <= 1).all())


def validate_dragon_pvalue_matrix(path: Path, nodes: int) -> list[str]:
    """A labeled square p-value matrix: empty diagonal, symmetric off-diagonal values in [0, 1]."""
    try:
        frame = pd.read_csv(path, sep=_delimiter(path), header=0)
    except Exception as error:  # noqa: BLE001 - malformed output is a typed result.
        return [f"DRAGON p-value matrix could not be parsed: {path.name}: {error}"]
    values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if values.shape != (nodes, nodes):
        return [f"DRAGON p-value matrix {path.name} must match the {nodes}-node network."]
    off = ~np.eye(nodes, dtype=bool)
    if not _pvalues_in_range(values[off]) or not np.allclose(values[off], values.T[off]):
        return [f"DRAGON p-value matrix {path.name} must hold symmetric values in [0, 1] off the diagonal."]
    return []


def validate_dragon_output(path_value: str, output_format: str) -> tuple[bool, list[str], dict[str, int | str]]:
    """Validate one labeled DRAGON matrix or one undirected edge list."""
    errors: list[str] = []
    metrics: dict[str, int | str] = {"output_format": output_format}
    path = _resolve_user_path(path_value)
    if not path.is_file() or path.stat().st_size == 0:
        return False, [f"DRAGON output is missing or empty: {path}"], metrics
    try:
        frame = pd.read_csv(path, sep=_delimiter(path), header=0)
    except Exception as error:  # noqa: BLE001 - malformed output is a typed result.
        return False, [f"DRAGON output could not be parsed: {error}"], metrics
    if output_format == "matrix":
        if frame.shape[1] < 2 or frame.columns[0] != "node_id":
            errors.append("DRAGON matrix must have a node_id column followed by feature columns.")
        labels = frame.iloc[:, 0].astype(str) if not frame.empty else pd.Series(dtype=str)
        numeric = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce") if frame.shape[1] > 1 else pd.DataFrame()
        if frame.shape[0] != max(frame.shape[1] - 1, 0):
            errors.append("DRAGON matrix must be square after removing node_id.")
        if labels.duplicated().any():
            errors.append("DRAGON matrix node IDs must be unique.")
        if numeric.empty or numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
            errors.append("DRAGON matrix values must be finite numeric values.")
        elif not np.allclose(numeric.to_numpy(dtype=float), numeric.to_numpy(dtype=float).T):
            errors.append("DRAGON partial-correlation matrix must be symmetric.")
        metrics["nodes"] = int(max(frame.shape[1] - 1, 0))
        pvalue_files = [p for p in dragon_pvalue_paths(path_value) if p.is_file()]
        metrics["p_values"] = "written" if len(pvalue_files) == 2 else "absent"
        if len(pvalue_files) == 1:
            errors.append("DRAGON wrote only one of its two p-value matrices.")
        for pvalue_path in pvalue_files if not errors else ():
            errors.extend(validate_dragon_pvalue_matrix(pvalue_path, int(metrics["nodes"])))
    elif output_format == "edge_list":
        with_p = list(frame.columns) == EDGE_COLUMNS + PVALUE_COLUMNS
        if list(frame.columns) != EDGE_COLUMNS and not with_p:
            errors.append(
                f"DRAGON edge list columns must be exactly: {', '.join(EDGE_COLUMNS)}"
                f" (optionally followed by {', '.join(PVALUE_COLUMNS)})."
            )
        else:
            if with_p and not _pvalues_in_range(
                frame[PVALUE_COLUMNS].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
            ):
                errors.append("DRAGON edge p-values must be in [0, 1].")
            metrics["p_values"] = "written" if with_p else "absent"
            if frame[["source", "target"]].isna().any().any():
                errors.append("DRAGON edge list source and target IDs must be non-empty.")
            numeric = frame[["partial_correlation", "precision"]].apply(pd.to_numeric, errors="coerce")
            if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
                errors.append("DRAGON edge weights must be finite numeric values.")
            if (frame["source"].astype(str) == frame["target"].astype(str)).any():
                errors.append("DRAGON edge list must not contain self-edges.")
            pairs = pd.Series(
                [
                    tuple(sorted((str(source), str(target))))
                    for source, target in zip(frame["source"], frame["target"])
                ],
                index=frame.index,
            )
            if pairs.duplicated().any():
                errors.append("DRAGON edge list must contain each undirected pair at most once.")
            metrics["edges"] = int(len(frame))
    else:
        errors.append(f"Unsupported DRAGON output format: {output_format}")
    return not errors, errors, metrics


__all__ = [
    "DRAGON_OUTPUT_FORMATS",
    "dragon_pvalue_paths",
    "estimate_dragon_pvalues",
    "write_dragon_outputs",
    "write_dragon_pvalue_matrices",
    "inspect_dragon_inputs_impl",
    "load_and_align_dragon_layers",
    "validate_dragon_output",
    "write_dragon_edge_list",
    "write_dragon_matrix",
]
