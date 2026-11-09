"""Strict, side-effect-free SCORPION input inspection and output checks (2026-11-08)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from scorpion_io import (
    ALL_CELLS, DEFAULTS, MIN_CELLS_FLOOR, comparison_plan, network_cell_counts, parameter_errors, read_cell_metadata,
    scan_cell_matrix,
)

from .paths import _resolve_user_path
from .tables import _read_checked_table, _validate_edge_or_bed

__all__ = ["inspect_scorpion_inputs_impl", "scorpion_gene_axes", "scorpion_parameters", "validate_scorpion_output"]

SCORPION_NETWORKS = "scorpion_networks.tsv"
SCORPION_CELLS = "scorpion_network_cells.tsv"
SCORPION_DIFFERENTIAL = "scorpion_differential_edges.tsv"


def _get(decision: Any, name: str) -> Any:
    return decision.get(name) if isinstance(decision, dict) else getattr(decision, name, None)


def scorpion_parameters(decision: Any | None) -> dict[str, Any]:
    """Declared SCORPION controls from a decision or dict; unset values take the defaults."""
    params = {name: (list(value) if isinstance(value, list) else value) for name, value in DEFAULTS.items()}
    if decision is None:
        return params
    for name in DEFAULTS:
        value = _get(decision, name)
        if value is not None and value != "":
            params[name] = value
    if isinstance(params["group_by"], str):
        params["group_by"] = [part.strip() for part in params["group_by"].split(",") if part.strip()]
    return params


def _edge_check(label: str, path: str):
    check = _validate_edge_or_bed(_read_checked_table(label, path), label)
    frame = check.frame
    first = second = set()
    if check.ok and frame is not None:
        rows = frame.iloc[1:] if check.has_header else frame
        first = set(rows.iloc[:, 0].astype(str).str.strip())
        second = set(rows.iloc[:, 1].astype(str).str.strip())
    return check, first, second


def scorpion_gene_axes(motif_file: str) -> list[tuple[list[str], str]]:
    """The motif prior's target genes, for the shared gene-namespace check.

    Expression genes are not checked here: a 10x features file lists both Ensembl IDs and symbols, and the run takes
    the column that shares more genes with the motif targets (run_scorpion.py)."""
    check, _tfs, genes = _edge_check("motif", motif_file)
    return [(sorted(genes), "SCORPION motif target genes")] if check.ok else []


def inspect_scorpion_inputs_impl(
    cell_expression_file: str,
    motif_file: str,
    ppi_file: str,
    decision: Any | None = None,
) -> tuple[str, bool]:
    """Validate the SCORPION expression/prior/metadata contract without writing files."""
    params = scorpion_parameters(decision)
    expression_path = _resolve_user_path(cell_expression_file) if cell_expression_file else Path("")
    metadata_value = _get(decision, "cell_metadata_file") if decision is not None else None
    lines = [
        "SCORPION input inspection:",
        f"- single-cell expression: {expression_path}",
        f"- motif prior: {_resolve_user_path(motif_file) if motif_file else ''}",
        f"- PPI network: {_resolve_user_path(ppi_file) if ppi_file else ''}",
        "  required expression format: genes x cells, as a table (header gene, then one column per cell) or a 10x "
        "Matrix Market directory (matrix.mtx, features.tsv, barcodes.tsv)",
    ]
    errors = list(parameter_errors(params))
    matrix = scan_cell_matrix(expression_path) if cell_expression_file else None
    if matrix is None:
        errors.append("cell_expression_file is required")
    else:
        errors += matrix.errors
        if not matrix.errors:
            lines.append(f"  expression: {len(matrix.genes)} genes x {len(matrix.cells)} cells ({matrix.layout})")
            if matrix.whole_numbers is False and params["normalize_data"]:
                lines.append(
                    "  note: the values are not all whole numbers; normalize_data log-normalizes counts, so set "
                    "normalize_data=false if they are already normalized"
                )
    motif, motif_tfs, motif_genes = _edge_check("motif", motif_file)
    ppi, ppi_a, ppi_b = _edge_check("ppi", ppi_file)
    errors += [f"motif: {error}" for error in motif.errors] + [f"PPI: {error}" for error in ppi.errors]
    if matrix is not None and not matrix.errors and motif.ok:
        genes = set(matrix.genes) | set(matrix.gene_symbols)
        shared = genes & motif_genes
        lines.append(f"  motif: {len(motif_tfs)} TFs, {len(motif_genes)} target genes; {len(shared)} are expression genes")
        if not shared:
            errors.append(
                "no motif target gene is a gene of cell_expression_file; check that both use the same identifiers "
                "(for example gene symbols, not Ensembl IDs)"
            )
    if motif.ok and ppi.ok:
        tfs = motif_tfs & (ppi_a | ppi_b)
        lines.append(f"  PPI: {len(ppi_a | ppi_b)} proteins; {len(tfs)} are motif TFs")
        if not tfs:
            errors.append("no motif TF is a protein of the PPI network; check that both use the same identifiers")

    group_by = list(params["group_by"])
    counts: dict[str, int] = {}
    if group_by:
        if not metadata_value:
            errors.append("group_by needs a cell_metadata_file")
        else:
            metadata, id_column, metadata_errors = read_cell_metadata(_resolve_user_path(metadata_value))
            errors += metadata_errors
            if metadata is not None:
                absent = [name for name in group_by if name not in metadata.columns]
                errors += [f"group_by column {name!r} is not in cell_metadata_file (columns: "
                           f"{', '.join(map(str, metadata.columns))})" for name in absent]
                if not absent and matrix is not None and not matrix.errors:
                    cells = set(matrix.cells)
                    known = metadata[metadata[id_column].isin(cells)]
                    lines.append(f"- cell metadata: {metadata_value}; {len(known)} of {len(cells)} cells have a row "
                                 f"(cell IDs from column {id_column})")
                    if known.empty:
                        errors.append("no cell ID in cell_metadata_file is a cell of cell_expression_file")
                    counts = network_cell_counts(known, group_by)
    elif matrix is not None and not matrix.errors:
        counts = {ALL_CELLS: len(matrix.cells)}
    minimum = max(int(params["min_cells"]), MIN_CELLS_FLOOR)
    if counts:
        built = sorted(name for name, cells in counts.items() if cells >= minimum)
        skipped = sorted(name for name, cells in counts.items() if cells < minimum)
        lines.append(f"  networks: {len(built)} of {len(counts)} groups have at least {minimum} cells")
        if skipped:
            lines.append("  skipped (too few cells): " + ", ".join(f"{name} ({counts[name]})" for name in skipped[:12])
                         + (" ..." if len(skipped) > 12 else ""))
        if not built:
            errors.append(f"no network has at least {minimum} cells")
        elif params.get("compare_by") and not parameter_errors(params):
            plan = comparison_plan(built, params)
            errors += plan.errors
            if not plan.errors:
                lines.append(f"  comparison ({'paired' if plan.paired else 'two-sample'}): "
                             f"{params['compare_by']}={params['group1']} ({len(plan.group1)} networks) vs "
                             f"{params['compare_by']}={params['group2']} ({len(plan.group2)} networks)")
    lines.extend(f"  error: {error}" for error in dict.fromkeys(errors))
    lines.append("  status: " + ("ready" if not errors else "not ready"))
    return "\n".join(lines), not errors


def validate_scorpion_output(output_dir: str) -> tuple[bool, list[str], list[str], dict[str, Any]]:
    """The SCORPION artifacts exist and have the declared orientation."""
    root = _resolve_user_path(output_dir)
    errors: list[str] = []
    artifacts: list[str] = []
    metrics: dict[str, Any] = {}
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return False, [f"SCORPION manifest.json could not be read: {error}"], artifacts, metrics
    expected = list(manifest.get("artifacts") or [])
    for name in expected:
        path = root / name
        if not path.is_file():
            errors.append(f"SCORPION output is missing: {path}")
            continue
        artifacts.append(str(path))
    networks = root / SCORPION_NETWORKS
    if networks.is_file():
        header = pd.read_csv(networks, sep="\t", nrows=0).columns.tolist()
        if header[:2] != ["tf", "target"] or len(header) < 3:
            errors.append(f"{SCORPION_NETWORKS} must start with tf, target and one column per network")
        metrics["scorpion_networks"] = len(header) - 2
    summary = manifest.get("input_summary") or {}
    metrics.update({key: summary[key] for key in ("cells_used", "edges", "regulators", "targets") if key in summary})
    if comparison := summary.get("comparison"):
        metrics["scorpion_edges_padj_below_0_05"] = comparison.get("edges_padj_below_0_05")
    artifacts.append(str(manifest_path))
    return not errors, errors, artifacts, metrics
