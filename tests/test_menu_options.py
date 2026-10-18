"""Options-first decision (the user's decision, 2026-10-18): two kinds of cannot-fill, CLARIFY only on evidence, the
result asked beside the doubts read, the options card, and settings only from the candidates' controls.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.menu_reading import (  # noqa: E402
    Count, MenuReading, Requirement, Said, SettingAsked, Wanted,
)
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.judgment_defaults import judgment_defaults  # noqa: E402

TABLE = judgment_defaults()
PRIORS = ["expression", "motif_prior", "ppi"]


def said(value: str, quote: str = "") -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote or value])


def doubt(*values, quote="not sure") -> Said:
    return Said(status="conflicting", values=list(values), quotes=[quote])


# --- two kinds of cannot-fill --------------------------------------------------------------------------------------

def test_what_the_user_did_not_say_is_never_a_refusal():
    for data in ([], ["expression"], PRIORS, ["expression", "methylation"]):
        decision = decide_menu(MenuReading(wanted=[Wanted(quote="help with our samples")], data=data))
        assert decision.kind in ("ASK", "CLARIFY") and decision.options and not decision.declined


def test_a_contract_violation_says_why_in_the_contracts_words_and_gives_the_nearest_option():
    task = "We want a TF-gene network for each of our 3,000 single cells."
    reading = MenuReading(wanted=[Wanted(quote="a TF-gene network for each of our 3,000 single cells",
                                         artifact=said("regulatory_network"), granularity=said("per_sample"),
                                         regulators=said("tf"))],
                          conditions={"data_unit": said("single_cells", "single cells")}, data=PRIORS)
    decision = decide_menu(reading, task)
    assert decision.kind == "DECLINE" and not decision.options
    lioness = next(x for x in decision.infeasible if x.workflow == "LIONESS-PANDA")
    assert "data_unit=single_cells" in lioness.reasons
    assert any("Built for bulk samples" in words for words in lioness.contract)
    nearest = {o.workflow: o for o in decision.nearest}
    assert "LIONESS-PANDA" in nearest and any("single cells" in line for line in nearest["LIONESS-PANDA"].to_confirm)


def test_a_near_miss_gives_its_registered_alternative():
    task = "Run OTTER to get one network per patient."
    reading = MenuReading(wanted=[Wanted(quote="one network per patient", granularity=said("per_sample"))],
                          data=PRIORS)
    decision = decide_menu(reading, task)
    assert decision.kind == "DECLINE"
    assert [o.workflow for o in decision.nearest] == ["LIONESS-PANDA"]
    assert any("One network per sample" in words for x in decision.infeasible for words in x.contract)


def test_an_out_of_range_setting_is_infeasible_and_never_an_option():
    task = "Run OTTER with lam 3.0."
    reading = MenuReading(wanted=[Wanted(quote="Run OTTER")], data=PRIORS,
                          settings=[SettingAsked(quote="lam 3.0", workflow="OTTER", control="lam", value="3.0")])
    decision = decide_menu(reading, task)
    assert decision.kind == "DECLINE" and not decision.options
    assert any("lam must be between 0 and 1" in r for x in decision.infeasible for r in x.reasons)


# --- CLARIFY only on evidence; the result beside the doubts read ---------------------------------------------------

def test_a_result_read_unsure_without_alternatives_is_inferred_and_the_real_doubt_asked():
    """h1 H13: CONDOR named, the network's kind unknown -- the result is CONDOR's, the doubt is what gets asked."""
    task = "Can CONDOR find modules in the network a collaborator emailed me?"
    reading = MenuReading(wanted=[Wanted(quote=task, artifact=Said(status="unsure", values=[], quotes=["modules"]))],
                          data=["regulator_gene_network"],
                          conditions={"input_network": doubt("regulator_gene", "gene_gene", quote="no idea whether")})
    decision = decide_menu(reading, task)
    assert decision.kind == "ASK" and [q.dimension for q in decision.questions] == ["input_network"]
    assert [o.workflow for o in decision.options] == ["CONDOR"]


def test_the_result_and_a_doubt_read_are_asked_together():
    task = "We have expression, motifs and PPI for either 2 or 20 samples. What can we build?"
    reading = MenuReading(wanted=[Wanted(quote="What can we build?", form="question_to_us")], data=PRIORS,
                          sample_count=Count(status="conflicting", values=[2, 20], quotes=["either 2 or 20 samples"]))
    decision = decide_menu(reading, task)
    assert decision.kind == "CLARIFY" and decision.evidence == ["What can we build?"]
    assert [q.dimension for q in decision.questions][:2] in (["artifact", "sample_count"],
                                                            ["artifact_group", "sample_count"])


def test_a_generic_word_is_evidence_and_a_named_result_is_not():
    generic = MenuReading(wanted=[Wanted(quote="a network analysis", artifact=said("network", "a network analysis"))],
                          data=["expression"])
    decision = decide_menu(generic, "a network analysis")
    assert decision.kind == "CLARIFY" and decision.evidence == ["a network analysis"]
    named = MenuReading(wanted=[Wanted(quote="a co-expression network", artifact=said("coexpression_network"))],
                        data=["expression"])
    assert decide_menu(named, "a co-expression network").kind == "ASK"  # one per sample or not: options, no CLARIFY


# --- the options card ----------------------------------------------------------------------------------------------

def test_a_tie_is_do_with_ranked_options_and_their_lines():
    reading = MenuReading(wanted=[Wanted(quote="one TF-gene network for the whole cohort", artifact=said(
        "regulatory_network"), granularity=said("whole_cohort"), regulators=said("tf"))], data=PRIORS)
    decision = decide_menu(reading, "one TF-gene network for the whole cohort")
    assert decision.kind == "DO" and len(decision.options) <= TABLE.ask_max_options
    assert [o.workflow for o in decision.options][:2] == ["PANDA", "OTTER"]  # the tie order
    panda = decision.options[0]
    assert panda.difference.startswith("The standard NetZoo network") and panda.good_for
    assert panda.matched == panda.relevant > 0 and "you have expression" in panda.fits


def test_options_rank_by_the_share_of_the_users_points_met():
    reading = MenuReading(wanted=[Wanted(
        quote="a gene co-expression network for each of our 9 biopsies", artifact=said("coexpression_network"),
        granularity=said("per_sample"),
        requirements=[Requirement(quote="a p-value for every edge",
                                  verdicts={"BONOBO": "met", "LIONESS-COEXPRESSION": "not_addressed"})])],
        data=["expression"])
    decision = decide_menu(reading, "co-expression per biopsy with a p-value for every edge")
    assert decision.options[0].workflow == "BONOBO"
    assert decision.options[0].matched == decision.options[0].relevant


def test_one_option_left_and_everything_confirmed_is_do():
    reading = MenuReading(wanted=[Wanted(quote="Run SAMBAR")], data=["mutation_calls"], run_requested=True)
    decision = decide_menu(reading, "Run SAMBAR on mut.csv")
    assert decision.kind == "DO" and [o.workflow for o in decision.options] == ["SAMBAR"] and decision.run_ready


# --- settings only from the candidates' controls -------------------------------------------------------------------

def test_words_read_as_another_workflows_control_are_no_setting():
    """h1 H23, H45: "header present" read as PANDA's with_header, an output folder as output_format."""
    bonobo = MenuReading(wanted=[Wanted(quote="Run BONOBO")], data=["expression"], settings=[
        SettingAsked(quote="header present", workflow="BONOBO", control="with_header", value="true"),
        SettingAsked(quote="log-transformed", workflow="BONOBO", control="log_transformed", value="true"),
        SettingAsked(quote="centered", workflow="BONOBO", control="centered", value="true")])
    assert decide_menu(bonobo, "Run BONOBO on core_expr.tsv").kind == "DO"
    sambar = MenuReading(wanted=[Wanted(quote="Run SAMBAR")], data=["mutation_calls"], settings=[
        SettingAsked(quote="put everything in sambar_uterine/", workflow="SAMBAR", control="output_format", value="")])
    assert decide_menu(sambar, "Run SAMBAR on mut.csv").kind == "DO"
    giraffe = MenuReading(wanted=[Wanted(quote="Run GIRAFFE")], data=PRIORS, settings=[
        SettingAsked(quote="a learning rate of 0.001", workflow="GIRAFFE", control="unregistered", value="0.001")])
    assert decide_menu(giraffe, "Run GIRAFFE with a learning rate of 0.001").kind == "DECLINE"
