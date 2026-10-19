"""Slim reading S1 (spec docs/superpowers/specs/2026-10-19-slim-reading-fields-design.md): the field table is complete
for the slim fields (C1-C4 restated: what the code reads in step 1 or chooses for step 3 covers every dimension the
decision needs), the two wire schemas are strict and small, and code checks every quote and value. No model calls.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs/research-log/closed-menu-phase0-2026-10-18"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.menu_reading import MenuReading, Said, Wanted  # noqa: E402
from netzoo_agent_core.contracts.slim_reading import ResultItem, SlimReading, Stated  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import b_fields, candidate_workflows, decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_focus import focus_limits  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import (  # noqa: E402
    FACTS, Needs, chosen, core_model, core_text, focus_model, from_core, merge_focus, slim_needs, split_b, to_menu,
    to_slim,
)
from netzoo_agent_core.interpretation.slim_values import (  # noqa: E402
    wire_payloads, wire_values,
)
from netzoo_agent_core.judgment_defaults import load_defaults  # noqa: E402

WORKFLOWS = ROOT / "workflows"
GOLD = yaml.safe_load((ROOT / "docs/research-log/closed-menu-phase0-2026-10-18/gold_readings.yaml").read_text())
ITEMS = {item["id"]: item for item in json.loads(
    (ROOT / "docs/research-log/core-judgment-2026-10-15/items.json").read_text())["items"]}


def said(value: str, quote: str) -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote])


def _needs(workflow: str, table) -> list[str]:
    data = []
    for need in table.workflow_data[workflow][1]:
        data += ["expression", "methylation"] if need == "two_layers" else [need.split("|")[0]]
    return list(dict.fromkeys(data))


def _b_dimensions(table) -> dict[str, str]:
    return {dimension: name for name, field in table.slim_fields.items() if field.kind == "B" for dimension in field.fills}


# --- C1-C4 for the slim fields -------------------------------------------------------------------------------------

def test_c1_results_told_apart_only_by_a_b_field_have_it_read():
    """Two workflows' results that differ only in B1-B3 attributes: whenever both are candidates, step 2 chooses one of
    those fields, so the focused read can tell them apart."""
    table, sheet = load_defaults(), sheet_entries()
    b = _b_dimensions(table)
    produces = sorted(key for key, entry in sheet.items() if entry.kind == "produces")
    checked = 0
    for first, second in itertools.combinations(produces, 2):
        a, c = sheet[first], sheet[second]
        if a.workflow == c.workflow or table.by_entry[first] != table.by_entry[second] \
                or table.by_entry[first] == "comparison":
            continue
        left = {"granularity": a.granularity, "regulators": a.regulators, "integration": a.layers}
        right = {"granularity": c.granularity, "regulators": c.regulators, "integration": c.layers}
        differ = {name for name in left if left[name] != right[name]}
        if not differ or not differ <= set(b) or (a.signed, a.input_network, a.groups) != (c.signed, c.input_network,
                                                                                            c.groups):
            continue
        reading = MenuReading(wanted=[Wanted(quote="x", artifact=said(table.by_entry[first], "x"))],
                              data=list(dict.fromkeys(_needs(a.workflow, table) + _needs(c.workflow, table))))
        if not {a.workflow, c.workflow} <= set(candidate_workflows(reading)):
            continue
        intents, _conditions, _candidates = b_fields(reading)
        chosen_ = {"layers" if d == "integration" else d for _item, d in intents}
        assert {"layers" if d == "integration" else d for d in differ} & chosen_, (first, second, differ, intents)
        checked += 1
    assert checked >= 5


def test_c2_every_near_miss_on_a_b_field_is_read_when_its_workflow_is_the_candidate():
    """A near miss ruled out by a B value (OTTER per sample, PUMA lncRNAs, DRAGON three layers, a germline SAMBAR):
    with that workflow named and a result asked, step 2 chooses the field for some result, so a stated off-menu value
    is read and refuses. (A near miss is about one result: GIRAFFE's per-sample wiring beside its per-sample TF
    activity, LIONESS-DRAGON's per-sample p-values -- an edge_significance it does not give.)"""
    table, sheet = load_defaults(), sheet_entries()
    b = _b_dimensions(table)
    checked = 0
    for key, (dimension, _value) in table.ruled_by.items():
        if dimension not in b or key not in sheet:
            continue
        workflow = sheet[key].workflow
        results = table.dimensions["artifact"].values
        read = set()
        for result in results:
            reading = MenuReading(wanted=[Wanted(quote="x", artifact=said(result, "x"))], named_workflows=[workflow],
                                  data=_needs(workflow, table))
            intents, conditions, _candidates = b_fields(reading)
            read |= {d for _item, d in intents} | set(conditions)
        if dimension == "mirna_driver":
            dimension = "regulators"  # B2: one cell for the regulators and what drives miRNA links
        assert dimension in read or (dimension == "layers" and "integration" in read), (key, read)
        checked += 1
    assert checked >= 6


def test_c3_every_request_scope_limit_is_read_by_b5_or_b6():
    table = load_defaults()
    b = _b_dimensions(table)
    assert set(table.limit_fields.values()) <= set(b)
    for path in WORKFLOWS.glob("*.yaml"):
        workflow_yaml = yaml.safe_load(path.read_text(encoding="utf-8"))
        for check in workflow_yaml.get("input_checks") or []:
            if check.get("scope") != "request":
                continue
            dimension = table.limit_fields[str(check["limit"]).split(":")[0]]
            workflow = next(name for name, entry in sheet_entries().items()
                            if entry.kind == "produces" and entry.workflow.casefold() == path.stem.casefold()).split(
                ".")[0]
            name = next(w for w in table.workflow_data if w.casefold() == path.stem.casefold())
            counts = focus_limits((name,))["counts"]
            if dimension == "settings":
                assert "sample_count" in counts, (name, check)  # SAMBAR: kmax at most the samples
            else:
                assert dimension in counts, (name, workflow, check)


def test_c4_every_dimension_is_read_by_one_slim_field_and_no_field_is_idle():
    table = load_defaults()
    names = {f"{c}{i}" for c, n in (("A", 4), ("B", 6), ("C", 7), ("D", 7)) for i in range(1, n + 1)}
    assert set(table.slim_fields) == names
    filled = {d for field in table.slim_fields.values() for d in field.fills}
    assert set(table.dimensions) <= filled, sorted(set(table.dimensions) - filled)
    assert all(field.fills for field in table.slim_fields.values())
    # One field reads each dimension, except C fields code derives from A or B (C1, C5, C6, C7) and value_type,
    # which is C4 when binary is in play and B4 (DRAGON's continuous values) otherwise.
    read = [d for name, field in table.slim_fields.items() if name not in ("C1", "C5", "C6", "C7")
            for d in field.fills]
    doubled = {d for d in read if read.count(d) > 1}
    assert doubled == {"value_type"}


def test_the_facts_code_writes_fill_their_fields():
    table = load_defaults()
    for key, raw in GOLD.items():
        from phase0_gate import reading
        for fact in to_slim(reading(raw)).stated:
            base = "settings" if fact.field == "B5" or fact.name.startswith("setting:") else \
                "feature_count" if fact.name == "single_feature_count" else fact.name
            assert base in table.slim_fields[fact.field].fills or (
                fact.field == "B4" and fact.name.startswith("setting:")), (key, fact)
    for name, (field, dimension, _menu) in FACTS.items():
        assert dimension in table.slim_fields[field].fills or (name == "special_data" and field == "C4")


def test_gold_readings_keep_their_calls_in_the_slim_shape():
    from phase0_gate import reading
    for key, raw in GOLD.items():
        gold = reading(raw)
        before, after = decide_menu(gold, ITEMS[key]["prompt"]), decide_menu(to_menu(to_slim(gold)), ITEMS[key]["prompt"])
        assert (before.kind, before.workflows, [q.dimension for q in before.questions]) == \
            (after.kind, after.workflows, [q.dimension for q in after.questions]), key


# --- the two wire schemas ---------------------------------------------------------------------------------------------

def _strict_everywhere(schema: dict) -> None:
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert node.get("additionalProperties") is False
                assert set(node.get("required") or []) == set(node["properties"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    enums = sum(len(node["enum"]) for node in _nodes(schema) if isinstance(node, dict) and "enum" in node)
    assert enums < 200


def _nodes(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _nodes(value)


def test_the_core_schema_is_strict_and_shows_no_b_field():
    schema = core_model(("PANDA", "OTTER")).model_json_schema()
    _strict_everywhere(schema)
    assert list(schema["properties"]) == ["items", "names", "data", "only_these", "run", "run_quote", "facts",
                                          "unregistered_methods"]
    assert "names" not in core_model(()).model_json_schema()["properties"]
    text = core_text()
    assert "CONTROLS" not in text and "granularity" not in text and len(text) < 8000


def test_the_focus_schema_has_one_cell_per_chosen_field():
    needs = Needs(intents=((0, "granularity"), (0, "regulators"), (0, "integration")),
                  conditions=("samples_matched", "setting:BONOBO.log_transformed"),
                  candidates=("BONOBO", "DRAGON"), counts=("sample_count",), groups=False)
    schema = focus_model(needs).model_json_schema()
    _strict_everywhere(schema)
    assert list(schema["properties"]) == ["item1_scale", "item1_regulators", "item1_layers", "samples_matched",
                                          "bonobo_log_transformed", "settings", "counts"]
    scale = schema["$defs"]["Cell_item1_scale"]["properties"]["value"]
    assert "per_group" not in json.dumps(scale)  # no groups named: no per-group value


# --- step 1: code checks the words and the values ---------------------------------------------------------------------

TASK = ("Run LIONESS-PANDA on expr.tsv, motif.txt and ppi.txt for our 40 tumours so I can later compare responders "
        "and non-responders; I also want a p-value for every edge. We have no methylation. "
        "Please e-mail the results to Dr. Lee.")


def test_from_core_keeps_only_the_requests_words_and_menu_values():
    payload = {
        "items": [{"quote": "Run LIONESS-PANDA on expr.tsv", "asks": "workflow_only", "result": "", "results": [],
                   "outside_name": ""},
                  {"quote": "a gene regulatory atlas", "asks": "menu_result", "result": "regulatory_network",
                   "results": [], "outside_name": ""}],  # not the request's words
        "names": {"LIONESS_PANDA": {"role": "target"}},
        "data": [{"kind": "expression", "status": "has", "quote": "expr.tsv"},
                 {"kind": "methylation", "status": "lacks", "quote": "We have no methylation"},
                 {"kind": "cytokines", "status": "has", "quote": "tumours"}],  # no data kind
        "only_these": "", "run": "run", "run_quote": "Run LIONESS-PANDA",
        "facts": [{"field": "comparison", "value": "later", "values": [],
                   "quote": "so I can later compare responders and non-responders"},
                  {"field": "requirement", "value": "what_it_contains", "values": [],
                   "quote": "a p-value for every edge"},
                  {"field": "outside_action", "value": "", "values": [], "quote": "e-mail the results to Dr. Lee"},
                  {"field": "sign", "value": "activating", "values": [], "quote": "for our 40 tumours"},  # off menu
                  {"field": "special_data", "value": "bulk_samples", "values": [], "quote": "40 tumours"}],  # plain
        "unregistered_methods": [],
    }
    slim, report = from_core(payload, TASK)
    assert [r.quote for r in slim.results] == ["Run LIONESS-PANDA on expr.tsv"]
    assert slim.roles == {"LIONESS-PANDA": "target"} and slim.run == "run"
    assert [(d.name, d.value) for d in slim.data] == [("expression", "has"), ("methylation", "lacks")]
    assert [(f.field, f.name, f.value) for f in slim.stated] == [
        ("D2", "compare", "later"), ("D4", "requirements", "what_it_contains"), ("C3", "delivery", "outside_netzoo")]
    assert any("quote not in the request" in line for line in report.dropped)
    menu = to_menu(slim)
    assert menu.delivery.known() == "outside_netzoo" and menu.data_absent == ["methylation"]
    assert any(w.form == "purpose" for w in menu.wanted) and menu.run_requested


def test_a_special_situation_the_user_is_unsure_of_is_unsure_between_both_values():
    task = "I am not sure whether these profiles are single cells or pseudo-bulk."
    slim, _ = from_core({"items": [], "data": [], "only_these": "", "run": "ask", "run_quote": "",
                         "facts": [{"field": "special_data", "value": "", "values": ["single_cells"],
                                    "quote": "not sure whether these profiles are single cells or pseudo-bulk"}],
                         "unregistered_methods": []}, task)
    assert [(f.field, f.name, f.values) for f in slim.stated] == [("C4", "data_unit", ["bulk_samples", "single_cells"])]


def test_an_off_menu_result_naming_a_workflow_or_a_file_names_no_result():
    task = "Run LIONESS-PANDA and analyze edges_release.tsv"
    payload = {"items": [{"quote": "Run LIONESS-PANDA", "asks": "off_menu_result", "result": "", "results": [],
                          "outside_name": "LIONESS-PANDA"},
                         {"quote": "analyze edges_release.tsv", "asks": "off_menu_result", "result": "",
                          "results": [], "outside_name": "edges_release.tsv"}],
               "data": [], "only_these": "", "run": "ask", "run_quote": "", "facts": [], "unregistered_methods": []}
    slim, _ = from_core(payload, task)
    assert [r.said for r in slim.results] == ["workflow_only", "workflow_only"]


# --- step 2 and step 3 -----------------------------------------------------------------------------------------------

DRAGON_TASK = ("Run DRAGON on expression.csv and methylation.csv from the same 110 patients; I am not sure if the "
               "methylation values are continuous betas or 0/1 calls. Use lambda 0.3.")


def _dragon_core() -> SlimReading:
    return SlimReading(results=[ResultItem(quote="Run DRAGON on expression.csv and methylation.csv",
                                           said="workflow_only")],
                       roles={"DRAGON": "target"},
                       data=[Stated(field="A3", name="expression", value="has", quote="expression.csv"),
                             Stated(field="A3", name="methylation", value="has", quote="methylation.csv")],
                       run="run", run_quote="Run DRAGON")


def test_step_two_chooses_dragons_conditions_and_step_three_fills_them():
    core = _dragon_core()
    needs = slim_needs(core, DRAGON_TASK)
    assert needs.candidates == ("DRAGON",)
    assert set(needs.conditions) == {"samples_matched", "value_type"}
    focused, report = merge_focus(core, {
        "item1_layers": {"status": "not_said", "value": None, "values": [], "quote": ""},
        "samples_matched": {"status": "stated", "value": "same_samples", "values": [],
                            "quote": "from the same 110 patients"},
        "value_type": {"status": "unsure", "value": None, "values": ["continuous", "binary"],
                       "quote": "not sure if the methylation values are continuous betas or 0/1 calls"},
        "settings": [{"quote": "lambda 0.3", "workflow": "DRAGON", "control": "no_such_control", "value": "0.3",
                      "values": [], "asks_to_set": True}],
        "counts": [{"what": "samples", "layer": "", "value": 110, "values": [], "quote": "the same 110 patients"}],
    } if "item1_layers" in [c[0] for c in needs.cells()] else {
        "samples_matched": {"status": "stated", "value": "same_samples", "values": [],
                            "quote": "from the same 110 patients"},
        "value_type": {"status": "unsure", "value": None, "values": ["continuous", "binary"],
                       "quote": "not sure if the methylation values are continuous betas or 0/1 calls"},
        "settings": [], "counts": []}, DRAGON_TASK, needs)
    menu = to_menu(focused)
    assert menu.conditions["samples_matched"].known() == "same_samples"
    assert menu.conditions["value_type"].status == "unsure"
    decision = decide_menu(menu, DRAGON_TASK)
    assert decision.kind == "ASK" and "value_type" in [q.dimension for q in decision.questions]
    assert all(f.field.startswith("B") for f in focused.stated)


def test_a_regulator_cell_maps_to_regulators_and_what_drives_mirna_links():
    task = "Build a TF and miRNA network where miRNA edges follow our measured miRNA expression."
    core = SlimReading(results=[ResultItem(quote="Build a TF and miRNA network", said="menu_result",
                                           value="regulatory_network")])
    needs = Needs(intents=((0, "regulators"),), candidates=("PUMA",))
    slim, _ = merge_focus(core, {"item1_regulators": {
        "status": "stated", "value": "mirna_expression_driven", "values": [],
        "quote": "miRNA edges follow our measured miRNA expression"}, "settings": []}, task, needs)
    menu = to_menu(slim)
    assert menu.wanted[0].regulators.known() == "tf_mirna"
    assert menu.conditions["mirna_driver"].known() == "measured_expression"
    unsure, _ = merge_focus(core, {"item1_regulators": {
        "status": "unsure", "value": None, "values": ["tf", "other_regulators"],
        "quote": "TF and miRNA network"}, "settings": []}, task, needs)
    assert to_menu(unsure).wanted[0].regulators.values == ["tf", "off_menu"]
    every, _ = merge_focus(core, {"item1_regulators": {
        "status": "unsure", "value": None, "values": ["tf", "tf_and_mirna_prior", "mirna_expression_driven"],
        "quote": "TF and miRNA network"}, "settings": []}, task, needs)
    menu = to_menu(every)
    assert menu.wanted[0].regulators.values == ["tf", "tf_mirna"] and "mirna_driver" not in menu.conditions


def test_not_said_writes_nothing_and_a_data_description_is_no_setting():
    task = "Run BONOBO on expr.tsv; the table has a header row."
    core = SlimReading(results=[ResultItem(quote="Run BONOBO on expr.tsv", said="workflow_only")],
                       roles={"BONOBO": "target"})
    needs = slim_needs(core, task)
    assert {"setting:BONOBO.log_transformed", "setting:BONOBO.centered"} <= set(needs.conditions)
    empty = {key: {"status": "not_said", "value": None, "values": [], "quote": ""} for key, _i, _d in needs.cells()}
    slim, report = merge_focus(core, {**empty, "settings": [
        {"quote": "the table has a header row", "workflow": "BONOBO", "control": "unregistered", "value": "",
         "values": [], "asks_to_set": False}], **({"counts": []} if needs.counts else {})}, task, needs)
    assert slim.stated == [] and report.dropped
    decision = decide_menu(to_menu(slim), task)
    assert decision.kind == "ASK" and "setting:BONOBO.log_transformed" in [q.dimension for q in decision.questions]


def test_counts_are_summed_over_layers_by_code():
    task = "We have 15 miRNAs and 210 cytokines measured on 64 patients."
    core = SlimReading(results=[ResultItem(quote="We have 15 miRNAs", said="workflow_only")])
    needs = Needs(candidates=("LIONESS-DRAGON",), counts=("sample_count", "feature_count"))
    slim, _ = merge_focus(core, {"settings": [], "counts": [
        {"what": "features", "layer": "mirna_expression", "value": 15, "values": [], "quote": "15 miRNAs"},
        {"what": "features", "layer": "protein", "value": 210, "values": [], "quote": "210 cytokines"},
        {"what": "samples", "layer": "", "value": 64, "values": [], "quote": "64 patients"}]}, task, needs)
    menu = to_menu(slim)
    assert (menu.sample_count.value, menu.feature_count.value, menu.single_feature_count) == (64, 225, None)


def test_b_facts_are_read_only_when_step_two_chooses_them():
    core = _dragon_core()
    slim = core.model_copy(update={"stated": [
        Stated(field="B4", name="samples_matched", value="same_samples", quote="from the same 110 patients"),
        Stated(field="B1", name="granularity", value="per_sample", quote="x", item=0)]})
    core_part, b_facts = split_b(slim)
    assert core_part.stated == [] and len(b_facts) == 2
    needs = slim_needs(core_part, DRAGON_TASK)
    assert chosen(b_facts[0], needs)
    assert chosen(b_facts[1], needs) == any(d == "granularity" for _i, d in needs.intents)
    assert not chosen(b_facts[0], Needs())


def test_wire_payloads_read_back_to_the_same_reading_and_count_their_values():
    core = _dragon_core()
    slim = core.model_copy(update={"stated": [
        Stated(field="B4", name="samples_matched", value="same_samples", quote="from the same 110 patients")]})
    needs = slim_needs(core, DRAGON_TASK)
    core_payload, focus_payload = wire_payloads(slim, needs, ("DRAGON",))
    read, _ = from_core(core_payload, DRAGON_TASK)
    assert read.model_dump(exclude={"stated"}) == core.model_dump(exclude={"stated"})
    merged, _ = merge_focus(read, focus_payload, DRAGON_TASK, needs)
    assert [(f.field, f.name, f.value) for f in merged.stated] == [("B4", "samples_matched", "same_samples")]
    written, content = wire_values(core_payload)
    assert 0 < content <= written < 40


# --- the calls ------------------------------------------------------------------------------------------------------

def test_read_slim_reads_the_core_then_only_the_fields_step_two_chose():
    from netzoo_agent_core.graph.slim_reading_call import read_slim

    core_payload = {
        "items": [{"quote": "Run DRAGON on expression.csv and methylation.csv", "asks": "workflow_only", "result": "",
                   "results": [], "outside_name": ""}],
        "names": {"DRAGON": {"role": "target"}},
        "data": [{"kind": "expression", "status": "has", "quote": "expression.csv"},
                 {"kind": "methylation", "status": "has", "quote": "methylation.csv"}],
        "only_these": "", "run": "run", "run_quote": "Run DRAGON", "facts": [], "unregistered_methods": []}
    seen = []

    class Model:
        def with_structured_output(self, schema, **kwargs):
            seen.append(schema.__name__)

            def invoke(_self, messages):
                if schema.__name__ == "SlimCoreWire":
                    assert "CONTROLS" not in messages[0].content
                    return {"parsed": schema.model_validate(core_payload), "raw": None}
                cells = {name: {"status": "not_said", "value": None, "values": [], "quote": ""}
                         for name in schema.model_fields if name not in ("settings", "counts")}
                cells["samples_matched"] = {"status": "stated", "value": "same_samples", "values": [],
                                            "quote": "from the same 110 patients"}
                return {"parsed": schema.model_validate({**cells, "settings": [], **(
                    {"counts": []} if "counts" in schema.model_fields else {})}), "raw": None}

            return type("Adapter", (), {"invoke": invoke})()

    read = read_slim(DRAGON_TASK, Model())
    assert seen == ["SlimCoreWire", "SlimFocusWire"] and not read.error and not read.focus_error
    assert [(f.field, f.name, f.value) for f in read.reading.stated] == [("B4", "samples_matched", "same_samples")]
    decision = decide_menu(to_menu(read.reading), DRAGON_TASK)
    assert decision.kind == "ASK"  # value_type not said: asked (after the result DRAGON gives), never refused

    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    failed = read_slim(DRAGON_TASK, Broken())
    assert failed.reading.status == "failed" and decide_menu(to_menu(failed.reading), DRAGON_TASK).kind == "UNCHECKED"


# --- hybrid spec 3.4: the three h3 bugs (synthetic cases) ------------------------------------------------------------

def test_a_settings_alternatives_are_only_values_the_user_wrote():
    task = "Run BONOBO with sparsify on, confidence 0.05, delta 0.5 and .h5 output. For OTTER, lam is 0.35 or 3.5."
    core = SlimReading(results=[ResultItem(quote="Run BONOBO", said="workflow_only")])
    needs = Needs(candidates=("BONOBO", "OTTER"))
    slim, _ = merge_focus(core, {"settings": [
        {"quote": "confidence 0.05", "workflow": "BONOBO", "control": "bonobo_confidence", "value": "0.05",
         "values": [str(i / 100) for i in range(101)], "asks_to_set": True},  # the whole range listed
        {"quote": ".h5 output", "workflow": "BONOBO", "control": "bonobo_output_format", "value": ".h5",
         "values": [".h5", ".hdf", ".txt", ".csv"], "asks_to_set": True},
        {"quote": "lam is 0.35 or 3.5", "workflow": "OTTER", "control": "lam", "value": "",
         "values": ["0.35", "3.5", "0.035"], "asks_to_set": True},
        {"quote": "sparsify on", "workflow": "BONOBO", "control": "sparsify", "value": "",
         "values": ["true", "false"], "asks_to_set": True}]}, task, needs)
    got = {(f.name, f.value, tuple(f.values)) for f in slim.stated}
    assert got == {("bonobo_confidence", "0.05", ()), ("bonobo_output_format", ".h5", ()),
                   ("lam", "", ("0.35", "3.5")), ("sparsify", "", ("true", "false"))}


def test_an_unsure_count_of_one_data_type_is_the_count_cobra_checks():
    task = "Start COBRA for our 380 patients; I think around 400 genes, but it might be fewer than 350."
    core = SlimReading(results=[ResultItem(quote="Start COBRA", said="workflow_only")], roles={"COBRA": "target"},
                       data=[Stated(field="A3", name="expression", value="has", quote="400 genes"),
                             Stated(field="A3", name="design_matrix", value="has", quote="380 patients")])
    needs = Needs(candidates=("COBRA",), counts=("sample_count", "feature_count"))
    slim, _ = merge_focus(core, {"settings": [], "counts": [
        {"what": "samples", "layer": "", "value": 380, "values": [], "quote": "380 patients"},
        {"what": "features", "layer": "expression", "value": None, "values": [400, 350],
         "quote": "around 400 genes, but it might be fewer than 350"}]}, task, needs)
    menu = to_menu(slim)
    assert menu.features_one_type and menu.feature_count.values == [350, 400]
    decision = decide_menu(menu, task)
    assert decision.kind == "ASK" and "feature_count" in [q.dimension for q in decision.questions]


def test_a_claim_no_workflow_supports_declines_without_asking_anything_else():
    task = "Per patient, link methylation and expression and tell me which methylation changes causally drive it."
    slim = SlimReading(results=[ResultItem(quote="link methylation and expression", said="menu_result",
                                           value="multi_omic_network")],
                       data=[Stated(field="A3", name="methylation", value="has", quote="methylation"),
                             Stated(field="A3", name="expression", value="has", quote="expression")],
                       stated=[Stated(field="C2", name="claims", value="causal", quote="causally drive it")])
    decision = decide_menu(to_menu(slim), task)
    assert decision.kind == "DECLINE" and not decision.questions and decision.declined[0].reasons == ["claims=causal"]
