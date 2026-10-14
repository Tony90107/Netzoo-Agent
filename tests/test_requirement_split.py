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
    assert combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmin", "kmin", "5")])  # default kmax 4
    assert combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=4)
    assert not combination_issues(conditions_for("SAMBAR"), [StatedSetting("SAMBAR.kmax", "kmax", "6")], samples=200)
    assert combination_issues(conditions_for("BONOBO"), [StatedSetting("BONOBO.sparsify", "sparsify", ""),
                                                         StatedSetting("BONOBO.delta", "delta", "0.5")])
    assert not combination_issues(conditions_for("BONOBO"), [StatedSetting("BONOBO.delta", "delta", "0.5")])
