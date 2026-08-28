#!/usr/bin/env python3
"""Run the pinned SAMBAR API in an isolated directory and publish typed artifacts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from netZooPy.sambar.sambar import sambar


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pinned netZooPy SAMBAR.")
    parser.add_argument("-m", "--mutation", required=True)
    parser.add_argument("-e", "--exon-size", required=True)
    parser.add_argument("-g", "--cancer-genes", required=True)
    parser.add_argument("-p", "--pathways", required=True)
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--kmin", type=int, default=2)
    parser.add_argument("--kmax", type=int, default=4)
    parser.add_argument("--distance", default="binomial")
    parser.add_argument("--linkage", default="complete")
    parser.add_argument("--no-norm-patient", action="store_false", dest="norm_patient")
    parser.add_argument("--no-gmt-msigdb", action="store_false", dest="gmt_msigdb")
    parser.add_argument("--no-subset-cancer-genes", action="store_false", dest="subset_cancer_genes")
    parser.add_argument("--no-cluster", action="store_false", dest="cluster")
    parser.set_defaults(norm_patient=True, gmt_msigdb=True, subset_cancer_genes=True, cluster=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    mutation_path = Path(args.mutation).resolve()
    exon_size_path = Path(args.exon_size).resolve()
    cancer_genes_path = Path(args.cancer_genes).resolve()
    pathway_path = Path(args.pathways).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_names = ["mt_out.csv", "pt_out.csv"]
    if args.cluster:
        artifact_names.extend(["clustergroups.csv", "dist_matrix.csv"])
    collisions = [output_dir / name for name in artifact_names if (output_dir / name).resolve() in {mutation_path, exon_size_path, cancer_genes_path, pathway_path}]
    if collisions:
        raise ValueError("SAMBAR output would overwrite an input: " + ", ".join(map(str, collisions)))
    with tempfile.TemporaryDirectory(prefix="sambar-", dir=output_dir) as temporary:
        working = Path(temporary)
        previous = Path.cwd()
        try:
            os.chdir(working)
            sambar(
                mut_file=str(mutation_path),
                esize_file=str(exon_size_path),
                genes_file=str(cancer_genes_path),
                gmtfile=str(pathway_path),
                normPatient=args.norm_patient,
                kmin=args.kmin,
                kmax=args.kmax,
                gmtMSigDB=args.gmt_msigdb,
                subcangenes=args.subset_cancer_genes,
                distance=args.distance,
                linkagem=args.linkage,
                cluster=args.cluster,
            )
        finally:
            os.chdir(previous)
        missing = [name for name in artifact_names if not (working / name).is_file()]
        if missing:
            raise RuntimeError("SAMBAR did not create required artifacts: " + ", ".join(missing))
        for name in artifact_names:
            shutil.move(str(working / name), output_dir / name)
    manifest = {
        "method": "SAMBAR",
        "inputs": {
            "mutation_file": str(mutation_path),
            "exon_size_file": str(exon_size_path),
            "cancer_gene_file": str(cancer_genes_path),
            "pathway_file": str(pathway_path),
        },
        "parameters": {
            "norm_patient": args.norm_patient, "kmin": args.kmin, "kmax": args.kmax,
            "gmt_msigdb": args.gmt_msigdb, "subset_cancer_genes": args.subset_cancer_genes,
            "distance": args.distance, "linkage": args.linkage, "cluster": args.cluster,
        },
        "artifacts": artifact_names,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for name in [*artifact_names, "manifest.json"]:
        print(f"Wrote {output_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
