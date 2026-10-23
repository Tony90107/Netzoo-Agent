"""ROUND-09 (collab/ROUND-09-PLAN.md): a sample count given as candidates is weighed even when the reading scoped it
to no asked result, and the fact agent cannot ask about words whose candidates code already weighed.

Live attempt-03 (gpt-4o-mini check): T03 "either 2 or 14 samples" and T01 "either nine or seventeen patients" were
read as unknown sample counts with `applies_to` [] and dropped, so 2-or-14 planned a LIONESS-PANDA run and
9-or-17 asked "Do you have at least three expression samples?" -- a question both candidates answer yes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402
from test_request_facts import _check  # noqa: E402

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.core_decision import FactQuestion  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402

ASK = "Build a TF-to-gene network for each sample"


def _single(values, *, about="sample_count", applies_to=()):
    words = f"either {' or '.join(map(str, values))} samples"
    task = f"{ASK}. The export has {words}; I do not know which."
    ask = _ask(ASK, ["lioness_panda.per_sample_networks"], scale="per_sample", regulator_kinds=["tf"])
    return task, words, _check(task, ask, unknown_facts=[{
        "about": about, "quote": words, "count_kind": "choices", "count_values": list(values),
        "applies_to": list(applies_to)}])


def _decision(check, *questions):
    accepted = [FactQuestion(question=text, user_quote=quote, workflows=["LIONESS-PANDA"],
                             contract_quote="Require at least three expression samples", uncertainty="two_versions",
                             if_yes="supported", if_no="not_supported") for text, quote in questions]
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, execution_requested=False,
                        confidence=0.9, reason="guidance", capability_check=check,
                        fact_check=FactCheck(status="checked", accepted=accepted))


def test_a_deciding_candidate_count_scoped_to_no_result_is_still_weighed():
    task, words, check = _single([2, 14])
    (row,) = check.results()
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "sample_count", True)
    assert row.outcomes == {"2": [], "14": ["lioness_panda.per_sample_networks"]}
    assert [c.reason for c in check.fact_conflicts] == ["empty_scope_kept"]
    core = decide_core(_decision(check, ("Do you have at least 3 samples?", words)), task)
    assert core.kind == "ASK" and core.basis == "count_fact"
    assert [fact.question for fact in core.facts] != ["Do you have at least 3 samples?"]  # code's own question


def test_candidates_that_all_fit_ask_nothing_even_when_the_agent_would():
    task, words, check = _single([9, 17])
    (row,) = check.results()
    assert row.status == "available" and not row.depends_on
    core = decide_core(_decision(check, ("Do you have at least three expression samples?", words)), task)
    assert core.kind == "DO"
    assert core.evidence["count_owned"] == ["Do you have at least three expression samples?"]


def test_candidates_that_all_fail_rule_the_result_out():
    task, words, check = _single([1, 2])
    (row,) = check.results()
    assert row.status == "not_available"
    assert decide_core(_decision(check, ("Do you have at least three samples?", words)), task).kind == "DECLINE"


def test_an_agent_question_on_other_words_is_still_asked():
    task, _words, check = _single([9, 17])
    core = decide_core(_decision(check, ("Is the expression already normalised?", "I do not know which")), task)
    assert core.kind == "ASK" and [f.question for f in core.facts] == ["Is the expression already normalised?"]


def test_other_unknowns_scoped_to_no_result_are_still_dropped():
    _task, _words, check = _single([9, 17], about="omics_layers")
    assert check.unknowns == [] and not check.fact_conflicts


def test_a_question_naming_one_candidate_is_kept_though_code_found_both_fit():
    """h2 J22: SAMBAR "2 to 6 subtypes" for 5 or 9 tumours -- the reading missed kmax 6, so code found both fit;
    the agent's "Will the final number of samples be 5?" tells the candidates apart and is still asked."""
    task, words, check = _single([5, 9])
    core = decide_core(_decision(check, ("Will the final number of samples be 5?", words)), task)
    assert core.kind == "ASK" and "count_owned" not in core.evidence


def test_splits_candidates_reads_only_the_numbers_a_question_states():
    from netzoo_agent_core.interpretation.count_alternatives import splits_candidates

    assert not splits_candidates("Do you have at least three expression samples?", [9, 17])
    assert splits_candidates("Do you have at least three expression samples?", [2, 14])
    assert splits_candidates("Will it end up as 9?", [5, 9])
    assert splits_candidates("Is the export already filtered?", [9, 17])  # no number: cannot judge, kept


def _waiting(quote, unknown, outcomes, notes=None):
    from netzoo_agent_core.contracts.capability_check import CheckedRequirement

    return CheckedRequirement(quote=quote, kind="result", status="needs_fact", depends_on="sample_count", by_code=True,
                              unknown_quote=unknown, outcomes=outcomes, outcome_notes=notes or {},
                              delivered_by=[k for keys in outcomes.values() for k in keys])


def test_one_count_question_when_two_results_wait_on_the_same_doubt():
    """Live attempt-04 T03: the first reading's result and the re-read's each waited on "2 or 14", asked twice."""
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck

    task = ("Could you start LIONESS-PANDA to build one TF-to-gene network per biological sample from pine_bulk.tsv? "
            "The export contains either 2 or 14 samples.")
    key = "lioness_panda.per_sample_networks"
    check = CapabilityCheck(requirements=[
        _waiting("one TF-to-gene network per biological sample", "either 2 or 14 samples", {"2": [], "14": [key]}),
        _waiting("Could you start LIONESS-PANDA", "2 or 14 samples", {"2": [], "14": [key]},
                 {"2": "LIONESS-PANDA needs at least 3 samples"})])
    core = decide_core(_decision(check), task)
    assert core.kind == "ASK" and [f.question for f in core.facts] == ["Which of these is right: 2 or 14?"]
    assert core.facts[0].notes == {"2": "LIONESS-PANDA needs at least 3 samples"}


def test_different_candidates_or_words_stay_separate_questions():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck

    task = "The confirmed set has either 2 or 14 samples. The archive set has either 2 or 6 samples."
    key = "lioness_panda.per_sample_networks"
    check = CapabilityCheck(requirements=[
        _waiting("The confirmed set", "either 2 or 14 samples", {"2": [], "14": [key]}),
        _waiting("The archive set", "either 2 or 6 samples", {"2": [], "6": [key]})])
    assert len(decide_core(_decision(check), task).facts) == 2
