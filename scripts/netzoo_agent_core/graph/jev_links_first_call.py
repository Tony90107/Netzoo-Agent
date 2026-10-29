"""The call for Jev's links (jev-links-first-2026-10-29; the pure part is `interpretation.jev_links_first`).

Off by default: NETZOO_JEV_LINKS_FIRST=shadow reads and records, =on applies the confident picks to the turn's main
reading before the capability check is built. One Jev call per ask, in parallel; any failure leaves that ask as the
reading linked it. The reads are recorded as `core.jev_links_first`.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

from ..interpretation.jev_links_first import INSTRUCTIONS, linked, menu, pick, state
from ..jev_client import decide

__all__ = ["jev_linked", "links_mode"]

TIMEOUT = 20


def links_mode() -> str:
    mode = os.environ.get("NETZOO_JEV_LINKS_FIRST", "off").strip().lower()
    return mode if mode in ("shadow", "on") else "off"


def _read(task: str, quote: str, options: dict[str, str]) -> dict:
    try:
        out = decide(state(task, quote), {"link": {"type": "choice", "instructions": INSTRUCTIONS,
                                                   "criteria": options}}, timeout=TIMEOUT)
        answer = out["answers"]["link"]
        return {"choice": answer["choice"], "confidence": answer["confidence"],
                "cost": (out.get("usage") or {}).get("cost", 0)}
    except Exception as error:  # noqa: BLE001 -- Jev down or slow: the reading's own link stands
        return {"error": f"{type(error).__name__}: {error}"[:200]}


def jev_linked(context, state_, task: str, proposal):
    """The reading the check is built from: Jev's confident links applied when on; the reading itself otherwise."""
    from .context import record_event

    mode = links_mode()
    if mode == "off" or proposal is None:
        return proposal
    quotes = list(dict.fromkeys(ask.quote for name in type(proposal).model_fields if name[1:].isdigit()
                                for ask in getattr(getattr(proposal, name), "asks", None) or ()))
    if not quotes:
        return proposal
    options = menu()[0]
    with ThreadPoolExecutor(max_workers=min(4, len(quotes))) as pool:
        reads = dict(zip(quotes, pool.map(lambda quote: _read(task, quote, options), quotes)))
    result = linked(proposal, reads) if mode == "on" else proposal
    record_event(context, state_, "core.jev_links_first", "classify", {
        "mode": mode, "reads": [{"quote": quote, **read, "pick": pick(read)} for quote, read in reads.items()],
        "applied": result is not proposal})
    return result
