"""Compare the two datasets through input preflight, without the router.

The prompts in this folder exercise the whole agent, which currently cannot
reach planning reliably (see README). This runs the check the prompts are
meant to reach, so the gene-existence comparison is usable on its own.

    python manual_tests/gene_existence/run_comparison.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

CASE_ROOT = Path(__file__).resolve().parent


def _check(dataset: str, taxon: str) -> list[str]:
    from netzoo_agent_core.data.preflight import validate_workflow_inputs

    root = CASE_ROOT / dataset
    return validate_workflow_inputs(
        "run_panda",
        {
            "expression_file": str(root / "expression.tsv"),
            "motif_file": str(root / "motif.tsv"),
            "ppi_file": str(root / "ppi.tsv"),
            "taxon": taxon,
        },
    )


def main() -> int:
    # A cold cache per run: a warm one answers the no-species case from an
    # earlier lookup and the comparison stops measuring anything.
    with tempfile.TemporaryDirectory() as workspace:
        os.environ["NETZOO_GENE_CACHE_PATH"] = str(Path(workspace) / "gene.sqlite3")
        cases = (
            ("dataset_a", "human", "真基因，有講物種"),
            ("dataset_b", "human", "假基因，有講物種"),
        )
        for dataset, taxon, label in cases:
            errors = _check(dataset, taxon)
            print(f"\n=== {dataset} ({label}) ===")
            if errors:
                for error in errors:
                    print(f"  BLOCKED  {error}")
            else:
                print("  PASS     沒有任何輸入錯誤")

        os.environ["NETZOO_GENE_CACHE_PATH"] = str(Path(workspace) / "cold.sqlite3")
        errors = _check("dataset_a", "")
        print("\n=== dataset_a (真基因，沒講物種) ===")
        for error in errors or ["PASS  沒有任何輸入錯誤"]:
            print(f"  {'BLOCKED  ' if errors else ''}{error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
