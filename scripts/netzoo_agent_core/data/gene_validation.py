"""Offline-first gene identifier validation with a small SQLite cache.

The cache stores only identifiers that the agent has actually observed.  A
cache miss uses structured NCBI Datasets or Ensembl REST responses when online
validation is enabled. Websearch is only a discovery fallback after an API
failure; search presence or absence never becomes an authoritative verdict.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.parse import quote, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..settings import PROJECT_ROOT
from .gene_authority_records import (
    TAXON_REQUIRED_SOURCE,
    UNRECOGNIZED_PHRASE,
    GeneRecord,
    _candidate_from_result,
    _field,
    _gene_payload,
    _invalid_record,
    _normalise_identifier,
    _result_matches_identifier,
    _search_results,
    _taxon_matches,
    _taxon_required_record,
    _trusted_url,
)

__all__ = [
    "GeneRecord",
    "GeneValidationSummary",
    "GeneCache",
    "validate_gene_identifiers",
    "_structured_gene_lookup",
    "TAXON_REQUIRED_SOURCE",
    "UNRECOGNIZED_PHRASE",
    "TruncatedAuthorityResponseError",
    "UnsupportedNamespaceError",
    "WebsearchScopeError",
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
# One symbol can resolve to several reports (synonyms shared across genes),
# so a page must comfortably exceed the batch size.
_NCBI_PAGE_SIZE = 1000
_NCBI_MAX_PAGES = 20
_WEBSEARCH_BATCH_SIZE = 5
# Websearch can only ever produce "unverified", so it is an annotation for a
# handful of leftover labels, never a way to clear a whole axis. Past this
# many identifiers it would issue hundreds of sequential MCP calls to reach
# a verdict that cannot authorize execution anyway.
_WEBSEARCH_MAX_IDENTIFIERS = 20
_IDENTIFIER_PREVIEW_LIMIT = 5
# Published unauthenticated ceilings: NCBI allows about 3 requests/second and
# raises that to 10 with a key; Ensembl REST allows 15. Stay under each, and
# leave every number overridable because a shared deployment may need to be
# gentler still.
_AUTHORITY_MIN_INTERVAL_SECONDS = {
    "api.ncbi.nlm.nih.gov": 0.11 if os.environ.get("NCBI_API_KEY") else 0.35,
    "rest.ensembl.org": 0.08,
}
_DEFAULT_MIN_INTERVAL_SECONDS = 0.1
_AUTHORITY_MAX_ATTEMPTS = int(os.environ.get("NETZOO_GENE_HTTP_ATTEMPTS", "4"))
_AUTHORITY_BACKOFF_SECONDS = float(
    os.environ.get("NETZOO_GENE_HTTP_BACKOFF_SECONDS", "1.0")
)
_AUTHORITY_MAX_BACKOFF_SECONDS = float(
    os.environ.get("NETZOO_GENE_HTTP_MAX_BACKOFF_SECONDS", "8.0")
)
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_THROTTLE_LOCK = threading.Lock()
_LAST_REQUEST_AT: dict[str, float] = {}


def _min_interval(host: str) -> float:
    return _AUTHORITY_MIN_INTERVAL_SECONDS.get(host, _DEFAULT_MIN_INTERVAL_SECONDS)


def _throttle(host: str) -> None:
    """Space out requests to one authority host across the whole process."""
    interval = _min_interval(host)
    with _THROTTLE_LOCK:
        previous = _LAST_REQUEST_AT.get(host)
        now = time.monotonic()
        wait = 0.0 if previous is None else previous + interval - now
        _LAST_REQUEST_AT[host] = now + max(wait, 0.0)
    if wait > 0:
        time.sleep(wait)


def _retry_after_seconds(error: HTTPError, attempt: int) -> float:
    """Honor an explicit Retry-After, otherwise back off exponentially."""
    header = error.headers.get("Retry-After") if error.headers else None
    if header:
        try:
            return min(float(header), _AUTHORITY_MAX_BACKOFF_SECONDS)
        except ValueError:
            pass
    return min(
        _AUTHORITY_BACKOFF_SECONDS * (2 ** attempt),
        _AUTHORITY_MAX_BACKOFF_SECONDS,
    )


def _authority_headers(host: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "NetZoo-Agent gene-validator",
    }
    api_key = os.environ.get("NCBI_API_KEY", "").strip()
    if api_key and host.endswith("ncbi.nlm.nih.gov"):
        # An NCBI key raises the per-IP ceiling; it is never required.
        headers["api-key"] = api_key
    return headers


class TruncatedAuthorityResponseError(RuntimeError):
    """The authority reported more matches than it actually returned.

    A partial page is indistinguishable from a gene the authority does not
    know, so acting on one silently converts real genes into "not recognized".
    Fail instead: not knowing is a reportable state, being wrong is not.
    """


class WebsearchScopeError(RuntimeError):
    """Too many identifiers to annotate through the Websearch fallback."""


class UnsupportedNamespaceError(ValueError):
    """No structured gene authority is configured for this namespace.

    Distinct from a transport failure: retrying elsewhere cannot help, so the
    Websearch fallback must not be attempted for it.
    """


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


def _identifier_preview(values: Sequence[str]) -> str:
    """Render bounded identifier diagnostics without hiding truncation."""
    items = [str(value) for value in values]
    if len(items) <= _IDENTIFIER_PREVIEW_LIMIT:
        return ", ".join(items)
    remaining = len(items) - _IDENTIFIER_PREVIEW_LIMIT
    return (
        ", ".join(items[:_IDENTIFIER_PREVIEW_LIMIT])
        + f" (and {remaining} more; see detailed input inspection)"
    )


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

    def upsert(
        self,
        records: Iterable[GeneRecord],
        requested_taxon: str | None = None,
    ) -> None:
        """Store resolved records under the taxon the caller actually queried.

        A record's own ``taxon`` is the organism the authority reported, which
        for a rejected match is a different organism from the requested one.
        Keying on that would file "TP53 is invalid" under the very taxon where
        TP53 is valid, so a later correct query reads back a false refusal.
        """
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
                        self._key(
                            record.identifier,
                            record.namespace,
                            requested_taxon
                            if requested_taxon is not None
                            else (record.taxon or ""),
                        ),
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
    # NCBI Datasets and Ensembl REST are the resolvers that actually decide a
    # verdict, and neither needs a credential. Gating them on a Websearch key
    # left a deployment with no Tavily account unable to verify anything, and
    # planning then refused every real gene as "unverified offline" -- a setup
    # problem reported as a data problem. Tavily only affects the fallback.
    return True


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
    """Fetch one structured authority response through a tiny injectable seam.

    Throttled per host and retried on the statuses that mean "slow down or try
    again". Without this a single large expression matrix issues its batches
    back to back, trips the per-IP ceiling, and the resulting failure is
    reported downstream as if the genes themselves could not be verified.
    """
    host = (urlparse(url).hostname or "").casefold()
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    last_error: Exception | None = None
    for attempt in range(_AUTHORITY_MAX_ATTEMPTS):
        request = Request(
            url,
            data=body,
            method=method,
            headers=_authority_headers(host),
        )
        _throttle(host)
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed trusted hosts
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            last_error = error
            if error.code not in _RETRYABLE_STATUS:
                raise
            delay = _retry_after_seconds(error, attempt)
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
            delay = min(
                _AUTHORITY_BACKOFF_SECONDS * (2 ** attempt),
                _AUTHORITY_MAX_BACKOFF_SECONDS,
            )
        if attempt == _AUTHORITY_MAX_ATTEMPTS - 1:
            break
        time.sleep(delay)
    raise last_error if last_error is not None else RuntimeError(
        f"No authority response from {host}."
    )


def _paged_reports(url: str) -> list[dict[str, object]]:
    """Collect every dataset report, following NCBI's paging to the end.

    The endpoint answers with at most 20 reports unless a page size is given,
    and reports beyond the first page are simply absent. Reading only the first
    page made every symbol it did not reach look unrecognized, so a matrix of
    real genes came back almost entirely invalid.
    """
    reports: list[dict[str, object]] = []
    page_token = ""
    total_count: int | None = None
    complete = False
    for _ in range(_NCBI_MAX_PAGES):
        separator = "&" if "?" in url else "?"
        page_url = f"{url}{separator}page_size={_NCBI_PAGE_SIZE}"
        if page_token:
            page_url = f"{page_url}&page_token={quote(page_token, safe='')}"
        response = _query_authority_json(page_url)
        if not isinstance(response, dict):
            break
        page = response.get("reports", [])
        if isinstance(page, list):
            reports.extend(item for item in page if isinstance(item, dict))
        if total_count is None:
            try:
                total_count = int(response["total_count"])
            except (KeyError, TypeError, ValueError):
                total_count = None
        page_token = str(response.get("next_page_token") or "")
        if not page_token:
            complete = True
            break
        if not page:
            # A further page was promised but nothing came back; stopping here
            # would silently drop the rest.
            break
    if not complete:
        raise TruncatedAuthorityResponseError(
            f"Paging stopped after {len(reports)} report(s) with more pages pending."
        )
    if total_count is not None and len(reports) < total_count:
        raise TruncatedAuthorityResponseError(
            f"Authority reported {total_count} match(es) but returned "
            f"{len(reports)}."
        )
    return reports


def _structured_ncbi_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str
) -> list[GeneRecord]:
    if namespace == "symbol_like" and not taxon.strip():
        # The NCBI symbol endpoint requires a species token; "all" is rejected
        # as a taxonomy level above species, so every gene would come back with
        # no report and be recorded as invalid. A bare symbol without a species
        # genuinely is ambiguous across organisms, so say that instead.
        return [
            _taxon_required_record(identifier, namespace)
            for identifier in identifiers
        ]
    encoded_ids = quote(",".join(identifiers), safe=",")
    if namespace == "symbol_like":
        encoded_taxon = quote(taxon, safe="")
        url = (
            "https://api.ncbi.nlm.nih.gov/datasets/v2/gene/symbol/"
            f"{encoded_ids}/taxon/{encoded_taxon}/dataset_report"
        )
    else:
        url = (
            "https://api.ncbi.nlm.nih.gov/datasets/v2/gene/id/"
            f"{encoded_ids}/dataset_report"
        )
    reports = _paged_reports(url)
    candidates: dict[str, list[dict[str, object]]] = {
        _normalise_identifier(identifier): [] for identifier in identifiers
    }
    for report in reports:
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
                _field(gene, "commonName", "common_name"),
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
    raise UnsupportedNamespaceError(
        f"No structured gene authority is configured for {namespace!r}."
    )


def _online_gene_lookup(
    identifiers: Sequence[str], namespace: str, taxon: str = ""
) -> list[GeneRecord]:
    try:
        return _structured_gene_lookup(identifiers, namespace, taxon)
    except (UnsupportedNamespaceError, TruncatedAuthorityResponseError):
        # Websearch resolves the same namespaces the structured resolver does.
        # Sending it labels no authority is configured for buys nothing and,
        # on a real expression matrix, costs hundreds of sequential calls. A
        # truncated page is the same: the batch is large by definition, so the
        # fallback would only spend calls to arrive at "unverified" anyway.
        raise
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
    if len(requested) > _WEBSEARCH_MAX_IDENTIFIERS:
        raise WebsearchScopeError(
            f"{len(requested)} identifiers exceed the Websearch fallback bound "
            f"of {_WEBSEARCH_MAX_IDENTIFIERS}."
        )
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
                # "stale_cache" is already stored, and a taxon_required verdict
                # describes the missing query, not the identifier, so caching it
                # would answer a later well-formed query with a stale refusal.
                if record.source not in {"stale_cache", TAXON_REQUIRED_SOURCE}:
                    cacheable.append(record)
        cache.upsert(cacheable, requested_taxon=taxon)

    return summary
