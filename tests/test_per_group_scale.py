"""per-group-scale-2026-10-29 (j6 X30): "one TF-to-gene network per stage, each built from all 12 samples of that
stage" is one aggregate result per group -- its own scale value, credited to aggregate workflows. Plus jev-guard's
opposite direction for settled-answers: a bound form answer that rules a workflow out still refuses it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_not_stated_fields import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import SCALE_QUESTION, checked_scale_question  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _fitting  # noqa: E402

OTTER, LIONESS = "otter.tf_gene_network", "lioness_panda.per_sample_networks"


def test_the_reading_schema_offers_per_group():
    schema = proposal_model(1).model_json_schema()
    ask = schema["$defs"][schema["properties"]["s1"]["$ref"].split("/")[-1]]["properties"]["asks"]["items"]
    ask = schema["$defs"][ask["$ref"].split("/")[-1]]["properties"]
    assert ask["scale"]["enum"] == ["per_sample", "per_group", "whole_cohort", "unstated"]


def test_a_result_per_group_is_credited_to_aggregate_workflows_only():
    keys = [OTTER, LIONESS]  # LIONESS-PANDA also writes the cohort network, so it carries both scales
    assert _fitting(keys, _ask(scale="per_group")) == _fitting(keys, _ask(scale="whole_cohort")) == keys
    assert _fitting(keys, _ask(scale="per_sample")) == [LIONESS]
    assert _fitting([OTTER], _ask(scale="per_group")) == [OTTER]
    assert _fitting([OTTER], _ask(scale="per_sample")) == []
    assert _fitting(keys, _ask(scale="unstated")) == keys


def test_a_per_group_scale_counts_as_stated_for_the_scale_question():
    question = f"Which workflow? {SCALE_QUESTION}"
    assert checked_scale_question(question, ["per_group"]) == "Which workflow?"
    assert checked_scale_question(question, ["per_group", "unstated"]) == question


TASK = "Run CONDOR on our TF-gene edge list to find modules."
QUOTE = "Run CONDOR on our TF-gene edge list to find modules."
REPLY = "A gene may belong to several modules at once."


def _check():
    from test_jev_answers import PLAIN

    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    proposal = proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
        {**PLAIN, "quote": QUOTE, "delivered_by": ["condor.communities"], "not_by": [],
         "group_membership": "several_groups"}]}})
    check, _ = build_capability_check(TASK, proposal, overlap_reader=lambda task, quote: True)
    return check


def test_a_bound_several_groups_answer_still_refuses_condor_without_the_condition_check():
    from netzoo_agent_core.engine.task_updates import _pending, bind_answers
    from netzoo_agent_core.contracts.task_state import TaskState
    from netzoo_agent_core.interpretation.core_decision import _facts
    from netzoo_agent_core.interpretation.task_answers import answered_check, without_settled

    check = _check()
    assert [row.depends_on for row in check.needed_facts()] == ["group_membership"]
    pending = _pending({"kind": "ASK", "facts": [fact.model_dump() for fact in _facts(check, task=TASK)]})
    state = TaskState.model_validate({"task_id": "t", "goal": TASK, "pending": [q.model_dump() for q in pending]})
    state, bound, _ = bind_answers(state, "Several groups at once.")
    assert [fact.value for fact in bound] == ["several_groups"]
    assert without_settled(["Several groups at once."], state) == []  # left out of the condition check ...
    (row,) = answered_check(check, state).results()  # ... and still refused by the answer itself
    assert row.status == "not_available" and row.delivered_by == []
    assert any("Several groups at once." in limit for limit in row.limits)
