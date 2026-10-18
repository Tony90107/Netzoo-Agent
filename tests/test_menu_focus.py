"""Closed-menu judgment phase 1, step 4: the focused re-read of the candidates' limits and doubts.

No model calls: the candidates the first reading leaves, the strict schema with one field per limit, and the merge
rules -- a limit the first reading missed is added, a doubt replaces a stated value, words not in the request do
nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.menu_reading import Count, MenuReading, Said, SettingAsked, Wanted  # noqa: E402
from netzoo_agent_core.graph.menu_reading_call import read_focused  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import candidate_workflows, decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_focus import focus_limits, focus_model, merge_focused  # noqa: E402


def said(value: str, quote: str) -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote])


def blank(candidates) -> dict:
    limits = focus_limits(tuple(candidates))
    empty = {"status": "not_mentioned", "quote": ""}
    return {
        "settings": {key: {**empty, "value": "", "values": []} for key in limits["controls"]},
        "counts": {name: {**empty, "value": None, "values": []} for name in limits["counts"]},
        "data": {kind: dict(empty) for kind in limits["data"]},
        "conditions": {name: {**empty, "value": None, "values": []} for name in limits["conditions"]},
        "unsupported_settings": [],
    }


def test_candidates_are_the_workflows_left_before_contract_conditions():
    task = "We want a co-expression network for each of our 2 samples."
    reading = MenuReading(wanted=[Wanted(quote="a co-expression network for each of our 2 samples",
                                         artifact=said("coexpression_network", "a co-expression network"),
                                         granularity=said("per_sample", "for each of our 2 samples"))],
                          sample_count=Count(status="stated", value=2))
    assert candidate_workflows(reading, task) == ["BONOBO", "LIONESS-COEXPRESSION"]
    assert decide_menu(reading, task).kind == "DECLINE"  # both need three samples: candidates are read before that


def test_focus_schema_has_one_field_per_limit_and_is_strict():
    schema = focus_model(("BONOBO", "LIONESS-COEXPRESSION")).model_json_schema()
    defs = schema["$defs"]
    assert "bonobo__log_transformed" in defs["FocusedSettings"]["properties"]
    assert set(defs["FocusedCounts"]["properties"]) == {"sample_count"}
    for node in defs.values():
        if "properties" in node:
            assert set(node["required"]) == set(node["properties"]) and node["additionalProperties"] is False
    focus_model(("BONOBO", "LIONESS-COEXPRESSION")).model_validate(blank(("BONOBO", "LIONESS-COEXPRESSION")))


def test_a_focused_doubt_replaces_a_stated_value_and_is_asked():
    task = "Run BONOBO on lunar.tsv; I do not know whether the export was log-transformed and centered."
    first = MenuReading(wanted=[Wanted(quote="Run BONOBO on lunar.tsv")], data=["expression"],
                        settings=[SettingAsked(quote="log-transformed", workflow="BONOBO", control="log_transformed",
                                               value="true")])
    payload = blank(("BONOBO",))
    payload["settings"]["bonobo__log_transformed"] = {
        "status": "unsure", "value": "", "values": ["true", "false"],
        "quote": "I do not know whether the export was log-transformed"}
    merged, report = merge_focused(first, payload, task, ("BONOBO",))
    assert [(s.control, s.unsure, s.values) for s in merged.settings] == [("log_transformed", True, ["true", "false"])]
    decision = decide_menu(merged, task)
    assert decision.kind == "ASK" and decision.questions[0].dimension == "setting:BONOBO.log_transformed"
    assert report.filled


def test_an_unsure_control_waits_for_its_answer_before_combination_checks():
    task = "Can BONOBO keep save_pvals=true? The lab has not confirmed whether sparsify was set to true or false."
    reading = MenuReading(wanted=[Wanted(quote="Can BONOBO keep save_pvals=true?")], data=["expression"],
                          settings=[SettingAsked(quote="save_pvals=true", workflow="BONOBO", control="save_pvals",
                                                 value="true"),
                                    SettingAsked(quote="whether sparsify was set to true or false", workflow="BONOBO",
                                                 control="sparsify", unsure=True, values=["true", "false"])])
    decision = decide_menu(reading, task)
    assert decision.kind == "ASK" and decision.questions[0].dimension == "setting:BONOBO.sparsify"


def test_focused_limits_fill_what_the_first_reading_missed_and_never_overwrite_a_stated_one():
    task = "Can OTTER run on the GPU with 150 iterations for our 2 samples? We have no PPI network."
    first = MenuReading(wanted=[Wanted(quote="Can OTTER run on the GPU")],
                        settings=[SettingAsked(quote="150 iterations", workflow="OTTER", control="iterations",
                                               value="150")])
    payload = blank(("OTTER",))
    payload["settings"]["otter__computing"] = {"status": "stated", "value": "gpu", "values": [], "quote": "on the GPU"}
    payload["settings"]["otter__iterations"] = {"status": "stated", "value": "200", "values": [],
                                                "quote": "150 iterations"}
    payload["counts"]["sample_count"] = {"status": "stated", "value": 2, "values": [], "quote": "our 2 samples"}
    payload["data"]["ppi"] = {"status": "lacks", "quote": "We have no PPI network"}
    merged, _ = merge_focused(first, payload, task, ("OTTER",))
    assert {(s.control, s.value) for s in merged.settings} == {("computing", "gpu"), ("iterations", "150")}
    assert merged.sample_count.value == 2 and merged.data_absent == ["ppi"]


def test_focused_words_not_in_the_request_do_nothing():
    task = "Run DRAGON on our expression and methylation tables."
    first = MenuReading(wanted=[Wanted(quote="Run DRAGON")], data=["expression", "methylation"])
    payload = blank(("DRAGON",))
    payload["conditions"]["samples_matched"] = {"status": "unsure", "value": None,
                                                "values": ["same_samples", "different_samples"],
                                                "quote": "maybe from different donors"}
    payload["counts"]["sample_count"] = {"status": "unsure", "value": None, "values": [2, 20], "quote": "2 or 20"}
    merged, report = merge_focused(first, payload, task, ("DRAGON",))
    assert merged == first and len(report.dropped) == 2


def test_a_focused_count_doubt_and_condition_doubt():
    task = ("Run DRAGON on our layers. They may hold two or ten paired samples, and I am not sure the layers come "
            "from the same mice.")
    first = MenuReading(wanted=[Wanted(quote="Run DRAGON on our layers")], data=["expression", "methylation"],
                        sample_count=Count(status="stated", value=10, quotes=["ten paired samples"]))
    payload = blank(("DRAGON",))
    payload["counts"]["sample_count"] = {"status": "unsure", "value": None, "values": [],
                                         "quote": "They may hold two or ten paired samples"}
    payload["conditions"]["samples_matched"] = {"status": "unsure", "value": None, "values": [],
                                                "quote": "I am not sure the layers come from the same mice"}
    merged, _ = merge_focused(first, payload, task, ("DRAGON",))
    assert merged.sample_count.status == "conflicting" and merged.sample_count.values == [2, 10]
    assert merged.conditions["samples_matched"].values == ["same_samples", "different_samples"]


def test_an_unsupported_setting_for_a_workflow_without_controls_is_a_reason():
    task = "Can GIRAFFE be run with a learning rate of 1e-4 and 2,000 iterations on our 52 samples?"
    first = MenuReading(wanted=[Wanted(quote="Can GIRAFFE be run")], data=["expression", "motif_prior", "ppi"])
    payload = blank(("GIRAFFE",))
    payload["unsupported_settings"] = [
        {"quote": "a learning rate of 1e-4", "workflow": "GIRAFFE", "value": "1e-4", "asks_to_set": True},
        {"quote": "our 52 samples", "workflow": "GIRAFFE", "value": "52", "asks_to_set": False},
        {"quote": "a momentum of 0.9", "workflow": "GIRAFFE", "value": "0.9", "asks_to_set": True}]
    merged, report = merge_focused(first, payload, task, ("GIRAFFE",))
    assert [(s.workflow, s.control, s.quote) for s in merged.settings] == [
        ("GIRAFFE", "unregistered", "a learning rate of 1e-4")]
    assert decide_menu(merged, task).kind == "DECLINE"


def test_no_focused_read_while_the_result_is_open():
    class Never:
        def with_structured_output(self, *args, **kwargs):
            raise AssertionError("no call")

    task = "Analyze everything in our folder."
    read, candidates = read_focused(task, MenuReading(wanted=[Wanted(quote=task)]), Never())
    assert read is None
    read, _ = read_focused(task, MenuReading(status="failed"), Never())
    assert read is None
