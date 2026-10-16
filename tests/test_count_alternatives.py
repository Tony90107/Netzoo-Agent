"""Core decision spec, phase 5b (section 13.3): a count the request gives as candidates, judged in code.

Rounds p2-p4c C45: "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the
2,000-protein discovery panel" was asked about the data's format; the LIONESS-DRAGON size limit decides it, and code
can judge each candidate. m3 U06 ("whether 20 or 200 genes remain for the 40 samples") is COBRA's relation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_m3_method_fitting import _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.core_decision import FactQuestion  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import without_legacy_waits  # noqa: E402
from netzoo_agent_core.interpretation.ask_facts import ask_reply  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402
from netzoo_agent_core.interpretation.count_alternatives import verified_count_alternatives  # noqa: E402
from netzoo_agent_core.contracts.capability_check import unstated_conditions, conditions_model  # noqa: E402

TASK = ("We want a separate miRNA-protein partial-correlation network for each of our 50 patients, from 300 serum "
        "miRNAs and a plasma proteomics panel. I don't remember whether the proteomics is the 200-protein targeted "
        "panel or the 2,000-protein discovery panel.")
NETWORKS = "a separate miRNA-protein partial-correlation network for each of our 50 patients"
PANELS = "the 200-protein targeted panel or the 2,000-protein discovery panel"
KEY = "lioness_dragon.per_sample_networks"


def _networks(**extra):
    return _ask(NETWORKS, [KEY], samples=50, samples_quote="50 patients", omics_layers=2, scale="per_sample", **extra)


def _alternative(quote=PANELS, values=(200, 2000), of="features"):
    return {"of": of, "quote": quote, "values": list(values)}


def _decision(check, fact_check=None):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_check=check, fact_check=fact_check)


def test_a_candidate_count_whose_workflows_differ_waits_with_each_outcome_judged_in_code():
    assert [row.status for row in _check(TASK, _networks(features=[(300, "300 serum miRNAs")])).results()] == [
        "available"]  # as recorded: only the miRNAs are counted
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]), count_alternatives=[_alternative()])
    (row,) = check.results()
    assert (row.status, row.by_code, row.depends_on, row.unknown_quote) == ("needs_fact", True, "feature_count", PANELS)
    assert row.outcomes == {"200": [KEY], "2000": []}
    assert "at most 20,000,000 values" in row.outcome_notes["2000"] and "2,300 features" in row.outcome_notes["2000"]
    assert check.count_alternatives == [_alternative()]


def test_a_stated_count_inside_the_candidates_words_was_never_settled():
    """The reading may also type one candidate as stated; it is taken off before each candidate is judged."""
    ask = _networks(features=[(300, "300 serum miRNAs"), (2000, "2,000-protein")])
    assert _check(TASK, ask).results()[0].status == "not_available"  # 2,300 features read as stated
    (row,) = _check(TASK, ask, count_alternatives=[_alternative()]).results()
    assert row.status == "needs_fact" and row.outcomes == {"200": [KEY], "2000": []}
    assert row.method["features"] == 300 and row.method["feature_counts"] == 1


def test_a_relation_is_judged_on_the_one_candidate_count():
    """m3 U06: the 40 samples are inside the candidates' words too, and stay stated (they are not features)."""
    task = "Can COBRA analyze the midge experiment? I do not know whether 20 or 200 genes remain for the 40 samples."
    quote = "whether 20 or 200 genes remain for the 40 samples"
    ask = _ask("Can COBRA analyze the midge experiment", ["cobra.covariate_components"], samples=40,
               samples_quote="the 40 samples")
    (row,) = _check(task, ask, count_alternatives=[_alternative(quote, (20, 200))]).results()
    assert row.status == "needs_fact" and row.outcomes == {"20": [], "200": ["cobra.covariate_components"]}
    assert row.outcome_notes["20"].startswith("COBRA requires more genes than samples")


def test_every_candidate_ruling_the_result_out_is_a_gap_with_each_reason():
    task = TASK.replace("200-protein targeted", "5,000-protein untargeted")
    panels = "the 5,000-protein untargeted panel or the 2,000-protein discovery panel"
    check = _check(task, _networks(features=[(300, "300 serum miRNAs")]),
                   count_alternatives=[_alternative(panels, (5000, 2000))])
    (row,) = check.results()
    assert row.status == "not_available" and not row.by_code
    assert [limit.split(":")[0] for limit in row.limits] == ["with 2,000", "with 5,000"]
    assert decide_core(_decision(check)).kind == "DECLINE"


def test_candidates_that_change_nothing_are_not_asked():
    task = TASK.replace("2,000-protein discovery", "100-protein discovery")
    panels = "the 200-protein targeted panel or the 100-protein discovery panel"
    (row,) = _check(task, _networks(features=[(300, "300 serum miRNAs")]),
                    count_alternatives=[_alternative(panels, (200, 100))]).results()
    assert (row.status, row.by_code) == ("available", False)


def test_candidates_are_kept_only_with_their_words_and_every_number_in_them():
    model = conditions_model()

    def read(*alternatives):
        return verified_count_alternatives(TASK, type("P", (), {"conditions": model.model_validate(
            {**unstated_conditions(), "count_alternatives": list(alternatives)})})())

    assert [item["values"] for item in read(_alternative())] == [[200, 2000]]
    assert read(_alternative(values=(200, 3000))) == []  # 3,000 is not in the words
    assert read(_alternative(values=(200, 200))) == []  # one candidate is no choice
    assert read(_alternative(quote="200 versus 2,000 participants")) == []  # not the request's words


def test_with_several_results_a_count_applies_only_to_the_result_its_words_touch():
    task = TASK.replace("We want a separate", "We want an aggregate PANDA network and a separate")
    aggregate = _ask("an aggregate PANDA network", ["panda.tf_gene_network"], scale="whole_cohort",
                     regulator_kinds=["tf"])
    check = _check(task, aggregate, _networks(features=[(300, "300 serum miRNAs")]),
                   count_alternatives=[_alternative()])
    assert [row.by_code for row in check.results()] == [False, False]  # the panels are in another sentence


def _waiting_check():
    return _check(TASK, _networks(features=[(300, "300 serum miRNAs")]), count_alternatives=[_alternative()])


def test_the_code_judged_count_is_asked_first_and_the_agents_question_on_the_same_words_is_dropped():
    agent = FactQuestion(question="Do you have the proteomics data in the required format for LIONESS-DRAGON?",
                         user_quote="I don't remember whether the proteomics is the 200-protein targeted panel",
                         workflows=["LIONESS-DRAGON"], contract_quote="LIONESS-DRAGON")
    other = FactQuestion(question="Were the serum and plasma samples drawn on the same day?",
                         user_quote="a plasma proteomics panel", workflows=["LIONESS-DRAGON"], contract_quote="x")
    check = without_legacy_waits(_waiting_check())
    assert check.results()[0].status == "needs_fact"  # a code-judged wait is no legacy shadow
    core = decide_core(_decision(check, FactCheck(status="checked", accepted=[agent, other])), TASK)
    assert (core.kind, core.basis) == ("ASK", "count_fact")
    assert [fact.question for fact in core.facts] == ["Which of these is right: 200 or 2,000?", other.question]
    held = with_core(_decision(check), core)
    assert (held.action, held.matched_actions, held.should_execute) == ("no_tool", [], False)


def test_the_ask_reply_says_what_each_candidate_leads_to():
    core = decide_core(_decision(_waiting_check(), FactCheck(status="checked")))
    text = ask_reply(core)
    assert 'You wrote: "the 200-protein targeted panel or the 2,000-protein discovery panel"' in text
    assert "  - 200: LIONESS-DRAGON can do this\n" in text
    assert "  - 2,000: no registered workflow can do this as asked -- LIONESS-DRAGON writes at most 20,000,000" in text
    assert text.endswith("No files were inspected and no analysis ran.")


def test_without_the_agent_the_legacy_reply_says_the_count_and_its_outcomes():
    from netzoo_agent_core.interpretation.capability_check import understanding_paragraph

    check = _waiting_check()
    core = decide_core(_decision(check))
    assert (core.kind, core.basis) == ("ASK", "needs_fact")
    assert "depends on a number you gave candidates for" in understanding_paragraph(check)
