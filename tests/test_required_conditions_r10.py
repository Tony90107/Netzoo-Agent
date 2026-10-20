"""ROUND-10 (collab/ROUND-10-PLAN.md, shrunk after step 0): a quantity condition the request does not state is never
taken as met. Unread side-by-side candidates in context are weighed by code (live T02: "either one or two biological
samples" for LIONESS-PANDA, minimum three, is not available); an answer about whether a workflow can do it says each
unstated condition; DRAGON, GIRAFFE and COBRA state the minimum their preflight already enforces."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    apply_second_opinion, build_capability_check, request_sentences, second_opinion_pairs, understanding_paragraph,
)

ASK = "Can LIONESS-PANDA produce a TF-to-gene network per sample from these bulk RNA measurements"


def _check(task, ask, has=()):
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{i}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for i in range(1, len(sentences) + 1)}
    index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
    readings[f"s{index}"].update(role="asks", asks=[ask])
    for quote in has:
        where = next(i for i, text in enumerate(sentences, 1) if quote in text)
        readings[f"s{where}"]["has"].append(quote)
    readings["conditions"] = unstated_conditions()
    return build_capability_check(task, proposal_model(len(sentences)).model_validate(readings))[0]


def _panda():
    return _ask(ASK, ["lioness_panda.per_sample_networks"], scale="per_sample", regulator_kinds=["tf"])


@pytest.mark.parametrize("numbers, status", [("one or two", "not_available"), ("nine or seventeen", "available"),
                                             ("2 or 14", "needs_fact")])
def test_unread_candidates_in_context_are_weighed_by_code(numbers, status):
    context = f"The entire cohort consists of either {numbers} biological samples"
    check = _check(f"{context}; the manifest is unavailable. {ASK}?", _panda(), has=[context])
    (row,) = check.results()
    assert row.status == status
    assert [a["values"] for a in check.count_alternatives] == [sorted({"one or two": [1, 2],
                                                                      "nine or seventeen": [9, 17],
                                                                      "2 or 14": [2, 14]}[numbers])]
    if status == "not_available":
        assert row.limits[0].startswith("with 1: LIONESS-PANDA needs at least 3 samples")
        assert row.unknown_quote == context


def test_a_result_every_candidate_rules_out_is_not_asked_again_by_the_second_opinion():
    context = "The entire cohort consists of either one or two biological samples"
    check = _check(f"{context}. {ASK}?", _panda(), has=[context])
    assert check.full_gap
    assert second_opinion_pairs(check, ["run_lioness_panda"]) == []


@pytest.mark.parametrize("context", [
    "We sampled at baseline and at 24 hours in four extraction batches",
    "The protocol owner must confirm whether delta is 0.2 or 0.5",
    "We have 40 samples, 300 genes and 2 batches",
])
def test_no_candidate_run_no_new_doubt(context):
    check = _check(f"{context}. {ASK}?", _panda(), has=[context])
    assert check.count_alternatives == [] and check.results()[0].status == "available"


def test_an_answer_says_the_unstated_minimum_but_not_a_stated_or_weighed_one():
    plain = _check(f"We have bulk RNA. {ASK}?", _panda(), has=["We have bulk RNA"])
    assert "Not stated in your request: LIONESS-PANDA needs at least 3 samples" in understanding_paragraph(plain)
    stated = _check(f"{ASK} for our 40 samples?", {**_panda(), "sample_count": 40,
                                                  "sample_count_quote": "our 40 samples"})
    assert "Not stated" not in (understanding_paragraph(stated) or "")
    weighed = _check(f"The cohort has nine or seventeen samples. {ASK}?", _panda(),
                     has=["The cohort has nine or seventeen samples"])
    assert "Not stated" not in understanding_paragraph(weighed)


def test_cobra_says_its_relation_and_minimum_when_no_count_is_stated():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement
    from netzoo_agent_core.interpretation.required_conditions import quantity_note

    row = CheckedRequirement(quote="adjusted co-expression", kind="result", status="available",
                             delivered_by=["cobra.covariate_components"])
    note = quantity_note(CapabilityCheck(requirements=[row]), row)
    assert "COBRA needs at least 2 samples" in note and "COBRA needs more genes than samples" in note


@pytest.mark.parametrize("action, minimum", [("run_dragon", 3), ("run_giraffe", 2), ("run_cobra", 2)])
def test_the_contract_states_the_minimum_the_preflight_enforces(action, minimum):
    from netzoo_agent_core.policy import ProjectPolicyLoader
    from netzoo_agent_core.settings import PROJECT_ROOT
    from netzoo_agent_core.workflow_conditions import conditions_for

    spec = ProjectPolicyLoader(PROJECT_ROOT).load().workflows[action]
    assert any(item.limit == "min_samples" and item.text in spec.conventions for item in spec.input_checks)
    assert conditions_for(action).min_samples == minimum


def test_one_result_read_twice_in_overlapping_words_is_one_result():
    """Live attempt-06 T03: the reading split one request into two asks whose words overlap; "either 2 or 14" was then
    applied to neither, as if two results were asked."""
    task = ("Could you start LIONESS-PANDA to build one TF-to-gene network per biological sample from pine_bulk.tsv? "
            "The export contains either 2 or 14 samples.")
    long, short = ("one TF-to-gene network per biological sample from pine_bulk.tsv",
                   "one TF-to-gene network per biological sample")
    sentences = [task[a:b] for a, b in request_sentences(task)]
    entries = ["lioness_panda.per_sample_networks"]
    proposal = proposal_model(len(sentences)).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask(long, entries, scale="per_sample", regulator_kinds=["tf"]),
            _ask(short, entries, scale="per_sample", regulator_kinds=["tf"])]},
        "s2": {"role": "background", "has": ["either 2 or 14 samples"], "about_methods": [], "asks": []},
        "conditions": unstated_conditions()})
    check = build_capability_check(task, proposal)[0]
    assert [(row.status, row.depends_on) for row in check.results()] == [("needs_fact", "sample_count")] * 2


def test_the_guard_is_not_silenced_by_candidates_never_weighed_for_the_result():
    """Two separate results, candidates in a third sentence overlapping neither: count_update weighs them for none, so
    the unread-quantity guard still holds the result (it must not count them as explained)."""
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import decide_core

    task = ("Build a PANDA network for the liver set. Build a LIONESS-PANDA network per sample for the kidney set. "
            "The kidney set has either 2 or 14 samples.")
    sentences = [task[a:b] for a, b in request_sentences(task)]
    proposal = proposal_model(len(sentences)).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("Build a PANDA network for the liver set", ["panda.tf_gene_network"], scale="whole_cohort",
                 regulator_kinds=["tf"])]},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask("Build a LIONESS-PANDA network per sample for the kidney set", ["lioness_panda.per_sample_networks"],
                 scale="per_sample", regulator_kinds=["tf"])]},
        "s3": {"role": "background", "has": ["The kidney set has either 2 or 14 samples"], "about_methods": [],
               "asks": []},
        "conditions": unstated_conditions()})
    check = build_capability_check(task, proposal)[0]
    assert all(row.status == "available" for row in check.results())  # weighed for neither
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_check=check)
    assert decide_core(decision, task).kind == "ASK"


def test_context_moved_back_to_its_own_sentence_is_read_for_candidates():
    """Live attempt-07 T01: the reading put "either nine or seventeen patients" in the first sentence as an uncredited
    ask; ownership correction returns it to its own background sentence, and the candidates must be read from there."""
    task = ("Is LIONESS-PANDA suitable for one TF-to-gene network per patient? "
            "The post-QC export has either nine or seventeen patients. We have the TF motif prior and TF PPI.")
    sentences = [task[a:b] for a, b in request_sentences(task)]
    first = "Is LIONESS-PANDA suitable for one TF-to-gene network per patient"
    proposal = proposal_model(len(sentences)).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
            _ask(first, ["lioness_panda.per_sample_networks"], scale="per_sample", regulator_kinds=["tf"]),
            _ask("The post-QC export has either nine or seventeen patients", [])]},
        "s2": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "s3": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "conditions": unstated_conditions()})
    check = build_capability_check(task, proposal)[0]
    assert [a["values"] for a in check.count_alternatives] == [[9, 17]]
    assert [row.status for row in check.results()] == ["available"]


@pytest.mark.parametrize("numbers, status, gap", [("one or two", "not_available", True),
                                                  ("nine or seventeen", "available", False),
                                                  ("2 or 14", "needs_fact", False)])
def test_candidates_are_weighed_for_a_result_the_second_opinion_credits(numbers, status, gap):
    """The first reading credited nothing, so the candidates had no workflow to be weighed for; the second opinion's
    credit is weighed like the first reading's (live attempt-07 open gap)."""
    context = f"The entire cohort consists of either {numbers} biological samples"
    task = f"{context}; the manifest is unavailable. {ASK}?"
    check = _check(task, _ask(ASK, [], scale="per_sample", regulator_kinds=["tf"]), has=[context])
    assert check.full_gap and check.count_alternatives
    pairs = second_opinion_pairs(check, ["run_lioness_panda"])
    assert pairs
    (row,) = apply_second_opinion(check, pairs, ["all"] * len(pairs), task).results()
    assert row.status == status and row.second_opinion
    assert apply_second_opinion(check, pairs, ["all"] * len(pairs), task).full_gap is gap
    if status == "not_available":
        assert any(limit.startswith("with 1: LIONESS-PANDA needs at least 3 samples") for limit in row.limits)
        assert row.unknown_quote == context and row.fact_ids
    if status == "needs_fact":
        assert row.by_code and set(row.outcomes) == {"2", "14"} and row.fact_ids
    # Without the request's words nothing is weighed, as before.
    assert apply_second_opinion(check, pairs, ["all"] * len(pairs)).results()[0].status == "available"
