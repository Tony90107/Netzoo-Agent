"""Advisory repair hints for gene labels the authority did not accept.

Strictly advisory. A hint never changes a verdict, never authorizes execution,
and is only produced after validation has already failed. The model proposes a
reading; NCBI or Ensembl decides whether that reading is a real gene, and only
a reading the authority confirms is offered as a concrete replacement.

This split matters. Asked directly whether a label is a real gene, a model
answers inconsistently on exactly the labels that matter -- a plausible
fabrication such as CCND8 was accepted in two of four runs of one unchanged
question at temperature zero. Asked instead to guess what a broken label was
meant to be, and having that guess checked against the authority, the same
model is useful and cannot let anything through.
"""

from __future__ import annotations

from typing import Any

from .. import settings
from ..contracts import GeneLabelSuggestions
from ..framework_compat import HumanMessage, SystemMessage
from .gene_validation import validate_gene_identifiers

__all__ = ["suggest_gene_corrections"]

# One bounded call on an already-failing path.
_MAX_LABELS = 12


def _payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return getattr(value, "content", value)


def _prompt(labels: list[str], taxon: str) -> str:
    species = taxon or "unspecified"
    return (
        "These labels appear in a gene expression or regulatory prior file but "
        "are not recognized gene identifiers. For each one, say what it was "
        "most likely meant to be.\n\n"
        "Common causes: a spreadsheet rewrote a gene name as a date or a date "
        "serial number (MARCH7, SEPT9, DEC1 and their serials); a withdrawn or "
        "provisional identifier (LOC*, FLJ*, KIAA*); an outdated symbol that "
        "HGNC has since renamed; a typo; or a symbol from a different "
        "organism.\n\n"
        "Put the corrected gene symbol in likely_symbol when you have one, and "
        "leave it empty when you do not. Put the cause in reason, in one short "
        "sentence. Never invent a symbol to fill the field.\n\n"
        f"ORGANISM: {species}\nLABELS: " + ", ".join(labels)
    )


def suggest_gene_corrections(
    labels: list[str],
    taxon: str,
    mapper: Any | None = None,
) -> list[tuple[str, str, str]]:
    """Return (label, confirmed symbol or "", reason) for unrecognized labels.

    A proposed symbol is returned only when the gene authority confirms it, so
    a hallucinated suggestion is dropped rather than shown. The reason text is
    the model's own and is presented as a hint, never as a finding.
    """
    if mapper is None or not labels or settings.TEST_DATA_MODE:
        return []
    requested = list(dict.fromkeys(labels))[:_MAX_LABELS]
    messages = [
        SystemMessage(
            content=(
                "You explain broken gene identifiers. Your answer is advisory "
                "and is checked against NCBI and Ensembl before it is shown."
            )
        ),
        HumanMessage(content=_prompt(requested, taxon)),
    ]
    try:
        structured = (
            mapper.with_structured_output(
                GeneLabelSuggestions,
                method="function_calling",
                include_raw=False,
            )
            if hasattr(mapper, "with_structured_output")
            else mapper
        )
        parsed = GeneLabelSuggestions.model_validate(
            _payload(structured.invoke(messages))
        )
    except Exception:
        return []

    by_label = {label.casefold(): label for label in requested}
    proposals: dict[str, tuple[str, str]] = {}
    for item in parsed.suggestions:
        label = by_label.get(item.label.strip().casefold())
        if label is None or label in proposals:
            continue
        proposals[label] = (item.likely_symbol.strip(), item.reason.strip())

    candidates = sorted(
        {symbol for symbol, _ in proposals.values() if symbol}
    )
    confirmed: set[str] = set()
    if candidates and taxon:
        try:
            summary = validate_gene_identifiers(candidates, "symbol_like", taxon)
            confirmed = {
                record.identifier
                for record in summary.records.values()
                if record.status == "valid"
            }
        except Exception:
            confirmed = set()

    return [
        (label, symbol if symbol in confirmed else "", reason)
        for label, (symbol, reason) in proposals.items()
        if reason or symbol in confirmed
    ]
