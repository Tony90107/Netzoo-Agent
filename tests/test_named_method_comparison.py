"""A request that names two methods and no result is answered by comparing those two (2026-11-16).

"What is the difference between PANDA and LIONESS-PANDA?" was read purpose_only. The choice rule only knew a choice
written with "or", so the turn fell back to listing all fourteen workflows and asking which result was wanted. The
core decision spec, section 5, already said such a request "may compare the named options, but must end by asking
the goal"; these tests hold the reply to that.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.core_decision import ClarifyNeed, CoreDecision  # noqa: E402
from netzoo_agent_core.interpretation.clarify_goal import clarify_reply, named_comparison  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402
from netzoo_agent_core.interpretation.goal_evidence import method_choice  # noqa: E402

COMPARE = "What is the difference between PANDA and LIONESS-PANDA? I only need a simple comparison."


def _purpose_only(task: str, quote: str) -> tuple[CapabilityCheck, TaskDecision]:
    """The reading the live run gave: purpose only, one result row nothing delivers, a full gap."""
    check = CapabilityCheck(goal="purpose_only", goal_quote=quote, full_gap=True, requirements=[
        CheckedRequirement(quote=quote, kind="result", status="not_available")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            intent_type="answer_question", capability_check=check)
    return check, decision


def test_two_methods_named_in_a_purpose_only_goal_are_the_choice_without_an_or():
    check, decision = _purpose_only(COMPARE, COMPARE.split("?")[0] + "?")
    assert method_choice(check, decision, COMPARE) == ["PANDA", "LIONESS-PANDA"]


def test_the_turn_still_ends_on_the_goal_but_only_between_the_named_methods():
    check, decision = _purpose_only(COMPARE, COMPARE.split("?")[0] + "?")
    core = decide_core(decision, COMPARE)
    assert core.kind == "CLARIFY" and core.basis == "goal_unclear"
    assert core.clarify.candidates == ["PANDA", "LIONESS-PANDA"]
    assert "aggregate or sample-specific" in core.clarify.question


def test_a_method_used_as_the_input_source_is_not_a_choice():
    """Saved readings: "Run CONDOR on the PANDA network ..." was read method_named with nothing found. PANDA names
    where the input came from; reading it as a choice between CONDOR and PANDA would answer the wrong question."""
    quote = "Run CONDOR on the PANDA network /data/porc/lioness_panda_network.txt."
    check = CapabilityCheck(goal="method_named", goal_quote=quote, full_gap=True,
                            requirements=[CheckedRequirement(quote=quote, kind="result", status="not_available")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            capability_check=check)
    assert method_choice(check, decision, quote) == []


@pytest.mark.parametrize("goal", ["result_named", "method_named"])
def test_other_readings_keep_the_or_test(goal):
    """Two methods joined by "and" in a goal that names a result are steps or a composition, not a choice."""
    task = "Run PANDA and LIONESS-PANDA on data/study."
    check = CapabilityCheck(goal=goal, goal_quote=task, requirements=[
        CheckedRequirement(quote=task, kind="result", status="not_available")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            capability_check=check)
    assert method_choice(check, decision, task) == []


def test_one_named_method_is_not_a_comparison():
    quote = "What does PANDA do?"
    check, decision = _purpose_only(quote, quote)
    assert method_choice(check, decision, quote) == []


def _clarify(candidates, quote, question="Should the result be aggregate or sample-specific?"):
    return CoreDecision(kind="CLARIFY", basis="goal_unclear", clarify=ClarifyNeed(
        missing="result", candidates=candidates, question=question, goal_quote=quote))


def test_the_reply_compares_only_the_named_methods_then_asks():
    reply = clarify_reply(_clarify(["PANDA", "LIONESS-PANDA"], COMPARE.split("?")[0] + "?"),
                          COMPARE + " We have 40 tumour samples.")
    assert reply.startswith("How PANDA and LIONESS-PANDA differ:")
    assert "- PANDA: One weighted TF-to-gene regulatory network across all the samples given." in reply
    assert "- LIONESS-PANDA: One TF-gene network per sample, plus the aggregate network." in reply
    assert reply.count("Needs expression matrix, motif/prior and PPI network.") == 2
    assert "41 PANDA runs" in reply, "the cost note uses the request's own sample count"
    assert reply.index("differ:") < reply.index("To pick one for your study: Should the result be aggregate")
    for absent in ("I can't tell yet", "PUMA", "OTTER", "CONDOR"):
        assert absent not in reply


def test_a_broad_request_still_lists_what_the_workflows_give():
    need = _clarify(["PANDA", "PUMA", "CONDOR"], "I want to understand regulation in my tumours.",
                    question="Which of these results do you want?")
    assert named_comparison(need.clarify) == []
    assert clarify_reply(need).startswith("I can't tell yet which result you want")


def test_the_card_headline_names_the_comparison():
    from netzoo_agent_core.reply_cards.builder import _core_card

    quote = COMPARE.split("?")[0] + "?"
    core = _clarify(["PANDA", "LIONESS-PANDA"], quote)
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            clarification_question=core.clarify.question, core=core)
    card = _core_card("clarify_goal", decision, None, COMPARE)
    assert card.headline == "How PANDA and LIONESS-PANDA differ, and the question that picks one."


# -- methods that give the same result: told apart by how they fit it (2026-11-16) ---------------------------------


def test_two_methods_with_the_same_result_are_the_choice_in_a_purpose_only_goal():
    quote = "PANDA or OTTER: which one should I use?"
    check, decision = _purpose_only(quote, quote)
    assert method_choice(check, decision, quote) == ["PANDA", "OTTER"]
    core = decide_core(decision, quote)
    assert core.clarify.candidates == ["PANDA", "OTTER"]
    assert core.clarify.question.startswith("Both fit; to choose, tell me:")
    assert "(yes → OTTER)" in core.clarify.question and "(yes → PANDA)" in core.clarify.question


def test_the_same_result_set_against_each_other_with_or_is_a_choice_in_any_reading():
    """Live 2026-11-16: the same words were read purpose_only twice and method_named once (a result row, a full gap).
    The "or" sets the two methods against each other whatever the reading."""
    quote = "PANDA or OTTER: which one should I use?"
    check = CapabilityCheck(goal="method_named", goal_quote=quote, full_gap=True, requirements=[
        CheckedRequirement(quote=quote, kind="result", status="not_available")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            capability_check=check)
    assert method_choice(check, decision, quote) == ["PANDA", "OTTER"]


def test_the_comparison_says_how_each_method_works():
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    quote = "PANDA or OTTER: which one should I use?"
    core = _clarify(["PANDA", "OTTER"], quote, question=_choice_question(["run_panda", "run_otter"]))
    reply = clarify_reply(core, quote)
    assert "- PANDA: One weighted TF-to-gene regulatory network" in reply
    assert "How it works: Message passing iteratively reconciles a regulator-target prior" in reply
    assert "How it works: OTTER optimizes a TF-gene matrix W" in reply
    assert "To pick one for your study: Both fit; to choose, tell me: (1) Is the network large enough" in reply
    assert "Which of these results" not in reply


def test_three_methods_are_asked_by_the_conditions_the_tie_replies_use():
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    question = _choice_question(["run_panda", "run_otter", "run_giraffe"])
    assert question.startswith("These all fit; to choose, tell me:")
    assert "(yes → GIRAFFE)" in question and "If none of these applies: PANDA." in question


@pytest.mark.parametrize("actions, expected", [
    (["run_panda", "run_lioness_panda"], "Should the result be aggregate or sample-specific?"),
    (["run_cobra", "run_condor"], "Which of these results do you want?"),
])
def test_scale_comes_first_and_unrelated_results_are_asked_as_results(actions, expected):
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    assert _choice_question(actions) == expected


@pytest.mark.parametrize("actions", [
    ["run_dragon", "run_puma"], ["run_panda", "run_cobra"], ["run_cobra", "run_bonobo"],
    ["run_bonobo", "run_lioness_panda"], ["run_condor", "run_sambar"],
])
def test_methods_with_different_results_are_never_told_both_fit(actions):
    """The tie question says "Both fit" and names a default. Asked of DRAGON and PUMA it said "Both fit ... If none of
    these applies: DRAGON" -- a claim nothing checked. It is only for methods that differ in algorithm alone."""
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    question = _choice_question(actions)
    assert question == "Which of these results do you want?"
    assert "fit" not in question and "If none" not in question


def test_a_method_named_goal_with_only_a_question_about_the_methods_is_the_choice():
    """Live 2026-11-16: "How do PANDA, OTTER and GIRAFFE differ?" was read method_named with one about_methods row
    and no result row -- the reading goal_unclear treats as the choice between the methods named."""
    quote = "How do PANDA, OTTER and GIRAFFE differ?"
    check = CapabilityCheck(goal="method_named", goal_quote=quote, requirements=[
        CheckedRequirement(quote=quote, kind="about_methods", status="not_checked")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            capability_check=check)
    assert method_choice(check, decision, quote) == ["PANDA", "OTTER", "GIRAFFE"]
    core = decide_core(decision, quote)
    assert core.kind == "CLARIFY" and core.clarify.candidates == ["PANDA", "OTTER", "GIRAFFE"]
    assert core.clarify.question.startswith("These all fit; to choose, tell me:")


@pytest.mark.parametrize("quote", [
    "Run PANDA on /data/raw/cpm.tsv with motif /data/raw/motif.tsv and ppi /data/raw/ppi.tsv, then run CONDOR on the result.",
    "run CONDOR on panda_lung_edges.csv; it's my PANDA TF-to-gene network, already thresholded so every weight is positive.",
])
def test_a_method_named_run_with_only_context_rows_is_not_a_choice(quote):
    """Saved readings, replayed: these runs were read method_named with only context rows. Taking any method_named
    goal without a result row as the choice turned them into "How CONDOR and PANDA differ"."""
    check = CapabilityCheck(goal="method_named", goal_quote=quote, requirements=[
        CheckedRequirement(quote=quote, kind="context", status="not_checked")])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            capability_check=check)
    assert method_choice(check, decision, quote) == []


# -- the thesis packages: a bare LIONESS, and single cells against bulk (2026-11-16) -------------------------------


@pytest.mark.parametrize("quote, expected", [
    ("What is the difference between PANDA and LIONESS?", ["PANDA", "LIONESS-PANDA"]),
    ("How is LIONESS different from SCORPION?", ["LIONESS-PANDA", "SCORPION"]),
    ("What is the difference between PORCUPINE and LIONESS?", ["PORCUPINE", "LIONESS-PANDA"]),
    ("Should I go with BONOBO or LIONESS?", ["BONOBO", "LIONESS-COEXPRESSION"]),
])
def test_a_bare_lioness_is_the_version_the_other_named_method_points_to(quote, expected):
    """Live: "PANDA and LIONESS" fell back to all fourteen workflows -- LIONESS names the family, no workflow."""
    check, decision = _purpose_only(quote, quote)
    assert method_choice(check, decision, quote) == expected
    core = decide_core(decision, quote)
    assert core.clarify.candidates == expected
    assert clarify_reply(core, quote).startswith(f"How {expected[0]} and {expected[1]} differ:")


def test_lioness_is_left_out_when_no_single_version_fits():
    from netzoo_agent_core.interpretation.goal_evidence import compared_workflows

    assert compared_workflows("What does LIONESS do?") == []
    # miRNAs named: LIONESS-PANDA and LIONESS-PUMA both give a regulatory network like SCORPION's -- no guess.
    assert compared_workflows("SCORPION or LIONESS, with miRNAs in the prior?") == ["SCORPION"]


@pytest.mark.parametrize("actions, cells, bulk", [
    (["run_panda", "run_scorpion"], "SCORPION", "PANDA"),
    (["run_lioness_panda", "run_scorpion"], "SCORPION", "LIONESS-PANDA"),
])
def test_single_cell_against_bulk_is_asked_by_the_data(actions, cells, bulk):
    """Live: PANDA and SCORPION were asked "aggregate or sample-specific?" -- SCORPION also gives a network per cell
    group, but what tells them apart is single cells against bulk samples."""
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    question = _choice_question(actions)
    assert question == (f"Is your expression data from single cells or from bulk samples? (single cells → {cells}; "
                        f"bulk samples → {bulk})")


def test_a_method_that_takes_networks_is_never_the_bulk_answer():
    from netzoo_agent_core.interpretation.core_decision import _choice_question

    assert _choice_question(["run_scorpion", "run_porcupine"]) == "Which of these results do you want?"
