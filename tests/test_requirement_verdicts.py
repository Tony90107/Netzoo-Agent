"""Log 403: every part of a reply reads the capability check's verdict on that part, and a turn the
check confirmed nothing for never presents a workflow as the answer.

heldout10 SC1 ("a network for each patient and a test of which edges differ with
the time point"): the check said the test is LIONESS-PANDA's output plus a step
outside NetZoo, while the per-reading reply and its card said no registered
workflow produces it. The three recorded decisions are replayed here as they were
stored; nothing calls a model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    checked_route_lines, requirement_for,
)
from netzoo_agent_core.interpretation.unconfirmed_routes import unconfirmed_reply  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
SC1 = json.loads((ROOT / "tests" / "log403_sc1_decisions.json").read_text())


def _replay(task: str, decision: TaskDecision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    return str(out["messages"][-1].content), out["reply_kind"], card


@pytest.mark.parametrize("session", sorted(SC1["decisions"]))
def test_sc1_reading_takes_the_checks_outside_step_route(session):
    decision = TaskDecision.model_validate(SC1["decisions"][session])
    text, kind, card = _replay(SC1["task"], decision)
    assert kind == "hypothesis_routes"
    understood, body = text.split("\n\n", 1)
    assert "LIONESS-PANDA's output plus a step you run outside NetZoo" in understood
    # The body says the same thing about the same words, never that nothing produces them.
    assert "No registered workflow produces this result" not in body
    assert "no registered workflow)" not in body
    assert "it comes from LIONESS-PANDA's output plus a step you run outside NetZoo" in body
    assert "2 (LIONESS-PANDA, then a step outside NetZoo)" in body
    # The card offers the same two readings; neither is listed as unavailable.
    keys = [option.key for option in card.choices.options]
    assert keys == ["reading-1", "reading-2"]
    assert not [option for option in card.unavailable if option.key.startswith("reading-")]
    assert "then a step outside NetZoo" in card.choices.options[1].description


TASK = "We want a network for each patient and a test of which edges differ with the time point."


def _check(status: str, delivered=("lioness_panda.association_tests",), **extra) -> CapabilityCheck:
    return CapabilityCheck(requirements=[
        CheckedRequirement(quote="a test of which edges differ with the time point", kind="result", status=status,
                           delivered_by=list(delivered) if status != "not_available" else []),
    ], **extra)


def test_a_passage_stands_for_the_result_whose_words_it_shares():
    check = _check("with_step")
    assert requirement_for(check, TASK, ["test of which edges differ with the time point."]) is check.requirements[0]
    assert requirement_for(check, TASK, ["We want a network for each patient"]) is None
    # A one-word overlap is not the same part of the request.
    assert requirement_for(check, TASK, ["the time point and more words than the requirement"]) is None
    assert requirement_for(CapabilityCheck(unavailable=True), TASK, ["a test of which edges"]) is None


def test_the_result_quote_wins_over_a_longer_quote_for_another_requests_scale():
    decision = TaskDecision.model_validate(SC1["decisions"]["ce-f10-cand-SC1-1"])
    old = decision.capability_check.requirements
    unsupported = old[1].model_copy(update={
        "quote": "which edges differ", "status": "not_available", "delivered_by": []})
    decision = decision.model_copy(update={"capability_check": decision.capability_check.model_copy(update={
        "requirements": [old[0], unsupported, old[2]],
    })})
    from netzoo_agent_core.interpretation.hypothesis_routes import _readings, checked_actions, reading_verdict

    edge_reading = _readings(decision, POLICY)[1]
    assert reading_verdict(decision, edge_reading, SC1["task"]) is unsupported
    assert checked_actions(decision, edge_reading, SC1["task"], POLICY) == []
    text, kind, card = _replay(SC1["task"], decision)
    assert kind == "hypothesis_routes"
    assert "No registered workflow produces this result" in text
    assert any(option.key == "reading-2" for option in card.unavailable)


def test_a_passage_covering_two_requirements_does_not_choose_one_as_the_whole():
    task = "Infer a network and predict survival."
    check = CapabilityCheck(requirements=[
        CheckedRequirement(quote="Infer a network", kind="result", status="available",
                           delivered_by=["panda.tf_gene_network"]),
        CheckedRequirement(quote="predict survival", kind="result", status="not_available"),
    ])
    assert requirement_for(check, task, [task]) is None


def test_an_unchecked_result_does_not_borrow_a_verdict_from_its_scale_quote():
    from netzoo_agent_core.interpretation.hypothesis_routes import _readings, reading_verdict

    decision = TaskDecision.model_validate(SC1["decisions"]["ce-f10-cand-SC1-1"])
    check = decision.capability_check
    decision = decision.model_copy(update={"capability_check": check.model_copy(update={
        "requirements": [check.requirements[0], check.requirements[2]],
        "unchecked": ["a test of which edges differ with the time point"],
    })})
    assert reading_verdict(decision, _readings(decision, POLICY)[1], SC1["task"]) is None


def test_only_a_delivering_verdict_gives_a_route():
    assert checked_route_lines(_check("not_available").requirements[0]) is None
    lines, names = checked_route_lines(_check("with_step").requirements[0])
    assert names == "LIONESS-PANDA, then a step outside NetZoo"
    assert "outside NetZoo" in lines[0]
    lines, _ = checked_route_lines(_check("with_step").requirements[0], provisional=True)
    assert lines[0].endswith("(The backup check found this; it is not confirmed.)")


def test_a_tie_of_more_workflows_than_a_card_holds_drops_only_the_method_question():
    """Log 403 replay: 21 recorded turns tied 11-13 workflows and the whole card was dropped."""
    from netzoo_agent_core.reply_cards.choices import method_choices
    from netzoo_agent_core.reply_cards.contracts import MAX_OPTIONS

    every = [action for action in POLICY.workflows if action.startswith("run_")]
    assert len(every) > MAX_OPTIONS
    task = "Which method should we use for our expression data?"
    tied = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.5, reason="r",
                        hypothesis_actions=every, capability_match_status="ambiguous")
    assert method_choices(tied, POLICY, task=task) is None
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=tied.model_dump(), status="respond_only")
    for kind in ("outcome_clarification", "research_choices"):
        result = {"decision": tied.model_dump(), "plan": plan.model_dump(), "tool_results": [],
                  "evaluation": None, "reply_kind": kind,
                  "messages": [HumanMessage(content=task), HumanMessage(content="The tied methods ...")]}
        card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)  # no overflow
        assert card is None or card.choices is None or len(card.choices.options) <= MAX_OPTIONS
    few = tied.model_copy(update={"hypothesis_actions": every[:3]})
    assert len(method_choices(few, POLICY, task=task).options) == 3


# -- Log 403, plan item 6: a turn whose check confirmed nothing --------------------------------

SPLICING = ("We have isoform-level quantifications from 80 brain samples. We want to find which splicing "
            "factors control inclusion of each alternative exon.")


def _splicing_gap_proposal():
    from netzoo_agent_core.contracts.capability_check import proposal_model

    blank = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
             "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
             "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}
    return proposal_model(2).model_validate({
        "s1": {"role": "background", "has": ["isoform-level quantifications from 80 brain samples"],
               "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [{
            "quote": "find which splicing factors control inclusion of each alternative exon",
            "delivered_by": [], "not_by": ["panda.no_motif_discovery"], **blank}]},
    })


def _exact_panda():
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_match_status="exact", matched_actions=["run_panda"])


def test_a_gap_whose_owed_second_opinion_could_not_answer_is_unconfirmed(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "has_check_model", lambda context: True)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (None, usage, warnings))
    invocation = router_invocation._RouterInvocation(
        decision=_exact_panda(), routing_state={}, usage=None, budget_warnings=[], reason_code=None)
    decision = router_invocation._with_capability_check(None, {}, SPLICING, invocation,
                                                         _splicing_gap_proposal()).decision
    check = decision.capability_check
    assert not check.full_gap and check.gap_unconfirmed and check.unconfirmed()
    assert decision.matched_actions == ["run_panda"]  # routing's offer stays
    from netzoo_agent_core.interpretation.capability_check import understanding_paragraph

    paragraph = understanding_paragraph(check)
    assert "could not run (not confirmed)" in paragraph and "not available here" not in paragraph


def test_the_body_lists_routings_workflows_as_unconfirmed_never_as_the_answer():
    check = CapabilityCheck(provisional=True, requirements=[CheckedRequirement(
        quote="find which splicing factors control inclusion of each alternative exon", kind="result",
        status="not_available")])
    decision = _exact_panda().model_copy(update={"capability_check": check, "recommended_actions": ["run_panda"]})
    text, kind, card = _replay(SPLICING, decision)
    assert kind == "capability_unconfirmed"
    assert "did not confirm that any of them gives what you asked for" in text
    assert "- **PANDA** — produces: One weighted TF-to-gene regulatory network" in text
    for promise in ("Selected path", "These all fit", "fits that result", "Recommended"):
        assert promise not in text
    assert [option.action for option in card.choices.options] == ["run_panda"]
    assert card.choices.options[0].description.startswith("Not confirmed.")
    assert not any(option.badge or option.recommended for option in card.choices.options)
    # A confirmed check leaves the usual reply alone.
    confirmed = decision.model_copy(update={"capability_check": check.model_copy(update={"provisional": False})})
    assert unconfirmed_reply(confirmed, POLICY) is None


def _next_prompt_and_selected_task(task, decision, card):
    from netzoo_agent_core.cli.follow_up import build_follow_up_context
    from netzoo_agent_core.engine.machine import ConversationMachine

    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    result = {"plan": plan.model_dump(), "tool_results": [], "evaluation": None}
    prompt = build_next_turn_prompt(result)
    context = build_follow_up_context(result, prompt, task)
    state = SimpleNamespace(reply_card=card.model_dump(), next_prompt=prompt, follow_up_context=context)
    machine = SimpleNamespace(state=state, _accept_task=lambda value: value)
    selected = ConversationMachine._submit_option(machine, card.choices.options[0].model_dump())
    return prompt, selected


def test_looking_at_an_unconfirmed_workflow_keeps_the_original_requirement():
    check = CapabilityCheck(provisional=True, requirements=[CheckedRequirement(
        quote="find which splicing factors control inclusion of each alternative exon", kind="result",
        status="not_available")])
    decision = _exact_panda().model_copy(update={"capability_check": check, "recommended_actions": ["run_panda"]})
    _, _, card = _replay(SPLICING, decision)
    prompt, selected = _next_prompt_and_selected_task(SPLICING, decision, card)
    assert not prompt.allow_workflow_continuation and prompt.continuation_action is None
    assert not any(option.resolution in {"confirm_workflow", "plan_workflow"} for option in card.next_steps)
    assert SPLICING in selected and "PANDA" in selected
    assert "CONFIRMED_OUTCOME_ACTION" not in selected


def test_a_backup_reading_with_no_result_still_says_it_is_not_confirmed():
    """o10 SN6: only a methods question was read, and the reply below looked checked."""
    from netzoo_agent_core.interpretation.capability_check import PROVISIONAL_NOTE, understanding_paragraph

    check = CapabilityCheck(provisional=True, requirements=[CheckedRequirement(
        quote="Is there a method?", kind="about_methods", status="not_checked")])
    assert understanding_paragraph(check) == PROVISIONAL_NOTE


def test_the_words_fallback_never_says_a_named_kind_is_unmentioned():
    from netzoo_agent_core.interpretation.data_plan import build_data_plan

    reading = TaskDecision.model_validate(SC1["decisions"]["ce-f10-cand-SC1-1"])
    for task, state in ((SC1["task"], "stated"),
                        ("We have expression and TF motifs. We want a TF-gene network for each patient.", "unstated"),
                        ("We have expression. We want a TF-gene network for each patient.", "unstated")):
        plan = build_data_plan((), reading, None, set(), task)
        assert [(need.kind, need.state, need.source) for need in plan.needs] == [("tf_priors", state, "words")]


# -- Log 403, plan items 2, 3 and 5: what a question asks for, result forms, part answers --------

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
         "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
         "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}


def _one_sentence(task, role, quote, delivered=(), not_by=(), **attrs):
    from netzoo_agent_core.contracts.capability_check import proposal_model

    return proposal_model(1).model_validate({"s1": {
        "role": role, "has": [], "about_methods": [],
        "asks": [{**PLAIN, "quote": quote, "delivered_by": list(delivered), "not_by": list(not_by), **attrs}]}})


SPOTS = "Is there a method that builds a regulatory network for each spot, smoothed over its neighbouring spots?"


def test_a_result_asked_as_a_question_is_checked_whatever_the_sentences_role():
    """o10 SN6, heldout8 QU2-QU8: "Is there a method that ..." was a bare methods quote, never checked."""
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    quote = "builds a regulatory network for each spot, smoothed over its neighbouring spots"
    asked, _ = build_capability_check(SPOTS, _one_sentence(SPOTS, "methods_question", quote, asked_as="question"))
    assert [(item.kind, item.status, item.asked_as) for item in asked.results()] == [
        ("result", "not_available", "question")]
    assert asked.full_gap
    # A request-form ask the model matched to nothing, in a sentence it called a methods question,
    # is still read as that question (Log 387's role rule).
    told, _ = build_capability_check(SPOTS, _one_sentence(SPOTS, "methods_question", quote))
    assert told.results() == [] and not told.full_gap


def test_result_forms_no_workflow_gives_rule_every_entry_out():
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    task = "We want a fuzzy community structure in which every gene has a degree of membership in each community."
    quote = "a fuzzy community structure in which every gene has a degree of membership in each community"
    for form, value in (("group_membership", "several_groups"), ("time_model", "dynamic"),
                        ("spatial", "uses_neighbors")):
        check, _ = build_capability_check(task, _one_sentence(task, "asks", quote, ("condor.communities",),
                                                                input_network="regulator_gene", **{form: value}))
        assert check.results()[0].status == "not_available", form
    plain, _ = build_capability_check(task, _one_sentence(task, "asks", quote, ("condor.communities",),
                                                          input_network="regulator_gene",
                                                          group_membership="one_group"))
    assert plain.results()[0].status == "available"


def test_a_part_answer_makes_the_result_partly_available_and_keeps_routing(monkeypatch):
    """heldout8 QP2-QP4: communities, then an interactive 3D view, in one quote, were gapped whole."""
    from netzoo_agent_core.graph import router_invocation
    from netzoo_agent_core.interpretation.capability_check import understanding_paragraph

    task = "We want to find the communities of our TF-gene network and then render them as an interactive 3D view."
    quote = "find the communities of our TF-gene network and then render them as an interactive 3D view"
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (["part"] * len(pairs),
                                                                                       usage, warnings))
    exact = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                         capability_match_status="exact", matched_actions=["run_condor"])
    invocation = router_invocation._RouterInvocation(decision=exact, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)
    decision = router_invocation._with_capability_check(
        None, {}, task, invocation, _one_sentence(task, "asks", quote, input_network="regulator_gene")).decision
    check = decision.capability_check
    assert not check.full_gap and decision.matched_actions == ["run_condor"]
    assert check.results()[0].status == "partial" and check.results()[0].second_opinion
    assert "partly available: CONDOR gives part of it" in understanding_paragraph(check)


@pytest.mark.parametrize("actions,answers", [
    (["run_giraffe", "run_panda"], ["all", "part"]),
    (["run_panda", "run_giraffe"], ["part", "all"]),
])
def test_a_partly_delivering_workflow_is_not_an_alternative_to_a_full_delivery(actions, answers):
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation.capability_check import apply_second_opinion, second_opinion_pairs

    attrs = {key: value for key, value in PLAIN.items() if key != "asked_as"}
    attrs["regulator_kinds"] = ["tf"]
    check = CapabilityCheck(full_gap=True, requirements=[CheckedRequirement(
        quote="Infer a regulatory network and estimate each TF activity per sample.",
        kind="result", status="not_available", attrs=attrs)])
    pairs = second_opinion_pairs(check, actions)
    assert [action for _, action, _ in pairs] == actions
    item = apply_second_opinion(check, pairs, answers).results()[0]
    assert item.status == "available"
    assert {entry(key).action for key in item.delivered_by} == {"run_giraffe"}


# -- Log 403, part D: a reading routing left `unknown` is not a tie of every workflow -------------

FUSIONS = "We have RNA-seq from 60 sarcomas. We want to detect gene fusions and report which fusions recur."


def _unknown_tie(check=None, **fields):
    reading = {"outcome": {"operation": "unknown", "input_artifacts": ["expression_matrix"], "artifact_type": "unknown",
                           "entity_types": [], "regulator_types": [], "target_types": [], "granularity": "unknown"},
               "confidence": 0.5, "evidence": []}
    every = [action for action in POLICY.workflows if action.startswith("run_")]
    return TaskDecision.model_validate({
        "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.5, "reason": "r",
        "capability_match_status": "ambiguous", "hypothesis_actions": every, "outcome_hypotheses": [reading],
        "requested_outcome": reading["outcome"], "capability_check": check, **fields})


def _fusion_check(**extra):
    return CapabilityCheck(requirements=[CheckedRequirement(
        quote="detect gene fusions and report which fusions recur", kind="result", status="not_available")],
        unchecked=["one more sentence"], **extra)


def test_an_unknown_reading_offers_no_workflow_and_never_the_registry():
    for check in (_fusion_check(), _fusion_check(provisional=True), CapabilityCheck(unavailable=True), None):
        text, kind, card = _replay(FUSIONS, _unknown_tie(check))
        assert kind == "unmapped_request", check
        assert "I could not tell which registered result you are asking for, so no workflow is offered" in text
        assert not any(f"**{spec.workflow}**" in text for spec in POLICY.workflows.values())
        assert card.choices is None and "no workflow is offered" in card.headline
    text, _, _ = _replay(FUSIONS, _unknown_tie(CapabilityCheck(unavailable=True)))
    assert text.startswith("This turn could not be checked against what the registered workflows produce.\n")
    assert "asking again re-runs it" in text


def test_an_unknown_reading_offers_only_what_the_check_found_for_a_part():
    task = "We want each TF's activity per sample, and each TF's protein amount from our raw mass spectra."
    check = CapabilityCheck(requirements=[
        CheckedRequirement(quote="each TF's activity per sample", kind="result", status="available",
                           delivered_by=["giraffe.tf_activity"]),
        CheckedRequirement(quote="each TF's protein amount from our raw mass spectra", kind="result",
                           status="not_available")])
    text, kind, card = _replay(task, _unknown_tie(check))
    assert kind == "unmapped_request"
    assert "- **GIRAFFE** — for \"each TF's activity per sample\"" in text
    assert [spec.workflow for action, spec in POLICY.workflows.items() if f"**{spec.workflow}**" in text] == ["GIRAFFE"]
    assert [option.action for option in card.choices.options] == ["run_giraffe"]


@pytest.mark.parametrize("extra", [{}, {"provisional": True}])
def test_selecting_a_credited_part_keeps_its_result_and_original_scope(extra):
    task = "We want each TF's activity per sample, and each TF's protein amount from our raw mass spectra."
    check = CapabilityCheck(requirements=[
        CheckedRequirement(quote="each TF's activity per sample", kind="result", status="available",
                           delivered_by=["giraffe.tf_activity"]),
        CheckedRequirement(quote="each TF's protein amount from our raw mass spectra", kind="result",
                           status="not_available")], **extra)
    decision = _unknown_tie(check)
    _, _, card = _replay(task, decision)
    prompt, selected = _next_prompt_and_selected_task(task, decision, card)
    assert task in selected and "GIRAFFE" in selected and "each TF's activity per sample" in selected
    assert "CONFIRMED_OUTCOME_ACTION" not in selected
    assert not prompt.allow_workflow_continuation


def test_unknown_routing_does_not_call_a_wholly_confirmed_request_partial():
    task = "We want each TF's activity per sample."
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote="each TF's activity per sample", kind="result", status="available",
        delivered_by=["giraffe.tf_activity"])])
    text, kind, card = _replay(task, _unknown_tie(check))
    assert kind == "unmapped_request"
    assert "no workflow is offered for all of it" not in text
    assert "Only part" not in card.headline and "the rest" not in card.headline
    assert "GIRAFFE" in text


def test_a_long_credited_requirement_still_has_a_selectable_card():
    words = ("each TF activity per sample " + "with matched samples and common TF identifiers, " * 11).rstrip(", ")
    task = "We want " + words + "."
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote=words, kind="result", status="available", delivered_by=["giraffe.tf_activity"])])
    decision = _unknown_tie(check)
    _, _, card = _replay(task, decision)
    _, selected = _next_prompt_and_selected_task(task, decision, card)
    assert len(card.choices.options[0].answer) <= 600 and task in selected


def test_a_confirmed_question_about_the_methods_alone_keeps_the_listing():
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote="Which methods are there?", kind="about_methods", status="not_checked")])
    from netzoo_agent_core.interpretation.unmapped_routes import unmapped_reply

    assert unmapped_reply(_unknown_tie(check), POLICY) is None
    assert unmapped_reply(_unknown_tie(check.model_copy(update={"provisional": True})), POLICY) is not None


def test_an_unknown_reading_is_not_a_tie_to_ask_a_second_opinion_about(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (asked.append(pairs) or
                                                                                       ["all"] * len(pairs),
                                                                                       usage, warnings))
    invocation = router_invocation._RouterInvocation(decision=_unknown_tie(), routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)
    task = "We want to detect gene fusions and report which fusions recur."
    decision = router_invocation._with_capability_check(
        None, {}, task, invocation, _one_sentence(task, "asks", "detect gene fusions and report which fusions recur")
    ).decision
    assert decision.capability_check.full_gap and not asked


def test_the_unconstrained_tie_is_removed_from_the_decision_for_every_reader():
    from netzoo_agent_core.interpretation.unmapped_routes import without_unmapped_candidates

    tied = _unknown_tie(_fusion_check())
    cleared = without_unmapped_candidates(tied)
    assert cleared.hypothesis_actions == [] and cleared.matched_actions == [] and cleared.recommended_actions == []
    # A workflow the user named, a confirmed context, a gap or a question about the methods keep theirs.
    for kept in (tied.model_copy(update={"match_basis": "workflow_name"}),
                 tied.model_copy(update={"match_basis": "confirmed_context"}),
                 _unknown_tie(_fusion_check().model_copy(update={"full_gap": True, "unchecked": []})),
                 _unknown_tie(CapabilityCheck(requirements=[CheckedRequirement(
                     quote="Which methods are there?", kind="about_methods", status="not_checked")]))):
        assert without_unmapped_candidates(kept) is kept
