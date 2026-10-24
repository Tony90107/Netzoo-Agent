"""M2 A (2026-10-14): a part that cannot be done is a requirement of its own and never takes the doable part with it.

Final acceptance a24b: MX10's overlapping communities refused CONDOR's communities too; MX02's dashboard was dropped
because it named the result; S138's output folder was refused as a delivery. Also the open items M1 left: settings a
request gives for one of several results, and the settings rules that held only in the executors.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, request_sentences, understanding_paragraph,
)
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402
from netzoo_agent_core.workflow_conditions import StatedSetting, combination_issues, conditions_for  # noqa: E402


def _check(task, *asks, has=(), **conditions):
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{index}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for index in range(1, len(sentences) + 1)}
    for ask in asks:
        index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
        readings[f"s{index}"]["asks"].append(ask)
        readings[f"s{index}"]["role"] = "asks"
    for quote in has:
        index = next(i for i, text in enumerate(sentences, 1) if quote in text)
        readings[f"s{index}"]["has"].append(quote)
    readings["conditions"] = {**unstated_conditions(), **conditions}
    check, rejected = build_capability_check(task, proposal_model(len(sentences)).model_validate(readings))
    assert not rejected, rejected
    return check


MX10 = ("Run CONDOR on our thresholded OTTER edge list otter_edges.csv (positive weights only) to get TF-gene "
        "communities, and allow genes to sit in more than one community.")


def test_mx10_overlap_stated_beside_the_ask_is_its_own_requirement():
    # As recorded: the ask itself typed several_groups, from the clause after it.
    check = _check(MX10, _ask("TF-gene communities", ["condor.communities"], group_membership="several_groups",
                              regulator_kinds=["tf"], input_network="regulator_gene", scale="whole_cohort"),
                   group_membership="several_groups",
                   group_membership_quote="allow genes to sit in more than one community")
    assert [(item.quote, item.status) for item in check.results()] == [
        ("TF-gene communities", "available"), ("allow genes to sit in more than one community", "not_available")]
    assert "none returns overlapping memberships" in understanding_paragraph(check)
    assert run_check_verdict(check, "run_condor")["verdict"] == "partial_gap"  # the run is held, never cut short


def test_an_ask_whose_own_words_ask_for_overlap_is_still_refused():
    task = "We want overlapping communities of our bipartite TF-gene network."
    check = _check(task, _ask("overlapping communities of our bipartite TF-gene network", ["condor.communities"],
                              group_membership="several_groups", input_network="regulator_gene"),
                   group_membership="several_groups", group_membership_quote="overlapping communities")
    assert [item.status for item in check.results()] == ["not_available"]


def test_matched_samples_and_data_units_still_rule_the_ask_out():
    # Facts about the user's data are not result forms (heldout17 KN1/KN3, a24b K02).
    task = "We want a DRAGON network of our two layers. The two layers were not measured on the same samples."
    check = _check(task, _ask("a DRAGON network of our two layers", ["dragon.two_layer_network"], omics_layers=2),
                   samples_matched="different_samples",
                   samples_matched_quote="The two layers were not measured on the same samples")
    assert [item.status for item in check.results()] == ["not_available"]


MX02 = ("Run LIONESS-PANDA on the 80 sarcoma samples with our motif and PPI priors, then put the per-sample networks "
        "into an interactive dashboard the clinicians can browse.")


def test_mx02_a_delivery_that_names_the_result_is_kept():
    check = _check(MX02, _ask("the per-sample networks", ["lioness_panda.per_sample_networks"], scale="per_sample",
                              regulator_kinds=["tf"]),
                   other_requirements=[{"about": "delivery", "quote": "put the per-sample networks into an "
                                        "interactive dashboard the clinicians can browse"}])
    assert [item.status for item in check.results()] == ["available", "not_available"]
    assert run_check_verdict(check, "run_lioness_panda")["verdict"] == "partial_gap"


def test_s138_an_output_folder_is_not_a_delivery():
    task = "We would like pathway mutation scores for every tumour. Outputs can go to /registry/sambar_run1."
    check = _check(task, _ask("pathway mutation scores for every tumour", ["sambar.subtypes"]),
                   other_requirements=[{"about": "delivery", "quote": "Outputs can go to /registry/sambar_run1"}])
    assert [item.status for item in check.results()] == ["available"]
    emailed = "We would like pathway mutation scores for every tumour, e-mailed to dr.lee@example.org."
    check = _check(emailed, _ask("pathway mutation scores for every tumour", ["sambar.subtypes"]),
                   other_requirements=[{"about": "delivery", "quote": "e-mailed to dr.lee@example.org"}])
    assert [item.status for item in check.results()] == ["available", "not_available"]


def test_a_one_level_output_folder_is_not_a_delivery_either():
    # Held-out h5 Q37: "Outputs can go to glioma_out/" refused a doable LIONESS-PUMA run as a delivery.
    task = "We would like pathway mutation scores for every tumour. Outputs can go to glioma_out/."
    check = _check(task, _ask("pathway mutation scores for every tumour", ["sambar.subtypes"]),
                   other_requirements=[{"about": "delivery", "quote": "Outputs can go to glioma_out/"}])
    assert [item.status for item in check.results()] == ["available"]


def test_settings_for_one_of_several_results_go_to_that_result():
    task = "Run DRAGON with lambda1 0.3 on our two layers, and run OTTER on our expression with motif and PPI."
    whole = {"named_method": "none", "named_method_quote": "",
             "settings": [{"name": "DRAGON.lambda1", "quote": "lambda1", "value_quote": "0.3"}]}
    check = _check(task, _ask("Run DRAGON with lambda1 0.3 on our two layers", ["dragon.two_layer_network"],
                              omics_layers=2),
                   _ask("run OTTER on our expression with motif and PPI", ["otter.tf_gene_network"],
                        regulator_kinds=["tf"]), **whole)
    dragon, otter = check.results()
    # The lone lambda1 holds DRAGON (both lambdas or neither); OTTER is not held to a DRAGON setting.
    assert dragon.status == "not_available" and "lambda1 and lambda2 must be supplied together" in dragon.limits[0]
    assert otter.status == "available" and "settings" not in otter.method


def test_combination_rules_are_the_executors():
    assert combination_issues(conditions_for("LIONESS-DRAGON"), [StatedSetting("LIONESS-DRAGON.lambda1", "lambda1",
                                                                                "0.3")])
    assert not combination_issues(conditions_for("DRAGON"), [StatedSetting("DRAGON.lambda1", "lambdas", "0.2"),
                                                             StatedSetting("DRAGON.lambda2", "lambdas", "0.6")])
    # ROUND-12 C17: one lambda fixed, the other named without a number (estimated) -- one manual value alone.
    assert combination_issues(conditions_for("DRAGON"), [
        StatedSetting("DRAGON.lambda1", "the transcript layer's shrinkage is fixed at 0.3", "0.3"),
        StatedSetting("DRAGON.lambda2", "the metabolite layer's shrinkage is estimated from the data", "")])
    # h2 J11: both named without a number -- both estimated, the default.
    assert not combination_issues(conditions_for("DRAGON"), [StatedSetting("DRAGON.lambda1", "lambda1", ""),
                                                             StatedSetting("DRAGON.lambda2", "lambda2", "")])
    assert combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmin", "kmin", "5")])  # default kmax 4
    assert combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=4)
    assert not combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=200)
    assert combination_issues(conditions_for("BONOBO"), [StatedSetting("BONOBO.sparsify", "sparsify", ""),
                                                         StatedSetting("BONOBO.delta", "delta", "0.5")])
    assert not combination_issues(conditions_for("BONOBO"), [StatedSetting("BONOBO.delta", "delta", "0.5")])


def test_boolean_values_control_when_combination_limits_apply():
    for words in ("false", "off", "disabled", "do not sparsify"):
        assert not combination_issues(conditions_for("BONOBO"), [
            StatedSetting("BONOBO.sparsify", "sparsify", words), StatedSetting("BONOBO.delta", "delta", "0.5")])
        assert not combination_issues(conditions_for("SAMBAR"), [
            StatedSetting("SAMBAR.cluster", "cluster", words), StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=4)
    for words in ("true", "on", "enabled"):
        assert combination_issues(conditions_for("BONOBO"), [
            StatedSetting("BONOBO.sparsify", "sparsify", words), StatedSetting("BONOBO.delta", "delta", "0.5")])
        assert combination_issues(conditions_for("SAMBAR"), [
            StatedSetting("SAMBAR.cluster", "cluster", words), StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=4)


# --- a24b MX03 / MX09: what an ask adds to a result it also names on its own ---------------------------------------

MX03 = ("We'd like a DRAGON network between the proteome and the transcriptome of our 64 matched tumours, and please "
        "fold the metabolome from the same tumours into the same model as a third layer.")
MX09 = ("We want a network of TFs and miRNAs regulating genes in our 72 hepatoblastoma samples (expression, motif prior "
        "with miRNA edges, miRNA list and PPI are ready), with the lncRNAs added as a third regulator class in the same "
        "network using our lncRNA-target predictions.")


def _adds(*items):
    return [{"quote": quote, "adds": kind} for quote, kind in items]


def test_mx03_the_two_layer_network_stands_and_the_third_layer_is_refused():
    # As recorded: one ask of three layers, nothing credited, DRAGON's near miss cited; plus the typed addition.
    ask = {**_ask(MX03.rstrip("."), (), ["dragon.no_more_layers"], omics_layers=3, scale="whole_cohort"),
           "adds": _adds(("fold the metabolome from the same tumours into the same model as a third layer",
                          "omics_layer"))}
    check = _check(MX03, ask)
    core, third = check.results()
    assert core.quote == ("We'd like a DRAGON network between the proteome and the transcriptome of our 64 matched "
                          "tumours")
    assert core.status == "available" and "dragon.two_layer_network" in core.delivered_by
    # P5 r1 (h7 S04): the near miss is the model's reading, which code cannot verify, so it is not said -- the cost: here
    # it was the right reason. The third layer is still refused, in layer 2.
    paragraph = understanding_paragraph(check)
    assert third.status == "not_available" and "does not give it" not in paragraph
    assert "I couldn't match this to anything a registered NetZoo workflow produces or lets you set." in paragraph
    assert run_check_verdict(check, "run_dragon")["verdict"] == "partial_gap"


def test_mx09_tf_and_mirna_stand_and_lncrna_is_refused():
    ask = {**_ask(MX09.rstrip("."), (), ["puma.no_lncrna_cerna"], omics_layers=2,
                  regulator_kinds=["tf", "mirna", "lncrna"], input_network="regulator_gene", scale="whole_cohort"),
           "adds": _adds(("with the lncRNAs added as a third regulator class in the same network using our "
                          "lncRNA-target predictions", "regulator_class"))}
    check = _check(MX09, ask)
    core, lncrna = check.results()
    assert core.status == "available" and core.delivered_by == ["puma.regulator_gene_network"]
    assert core.quote.endswith("are ready)")
    assert lncrna.status == "not_available" and "none models lncRNA regulators" in understanding_paragraph(check)


def test_a_result_named_as_a_whole_is_not_split():
    # a24b U15 shape: four layers as one model, no addition typed -- refused whole, as before.
    task = "We want one network that joins our genome, transcriptome, proteome and metabolome in a single model."
    check = _check(task, _ask("one network that joins our genome, transcriptome, proteome and metabolome in a single "
                              "model", (), ["dragon.no_more_layers"], omics_layers=4))
    assert [item.status for item in check.results()] == ["not_available"]


def test_an_overlap_typed_both_as_an_addition_and_a_condition_is_one_line():
    ask = {**_ask("to get TF-gene communities, and allow genes to sit in more than one community",
                  ["condor.communities"], group_membership="several_groups", input_network="regulator_gene"),
           "adds": _adds(("allow genes to sit in more than one community", "group_overlap"))}
    check = _check(MX10, ask, group_membership="several_groups",
                   group_membership_quote="allow genes to sit in more than one community")
    assert [(item.quote, item.status) for item in check.results()] == [
        ("to get TF-gene communities", "available"), ("allow genes to sit in more than one community", "not_available")]


# --- a24b N35 / MX14: a requirement in the asking sentence, outside the ask's words --------------------------------

N35 = ("Build a PUMA network in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA "
       "expression levels in the same 80 samples.")


def test_n35_an_unmet_requirement_beside_the_ask_is_its_own_line():
    from netzoo_agent_core.interpretation.capability_check import condition_pairs, stated_requirements
    from netzoo_agent_core.interpretation.requirement_split import apply_own_sentence_answers

    quote = ("in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA expression levels")
    check = _check(N35, _ask("Build a PUMA network", ["puma.regulator_gene_network"], omics_layers=2,
                             regulator_kinds=["tf", "mirna"], scale="whole_cohort"),
                   other_requirements=[{"about": "how_computed", "quote": quote},
                                       {"about": "how_computed", "quote": "Build a PUMA network"}])
    proposal_free = stated_requirements(N35, _proposal_of(N35, quote), check)
    own = stated_requirements(N35, _proposal_of(N35, quote), check, own_sentence=True)
    assert proposal_free == [] and own == [quote]  # the ask's own words are never checked again
    pairs = condition_pairs(check, own)
    assert [action for _index, action, _keys, _quote in pairs] == ["run_puma"]
    unmet = apply_own_sentence_answers(check, pairs, ["violates"])
    assert [(item.quote[:20], item.status) for item in unmet.results()] == [
        ("Build a PUMA network", "available"), ("in which the miRNA-g", "not_available")]
    assert unmet.results()[1].limits[0].startswith('PUMA does not meet "in which the miRNA-gene')
    # ROUND-20 B: the model's answer holds the row and is never said as its reason.
    assert '"in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA expression levels" -- ' \
           "I couldn't match this to anything a registered NetZoo workflow produces or lets you set." in understanding_paragraph(unmet)
    assert run_check_verdict(unmet, "run_puma")["verdict"] == "partial_gap"
    # Met or unrelated: nothing is added. Unanswered checks are held by the router.
    assert apply_own_sentence_answers(check, pairs, ["satisfies"]).results() == check.results()
    assert apply_own_sentence_answers(check, pairs, ["unrelated"]).results() == check.results()


def _proposal_of(task, quote):
    from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions

    return proposal_model(1).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(), "other_requirements": [
            {"about": "how_computed", "quote": quote}, {"about": "how_computed", "quote": "Build a PUMA network"}]}})


def test_the_router_checks_the_asking_sentence_requirement_in_the_same_call(monkeypatch):
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph import router_invocation

    quote = "in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA expression levels"
    proposal = _proposal_of(N35, quote).model_copy(update={"s1": proposal_model(1).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
            "Build a PUMA network", ["puma.regulator_gene_network"], omics_layers=2, regulator_kinds=["tf", "mirna"],
            scale="whole_cohort")]}}).s1})
    decision = TaskDecision.model_validate({"action": "no_tool", "in_scope": True, "should_execute": False,
                                            "confidence": 0.9, "reason": "r", "capability_match_status": "exact",
                                            "matched_actions": ["run_puma"]})
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    for answer, statuses in (("violates", ["available", "not_available"]), ("satisfies", ["available"])):
        calls = []

        def condition_check(context, state, shown, usage, warnings, **kwargs):
            calls.append(shown)
            return [answer] * len(shown), usage, warnings

        monkeypatch.setattr(router_invocation, "request_condition_check", condition_check)
        invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                         budget_warnings=[], reason_code=None)
        result = router_invocation._with_capability_check(SimpleNamespace(project_policy=None), {}, N35, invocation,
                                                          proposal)
        assert len(calls) == 1 and [shown[1] for shown in calls[0]] == [quote]
        assert [item.status for item in result.decision.capability_check.results()] == statuses


def test_a_run_waits_when_its_own_sentence_condition_could_not_be_checked(monkeypatch):
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph import router_invocation

    quote = "in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA expression levels"
    proposal = _proposal_of(N35, quote).model_copy(update={"s1": proposal_model(1).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
            "Build a PUMA network", ["puma.regulator_gene_network"], omics_layers=2, regulator_kinds=["tf", "mirna"],
            scale="whole_cohort")]}}).s1})
    decision = TaskDecision(action="run_puma", in_scope=True, should_execute=True, confidence=0.9,
                            reason="r", capability_match_status="exact", matched_actions=["run_puma"])
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    for answer, expected in ((None, "unread"), (["violates"], "partial_gap"), (["satisfies"], "agrees")):
        monkeypatch.setattr(router_invocation, "request_condition_check",
                            lambda context, state, shown, usage, warnings: (answer, usage, warnings))
        invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                         budget_warnings=[], reason_code=None)
        result = router_invocation._with_run_check(SimpleNamespace(project_policy=None), {}, N35, invocation,
                                                   proposal, "ok")
        assert result.decision.run_verdict.verdict == expected
        assert result.decision.should_execute is (expected == "agrees")
        if answer is None:
            assert quote in result.decision.capability_check.unchecked


def test_g1_an_addition_beside_the_asks_words_and_a_blank_core_named_by_its_method():
    # live m2a G1: the addition sat in the ask's sentence outside its words, and nothing was credited to the core.
    task = ("Build an aggregate PANDA network for our 60 lung adenocarcinoma samples from expression, motifs and PPI, "
            "and add our lncRNAs as a further class of regulators in the same network.")
    ask = {**_ask("aggregate PANDA network", (), named="PANDA", named_quote="PANDA", omics_layers=1,
                  regulator_kinds=["tf", "lncrna"], scale="whole_cohort"),
           "adds": _adds(("add our lncRNAs as a further class of regulators", "regulator_class"))}
    core, lncrna = _check(task, ask).results()
    assert (core.quote, core.status) == ("aggregate PANDA network", "available")
    assert "panda.tf_gene_network" in core.delivered_by
    assert (lncrna.quote, lncrna.status) == ("add our lncRNAs as a further class of regulators", "not_available")


# --- live m2b P30: the backup model's provider takes at most 1,000 enum values per schema ----------------------------

def test_the_compact_schema_stays_under_the_enum_limit_and_reads_the_same():
    from netzoo_agent_core.contracts.capability_check import MAX_SENTENCES
    from netzoo_agent_core.contracts.strict_schema import expanded_enum_values

    assert expanded_enum_values(proposal_model(9).model_json_schema()) > 1000  # what m2b P30's backup call refused
    assert expanded_enum_values(proposal_model(MAX_SENTENCES, compact=True).model_json_schema()) <= 1000
    task = "Can you infer TF activities for our 70 samples with the TIGER Bayesian model and an L1 penalty of 0.1?"
    ask = {**_ask("infer TF activities", ["giraffe.tf_activity", "made.up_entry"], named="TIGER",
                  named_quote="TIGER Bayesian model", asked_as="question"),
           "settings": [{"name": "GIRAFFE.l1_penalty", "quote": "an L1 penalty of 0.1", "value_quote": "0.1"}]}
    proposal = proposal_model(1, compact=True).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [ask]}, "conditions": unstated_conditions()})
    [result] = build_capability_check(task, proposal)[0].results()
    # Names not registered are unregistered; ids not on the sheet are dropped.
    assert result.method["named"] == "unregistered" and result.method["settings"][0]["name"] == "unregistered"
    assert result.status == "not_available" and result.instead == ["giraffe.tf_activity"]


def test_the_backup_call_takes_the_compact_schema_for_a_long_request(monkeypatch):
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.contracts.strict_schema import expanded_enum_values
    from netzoo_agent_core.graph import capability_check_call as call

    seen = []

    class Recording:
        def with_structured_output(self, schema, **kwargs):
            seen.append(expanded_enum_values(schema.model_json_schema()))
            return self

        def invoke(self, messages):
            raise ValueError("Semantic structured output could not be decoded")

    monkeypatch.delenv("OPENROUTER_CAPABILITY_MODEL", raising=False)
    monkeypatch.setattr(call, "preflight_budget", lambda context, state, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    context = SimpleNamespace(study_purpose_llm=Recording(), semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    long_request = " ".join(f"Sentence {index} asks for a TF-gene network." for index in range(1, 10))
    call.request_capability_check(context, {}, long_request, LLMUsage(budget_tokens=30000), [])
    assert seen and all(count <= 1000 for count in seen)


def test_second_opinion_credit_rechecks_own_sentence_conditions(monkeypatch):
    from types import SimpleNamespace
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph import router_invocation
    quote = "in which the miRNA-gene edge weights are driven by our matched small-RNA-seq miRNA expression levels"
    proposal = _proposal_of(N35, quote).model_copy(update={"s1": proposal_model(1).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
            "Build a PUMA network", [], regulator_kinds=["tf", "mirna"], scale="whole_cohort")]}}).s1})
    decision = TaskDecision(action="run_puma", in_scope=True, should_execute=True, confidence=0.9,
                            reason="r", capability_match_status="exact", matched_actions=["run_puma"])
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, shown, usage, warnings, situation: (["all"] * len(shown), usage, warnings))
    monkeypatch.setattr(router_invocation, "reread_passages", lambda *args: [])
    for answer, verdict in ((None, "unread"), ("violates", "partial_gap"), ("satisfies", "agrees")):
        seen = []
        def condition_check(context, state, shown, usage, warnings):
            seen.extend(shown)
            return ([answer] * len(shown) if answer else None), usage, warnings
        monkeypatch.setattr(router_invocation, "request_condition_check", condition_check)
        invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                         budget_warnings=[], reason_code=None)
        result = router_invocation._with_run_check(SimpleNamespace(project_policy=None), {}, N35, invocation, proposal, "ok")
        assert any(quote == row[1] for row in seen)
        assert result.decision.run_verdict.verdict == verdict
