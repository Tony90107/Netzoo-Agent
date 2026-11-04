#!/usr/bin/env python3
"""Run pinned PySNAIL (SNAIL smooth-quantile normalization) and record what was done.

Runs in its own process: importing pysnail starts pandarallel workers.
Writes the normalized gene-by-sample matrix and ``<output>.normalization.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import warnings
from pathlib import Path

from netzoo_agent_core.data.normalization import (
    SNAIL_AGGREGATIONS,
    load_normalization_inputs,
    normalization_record_path,
)


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample_name(key: object) -> str:
    # Qstat series are indexed by (Group, Sample).
    return str(key[-1]) if isinstance(key, tuple) else str(key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PySNAIL SNAIL normalization.")
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-g", "--groups", default="")
    parser.add_argument("-m", "--aggregation", default="median", choices=SNAIL_AGGREGATIONS)
    parser.add_argument("-t", "--threshold", type=float, default=0.25)
    parser.add_argument("-c", "--cutoff", type=float, default=0.15)
    args = parser.parse_args()

    inputs = load_normalization_inputs(args.expression, args.output, args.groups)
    if inputs.errors:
        for error in inputs.errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    # PySNAIL's tqdm progress bars would fill the tool report's stderr.
    os.environ.setdefault("TQDM_DISABLE", "1")
    with warnings.catch_warnings():
        # PySNAIL warns on every call (e.g. "ignored argument 'threshold'"); keep stderr for real failures.
        warnings.simplefilter("ignore", RuntimeWarning)
        from pysnail import Dataset, qsmooth

        dataset = Dataset(inputs.expression, inputs.groups)
        normalized, qstat = qsmooth(
            dataset,
            aggregation=args.aggregation,
            threshold=args.threshold,
            cutoff=args.cutoff,
        )

    affected_samples = int(qstat.num_affected_samples)
    aggregation_used = args.aggregation
    if aggregation_used == "auto":
        # The same rule pysnail.qsmooth applies.
        aggregation_used = (
            "median" if affected_samples / dataset.num_samples >= args.threshold else "mean"
        )

    normalized.columns = normalized.columns.get_level_values(-1)
    normalized = normalized.loc[inputs.expression.index, inputs.expression.columns]
    output = inputs.output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output, sep="\t", index_label="gene", float_format="%.10g")

    affected_genes = {
        _sample_name(key): int(count)
        for key, count in qstat.num_affected_genes.items()
        if int(count)
    }
    groups = (
        {str(name): int(count) for name, count in inputs.groups.value_counts().sort_index().items()}
        if inputs.groups is not None
        else None
    )
    manifest = {
        "method": "snail",
        "method_label": "SNAIL (PySNAIL)",
        "software": "PySNAIL",
        "pysnail_ref": os.environ.get("PYSNAIL_REF", "unknown"),
        "expression_file": str(inputs.expression_path),
        "expression_sha256": checksum(inputs.expression_path),
        "groups_file": str(inputs.groups_path) if inputs.groups_path else None,
        "groups": groups,
        "aggregation_requested": args.aggregation,
        "aggregation_used": aggregation_used,
        "threshold": args.threshold if args.aggregation == "auto" else None,
        "trimmed_mean_cutoff": args.cutoff,
        "genes": int(normalized.shape[0]),
        "samples": int(normalized.shape[1]),
        "scale": "count scale (not log-transformed)",
        "affected_samples": affected_samples,
        "affected_genes_per_sample": affected_genes,
        "output_file": str(output),
        "output_sha256": checksum(output),
    }
    normalization_record_path(output).write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"SNAIL normalization complete: {manifest['genes']} genes x {manifest['samples']} samples, "
        f"{aggregation_used} aggregation, {affected_samples} sample(s) with genes affected by "
        "qsmooth tie averaging."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
