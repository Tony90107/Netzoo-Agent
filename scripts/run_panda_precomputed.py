#!/usr/bin/env python3
"""Run PANDA with a validated, precomputed gene-gene co-expression matrix."""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from netZooPy.panda.panda import Panda
from netzoo_agent_core.data.coexpression import read_coexpression_matrix


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run netZooPy PANDA with precomputed co-expression."
    )
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-m", "--motif", required=True)
    parser.add_argument("-p", "--ppi", required=True)
    parser.add_argument("-c", "--coexpression", required=True)
    parser.add_argument("-o", "--out", required=True)
    parser.add_argument("--with_header", action="store_true")
    parser.add_argument("--mode_process", default="intersection")
    parser.add_argument("--computing", default="cpu")
    parser.add_argument("--precision", default="double")
    parser.add_argument("--alpha", type=float, default=0.1)
    args = parser.parse_args()

    # process_data_only lets PANDA establish the authoritative post-filter
    # gene/TF axes and prior matrices without running Pearson or PANDA yet.
    panda = Panda(
        args.expression,
        args.motif,
        args.ppi,
        save_memory=False,
        modeProcess=args.mode_process,
        with_header=args.with_header,
        process_data_only=True,
    )
    gene_ids = [str(gene) for gene in panda.gene_names]
    coexpression = read_coexpression_matrix(
        args.coexpression,
        expected_gene_ids=gene_ids,
    ).to_numpy(dtype=float)
    if coexpression.shape != (len(gene_ids), len(gene_ids)):
        raise ValueError(
            "precomputed co-expression dimensions do not match PANDA's filtered gene axis"
        )

    panda.precision = args.precision
    panda.correlation_matrix = panda._normalize_network(coexpression)
    panda.motif_matrix = panda._normalize_network(panda.motif_matrix_unnormalized)
    panda.ppi_matrix = panda._normalize_network(panda.ppi_matrix)
    panda.tfs, panda.genes = panda.unique_tfs, panda.gene_names
    if args.precision == "single":
        panda.correlation_matrix = np.float32(panda.correlation_matrix)
        panda.motif_matrix = np.float32(panda.motif_matrix)
        panda.ppi_matrix = np.float32(panda.ppi_matrix)
    panda.panda_network = panda.panda_loop(
        panda.correlation_matrix,
        panda.motif_matrix,
        panda.ppi_matrix,
        args.computing,
        args.alpha,
    )
    if not np.isfinite(np.asarray(panda.panda_network, dtype=float)).all():
        raise ValueError(
            "PANDA produced non-finite regulatory-network weights; no output was "
            "written. Check expression variability and motif/PPI overlap before "
            "treating this as a valid COBRA-to-PANDA result."
        )
    panda.panda_network = pd.DataFrame(
        panda.panda_network,
        index=panda.tfs,
        columns=panda.genes,
    )
    panda.save_panda_results(args.out, old_compatible=False)
    print(f"Used precomputed co-expression: {args.coexpression}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
