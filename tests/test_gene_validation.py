from __future__ import annotations

import json
import pytest
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.data.gene_validation import (  # noqa: E402
    TAXON_REQUIRED_SOURCE,
    GeneCache,
    TruncatedAuthorityResponseError,
    GeneRecord,
    UnsupportedNamespaceError,
    WebsearchScopeError,
    _authority_headers,
    _online_gene_lookup,
    _query_authority_json,
    _websearch_gene_lookup,
    _structured_gene_lookup,
    validate_gene_identifiers,
)
from netzoo_agent_core.data.tables import _identifier_namespace  # noqa: E402
from netzoo_agent_core.data.preflight import (  # noqa: E402
    _validate_workflow_inputs_impl,
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


def test_synthetic_test_mode_allows_unknown_labels_with_explicit_warning(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)

    expression = tmp_path / "expression.tsv"
    expression.write_text("gene\ts1\ts2\nGeneA\t1\t2\nGeneB\t2\t1\n", encoding="utf-8")
    motif = tmp_path / "motif.tsv"
    motif.write_text("TF1\tGeneA\t1\nTF2\tGeneB\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("TF1\tTF2\t1\n", encoding="utf-8")

    report, ok, _ = _inspect_panda_inputs_impl(
        str(expression), str(motif), str(ppi), taxon="Homo sapiens"
    )

    assert ok, report
    assert "status: test_only" in report
    assert "accepted as test-only identifiers" in report


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


def _ncbi_report(symbol: str, gene_id: str, tax_id: str, taxname: str, common: str):
    return {
        "reports": [
            {
                "gene": {
                    "geneId": gene_id,
                    "symbol": symbol,
                    "taxId": tax_id,
                    "taxname": taxname,
                    "commonName": common,
                }
            }
        ]
    }


def test_a_common_name_taxon_matches_the_scientific_name_in_the_response(monkeypatch):
    """NCBI accepts "human" as a selector but answers with "Homo sapiens"."""
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: _ncbi_report(
            "TP53", "7157", "9606", "Homo sapiens", "human"
        ),
    )

    [record] = _structured_gene_lookup(["TP53"], "symbol_like", "human")

    assert record.status == "valid"
    assert record.canonical_id == "ncbi_gene:7157"


def test_a_taxon_alias_matches_even_when_no_common_name_is_returned(monkeypatch):
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: {
            "reports": [
                {"gene": {"geneId": "22059", "symbol": "Trp53", "taxId": "10090"}}
            ]
        },
    )

    [record] = _structured_gene_lookup(["Trp53"], "symbol_like", "mouse")

    assert record.status == "valid"


def test_a_symbol_without_a_species_is_unresolvable_rather_than_invalid(monkeypatch):
    """The NCBI symbol endpoint rejects a taxon above species such as "all"."""

    def fail(*args, **kwargs):
        raise AssertionError("no authority call may be made without a species")

    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json", fail
    )

    records = _structured_gene_lookup(["TP53", "BRCA1"], "symbol_like", "")

    assert [record.status for record in records] == ["ambiguous", "ambiguous"]
    assert {record.source for record in records} == {TAXON_REQUIRED_SOURCE}


def test_a_missing_species_blocks_preflight_and_names_the_remedy(tmp_path, monkeypatch):
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._online_lookup_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("no authority call may be made without a species")
        ),
    )
    expression = tmp_path / "expression.tsv"
    expression.write_text("gene\ts1\ts2\nTP53\t1\t2\nBRCA1\t2\t1\n", encoding="utf-8")
    motif = tmp_path / "motif.tsv"
    motif.write_text("STAT1\tTP53\t1\nSTAT3\tBRCA1\t1\n", encoding="utf-8")
    ppi = tmp_path / "ppi.tsv"
    ppi.write_text("STAT1\tSTAT3\t1\n", encoding="utf-8")

    errors = _validate_workflow_inputs_impl(
        "run_panda",
        {
            "expression_file": str(expression),
            "motif_file": str(motif),
            "ppi_file": str(ppi),
            "taxon": "",
        },
    )

    assert errors
    assert all("cannot be verified without a species" in error for error in errors)
    assert all("not recognized" not in error for error in errors)


def test_a_species_mismatch_is_cached_under_the_requested_taxon(tmp_path, monkeypatch):
    """A mouse-only match must not file "invalid" under the taxon it belongs to."""
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._online_lookup_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: _ncbi_report(
            "Trp53", "22059", "10090", "Mus musculus", "house mouse"
        ),
    )
    cache_path = tmp_path / "gene.sqlite3"

    mismatch = validate_gene_identifiers(
        ["Trp53"], "symbol_like", "Homo sapiens", cache_path=cache_path
    )
    assert mismatch.records["trp53"].status == "invalid"

    keys = {
        row[0]
        for row in sqlite3.connect(cache_path).execute(
            "SELECT lookup_key FROM gene_validation_cache"
        )
    }
    assert keys == {"symbol_like|homo sapiens|trp53"}

    mouse = validate_gene_identifiers(
        ["Trp53"], "symbol_like", "Mus musculus", cache_path=cache_path
    )
    assert mouse.records["trp53"].status == "valid"


def test_a_taxon_required_verdict_is_never_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._online_lookup_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda *args, **kwargs: {"messages": [{"warning": {}}]},
    )
    cache_path = tmp_path / "gene.sqlite3"

    summary = validate_gene_identifiers(
        ["TP53"], "symbol_like", "", cache_path=cache_path
    )

    assert summary.records["tp53"].source == TAXON_REQUIRED_SOURCE
    assert not list(
        sqlite3.connect(cache_path).execute(
            "SELECT lookup_key FROM gene_validation_cache"
        )
    )


def test_every_symbol_is_resolved_even_when_the_authority_pages_the_answer(monkeypatch):
    """NCBI caps a page at 20 reports; unread pages are not absent genes."""
    symbols = [f"GENE{index}" for index in range(45)]
    pages = [symbols[:20], symbols[20:40], symbols[40:]]
    seen_urls = []

    def paged(url, **kwargs):
        seen_urls.append(url)
        index = min(len(seen_urls) - 1, len(pages) - 1)
        payload = {
            "reports": [
                {
                    "gene": {
                        "geneId": str(1000 + symbols.index(symbol)),
                        "symbol": symbol,
                        "taxId": "9606",
                        "taxname": "Homo sapiens",
                    }
                }
                for symbol in pages[index]
            ]
        }
        if index < len(pages) - 1:
            payload["next_page_token"] = f"token-{index}"
        return payload

    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json", paged
    )

    records = _structured_gene_lookup(symbols, "symbol_like", "human")

    assert len(seen_urls) == 3
    assert "page_size=" in seen_urls[0]
    assert "page_token=token-0" in seen_urls[1]
    assert {record.status for record in records} == {"valid"}


def test_a_rate_limited_authority_is_retried_rather_than_reported_as_invalid(monkeypatch):
    import email.message
    from urllib.error import HTTPError

    attempts = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"reports": []}'

    def flaky(request, timeout=None):
        attempts.append(request.full_url)
        if len(attempts) < 3:
            headers = email.message.Message()
            headers["Retry-After"] = "0"
            raise HTTPError(request.full_url, 429, "Too Many Requests", headers, None)
        return _Response()

    monkeypatch.setattr("netzoo_agent_core.data.gene_validation.urlopen", flaky)
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._throttle", lambda host: None
    )

    assert _query_authority_json("https://api.ncbi.nlm.nih.gov/probe") == {"reports": []}
    assert len(attempts) == 3


def test_a_client_error_is_not_retried(monkeypatch):
    import email.message
    from urllib.error import HTTPError

    attempts = []

    def not_found(request, timeout=None):
        attempts.append(request.full_url)
        raise HTTPError(
            request.full_url, 404, "Not Found", email.message.Message(), None
        )

    monkeypatch.setattr("netzoo_agent_core.data.gene_validation.urlopen", not_found)
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._throttle", lambda host: None
    )

    with pytest.raises(HTTPError):
        _query_authority_json("https://api.ncbi.nlm.nih.gov/probe")
    assert len(attempts) == 1


def test_an_ncbi_key_is_sent_only_to_ncbi(monkeypatch):
    monkeypatch.setenv("NCBI_API_KEY", "secret-key")
    assert _authority_headers("api.ncbi.nlm.nih.gov")["api-key"] == "secret-key"
    assert "api-key" not in _authority_headers("rest.ensembl.org")


def test_a_spreadsheet_mangled_label_does_not_disable_its_whole_axis():
    """One date-serial label must not make a thousand real genes unverifiable."""
    identifiers = [f"GENE{index}" for index in range(40)] + ["41157"]

    assert _identifier_namespace(identifiers) == "symbol_like"
    assert _identifier_namespace(["TP53", "41157"]) == "opaque"


def test_a_websearch_fallback_never_runs_for_a_whole_expression_axis(monkeypatch):
    called = []
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_web_search",
        lambda query: called.append(query) or "",
    )

    with pytest.raises(WebsearchScopeError):
        _websearch_gene_lookup([f"GENE{index}" for index in range(60)], "symbol_like")
    assert called == []


def test_an_unserved_namespace_does_not_reach_the_websearch_fallback(monkeypatch):
    called = []
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._websearch_gene_lookup",
        lambda *args, **kwargs: called.append(args) or [],
    )
    monkeypatch.setenv("TAVILY_API_KEY", "present")

    with pytest.raises(UnsupportedNamespaceError):
        _online_gene_lookup(["weird.id"], "opaque", "human")
    assert called == []


def test_a_short_page_is_an_error_rather_than_a_batch_of_missing_genes(monkeypatch):
    """A page that omits matches must never read as "these genes do not exist"."""
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda url, **kwargs: {
            "reports": [
                {
                    "gene": {
                        "geneId": "7157",
                        "symbol": "TP53",
                        "taxId": "9606",
                        "taxname": "Homo sapiens",
                    }
                }
            ],
            "total_count": 40,
        },
    )

    with pytest.raises(TruncatedAuthorityResponseError):
        _structured_gene_lookup(["TP53", "BRCA1"], "symbol_like", "human")


def test_a_promised_page_that_never_arrives_is_an_error(monkeypatch):
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda url, **kwargs: {"reports": [], "next_page_token": "always-more"},
    )

    with pytest.raises(TruncatedAuthorityResponseError):
        _structured_gene_lookup(["TP53"], "symbol_like", "human")


def test_a_truncated_page_never_falls_through_to_websearch(monkeypatch):
    called = []
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._websearch_gene_lookup",
        lambda *args, **kwargs: called.append(args) or [],
    )
    monkeypatch.setenv("TAVILY_API_KEY", "present")
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda url, **kwargs: {"reports": [], "total_count": 12},
    )

    with pytest.raises(TruncatedAuthorityResponseError):
        _online_gene_lookup(["TP53"], "symbol_like", "human")
    assert called == []


def test_an_unverified_batch_is_reported_as_unverified_not_as_absent(monkeypatch):
    """The whole point of failing closed: the wording must not accuse the genes."""
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._online_lookup_enabled", lambda: True
    )
    monkeypatch.setattr(
        "netzoo_agent_core.data.gene_validation._query_authority_json",
        lambda url, **kwargs: {"reports": [], "total_count": 5},
    )

    summary = validate_gene_identifiers(["TP53", "BRCA1"], "symbol_like", "human")

    assert {record.status for record in summary.records.values()} == {"unverified"}
    assert all(
        record.status != "invalid" for record in summary.records.values()
    )
