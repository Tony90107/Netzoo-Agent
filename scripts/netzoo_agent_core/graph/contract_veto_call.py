"""The contract veto layer's calls on the live path (hybrid spec docs/superpowers/specs/
2026-10-19-hybrid-contract-veto-design.md, sections 2-3). Off by default: NETZOO_CONTRACT_VETO=1 turns it on.

After `decide_core` makes a DO, `apply_contract_veto` reads the request for the workflows the live system picked:
the slim core read (C facts, D4, D7), the focused read of their limit fields only (B4, B5, B6, required declarations),
and -- when a fact has no code-verified contract words -- the contract check that copies the clause. Code then judges
(`interpretation.contract_veto`) and may change the call. Every call is priced against the turn's budget and recorded
in its usage (the hybrid gates' `_call`); a call that cannot be made or fails leaves the live call as it was.
"""

from __future__ import annotations

import os

from ..contracts import HumanMessage, SystemMessage
from ..contracts.slim_reading import SlimReading
from ..interpretation.contract_veto import check_pairs, check_text, contract_veto, limit_needs, vetoed_core
from ..interpretation.menu_reader import request_layout
from ..interpretation.menu_requirements import requirement_model
from ..interpretation.slim_reader import core_model, focus_model, from_core, merge_focus
from ..interpretation.veto_evidence import veto_ledger
from ..method_names import registered_workflows
from .context import record_event
from .hybrid_gate_call import _call
from .slim_reading_call import build_core_messages, build_focus_messages

__all__ = ["CHECK_SHAPE", "apply_contract_veto", "veto_reads"]

CHECK_SHAPE = (
    "Return only the RequirementVerdicts structure. Each numbered pair gives something the user's request says (what "
    "they need, what their data is or lacks, a result they want) and one registered workflow, whose contract is "
    "listed. For each pair, copy the clause of that workflow's contract that speaks to it, in its exact words (empty "
    "when none does), then say whether the contract says the workflow can do it (met), says it cannot (contradicted), "
    "or does not address it."
)


def veto_reads(task: str, workflows, call, reports: list | None = None):
    """(slim reading, pairs, check payload) for the workflows, or None when the core read fails. `call(role, messages,
    schema)` makes one structured call and returns its payload dict (None on failure). `reports` collects each read's
    ReadReport (what was dropped and why) for the ledger (ROUND-02 C)."""
    reports = [] if reports is None else reports
    layout = request_layout(task)
    data = call("contract_veto_core", build_core_messages(task), core_model(layout.names))
    if data is None:
        return None
    slim, report = from_core(data, task, layout)
    reports.append(report)
    needs = limit_needs(slim, workflows)
    if needs.runs:
        focused = call("contract_veto_limits", build_focus_messages(task, slim, needs), focus_model(needs))
        if focused is not None:
            slim, report = merge_focus(slim, focused, task, needs)
            reports.append(report)
        else:
            report.dropped.append("focus: the limit read failed; its cells were not read")
    pairs = check_pairs(slim, workflows)
    payload = None
    if pairs:
        payload = call("contract_veto_check", [SystemMessage(content=CHECK_SHAPE),
                                               HumanMessage(content=check_text(task, pairs))],
                       requirement_model(len(pairs)))
    return slim, pairs, payload


def apply_contract_veto(context, state, decision, core, user_task: str, usage, warnings):
    """(core, usage, warnings): the live DO judged against its workflows' contracts; anything else as it came."""
    if core.kind != "DO" or os.environ.get("NETZOO_CONTRACT_VETO", "0") != "1":
        return core, usage, warnings
    known = registered_workflows()
    workflows = tuple(name for name in core.workflows if name in known)
    llm, model = getattr(context, "study_purpose_llm", None), getattr(context, "semantic_model_name", None)
    if not workflows or llm is None or usage.budget_exhausted:
        # ROUND-02 C: a veto that never ran says so -- an empty record is never a pass.
        reason = "no_workflows" if not workflows else "no_model" if llm is None else "budget_exhausted"
        record_event(context, state, "core.contract_veto", "classify", {
            "status": f"not_run:{reason}", "workflows": list(workflows),
            "ledger": veto_ledger(workflows, f"not_run:{reason}")})
        return core, usage, warnings
    spent = {"usage": usage, "warnings": warnings}

    def call(role, messages, schema):
        data, spent["usage"], spent["warnings"], _status = _call(context, state, role, model, llm, messages, schema,
                                                                  spent["usage"], spent["warnings"])
        return data

    reports: list = []
    read = veto_reads(user_task, workflows, call, reports)
    if read is None:
        record_event(context, state, "core.contract_veto", "classify",
                     {"status": "read_failed", "workflows": list(workflows),
                      "ledger": veto_ledger(workflows, "read_failed")})
        return core, spent["usage"], spent["warnings"]
    slim, pairs, payload = read
    verdict = contract_veto(slim, workflows, user_task, payload, pairs)
    vetoed = vetoed_core(core, verdict)
    record_event(context, state, "core.contract_veto", "classify", {
        "status": "checked", "workflows": list(workflows), "kind_before": core.kind, "kind_after": vetoed.kind,
        "evidence": vetoed.evidence.get("contract_veto"), "reading": slim.model_dump(mode="json", exclude_defaults=True),
        "ledger": veto_ledger(workflows, "checked", slim, reports, verdict, verdict.set_aside)})
    return vetoed, spent["usage"], spent["warnings"]
