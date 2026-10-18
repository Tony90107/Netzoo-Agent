"""Closed-menu judgment phase 0: the decision table and ask loop (spec 2026-10-18, sections 3.2-3.4, 3.8-3.10).

Two kinds of test. A grid of readings -- every result value, scale, regulator and integration state, over four data
situations -- checked against invariants the spec states; and the cases the user decided, one by one.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.menu_reading import (  # noqa: E402
    Answer, Count, MenuReading, Requirement, Said, SettingAsked, Wanted,
)
from netzoo_agent_core.interpretation.menu_decision import apply_answers, decide_menu  # noqa: E402
from netzoo_agent_core.judgment_defaults import judgment_defaults  # noqa: E402

TABLE = judgment_defaults()


def said(value: str) -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[value])


def unsure(*values: str) -> Said:
    return Said(status="unsure", values=list(values), quotes=["not sure"])


ARTIFACTS = [*TABLE.dimensions["artifact"].values, "network", "regulation", None]
SCALES = [None, "whole_cohort", "per_group", "per_sample"]
REGULATORS = [None, "tf", "tf_mirna", "unsure"]
INTEGRATION = [None, "joint", "per_layer"]
DATA = [[], ["expression"], ["expression", "methylation"], ["expression", "methylation", "protein"]]


def reading(artifact, scale, regulators, integration, data, groups=()) -> MenuReading:
    wanted = Wanted(
        quote="the result",
        artifact=said(artifact) if artifact else Said(),
        granularity=said(scale) if scale else Said(),
        regulators=unsure("tf", "tf_mirna") if regulators == "unsure" else said(regulators) if regulators else Said(),
        integration=said(integration) if integration else Said())
    return MenuReading(wanted=[wanted], data=list(data), groups=list(groups))


GRID = list(itertools.product(ARTIFACTS, SCALES, REGULATORS, INTEGRATION, range(len(DATA))))


def _outcome(decision):
    return decision.kind, tuple(decision.workflows), tuple((q.dimension, tuple(v for v, _ in q.options))
                                                          for q in decision.questions)


@pytest.mark.parametrize("artifact, scale, regulators, integration, data", GRID[::7] + GRID[3::11])
def test_grid_invariants(artifact, scale, regulators, integration, data):
    read = reading(artifact, scale, regulators, integration, DATA[data])
    decision = decide_menu(read)
    # I1: a refusal always carries a positive reason, and no reading that states nothing is ever refused.
    if decision.kind == "DECLINE":
        assert decision.declined and all(part.reasons for part in decision.declined)
        assert any(value for value in (artifact, scale, regulators, integration))
    # I5: every workflow offered gives the result asked for.
    if decision.kind == "DO" and artifact and artifact not in TABLE.generic:
        for workflow in decision.workflows:
            assert any(TABLE.by_entry[key] == artifact for key, entry in sheet_entries().items()
                       if entry.kind == "produces" and entry.workflow == workflow), (workflow, artifact)
    # I6: several workflows for one result are a tie with its reasons written down.
    if decision.kind == "DO" and len(decision.workflows) > 1:
        assert decision.ties and all(tie.group for tie in decision.ties), decision.workflows
    # A question is never empty, and asks at most ask_max_options choices (one is a confirmation).
    for question in decision.questions:
        assert 1 <= len(question.options) <= max(TABLE.ask_max_options, 4)


def _walk(read, answers=(), depth=0, seen=None):
    """Every path of answers from a reading: (final decision, answers) at each leaf."""
    decision = decide_menu(read, answers=answers, rounds_asked=depth)
    if not decision.questions or depth > 6:
        yield decision, answers
        return
    question = decision.questions[0]
    for value, _label in question.options:
        yield from _walk(read, (*answers, Answer(item=question.item, dimension=question.dimension, value=value)),
                         depth + 1)


@pytest.mark.parametrize("data", range(len(DATA)))
def test_every_answer_path_ends_within_the_round_limit_and_every_option_matters(data):
    """I3 + I4: answering any option moves the call on, and every path ends in DO or DECLINE."""
    read = MenuReading(data=DATA[data])
    leaves = list(_walk(read))
    assert leaves
    for decision, answers in leaves:
        assert decision.kind in ("DO", "DECLINE"), (answers, decision.kind)
        intent_rounds = sum(1 for a in answers if a.dimension in ("artifact", "artifact_group"))
        assert len(answers) - intent_rounds <= TABLE.max_ask_rounds + 1
    first = decide_menu(read)
    for question in first.questions:
        outcomes = {_outcome(decide_menu(read, answers=[Answer(item=question.item, dimension=question.dimension,
                                                               value=value)]))
                    for value, _ in question.options}
        assert len(outcomes) == len(question.options), question.dimension


# --- The user's decisions, case by case -------------------------------------------------------------------------

def test_a_network_is_asked_one_or_per_sample():
    """Draft 3: "a network" says nothing about one versus many."""
    decision = decide_menu(reading("regulatory_network", None, None, None, ["expression", "motif_prior", "ppi"]))
    assert decision.kind == "ASK" and decision.questions[0].dimension == "granularity"


def test_two_layers_without_linking_words_ask_integrated_or_per_layer():
    decision = decide_menu(reading("network", "whole_cohort", None, None, ["expression", "methylation"]))
    assert decision.kind in ("ASK", "CLARIFY")
    assert any(q.dimension in ("integration", "artifact", "artifact_group") for q in decision.questions)


def test_linking_words_give_the_joint_network():
    decision = decide_menu(reading("multi_omic_network", "whole_cohort", None, "joint", ["expression", "methylation"]))
    assert (decision.kind, decision.workflows) == ("DO", ["DRAGON"])


def test_three_layers_ask_which_pair():
    decision = decide_menu(reading("multi_omic_network", "whole_cohort", None, "joint",
                                   ["expression", "methylation", "protein"]))
    assert decision.kind == "ASK" and decision.questions[0].dimension == "layers"
    assert len(decision.questions[0].options) == 3


def test_groups_add_the_per_group_choice():
    decision = decide_menu(reading("regulatory_network", None, "tf", None, ["expression"], groups=["AD", "controls"]))
    assert {value for value, _ in decision.questions[0].options} == {"whole_cohort", "per_group", "per_sample"}


def test_mirna_never_mentioned_is_tf_only_and_mentioned_is_asked():
    """Draft 4: an extra the user asks for (0/93 dev requests without a miRNA mention needed one)."""
    plain = decide_menu(reading("regulatory_network", "per_sample", None, None, ["expression"]))
    assert plain.workflows == ["LIONESS-PANDA"]
    asked = decide_menu(reading("regulatory_network", "per_sample", "unsure", None, ["expression"]))
    assert asked.kind == "ASK" and asked.questions[0].dimension == "regulators"


def test_a_tie_is_offered_with_the_option_that_fits_what_was_said():
    read = reading("regulatory_network", "whole_cohort", "tf", None, ["coexpression_matrix", "motif_prior", "ppi"])
    decision = decide_menu(read)
    assert decision.kind == "DO" and set(decision.workflows) == {"PANDA", "OTTER", "GIRAFFE"}
    assert decision.ties[0].group == "whole_cohort_tf_network" and decision.ties[0].fits == ["OTTER"]


def test_one_named_workflow_is_its_own_result():
    decision = decide_menu(MenuReading(run_requested=True), "Run PANDA on expr.tsv, motif.txt and ppi.txt")
    assert (decision.kind, decision.workflows, decision.run_ready) == ("DO", ["PANDA"], True)


def test_two_named_workflows_and_no_result_ask_the_result():
    decision = decide_menu(MenuReading(), "Should I use COBRA or CONDOR?")
    assert decision.kind == "CLARIFY"


def test_nothing_said_is_clarify_never_decline():
    for data in DATA:
        assert decide_menu(MenuReading(data=data)).kind == "CLARIFY"


def test_an_off_menu_result_needs_the_users_words_and_declines():
    read = MenuReading(wanted=[Wanted(quote="filtered VCF", artifact=said("off_menu"), outside_name="filtered VCF")])
    decision = decide_menu(read)
    assert decision.kind == "DECLINE" and "filtered VCF" in decision.declined[0].reasons[0]


@pytest.mark.parametrize("name", ["data_unit", "time_model", "spatial"])
def test_an_off_menu_condition_rules_out_every_workflow(name):
    from netzoo_agent_core.contracts.capability_check import CONDITIONS
    read = reading("coexpression_network", "per_sample", None, None, ["expression"])
    read = read.model_copy(update={"conditions": {name: said(CONDITIONS[name][1])}})
    assert decide_menu(read).kind == "DECLINE"


def test_an_unsure_condition_is_asked_only_when_it_decides():
    read = reading("coexpression_network", "per_sample", None, None, ["expression"])
    asked = decide_menu(read.model_copy(update={"conditions": {"data_unit": unsure("bulk_samples", "single_cells")}}))
    assert asked.kind == "ASK" and asked.questions[0].dimension == "data_unit"
    ignored = decide_menu(read.model_copy(update={"conditions": {"mutation_origin": unsure("somatic", "germline")}}))
    assert ignored.kind == "DO"


def test_one_failed_condition_vetoes_however_much_else_fits():
    """Draft 5: the 9/10 rule never applies to a FAIL (a24b: 9 of 11 false accepts were one condition off)."""
    read = reading("regulatory_network", "whole_cohort", "tf", None, ["expression", "motif_prior", "ppi"])
    read = read.model_copy(update={"settings": [SettingAsked(quote="an L1 penalty", workflow=w, control="unregistered")
                                                for w in ("PANDA", "OTTER", "GIRAFFE")]})
    assert decide_menu(read).kind == "DECLINE"


def test_a_setting_the_workflow_has_is_kept():
    read = reading("multi_omic_network", "whole_cohort", None, "joint", ["expression", "methylation"])
    read = read.model_copy(update={"settings": [SettingAsked(quote="as an edge list", workflow="DRAGON",
                                                             control="output_format", value="edge list")]})
    assert decide_menu(read).workflows == ["DRAGON"]


def test_counts_judged_now_and_an_unsure_count_asked_when_it_decides():
    base = reading("multi_omic_network", "per_sample", None, "joint", ["mirna_expression", "protein"])
    small = base.model_copy(update={"sample_count": Count(status="stated", value=2)})
    assert decide_menu(small).kind == "DECLINE"
    unsure_size = base.model_copy(update={"sample_count": Count(status="stated", value=50),
                                          "feature_count": Count(status="conflicting", values=[500, 2300])})
    decision = decide_menu(unsure_size)
    assert decision.kind == "ASK" and decision.questions[0].dimension == "feature_count"


def _with_requirements(met: int, open_: int) -> MenuReading:
    requirements = ([Requirement(quote=f"met {i}", verdicts={"DRAGON": "met"}) for i in range(met)]
                    + [Requirement(quote=f"open {i}", verdicts={"DRAGON": "not_addressed"}) for i in range(open_)])
    read = reading("multi_omic_network", "whole_cohort", None, "joint", ["expression", "methylation"])
    return read.model_copy(update={"wanted": [read.wanted[0].model_copy(update={"requirements": requirements})]})


def test_nine_of_ten_requirements_met_goes_ahead_and_lists_the_tenth():
    decision = decide_menu(_with_requirements(9, 1))
    assert decision.kind == "DO" and decision.unconfirmed == ["open 0"]


def test_fewer_than_nine_of_ten_asks_whether_the_rest_are_musts():
    decision = decide_menu(_with_requirements(8, 2))
    assert decision.kind == "ASK" and all(q.kind == "requirement" for q in decision.questions)
    answered = decide_menu(_with_requirements(8, 2), answers=[
        Answer(item=0, dimension="requirement:8", value="no"), Answer(item=0, dimension="requirement:9", value="no")])
    assert answered.kind == "DO"


def test_a_contradicted_requirement_rules_the_workflow_out():
    read = _with_requirements(1, 0)
    wanted = read.wanted[0]
    contradicted = wanted.model_copy(update={"requirements": [Requirement(quote="a convex solution",
                                                                           verdicts={"DRAGON": "contradicted"})]})
    assert decide_menu(read.model_copy(update={"wanted": [contradicted]})).kind == "DECLINE"


def test_answers_are_locked_as_answered():
    read = apply_answers(reading("regulatory_network", None, None, None, []),
                         [Answer(item=0, dimension="granularity", value="per_sample")])
    assert read.wanted[0].granularity.basis == "answered"


def test_a_failed_reading_is_unchecked():
    assert decide_menu(MenuReading(status="failed")).kind == "UNCHECKED"


def test_the_last_round_is_marked():
    decision = decide_menu(MenuReading(), rounds_asked=TABLE.max_ask_rounds)
    assert decision.final_round


def test_a_result_never_named_is_confirmed_even_when_the_data_leave_one():
    """Phase 0 missed-field check (C15, C26): the data alone never choose the result for the user."""
    decision = decide_menu(MenuReading(data=["mutation_calls"]))
    assert decision.kind == "CLARIFY" and decision.questions[0].options[0][0] == "patient_subtypes"


def test_mirna_data_is_a_mention_so_the_regulator_kind_is_asked():
    """Phase 0 missed-field check (C25, C59): a miRNA prior in the data makes an unstated regulator kind unclear."""
    decision = decide_menu(reading("regulatory_network", "whole_cohort", None, None,
                                   ["expression", "motif_prior", "ppi", "mirna_prior"]))
    assert decision.kind == "ASK" and decision.questions[0].dimension == "regulators"
