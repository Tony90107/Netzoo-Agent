"""Strict OTTER input/output contracts and matrix preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .paths import _resolve_user_path

__all__ = [
    "OtterInputBundle",
    "inspect_otter_inputs_impl",
    "load_otter_inputs",
    "validate_otter_output",
    "write_otter_output",
]


@dataclass(frozen=True, slots=True)
class OtterInputBundle:
    """Validated arrays in the exact orientation required by netZooPy OTTER."""

    W: np.ndarray
    P: np.ndarray
    C: np.ndarray
    tf_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]
    source: str
    sample_count: int | None


def _path(path: str, label: str) -> Path:
    if not path:
        raise ValueError(f"{label} path is empty")
    resolved = _resolve_user_path(path)
    if not resolved.exists():
        raise ValueError(f"{label} file does not exist: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"{label} path is not a regular file: {resolved}")
    return resolved


def _read_raw(path: str, label: str) -> pd.DataFrame:
    resolved = _path(path, label)
    try:
        frame = pd.read_csv(
            resolved,
            sep=None,
            engine="python",
            header=None,
            comment="#",
        )
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"{label} could not be parsed as a delimited table: {error}") from error
    if frame.empty:
        raise ValueError(f"{label} table is empty")
    return frame


def _normalise_ids(values: object, label: str) -> list[str]:
    ids = [str(value).strip() for value in values]
    if not ids or any(not value or value.casefold() in {"nan", "none", "null"} for value in ids):
        raise ValueError(f"{label} must contain non-empty identifiers")
    if len(set(ids)) != len(ids):
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        raise ValueError(f"{label} contains duplicate identifiers: {duplicates[:5]}")
    return ids


def _normalise_edge_ids(values: object, label: str) -> list[str]:
    """Validate edge endpoint cells; repeated nodes are valid across edge rows."""
    ids = [str(value).strip() for value in values]
    if not ids or any(not value or value.casefold() in {"nan", "none", "null"} for value in ids):
        raise ValueError(f"{label} must contain non-empty identifiers")
    return ids


def _numeric(frame: pd.DataFrame, label: str) -> np.ndarray:
    values = frame.apply(pd.to_numeric, errors="coerce")
    array = values.to_numpy(dtype=float)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError(f"{label} values must all be finite and numeric; NA is not supported")
    if (values.isna().all(axis=1)).any() or (values.isna().all(axis=0)).any():
        raise ValueError(f"{label} contains an empty row or column")
    return array


def _drop_edge_header(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    if frame.shape[0] == 0:
        return frame
    first = [str(value).strip().casefold() for value in frame.iloc[0, :3]]
    header_tokens = {
        "tf", "regulator", "source", "protein1", "gene", "target", "weight", "exists"
    }
    third_numeric = pd.to_numeric(frame.iloc[0, 2], errors="coerce") if frame.shape[1] >= 3 else np.nan
    if any(value in header_tokens for value in first) or pd.isna(third_numeric):
        return frame.iloc[1:].reset_index(drop=True)
    return frame


def _read_edge_list(path: str, label: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    frame = _drop_edge_header(_read_raw(path, label), label)
    if frame.empty or frame.shape[1] < 3:
        raise ValueError(f"{label} must have at least three columns: source, target, weight")
    if frame.iloc[:, :3].isna().any().any():
        raise ValueError(f"{label} contains empty rows or columns")
    left = _normalise_edge_ids(frame.iloc[:, 0], f"{label} source IDs")
    right = _normalise_edge_ids(frame.iloc[:, 1], f"{label} target IDs")
    weights = _numeric(frame.iloc[:, 2:3], f"{label} weight")[:, 0]
    pairs = list(zip(left, right))
    if len(set(pairs)) != len(pairs):
        raise ValueError(f"{label} contains duplicate source-target pairs")
    parsed = pd.DataFrame({"left": left, "right": right, "weight": weights})
    return parsed, list(dict.fromkeys(left)), list(dict.fromkeys(right))


def _read_expression(path: str) -> tuple[pd.DataFrame, int]:
    resolved = _path(path, "expression")
    try:
        frame = pd.read_csv(resolved, sep=None, engine="python", header=0, comment="#")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"expression could not be parsed as a delimited table: {error}") from error
    if frame.empty or frame.shape[1] < 3:
        raise ValueError("expression must have a gene ID column and at least two sample columns")
    genes = _normalise_ids(frame.iloc[:, 0], "expression gene IDs")
    samples = _normalise_ids(frame.columns[1:], "expression sample IDs")
    if len(set(samples)) != len(samples):
        raise ValueError("expression contains duplicate sample IDs")
    values = _numeric(frame.iloc[:, 1:], "expression")
    if len(genes) != values.shape[0] or len(samples) != values.shape[1]:
        raise ValueError("expression identifiers do not match its numeric matrix shape")
    expression = pd.DataFrame(values, index=genes, columns=samples)
    return expression, len(samples)


def _read_coexpression(path: str) -> pd.DataFrame:
    resolved = _path(path, "co-expression")
    try:
        frame = pd.read_csv(resolved, sep=None, engine="python", header=0, comment="#")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"co-expression could not be parsed as a delimited table: {error}") from error
    if frame.empty or frame.shape[1] < 2:
        raise ValueError("co-expression must have a gene ID column and a non-empty square matrix")
    genes = _normalise_ids(frame.iloc[:, 0], "co-expression row IDs")
    columns = _normalise_ids(frame.columns[1:], "co-expression column IDs")
    if genes != columns:
        raise ValueError(
            "co-expression row and column gene order must match exactly; "
            "do not rely on implicit intersection/reordering"
        )
    values = _numeric(frame.iloc[:, 1:], "co-expression")
    if values.shape != (len(genes), len(genes)):
        raise ValueError("co-expression matrix must be square")
    if not np.allclose(values, values.T, rtol=1e-7, atol=1e-8):
        raise ValueError("co-expression matrix must be symmetric")
    return pd.DataFrame(values, index=genes, columns=genes)


def _build_bundle(
    expression_file: str,
    coexpression_file: str,
    motif_file: str,
    ppi_file: str,
    precision: str,
) -> OtterInputBundle:
    if not expression_file and not coexpression_file:
        raise ValueError("provide expression_file or coexpression_file")
    if precision not in {"single", "double"}:
        raise ValueError("precision must be single or double")

    motif, motif_tfs, motif_genes = _read_edge_list(motif_file, "OTTER seed/prior")
    ppi, ppi_left, ppi_right = _read_edge_list(ppi_file, "PPI")
    ppi_ids = list(dict.fromkeys([*ppi_left, *ppi_right]))
    if set(ppi_ids) != set(motif_tfs):
        missing = sorted(set(motif_tfs) - set(ppi_ids))
        extra = sorted(set(ppi_ids) - set(motif_tfs))
        raise ValueError(
            "PPI must be a TF-TF network with exactly the OTTER seed TF IDs; "
            f"missing TFs={missing[:5]}, extra IDs={extra[:5]}"
        )
    if set(motif_tfs) & set(motif_genes):
        raise ValueError("OTTER seed/prior must be bipartite: TF IDs and gene IDs overlap")

    expression: pd.DataFrame | None = None
    sample_count: int | None = None
    if expression_file:
        expression, sample_count = _read_expression(expression_file)
        if set(expression.index) != set(motif_genes):
            missing = sorted(set(motif_genes) - set(expression.index))
            extra = sorted(set(expression.index) - set(motif_genes))
            raise ValueError(
                "expression and OTTER seed gene IDs must match exactly; "
                f"missing genes={missing[:5]}, extra genes={extra[:5]}"
            )
        if list(expression.index) != motif_genes:
            raise ValueError(
                "expression and OTTER seed gene order must match exactly; "
                "do not rely on implicit reordering"
            )

    if coexpression_file:
        coexpression = _read_coexpression(coexpression_file)
        if expression is not None and list(coexpression.index) != list(expression.index):
            raise ValueError("expression and co-expression gene order must match exactly")
    else:
        assert expression is not None
        coexpression_values = np.corrcoef(expression.to_numpy(dtype=float))
        if not np.isfinite(coexpression_values).all():
            raise ValueError("expression produced non-finite co-expression values; check constant rows or NA")
        coexpression = pd.DataFrame(
            coexpression_values,
            index=expression.index,
            columns=expression.index,
        )

    if list(coexpression.index) != list(motif_genes):
        missing = sorted(set(motif_genes) - set(coexpression.index))
        extra = sorted(set(coexpression.index) - set(motif_genes))
        raise ValueError(
            "co-expression and OTTER seed gene IDs must match exactly; "
            f"missing genes={missing[:5]}, extra genes={extra[:5]}"
        )

    tf_ids = tuple(motif_tfs)
    gene_ids = tuple(coexpression.index)
    w = np.zeros((len(tf_ids), len(gene_ids)), dtype=float)
    tf_index = {value: index for index, value in enumerate(tf_ids)}
    gene_index = {value: index for index, value in enumerate(gene_ids)}
    for row in motif.itertuples(index=False):
        w[tf_index[row.left], gene_index[row.right]] = float(row.weight)
    p = np.eye(len(tf_ids), dtype=float)
    for row in ppi.itertuples(index=False):
        p[tf_index[row.left], tf_index[row.right]] = 1.0
        p[tf_index[row.right], tf_index[row.left]] = 1.0
    dtype = np.float32 if precision == "single" else np.float64
    return OtterInputBundle(
        W=w.astype(dtype),
        P=p.astype(dtype),
        C=coexpression.to_numpy(dtype=dtype),
        tf_ids=tf_ids,
        gene_ids=gene_ids,
        source="precomputed co-expression" if coexpression_file else "expression-derived co-expression",
        sample_count=sample_count,
    )


def load_otter_inputs(
    expression_file: str = "",
    coexpression_file: str = "",
    motif_file: str = "",
    ppi_file: str = "",
    precision: str = "double",
) -> OtterInputBundle:
    """Validate and materialise W (TF×gene), P (TF×TF), and C (gene×gene)."""
    return _build_bundle(
        expression_file,
        coexpression_file,
        motif_file,
        ppi_file,
        precision,
    )


def inspect_otter_inputs_impl(
    expression_file: str = "",
    coexpression_file: str = "",
    motif_file: str = "",
    ppi_file: str = "",
    precision: str = "double",
) -> tuple[str, bool]:
    """Return a truthful, side-effect-free OTTER contract report."""
    lines = [
        "OTTER input inspection:",
        "- W / OTTER seed: TF-by-gene regulator-to-target edge list (not a PANDA motif input)",
        "- P: TF-by-TF PPI adjacency projection",
        "- C: gene-by-gene co-expression projection",
        "- merge policy: exact identifiers and exact gene order; no implicit intersection",
        "- NA policy: reject NA/non-finite values before the API call",
    ]
    try:
        bundle = _build_bundle(
            expression_file,
            coexpression_file,
            motif_file,
            ppi_file,
            precision,
        )
    except (OSError, ValueError) as error:
        lines.append(f"  error: {error}")
        return "\n".join(lines), False
    lines.extend(
        [
            f"- source: {bundle.source}",
            f"- W shape: {bundle.W.shape[0]} TFs x {bundle.W.shape[1]} genes",
            f"- P shape: {bundle.P.shape[0]} TFs x {bundle.P.shape[1]} TFs",
            f"- C shape: {bundle.C.shape[0]} genes x {bundle.C.shape[1]} genes",
            f"- TF identifiers: {', '.join(bundle.tf_ids[:5])}{' ...' if len(bundle.tf_ids) > 5 else ''}",
            f"- gene identifiers: {', '.join(bundle.gene_ids[:5])}{' ...' if len(bundle.gene_ids) > 5 else ''}",
        ]
    )
    if bundle.sample_count is not None:
        lines.append(f"- expression samples: {bundle.sample_count}")
    return "\n".join(lines), True


def write_otter_output(
    output_file: str,
    network: np.ndarray,
    tf_ids: tuple[str, ...],
    gene_ids: tuple[str, ...],
    output_format: str,
) -> str:
    """Write a labeled matrix or a complete TF→gene edge list."""
    if output_format not in {"matrix", "edge_list"}:
        raise ValueError("output_format must be matrix or edge_list")
    output = _resolve_user_path(output_file)
    if output.suffix.casefold() not in {".tsv", ".csv"}:
        raise ValueError("OTTER output_file must use .tsv or .csv so identifiers remain attached")
    array = np.asarray(network, dtype=float)
    if array.shape != (len(tf_ids), len(gene_ids)) or not np.isfinite(array).all():
        raise ValueError("OTTER result must be a finite TF-by-gene matrix with the declared shape")
    output.parent.mkdir(parents=True, exist_ok=True)
    separator = "," if output.suffix.casefold() == ".csv" else "\t"
    if output_format == "matrix":
        frame = pd.DataFrame(array, index=tf_ids, columns=gene_ids)
        frame.index.name = "tf"
        frame.to_csv(output, sep=separator, float_format="%.12g")
    else:
        rows = [
            (tf, gene, float(array[tf_index, gene_index]))
            for tf_index, tf in enumerate(tf_ids)
            for gene_index, gene in enumerate(gene_ids)
        ]
        pd.DataFrame(rows, columns=["source", "target", "weight"]).to_csv(
            output,
            sep=separator,
            index=False,
            float_format="%.12g",
        )
    return str(output)


def validate_otter_output(
    output_file: str,
    output_format: str,
    expected_tf_ids: tuple[str, ...] | None = None,
    expected_gene_ids: tuple[str, ...] | None = None,
) -> tuple[bool, list[str], dict[str, int | str]]:
    """Validate OTTER artifact orientation and its regulator/target partition."""
    errors: list[str] = []
    metrics: dict[str, int | str] = {}
    try:
        resolved = _path(output_file, "OTTER output")
        if output_format == "matrix":
            frame = pd.read_csv(resolved, sep=None, engine="python", header=0)
            if frame.shape[1] < 2:
                raise ValueError("matrix output must have a tf ID column and gene columns")
            row_ids = _normalise_ids(frame.iloc[:, 0], "OTTER matrix regulator IDs")
            gene_ids = _normalise_ids(frame.columns[1:], "OTTER matrix target IDs")
            values = _numeric(frame.iloc[:, 1:], "OTTER matrix")
            if values.shape != (len(row_ids), len(gene_ids)):
                raise ValueError("OTTER matrix output shape does not match its identifiers")
            if expected_tf_ids is not None and tuple(row_ids) != tuple(expected_tf_ids):
                raise ValueError("OTTER matrix regulator order does not match the declared TF layer")
            if expected_gene_ids is not None and tuple(gene_ids) != tuple(expected_gene_ids):
                raise ValueError("OTTER matrix target order does not match the declared gene layer")
            if set(row_ids) & set(gene_ids):
                raise ValueError("OTTER matrix is not bipartite: regulator and target IDs overlap")
            metrics.update({"otter_regulators": len(row_ids), "otter_targets": len(gene_ids), "otter_values": int(values.size)})
        elif output_format == "edge_list":
            frame = pd.read_csv(resolved, sep=None, engine="python", header=0)
            required = ["source", "target", "weight"]
            if list(frame.columns[:3]) != required:
                raise ValueError("OTTER edge-list output must have source, target, weight columns")
            source = _normalise_edge_ids(frame["source"], "OTTER edge-list source IDs")
            target = _normalise_edge_ids(frame["target"], "OTTER edge-list target IDs")
            weights = _numeric(frame[["weight"]], "OTTER edge-list weight")[:, 0]
            if len(set(zip(source, target))) != len(source):
                raise ValueError("OTTER edge-list output contains duplicate source-target pairs")
            source_ids = tuple(dict.fromkeys(source))
            target_ids = tuple(dict.fromkeys(target))
            if set(source_ids) & set(target_ids):
                raise ValueError("OTTER edge-list output is not bipartite: source and target IDs overlap")
            if expected_tf_ids is not None and set(source_ids) != set(expected_tf_ids):
                raise ValueError("OTTER edge-list source IDs do not match the declared TF layer")
            if expected_gene_ids is not None and set(target_ids) != set(expected_gene_ids):
                raise ValueError("OTTER edge-list target IDs do not match the declared gene layer")
            expected_pairs = len(source_ids) * len(target_ids)
            if len(frame) != expected_pairs:
                raise ValueError("OTTER edge-list must contain the complete TF-by-gene grid")
            metrics.update({"otter_regulators": len(source_ids), "otter_targets": len(target_ids), "otter_values": int(weights.size)})
        else:
            raise ValueError("output_format must be matrix or edge_list")
    except (OSError, ValueError, pd.errors.ParserError) as error:
        errors.append(str(error))
    return not errors, errors, metrics
