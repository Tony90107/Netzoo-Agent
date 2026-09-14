"""Run deterministic direct checks for the gene validation flow."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from netzoo_agent_core.data.tables import _inspect_panda_inputs_impl  # noqa: E402
from seed_cache import seed_cache  # noqa: E402


CASE_ROOT = Path(__file__).resolve().parent


def _inspect(case: str, *, taxon: str = "") -> tuple[str, bool]:
    root = CASE_ROOT / case
    report, ok, _ = _inspect_panda_inputs_impl(
        str(root / "expression.tsv"),
        str(root / "motif.tsv"),
        str(root / "ppi.tsv"),
        taxon=taxon,
    )
    return report, ok


def main() -> int:
    old_cache = os.environ.get("NETZOO_GENE_CACHE_PATH")
    old_online = os.environ.get("NETZOO_GENE_ONLINE_LOOKUP")
    results: list[bool] = []
    with TemporaryDirectory() as temporary_dir:
        cache_path = Path(temporary_dir) / "gene-validation-fixture.sqlite3"
        seed_cache(cache_path)
        os.environ["NETZOO_GENE_CACHE_PATH"] = str(cache_path)
        os.environ["NETZOO_GENE_ONLINE_LOOKUP"] = "off"
        try:
            checks = (
                (
                    "valid_canonical_match",
                    True,
                    "canonical gene matches found after identifier mapping",
                    "",
                ),
                (
                    "expression_motif_conflict",
                    False,
                    "no exact ID overlap between motif target gene and expression gene IDs",
                    "",
                ),
                (
                    "motif_ppi_conflict",
                    False,
                    "no exact ID overlap between motif TF and PPI TF IDs",
                    "",
                ),
                (
                    "unknown_gene",
                    False,
                    "not recognized by the configured gene authority",
                    "Homo sapiens",
                ),
            )
            for case, expected_ok, expected_text, taxon in checks:
                report, ok = _inspect(case, taxon=taxon)
                passed = ok == expected_ok and expected_text in report
                results.append(passed)
                print(f"[{'PASS' if passed else 'FAIL'}] {case}")
                print(report)

            ambiguous_report, ambiguous_ok = _inspect("taxon_ambiguous")
            ambiguous_passed = (
                ambiguous_ok and "multiple authority matches" in ambiguous_report
            )
            results.append(ambiguous_passed)
            print(f"[{'PASS' if ambiguous_passed else 'FAIL'}] taxon_ambiguous_without_taxon")
            print(ambiguous_report)

            scoped_report, scoped_ok = _inspect(
                "taxon_ambiguous", taxon="Homo sapiens"
            )
            scoped_passed = scoped_ok and "1 valid" in scoped_report
            results.append(scoped_passed)
            print(f"[{'PASS' if scoped_passed else 'FAIL'}] taxon_ambiguous_human")
            print(scoped_report)
        finally:
            if old_cache is None:
                os.environ.pop("NETZOO_GENE_CACHE_PATH", None)
            else:
                os.environ["NETZOO_GENE_CACHE_PATH"] = old_cache
            if old_online is None:
                os.environ.pop("NETZOO_GENE_ONLINE_LOOKUP", None)
            else:
                os.environ["NETZOO_GENE_ONLINE_LOOKUP"] = old_online

    passed = sum(results)
    print(f"Summary: {passed}/{len(results)} direct checks passed.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
