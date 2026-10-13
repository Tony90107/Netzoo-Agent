"""Verdict layer step 1: a run the user asked for is decided after the final verdict, not lost to guidance.

r17 (run17 = heldout17 as run commands): 23 of 32 supported run commands were answered as guidance -- the text gate
wanted the workflow's name or a listed verb, or routing fell back and the check credited one workflow only afterwards.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.routing.capability import validate_task_text  # noqa: E402

PL6 = ("Compute now: from the bulk RNA-seq of 12 patient biopsies, which is all we have, produce sample-specific gene "
       "co-expression networks with a p-value for each edge.")
PI1 = "Set this up and run it: build one network of how TFs and miRNAs regulate genes in our 70 samples."
PL9 = ("Please run this: using the mutation calls for 190 ovarian tumors plus gene lengths, cancer genes and pathway "
       "sets, derive subtypes from pathway mutation scores.")
QUESTION = "Which tool groups patients from somatic mutations using gene length normalization?"


def _ask(quote, delivered, asked_as="request"):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "unstated", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": asked_as}


def _check(task, *asks):
    proposal = proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [],
                                                        "asks": list(asks)}})
    return build_capability_check(task, proposal)[0]


def _decision(check, matched, **update):
    fields = {"capability_match_status": "exact", "execution_requested": True, **update}
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="guidance",
                        matched_actions=matched, capability_check=check, **fields)


def _run(task, decision, monkeypatch):
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)
    return router_invocation._with_requested_run(None, {}, task, invocation).decision, events


def _bonobo(asked_as="request"):
    return _check(PL6, _ask("produce sample-specific gene co-expression networks with a p-value for each edge",
                            ["bonobo.per_sample_networks"], asked_as))


def test_a_run_the_text_gate_refused_is_planned_when_three_readings_agree(monkeypatch):
    """r17 PL6: exact BONOBO, both routing readings "execute", refused for want of "bonobo" or "run"."""
    assert validate_task_text(PL6, "run_bonobo", matched_actions=["run_bonobo"]) is not None
    decision, events = _run(PL6, _decision(_bonobo(), ["run_bonobo"]), monkeypatch)
    assert decision.action == "run_bonobo" and decision.should_execute and decision.intent_type == "run_analysis"
    assert [event[2] for event in events] == ["routing.requested_run_adopted"]


def test_a_workflow_the_check_adopted_is_run(monkeypatch):
    """r17 PI1: routing fell back, the check credited PUMA (Logs 405, 409), the "run it" was lost."""
    check = _check(PI1, _ask("build one network of how TFs and miRNAs regulate genes",
                             ["puma.regulator_gene_network"]))
    decision, _ = _run(PI1, _decision(check, ["run_puma"], match_basis="capability_check"), monkeypatch)
    assert decision.action == "run_puma"


def test_a_question_about_which_method_is_never_run(monkeypatch):
    check = _check(QUESTION, _ask("groups patients from somatic mutations", ["sambar.subtypes"], "question"))
    decision, events = _run(QUESTION, _decision(check, ["run_sambar"]), monkeypatch)
    assert decision.action == "no_tool" and events == []


def test_nothing_runs_without_both_routing_readings_or_a_confirmed_single_credit(monkeypatch):
    assert _run(PL6, _decision(_bonobo(), ["run_bonobo"], execution_requested=False), monkeypatch)[0].action == "no_tool"
    unconfirmed = _bonobo().model_copy(update={"provisional": True})
    assert _run(PL6, _decision(unconfirmed, ["run_bonobo"]), monkeypatch)[0].action == "no_tool"
    tied = _check(PL6, _ask("produce sample-specific gene co-expression networks with a p-value for each edge",
                            ["bonobo.per_sample_networks", "lioness_coexpression.per_sample_networks"]))
    assert _run(PL6, _decision(tied, ["run_bonobo"]), monkeypatch)[0].action == "no_tool"
    assert _run(PL6, _decision(_bonobo(), ["run_lioness_coexpression"]), monkeypatch)[0].action == "no_tool"


def test_a_result_nothing_registered_gives_keeps_the_reply(monkeypatch):
    """r17 MX1: networks plus an upload to a public repository -- the upload must still be said."""
    task = "Run it now: build TF-gene networks per sample and upload the networks to a public repository for us."
    check = _check(task, _ask("build TF-gene networks per sample", ["lioness_panda.per_sample_networks"]),
                   _ask("upload the networks to a public repository", []))
    assert _run(task, _decision(check, ["run_lioness_panda"]), monkeypatch)[0].action == "no_tool"


def test_mutation_calls_the_user_has_are_not_a_request_to_call_variants():
    """r17 PL9: the deliverable word list read "mutation calls" as variant calling; the check owns that verdict now."""
    assert validate_task_text(PL9, "run_sambar", matched_actions=["run_sambar"], model_execution=True) is None


def test_a_result_needing_an_outside_step_keeps_the_reply_that_names_it(monkeypatch):
    """r17 NM14: differential co-expression with p-values is LIONESS-COEXPRESSION plus a test outside NetZoo."""
    task = ("Go ahead and run it: from the expression of 100 cases and 100 controls, compute the gene pairs whose "
            "co-expression differs significantly between them, with p-values.")
    check = _check(task, _ask("compute the gene pairs whose co-expression differs significantly between them",
                              ["lioness_coexpression.comparisons"]))
    assert check.results()[0].status == "with_step"
    assert _run(task, _decision(check, ["run_lioness_coexpression"]), monkeypatch)[0].action == "no_tool"
