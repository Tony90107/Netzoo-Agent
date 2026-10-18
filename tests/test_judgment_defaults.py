"""Closed-menu judgment phase 0: the defaults table stays consistent with the capability sheet."""

from __future__ import annotations

import sys
from pathlib import Path

import itertools

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.judgment_defaults import DEFAULTS_PATH, load_defaults  # noqa: E402

WORKFLOWS = Path(__file__).parents[1] / "workflows"


def _write(tmp_path, change):
    data = yaml.safe_load(DEFAULTS_PATH.read_text(encoding="utf-8"))
    change(data)
    path = tmp_path / "defaults.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_every_produces_entry_is_in_exactly_one_artifact():
    table = load_defaults()
    produces = {key for key, item in sheet_entries().items() if item.kind == "produces"}
    assert set(table.by_entry) == produces


def test_no_intent_is_assumed():
    """User decision 2026-10-18: an unclear intent is asked, never guessed (compare: none mentioned is none asked)."""
    table = load_defaults()
    intents = {name: d for name, d in table.dimensions.items() if d.kind == "intent"}
    assert {"artifact", "granularity", "regulators", "layers"} <= set(intents)
    assert all(d.policy in ("ask", "extra", "no_filter") for d in intents.values())
    assert table.dimensions["artifact"].policy == "ask"


def test_every_result_is_in_one_question_group():
    table = load_defaults()
    grouped = [a for group in table.question_groups.values() for a in group.artifacts]
    assert sorted(grouped) == sorted(set(table.artifacts) - {"comparison"})


def test_asked_dimensions_have_user_facing_options():
    table = load_defaults()
    for name, dimension in table.dimensions.items():
        if dimension.kind == "intent" and dimension.policy == "ask" and name not in ("artifact", "layers"):
            assert set(dimension.options) == set(dimension.values), name


def test_extras_are_plain_when_never_mentioned():
    """Draft 4 (measured on 108 dev requests): miRNA regulators and comparisons are extras a user asks for."""
    table = load_defaults()
    assert (table.dimensions["regulators"].policy, table.dimensions["regulators"].value) == ("extra", "tf")
    assert (table.dimensions["compare"].policy, table.dimensions["compare"].value) == ("extra", "none")


def test_every_method_tie_is_offered_with_reasons():
    table = load_defaults()
    offered = [{option.workflow for option in options} for _, options in table.tie_options.values()]
    assert all(any(tie <= group for group in offered) for tie in table.method_ties)


def test_soft_requirement_share_is_the_users_nine_of_ten():
    assert load_defaults().soft_requirements_met == 0.9


def test_tie_options_are_shown_as_differences_for_the_question():
    """Draft 5: shown lines say how options differ and which need each serves; the logic stays internal."""
    table = load_defaults()
    otter = next(o for _, options in table.tie_options.values() for o in options if o.workflow == "OTTER")
    assert otter.difference and otter.good_for and otter.logic
    assert ("data_available", "coexpression_matrix") in otter.fits_when


def test_a_generic_network_implies_no_scale():
    """User decision 2026-10-18 (draft 3): "a network" says the result is a network, not one for every sample or layer."""
    table = load_defaults()
    assert table.dimensions["granularity"].policy == "ask"
    assert table.dimensions["integration"].policy == "ask"


# Spec section 3.9: the dimensions are complete (C1-C3) and none is idle (C4).

def _attributes(table, key):
    item = sheet_entries()[key]
    return {
        "artifact": table.by_entry[key], "granularity": item.granularity, "regulators": item.regulators,
        "signed": item.signed, "layers": item.layers, "input_network": item.input_network, "groups": item.groups,
        "compared": table.artifacts["comparison"].of.get(key),
    }


def test_c1_entries_of_different_workflows_are_told_apart_or_are_listed_ties():
    table = load_defaults()
    produces = sorted(key for key, item in sheet_entries().items() if item.kind == "produces")
    untold = set()
    for a, b in itertools.combinations(produces, 2):
        first, second = sheet_entries()[a], sheet_entries()[b]
        if first.workflow == second.workflow:
            continue
        left, right = _attributes(table, a), _attributes(table, b)
        assert set(left) == set(table.entry_attributes)
        if left == right:
            untold.add(frozenset({first.workflow, second.workflow}))
    assert untold <= set(table.method_ties), sorted(map(sorted, untold - set(table.method_ties)))


def test_c2_every_near_miss_and_registry_wide_entry_is_ruled_out_by_a_dimension():
    table = load_defaults()
    expected = {key for key, item in sheet_entries().items() if item.kind in ("near_miss", "registry_wide")}
    assert set(table.ruled_by) == expected


def test_c3_every_request_scope_limit_is_judged_by_a_dimension():
    table = load_defaults()
    limits = set()
    for path in WORKFLOWS.glob("*.yaml"):
        for check in yaml.safe_load(path.read_text(encoding="utf-8")).get("input_checks") or []:
            if check.get("scope") == "request":
                limits.add(str(check["limit"]).split(":")[0])
    assert limits and limits <= set(table.limit_fields)


def test_c4_every_dimension_serves_a_check_reads_a_condition_or_says_what_it_decides():
    table = load_defaults()
    used = {*table.entry_attributes.values(), *(name for name, _ in table.ruled_by.values()),
            *table.limit_fields.values()}
    idle = [name for name, d in table.dimensions.items() if name not in used and not d.condition and not d.serves]
    assert idle == []


def test_generic_words_expand_to_artifacts():
    table = load_defaults()
    assert "regulatory_network" in table.expand("network")
    assert table.expand("tf_activity") == ("tf_activity",)


def test_comparisons_name_the_result_they_compare():
    table = load_defaults()
    assert table.artifacts["comparison"].of["giraffe.activity_tests"] == "tf_activity"


def test_condition_defaults_are_values_of_their_condition():
    table = load_defaults()
    assert table.dimensions["data_unit"].value == "bulk_samples"
    assert table.dimensions["data_unit"].kind == "condition"


@pytest.mark.parametrize("change, message", [
    (lambda d: d["artifacts"]["tf_activity"]["entries"].append("panda.tf_gene_network"), "in both"),
    (lambda d: d["artifacts"]["tf_activity"].update(entries=[]), "in no artifact"),
    (lambda d: d["artifacts"]["tf_activity"]["entries"].append("giraffe.no_protein_level"), "unknown produces"),
    (lambda d: d["generic"].update(stuff=["no_such_artifact"]), "generic"),
    (lambda d: d["dimensions"]["granularity"]["not_stated"].update(policy="guess"), "unknown policy"),
    (lambda d: d["dimensions"]["data_unit"]["not_stated"].update(value="cells"), "is not one of"),
    (lambda d: d["dimensions"]["artifact"]["not_stated"].update(policy="no_filter"), "assume nothing"),
    (lambda d: d["dimensions"]["granularity"]["not_stated"].update(policy="default", value="aggregate"),
     "must not be assumed"),
    (lambda d: d["dimensions"]["regulators"]["not_stated"].update(plain="lncrna"), "plain value"),
    (lambda d: d["tie_options"]["per_sample_coexpression"]["options"]["BONOBO"].pop("good_for"), "misses a part"),
    (lambda d: d["tie_options"]["whole_cohort_tf_network"]["options"]["OTTER"].update(fits_when=["mood=good"]),
     "not a dimension"),
    (lambda d: d["tie_options"]["per_sample_coexpression"]["options"].pop("BONOBO"), "at least two"),
    (lambda d: d["tie_options"]["whole_cohort_targeting"]["options"].update(TIGER={}), "unknown"),
    (lambda d: d["thresholds"].update(soft_requirements_met=1.5), "soft_requirements_met"),
    (lambda d: d["dimensions"]["granularity"].update({"class": "wish"}), "unknown class"),
    (lambda d: d["question_groups"]["groups"]["artifacts"].append("tf_activity"), "already grouped"),
    (lambda d: d["question_groups"]["groups"]["artifacts"].remove("patient_subtypes"), "in no question group"),
    (lambda d: d["thresholds"].update(ask_max_options=1), "ask_max_options"),
    (lambda d: d["thresholds"].update(max_ask_rounds=0), "max_ask_rounds"),
    (lambda d: d["ruled_by"].update({"panda.no_sign": "signed=maybe"}), "not a dimension"),
    (lambda d: d["ruled_by"].update({"panda.no_sign": "colour=red"}), "not a dimension"),
    (lambda d: d["limit_fields"].update(min_samples="cohort_size"), "unknown dimensions"),
])
def test_an_inconsistent_table_fails_to_load(tmp_path, change, message):
    with pytest.raises(ValueError, match=message):
        load_defaults(_write(tmp_path, change))
