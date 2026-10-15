"""Verdict layer step 2: a result waits on a fact the user said they do not know, only when the fact decides it.

Blind set heldout416b UNKNOWN_INPUT: 0/10 such requests were asked about; feasibility eval F46 was refused.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402

CONDOR = ("Run CONDOR on the network my student made. I can't recall whether it connects TFs to genes or genes to "
          "genes.")
COEXPRESSION = ("I want a per-sample co-expression network from my count matrix. I am not sure whether the prior I "
                "downloaded includes miRNAs.")


def _ask(quote, delivered, **attrs):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "unstated", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request", **attrs}


def _check(task, ask, unknown_quote, about):
    conditions = {**unstated_conditions(), "unknown_facts": [{"quote": unknown_quote, "about": about}]}
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [ask]},
        "s2": {"role": "background", "has": [unknown_quote], "about_methods": [], "asks": []},
        "conditions": conditions})
    return build_capability_check(task, proposal)[0]


def _condor_check(input_network="gene_gene"):
    return _check(CONDOR, _ask("Run CONDOR on the network my student made", ["condor.communities"],
                               input_network=input_network),
                  "I can't recall whether it connects TFs to genes or genes to genes", "input_network")


def test_a_deciding_unknown_fact_makes_the_result_wait_instead_of_a_gap():
    """F46 / heldout416b B20: the model guessed gene-gene, which rules CONDOR out -- the user said they do not know."""
    check = _condor_check()
    (item,) = check.needed_facts()
    assert item.depends_on == "input_network" and not check.full_gap
    assert item.outcomes == {"regulator_gene": ["condor.communities"], "gene_gene": []}


def test_an_unknown_fact_that_changes_nothing_is_never_asked_about():
    check = _check(COEXPRESSION, _ask("a per-sample co-expression network", ["bonobo.per_sample_networks"],
                                      scale="per_sample"),
                   "I am not sure whether the prior I downloaded includes miRNAs", "regulator_kinds")
    assert check.needed_facts() == [] and check.results()[0].status == "available"


def test_unknown_words_not_in_the_request_are_ignored():
    check = _check(CONDOR, _ask("Run CONDOR on the network my student made", ["condor.communities"],
                                input_network="gene_gene"),
                   "I do not know the node roles", "input_network")
    assert check.needed_facts() == []


def _invocation(check, action):
    decision = TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", confidence=0.9,
                            reason="r", capability_match_status="exact", matched_actions=["run_condor"],
                            capability_check=check)
    return router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None, budget_warnings=[],
                                               reason_code=None)


def test_a_waiting_turn_selects_and_runs_nothing_and_asks_one_question(monkeypatch):
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    check = _condor_check()
    from netzoo_agent_core.interpretation.needed_facts import waiting_decision

    waiting = waiting_decision(_invocation(check, "run_condor").decision, check)
    assert waiting.action == "no_tool" and not waiting.should_execute and waiting.matched_actions == []
    assert waiting.hypothesis_actions == ["run_condor"]
    reply = respond(None, {"decision": waiting.model_dump(), "messages": []})
    text = reply["messages"][-1].content
    assert reply["reply_kind"] == "needs_fact"
    assert ("depends on whether your network links regulators to genes or genes to genes, which you said you do not "
            "know") in text
    assert "if regulators to genes: CONDOR; if genes to genes: no registered workflow gives this." in text
    assert "Before I choose a workflow, please tell me: Does your network link regulators" in text
    assert "No registered workflow produces" not in text


def test_the_run_path_waits_too(monkeypatch):
    """heldout416b B20 ("Run community detection on the network my student made ..."): a run is not planned."""
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("Run CONDOR on the network my student made", ["condor.communities"], input_network="gene_gene")]},
        "s2": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(), "unknown_facts": [
            {"quote": "I can't recall whether it connects TFs to genes or genes to genes", "about": "input_network"}]}})
    updated = router_invocation._with_run_check(None, {}, CONDOR, _invocation(None, "run_condor"), proposal, "ok")
    assert updated.decision.action == "no_tool" and updated.decision.capability_check.needed_facts()


def _puma_decision(delivered=("puma.regulator_gene_network",), plan=None):
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement

    requirement = CheckedRequirement(quote="a TF and miRNA regulatory network", kind="result", status="available",
                                     delivered_by=list(delivered))
    check = CapabilityCheck(requirements=[requirement], unknowns=[[
        "regulator_kinds", "The target prior I downloaded may include miRNA-target pairs or may only hold TF-gene "
                           "motif hits"]])
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_check=check, data_plan=plan)


def test_an_unknown_mirna_input_a_credited_workflow_takes_is_asked_in_the_users_words():
    """Pre-measure B23: PUMA gives the network either way; what waits is PUMA's miRNA input."""
    from netzoo_agent_core.interpretation.data_plan import plan_with_unknowns, render_plan_block

    plan = plan_with_unknowns(None, _puma_decision())
    (need,) = plan.needs
    assert (need.kind, need.action) == ("mirna", "ask")
    assert render_plan_block(plan, "") == (
        '**Data your question needs.** Your question needs a miRNA list, and you said you do not know whether your '
        'data has it ("The target prior I downloaded may include miRNA-target pairs or may only hold TF-gene motif '
        'hits"). Does it?')


def test_no_mirna_ask_when_no_credited_workflow_takes_it_or_the_request_rules_it_out():
    from netzoo_agent_core.contracts.data_plan import DataNeed, DataPlan
    from netzoo_agent_core.interpretation.data_plan import plan_with_unknowns

    assert plan_with_unknowns(None, _puma_decision(("panda.tf_gene_network",))) is None
    ruled_out = DataPlan(answerable=True, basis="question", needs=[DataNeed(
        kind="mirna", state="ruled_out", source="model", quote="the miRNA list is missing", action="say_ruled_out")])
    assert plan_with_unknowns(ruled_out, _puma_decision(plan=ruled_out)) is ruled_out


def _blank(quote, **attrs):
    from netzoo_agent_core.contracts.capability_check import CheckedRequirement

    base = {"scale": "unstated", "omics_layers": 2, "data_unit": "not_stated", "regulator_kinds": [],
            "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
            "time_model": "not_dynamic", "spatial": "not_spatial"}
    return CheckedRequirement(quote=quote, kind="result", status="not_available", blank=True, attrs={**base, **attrs})


DRAGON_PAIRS = [(0, "run_dragon", ["dragon.two_layer_network", "dragon.edge_pvalues"]),
                (0, "run_lioness_dragon", ["lioness_dragon.per_sample_networks"])]


def test_an_unknown_fact_decides_among_the_workflows_the_second_opinion_weighed():
    """Live B30: nothing credited, second opinion 'part' for DRAGON/LIONESS-DRAGON, layer count unknown -> wait."""
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked

    check = CapabilityCheck(requirements=[_blank("partial-correlation networks linking my omics layers")],
                            full_gap=True, unknowns=[["omics_layers", "whether there are two layers or more"]])
    updated = wait_on_asked(check, DRAGON_PAIRS)
    (item,) = updated.needed_facts()
    assert not updated.full_gap and item.depends_on == "omics_layers"
    assert item.outcomes["3"] == [] and "dragon.two_layer_network" in item.outcomes["2"]


def test_without_an_unknown_fact_or_a_deciding_one_the_gap_stands():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked

    plain = CapabilityCheck(requirements=[_blank("a network")], full_gap=True)
    assert wait_on_asked(plain, DRAGON_PAIRS) is plain
    undecided = CapabilityCheck(requirements=[_blank("a network")], full_gap=True,
                                unknowns=[["data_unit", "not sure"]])
    assert wait_on_asked(undecided, [(0, "run_dragon", [])]) is undecided


F41 = ("Run DRAGON on my RNA and methylation tables. I do not know whether their columns are in the same sample order, "
       "and I have not supplied sample IDs or file paths.")
B18 = "We want a network linking our RNA and methylation tables. I am not sure they came from the same patients."


def test_file_alignment_is_checked_but_biological_identity_is_asked():
    unknown = "I do not know whether their columns are in the same sample order"
    check = _check(F41, _ask("Run DRAGON on my RNA and methylation tables.",
                            ["dragon.two_layer_network"], omics_layers=2), unknown, "sample_alignment")
    (item,) = check.results()
    assert not check.needed_facts() and item.file_checked == "sample_alignment"
    from netzoo_agent_core.interpretation.capability_check import understanding_paragraph
    assert "Matching IDs do not establish biological identity" in understanding_paragraph(check)
    check = _check(B18, _ask("a network linking our RNA and methylation tables",
                            ["dragon.two_layer_network"], omics_layers=2),
                   "I am not sure they came from the same patients", "samples_matched")
    assert check.needed_facts()[0].depends_on == "samples_matched"


def test_facts_the_files_do_not_settle_are_still_asked():
    """CONDOR's input check only warns on overlapping node IDs, so node roles are asked (B03); so is the data unit."""
    assert _condor_check().needed_facts()[0].file_checked is None
    cells = "I want a per-sample co-expression network. Its columns could be single cells or bulk libraries."
    check = _check(cells, _ask("a per-sample co-expression network", ["lioness_coexpression.per_sample_networks"],
                               scale="per_sample"), "Its columns could be single cells or bulk libraries", "data_unit")
    assert check.needed_facts()[0].depends_on == "data_unit"


def test_a_second_opinion_gap_with_unknown_biological_identity_waits():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked

    check = CapabilityCheck(requirements=[_blank("a network linking the two tables")], full_gap=True,
                            unknowns=[["samples_matched", "not sure they are the same patients"]])
    (item,) = wait_on_asked(check, DRAGON_PAIRS).results()
    assert item.status == "needs_fact" and item.file_checked is None
    assert set(item.delivered_by) == {"dragon.two_layer_network", "dragon.edge_pvalues",
                                      "lioness_dragon.per_sample_networks"}


def test_new_deciding_facts_and_irrelevant_unknowns():
    cases = [
        ("sample_count", "I don't know the sample count", "lioness_coexpression.per_sample_networks", {}),
        ("mutation_origin", "I don't know if variants are somatic or germline", "sambar.subtypes", {}),
        ("value_type", "I don't know if measurements are binary or continuous", "dragon.two_layer_network", {"omics_layers": 2}),
        ("mirna_driver", "I don't know whether miRNA links must use expression or a target prior",
         "puma.regulator_gene_network", {"regulator_kinds": ["tf", "mirna"]}),
    ]
    for about, unknown, key, attrs in cases:
        task = "Please produce the result. " + unknown
        check = _check(task, _ask("Please produce the result", [key], **attrs), unknown, about)
        assert check.needed_facts()[0].depends_on == about
        # An unrelated CONDOR request must not inherit mutation/measurement/sample-count constraints.
        irrelevant = _check(task, _ask("Please produce the result", ["condor.communities"]), unknown, about)
        assert not irrelevant.needed_facts()


def test_sample_count_question_tracks_executor_minimum(monkeypatch):
    from netzoo_agent_core.data import inspection
    from netzoo_agent_core.interpretation.needed_facts import fact_line
    monkeypatch.setattr(inspection, "LIONESS_MIN_SAMPLES", 7)
    task = "Please infer per-sample networks. I don't know the sample count"
    check = _check(task, _ask("infer per-sample networks", ["lioness_coexpression.per_sample_networks"]),
                   "I don't know the sample count", "sample_count")
    item = check.needed_facts()[0]
    assert item.outcomes["6"] == [] and item.outcomes["7"]
    assert "if 7 samples" in fact_line(item)


def test_backup_read_still_asks_and_does_not_authorize_a_run(monkeypatch):
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    task = "Please infer per-sample networks. I don't know the sample count"
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("infer per-sample networks", ["lioness_coexpression.per_sample_networks"])]},
        "s2": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(), "unknown_facts": [
            {"quote": "I don't know the sample count", "about": "sample_count"}]}})
    for action, shadow in (("no_tool", None), ("run_lioness_coexpression", "ok")):
        result = router_invocation._with_capability_check(
            None, {}, task, _invocation(None, action), proposal, provisional=True, shadow_status=shadow)
        decision = result.decision
        assert decision.action == "no_tool" and not decision.should_execute
        assert decision.capability_check.provisional
        assert "independent biological samples" in decision.clarification_question
        reply = respond(None, {"decision": decision.model_dump(), "messages": []})
        assert reply["reply_kind"] == "needs_fact"
        assert "How many independent biological samples" in reply["messages"][-1].content


def test_second_opinion_cannot_credit_a_stale_pair_exceeding_typed_limit():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import apply_second_opinion
    check = CapabilityCheck(requirements=[_blank("joint network", omics_layers=5)], full_gap=True)
    updated = apply_second_opinion(check, DRAGON_PAIRS, ["all", "named"])
    assert updated.full_gap and not updated.results()[0].delivered_by


def test_joint_layer_range_is_not_replaced_by_two_layer_second_opinion():
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs
    task = "We may have four or five layers. Please model all of them jointly."
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "background", "has": ["We may have four or five layers"], "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask("model all of them jointly", [])]},
        "conditions": {**unstated_conditions(), "joint_layers": 4, "joint_layers_quote": "four or five layers",
                       "unknown_facts": [{"about": "omics_layers", "quote": "may have four or five layers"}]}})
    check = build_capability_check(task, proposal)[0]
    assert check.results()[0].attrs["omics_layers"] == 4
    assert not check.needed_facts()
    assert second_opinion_pairs(check, ["run_dragon", "run_lioness_dragon"]) == []


def test_second_opinion_all_cannot_skip_a_deciding_unknown():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import apply_second_opinion, wait_on_asked
    check = CapabilityCheck(requirements=[_blank("joint network")], full_gap=True,
                            unknowns=[["value_type", "not sure if binary or continuous"]])
    check = wait_on_asked(apply_second_opinion(check, DRAGON_PAIRS, ["all", "all"]), DRAGON_PAIRS)
    assert check.needed_facts()[0].depends_on == "value_type"


def test_file_alignment_does_not_hide_a_later_biological_unknown():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked
    check = CapabilityCheck(requirements=[_blank("joint network")], full_gap=True,
                            unknowns=[["sample_alignment", "not sure the IDs match"],
                                      ["samples_matched", "not sure they are the same patients"]])
    item = wait_on_asked(check, DRAGON_PAIRS).needed_facts()[0]
    assert item.depends_on == "samples_matched" and item.file_checked is None


def test_sample_count_counterfactuals_keep_settings_and_output_limits():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked
    from netzoo_agent_core.interpretation.needed_facts import fact_line
    cases = [
        ("run_sambar", "sambar.subtypes", {"settings": [{"name": "SAMBAR.kmax", "quote": "kmax", "value": "6"}]},
         "I don't know whether there are 4 or 8 samples", "4", "8"),
        ("run_lioness_dragon", "lioness_dragon.per_sample_networks", {"features": 1000},
         "I don't know whether there are 4 or 100 samples", "100", "4"),
    ]
    for action, key, method, quote, blocked, allowed in cases:
        requirement = _blank("result", omics_layers=2 if "dragon" in action else 0).model_copy(update={"method": method})
        check = CapabilityCheck(requirements=[requirement], full_gap=True, unknowns=[["sample_count", quote]])
        item = wait_on_asked(check, [(0, action, [key])]).needed_facts()[0]
        assert item.outcomes[blocked] == [] and item.outcomes[allowed] == [key]
        assert "at least" not in fact_line(item)
        # No explicit alternatives: derive representative cases from the same runtime boundaries.
        plain = check.model_copy(update={"unknowns": [["sample_count", "I don't know how many samples"]]})
        assert wait_on_asked(plain, [(0, action, [key])]).needed_facts()


def test_unknown_fact_is_scoped_to_its_own_data_and_result():
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs, apply_second_opinion, wait_on_asked
    task = ("Produce subtypes from the confirmed somatic cohort. Produce subtypes for the archive too. "
            "The archive variants may be somatic or germline.")
    first, second = "Produce subtypes from the confirmed somatic cohort", "Produce subtypes for the archive too"
    unknown = "The archive variants may be somatic or germline"
    for applies, expected in (([], 0), ([second], 1), (["invented result"], 0)):
        proposal = proposal_model(3).model_validate({
            "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
                _ask(first, ["sambar.subtypes"], mutation_origin="somatic")]},
            "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(second, ["sambar.subtypes"])]},
            "s3": {"role": "background", "has": [unknown], "about_methods": [], "asks": []},
            "conditions": {**unstated_conditions(), "unknown_facts": [
                {"about": "mutation_origin", "quote": unknown, "applies_to": applies}]}})
        check = build_capability_check(task, proposal)[0]
        assert check.results()[0].status == "available"
        assert len(check.needed_facts()) == expected
        # The same scope must survive a blank first reading and second-opinion credit.
        blank = check.model_copy(update={"requirements": [x.model_copy(update={"status": "not_available", "delivered_by": []})
                                                          if x.kind == "result" else x for x in check.requirements], "full_gap": True})
        pairs = second_opinion_pairs(blank, ["run_sambar"])
        restored = wait_on_asked(apply_second_opinion(blank, pairs, ["all"] * len(pairs)), pairs)
        assert restored.results()[0].status == "available"
        assert len(restored.needed_facts()) == expected


def test_count_ranges_probe_interior_but_discrete_choices_do_not():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import wait_on_asked, second_opinion_pairs
    requirement = _blank("joint networks").model_copy(update={"method": {"features": 1000}})
    for kind, quote, asked in (("range", "somewhere between 1 and 100 samples", True),
                               ("choices", "either 1 or 100 samples", False)):
        check = CapabilityCheck(requirements=[requirement], full_gap=True, unknowns=[["sample_count", quote]],
                                unknown_domains={quote: {"kind": kind, "values": [1, 100]}})
        pairs = [(0, "run_lioness_dragon", ["lioness_dragon.per_sample_networks"])]
        result = wait_on_asked(check, pairs)
        assert bool(result.needed_facts()) is asked
        if asked:
            assert any(result.needed_facts()[0].outcomes.values())
        else:
            assert result.full_gap
            assert second_opinion_pairs(check, ["run_lioness_dragon"]) == []


def test_uniformly_impossible_count_choices_do_not_credit_initial_reading():
    task = "Infer joint networks. We will have either 1 or 100 samples."
    unknown = "either 1 or 100 samples"
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
            "Infer joint networks", ["lioness_dragon.per_sample_networks"], omics_layers=2,
            feature_counts=[{"count": 1000, "quote": "1000 features"}])]},
        "s2": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(), "unknown_facts": [{"about": "sample_count", "quote": unknown,
                         "count_kind": "choices", "count_values": [1, 100]}]}})
    # Quoted features must really be in the request before the cap is applied.
    task += " There are 1000 features."
    check = build_capability_check(task, proposal)[0]
    assert check.results()[0].status == "not_available" and not check.needed_facts()


def test_multiple_unknowns_do_not_depend_on_guess_or_order():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs, wait_on_asked
    unknowns = [["sample_count", "I don't know the sample count"],
                ["value_type", "I don't know if measurements are binary or continuous"]]
    for ordered in (unknowns, list(reversed(unknowns))):
        check = CapabilityCheck(requirements=[_blank("joint network", value_type="binary")], full_gap=True,
                                unknowns=ordered)
        pairs = second_opinion_pairs(check, ["run_dragon"])
        assert pairs
        result = wait_on_asked(check, pairs)
        assert result.needed_facts() and not result.full_gap
        assert any(result.needed_facts()[0].outcomes.values())


def test_an_independently_impossible_count_domain_wins_in_either_unknown_order():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs, wait_on_asked
    count = "either 1 or 100 samples"
    unknowns = [["sample_count", count], ["value_type", "binary or continuous"]]
    requirement = _blank("joint networks", value_type="binary").model_copy(update={"method": {"features": 1000}})
    for ordered in (unknowns, list(reversed(unknowns))):
        check = CapabilityCheck(requirements=[requirement], full_gap=True, unknowns=ordered,
                                unknown_domains={count: {"kind": "choices", "values": [1, 100]}})
        assert second_opinion_pairs(check, ["run_lioness_dragon"]) == []
        result = wait_on_asked(check, [(0, "run_lioness_dragon", ["lioness_dragon.per_sample_networks"])])
        assert result.full_gap and not result.needed_facts()


def test_alignment_unknown_cannot_override_known_different_biological_samples():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs, wait_on_asked
    check = CapabilityCheck(requirements=[_blank("joint network", samples_matched="different_samples")], full_gap=True,
                            unknowns=[["sample_alignment", "not sure the file IDs match"]])
    assert second_opinion_pairs(check, ["run_dragon"]) == []
    assert wait_on_asked(check, DRAGON_PAIRS).full_gap
