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
    build_capability_check, request_sentences, second_opinion_pairs, understanding_paragraph,
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
