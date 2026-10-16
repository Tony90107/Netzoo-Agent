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
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402


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


def test_nothing_read_nothing_routed_is_clarify_with_the_same_question():
    """Round p1 C41, C48: a CLARIFY with no question fell through to the budget-exhausted fallback reply."""
    core = decide_core(_decision(rows=[_row("not_checked", kind="context")], capability_match_status="ambiguous"))
    assert (core.kind, core.basis) == ("CLARIFY", "no_result_read")
    assert core.clarify.question.startswith("Which of these results do you want")


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


def test_a_confirmed_full_gap_is_decline_even_when_routing_failed_closed():
    """Round p0 C10, C22, C37, C49: semantic routing failed, the check confirmed a gap, and the reply declined."""
    decision = _decision(rows=[_row("not_available")], full_gap=True, confidence=0.0, match_basis="provider_unavailable")
    assert decide_core(decision, reason_code="semantic_fallback").kind == "DECLINE"
    unconfirmed = _decision(rows=[_row("not_available")], full_gap=True, provisional=True, confidence=0.0,
                            match_basis="provider_unavailable")
    assert decide_core(unconfirmed, reason_code="semantic_fallback").kind == "UNCHECKED"


# Phase 1 (spec section 5): a request that names no result is CLARIFY, asked before any workflow is chosen.

def _goal_check(goal, quote, rows=None, **extra):
    return CapabilityCheck(requirements=rows if rows is not None else [_row("not_available")], goal=goal,
                           goal_quote=quote, **extra)


def _with_check(check, **extra):
    fields = {"confidence": 0.9, **extra}
    return TaskDecision(action=fields.pop("action", "no_tool"), in_scope=True, should_execute=False, reason="r",
                        capability_check=check, **fields)


def test_a_purpose_only_reading_is_clarify_even_over_a_full_gap():
    check = _goal_check("purpose_only", "see how genes are connected", full_gap=True)
    core = decide_core(_with_check(check))
    assert (core.kind, core.basis) == ("CLARIFY", "goal_unclear")
    assert core.clarify.question.startswith("Which of these results do you want")
    assert core.clarify.missing == "both" and "PANDA" in core.clarify.candidates


def test_a_named_result_no_requirement_reads_is_clarify_and_one_a_requirement_reads_is_not():
    rows = [_row("not_available")]  # the requirement's quote is "a network"
    assert decide_core(_with_check(_goal_check("result_named", "the analysis", rows))).kind == "CLARIFY"
    assert decide_core(_with_check(_goal_check("result_named", "a network", rows))).kind == "DECLINE"


def test_a_named_method_or_an_unconfirmed_reading_never_clarifies():
    assert decide_core(_with_check(_goal_check("method_named", "BONOBO", [_row("available", ["bonobo.per_sample_networks"])]))).kind == "DO"
    unconfirmed = _goal_check("purpose_only", "help me", [_row("available", ["panda.tf_gene_network"])], provisional=True)
    assert decide_core(_with_check(unconfirmed)).kind == "UNCHECKED"


def test_clarify_lists_the_results_the_stated_data_can_give():
    from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis

    hypothesis = OutcomeHypothesis.model_validate({
        "outcome": {"operation": "infer", "input_artifacts": ["mutation_matrix"], "artifact_type": "unknown",
                    "granularity": "unknown"},
        "confidence": 0.5, "evidence": [], "assumptions": []})
    core = decide_core(_with_check(_goal_check("purpose_only", "tell me what you see"), outcome_hypotheses=[hypothesis]))
    assert (core.clarify.inputs, core.clarify.candidates, core.clarify.missing) == (["mutation_matrix"], ["SAMBAR"], "result")


def test_with_core_holds_a_clarify_turn_and_leaves_other_calls_alone():
    from netzoo_agent_core.interpretation.core_decision import with_core

    run = _with_check(_goal_check("purpose_only", "do whatever makes sense"), action="run_panda",
                      matched_actions=["run_panda"], recommended_actions=["run_panda"])
    held = with_core(run, decide_core(run))
    assert (held.action, held.should_execute, held.matched_actions, held.recommended_actions) == ("no_tool", False, [], [])
    assert held.clarification_question == held.core.clarify.question
    done = _decision(rows=[_row("available", ["panda.tf_gene_network"])], matched_actions=["run_panda"])
    kept = with_core(done, decide_core(done))
    assert (kept.matched_actions, kept.core.kind) == (["run_panda"], "DO")


def test_the_goal_is_kept_only_when_its_words_are_in_the_request():
    from types import SimpleNamespace
    from netzoo_agent_core.interpretation.capability_check import verified_goal

    task = "Please run the network analysis on expr.tsv and send me the results."
    said = SimpleNamespace(conditions=SimpleNamespace(goal="purpose_only", goal_quote="run the network analysis"))
    invented = SimpleNamespace(conditions=SimpleNamespace(goal="purpose_only", goal_quote="understand regulation"))
    assert verified_goal(task, said) == ("purpose_only", "run the network analysis")
    assert verified_goal(task, invented) == ("", "")


def test_the_clarify_reply_lists_possible_results_asks_once_and_selects_nothing():
    from netzoo_agent_core.interpretation.capability_check import whole_check_result
    from netzoo_agent_core.interpretation.core_decision import with_core

    decision = _with_check(_goal_check("purpose_only", "see how genes are connected", full_gap=True))
    decision = with_core(decision, decide_core(decision))
    result = whole_check_result({"decision": decision.model_dump(), "messages": []},
                                lambda text, kind: {"text": text, "reply_kind": kind})
    assert result["reply_kind"] == "clarify_goal"
    text = result["text"]
    assert text.startswith("I can't tell yet which result you want")
    assert "(PANDA)" in text and text.count("?") == 2  # the result question and the data question
    assert "fits" not in text and "available from" not in text and "No registered workflow" not in text


def test_the_clarify_card_is_a_clarification_with_the_question():
    from netzoo_agent_core.interpretation.core_decision import with_core
    from netzoo_agent_core.reply_cards.builder import _core_card

    decision = _with_check(_goal_check("purpose_only", "see how genes are connected"))
    decision = with_core(decision, decide_core(decision))
    card = _core_card("clarify_goal", decision, None, "")
    assert (card.kind, card.points) == ("clarification", [decision.clarification_question])


def test_the_clarify_reply_lists_every_candidate_and_keeps_abbreviations_whole():
    from netzoo_agent_core.interpretation.clarify_goal import _first_sentence

    assert _first_sentence("Covariates (e.g. group, batch) shape it. More text.") == "Covariates (e.g. group, batch) shape it"
    decision = _with_check(_goal_check("purpose_only", "see how genes are connected"))
    core = decide_core(decision)
    from netzoo_agent_core.interpretation.clarify_goal import clarify_reply
    assert all(f"({name})" in clarify_reply(core) for name in core.clarify.candidates)


def test_a_clarify_turn_shows_no_workflow_in_its_progress_line():
    """Round p1 C19: the CLARIFY reply was headed "Matched workflows -- PUMA" from routing's candidates."""
    from netzoo_agent_core.interpretation.core_decision import with_core
    from netzoo_agent_core.interpretation.semantic_goal import classification_progress_detail

    decision = _with_check(_goal_check("purpose_only", "do whatever makes sense"), matched_actions=["run_puma"])
    goal = {"candidates": ["run_puma"], "request_mode": "execute"}
    assert classification_progress_detail(goal, decision)["workflows"] == ["PUMA"]
    held = with_core(decision, decide_core(decision))
    detail = classification_progress_detail(goal, held)
    assert (detail["workflows"], detail["workflow_path"]) == ([], [])


# Phase 3 (sections 4.3, 7): a call that is not DO is answered by its one view; the gates read the call.

def _view(decision):
    from netzoo_agent_core.interpretation.core_views import core_view

    decision = with_core(decision, decide_core(decision, decision.reason if decision.reason != "r" else ""))
    return core_view(None, {"decision": decision.model_dump(), "messages": []},
                     lambda text, kind: {"text": text, "reply_kind": kind})


def test_a_decline_is_answered_by_the_decline_view_with_its_reason():
    from netzoo_agent_core.interpretation.core_views import core_view

    decision = _decision(rows=[_row("not_available", limits=["LIONESS needs at least 3 samples; the request has 2"])])
    decision = with_core(decision, decide_core(decision))
    assert decision.core.declined[0].line.startswith('"a network" -- not available here as asked.')
    result = core_view(None, {"decision": decision.model_dump(), "messages": []},
                       lambda text, kind: {"text": text, "reply_kind": kind})
    assert result["reply_kind"] == "decline"
    assert "LIONESS needs at least 3 samples" in result["text"] and "none is offered as asked" in result["text"]


def test_the_text_boundaries_are_decline_evidence_not_replies_of_their_own():
    task = "Use graphical lasso with Bayesian optimization to tune the penalty for my network."
    core = decide_core(_decision(rows=[_row("available", ["panda.tf_gene_network"])]), task)
    assert (core.kind, core.basis) == ("DECLINE", "algorithm_boundary")
    assert "Graphical Lasso" in core.declined[0].line


def test_an_unconfirmed_guidance_turn_is_unchecked_and_answered_as_such():
    decision = _decision(rows=[], provisional=True, matched_actions=["run_panda"])
    core = decide_core(decision)
    assert (core.kind, core.basis, core.workflows) == ("UNCHECKED", "check_unconfirmed", ["PANDA"])
    from netzoo_agent_core.interpretation.core_views import unchecked_reply
    assert "nothing was selected and nothing runs" in unchecked_reply(core)


def test_do_keeps_its_renderers_and_every_reply_kind_belongs_to_one_call():
    from netzoo_agent_core.interpretation.core_views import ALLOWED, core_view

    done = _decision(rows=[_row("available", ["panda.tf_gene_network"])])
    done = with_core(done, decide_core(done))
    assert core_view(None, {"decision": done.model_dump(), "messages": []}, lambda t, k: (t, k)) is None
    assert ALLOWED["DECLINE"].isdisjoint(ALLOWED["DO"]) and ALLOWED["CLARIFY"].isdisjoint(ALLOWED["DO"])


def test_the_view_record_marks_a_reply_that_is_not_its_calls():
    from types import SimpleNamespace
    from netzoo_agent_core.graph.context import record_core_view

    events = []
    context = SimpleNamespace(recorder=SimpleNamespace(append=lambda run, kind, node, payload: events.append(payload)))
    state = {"decision": {"core": {"kind": "DO", "basis": "routed"}}}
    record_core_view(context, state, {"reply_kind": "capability_check_gap"})
    record_core_view(context, state, {"reply_kind": "verified_guidance"})
    assert [event["mismatch"] for event in events] == [True, False]


def test_the_run_gates_read_the_call():
    from netzoo_agent_core.interpretation.run_check import run_approval_failures, request_sha256

    message = "Run COBRA on expr.tsv"
    verdict = RunVerdict(action="run_cobra", verdict="agrees", request_sha256=request_sha256(message))
    run = _decision(action="run_cobra", rows=[], matched_actions=["run_cobra"], run_verdict=verdict)
    allowed = run.model_copy(update={"core": decide_core(run)})
    assert allowed.core.run_allowed and run_approval_failures(allowed, message) == []
    held = allowed.model_copy(update={"core": allowed.core.model_copy(update={"run_allowed": False})})
    assert run_approval_failures(held, message) == ["the turn's call (DO, run) does not allow a run"]


def test_an_unchecked_turn_names_no_workflow_and_never_says_available():
    """Round p3 C42, C43: a run held as unconfirmed was headed 'Workflow -- DRAGON' over 'available from DRAGON'."""
    from netzoo_agent_core.interpretation.capability_check import understanding_paragraph
    from netzoo_agent_core.interpretation.semantic_goal import classification_progress_detail

    check = CapabilityCheck(requirements=[_row("available", ["panda.tf_gene_network"])], provisional=True)
    line = understanding_paragraph(check)
    assert "available from" not in line and "the backup check matched PANDA to this (not confirmed)" in line
    decision = _decision(rows=[_row("available", ["panda.tf_gene_network"])], provisional=True,
                         matched_actions=["run_panda"])
    held = with_core(decision, decide_core(decision))
    assert held.core.kind == "UNCHECKED"
    assert classification_progress_detail({"candidates": ["run_panda"], "request_mode": "execute"}, held)["workflows"] == []


def test_an_unchecked_exact_match_names_no_workflow_path_either():
    """Phase 4b smoke S1b: an UNCHECKED turn whose routing matched CONDOR exactly was headed "Workflow -- CONDOR"."""
    from netzoo_agent_core.interpretation.semantic_goal import classification_progress_detail

    decision = _decision(rows=[], provisional=True, matched_actions=["run_condor"], recommended_actions=["run_condor"],
                         capability_match_status="exact")
    held = with_core(decision, decide_core(decision))
    assert held.core.kind == "UNCHECKED"
    detail = classification_progress_detail({"candidates": ["run_condor"]}, held)
    assert (detail["workflows"], detail["workflow_path"]) == ([], [])


# Rounds p4b and p4c: the calls both rounds got wrong (research log RESULTS-BOTH-WRONG.md).

def test_a_run_names_the_workflow_it_runs_not_routings_other_picks():
    """p4b/p4c C59: a LIONESS-PUMA run was recorded as DO for LIONESS-PUMA and PUMA (routing recommended both)."""
    decision = _decision(action="run_lioness_puma", rows=[], matched_actions=["run_lioness_puma"],
                         recommended_actions=["run_puma", "run_lioness_puma"],
                         run_verdict=RunVerdict(action="run_lioness_puma", verdict="agrees"))
    core = decide_core(decision)
    assert (core.kind, core.workflows, core.run_allowed) == ("DO", ["LIONESS-PUMA"], True)


def test_one_method_the_goal_words_name_is_the_goal():
    """p4b/p4c C39 ("Can PUMA model the small RNAs ...?") and p1 C32 were read purpose_only."""
    rows = [_row("not_checked", kind="about_methods")]
    check = _goal_check("purpose_only", "Can PUMA model the small RNAs from our mouse testis small-RNA-seq", rows)
    assert decide_core(_with_check(check, matched_actions=["run_puma"])).kind == "DO"
    assert decide_core(_with_check(_goal_check("purpose_only", "Can LIONESS-PUMA do it", rows),
                                   matched_actions=["run_lioness_puma"])).kind == "DO"


def test_two_methods_named_as_the_choice_with_no_result_is_clarify():
    """Spec section 5 ("BONOBO or LIONESS?"); p4b C10 read "COBRA or CONDOR" as method_named."""
    rows = [_row("not_checked", kind="context"), _row("not_checked", kind="about_methods")]
    core = decide_core(_with_check(_goal_check("method_named", "COBRA or CONDOR", rows), matched_actions=["run_cobra"]))
    assert (core.kind, core.basis) == ("CLARIFY", "goal_unclear")
    named_result = [_row("available", ["puma.tf_gene_network"])]  # the reading read a result: the choice is a tie
    assert decide_core(_with_check(_goal_check("method_named", "PANDA or PUMA", named_result))).kind == "DO"


def test_only_the_registered_spelling_names_a_method():
    from netzoo_agent_core.method_names import workflows_in

    assert workflows_in("Should I be using COBRA or CONDOR on our cohort?") == ["COBRA", "CONDOR"]
    assert workflows_in("PANDA or LIONESS or something; LIONESS-PUMA per sample") == ["PANDA", "LIONESS", "LIONESS-PUMA"]
    assert workflows_in("the panda cohort, LIONESS-OTTER networks") == []
