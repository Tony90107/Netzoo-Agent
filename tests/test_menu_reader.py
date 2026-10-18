"""Closed-menu judgment phase 1: the reader's contract (spec 2026-10-18, section 3.1).

No model calls: the strict wire schema, the menu it is shown, the sentences and numbers code lists for it, the
verbatim-quote check, and the code that turns a wire payload into the `MenuReading` that `decide_menu` reads.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CONDITIONS  # noqa: E402
from netzoo_agent_core.graph.menu_reading_call import build_menu_reading_messages, read_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_reader import (  # noqa: E402
    CONDITION_FIELDS, WANTED_FIELDS, menu_text, name_key, quote_in, reader_model, request_layout, to_menu_reading,
)
from netzoo_agent_core.judgment_defaults import judgment_defaults  # noqa: E402
from netzoo_agent_core.workflow_conditions import all_conditions  # noqa: E402

TABLE = judgment_defaults()
DATA = TABLE.dimensions["data_available"].values


def blank_said() -> dict:
    return {"quote": "", "status": "not_stated", "basis": None, "value": None, "values": []}


def said(value, quote, basis="explicit") -> dict:
    return {"quote": quote, "status": "stated", "basis": basis, "value": value, "values": []}


def doubt(values, quote, status="unsure") -> dict:
    return {"quote": quote, "status": status, "basis": None, "value": None, "values": list(values)}


def result(names="nothing", quote="", value=None, kind=None, values=(), outside="") -> dict:
    return {"quote": quote, "names": names, "value": value, "kind": kind, "values": list(values),
            "outside_name": outside}


def item(quote, form="asks", requirements=(), **fields) -> dict:
    return {"quote": quote, "form": form, "result": fields.pop("result", result()),
            "requirements": [{"quote": q, "about": about} for q, about in requirements],
            **{name: fields.get(name, blank_said()) for name in WANTED_FIELDS}}


def number(what="other", layer="unspecified", workflow="unspecified", control="unregistered", alternative=False,
           unit=""):
    return {"unit": unit, "what": what, "layer": layer, "workflow": workflow, "control": control,
            "alternative": alternative}


def sentence(doubt_quote="", about="none", values=(), workflow="unspecified", control="none") -> dict:
    return {"doubt": bool(doubt_quote), "quote": doubt_quote, "about": about, "workflow": workflow,
            "control": control, "values": list(values)}


def payload(task: str, *, data=None, numbers=None, sentences=None, conditions=None, roles=None, **fields) -> dict:
    """A wire payload for the task: every field blank unless given; numbers and sentences by position."""
    layout = request_layout(task)
    base = {
        "wanted": [], "groups": [], "settings": [], "unregistered_methods": [],
        "names": {name_key(name): {"role": (roles or {}).get(name, "target")} for name in layout.names},
        "claims": blank_said(), "delivery": blank_said(), "run_requested": {"quote": "", "value": False},
        "data": {name: {"quote": "", "status": "not_mentioned"} for name in DATA},
        "conditions": {name: blank_said() for name in CONDITION_FIELDS},
        "numbers": {f"n{i}": number() for i in range(1, len(layout.numbers) + 1)},
        "sentences": {f"s{i}": sentence() for i in range(1, len(layout.sentences) + 1)},
    }
    for name, (quote, status) in (data or {}).items():
        base["data"][name] = {"quote": quote, "status": status}
    base["numbers"].update(numbers or {})
    base["sentences"].update(sentences or {})
    base["conditions"].update(conditions or {})
    base.update(fields)
    reader_model(len(layout.sentences), len(layout.numbers), layout.names).model_validate(base)  # valid wire
    return base


def read(task: str, **fields):
    return to_menu_reading(payload(task, **fields), task)


# --- the schema, the menu and the layout ----------------------------------------------------------------------------

def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


@pytest.mark.parametrize("sentences, numbers", [(1, 0), (3, 2), (16, 16)])
def test_wire_schema_is_strict(sentences, numbers):
    schema = reader_model(sentences, numbers).model_json_schema()
    objects = [node for node in _walk(schema) if "properties" in node]
    assert len(objects) > 10
    for node in objects:
        assert set(node["required"]) == set(node["properties"]), node.get("title")
        assert node["additionalProperties"] is False, node.get("title")
    assert all("default" not in node for node in _walk(schema))
    defs = schema["$defs"]
    assert set(defs["SentencesWire"]["properties"]) == {f"s{i}" for i in range(1, sentences + 1)}
    assert set(defs["NumbersWire"]["properties"]) == {f"n{i}" for i in range(1, numbers + 1)}


def _enum_values(node, defs) -> int:
    """Enum values as OpenAI counts them for one schema: every occurrence, with each $ref expanded."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _enum_values(defs[node["$ref"].rsplit("/", 1)[1]], defs)
        return len(node.get("enum", ())) + sum(_enum_values(v, defs) for k, v in node.items() if k != "$defs")
    if isinstance(node, list):
        return sum(_enum_values(v, defs) for v in node)
    return 0


def test_wire_schema_stays_under_the_providers_enum_limit():
    """OpenAI strict mode takes at most 1000 enum values in one schema (d6: m3:U12 sent 1020 and was refused)."""
    from netzoo_agent_core.method_names import method_names
    schema = reader_model(16, 16, tuple(method_names())).model_json_schema()
    assert _enum_values(schema, schema["$defs"]) <= 1000


def test_a_number_or_doubt_naming_no_control_is_dropped_not_refused():
    task = "Run OTTER with lamda 0.4. I am not sure whether the gamma is 0.3 or 0.5."
    reading, report = read(task, numbers={"n1": number("setting", workflow="otter", control="lamda"),
                                          "n2": number("other"), "n3": number("other")},
                           sentences={"s2": sentence("I am not sure whether the gamma is 0.3 or 0.5", "setting",
                                                     ["0.3", "0.5"], workflow="OTTER", control="Gamma")})
    assert [(s.workflow, s.control, s.unsure) for s in reading.settings] == [("OTTER", "gamma", True)]
    assert any("'lamda' is no control" in line for line in report.dropped)


def test_wire_schema_offers_only_menu_values():
    enums = {tuple(node["enum"]) for node in _walk(reader_model(2, 2).model_json_schema()) if "enum" in node}
    assert tuple(TABLE.dimensions["artifact"].values) in enums
    assert tuple(DATA) not in enums  # data kinds are fields of their own, never a list to pick from
    for name in CONDITION_FIELDS:
        values = tuple(v for v in CONDITIONS[name][0] if v != "not_stated") if name in CONDITIONS \
            else TABLE.dimensions[name].values
        assert tuple(values) in enums, name


def test_menu_shows_every_result_workflow_control_and_off_menu_record():
    text = menu_text()
    for name in (*TABLE.dimensions["artifact"].values, *CONDITION_FIELDS, *DATA):
        assert f"- {name}" in text, name
    for workflow, conditions in all_conditions().items():
        assert f"- {workflow}" in text
        for control in conditions.settings:
            assert f"  - {control} (" in text, (workflow, control)
    assert "- LIONESS-PANDA: regulatory_network (per sample and cohort)" in text
    for label in ("claims=causal", "claims=prediction", "delivery=outside_netzoo", "result: off_menu_result",
                  "regulators=off_menu", "layers=three_or_more_jointly", "conditions.data_unit=single_cells",
                  "data.mutation_calls=lacks"):
        assert label in text
    # a near miss of one workflow is on the menu elsewhere, never shown as off it
    assert "granularity=per_sample" not in text and "signed=signed" not in text


def test_layout_lists_sentences_and_numbers():
    task = ("We have 2,000 genes in twelve samples, log2 at 1e-4. Run it on expr_t2d.tsv from the 10x run! "
            "One network, please.")
    layout = request_layout(task)
    assert len(layout.sentences) == 3
    assert [(n.text, n.value) for n in layout.numbers] == [("2,000", 2000), ("twelve", 12), ("1e-4", 0.0001)]
    assert all(quote_in(n.context, task) for n in layout.numbers)
    system, human = build_menu_reading_messages(task)
    assert "RESULTS ON THE MENU" in system.content
    assert "s3. One network, please." in human.content and 'n2 = twelve: "' in human.content


# --- verbatim quotes -----------------------------------------------------------------------------------------------

TASK = ("We have RNA-seq from 64 kidney biopsies and a TF motif prior. I’m not sure whether the samples are "
        "pooled cells or single cells. Build a separate network for each patient.")


@pytest.mark.parametrize("quote, found", [
    ("a separate network for each patient", True),
    ("A Separate  Network for each patient.", True),
    ("I'm not sure whether the samples are pooled cells", True),          # typographic apostrophe in the request
    ("RNA-seq from 64 kidney biopsies ... a TF motif prior", True),
    ("a TF motif prior ... RNA-seq from 64 kidney biopsies", False),      # fragments out of order
    ("a network for each patient", False),                                # words dropped from the middle
    ("one network for the whole cohort", False),
    ("", False), ("...", False),
])
def test_quote_in(quote, found):
    assert quote_in(quote, TASK) is found


# --- wire -> MenuReading -------------------------------------------------------------------------------------------

def test_unverified_words_state_nothing():
    reading, report = read(TASK, wanted=[item(
        "Build a separate network for each patient", result=result("kind_of_result", "network", kind="network"),
        granularity=said("per_sample", "one network per donor"))])
    assert reading.wanted[0].granularity.status == "not_stated"
    assert reading.wanted[0].artifact.value == "network"
    assert any("one network per donor" in line for line in report.dropped)


def test_stated_without_a_value_is_not_stated():
    reading, _ = read(TASK, wanted=[item("Build a separate network for each patient",
                                         granularity=said(None, "a separate network for each patient"))])
    assert reading.wanted[0].granularity.status == "not_stated"


def test_a_named_workflow_is_never_an_off_menu_result():
    task = "Run LIONESS-PANDA for the validated acorn RNA panel."
    reading, report = read(task, wanted=[item("Run LIONESS-PANDA for the validated acorn RNA panel",
                                              result=result("off_menu_result", "Run LIONESS-PANDA",
                                                            outside="LIONESS-PANDA"))])
    assert reading.wanted[0].artifact.status == "not_stated"
    assert any("off_menu_result" in line for line in report.dropped)
    only, _ = read(task, wanted=[item("Run LIONESS-PANDA", result=result("workflow_only", "Run LIONESS-PANDA"))])
    assert only.wanted[0].artifact.status == "not_stated"


def test_a_file_name_or_identifier_is_never_an_off_menu_result():
    task = "Can CONDOR analyze edges_release.tsv? Can OTTER take it as coexpression_file?"
    reading, _ = read(task, wanted=[
        item("Can CONDOR analyze edges_release.tsv?", result=result("off_menu_result", "analyze edges_release.tsv",
                                                                     outside="analyze edges_release.tsv")),
        item("Can OTTER take it as coexpression_file?", result=result("off_menu_result", "coexpression_file",
                                                                       outside="coexpression_file"))])
    assert [w.artifact.status for w in reading.wanted] == ["not_stated", "not_stated"]


def test_a_number_of_tables_is_no_sample_count():
    task = "Run DRAGON on the two cell-culture tables."
    reading, _ = read(task, numbers={"n1": number("layers_files_or_groups", unit="tables")})
    assert reading.sample_count.status == "not_stated"


def test_off_menu_needs_the_users_words_naming_the_result():
    task = "Call somatic SNVs from our BAM files and give me a filtered VCF."
    named, _ = read(task, wanted=[item("give me a filtered VCF", result=result(
        "off_menu_result", "give me a filtered VCF", outside="a filtered VCF"))])
    assert named.wanted[0].outside_name == "a filtered VCF"
    assert decide_menu(named, task).kind == "DECLINE"
    unnamed, report = read(task, wanted=[item("give me a filtered VCF", result=result(
        "off_menu_result", "annotated variants", outside="annotated variants"))])
    assert unnamed.wanted[0].artifact.status == "not_stated"
    assert decide_menu(unnamed, task).kind != "DECLINE"
    assert any("wanted[0].result" in line for line in report.dropped)


def test_results_named_as_a_menu_result_kind_or_doubt():
    task = "We want TF activity or TF targeting per patient, or maybe just a network."
    reading, _ = read(task, wanted=[
        item("TF activity or TF targeting per patient", result=result(
            "unsure_between_results", "TF activity or TF targeting", values=["tf_activity", "targeting_scores"])),
        item("just a network", result=result("kind_of_result", "a network", kind="network")),
        item("TF activity", result=result("menu_result", "TF activity", value="tf_activity"))])
    assert reading.wanted[0].artifact.status == "unsure"
    assert reading.wanted[0].artifact.values == ["tf_activity", "targeting_scores"]
    assert reading.wanted[1].artifact.value == "network" and reading.wanted[2].artifact.value == "tf_activity"


def test_data_kinds_have_lack_or_are_not_mentioned():
    task = "We have expression and a PPI network but no motif prior."
    reading, _ = read(task, data={"expression": ("expression", "has"), "ppi": ("a PPI network", "has"),
                                  "motif_prior": ("no motif prior", "lacks"),
                                  "mirna_prior": ("a miRNA prior", "lacks")})
    assert reading.data == ["expression", "ppi"] and reading.data_absent == ["motif_prior"]
    assert reading.only_data is False  # never read: a lack is said kind by kind


def test_numbers_become_counts_and_settings():
    task = ("We measured 300 miRNAs in 50 patients, and the protein data is either the 200-protein targeted panel or "
            "the 2,000-protein discovery panel. Use lam 0.4.")
    assert [n.text for n in request_layout(task).numbers] == ["300", "50", "200", "2,000", "0.4"]
    reading, _ = read(task, numbers={
        "n1": number("feature_count", "mirna_expression"), "n2": number("sample_count"),
        "n3": number("feature_count", "protein", alternative=True),
        "n4": number("feature_count", "protein", alternative=True),
        "n5": number("setting", workflow="OTTER", control="lam")})
    assert reading.sample_count.value == 50
    assert reading.feature_count.status == "conflicting" and reading.feature_count.values == [500, 2300]
    assert reading.single_feature_count is None
    assert [(s.workflow, s.control, s.value) for s in reading.settings] == [("OTTER", "lam", "0.4")]
    assert quote_in(reading.settings[0].quote, task)


def test_one_layer_count_is_the_single_feature_count_and_alternatives_conflict():
    task = "COBRA on 18,000 genes across two samples or twelve."
    reading, _ = read(task, numbers={"n1": number("feature_count", "expression"),
                                     "n2": number("sample_count", alternative=True),
                                     "n3": number("sample_count", alternative=True)})
    assert reading.single_feature_count == 18000 and reading.feature_count.value == 18000
    assert reading.sample_count.status == "conflicting" and reading.sample_count.values == [2, 12]


def test_numbers_in_a_doubt_sentence_are_alternatives():
    task = "Run LIONESS-PANDA on the acorn panel. I am waiting to learn whether it has two independent samples or five."
    reading, report = read(task, numbers={"n1": number("sample_count"), "n2": number("sample_count")},
                           sentences={"s2": sentence("I am waiting to learn", "other")})
    assert reading.sample_count.status == "conflicting" and reading.sample_count.values == [2, 5]
    plain, _ = read(task, numbers={"n1": number("sample_count"), "n2": number("sample_count")})
    assert plain.sample_count.status == "stated" and plain.sample_count.value == 5


def test_a_count_doubt_with_number_words():
    task = "Run LIONESS-PANDA on the acorn panel. I do not know whether it has two samples or five."
    reading, _ = read(task, numbers={"n1": number("sample_count"), "n2": number("sample_count")},
                      sentences={"s2": sentence("I do not know whether it has two samples or five", "sample_count",
                                                ["two", "five"])})
    assert reading.sample_count.status == "conflicting" and reading.sample_count.values == [2, 5]
    assert decide_menu(reading, task).kind == "ASK"


def test_one_control_given_two_values_is_unsure_between_them():
    task = "Can OTTER run with our approved lam setting? The note could be 0.3 or 3.0."
    reading, _ = read(task, numbers={"n1": number("setting", workflow="OTTER", control="lam"),
                                     "n2": number("setting", workflow="OTTER", control="lam")})
    assert [(s.control, s.unsure, s.values) for s in reading.settings] == [("lam", True, ["0.3", "3.0"])]
    decision = decide_menu(reading, task)
    assert decision.kind == "ASK" and decision.questions[0].dimension == "setting:OTTER.lam"


def test_a_question_naming_a_result_asks_for_it():
    task = "Can BONOBO output a cohort-level aggregate network directly? Which one should I run?"
    reading, _ = read(task, wanted=[
        item("Can BONOBO output a cohort-level aggregate network directly?",
             granularity=said("whole_cohort", "a cohort-level aggregate network")),
        item("Which one should I run?")])
    assert [w.form for w in reading.wanted] == ["deliverable", "question_to_us"]
    assert decide_menu(reading, task).kind == "DECLINE"


def test_a_choice_between_workflows_is_asked_as_the_goal():
    task = "Should I be using COBRA or CONDOR on our lupus nephritis cohort?"
    reading, _ = read(task, wanted=[item(task, result=result("choice_between_workflows", task))],
                      roles={"COBRA": "choice", "CONDOR": "choice"})
    assert reading.wanted[0].artifact.status == "not_stated" and reading.wanted[0].method_choice == [task]
    decision = decide_menu(reading, task)
    assert decision.kind == "CLARIFY"
    # the roles alone are the same evidence
    reading, report = read(task, wanted=[item(task, result=result("workflow_only", "COBRA"))],
                           roles={"COBRA": "choice", "CONDOR": "choice"})
    assert reading.wanted[0].method_choice == [task] and decide_menu(reading, task).kind == "CLARIFY"
    # one name found: still the goal, never that workflow's run
    one = "Should I use COBRA here, or something else?"
    reading, _ = read(one, wanted=[item(one, result=result("choice_between_workflows", one))])
    assert decide_menu(reading, one).kind == "CLARIFY"


def test_names_found_by_code_get_roles_and_background_ones_are_not_counted():
    task = "Run PANDA on expr_ipf.tsv with motif.tsv, ppi.tsv and the adjusted matrix from COBRA."
    reading, _ = read(task, wanted=[item("Run PANDA on expr_ipf.tsv", result=result("workflow_only", "Run PANDA"))],
                      roles={"PANDA": "target", "COBRA": "background"},
                      data={"expression": ("expr_ipf.tsv", "has"), "motif_prior": ("motif.tsv", "has"),
                            "ppi": ("ppi.tsv", "has")})
    assert reading.context_mentions == ["COBRA"]
    decision = decide_menu(reading, task)
    assert decision.kind == "DO" and decision.workflows == ["PANDA"]


def test_a_doubt_about_none_goes_to_the_one_field_its_values_fit():
    task = "We want a TF network. We have not decided whether per-sample TF activity or per-sample TF networks."
    reading, report = read(task, wanted=[item("We want a TF network", result=result(
        "menu_result", "a TF network", value="regulatory_network"))],
        sentences={"s2": sentence("We have not decided whether per-sample TF activity or per-sample TF networks",
                                  "none", ["tf_activity", "regulatory_network"])})
    assert reading.wanted[0].artifact.status == "unsure"
    assert any("the one field" in line for line in report.filled)


def test_an_unregistered_lioness_version_is_found_by_its_name():
    task = "Can registered OTTER produce a network per individual using LIONESS-OTTER, or LIONESS-PANDA?"
    reading, _ = read(task)
    assert reading.unregistered_methods == ["LIONESS-OTTER"]


def test_sentence_doubts_set_their_field():
    task = ("We have 3,000 columns from the core. I'm not sure whether those columns are single cells or pooled bulk "
            "samples. We want a TF-gene network for each column.")
    reading, _ = read(task, wanted=[item("a TF-gene network for each column", result=result(
        "menu_result", "TF-gene network", value="regulatory_network"),
        granularity=said("per_sample", "for each column"))],
        sentences={"s2": sentence("I'm not sure whether those columns are single cells or pooled bulk samples",
                                  "data_unit", ["single_cells", "bulk_samples"])})
    assert reading.conditions["data_unit"].status == "unsure"
    assert set(reading.conditions["data_unit"].values) == {"single_cells", "bulk_samples"}
    decision = decide_menu(reading, task)
    assert decision.kind == "ASK" and [q.dimension for q in decision.questions] == ["data_unit"]


def test_a_doubt_without_two_values_gets_the_menus_values_and_wrong_words_drop_it():
    task = "Build a network per patient or per group, I have not decided. We have 40 samples."
    reading, report = read(task, wanted=[item("Build a network", result=result("kind_of_result", "a network",
                                                                                kind="network"))],
                           sentences={"s1": sentence("I have not decided", "granularity", ["per_patient"]),
                                      "s2": sentence("we do not know the count", "sample_count", ["40", "80"])})
    assert reading.wanted[0].granularity.values == list(TABLE.dimensions["granularity"].values)
    assert report.filled and any("sentences.s2" in line for line in report.dropped)


def test_setting_and_file_doubts():
    task = ("Run BONOBO on expr.tsv; I can't tell whether the values were log-transformed. I am not sure which export "
            "coexp.tsv is.")
    reading, _ = read(task, sentences={
        "s1": sentence("I can't tell whether the values were log-transformed", "setting", ["true", "false"],
                       workflow="BONOBO", control="log_transformed"),
        "s2": sentence("I am not sure which export coexp.tsv is", "file_content")})
    assert reading.settings[0].unsure and reading.settings[0].values == ["true", "false"]
    assert reading.unsure_files == ["I am not sure which export coexp.tsv is"]


def test_requirements_kept_only_about_the_result():
    task = "Build the network with a p-value for every edge from our log-transformed, centered table saved as CSV."
    reading, _ = read(task, wanted=[item("Build the network", requirements=[
        ("with a p-value for every edge", "what_it_contains"), ("log-transformed, centered table", "data_property"),
        ("saved as CSV", "file_or_format"), ("Build the network", "another_result")])])
    assert [r.quote for r in reading.wanted[0].requirements] == ["with a p-value for every edge"]


def test_settings_background_and_unregistered_methods():
    task = ("Run OTTER with edge-list output on the matrix from our earlier LIONESS run, or TIGER if OTTER cannot; "
            "maybe use PANDA instead.")
    reading, _ = read(task, settings=[
        {"quote": "edge-list output", "workflow": "OTTER", "control": "output_format", "value": "edge_list",
         "asks_to_set": True},
        {"quote": "not in the request", "workflow": "unspecified", "control": "gamma", "value": "2", "asks_to_set": True},
        {"quote": "the matrix from our earlier LIONESS run", "workflow": "OTTER", "control": "unregistered",
         "value": "", "asks_to_set": False}],
        roles={"LIONESS": "background", "OTTER": "target", "PANDA": "choice"}, unregistered_methods=["TIGER", "PANDA"])
    assert [(s.workflow, s.control, s.value) for s in reading.settings] == [("OTTER", "output_format", "edge_list")]
    assert reading.context_mentions == ["LIONESS"]          # the one name typed background
    assert reading.unregistered_methods == ["TIGER"]        # PANDA is registered
    assert reading.named_workflows is None                  # code counts names from the words


def test_a_result_without_words_rests_on_the_items_words():
    task = "We have expression. We want subtypes from pathway mutation scores."
    reading, report = read(task, wanted=[item("We want subtypes from pathway mutation scores.", result=result(
        "menu_result", "", value="patient_subtypes"))])
    assert reading.wanted[0].artifact.value == "patient_subtypes"
    assert reading.wanted[0].artifact.quotes == ["We want subtypes from pathway mutation scores."]


def test_a_doubt_with_a_control_is_about_that_setting():
    task = "Run OTTER on our files. I have not checked whether CPU is allowed or GPU is mandatory."
    reading, _ = read(task, settings=[{"quote": "I have not checked whether CPU is allowed or GPU is mandatory",
                                       "workflow": "OTTER", "control": "computing", "value": "unspecified",
                                       "asks_to_set": True}],
                      sentences={"s2": sentence("I have not checked whether CPU is allowed or GPU is mandatory",
                                                "none", ["cpu", "gpu"], workflow="OTTER", control="computing")})
    assert [(s.control, s.unsure, s.values) for s in reading.settings] == [("computing", True, ["cpu", "gpu"])]


def test_an_item_with_no_words_from_the_request_is_dropped():
    reading, report = read(TASK, wanted=[item("a cohort network for everything", result=result(
        "kind_of_result", "cohort network", kind="network"))])
    assert reading.wanted == [] and any("item dropped" in line for line in report.dropped)


def test_conditions_and_flags_need_words():
    task = "Only the expression matrix is available; run it now on our 12 single cells."
    reading, _ = read(task, conditions={"data_unit": said("single_cells", "single cells")},
                      run_requested={"quote": "start immediately", "value": True})
    assert reading.conditions["data_unit"].value == "single_cells" and not reading.run_requested


def test_a_failed_call_is_a_failed_reading():
    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    read_ = read_menu("Run PANDA on expr.tsv", Broken())
    assert read_.reading.status == "failed" and "provider down" in read_.error
    assert decide_menu(read_.reading, "Run PANDA on expr.tsv").kind == "UNCHECKED"


def test_a_decoded_call_is_checked_and_converted():
    task = "Run PANDA on expr.tsv with motif.txt and ppi.txt."
    data = payload(task, wanted=[item("Run PANDA on expr.tsv", result=result("workflow_only", "Run PANDA"))],
                   data={"expression": ("expr.tsv", "has"), "motif_prior": ("motif.txt", "has"),
                         "ppi": ("ppi.txt", "has")},
                   run_requested={"quote": "Run PANDA", "value": True})

    class Model:
        def with_structured_output(self, schema, **kwargs):
            assert kwargs == {"method": "function_calling", "include_raw": True, "strict": True}
            defs = schema.model_json_schema()["$defs"]
            assert set(defs["SentencesWire"]["properties"]) == {"s1"} and set(defs["NamesWire"]["properties"]) == {
                "PANDA"}
            return type("Adapter", (), {"invoke": lambda self, messages: {
                "parsed": schema.model_validate(data), "raw": None}})()

    read_ = read_menu(task, Model())
    assert read_.reading.status == "read" and read_.reading.data == ["expression", "motif_prior", "ppi"]
    decision = decide_menu(read_.reading, task)
    assert decision.kind == "DO" and decision.workflows == ["PANDA"]


def test_every_sheet_off_menu_value_is_a_schema_value():
    """What the menu says records an off-menu request can be written in the schema."""
    schema = str(reader_model(1, 0).model_json_schema())
    for key, (dimension, value) in TABLE.ruled_by.items():
        if key in sheet_entries() and value in TABLE.dimensions[dimension].off_menu and dimension not in (
                "data_available", "artifact"):
            assert f"'{value}'" in schema, (key, dimension, value)
    assert "'off_menu_result'" in schema
