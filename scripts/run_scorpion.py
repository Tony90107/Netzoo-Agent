#!/usr/bin/env python3
"""Run the pinned SCORPION R package on single-cell expression and publish typed artifacts.

Outputs (tab separated, written to output_dir):
  scorpion_networks.tsv            tf, target, one column per network (edges x networks); one column "all_cells"
                                   without group_by
  scorpion_network_cells.tsv       cells per requested network and whether it was built
  scorpion_differential_edges.tsv  testEdges() two-sample (or paired) comparison, sorted by pAdj (with a comparison)
  manifest.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scorpion_io import (  # noqa: E402
    ALL_CELLS, DEFAULTS, BARCODE_NAMES, FEATURE_NAMES, MTX_NAMES, comparison_plan, network_cell_counts,
    parameter_errors, read_cell_metadata, scan_cell_matrix,
)

R_SCRIPT = Path(__file__).resolve().parent / "scorpion_run.R"
NETWORKS = "scorpion_networks.tsv"
CELLS = "scorpion_network_cells.tsv"
DIFFERENTIAL = "scorpion_differential_edges.tsv"


def _bool(text: str) -> bool:
    lowered = text.strip().casefold()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {text!r}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pinned SCORPION (R) on single-cell expression.")
    parser.add_argument("-e", "--expression", required=True, help="genes x cells table or 10x Matrix Market directory")
    parser.add_argument("-m", "--motif", required=True, help="TF, gene, weight motif prior")
    parser.add_argument("-p", "--ppi", required=True, help="protein, protein, weight PPI network")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--cell-metadata", default="", help="cell metadata table (needed with --group-by)")
    parser.add_argument("--group-by", default="", help="comma-separated metadata columns; one network per group")
    parser.add_argument("--compare-by", default="")
    parser.add_argument("--group1", default="")
    parser.add_argument("--group2", default="")
    parser.add_argument("--paired", type=_bool, default=DEFAULTS["paired"])
    parser.add_argument("--normalize-data", type=_bool, default=DEFAULTS["normalize_data"])
    parser.add_argument("--gamma-value", type=float, default=DEFAULTS["gamma_value"])
    parser.add_argument("--n-pc", type=int, default=DEFAULTS["n_pc"])
    parser.add_argument("--assoc-method", default=DEFAULTS["assoc_method"])
    parser.add_argument("--alpha-value", type=float, default=DEFAULTS["alpha_value"])
    parser.add_argument("--min-cells", type=int, default=DEFAULTS["min_cells"])
    parser.add_argument("--z-scaling", type=_bool, default=DEFAULTS["z_scaling"])
    parser.add_argument("--n-cores", type=int, default=DEFAULTS["n_cores"])
    parser.add_argument("--seed", type=int, default=1)
    return parser


def _edge_table(path: Path) -> tuple[str, bool]:
    """R's separator and header flag for a three-column edge list (the header test PANDA's check uses)."""
    with (gzip.open(path, "rt", encoding="utf-8") if path.name.endswith(".gz")
          else path.open("r", encoding="utf-8")) as handle:
        first = handle.readline().rstrip("\r\n")
    separator = "\t" if "\t" in first else "," if "," in first else ""
    fields = first.split(separator) if separator else first.split()
    try:
        float(fields[2])
        header = False
    except (IndexError, ValueError):
        header = True
    return separator, header


def _first(directory: Path, names) -> str:
    return str(next(directory / name for name in names if (directory / name).is_file()))


def _gene_column(matrix, motif_genes: set[str]) -> int:
    """10x features: the column (1 = ID, 2 = symbol) sharing more genes with the motif prior's targets."""
    ids, symbols = set(matrix.genes), set(matrix.gene_symbols)
    return 2 if len(symbols & motif_genes) > len(ids & motif_genes) else 1


def main() -> int:
    args = _parser().parse_args()
    group_by = [name.strip() for name in args.group_by.split(",") if name.strip()]
    params = {
        "group_by": group_by, "compare_by": args.compare_by or None, "group1": args.group1 or None,
        "group2": args.group2 or None, "paired": args.paired, "normalize_data": args.normalize_data,
        "gamma_value": args.gamma_value, "n_pc": args.n_pc, "assoc_method": args.assoc_method,
        "alpha_value": args.alpha_value, "min_cells": args.min_cells, "z_scaling": args.z_scaling,
        "n_cores": args.n_cores,
    }
    expression = Path(args.expression).resolve()
    motif, ppi = Path(args.motif).resolve(), Path(args.ppi).resolve()
    output_dir = Path(args.output_dir).resolve()

    errors = parameter_errors(params)
    matrix = scan_cell_matrix(expression)
    errors += matrix.errors
    metadata, id_column, metadata_errors = (None, None, [])
    if group_by:
        if not args.cell_metadata:
            errors.append("group_by needs a cell_metadata_file")
        else:
            metadata, id_column, metadata_errors = read_cell_metadata(Path(args.cell_metadata).resolve())
            errors += metadata_errors
            if metadata is not None:
                errors += [f"group_by column {name!r} is not in cell_metadata_file" for name in group_by
                           if name not in metadata.columns]
    if errors:
        raise SystemExit("SCORPION input validation failed:\n  " + "\n  ".join(errors))

    counts = {ALL_CELLS: len(matrix.cells)}
    if group_by:
        metadata = metadata[metadata[id_column].isin(set(matrix.cells))]
        if metadata.empty:
            raise SystemExit("SCORPION input validation failed:\n  no cell ID in cell_metadata_file is a cell of "
                             "cell_expression_file")
        counts = network_cell_counts(metadata, group_by)
    minimum = max(args.min_cells, 30)
    expected = [name for name, cells in counts.items() if cells >= minimum]
    if not expected:
        raise SystemExit(f"SCORPION input validation failed:\n  no network has at least {minimum} cells")
    comparison = None
    if params["compare_by"]:
        plan = comparison_plan(expected, params)
        if plan.errors:
            raise SystemExit("SCORPION input validation failed:\n  " + "\n  ".join(plan.errors))
        comparison = {"compare_by": params["compare_by"], "group1": params["group1"], "group2": params["group2"],
                      "paired": params["paired"]}

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = [NETWORKS, CELLS, *([DIFFERENTIAL] if comparison else [])]
    outputs = [output_dir / name for name in (*artifacts, "manifest.json")]
    inputs = {expression, motif, ppi, *([Path(args.cell_metadata).resolve()] if args.cell_metadata else [])}
    if collision := next((path for path in outputs if path in inputs), None):
        raise SystemExit(f"SCORPION output would overwrite an input: {collision}")

    motif_separator, motif_header = _edge_table(motif)
    ppi_separator, ppi_header = _edge_table(ppi)
    r_params = {
        **params, "seed": args.seed, "all_cells": ALL_CELLS, "layout": matrix.layout,
        "motif_file": str(motif), "motif_separator": motif_separator, "motif_header": motif_header,
        "ppi_file": str(ppi), "ppi_separator": ppi_separator, "ppi_header": ppi_header,
        "comparison": comparison,
    }
    gene_column = None
    if matrix.layout == "mtx":
        directory = expression if expression.is_dir() else expression.parent
        motif_genes = set(pd.read_csv(motif, sep=motif_separator or r"\s+", header=0 if motif_header else None,
                                      usecols=[1], dtype=str).iloc[:, 0].str.strip())
        gene_column = _gene_column(matrix, motif_genes)
        r_params.update(mtx_file=_first(directory, MTX_NAMES), features_file=_first(directory, FEATURE_NAMES),
                        barcodes_file=_first(directory, BARCODE_NAMES), gene_column=gene_column)
    else:
        r_params.update(cell_expression_file=str(expression),
                        separator="," if expression.name.casefold().removesuffix(".gz").endswith(".csv") else "\t")
    if group_by:
        meta_path = Path(args.cell_metadata).resolve()
        with (gzip.open(meta_path, "rt", encoding="utf-8") if meta_path.name.endswith(".gz")
              else meta_path.open("r", encoding="utf-8")) as handle:
            header = handle.readline()
        r_params.update(cell_metadata_file=str(meta_path), cell_id_column=id_column,
                        metadata_separator="\t" if "\t" in header else "," if "," in header else "")

    rscript = os.environ.get("NETZOO_RSCRIPT", "/opt/conda/envs/netzoo-r/bin/Rscript")
    with tempfile.TemporaryDirectory(prefix="scorpion-", dir=output_dir) as temporary:
        staging = Path(temporary)
        r_params["output_dir"] = str(staging)
        params_path = staging / "params.json"
        params_path.write_text(json.dumps(r_params), encoding="utf-8")
        completed = subprocess.run([rscript, str(R_SCRIPT), str(params_path)], check=False)
        if completed.returncode != 0:
            raise SystemExit(f"SCORPION R run failed with exit code {completed.returncode}")
        missing = [name for name in (*artifacts, "summary.json") if not (staging / name).is_file()]
        if missing:
            raise SystemExit("SCORPION did not create required artifacts: " + ", ".join(missing))
        summary = json.loads((staging / "summary.json").read_text(encoding="utf-8"))
        for name in artifacts:
            shutil.move(str(staging / name), output_dir / name)

    manifest = {
        "method": "SCORPION",
        "package": {"name": "SCORPION", "repository": "kuijjerlab/SCORPION",
                    "ref": os.environ.get("SCORPION_REF", "unknown")},
        "inputs": {
            "cell_expression_file": str(expression), "motif_file": str(motif), "ppi_file": str(ppi),
            **({"cell_metadata_file": str(Path(args.cell_metadata).resolve())} if args.cell_metadata else {}),
        },
        "input_summary": {
            "layout": matrix.layout,
            **({"gene_ids_from_features_column": gene_column} if gene_column else {}),
            **summary,
        },
        "parameters": {**params, "seed": args.seed},
        "artifacts": artifacts,
        "orientation": {
            NETWORKS: "rows=TF->target edges, columns=tf,target then one column per network (group_by values "
                      "joined by '--'; 'all_cells' without group_by); weights are PANDA scores"
                      + (" (z-scaled)" if args.z_scaling else " (0-1 scale)"),
            CELLS: "rows=requested networks, columns=network_id,n_cells,built",
            **({DIFFERENTIAL: "rows=edges, columns=testEdges statistics (meanGroup1, meanGroup2, cohensD, "
                              "log2FoldChange, tStatistic, pValue, pAdj); group1 minus group2"} if comparison else {}),
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in outputs:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
