"""Seed deterministic gene metadata for the manual validation fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from netzoo_agent_core.data.gene_validation import GeneCache, GeneRecord  # noqa: E402


def _record(
    identifier: str,
    namespace: str,
    canonical_id: str | None,
    *,
    taxon: str = "Homo sapiens",
    status: str = "valid",
    symbol: str | None = None,
) -> GeneRecord:
    return GeneRecord(
        identifier=identifier,
        normalized_identifier=identifier.casefold(),
        namespace=namespace,
        canonical_id=canonical_id,
        symbol=symbol or identifier,
        taxon=taxon,
        status=status,
        authority="NCBI Gene",
        source="manual_fixture",
    )


def seed_cache(output: str | Path) -> Path:
    path = Path(output)
    GeneCache(path).upsert(
        [
            _record("ENSG00000141510", "ensembl_gene", "ncbi_gene:7157", symbol="TP53"),
            _record("TP53", "symbol_like", "ncbi_gene:7157"),
            _record("ENSG00000136997", "ensembl_gene", "ncbi_gene:4609", symbol="MYC"),
            _record("MYC", "symbol_like", "ncbi_gene:4609"),
            _record("ENSG00000149925", "ensembl_gene", "ncbi_gene:4149", symbol="MAX"),
            _record("MAX", "symbol_like", "ncbi_gene:4149"),
            _record("NOT_A_REAL_GENE_999", "opaque", None, status="invalid"),
            _record(
                "QSOX1",
                "symbol_like",
                "ncbi_gene:5768",
                taxon="Homo sapiens",
            ),
            _record(
                "QSOX1",
                "symbol_like",
                "ncbi_gene:104009",
                taxon="Mus musculus",
                symbol="Qsox1",
            ),
        ]
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="SQLite cache path to create")
    args = parser.parse_args()
    print(f"Seeded gene fixture cache: {seed_cache(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
