"""Offline-first gene identifier validation with a small SQLite cache.

The cache stores only identifiers that the agent has actually observed.  A
cache miss uses structured NCBI Datasets or Ensembl REST responses when online
validation is enabled. Websearch is only a discovery fallback after an API
failure; search presence or absence never becomes an authoritative verdict.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from ..settings import PROJECT_ROOT

__all__ = [
    "GeneRecord",
    "GeneValidationSummary",
    "GeneCache",
    "validate_gene_identifiers",
    "_structured_gene_lookup",
    "_websearch_gene_lookup",
    "_query_web_search",
]


_CACHE_ENV = "NETZOO_GENE_CACHE_PATH"
_CACHE_TTL_ENV = "NETZOO_GENE_CACHE_TTL_DAYS"
_CACHE_REVIEW_TTL_ENV = "NETZOO_GENE_CACHE_REVIEW_TTL_DAYS"
_CACHE_MAX_ENV = "NETZOO_GENE_CACHE_MAX_ROWS"
_ONLINE_ENV = "NETZOO_GENE_ONLINE_LOOKUP"
_DEFAULT_CACHE_TTL_DAYS = 90
_DEFAULT_CACHE_REVIEW_TTL_DAYS = 30
_DEFAULT_CACHE_MAX_ROWS = 100_000
_REMOTE_BATCH_SIZE = 100
_WEBSEARCH_BATCH_SIZE = 5
_TRUSTED_HOSTS = ("ncbi.nlm.nih.gov", "ensembl.org")
_NCBI_GENE_URL = re.compile(r"/gene/(\d+)(?:[/?#]|$)", re.IGNORECASE)
_ENSEMBL_GENE_ID = re.compile(r"\bENS[A-Z0-9]*G\d+(?:\.\d+)?\b", re.IGNORECASE)


@dataclass(frozen=True)
class GeneRecord:
    """One authoritative or provisional resolution for an observed ID."""

    identifier: str
    normalized_identifier: str
    namespace: str
    canonical_id: str | None
    symbol: str | None
    taxon: str | None
    status: str
    authority: str
    source: str
    url: str | None = None


@dataclass
class GeneValidationSummary:
    records: dict[str, GeneRecord]
    cache_hits: int = 0
    stale_cache_hits: int = 0
    online_queries: int = 0

    @property
    def canonical_map(self) -> dict[str, str]:
        return {
            key: record.canonical_id
            for key, record in self.records.items()
            if record.status == "valid" and record.canonical_id
        }

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.records.values():
            counts[record.status] = counts.get(record.status, 0) + 1
        return counts


def _normalise_identifier(value: object) -> str:
    return str(value).strip().casefold()


def _cache_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    configured = os.environ.get(_CACHE_ENV)
    if configured:
        return Path(configured)
    return PROJECT_ROOT / ".netzoo" / "gene_validation.sqlite3"


@dataclass
class _CacheLookup:
    records: dict[str, GeneRecord]
    stale_records: dict[str, GeneRecord]


class GeneCache:
    """Small project-local cache for identifiers that were actually queried."""

    def __init__(self, path: str | Path | None = None):
        self.path = _cache_path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS gene_validation_cache (
                lookup_key TEXT PRIMARY KEY,
                identifier TEXT NOT NULL,
                normalized_identifier TEXT NOT NULL,
                namespace TEXT NOT NULL,
                taxon TEXT NOT NULL,
                canonical_id TEXT,
                symbol TEXT,
                status TEXT NOT NULL,
                authority TEXT NOT NULL,
                url TEXT,
                checked_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(gene_validation_cache)"
            ).fetchall()
        }
        if "last_accessed_at" not in columns:
            connection.execute(
                "ALTER TABLE gene_validation_cache ADD COLUMN last_accessed_at TEXT"
            )
            connection.execute(
                "UPDATE gene_validation_cache "
                "SET last_accessed_at = checked_at "
                "WHERE last_accessed_at IS NULL"
            )
            connection.commit()
        return connection

    @staticmethod
    def _key(identifier: str, namespace: str, taxon: str) -> str:
        return "|".join(
            (
                namespace.casefold().strip() or "unknown",
                taxon.casefold().strip(),
                _normalise_identifier(identifier),
            )
        )

    @staticmethod
    def _ttl_days(status: str) -> int:
        env_name = _CACHE_TTL_ENV if status == "valid" else _CACHE_REVIEW_TTL_ENV
        default = (
            _DEFAULT_CACHE_TTL_DAYS
            if status == "valid"
            else _DEFAULT_CACHE_REVIEW_TTL_DAYS
        )
        try:
            return max(0, int(os.environ.get(env_name, default)))
        except ValueError:
            return default

    @classmethod
    def _is_fresh(cls, checked_at: str, status: str) -> bool:
        try:
            timestamp = datetime.fromisoformat(checked_at)
        except ValueError:
            return False
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - timestamp
        return age < timedelta(days=cls._ttl_days(status))

    @staticmethod
    def _record_from_rows(
        grouped_rows: list[tuple],
        source: str,
    ) -> GeneRecord:
        normalized = grouped_rows[0][2]
        distinct_results = {(row[5], row[7], row[8]) for row in grouped_rows}
        if len(distinct_results) > 1:
            first = grouped_rows[0]
            return GeneRecord(
                identifier=first[1],
                normalized_identifier=normalized,
                namespace=first[3],
                canonical_id=None,
                symbol=first[6],
                taxon=None,
                status="ambiguous",
                authority="/".join(sorted({row[8] for row in grouped_rows})),
                source=source,
            )

        row = grouped_rows[0]
        _, identifier, normalized, row_namespace, row_taxon, canonical_id, symbol, status, authority, url, _, _ = row
        return GeneRecord(
            identifier=identifier,
            normalized_identifier=normalized,
            namespace=row_namespace,
            canonical_id=canonical_id,
            symbol=symbol,
            taxon=row_taxon or None,
            status=status,
            authority=authority,
            source=source,
            url=url,
        )

    def get_many(
        self,
        identifiers: Sequence[str],
        namespace: str,
        taxon: str = "",
    ) -> _CacheLookup:
        if not identifiers:
            return _CacheLookup(records={}, stale_records={})
        placeholders = ",".join("?" for _ in identifiers)
        connection = self._connect()
        try:
            if taxon:
                keys = [self._key(identifier, namespace, taxon) for identifier in identifiers]
                rows = connection.execute(
                    f"SELECT lookup_key, identifier, normalized_identifier, namespace, "
                    f"taxon, canonical_id, symbol, status, authority, url, "
                    f"checked_at, last_accessed_at "
                    f"FROM gene_validation_cache WHERE lookup_key IN ({placeholders})",
                    keys,
                ).fetchall()
            else:
                rows = connection.execute(
                    f"SELECT lookup_key, identifier, normalized_identifier, namespace, "
                    f"taxon, canonical_id, symbol, status, authority, url, "
                    f"checked_at, last_accessed_at "
                    f"FROM gene_validation_cache WHERE namespace = ? "
                    f"AND normalized_identifier IN ({placeholders}) "
                    "ORDER BY last_accessed_at DESC, checked_at DESC",
                    [namespace, *[_normalise_identifier(identifier) for identifier in identifiers]],
                ).fetchall()
            if rows:
                access_time = datetime.now(timezone.utc).isoformat()
                row_keys = [row[0] for row in rows]
                access_placeholders = ",".join("?" for _ in row_keys)
                connection.execute(
                    f"UPDATE gene_validation_cache SET last_accessed_at = ? "
                    f"WHERE lookup_key IN ({access_placeholders})",
                    [access_time, *row_keys],
                )
                connection.commit()
        finally:
            connection.close()

        grouped: dict[str, list[tuple]] = {}
        for row in rows:
            grouped.setdefault(row[2], []).append(row)

        records: dict[str, GeneRecord] = {}
        stale_records: dict[str, GeneRecord] = {}
        for normalized, grouped_rows in grouped.items():
            fresh_rows = [
                row for row in grouped_rows if self._is_fresh(row[10], row[7])
            ]
            if fresh_rows:
                records[normalized] = self._record_from_rows(fresh_rows, "cache")
            else:
                stale_records[normalized] = self._record_from_rows(
                    grouped_rows, "stale_cache"
                )
        return _CacheLookup(records=records, stale_records=stale_records)

    def upsert(self, records: Iterable[GeneRecord]) -> None:
        rows = list(records)
        if not rows:
            return
        now = datetime.now(timezone.utc).isoformat()
        connection = self._connect()
        try:
            connection.executemany(
                """
                INSERT INTO gene_validation_cache (
                    lookup_key, identifier, normalized_identifier, namespace, taxon,
                    canonical_id, symbol, status, authority, url, checked_at,
                    last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lookup_key) DO UPDATE SET
                    identifier=excluded.identifier,
                    normalized_identifier=excluded.normalized_identifier,
                    canonical_id=excluded.canonical_id,
                    symbol=excluded.symbol,
                    status=excluded.status,
                    authority=excluded.authority,
                    url=excluded.url,
                    checked_at=excluded.checked_at,
                    last_accessed_at=excluded.last_accessed_at
                """,
                [
                    (
                        self._key(record.identifier, record.namespace, record.taxon or ""),
                        record.identifier,
                        record.normalized_identifier,
                        record.namespace,
                        record.taxon or "",
                        record.canonical_id,
                        record.symbol,
                        record.status,
                        record.authority,
                        record.url,
                        now,
                        now,
                    )
                    for record in rows
                ],
            )
            connection.commit()
            try:
                max_rows = max(
                    1,
                    int(os.environ.get(_CACHE_MAX_ENV, _DEFAULT_CACHE_MAX_ROWS)),
                )
            except ValueError:
                max_rows = _DEFAULT_CACHE_MAX_ROWS
            deleted = connection.execute(
                "DELETE FROM gene_validation_cache "
                "WHERE lookup_key NOT IN ("
                "SELECT lookup_key FROM gene_validation_cache "
                "ORDER BY last_accessed_at DESC, checked_at DESC "
                "LIMIT ?)",
                (max_rows,),
            ).rowcount
            connection.commit()
            if deleted:
                connection.execute("VACUUM")
        finally:
            connection.close()


def _online_lookup_enabled() -> bool:
    mode = os.environ.get(_ONLINE_ENV, "auto").casefold().strip()
    if mode in {"0", "false", "off", "disabled"}:
        return False
    if mode in {"1", "true", "on", "always"}:
        return True
    # Avoid surprising network calls in local/test environments where the
    # Websearch MCP has not been configured. Docker supplies this URL when the
    # agent is intentionally configured for external retrieval.
    return bool(os.environ.get("TAVILY_API_KEY") or os.environ.get("WEBSEARCH_MCP_URL"))


def _trusted_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").casefold().lstrip("www.")
    return any(hostname == host or hostname.endswith("." + host) for host in _TRUSTED_HOSTS)


def _contains_identifier(text: str, identifier: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9]){re.escape(identifier)}(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _result_matches_identifier(
    result: dict[str, object], identifier: str, namespace: str
) -> bool:
    """Require the queried label in an authoritative result's identity fields."""
    title_url = " ".join(str(result.get(field) or "") for field in ("title", "url"))
    if namespace == "symbol_like":
        title = str(result.get("title") or "")
        return bool(
            re.match(
                rf"\s*{re.escape(identifier)}(?![A-Za-z0-9])",
                title,
                re.IGNORECASE,
            )
        ) or bool(
            re.search(
                rf"Official Symbol\s+{re.escape(identifier)}(?![A-Za-z0-9])",
                str(result.get("content") or ""),
                re.IGNORECASE,
            )
        )
    if namespace == "ensembl_gene":
        return _contains_identifier(title_url, identifier)
    return _contains_identifier(
        " ".join(str(result.get(field) or "") for field in ("title", "content", "url")),
        identifier,
    )


def _search_results(text: str) -> list[dict[str, object]]:
    _, separator, payload = text.partition("\n\n")
    if not separator:
        return []
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return []
    results = parsed.get("results", []) if isinstance(parsed, dict) else []
    return [result for result in results if isinstance(result, dict)]


def _candidate_from_result(result: dict[str, object]) -> tuple[str, str, str] | None:
    url = str(result.get("url") or "")
    if not _trusted_url(url):
        return None
    ncbi_match = _NCBI_GENE_URL.search(url)
    if ncbi_match:
        return f"ncbi_gene:{ncbi_match.group(1)}", "NCBI Gene", url
    combined = " ".join(
        str(result.get(field) or "") for field in ("title", "content", "url")
    )
    ensembl_match = _ENSEMBL_GENE_ID.search(combined)
    if ensembl_match:
        return (
            f"ensembl_gene:{ensembl_match.group(0).upper()}",
            "Ensembl",
            url,
        )
    return None


def _query_web_search(query: str) -> str:
    """Load the routing adapter only when a cache miss needs network access."""
    from ..routing.retrieval import query_web_search

    return query_web_search(query)


def _query_authority_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> object:
    """Fetch one structured authority response through a tiny injectable seam."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NetZoo-Agent gene-validator",
        },
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed trusted hosts
        return json.loads(response.read().decode("utf-8"))


def _gene_payload(report: object) -> dict[str, object]:
    if not isinstance(report, dict):
        return {}
    nested = report.get("gene")
    return nested if isinstance(nested, dict) else report


def _field(payload: dict[str, object], *names: str) -> object:
    for name in names:
        value = payload.get(name)
        if value not in (None, ""):
            return value
    return None


def _taxon_matches(requested: str, tax_id: object, taxname: object) -> bool:
    if not requested.strip():
        return True
    wanted = requested.casefold().strip().replace("_", " ")
    observed = {
        str(tax_id or "").casefold().strip(),
        str(taxname or "").casefold().strip().replace("_", " "),
    }
    return wanted in observed


def _invalid_record(
    identifier: str,
    namespace: str,
    taxon: str,
    *,
    authority: str,
    source: str,
    observed_taxon: str | None = None,
) -> GeneRecord:
    return GeneRecord(
        identifier=identifier,
        normalized_identifier=_normalise_identifier(identifier),
        namespace=namespace,
        canonical_id=None,
        symbol=identifier if namespace == "symbol_like" else None,
        taxon=observed_taxon or taxon or None,
        status="invalid",
        authority=authority,
        source=source,
    )


def _structured_ncbi_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str
) -> list[GeneRecord]:
    encoded_ids = quote(",".join(identifiers), safe=",")
    if namespace == "symbol_like":
        encoded_taxon = quote(taxon or "all", safe="")
        url = (
            "https://api.ncbi.nlm.nih.gov/datasets/v2/gene/symbol/"
            f"{encoded_ids}/taxon/{encoded_taxon}/dataset_report"
        )
    else:
        url = (
            "https://api.ncbi.nlm.nih.gov/datasets/v2/gene/id/"
            f"{encoded_ids}/dataset_report"
        )
    response = _query_authority_json(url)
    reports = response.get("reports", []) if isinstance(response, dict) else []
    candidates: dict[str, list[dict[str, object]]] = {
        _normalise_identifier(identifier): [] for identifier in identifiers
    }
    for report in reports if isinstance(reports, list) else []:
        gene = _gene_payload(report)
        symbol = str(_field(gene, "symbol") or "")
        gene_id = str(_field(gene, "geneId", "gene_id") or "")
        synonyms = _field(gene, "synonyms")
        aliases = [symbol, gene_id]
        if isinstance(synonyms, list):
            aliases.extend(str(value) for value in synonyms)
        for alias in aliases:
            normalized = _normalise_identifier(alias)
            if normalized in candidates:
                candidates[normalized].append(gene)

    records: list[GeneRecord] = []
    for identifier in identifiers:
        normalized = _normalise_identifier(identifier)
        matches = candidates.get(normalized, [])
        taxon_matches = [
            gene
            for gene in matches
            if _taxon_matches(
                taxon,
                _field(gene, "taxId", "tax_id"),
                _field(gene, "taxname", "tax_name"),
            )
        ]
        if len(taxon_matches) > 1:
            records.append(
                GeneRecord(
                    identifier=identifier,
                    normalized_identifier=normalized,
                    namespace=namespace,
                    canonical_id=None,
                    symbol=identifier if namespace == "symbol_like" else None,
                    taxon=taxon or None,
                    status="ambiguous",
                    authority="NCBI Gene",
                    source="ncbi_datasets",
                )
            )
            continue
        if len(taxon_matches) == 1:
            gene = taxon_matches[0]
            gene_id = str(_field(gene, "geneId", "gene_id") or "")
            records.append(
                GeneRecord(
                    identifier=identifier,
                    normalized_identifier=normalized,
                    namespace=namespace,
                    canonical_id=f"ncbi_gene:{gene_id}" if gene_id else None,
                    symbol=str(_field(gene, "symbol") or "") or None,
                    # Cache under the caller's taxon token when one was supplied
                    # (for example both "9606" and "Homo sapiens" are valid API
                    # selectors); response fields were already checked above.
                    taxon=(
                        taxon
                        or str(_field(gene, "taxname", "tax_name") or "")
                        or None
                    ),
                    status="valid" if gene_id else "invalid",
                    authority="NCBI Gene",
                    source="ncbi_datasets",
                    url=f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}" if gene_id else None,
                )
            )
            continue
        observed_taxon = None
        if matches:
            observed_taxon = str(
                _field(matches[0], "taxname", "tax_name") or ""
            ) or None
        records.append(
            _invalid_record(
                identifier,
                namespace,
                taxon,
                authority="NCBI Gene",
                source="ncbi_datasets",
                observed_taxon=observed_taxon,
            )
        )
    return records


def _structured_ensembl_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str
) -> list[GeneRecord]:
    response = _query_authority_json(
        "https://rest.ensembl.org/lookup/id",
        method="POST",
        payload={"ids": list(identifiers)},
    )
    payload = response if isinstance(response, dict) else {}
    records: list[GeneRecord] = []
    for identifier in identifiers:
        gene = payload.get(identifier)
        if not isinstance(gene, dict):
            records.append(
                _invalid_record(
                    identifier,
                    namespace,
                    taxon,
                    authority="Ensembl",
                    source="ensembl_rest",
                )
            )
            continue
        species = str(gene.get("species") or "")
        gene_id = str(gene.get("id") or "").split(".", 1)[0].upper()
        is_gene = str(gene.get("object_type") or "").casefold() == "gene"
        is_taxon = _taxon_matches(taxon, None, species)
        valid = bool(gene_id and is_gene and is_taxon)
        records.append(
            GeneRecord(
                identifier=identifier,
                normalized_identifier=_normalise_identifier(identifier),
                namespace=namespace,
                canonical_id=f"ensembl_gene:{gene_id}" if valid else None,
                symbol=str(gene.get("display_name") or "") or None,
                taxon=(
                    taxon
                    if valid and taxon
                    else species.replace("_", " ") or taxon or None
                ),
                status="valid" if valid else "invalid",
                authority="Ensembl",
                source="ensembl_rest",
                url=(
                    f"https://www.ensembl.org/id/{gene_id}" if gene_id else None
                ),
            )
        )
    return records


def _structured_gene_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str = ""
) -> list[GeneRecord]:
    """Resolve IDs using response fields from an authoritative gene API."""
    requested = list(dict.fromkeys(identifier for identifier in identifiers if identifier))
    if namespace == "ensembl_gene":
        return _structured_ensembl_lookup(requested, namespace, taxon)
    if namespace in {"symbol_like", "ncbi_gene", "numeric_identifier"}:
        return _structured_ncbi_lookup(requested, namespace, taxon)
    raise ValueError(f"No structured gene authority is configured for {namespace!r}.")


def _online_gene_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str = ""
) -> list[GeneRecord]:
    try:
        return _structured_gene_lookup(identifiers, namespace, taxon)
    except Exception:
        if os.environ.get("TAVILY_API_KEY") or os.environ.get("WEBSEARCH_MCP_URL"):
            return _websearch_gene_lookup(identifiers, namespace, taxon)
        raise


def _websearch_gene_lookup(
    identifiers: Sequence[str],
    namespace: str,
    taxon: str = "",
) -> list[GeneRecord]:
    """Resolve a bounded batch through the existing Websearch MCP adapter."""
    requested = list(dict.fromkeys(identifier for identifier in identifiers if identifier))
    if not requested:
        return []
    if len(requested) > _WEBSEARCH_BATCH_SIZE:
        return [
            record
            for start in range(0, len(requested), _WEBSEARCH_BATCH_SIZE)
            for record in _websearch_gene_lookup(
                requested[start : start + _WEBSEARCH_BATCH_SIZE], namespace, taxon
            )
        ]

    quoted = " OR ".join(f'"{identifier}"' for identifier in requested)
    taxon_clause = f' "{taxon}"' if taxon else ""
    query = (
        "site:ncbi.nlm.nih.gov/gene OR site:ensembl.org "
        f"({quoted}){taxon_clause}"
    )
    search_text = _query_web_search(query)
    results = _search_results(search_text)
    records: list[GeneRecord] = []
    for identifier in requested:
        matching_candidates: dict[str, tuple[str, str]] = {}
        for result in results:
            url = str(result.get("url") or "")
            if not _trusted_url(url) or not _result_matches_identifier(
                result, identifier, namespace
            ):
                continue
            candidate = _candidate_from_result(result)
            if candidate:
                canonical_id, authority, candidate_url = candidate
                matching_candidates[canonical_id] = (authority, candidate_url)

        normalized = _normalise_identifier(identifier)
        if len(matching_candidates) == 1:
            canonical_id, (authority, url) = next(iter(matching_candidates.items()))
            records.append(
                GeneRecord(
                    identifier=identifier,
                    normalized_identifier=normalized,
                    namespace=namespace,
                    canonical_id=canonical_id,
                    symbol=identifier if namespace == "symbol_like" else None,
                    taxon=taxon or None,
                    status="unverified",
                    authority=authority,
                    source="websearch",
                    url=url,
                )
            )
        elif len(matching_candidates) > 1:
            records.append(
                GeneRecord(
                    identifier=identifier,
                    normalized_identifier=normalized,
                    namespace=namespace,
                    canonical_id=None,
                    symbol=identifier if namespace == "symbol_like" else None,
                    taxon=taxon or None,
                    status="ambiguous",
                    authority="NCBI/Ensembl",
                    source="websearch",
                )
            )
        else:
            # Search absence is not authoritative proof of invalidity.
            records.append(
                GeneRecord(
                    identifier=identifier,
                    normalized_identifier=normalized,
                    namespace=namespace,
                    canonical_id=None,
                    symbol=identifier if namespace == "symbol_like" else None,
                    taxon=taxon or None,
                    status="unverified",
                    authority="NCBI/Ensembl",
                    source="websearch",
                )
            )
    return records


def validate_gene_identifiers(
    identifiers: Iterable[str],
    namespace: str,
    taxon: str = "",
    *,
    cache_path: str | Path | None = None,
    remote_lookup: Callable[[Sequence[str], str, str], Iterable[GeneRecord]] | None = None,
) -> GeneValidationSummary:
    """Resolve observed IDs from cache, then query only cache misses.

    ``remote_lookup`` is injectable so tests and deployments can provide a
    structured resolver without changing the cache or validation behavior.
    """
    unique: list[str] = []
    seen: set[str] = set()
    for identifier in identifiers:
        value = str(identifier).strip()
        normalized = _normalise_identifier(value)
        if value and normalized not in seen:
            unique.append(value)
            seen.add(normalized)

    if not unique:
        return GeneValidationSummary(records={})

    cache = GeneCache(cache_path)
    cache_lookup = cache.get_many(unique, namespace, taxon)
    records = cache_lookup.records
    stale_records = cache_lookup.stale_records
    missing = [
        identifier
        for identifier in unique
        if _normalise_identifier(identifier) not in records
    ]
    summary = GeneValidationSummary(
        records=records,
        cache_hits=len(records),
    )
    if not missing:
        return summary

    resolver = remote_lookup
    if resolver is None and _online_lookup_enabled():
        resolver = _online_gene_lookup

    if resolver is None:
        records.update(stale_records)
        summary.stale_cache_hits = len(stale_records)
        for identifier in missing:
            normalized = _normalise_identifier(identifier)
            if normalized in records:
                continue
            records[normalized] = GeneRecord(
                identifier=identifier,
                normalized_identifier=normalized,
                namespace=namespace,
                canonical_id=None,
                symbol=identifier if namespace == "symbol_like" else None,
                taxon=taxon or None,
                status="unverified",
                authority="NCBI/Ensembl",
                source="offline",
            )
        return summary

    for start in range(0, len(missing), _REMOTE_BATCH_SIZE):
        batch = missing[start : start + _REMOTE_BATCH_SIZE]
        summary.online_queries += 1
        try:
            resolved = list(resolver(batch, namespace, taxon))
        except Exception:
            resolved = []
        resolved_by_id = {
            record.normalized_identifier: record for record in resolved
        }
        cacheable: list[GeneRecord] = []
        for identifier in batch:
            normalized = _normalise_identifier(identifier)
            record = resolved_by_id.get(normalized)
            if record is None:
                stale_record = stale_records.get(normalized)
                if stale_record is not None:
                    record = stale_record
                    summary.stale_cache_hits += 1
                else:
                    record = GeneRecord(
                        identifier=identifier,
                        normalized_identifier=normalized,
                        namespace=namespace,
                        canonical_id=None,
                        symbol=identifier if namespace == "symbol_like" else None,
                        taxon=taxon or None,
                        status="unverified",
                        authority="NCBI/Ensembl",
                        source="remote_error",
                    )
            records[normalized] = record
            if record.status in {"valid", "ambiguous", "invalid"}:
                if record.source != "stale_cache":
                    cacheable.append(record)
        cache.upsert(cacheable)

    return summary
