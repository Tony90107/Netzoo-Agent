#!/usr/bin/env python3
"""Run PUMA with a validated, precomputed gene-gene co-expression matrix."""

from __future__ import annotations

import argparse

import pandas as pd

from netZooPy.puma.puma import Puma
from netzoo_agent_core.data.coexpression import (
    read_coexpression_matrix,
    read_expression_gene_ids,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run netZooPy PUMA with precomputed co-expression."
    )
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-m", "--motif", required=True)
    parser.add_argument("-p", "--ppi", required=True)
    parser.add_argument("-i", "--mir", required=True)
    parser.add_argument("-c", "--coexpression", required=True)
    parser.add_argument("-o", "--out", required=True)
    parser.add_argument(
        "--mode_process", choices=["intersection"], default="intersection"
    )
    parser.add_argument("--computing", default="cpu")
    parser.add_argument("--precision", default="double")
    parser.add_argument("--alpha", type=float, default=0.1)
    args = parser.parse_args()

    expression_genes = set(read_expression_gene_ids(args.expression))
    try:
        motif = pd.read_csv(args.motif, sep="\t", header=None)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise ValueError(f"motif prior could not be read: {error}") from error
    if motif.shape[1] < 2:
        raise ValueError("motif prior must contain regulator and gene columns")
    filtered_genes = sorted(
        expression_genes & set(motif.iloc[:, 1].astype(str).str.strip())
    )
    # PUMA's public Python API accepts df_correlation_matrix.  We validate the
    # artifact before handing it to that API so the wrapper cannot silently
    # reorder or invent genes.
    coexpression = read_coexpression_matrix(
        args.coexpression,
        expected_gene_ids=filtered_genes,
    )
    puma = Puma(
        args.expression,
        args.motif,
        args.ppi,
        args.mir,
        modeProcess=args.mode_process,
        computing=args.computing,
        precision=args.precision,
        save_memory=False,
        alpha=args.alpha,
        df_correlation_matrix=coexpression,
    )
    gene_ids = [str(gene) for gene in puma.gene_names]
    if list(coexpression.index.astype(str)) != gene_ids:
        raise ValueError(
            "precomputed co-expression gene IDs do not match PUMA's filtered gene axis"
        )
    puma.save_puma_results(args.out)
    print(f"Used precomputed co-expression: {args.coexpression}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
