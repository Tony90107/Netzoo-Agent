"""Options-first decision, step 6: the English reply built from the options card alone (no model at reply time)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.menu_reading import Count, MenuReading, Said, SettingAsked, Wanted  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_reply import FREE_TEXT, render_menu_reply  # noqa: E402
from netzoo_agent_core.method_names import registered_workflows, workflows_in  # noqa: E402

PRIORS = ["expression", "motif_prior", "ppi"]
CJK = re.compile(r"[一-鿿]")


def said(value: str, quote: str = "") -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote or value])


def grounded(text: str, decision) -> None:
    """Every workflow the reply names is one the decision offers, refuses or proposes instead, or one the contract's
    own option lines name (tie_options mention follow-ups such as LIONESS-PANDA); English only."""
    options = (*decision.options, *decision.nearest)
    allowed = {o.workflow for o in options} | {x.workflow for x in decision.infeasible} | set(decision.workflows) \
        | {name for o in options for name in workflows_in(f"{o.difference} {o.good_for}")}
    assert set(workflows_in(text)) & set(registered_workflows()) <= allowed, workflows_in(text)
    assert not CJK.search(text) and FREE_TEXT in text


def test_a_refusal_says_netzoo_cannot_with_the_contract_words_and_the_nearest_options():
    reading = MenuReading(wanted=[Wanted(quote="a TF-gene network for each single cell",
                                         artifact=said("regulatory_network"), granularity=said("per_sample"),
                                         regulators=said("tf"))],
                          conditions={"data_unit": said("single_cells", "single cells")}, data=PRIORS)
    decision = decide_menu(reading, "a TF-gene network for each single cell")
    text = render_menu_reply(decision)
    assert "NetZoo cannot run LIONESS-PANDA for this because the request says data unit: single cells." in text
    assert 'The contract says: "Networks for individual cells. -- Built for bulk samples' in text
    assert "The nearest options NetZoo can run:" in text and "leaves out data unit: single cells" in text
    grounded(text, decision)


def test_an_off_menu_result_says_no_registered_workflow_gives_it():
    reading = MenuReading(wanted=[Wanted(quote="a filtered VCF", artifact=said("off_menu", "a filtered VCF"),
                                         outside_name="a filtered VCF")])
    text = render_menu_reply(decide_menu(reading, "Give me a filtered VCF"))
    assert 'NetZoo cannot do "a filtered VCF": not a registered result: a filtered VCF.' in text
    assert "No registered workflow gives this." in text


def test_a_tie_lists_the_options_with_their_lines_and_waits_for_approval():
    reading = MenuReading(wanted=[Wanted(quote="one TF-gene network for the whole cohort", artifact=said(
        "regulatory_network"), granularity=said("whole_cohort"), regulators=said("tf"))], data=PRIORS)
    decision = decide_menu(reading, "one TF-gene network for the whole cohort")
    text = render_menu_reply(decision)
    assert "please choose one:" in text and "1. PANDA -- A weighted regulator-to-gene network" in text
    assert "How it differs: The standard NetZoo network" in text and "Good for: " in text
    assert "Matches 6 of the 6 points you gave" in text and "Nothing runs until you approve it." in text
    grounded(text, decision)


def test_a_question_lists_the_options_and_asks_with_not_sure_and_none_of_these():
    task = "Can CONDOR find modules in the network a collaborator emailed me?"
    reading = MenuReading(wanted=[Wanted(quote=task)], data=["regulator_gene_network"], conditions={
        "input_network": Said(status="conflicting", values=["regulator_gene", "gene_gene"],
                              quotes=["no idea whether it is TF-to-gene or gene-gene"])})
    decision = decide_menu(reading, task)
    text = render_menu_reply(decision)
    assert "The options that fit what you said so far:\n1. CONDOR" in text
    assert "Which is right about the input network?" in text and "  - Gene-gene edges (for example co-expression)" in text
    assert '(You wrote: "no idea whether it is TF-to-gene or gene-gene")' in text
    assert "  - Not sure -- suggest one" in text and "  - None of these (please describe)" in text
    grounded(text, decision)


def test_an_unclear_goal_quotes_the_words_that_make_it_unclear():
    task = "What can we build? We have expression, motifs and PPI for either 2 or 20 samples."
    reading = MenuReading(wanted=[Wanted(quote="What can we build?", form="question_to_us")], data=PRIORS,
                          sample_count=Count(status="conflicting", values=[2, 20], quotes=["either 2 or 20 samples"]))
    decision = decide_menu(reading, task)
    text = render_menu_reply(decision)
    assert text.startswith('You wrote "What can we build?", which does not yet say what result you want.')
    assert "How many samples are there?" in text
    grounded(text, decision)


def test_an_unsupported_setting_is_refused_in_the_contracts_words():
    reading = MenuReading(wanted=[Wanted(quote="Run GIRAFFE")], data=PRIORS, settings=[
        SettingAsked(quote="a learning rate of 0.001", workflow="GIRAFFE", control="unregistered", value="0.001")])
    text = render_menu_reply(decide_menu(reading, "Run GIRAFFE with a learning rate of 0.001"))
    assert "NetZoo cannot run GIRAFFE for this because NetZoo runs GIRAFFE with its package defaults" in text


def test_an_unchecked_reading_says_so_and_offers_nothing():
    text = render_menu_reply(decide_menu(MenuReading(status="failed")))
    assert "could not check" in text and not workflows_in(text)
