"""Core decision spec, phase 0: `decide_core` names the turn's four-way call from its final decision (shadow).

Offline check before wiring: on m3's 150 labelled sessions the shadow call matched the labelled takeaway in 115;
most of the rest are replies that asked a question from a path the decision does not record (research log).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    CapabilityCheck, CheckedRequirement, RunVerdict,
)
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402


def _row(status, delivered=(), kind="result", **extra):
    return CheckedRequirement(quote="a network", kind=kind, status=status, delivered_by=list(delivered), **extra)


def _decision(action="no_tool", rows=None, **extra):
    check = None if rows is None else CapabilityCheck(requirements=rows, **{
        k: extra.pop(k) for k in ("full_gap", "provisional", "unavailable") if k in extra})
    fields = {"confidence": 0.9, **extra}
    return TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", reason="r",
                        capability_check=check, **fields)


def test_a_result_the_check_gives_is_do_with_its_workflow():
    core = decide_core(_decision(rows=[_row("available", ["panda.tf_gene_network"])]))
    assert (core.kind, core.workflows, core.run_allowed) == ("DO", ["PANDA"], False)


def test_every_result_not_available_is_decline_with_the_reasons():
    core = decide_core(_decision(rows=[_row("not_available", limits=["LIONESS needs at least 3 samples"])]))
    assert core.kind == "DECLINE"
    assert core.declined[0].reasons == ["LIONESS needs at least 3 samples"]


def test_a_full_gap_is_decline():
    assert decide_core(_decision(rows=[_row("not_available")], full_gap=True)).basis == "full_gap"


def test_a_given_and_a_declined_result_is_a_partial_do_never_a_run():
    core = decide_core(_decision(rows=[_row("available", ["panda.tf_gene_network"]), _row("not_available")]))
    assert (core.kind, core.partial, core.run_allowed) == ("DO", True, False)


def test_a_result_waiting_on_a_fact_is_ask_with_the_question():
    row = _row("needs_fact", depends_on="input_network", unknown_quote="I can't recall",
               outcomes={"regulator_gene": ["condor.communities"], "gene_gene": []})
    core = decide_core(_decision(rows=[row]))
    assert core.kind == "ASK"
    (fact,) = core.facts
    assert (fact.user_quote, fact.workflows) == ("I can't recall", ["CONDOR"])
    assert fact.question.startswith("Does your network link regulators")


def test_nothing_read_nothing_routed_is_clarify():
    core = decide_core(_decision(rows=[_row("not_checked", kind="context")], capability_match_status="ambiguous"))
    assert (core.kind, core.basis) == ("CLARIFY", "no_result_read")


def test_a_methods_question_with_a_named_workflow_is_do_as_the_reply_gives_it():
    core = decide_core(_decision(rows=[_row("not_checked", kind="about_methods")], matched_actions=["run_bonobo"]))
    assert (core.kind, core.workflows) == ("DO", ["BONOBO"])


def test_an_approved_run_is_allowed_and_a_held_one_is_not():
    run = dict(action="run_cobra", rows=[], matched_actions=["run_cobra"])
    allowed = decide_core(_decision(**run, run_verdict=RunVerdict(action="run_cobra", verdict="agrees")))
    held = decide_core(_decision(**run, run_verdict=RunVerdict(action="run_cobra", verdict="partial_gap", held=True)))
    assert (allowed.kind, allowed.run_allowed) == ("DO", True)
    assert (held.kind, held.basis, held.run_allowed) == ("DO", "run_held", False)


def test_a_run_held_unread_or_a_check_it_could_not_confirm_is_unchecked():
    held = decide_core(_decision(action="run_cobra", rows=[], matched_actions=["run_cobra"],
                                 run_verdict=RunVerdict(action="run_cobra", verdict="unread", held=True)))
    unconfirmed = decide_core(_decision(rows=[_row("available", ["panda.tf_gene_network"])], provisional=True))
    assert (held.kind, unconfirmed.kind) == ("UNCHECKED", "UNCHECKED")


def test_routing_that_failed_closed_with_nothing_routed_is_unchecked():
    core = decide_core(_decision(confidence=0.0, match_basis="provider_unavailable"), reason_code="semantic_fallback")
    assert core.kind == "UNCHECKED"


def test_a_known_unsupported_method_combination_is_decline():
    task = "Use graphical lasso with Bayesian optimization to tune the penalty for my network."
    assert decide_core(_decision(), task).basis == "algorithm_boundary"


def test_the_core_call_is_recorded_on_the_decision_dump_only_when_set():
    decision = _decision()
    assert "core" not in decision.model_dump()
    with_core = decision.model_copy(update={"core": decide_core(decision)})
    assert TaskDecision.model_validate(with_core.model_dump()).core.kind == "CLARIFY"
