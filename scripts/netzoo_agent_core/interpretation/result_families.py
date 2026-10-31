"""The registry's results in a few families, for "which result do you want?" (docs/research-log/clarify-menu-2026-11-01).

clarify-options showed Jev cannot list alternatives for a vague request (its read is one result or none). The question
asks what kind of result the user wants, so the card offers every kind there is. The families live in the capability
sheet (`result_families`, and each produces entry's `family`; the loader rejects a produces entry without one) --
one source, read here. No model is involved.
"""
from __future__ import annotations

from functools import lru_cache

__all__ = ["families", "family_of"]


@lru_cache(maxsize=1)
def families() -> list[dict]:
    """[{key, text, entries, workflows}] in the sheet's order."""
    from ..capability_sheet import result_families, sheet_entries

    entries = [e for e in sheet_entries().values() if e.kind == "produces"]
    return [{"key": key, "text": text, "entries": [e.id for e in entries if e.family == key],
             "workflows": sorted({e.workflow for e in entries if e.family == key})} for key, text in result_families()]


def family_of(entry_id: str) -> str | None:
    from ..capability_sheet import sheet_entries

    found = sheet_entries().get(entry_id)
    return found.family if found is not None else None
