#!/usr/bin/env python3
"""Run pinned netZooPy COBRA and write reproducible local artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from netZooPy.cobra import cobra
from netzoo_agent_core.data.cobra import (
    cobra_input_output_collisions,
    load_cobra_inputs,
)
from netzoo_agent_core.data.coexpression import (
    adjusted_coexpression_from_cobra,
    write_adjusted_coexpression,
)


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run netZooPy COBRA.")
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-d", "--design", required=True)
    parser.add_argument("-o", "--output-dir", required=True)
    args = parser.parse_args()
    collisions = cobra_input_output_collisions(args.expression, args.design, args.output_dir)
    if collisions:
        raise ValueError(
            "COBRA output would overwrite an input: " + ", ".join(map(str, collisions))
        )
    expression, design = load_cobra_inputs(args.expression, args.design)
    if "intercept" not in design.columns:
        design.insert(0, "intercept", 1.0)
    elif not np.allclose(design["intercept"].to_numpy(dtype=float), 1.0):
        raise ValueError("COBRA intercept column must contain only ones")
    psi, q, d, g = cobra(design.to_numpy(), expression.to_numpy())
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_dir / "components.npz", psi=psi, Q=q, d=d, g=g)
    adjusted = adjusted_coexpression_from_cobra(
        psi,
        q,
        list(expression.index.astype(str)),
        list(design.columns.astype(str)),
    )
    adjusted_tsv, adjusted_npz = write_adjusted_coexpression(adjusted, output_dir)
    pd.DataFrame(
        {
            "component": range(1, len(d) + 1),
            "eigenvalue": d,
            "max_absolute_covariate_impact": np.abs(psi).max(axis=0),
        }
    ).to_csv(output_dir / "summary.tsv", sep="\t", index=False)
    manifest = {
        "method": "COBRA",
        "netzoopy_revision": "60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822",
        "expression_file": str(Path(args.expression).resolve()),
        "design_file": str(Path(args.design).resolve()),
        "expression_sha256": checksum(Path(args.expression)),
        "design_sha256": checksum(Path(args.design)),
        "genes": int(expression.shape[0]),
        "samples": int(expression.shape[1]),
        "covariates": list(design.columns.astype(str)),
        "sample_order": list(expression.columns.astype(str)),
        "adjustment": {
            "method": "intercept_component",
            "intercept_column": "intercept",
            "formula": "Q @ diag(psi[intercept, :]) @ Q.T, normalized to correlation",
        },
        "adjusted_coexpression": {
            "format": "labeled_gene_by_gene_correlation",
            "tsv": adjusted_tsv.name,
            "npz": adjusted_npz.name,
            "genes": int(adjusted.shape[0]),
        },
        "artifacts": [
            "components.npz",
            "summary.tsv",
            adjusted_tsv.name,
            adjusted_npz.name,
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_dir / 'manifest.json'}")
    print(f"Wrote {output_dir / 'components.npz'}")
    print(f"Wrote {output_dir / 'summary.tsv'}")
    print(f"Wrote {adjusted_tsv}")
    print(f"Wrote {adjusted_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
