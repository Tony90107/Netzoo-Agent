#!/usr/bin/env python3
"""Run the pinned PORCUPINE R package on a sample-specific network and publish typed artifacts.

Input preparation (the explicit LIONESS -> PORCUPINE conversion step):
  1. Parse the labelled edges-by-samples table (LIONESS-PANDA / LIONESS-PUMA text output).
  2. Drop the optional prior column (an edge annotation, not a sample).
  3. With scale_data=true, drop edges whose weight is constant across samples (streamed, chunk by chunk):
     they cannot be unit-variance scaled and would abort the PCA.
  4. Write ``regulator, target, <samples>`` TSV for PORCUPINE (edges x samples).
Outputs (all tab separated, written to output_dir):
  porcupine_pathways.tsv            one row per tested pathway (statistics)
  porcupine_random_null.tsv         one row per random gene set (null PCA)
  porcupine_pc1_sample_scores.tsv   pathways x samples PC1 scores
  porcupine_edge_loadings.tsv       pathway x edge PC1/PC2 loadings (significant pathways)
  manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from porcupine_io import DEFAULTS, MIN_SAMPLES, parameter_errors, read_gmt, scan_sample_network, write_r_matrix  # noqa: E402

ARTIFACTS = (
    "porcupine_pathways.tsv",
    "porcupine_random_null.tsv",
    "porcupine_pc1_sample_scores.tsv",
    "porcupine_edge_loadings.tsv",
)
R_SCRIPT = Path(__file__).resolve().parent / "porcupine_run.R"


def _bool(text: str) -> bool:
    lowered = text.strip().casefold()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {text!r}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pinned PORCUPINE (R) on sample-specific networks.")
    parser.add_argument("-n", "--network", required=True, help="labelled edges x samples network table")
    parser.add_argument("-p", "--pathways", required=True, help="GMT pathway file")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--min-pathway-size", type=int, default=DEFAULTS["min_pathway_size"])
    parser.add_argument("--max-pathway-size", type=int, default=DEFAULTS["max_pathway_size"])
    parser.add_argument("--n-permutations", type=int, default=DEFAULTS["n_permutations"])
    parser.add_argument("--n-cores", type=int, default=DEFAULTS["n_cores"])
    parser.add_argument("--scale-data", type=_bool, default=DEFAULTS["scale_data"])
    parser.add_argument("--center-data", type=_bool, default=DEFAULTS["center_data"])
    parser.add_argument("--fdr-threshold", type=float, default=DEFAULTS["fdr_threshold"])
    parser.add_argument("--min-effect-size", type=float, default=DEFAULTS["min_effect_size"])
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    return parser


def main() -> int:
    args = _parser().parse_args()
    params = {name: getattr(args, name) for name in DEFAULTS}
    network_path = Path(args.network).resolve()
    pathway_path = Path(args.pathways).resolve()
    output_dir = Path(args.output_dir).resolve()

    errors = parameter_errors(params)
    network = scan_sample_network(network_path)  # labels and checks only; the matrix is streamed below
    pathways, gmt_errors = read_gmt(pathway_path)
    errors += network.errors + gmt_errors
    if not network.errors and len(network.samples) < MIN_SAMPLES:
        errors.append(f"PORCUPINE needs at least {MIN_SAMPLES} samples for a stable PCA; got {len(network.samples)}")
    if errors:
        raise SystemExit("PORCUPINE input validation failed:\n  " + "\n  ".join(errors))

    if args.scale_data and network.constant_edges >= network.n_edges:
        raise SystemExit("PORCUPINE input validation failed:\n  every edge is constant across samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [output_dir / name for name in (*ARTIFACTS, "manifest.json")]
    collision = next((path for path in outputs if path in {network_path, pathway_path}), None)
    if collision is not None:
        raise SystemExit(f"PORCUPINE output would overwrite an input: {collision}")

    rscript = os.environ.get("NETZOO_RSCRIPT", "/opt/conda/envs/netzoo-r/bin/Rscript")
    with tempfile.TemporaryDirectory(prefix="porcupine-", dir=output_dir) as temporary:
        staging = Path(temporary)
        matrix_path = staging / "network_matrix.tsv"
        # Pathway sizes count target genes that kept at least one usable edge: the genes R will see.
        edges_used, dropped, targets = write_r_matrix(network_path, matrix_path, drop_constant=args.scale_data)
        overlap = {name: [g for g in genes if g in targets] for name, genes in pathways.items()}
        testable = [name for name, genes in overlap.items()
                    if args.min_pathway_size <= len(genes) <= args.max_pathway_size]
        if not testable:
            raise SystemExit(
                "PORCUPINE input validation failed:\n  no GMT pathway has between "
                f"{args.min_pathway_size} and {args.max_pathway_size} genes among the network targets; "
                "check that GMT and network gene identifiers use the same namespace (e.g. symbols vs Ensembl)"
            )
        r_params = {**params, "network_matrix": str(matrix_path), "pathway_file": str(pathway_path),
                    "output_dir": str(staging)}
        params_path = staging / "params.json"
        params_path.write_text(json.dumps(r_params), encoding="utf-8")
        completed = subprocess.run([rscript, str(R_SCRIPT), str(params_path)], check=False)
        if completed.returncode != 0:
            raise SystemExit(f"PORCUPINE R run failed with exit code {completed.returncode}")
        missing = [name for name in ARTIFACTS if not (staging / name).is_file()]
        if missing:
            raise SystemExit("PORCUPINE did not create required artifacts: " + ", ".join(missing))
        for name in ARTIFACTS:
            shutil.move(str(staging / name), output_dir / name)

    manifest = {
        "method": "PORCUPINE",
        "package": {"name": "PORCUPINE", "repository": "kuijjerlab/PORCUPINE",
                    "ref": os.environ.get("PORCUPINE_REF", "unknown")},
        "inputs": {"sample_network_file": str(network_path), "pathway_file": str(pathway_path)},
        "input_summary": {
            "samples": len(network.samples),
            "edges": network.n_edges,
            "edges_used": edges_used,
            "constant_edges_dropped": dropped,
            "prior_column_ignored": network.prior_column,
            "gmt_pathways": len(pathways),
            "pathways_tested": len(testable),
        },
        "parameters": params,
        "artifacts": list(ARTIFACTS),
        "orientation": {
            "porcupine_pathways.tsv": "rows=pathways, columns=statistics",
            "porcupine_random_null.tsv": "rows=random gene sets, columns=pathway_size,n_edges,pc1_variance_pct",
            "porcupine_pc1_sample_scores.tsv": "rows=pathways, columns=samples",
            "porcupine_edge_loadings.tsv": "rows=pathway x regulator->target edges",
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in outputs:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
