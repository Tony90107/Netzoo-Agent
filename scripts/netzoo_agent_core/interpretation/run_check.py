"""Verdict layer step 1 (2026-10-12): what the capability check says about a run routing selected.

Feasibility eval 2026-10-12: the check reads only guidance turns, so all 8 run-path turns went unchecked,
and F32 ("only gene expression ... use SAMBAR for expression-based subtypes") was planned as an exact
SAMBAR run. Of 6,295 recorded sessions only 29 took the run path, so no held-out set measured it. In shadow
mode (`NETZOO_SHADOW_RUN_CHECK=1`) the check reads a run request too, and this verdict is recorded beside the
run; nothing acts on it.
"""

from __future__ import annotations

import os
from typing import Literal

from ..capability_sheet import entry, sheet_entries
from ..contracts.capability_check import CapabilityCheck

__all__ = ["RunVerdict", "run_check_verdict", "shadow_run_check_enabled"]

RunVerdict = Literal["agrees", "other_workflow", "partial_gap", "gap", "no_result", "not_on_sheet", "unconfirmed"]
"""agrees: the run's workflow gives every result some workflow gives; other_workflow: a result some workflow gives
is not credited to the run's workflow; partial_gap: the run's workflow gives the results that are given, but some
result no workflow gives; gap: no workflow gives any result; no_result: the check found nothing asked for;
not_on_sheet: the run's action has no sheet entry (STRING download); unconfirmed: the check was not confirmed."""


def shadow_run_check_enabled() -> bool:
    return os.environ.get("NETZOO_SHADOW_RUN_CHECK", "").strip() == "1"


def _actions(item) -> set[str]:
    return {entry(key).action for key in item.delivered_by if entry(key).action}


def run_check_verdict(check: CapabilityCheck | None, action: str) -> dict:
    """The check's verdict on a run of `action`, with each result's status and credited workflows."""
    on_sheet = {item.action for item in sheet_entries().values() if item.action}
    results = check.results() if check is not None else []
    rows = [{"quote": item.quote, "status": item.status, "credited": sorted(_actions(item))} for item in results]
    if action not in on_sheet:
        verdict = "not_on_sheet"
    elif check is None or check.unconfirmed():
        verdict = "unconfirmed"
    elif not results:
        verdict = "no_result"
    elif all(item.status == "not_available" for item in results):
        verdict = "gap"
    elif any(action not in _actions(item) for item in results if item.status != "not_available"):
        verdict = "other_workflow"
    elif any(item.status == "not_available" for item in results):
        verdict = "partial_gap"
    else:
        verdict = "agrees"
    return {"action": action, "verdict": verdict, "results": rows,
            "unchecked": list(check.unchecked) if check is not None else []}
