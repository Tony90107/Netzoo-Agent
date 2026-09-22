"""Normalize gene-authority records without performing network or cache I/O."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse


_TRUSTED_HOSTS = ("ncbi.nlm.nih.gov", "ensembl.org")
_NCBI_GENE_URL = re.compile(r"/gene/(\d+)(?:[/?#]|$)", re.IGNORECASE)
_ENSEMBL_GENE_ID = re.compile(r"\bENS[A-Z0-9]*G\d+(?:\.\d+)?\b", re.IGNORECASE)

# Equivalent spellings for the organisms these workflows are actually run on.
# Each group holds the NCBI tax ID, the scientific name, and the common names
# that NCBI and Ensembl accept as query selectors.
_TAXON_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"9606", "homo sapiens", "human"}),
    frozenset({"10090", "mus musculus", "mouse", "house mouse"}),
    frozenset({"10116", "rattus norvegicus", "rat", "norway rat"}),
    frozenset({"7227", "drosophila melanogaster", "fruit fly"}),
    frozenset({"6239", "caenorhabditis elegans", "roundworm", "nematode"}),
    frozenset({"4932", "saccharomyces cerevisiae", "yeast", "baker's yeast"}),
    frozenset({"7955", "danio rerio", "zebrafish"}),
    frozenset({"3702", "arabidopsis thaliana", "thale cress"}),
    frozenset({"9615", "canis lupus familiaris", "dog"}),
    frozenset({"9913", "bos taurus", "cattle", "cow"}),
    frozenset({"9823", "sus scrofa", "pig"}),
    frozenset({"9544", "macaca mulatta", "rhesus monkey"}),
    frozenset({"9031", "gallus gallus", "chicken"}),
    frozenset({"8355", "xenopus laevis", "african clawed frog"}),
)
_TAXON_ALIASES: dict[str, frozenset[str]] = {
    name: group for group in _TAXON_GROUPS for name in group
}

TAXON_REQUIRED_SOURCE = "taxon_required"
UNRECOGNIZED_PHRASE = "not recognized by the configured gene authority: "


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


def _normalise_identifier(value: object) -> str:
    return str(value).strip().casefold()


def _trusted_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").casefold().lstrip("www.")
    return any(
        hostname == host or hostname.endswith("." + host) for host in _TRUSTED_HOSTS
    )


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
        " ".join(
            str(result.get(field) or "")
            for field in ("title", "content", "url")
        ),
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


def _taxon_tokens(value: str) -> set[str]:
    """Expand one taxon spelling into every equivalent spelling we accept."""
    normalized = str(value or "").casefold().strip().replace("_", " ")
    if not normalized:
        return set()
    return {normalized, *_TAXON_ALIASES.get(normalized, frozenset())}


def _taxon_matches(
    requested: str,
    tax_id: object,
    taxname: object,
    common_name: object = None,
) -> bool:
    """Compare a requested taxon with every identity field returned by the API."""
    if not requested.strip():
        return True
    wanted = _taxon_tokens(requested)
    observed: set[str] = set()
    for value in (tax_id, taxname, common_name):
        observed |= _taxon_tokens(str(value or ""))
    return bool(wanted & observed)


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


def _taxon_required_record(identifier: str, namespace: str) -> GeneRecord:
    """Report a symbol that cannot be resolved because no species was given."""
    return GeneRecord(
        identifier=identifier,
        normalized_identifier=_normalise_identifier(identifier),
        namespace=namespace,
        canonical_id=None,
        symbol=identifier,
        taxon=None,
        status="ambiguous",
        authority="NCBI Gene",
        source=TAXON_REQUIRED_SOURCE,
    )
