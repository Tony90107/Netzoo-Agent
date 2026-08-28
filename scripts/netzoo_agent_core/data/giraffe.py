"""Strict file adapters for the source-verified netZooPy GIRAFFE API.

GIRAFFE itself accepts in-memory NumPy arrays/DataFrames, not file paths.  This
module owns the explicit conversion from the agent's labelled text contracts to
the three matrices required by ``netZooPy.giraffe.Giraffe``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from netzoo_table_io import read_table, table_read_info

from .paths import _resolve_user_path

__all__ = [
    "GiraffeInputBundle",
    "GiraffeInputError",
    "giraffe_output_paths",
    "inspect_giraffe_inputs_impl",
    "load_giraffe_inputs",
    "validate_giraffe_output",
    "write_giraffe_outputs",
]


_ID_TOKENS = {"id", "gene", "gene_id", "tf", "tf_id", "regulator", "node_id"}
_EDGE_HEADER_TOKENS = {
    ("source", "target"),
    ("regulator", "gene"),
    ("tf", "gene"),
    ("tf1", "tf2"),
}


class GiraffeInputError(ValueError):
    """A user-correctable GIRAFFE input contract failure."""


@dataclass(frozen=True, slots=True)
class GiraffeInputBundle:
    expression: np.ndarray
    prior: np.ndarray
    ppi: np.ndarray
    gene_ids: tuple[str, ...]
    sample_ids: tuple[str, ...]
    tf_ids: tuple[str, ...]


def _read(path_value: str, label: str, min_fields: int = 2) -> pd.DataFrame:
    if not path_value:
        raise GiraffeInputError(f"{label} path is missing.")
    path = _resolve_user_path(path_value)
    if not path.exists():
        raise GiraffeInputError(f"{label} file not found: {path}")
    if not path.is_file():
        raise GiraffeInputError(f"{label} path is not a regular file: {path}")
    try:
        info = table_read_info(path, min_fields=min_fields)
        frame = read_table(path, min_fields=min_fields)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise GiraffeInputError(
            f"{label} could not be parsed as a delimited table: {error}"
        ) from error
    if frame.empty or frame.shape[1] < min_fields:
        raise GiraffeInputError(
            f"{label} is empty or has fewer than {min_fields} columns "
            f"(detected delimiter: {info.delimiter_name})."
        )
    return frame


def _clean_ids(
    values: pd.Series | list[str], label: str, *, unique: bool = True
) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in values)
    invalid = {"", "nan", "none", "null"}
    if any(value.casefold() in invalid for value in ids):
        raise GiraffeInputError(f"{label} contains an empty identifier.")
    if unique and len(set(ids)) != len(ids):
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        raise GiraffeInputError(
            f"{label} contains duplicate identifiers: {', '.join(duplicates[:5])}."
        )
    return ids


def _numeric(frame: pd.DataFrame, label: str) -> np.ndarray:
    values = frame.apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        raise GiraffeInputError(f"{label} contains missing or non-numeric values.")
    array = values.to_numpy(dtype=float)
    if not np.isfinite(array).all():
        raise GiraffeInputError(f"{label} contains non-finite numeric values.")
    return array


def _looks_like_header(frame: pd.DataFrame) -> bool:
    if frame.shape[0] < 2 or frame.shape[1] < 2:
        return False
    first = [str(value).strip().casefold() for value in frame.iloc[0].tolist()]
    if first[0] in _ID_TOKENS:
        return True
    return not pd.to_numeric(frame.iloc[0, 1:], errors="coerce").notna().all()


def _read_expression(path_value: str) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    frame = _read(path_value, "GIRAFFE expression", min_fields=3)
    has_header = _looks_like_header(frame)
    if has_header:
        sample_ids = _clean_ids(list(frame.iloc[0, 1:]), "expression sample IDs")
        data = frame.iloc[1:].reset_index(drop=True)
    else:
        sample_ids = tuple(f"sample_{index}" for index in range(1, frame.shape[1]))
        data = frame
    gene_ids = _clean_ids(data.iloc[:, 0], "expression gene IDs")
    if len(sample_ids) < 2:
        raise GiraffeInputError("expression requires at least two sample columns.")
    values = _numeric(data.iloc[:, 1:], "expression matrix")
    if values.shape[0] < 2:
        raise GiraffeInputError("expression requires at least two genes.")
    return values, gene_ids, sample_ids


def _edge_header(frame: pd.DataFrame) -> bool:
    if frame.shape[1] < 2:
        return False
    first = tuple(str(value).strip().casefold() for value in frame.iloc[0, :2])
    if first == ("tf1", "tf2"):
        return frame.shape[1] >= 3 and pd.isna(
            pd.to_numeric(frame.iloc[0, 2], errors="coerce")
        )
    return first in _EDGE_HEADER_TOKENS or first == ("source", "target")


def _read_prior(path_value: str, gene_ids: tuple[str, ...]) -> tuple[np.ndarray, tuple[str, ...]]:
    frame = _read(path_value, "GIRAFFE motif/prior", min_fields=3)
    edge = frame.shape[1] == 3 and (
        _edge_header(frame)
        or not pd.isna(pd.to_numeric(frame.iloc[0, 2], errors="coerce"))
    )
    if edge:
        if _edge_header(frame):
            frame = frame.iloc[1:].reset_index(drop=True)
        if frame.empty:
            raise GiraffeInputError("motif/prior edge list has no data rows.")
        sources = _clean_ids(frame.iloc[:, 0], "motif/prior regulator IDs", unique=False)
        targets = _clean_ids(frame.iloc[:, 1], "motif/prior gene IDs", unique=False)
        weights = _numeric(frame.iloc[:, 2:].iloc[:, :1], "motif/prior weights")[:, 0]
        if len(set(zip(sources, targets))) != len(sources):
            raise GiraffeInputError("motif/prior edge list contains duplicate regulator-gene pairs.")
        if set(targets) != set(gene_ids):
            missing = sorted(set(gene_ids) - set(targets))
            extra = sorted(set(targets) - set(gene_ids))
            raise GiraffeInputError(
                "motif/prior gene IDs must exactly match expression gene IDs; "
                f"missing={missing[:5] or 'none'}, extra={extra[:5] or 'none'}."
            )
        tf_ids = tuple(dict.fromkeys(sources))
        matrix = np.zeros((len(tf_ids), len(gene_ids)), dtype=float)
        tf_index = {value: index for index, value in enumerate(tf_ids)}
        gene_index = {value: index for index, value in enumerate(gene_ids)}
        for source, target, weight in zip(sources, targets, weights):
            matrix[tf_index[source], gene_index[target]] = weight
    else:
        if not _looks_like_header(frame):
            raise GiraffeInputError(
                "motif/prior must be either a three-column regulator-gene-weight "
                "edge list or a labelled TF-by-gene matrix with a header."
            )
        columns = _clean_ids(list(frame.iloc[0, 1:]), "motif/prior gene IDs")
        data = frame.iloc[1:].reset_index(drop=True)
        if set(columns) != set(gene_ids) or len(columns) != len(gene_ids):
            raise GiraffeInputError("motif/prior matrix gene headers must exactly match expression gene IDs.")
        tf_ids = _clean_ids(data.iloc[:, 0], "motif/prior regulator IDs")
        matrix = _numeric(data.iloc[:, 1:], "motif/prior matrix")
        matrix = matrix[:, [columns.index(gene) for gene in gene_ids]]
    if not np.isfinite(matrix).all() or np.linalg.norm(matrix) == 0:
        raise GiraffeInputError("motif/prior matrix must be finite and contain at least one non-zero value.")
    return matrix, tf_ids


def _read_ppi(path_value: str, tf_ids: tuple[str, ...]) -> np.ndarray:
    frame = _read(path_value, "GIRAFFE PPI", min_fields=2)
    tf_set = set(tf_ids)
    dense = (
        frame.shape[0] == frame.shape[1] - 1
        and frame.shape[1] >= 3
        and str(frame.iloc[0, 0]).strip().casefold() in _ID_TOKENS
    )
    if dense:
        columns = _clean_ids(list(frame.iloc[0, 1:]), "PPI matrix column IDs")
        rows = _clean_ids(frame.iloc[1:, 0], "PPI matrix row IDs")
        if set(columns) != tf_set or set(rows) != tf_set or columns != rows:
            raise GiraffeInputError("PPI matrix row/column IDs must exactly match motif/prior TF IDs in the same order.")
        matrix = _numeric(frame.iloc[1:, 1:], "PPI matrix")
    else:
        if _edge_header(frame):
            frame = frame.iloc[1:].reset_index(drop=True)
        if frame.shape[1] not in {2, 3}:
            raise GiraffeInputError("PPI must be a two/three-column edge list or a labelled square matrix.")
        if frame.empty:
            raise GiraffeInputError("PPI edge list has no data rows.")
        sources = _clean_ids(frame.iloc[:, 0], "PPI source IDs", unique=False)
        targets = _clean_ids(frame.iloc[:, 1], "PPI target IDs", unique=False)
        if not set(sources) | set(targets) == tf_set:
            unknown = sorted((set(sources) | set(targets)) - tf_set)
            missing = sorted(tf_set - (set(sources) | set(targets)))
            raise GiraffeInputError(
                "PPI identifiers must cover exactly the motif/prior TF set; "
                f"missing={missing[:5] or 'none'}, unknown={unknown[:5] or 'none'}."
            )
        if frame.shape[1] == 3:
            weights = _numeric(frame.iloc[:, 2:].iloc[:, :1], "PPI weights")[:, 0]
        else:
            weights = np.ones(len(frame), dtype=float)
        unordered = [tuple(sorted(pair)) for pair in zip(sources, targets)]
        if len(set(unordered)) != len(unordered):
            raise GiraffeInputError("PPI edge list contains duplicate undirected pairs.")
        matrix = np.eye(len(tf_ids), dtype=float)
        index = {value: position for position, value in enumerate(tf_ids)}
        for source, target, weight in zip(sources, targets, weights):
            if source == target and weight != 1:
                raise GiraffeInputError("PPI diagonal entries must be exactly one.")
            matrix[index[source], index[target]] = weight
            matrix[index[target], index[source]] = weight
    if matrix.shape != (len(tf_ids), len(tf_ids)):
        raise GiraffeInputError("PPI must be square with one row and column per motif/prior TF.")
    if not np.isfinite(matrix).all():
        raise GiraffeInputError("PPI must contain only finite numeric values.")
    if not np.allclose(matrix, matrix.T):
        raise GiraffeInputError("PPI must be symmetrical.")
    if not np.allclose(np.diag(matrix), 1.0):
        raise GiraffeInputError("PPI diagonal entries must be exactly one.")
    return matrix


def load_giraffe_inputs(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
) -> GiraffeInputBundle:
    """Load and align labelled files into GIRAFFE's exact matrix contract."""
    expression, gene_ids, sample_ids = _read_expression(expression_file)
    prior, tf_ids = _read_prior(motif_file, gene_ids)
    ppi = _read_ppi(ppi_file, tf_ids)
    return GiraffeInputBundle(
        expression=expression,
        prior=prior,
        ppi=ppi,
        gene_ids=gene_ids,
        sample_ids=sample_ids,
        tf_ids=tf_ids,
    )


def inspect_giraffe_inputs_impl(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
) -> tuple[str, bool]:
    lines = [
        "GIRAFFE input contract:",
        "- expression: gene-by-sample numeric matrix; first column contains gene IDs",
        "- motif/prior: three-column regulator-gene-weight edge list or labelled TF-by-gene matrix",
        "- PPI: two/three-column TF edge list or labelled square TF matrix; diagonal must be one and matrix symmetrical",
        "- expression genes, motif/prior genes, and PPI/motif TF identifiers must be exactly compatible",
        "- files are converted to NumPy arrays because the verified GIRAFFE API does not accept file paths",
    ]
    try:
        bundle = load_giraffe_inputs(expression_file, motif_file, ppi_file)
    except GiraffeInputError as error:
        lines.append(f"error: {error}")
        return "\n".join(lines), False
    lines.extend(
        [
            f"- expression shape: genes={len(bundle.gene_ids)}, samples={len(bundle.sample_ids)}",
            f"- prior shape: TFs={len(bundle.tf_ids)}, genes={len(bundle.gene_ids)}",
            f"- PPI shape: TFs={bundle.ppi.shape[0]} x {bundle.ppi.shape[1]}",
            "- status: inputs are valid, finite, and identifier-compatible",
        ]
    )
    return "\n".join(lines), True


def giraffe_output_paths(output_file: str) -> tuple[Path, Path]:
    regulation = _resolve_user_path(output_file)
    suffix = regulation.suffix or ".tsv"
    tfa = regulation.with_name(f"{regulation.stem}.tfa{suffix}")
    return regulation, tfa


def write_giraffe_outputs(
    output_file: str,
    regulation: np.ndarray,
    tfa: np.ndarray,
    bundle: GiraffeInputBundle,
) -> tuple[str, str]:
    regulation_path, tfa_path = giraffe_output_paths(output_file)
    regulation_path.parent.mkdir(parents=True, exist_ok=True)
    separator = "," if regulation_path.suffix.casefold() == ".csv" else "\t"
    pd.DataFrame(regulation, index=bundle.tf_ids, columns=bundle.gene_ids).rename_axis(
        "tf_id"
    ).to_csv(regulation_path, sep=separator, float_format="%.12g")
    pd.DataFrame(tfa, index=bundle.tf_ids, columns=bundle.sample_ids).rename_axis(
        "tf_id"
    ).to_csv(tfa_path, sep=separator, float_format="%.12g")
    return str(regulation_path), str(tfa_path)


def _validate_labeled_matrix(
    path: Path,
    label: str,
    expected_rows: tuple[str, ...],
    expected_columns: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    if not path.is_file() or path.stat().st_size == 0:
        return [f"{label} output is missing or empty: {path}"]
    try:
        separator = "," if path.suffix.casefold() == ".csv" else "\t"
        frame = pd.read_csv(path, sep=separator)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        return [f"{label} output could not be parsed: {error}"]
    if frame.empty or frame.columns[0] != "tf_id":
        errors.append(f"{label} output must start with a tf_id column.")
        return errors
    rows = _clean_ids(frame.iloc[:, 0], f"{label} output TF IDs")
    columns = tuple(str(value).strip() for value in frame.columns[1:])
    if rows != expected_rows:
        errors.append(f"{label} output TF IDs do not match the validated motif/prior order.")
    if columns != expected_columns:
        errors.append(f"{label} output columns do not match the validated input identifiers and order.")
    if frame.shape[1] != len(expected_columns) + 1 or frame.shape[0] != len(expected_rows):
        errors.append(f"{label} output shape is {frame.shape}; expected {len(expected_rows)} x {len(expected_columns)} data values.")
    if frame.shape[1] > 1:
        values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            errors.append(f"{label} output values must be finite numeric values.")
    return errors


def validate_giraffe_output(
    output_file: str,
    bundle: GiraffeInputBundle,
) -> tuple[bool, list[str], dict[str, int | str]]:
    regulation_path, tfa_path = giraffe_output_paths(output_file)
    errors = [
        *_validate_labeled_matrix(
            regulation_path, "GIRAFFE regulation", bundle.tf_ids, bundle.gene_ids
        ),
        *_validate_labeled_matrix(
            tfa_path, "GIRAFFE TFA", bundle.tf_ids, bundle.sample_ids
        ),
    ]
    return (
        not errors,
        errors,
        {
            "regulation_output": str(regulation_path),
            "tfa_output": str(tfa_path),
            "regulation_rows": len(bundle.tf_ids),
            "regulation_columns": len(bundle.gene_ids),
            "tfa_columns": len(bundle.sample_ids),
        },
    )
