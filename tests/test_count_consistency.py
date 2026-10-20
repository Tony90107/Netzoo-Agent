"""A candidate quantity is judged once, with its meaning and deciding outcomes intact."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_count_alternatives import KEY, NETWORKS, PANELS, TASK, _alternative, _networks  # noqa: E402
from test_request_facts import _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import without_legacy_waits  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import wait_on_asked  # noqa: E402


def _sample_check(values, *, duplicate=False, **attrs):
    numbers = " or ".join(str(n) for n in values)
    task = f"Build a network for each tumour. We have either {numbers} tumours."
    quote = f"either {numbers} tumours"
    ask = _ask("Build a network for each tumour", ["lioness_panda.per_sample_networks"],
               scale="per_sample", regulator_kinds=["tf"], **attrs)
    extra = {"count_alternatives": [{"of": "samples", "values": list(values), "quote": quote}]} if duplicate else {}
    return task, _check(task, ask, unknown_facts=[{
        "about": "sample_count", "quote": quote, "count_kind": "choices", "count_values": list(values)}], **extra)


def _run_decision(check):
    return TaskDecision(action="run_lioness_panda", in_scope=True, should_execute=True,
                        execution_requested=True, confidence=0.9, reason="user requested networks",
                        capability_check=check, fact_check=FactCheck(status="checked"))


def test_feature_candidates_do_not_replace_the_stated_patient_count():
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]),
                   count_alternatives=[_alternative()], unknown_facts=[{
                       "about": "sample_count", "quote": PANELS, "count_kind": "choices",
                       "count_values": [200, 2000]}])
    (row,) = check.results()
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "feature_count", True)
    assert row.method["samples"] == 50
    assert row.outcomes == {"200": [KEY], "2000": []}
    assert not check.unknowns  # the same doubt must not also run through the generic sample-count rules
    [conflict] = [c for c in check.fact_conflicts if c.reason == "count_reading_precedence"]
    facts = {f.id: f for f in check.facts}
    assert {facts[i].property for i in conflict.used} == {"feature_count"}
    assert {facts[i].property for i in conflict.set_aside} == {"sample_count"}


def test_deciding_sample_count_cannot_be_cleared_by_the_fact_agent():
    task, check = _sample_check([2, 10])
    (row,) = without_legacy_waits(check).results()
    assert row.status == "needs_fact" and row.by_code
    core = decide_core(_run_decision(without_legacy_waits(check)), task)
    assert (core.kind, core.basis) == ("ASK", "count_fact")
    assert core.facts[0].outcomes == {"2": [], "10": ["LIONESS-PANDA"]}
    held = with_core(_run_decision(check), core)
    assert held.action == "no_tool" and not held.should_execute and not held.execution_requested
    reply = respond(None, {"decision": held.model_dump(), "messages": []})
    assert reply["reply_kind"] == "ask_facts"
    assert "No workflow has been selected and nothing runs before you answer" in reply["messages"][-1].content


@pytest.mark.parametrize("values,kind,status,outcomes", [
    ([8, 15], "DO", "available", {}),
    ([1, 2], "DECLINE", "not_available", {}),
    ([2, 10], "ASK", "needs_fact", {"2": [], "10": ["lioness_panda.per_sample_networks"]}),
])
@pytest.mark.parametrize("duplicate", [False, True])
def test_discrete_counts_have_the_same_three_way_verdict_through_either_field(values, kind, status, outcomes, duplicate):
    task, check = _sample_check(values, duplicate=duplicate)
    (row,) = check.results()
    assert (row.status, row.outcomes) == (status, outcomes)
    checked = without_legacy_waits(check)
    assert decide_core(_run_decision(checked), task).kind == kind


def test_second_opinion_count_question_has_the_same_protection():
    task, check = _sample_check([2, 10])
    blank = check.model_copy(update={"full_gap": True, "requirements": [
        row.model_copy(update={"status": "not_available", "delivered_by": [], "by_code": False})
        for row in check.results()]})
    checked = wait_on_asked(blank, [(0, "run_lioness_panda", ["lioness_panda.per_sample_networks"])])
    core = decide_core(_run_decision(without_legacy_waits(checked)), task)
    assert core.kind == "ASK" and core.facts[0].by_code


def test_different_quantities_with_the_same_candidates_remain_independent():
    task = "Build a network for each tumour. We have either 2 or 10 tumours and either 2 or 10 genes."
    ask = _ask("Build a network for each tumour", ["lioness_panda.per_sample_networks"],
               scale="per_sample", regulator_kinds=["tf"])
    check = _check(task, ask, count_alternatives=[{
        "of": "features", "quote": "either 2 or 10 genes", "values": [2, 10]}], unknown_facts=[{
            "about": "sample_count", "quote": "either 2 or 10 tumours", "count_kind": "choices",
            "count_values": [2, 10]}])
    assert check.unknowns == [["sample_count", "either 2 or 10 tumours"]]


def test_matching_words_but_different_candidate_sets_are_not_deduplicated():
    task = TASK + " We also do not know whether 2 or 10 patients passed QC."
    unknown = task.rstrip(".")
    check = _check(task, _networks(features=[(300, "300 serum miRNAs")]),
                   count_alternatives=[_alternative()], unknown_facts=[{
                       "about": "sample_count", "quote": unknown, "count_kind": "choices",
                       "count_values": [2, 10]}])
    assert check.unknowns == [["sample_count", unknown]]


def test_other_unknown_dimensions_on_the_same_words_are_not_deduplicated():
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]),
                   count_alternatives=[_alternative()], unknown_facts=[{
                       "about": "value_type", "quote": PANELS, "count_kind": "choices",
                       "count_values": [200, 2000]}])
    assert check.unknowns == [["value_type", PANELS]]


@pytest.mark.parametrize("scope,waiting", [("archive", True), ("none", False), ("invalid", False)])
@pytest.mark.parametrize("duplicate", [False, True])
def test_sample_count_candidates_affect_only_the_result_they_are_scoped_to(scope, waiting, duplicate):
    first, second = "Build a network for each confirmed tumour", "Build a network for each archive tumour"
    task = f"{first}; there are 12 confirmed tumours. {second}. The archive has either 2 or 10 tumours."
    asks = [_ask(first, ["lioness_panda.per_sample_networks"], scale="per_sample", regulator_kinds=["tf"],
                 samples=12, samples_quote="12 confirmed tumours"),
            _ask(second, ["lioness_panda.per_sample_networks"], scale="per_sample", regulator_kinds=["tf"])]
    applies = {"archive": [second], "none": [], "invalid": ["an invented result"]}[scope]
    extra = {"count_alternatives": [{"of": "samples", "quote": "either 2 or 10 tumours", "values": [2, 10]}]} \
        if duplicate else {}
    check = _check(task, *asks, unknown_facts=[{
        "about": "sample_count", "quote": "either 2 or 10 tumours", "count_kind": "choices",
        "count_values": [2, 10], "applies_to": applies}], **extra)
    confirmed, archive = without_legacy_waits(check).results()
    assert confirmed.status == "available" and confirmed.method["samples"] == 12
    assert (archive.status == "needs_fact") is waiting
    assert decide_core(_run_decision(without_legacy_waits(check)), task).kind == ("ASK" if waiting else "DO")


def test_deduplication_still_sets_aside_a_count_the_user_left_in_doubt():
    asked = "Build a joint network for each patient"
    task = (f"{asked} from 1,000 features and 1000 patients. "
            "The final sample count after QC is either 4 or 10.")
    unknown = "The final sample count after QC is either 4 or 10"
    ask = _ask(asked, [KEY], scale="per_sample", omics_layers=2, samples=1000,
               samples_quote="1000 patients", features=[(1000, "1,000 features")])
    check = _check(task, ask, count_alternatives=[{"of": "samples", "quote": unknown, "values": [4, 10]}],
                   unknown_facts=[{"about": "sample_count", "quote": unknown, "count_kind": "choices",
                                   "count_values": [4, 10]}])
    (row,) = check.results()
    assert row.status == "available" and not check.needed_facts()  # both 4 and 10 fit the 20M-value cap
    assert "samples" not in row.method
    assert decide_core(_run_decision(check), task).kind == "DO"
