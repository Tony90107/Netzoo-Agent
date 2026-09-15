from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.gene_validation import (  # noqa: E402
    GeneCache,
    GeneRecord,
    _websearch_gene_lookup,
    _structured_gene_lookup,
    validate_gene_identifiers,
)
from netzoo_agent_core.data.tables import _inspect_panda_inputs_impl  # noqa: E402


def _record(
    identifier: str,
    namespace: str,
    canonical_id: str | None,
    status: str = "valid",
) -> GeneRecord:
    return GeneRecord(
        identifier=identifier,
        normalized_identifier=identifier.casefold(),
        namespace=namespace,
        canonical_id=canonical_id,
        symbol=identifier,
        taxon="Homo sapiens",
        status=status,
        authority="NCBI Gene",
        source="test",
    )


def test_cache_miss_uses_remote_once_then_reads_local_cache(tmp_path):
    calls: list[list[str]] = []

    def remote_lookup(ids, namespace, taxon):
        calls.append(list(ids))
        return [
            _record(identifier, namespace, f"ncbi_gene:{index}")
            for index, identifier in enumerate(ids, start=1)
        ]

    cache_path = tmp_path / "gene.sqlite3"
    first = validate_gene_identifiers(
        ["TP53", "BRCA2"],
        "symbol_like",
        "Homo sapiens",
        cache_path=cache_path,
        remote_lookup=remote_lookup,
    )
    second = validate_gene_identifiers(
        ["TP53", "BRCA2"],
        "symbol_like",
        "Homo sapiens",
        cache_path=cache_path,
        remote_lookup=lambda *_: (_ for _ in ()).throw(
            AssertionError("cache hit should not call remote lookup")
        ),
    )

    assert calls == [["TP53", "BRCA2"]]
    assert first.online_queries == 1
    assert first.cache_hits == 0
    assert second.cache_hits == 2
    assert second.records["tp53"].source == "cache"


def test_websearch_accepts_only_trusted_exact_gene_results(monkeypatch):
    payload = {
        "results": [
            {
                "url": "https://www.ncbi.nlm.nih.gov/gene/7157",
                "title": "TP53 gene - Homo sapiens",
                "content": "TP53 tumor protein p53 GeneID 7157",
            },
            {
                "url": "https://example.test/gene/675",
                "title": "BRCA2 gene - Homo sapiens",
                "content": "BRCA2 GeneID 675",
            },
        ]
    }
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_web_search",
        lambda query: "Websearch MCP result:\n\n" + json.dumps(payload),
    )

    records = _websearch_gene_lookup(
        ["TP53", "BRCA2"], "symbol_like", "Homo sapiens"
    )

    # Search results are discovery evidence, not an authoritative existence check.
    assert records[0].status == "unverified"
    assert records[0].canonical_id == "ncbi_gene:7157"
    assert records[1].status == "unverified"


def test_websearch_fallback_cannot_authorize_panda_execution(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "on")

    def discovery_only(ids, namespace, taxon):
        return [
            GeneRecord(
                identifier=identifier,
                normalized_identifier=identifier.casefold(),
                namespace=namespace,
                canonical_id=None,
                symbol=identifier,
                taxon=taxon or None,
                status="unverified",
                authority="NCBI/Ensembl",
                source="websearch",
            )
            for identifier in ids
        ]

    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._online_gene_lookup",
        discovery_only,
    )
    expression = tmp_path / "expression.tsv"
    expression.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    motif = tmp_path / "motif.tsv"
    motif.write_text("MYC\tTP53\t1\nMAX\tTP53\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("MYC\tMAX\t1\n", encoding="utf-8")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi), taxon="Homo sapiens"
    )

    assert not ok
    assert "Websearch cannot authorize execution" in report


def test_structured_ncbi_lookup_marks_authoritative_absence_invalid(monkeypatch):
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: {
            "reports": [
                {
                    "gene": {
                        "geneId": "7157",
                        "symbol": "TP53",
                        "taxId": 9606,
                        "taxname": "Homo sapiens",
                    }
                }
            ]
        },
    )

    records = _structured_gene_lookup(
        ["TP53", "NOTAGENE"], "symbol_like", "Homo sapiens"
    )

    assert records[0].status == "valid"
    assert records[0].canonical_id == "ncbi_gene:7157"
    assert records[1].status == "invalid"
    assert records[1].source == "ncbi_datasets"


def test_structured_lookup_uses_response_taxon_not_query_text(monkeypatch):
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: {
            "reports": [
                {
                    "gene": {
                        "geneId": "22059",
                        "symbol": "Trp53",
                        "taxId": 10090,
                        "taxname": "Mus musculus",
                    }
                }
            ]
        },
    )

    [record] = _structured_gene_lookup(
        ["Trp53"], "symbol_like", "Homo sapiens"
    )

    assert record.status == "invalid"
    assert record.taxon == "Mus musculus"


def test_remote_validation_does_not_stop_after_fifty_identifiers(tmp_path):
    calls: list[list[str]] = []

    def remote_lookup(ids, namespace, taxon):
        calls.append(list(ids))
        return [
            _record(identifier, namespace, f"ncbi_gene:{index}")
            for index, identifier in enumerate(ids)
        ]

    identifiers = [f"GENE{index}" for index in range(51)]
    result = validate_gene_identifiers(
        identifiers,
        "symbol_like",
        "Homo sapiens",
        cache_path=tmp_path / "many.sqlite3",
        remote_lookup=remote_lookup,
    )

    assert sum(len(call) for call in calls) == 51
    assert len(calls) == 1
    assert set(result.status_counts()) == {"valid"}
    assert all(record.source != "remote_limit" for record in result.records.values())


def test_canonical_gene_mapping_matches_expression_and_motif_across_namespaces(
    tmp_path, monkeypatch
):
    cache_path = tmp_path / "gene.sqlite3"
    cache = GeneCache(cache_path)
    cache.upsert(
        [
            _record(
                "ENSG00000141510",
                "ensembl_gene",
                "ncbi_gene:7157",
            ),
            _record("TP53", "symbol_like", "ncbi_gene:7157"),
            _record("MYC", "symbol_like", "ncbi_gene:4609"),
            _record("MAX", "symbol_like", "ncbi_gene:4149"),
            _record(
                "ENSG00000136997",
                "ensembl_gene",
                "ncbi_gene:4609",
            ),
            _record(
                "ENSG00000149925",
                "ensembl_gene",
                "ncbi_gene:4149",
            ),
        ]
    )
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")

    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene_id\ts1\ts2\nENSG00000141510\t1\t2\n", encoding="utf-8"
    )
    motif = tmp_path / "motif.tsv"
    motif.write_text("MYC\tTP53\t1\nMAX\tTP53\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text(
        "ENSG00000136997\tENSG00000149925\t1\n"
        "ENSG00000149925\tENSG00000136997\t1\n",
        encoding="utf-8",
    )

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert ok, report
    assert "canonical gene matches found after identifier mapping" in report
    assert report.count("canonical gene matches found after identifier mapping") == 2


def test_authoritative_invalid_cache_entry_is_a_preflight_error(tmp_path, monkeypatch):
    cache_path = tmp_path / "gene.sqlite3"
    GeneCache(cache_path).upsert(
        [_record("NOTAGENE", "symbol_like", None, status="invalid")]
    )
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")

    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "gene_id\ts1\ts2\nNOTAGENE\t1\t2\n", encoding="utf-8"
    )
    motif = tmp_path / "motif.tsv"
    motif.write_text("TF1\tNOTAGENE\t1\nTF2\tNOTAGENE\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("TF1\tTF2\t1\n", encoding="utf-8")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert not ok
    assert "not recognized by the configured gene authority" in report


def test_authoritative_invalid_regulator_is_also_a_preflight_error(
    tmp_path, monkeypatch
):
    cache_path = tmp_path / "gene.sqlite3"
    GeneCache(cache_path).upsert(
        [_record("NOTATF", "symbol_like", None, status="invalid")]
    )
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(cache_path))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    expression = tmp_path / "expression.tsv"
    expression.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    motif = tmp_path / "motif.tsv"
    motif.write_text("NOTATF\tTP53\t1\nMAX\tTP53\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("NOTATF\tMAX\t1\n", encoding="utf-8")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi)
    )

    assert not ok
    assert "motif regulator genes not recognized" in report
    assert "NOTATF" in report


def test_taxon_scopes_cache_matching(tmp_path):
    cache_path = tmp_path / "gene.sqlite3"
    GeneCache(cache_path).upsert(
        [
            _record("QSOX1", "symbol_like", "ncbi_gene:5768"),
            GeneRecord(
                identifier="QSOX1",
                normalized_identifier="qsox1",
                namespace="symbol_like",
                canonical_id="ncbi_gene:104009",
                symbol="Qsox1",
                taxon="Mus musculus",
                status="valid",
                authority="NCBI Gene",
                source="test",
            ),
        ]
    )

    human = validate_gene_identifiers(
        ["QSOX1"], "symbol_like", "Homo sapiens", cache_path=cache_path
    )
    mouse = validate_gene_identifiers(
        ["QSOX1"], "symbol_like", "Mus musculus", cache_path=cache_path
    )

    assert human.records["qsox1"].canonical_id == "ncbi_gene:5768"
    assert mouse.records["qsox1"].canonical_id == "ncbi_gene:104009"


def test_cache_prunes_least_recently_used_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_MAX_ROWS", "2")
    cache_path = tmp_path / "gene.sqlite3"
    cache = GeneCache(cache_path)
    cache.upsert(
        [
            _record("TP53", "symbol_like", "ncbi_gene:7157"),
            _record("BRCA2", "symbol_like", "ncbi_gene:675"),
            _record("EGFR", "symbol_like", "ncbi_gene:1956"),
        ]
    )

    with sqlite3.connect(cache_path) as connection:
        row_count = connection.execute(
            "SELECT COUNT(*) FROM gene_validation_cache"
        ).fetchone()[0]

    assert row_count == 2


def test_stale_cache_refreshes_online_and_falls_back_offline(tmp_path, monkeypatch):
    cache_path = tmp_path / "gene.sqlite3"
    GeneCache(cache_path).upsert(
        [_record("TP53", "symbol_like", "ncbi_gene:7157")]
    )
    monkeypatch.setenv("NETZOO_GENE_CACHE_TTL_DAYS", "0")

    refreshed = validate_gene_identifiers(
        ["TP53"],
        "symbol_like",
        "Homo sapiens",
        cache_path=cache_path,
        remote_lookup=lambda ids, namespace, taxon: [
            _record(identifier, namespace, "ncbi_gene:9999") for identifier in ids
        ],
    )

    assert refreshed.online_queries == 1
    assert refreshed.stale_cache_hits == 0
    assert refreshed.records["tp53"].canonical_id == "ncbi_gene:9999"

    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    offline = validate_gene_identifiers(
        ["TP53"],
        "symbol_like",
        "Homo sapiens",
        cache_path=cache_path,
    )

    assert offline.stale_cache_hits == 1
    assert offline.records["tp53"].source == "stale_cache"
    assert offline.records["tp53"].canonical_id == "ncbi_gene:9999"
