"""Read and validate the SCORPION input contract (no side effects).

SCORPION (kuijjerlab/SCORPION, Osorio, Capasso & Kuijjer 2024) builds PANDA regulatory networks from
single-cell RNA-seq: it aggregates similar cells into super-cells, then runs PANDA's message passing with a
TF motif prior and a PPI network. With a cell metadata table it builds one network per group of cells
(``runSCORPION``: e.g. one per donor and tissue region) and can test which edges differ between two sets of
those networks (``testEdges``).

Accepted single-cell expression (``cell_expression_file``), genes as rows and cells as columns:

* a delimited text table (``.tsv``/``.txt``/``.csv``, optionally ``.gz``): header ``gene, <cell IDs>``, one row
  per gene, non-negative finite values;
* a 10x Genomics Matrix Market directory: ``matrix.mtx[.gz]`` with ``features.tsv[.gz]`` (or ``genes.tsv``) and
  ``barcodes.tsv[.gz]``.

The motif prior and the PPI network are the same three-column edge lists PANDA reads (TF, gene, weight and
protein, protein, weight). The cell metadata table (``cell_metadata_file``) has a header; its first column (or a
column named cell_id/cell/barcode) holds the cell IDs of the expression matrix, and ``group_by`` names other
columns.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

#: runSCORPION builds a network only for groups of at least max(minCells, 30) cells.
MIN_CELLS_FLOOR = 30
#: testEdges' two-sample t-test needs a spread on each side.
MIN_NETWORKS_PER_SIDE = 2
#: runSCORPION joins the group_by values of a cell with this separator to name its network.
NETWORK_ID_SEPARATOR = "--"
#: The network ID when no group_by is given: every cell builds one network.
ALL_CELLS = "all_cells"
ASSOC_METHODS = ("pearson", "spearman", "pcNet")
DEFAULTS: dict[str, Any] = {
    "group_by": [],
    "compare_by": None,
    "group1": None,
    "group2": None,
    "paired": False,
    "normalize_data": True,
    "gamma_value": 10.0,
    "n_pc": 25,
    "assoc_method": "pearson",
    "alpha_value": 0.1,
    "min_cells": 30,
    "z_scaling": True,
    "n_cores": 1,
}
CELL_ID_NAMES = frozenset({"cell_id", "cell", "cells", "barcode", "barcodes", "cell_barcode"})
TEXT_SUFFIXES = (".tsv", ".txt", ".csv", ".tab")
MTX_NAMES = ("matrix.mtx", "matrix.mtx.gz")
FEATURE_NAMES = ("features.tsv", "features.tsv.gz", "genes.tsv", "genes.tsv.gz")
BARCODE_NAMES = ("barcodes.tsv", "barcodes.tsv.gz")
#: Rows parsed at a time when a dense table is checked, so memory stays at one chunk.
SCAN_CHUNK_ROWS = 2_000

__all__ = [
    "ALL_CELLS", "ASSOC_METHODS", "CellMatrix", "DEFAULTS", "MIN_CELLS_FLOOR", "MIN_NETWORKS_PER_SIDE",
    "NETWORK_ID_SEPARATOR", "comparison_plan", "network_cell_counts", "parameter_errors", "read_cell_metadata",
    "scan_cell_matrix",
]


@dataclass
class CellMatrix:
    """What the checks need from the single-cell matrix: its labels, never its values."""

    layout: str = ""  # "text" or "mtx"
    genes: list[str] = field(default_factory=list)
    cells: list[str] = field(default_factory=list)
    gene_symbols: list[str] = field(default_factory=list)  # mtx only: the features file's second column
    nonzero: int | None = None
    whole_numbers: bool | None = None  # every value read is a whole number (counts)
    errors: list[str] = field(default_factory=list)


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.name.endswith(".gz") else path.open("r", encoding="utf-8")


def _first(directory: Path, names: Iterable[str]) -> Path | None:
    return next((directory / name for name in names if (directory / name).is_file()), None)


def _separator(path: Path, header: str) -> str:
    stem = path.name[:-3] if path.name.endswith(".gz") else path.name
    if stem.casefold().endswith(".csv"):
        return ","
    return "\t" if "\t" in header else "," if "," in header else r"\s+"


def _scan_text(path: Path, matrix: CellMatrix) -> None:
    try:
        with _open_text(path) as handle:
            header = handle.readline().rstrip("\r\n")
    except (OSError, UnicodeDecodeError, EOFError) as error:
        matrix.errors.append(f"cell_expression_file could not be read: {error}")
        return
    separator = _separator(path, header)
    columns = [name.strip().strip('"') for name in (re.split(r"\s+", header.strip()) if separator == r"\s+"
                                                    else header.split(separator))]
    if len(columns) < 3:
        matrix.errors.append("cell_expression_file needs a header: gene, then one column per cell")
        return
    cells = columns[1:]
    if any(not cell for cell in cells):
        matrix.errors.append("cell_expression_file cell IDs (column names) must be non-empty")
    if len(set(cells)) != len(cells):
        matrix.errors.append("cell_expression_file cell IDs (column names) must be unique")
    genes: list[str] = []
    whole, finite, negative = True, True, False
    text_values = values_seen = 0
    try:
        names = [f"c{index}" for index in range(len(columns))]
        reader = pd.read_csv(path, sep=separator, header=0, names=names, chunksize=SCAN_CHUNK_ROWS,
                             dtype={names[0]: str}, engine="c" if separator != r"\s+" else "python")
        for chunk in reader:
            genes.extend(chunk.iloc[:, 0].astype(str).str.strip().str.strip('"'))
            raw = chunk.iloc[:, 1:]
            values = raw.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
            text_values += int((pd.isna(values) & raw.notna().to_numpy()).sum())
            values_seen += int(values.size)
            finite = finite and bool(pd.notna(values).all()) and bool((abs(values) != float("inf")).all())
            if finite and values.size:
                negative = negative or bool((values < 0).any())
                whole = whole and bool((values == values.round()).all())
    except (ValueError, OSError, pd.errors.ParserError, EOFError) as error:
        matrix.errors.append(f"cell_expression_file could not be parsed as a delimited table: {error}")
        return
    if not finite and values_seen and text_values * 2 > values_seen:
        # Mostly words, not numbers: the file is a table of cell annotations (2026-11-10: a request's cell metadata
        # was bound as the matrix, and "values must be finite" did not say why).
        matrix.errors.append(f"cell_expression_file {path.name} holds mostly text, not counts: it looks like a cell "
                             "metadata or annotation table; give the genes x cells matrix or 10x directory instead")
    elif not finite:
        matrix.errors.append("cell_expression_file values must all be finite numbers")
    if negative:
        matrix.errors.append("cell_expression_file values must be non-negative (counts or normalized expression)")
    matrix.layout, matrix.genes, matrix.cells = "text", genes, cells
    matrix.whole_numbers = whole if finite else None


def _read_lines(path: Path) -> list[list[str]]:
    with _open_text(path) as handle:
        return [line.rstrip("\r\n").split("\t") for line in handle if line.strip()]


def _scan_mtx(directory: Path, matrix: CellMatrix) -> None:
    mtx, features, barcodes = (_first(directory, names) for names in (MTX_NAMES, FEATURE_NAMES, BARCODE_NAMES))
    missing = [label for label, found in (("matrix.mtx[.gz]", mtx), ("features.tsv[.gz] or genes.tsv[.gz]", features),
                                          ("barcodes.tsv[.gz]", barcodes)) if found is None]
    if missing:
        matrix.errors.append(f"10x directory {directory} is missing: " + ", ".join(missing))
        return
    try:
        with _open_text(mtx) as handle:
            banner = handle.readline()
            if not banner.startswith("%%MatrixMarket matrix coordinate"):
                matrix.errors.append("matrix.mtx must be a Matrix Market coordinate matrix")
                return
            field_type = banner.split()[3].casefold() if len(banner.split()) > 3 else ""
            line = handle.readline()
            while line.startswith("%"):
                line = handle.readline()
            n_rows, n_cols, nonzero = (int(value) for value in line.split()[:3])
        feature_rows = _read_lines(features)
        barcode_rows = _read_lines(barcodes)
    except (OSError, UnicodeDecodeError, ValueError, EOFError) as error:
        matrix.errors.append(f"10x directory could not be read: {error}")
        return
    if len(feature_rows) != n_rows:
        matrix.errors.append(f"matrix.mtx has {n_rows} rows but the features file lists {len(feature_rows)} genes")
    if len(barcode_rows) != n_cols:
        matrix.errors.append(f"matrix.mtx has {n_cols} columns but barcodes.tsv lists {len(barcode_rows)} cells")
    cells = [row[0].strip() for row in barcode_rows]
    if len(set(cells)) != len(cells):
        matrix.errors.append("barcodes.tsv cell IDs must be unique")
    matrix.layout = "mtx"
    matrix.genes = [row[0].strip() for row in feature_rows]
    matrix.gene_symbols = [row[1].strip() if len(row) > 1 else row[0].strip() for row in feature_rows]
    matrix.cells = cells
    matrix.nonzero = nonzero
    matrix.whole_numbers = True if field_type in {"integer", "pattern"} else None


def scan_cell_matrix(path: str | Path) -> CellMatrix:
    """The matrix's gene and cell labels, from a text table or a 10x directory, with its format errors."""
    resolved = Path(path)
    matrix = CellMatrix()
    if resolved.is_dir():
        _scan_mtx(resolved, matrix)
    elif resolved.is_file() and resolved.name.casefold().endswith(MTX_NAMES):
        _scan_mtx(resolved.parent, matrix)
    elif resolved.is_file():
        stem = resolved.name[:-3] if resolved.name.casefold().endswith(".gz") else resolved.name
        if resolved.suffix.casefold() in {".h5", ".h5ad", ".rds", ".loom", ".npy", ".npz"}:
            matrix.errors.append(
                "cell_expression_file must be a delimited genes x cells table (.tsv/.csv) or a 10x Matrix Market "
                f"directory; {resolved.suffix} files are not read here. Export the counts as a 10x directory "
                "(matrix.mtx, features.tsv, barcodes.tsv) or as a table."
            )
            return matrix
        if not stem.casefold().endswith(TEXT_SUFFIXES):
            matrix.errors.append("cell_expression_file must end in .tsv, .txt, .csv or .tab (optionally .gz)")
            return matrix
        _scan_text(resolved, matrix)
    else:
        matrix.errors.append(f"cell_expression_file must be an existing file or 10x directory: {resolved}")
        return matrix
    if not matrix.errors:
        if len(matrix.genes) < 10:
            matrix.errors.append(f"SCORPION needs at least 10 genes; cell_expression_file has {len(matrix.genes)}")
        if len(matrix.cells) < MIN_CELLS_FLOOR:
            matrix.errors.append(
                f"SCORPION builds a network from at least {MIN_CELLS_FLOOR} cells; "
                f"cell_expression_file has {len(matrix.cells)}"
            )
        if any(not gene for gene in matrix.genes):
            matrix.errors.append("cell_expression_file gene IDs must be non-empty")
    return matrix


def read_cell_metadata(path: str | Path) -> tuple[pd.DataFrame | None, str | None, list[str]]:
    """The metadata table as text, the name of its cell-ID column, and its format errors."""
    resolved = Path(path)
    if not resolved.is_file():
        return None, None, [f"cell_metadata_file must be an existing file: {resolved}"]
    try:
        with _open_text(resolved) as handle:
            header = handle.readline().rstrip("\r\n")
        separator = _separator(resolved, header)
        frame = pd.read_csv(resolved, sep=separator, dtype=str, keep_default_na=False,
                            engine="c" if separator != r"\s+" else "python")
    except (OSError, UnicodeDecodeError, ValueError, pd.errors.ParserError, EOFError) as error:
        return None, None, [f"cell_metadata_file could not be parsed as a delimited table: {error}"]
    frame.columns = [str(name).strip() for name in frame.columns]
    if frame.empty or frame.shape[1] < 2:
        return None, None, ["cell_metadata_file needs a header, a cell-ID column and at least one grouping column"]
    named = [name for name in frame.columns if name.casefold() in CELL_ID_NAMES]
    id_column = named[0] if named else frame.columns[0]
    frame[id_column] = frame[id_column].str.strip()
    errors = []
    if frame[id_column].duplicated().any():
        errors.append(f"cell_metadata_file cell IDs (column {id_column}) must be unique")
    return frame, id_column, errors


def parameter_errors(params: dict[str, Any]) -> list[str]:
    errors = []
    if not 0 <= float(params["alpha_value"]) <= 1:
        errors.append("alpha_value must be between 0 and 1")
    if float(params["gamma_value"]) < 1:
        errors.append("gamma_value (cells per super-cell) must be at least 1")
    if int(params["n_pc"]) < 2:
        errors.append("n_pc must be at least 2")
    if params["assoc_method"] not in ASSOC_METHODS:
        errors.append("assoc_method must be one of " + ", ".join(ASSOC_METHODS))
    if int(params["min_cells"]) < 1:
        errors.append("min_cells must be a positive integer")
    if int(params["n_cores"]) < 1:
        errors.append("n_cores must be at least 1")
    compare = [params.get(name) for name in ("compare_by", "group1", "group2")]
    if any(compare) and not all(compare):
        errors.append("a comparison needs compare_by, group1 and group2 together")
    if params.get("compare_by") and params["compare_by"] not in (params.get("group_by") or []):
        errors.append("compare_by must be one of the group_by columns (networks are built per group_by)")
    if params.get("group1") and params.get("group1") == params.get("group2"):
        errors.append("group1 and group2 must be different values")
    if params.get("paired") and not params.get("compare_by"):
        errors.append("paired needs a comparison (compare_by, group1, group2)")
    return errors


def network_cell_counts(metadata: pd.DataFrame | None, group_by: list[str]) -> dict[str, int]:
    """Cells per network as runSCORPION names them: the group_by values joined by '--'."""
    if metadata is None or not group_by:
        return {}
    ids = metadata[group_by].astype(str).agg(NETWORK_ID_SEPARATOR.join, axis=1)
    return {str(key): int(value) for key, value in ids.value_counts(sort=False).items()}


@dataclass
class ComparisonPlan:
    group1: list[str]
    group2: list[str]
    paired: bool
    errors: list[str]


def comparison_plan(built: Iterable[str], params: dict[str, Any]) -> ComparisonPlan:
    """The networks on each side of a testEdges comparison, chosen from the networks that are built.

    A network's compare_by value is its component at compare_by's position in group_by. Paired networks are matched
    on their other components (for example the donor) and kept in that order.
    """
    group_by = list(params.get("group_by") or [])
    column, first, second = params.get("compare_by"), params.get("group1"), params.get("group2")
    position = group_by.index(column)
    sides: dict[str, dict[tuple[str, ...], str]] = {first: {}, second: {}}
    for network in built:
        parts = network.split(NETWORK_ID_SEPARATOR)
        if len(parts) != len(group_by):
            continue
        if parts[position] in sides:
            sides[parts[position]][tuple(parts[:position] + parts[position + 1:])] = network
    errors: list[str] = []
    one, two = sides[first], sides[second]
    for value, networks in ((first, one), (second, two)):
        if len(networks) < MIN_NETWORKS_PER_SIDE:
            others = [name for name in group_by if name != column]
            hint = (f"; add a replicate column such as a donor or sample column to group_by so each {column} "
                    "value gives several networks") if not others else ""
            errors.append(
                f"testEdges needs at least {MIN_NETWORKS_PER_SIDE} networks with {column}={value}; "
                f"{len(networks)} meet the cell minimum{hint}"
            )
    paired = bool(params.get("paired"))
    if paired and not errors:
        keys = sorted(set(one) & set(two))
        if len(keys) < MIN_NETWORKS_PER_SIDE:
            errors.append(f"a paired comparison needs at least {MIN_NETWORKS_PER_SIDE} matched pairs; got {len(keys)}")
        return ComparisonPlan([one[key] for key in keys], [two[key] for key in keys], True, errors)
    return ComparisonPlan(sorted(one.values()), sorted(two.values()), False, errors)
