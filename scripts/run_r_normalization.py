#!/usr/bin/env python3
"""Run RLE (DESeq2), TMM (edgeR) or quantile (preprocessCore) normalization and record what was done.

The inputs are checked with the same contract as SNAIL; ``normalize_counts.R`` runs in the image's separate R
environment (``NETZOO_RSCRIPT``, default ``/opt/conda/envs/netzoo-r/bin/Rscript``). Writes the normalized
gene-by-sample matrix and ``<output>.normalization.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from netzoo_agent_core.data.normalization import (
    METHOD_LABELS,
    load_normalization_inputs,
    normalization_record_path,
)

R_METHODS = ("rle", "tmm", "quantile")


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RLE, TMM or quantile normalization in R.")
    parser.add_argument("-m", "--method", required=True, choices=R_METHODS)
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    inputs = load_normalization_inputs(args.expression, args.output, "", args.method)
    if inputs.errors:
        for error in inputs.errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    output = inputs.output_path
    output.parent.mkdir(parents=True, exist_ok=True)
    rscript = os.environ.get("NETZOO_RSCRIPT", "/opt/conda/envs/netzoo-r/bin/Rscript")
    script = Path(__file__).with_name("normalize_counts.R")
    with tempfile.TemporaryDirectory() as tmp:
        # R reads the checked matrix, so the gene and sample labels are the ones the checks saw.
        matrix = Path(tmp) / "counts.tsv"
        inputs.expression.to_csv(matrix, sep="\t", index_label="gene")
        r_record = Path(tmp) / "record.json"
        result = subprocess.run(
            [rscript, "--vanilla", str(script), args.method, str(matrix), str(output), str(r_record)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(result.stderr.strip() or result.stdout.strip(), file=sys.stderr)
            return result.returncode
        record = json.loads(r_record.read_text())

    record.update({
        "method_label": METHOD_LABELS[args.method],
        "expression_file": str(inputs.expression_path),
        "expression_sha256": checksum(inputs.expression_path),
        "output_file": str(output),
        "output_sha256": checksum(output),
    })
    normalization_record_path(output).write_text(json.dumps(record, indent=2) + "\n")
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
