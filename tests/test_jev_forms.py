"""jev-forms-2026-10-27 (ROUND.md): Jev's second read of time_model, spatial and input_network."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.interpretation.jev_forms import doubted, limiting_forms  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
         "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
         "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}
CONDOR = ("Please run CONDOR on it to find communities of transcription factors and their target genes.")
DRAGON = "Take the DRAGON edge list of microbes against metabolites and run CONDOR on it so I get communities."
TIME = ("I'd like to estimate transcription factor activity in each of our 30 yeast stress time-course samples and "
        "see which TFs activate or repress which genes.")
LAGGED = ("We want a dynamic model of how each TF's activity evolves from one visit to the next.")


def _proposal(quote, delivered, **attrs):
    from netzoo_agent_core.contracts.capability_check import proposal_model

    return proposal_model(1).model_validate({"s1": {
        "role": "asks", "has": [], "about_methods": [],
        "asks": [{**PLAIN, "quote": quote, "delivered_by": list(delivered), "not_by": [], **attrs}]}})


def _reader(said: dict, calls: list):
    """Jev as a table: (attr, words in the task) -> probabilities; the reader answers like `forms_doubted` when on."""
    def read(task, quote, attr, options):
        calls.append(attr)
        probs = next((p for (a, word), p in said.items() if a == attr and word in task), {})
        return doubted({"probabilities": probs}, options)
    return read


USER_SAYS_NOTHING = {("time_model", "time-course"): {"dynamic": 0.0, "separate": 0.99},
                     ("input_network", "transcription"): {"regulator_gene": 1.0},
                     ("group_membership", "transcription"): {}}
USER_SAYS_IT = {("time_model", "dynamic model"): {"dynamic": 1.0},
                ("input_network", "DRAGON"): {"gene_gene": 0.83, "other": 0.17}}


def _check(task, quote, delivered, said=USER_SAYS_NOTHING, overlap=None, **attrs):
    from netzoo_agent_core.interpretation.capability_check import _status_line, build_capability_check

    calls = []
    check, _ = build_capability_check(task, _proposal(quote, delivered, **attrs), forms_reader=_reader(said, calls),
                                      overlap_reader=overlap)
    [row] = check.results()
    return row, _status_line(row, check=check), calls


def test_limiting_forms_names_only_values_that_rule_the_credits_out():
    from netzoo_agent_core.capability_sheet import sheet_entries

    condor = sheet_entries()["condor.communities"]
    assert limiting_forms({"input_network": "gene_gene"}, [condor]) == [("input_network", ("gene_gene", "other"))]
    assert limiting_forms({"input_network": "regulator_gene"}, [condor]) == []
    assert limiting_forms({"input_network": "gene_gene"}, []) == []
    assert limiting_forms({"time_model": "dynamic", "spatial": "uses_neighbors"}, []) == [
        ("time_model", ("dynamic",)), ("spatial", ("uses_neighbors",))]


def test_without_a_reader_nothing_is_read_and_the_limit_stands():
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    check, _ = build_capability_check(TIME, _proposal(TIME, ("giraffe.tf_activity",), time_model="dynamic"))
    assert check.results()[0].status == "not_available"


def test_a_time_course_typed_dynamic_waits_on_the_time_model_question():
    """j3 R13: "time-course samples" typed dynamic refused GIRAFFE with a reason the user never gave."""
    from netzoo_agent_core.interpretation.needed_facts import fact_questions

    row, line, calls = _check(TIME, TIME, ("giraffe.tf_activity",), time_model="dynamic")
    assert calls == ["time_model"] and row.status == "needs_fact" and row.depends_on == "time_model"
    assert row.outcomes == {"not_dynamic": ["giraffe.tf_activity"], "dynamic": []}
    assert "the request does not say" in line and "you said you do not know" not in line
    assert "a dynamic model" in fact_questions(SimpleCheck(row))[0]


class SimpleCheck:
    def __init__(self, row):
        self.row = row

    def needed_facts(self):
        return [self.row]


def test_a_real_dynamic_request_keeps_its_refusal():
    row, line, _ = _check(LAGGED, LAGGED, ("giraffe.tf_activity",), said=USER_SAYS_IT, time_model="dynamic")
    assert row.status == "not_available" and "from one time point to the next" in line


def test_a_tf_gene_edge_list_typed_gene_gene_waits_on_the_network_question():
    """j3 R39 family: a TF-to-gene edge list typed gene_gene ruled CONDOR out."""
    row, _line, calls = _check(CONDOR, CONDOR, ("condor.communities",), input_network="gene_gene")
    assert calls == ["input_network"] and row.status == "needs_fact" and row.depends_on == "input_network"
    assert row.outcomes["regulator_gene"] == ["condor.communities"] and row.outcomes["gene_gene"] == []


def test_a_dragon_network_keeps_its_refusal():
    row, _line, _ = _check(DRAGON, DRAGON, ("condor.communities",), said=USER_SAYS_IT, input_network="gene_gene")
    assert row.status == "not_available"


def test_two_misreads_wait_together_when_the_overlap_read_doubts_too():
    """j3 R39: gene_gene and several_groups at once; neither read alone could make the credits fit."""
    row, _line, calls = _check(CONDOR, CONDOR, ("condor.communities",), input_network="gene_gene",
                               group_membership="several_groups", overlap=lambda task, quote: True)
    assert row.status == "needs_fact" and row.depends_on in ("input_network", "group_membership")
    without, _line, _ = _check(CONDOR, CONDOR, ("condor.communities",), input_network="gene_gene",
                               group_membership="several_groups", overlap=lambda task, quote: False)
    assert without.status == "not_available"


def test_an_uncredited_time_course_loses_the_wrong_time_reason():
    from netzoo_agent_core.interpretation.reason_layers import is_unmatched

    row, line, _ = _check(TIME, TIME, (), time_model="dynamic")
    assert row.doubted_forms == ["time_model"] and "from one time point to the next" not in line
    assert is_unmatched(line)


def test_the_time_model_answer_binds_in_code():
    from netzoo_agent_core.contracts.task_state import TaskState
    from netzoo_agent_core.engine.task_updates import _pending, bind_answers
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.core_decision import _facts
    from netzoo_agent_core.interpretation.task_answers import answered_check

    check, _ = build_capability_check(TIME, _proposal(TIME, ("giraffe.tf_activity",), time_model="dynamic"),
                                      forms_reader=_reader(USER_SAYS_NOTHING, []))
    [fact] = _facts(check, task=TIME)
    [pending] = _pending({"kind": "ASK", "facts": [fact.model_dump()]})
    state = TaskState.model_validate({"task_id": "t", "goal": TIME, "pending": [pending.model_dump()]})
    state, bound, _ = bind_answers(state, "Each time point separately.")
    assert [item.value for item in bound] == ["not_dynamic"]
    settled = answered_check(check, state.model_copy(update={"facts": bound})).results()[0]
    assert settled.status == "available"
