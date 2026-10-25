"""ROUND-27 C1: the data-item judgment (interpretation.data_items) -- code's rules A and B, never a refusal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.interpretation.data_items import (  # noqa: E402
    DataItem, DataItemsRead, asked_core, data_item_findings, takes,
)


def item(quote, content, made_by="outside", certainty="stated", contents=(), makers=()):
    return DataItem(quote=quote, content=content, made_by=made_by, certainty=certainty,
                    content_alternatives=list(contents), made_by_alternatives=list(makers))


def read(*items):
    return DataItemsRead(items=list(items))


def test_takes_follows_input_artifacts_and_handoffs():
    assert takes("LIONESS-PANDA", "expression", "outside") is True
    assert takes("LIONESS-PANDA", "coexpression_matrix", "COBRA") is False
    assert takes("PANDA", "coexpression_matrix", "COBRA") is True  # COBRA hands off to run_panda
    assert takes("PANDA", "coexpression_matrix", "BONOBO") is False  # BONOBO has no handoff targets
    assert takes("CONDOR", "regulator_gene_network", "PANDA") is True
    assert takes("SAMBAR", "expression", "outside") is False
    assert takes("PANDA", "tf_gene_prior", "outside") is None  # priors are never judged


def test_rule_a_cobra_matrix_to_lioness_panda():
    task = ("Run LIONESS-PANDA now using cobra_out/adjusted_coexpression.tsv as the input together with "
            "motif_hs.tsv and ppi_hs.tsv.")
    found = data_item_findings(task, read(
        item("cobra_out/adjusted_coexpression.tsv", "coexpression_matrix", "COBRA"),
        item("motif_hs.tsv", "tf_gene_prior"), item("ppi_hs.tsv", "protein_interactions")), ["LIONESS-PANDA"])
    assert [f.rule for f in found] == ["A"]
    assert "made by COBRA" in found[0].question and "gene-by-sample expression table" in found[0].question
    assert found[0].question.endswith("?") is False and "?" in found[0].question


def test_no_finding_when_one_stated_main_input_fits():
    task = "Run PANDA on expr.tsv with motif.txt and ppi.txt, and use the COBRA adjusted_coexpression.tsv too."
    found = data_item_findings(task, read(
        item("expr.tsv", "expression"), item("adjusted_coexpression.tsv", "coexpression_matrix", "COBRA")), ["PANDA"])
    assert found == []


def test_rule_a_expression_only_for_condor_and_sambar():
    task = "I only have bulk RNA-seq from 200 tumours."
    one = read(item("bulk RNA-seq from 200 tumours", "expression"))
    assert [f.workflow for f in data_item_findings(task, one, ["CONDOR", "SAMBAR"])] == ["CONDOR", "SAMBAR"]


def test_not_stated_and_priors_change_nothing():
    task = "Run PANDA on my file with the motif prior."
    found = data_item_findings(task, read(item("my file", "not_stated"), item("the motif prior", "tf_gene_prior")),
                               ["PANDA"])
    assert found == []


def test_rule_b_unsure_alternatives_that_split_the_workflow():
    task = "Run PANDA on tumour_profiles_v2.tsv; I'm not sure if it holds expression or mutation calls."
    found = data_item_findings(task, read(item("tumour_profiles_v2.tsv", "expression", certainty="unsure",
                                               contents=("expression", "somatic_mutation"))), ["PANDA"])
    assert [f.rule for f in found] == ["B"]
    # alternatives that both fit (or both fail) ask nothing
    same = read(item("tumour_profiles_v2.tsv", "expression", certainty="unsure",
                     contents=("expression", "coexpression_matrix")))  # PANDA takes both
    assert data_item_findings(task, same, ["PANDA"]) == []


def test_unsure_with_one_alternative_judges_nothing():
    task = "Run PANDA on tumour_profiles_v2.tsv."
    one = read(item("tumour_profiles_v2.tsv", "somatic_mutation", certainty="unsure"))
    assert data_item_findings(task, one, ["PANDA"]) == []


def test_quote_not_in_request_is_dropped():
    task = "Run LIONESS-PANDA on the matrix."
    found = data_item_findings(task, read(item("adjusted_coexpression.tsv", "coexpression_matrix", "COBRA")),
                               ["LIONESS-PANDA"])
    assert found == []


def test_asked_core_only_changes_a_do_into_an_ask():
    task = "Run SAMBAR on expr.tsv."
    found = data_item_findings(task, read(item("expr.tsv", "expression")), ["SAMBAR"])
    do = CoreDecision(kind="DO", basis="run", workflows=["SAMBAR"], run_allowed=True)
    asked = asked_core(do, found)
    assert asked.kind == "ASK" and asked.basis == "data_item_fact" and asked.facts[0].user_quote == "expr.tsv"
    declined = CoreDecision(kind="DECLINE", basis="x", workflows=["SAMBAR"])
    assert asked_core(declined, found) is declined
    assert asked_core(do, []) is do


def test_with_core_stops_execution_for_the_data_item_ask():
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import with_core
    core = CoreDecision(kind="ASK", basis="data_item_fact", workflows=["SAMBAR"])
    decision = TaskDecision.model_construct(should_execute=True, execution_requested=True, action="run_sambar")
    out = with_core(decision, core)
    assert out.should_execute is False and out.action == "no_tool"


def test_flag_off_leaves_the_call(monkeypatch):
    from netzoo_agent_core.graph.data_items_call import apply_data_items
    monkeypatch.delenv("NETZOO_DATA_ITEMS", raising=False)
    do = CoreDecision(kind="DO", basis="run", workflows=["SAMBAR"])
    assert apply_data_items(None, {}, do, "Run SAMBAR on expr.tsv.", None, [])[0] is do
