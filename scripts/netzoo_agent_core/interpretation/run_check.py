"""Verdict layer step 1 (2026-10-12): what the capability check says about a run routing selected.

Feasibility eval 2026-10-12: the check reads only guidance turns, so all 8 run-path turns went unchecked,
and F32 ("only gene expression ... use SAMBAR for expression-based subtypes") was planned as an exact
SAMBAR run. Of 6,295 recorded sessions only 29 took the run path, so no held-out set measured it. Now
the check reads a run request too, and this verdict is recorded beside the run; a confirmed `gap` is answered
as a full gap instead of a planned run (`graph.router_invocation._with_run_check`).

Items 1-2 (2026-10-14): every other verdict that is not an approval holds the run too, and the verdict travels with
the decision as a `RunVerdict`, which the Plan Evaluator and the executor gate require (`run_approval_failures`).
"""

from __future__ import annotations

import hashlib

from workflow_registry import RUN_ACTIONS

from ..capability_sheet import entry, sheet_entries
from ..contracts.capability_check import CapabilityCheck, RunVerdict
from .checked_match import credited_workflows

__all__ = ["request_sha256", "run_approval_failures", "run_check_verdict", "run_verdict"]


def _actions(item) -> set[str]:
    return {entry(key).action for key in item.delivered_by if entry(key).action}


def run_check_verdict(check: CapabilityCheck | None, action: str) -> dict:
    """The check's verdict on a run of `action`, with each result's status and credited workflows.

    agrees: the run's workflow gives every result directly; other_workflow: a result some workflow gives is not
    credited to the run's workflow; partial_gap: the run's workflow gives what is given, but some result no workflow
    gives (or one reading credits it and another nothing); outside_step: a result needs a step outside NetZoo after
    the run; needs_fact: a result waits on a fact the user does not know; unread: the run's workflow gives every
    result read (or nothing was found asked for), but some request sentences were not read; gap: no workflow gives any result; no_result: the check
    found nothing asked for; not_on_sheet: the run's action has no sheet entry (STRING download); unconfirmed: the
    check was not confirmed.
    """
    on_sheet = {item.action for item in sheet_entries().values() if item.action}
    results = check.results() if check is not None else []
    # M1: `limited` -- the result is not given as asked because of its method, settings or data size.
    rows = [{"quote": item.quote, "status": item.status, "credited": sorted(_actions(item)),
             **({"limited": True} if item.limits and item.status == "not_available" else {})} for item in results]
    given = [item for item in results if item.status != "not_available"]
    if action not in on_sheet:
        verdict = "not_on_sheet"
    elif check is None or check.unconfirmed():
        verdict = "unconfirmed"
    elif not results:
        verdict = "unread" if check.unchecked else "no_result"
    elif not given:
        verdict = "gap"
    elif any(action not in _actions(item) for item in given if item.status != "needs_fact"):
        verdict = "other_workflow"
    elif any(item.status in ("not_available", "partial") for item in results):
        verdict = "partial_gap"
    elif any(item.status == "needs_fact" for item in results):
        verdict = "needs_fact"
    elif any(item.status == "with_step" for item in results):
        verdict = "outside_step"
    elif check.unchecked:
        verdict = "unread"
    else:
        verdict = "agrees"
    return {"action": action, "verdict": verdict, "results": rows,
            "unchecked": list(check.unchecked) if check is not None else []}


def run_verdict(check: CapabilityCheck | None, action: str, *, check_status: str = "ok", named: bool = False,
                held: bool = False) -> RunVerdict:
    """The record a run is planned or held under; `no_check_model` only when nothing is configured to read it."""
    found = run_check_verdict(check, action)
    verdict = "no_check_model" if check is None and check_status == "no_model" else found["verdict"]
    credited = (credited_workflows(check) or []) if check is not None and not check.unconfirmed() else []
    return RunVerdict(action=action, verdict=verdict, held=held, named=named, credited=credited,
                      results=found["results"], unchecked=found["unchecked"])


def request_sha256(message: str) -> str:
    """The hash `RequestRequirements.source_sha256` binds a turn's requirements with."""
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def run_approval_failures(decision, user_message: str) -> list[str]:
    """Why a plan of `decision` may not run for `user_message`; [] when its capability verdict approves it.

    Only the analysis workflows (`RUN_ACTIONS`) are gated here; inspecting files, reading documents and the STRING
    download keep their own rules.
    """
    if decision.action not in RUN_ACTIONS:
        return []
    if decision.run_verdict is None:
        return ["no capability verdict was given for this run"]
    return decision.run_verdict.run_failures(decision.action, request_sha256(user_message))
