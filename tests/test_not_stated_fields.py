"""2026-10-22 (user decision): group_membership and input_network say "not stated" apart from a stated value.

Held-out h5 Q26 ("split the tumors into somewhere between 2 and 5 subtypes") typed several_groups, the only grouping
value besides one_group, and SAMBAR was refused; input_network "none" was the only answer when a request said nothing
about a network, and code reads it as "the user has none" (R22-A)."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import _ask_model, proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _fitting, _with_conditions  # noqa: E402

_ASK = dict(scale="unstated", omics_layers=0, data_unit="not_stated", regulator_kinds=[], needs_sign=False,
            input_network="none", group_membership="not_about_groups", time_model="not_dynamic", spatial="not_spatial",
            samples_matched="not_stated", mutation_origin="not_stated", value_type="not_stated",
            mirna_driver="not_stated", _method={})


def _ask(**changes):
    return SimpleNamespace(**{**_ASK, **changes})


def test_the_reading_schema_offers_not_stated_for_both_fields():
    schema = proposal_model(1).model_json_schema()
    ask = schema["$defs"][schema["properties"]["s1"]["$ref"].split("/")[-1]]["properties"]["asks"]["items"]
    ask = schema["$defs"][ask["$ref"].split("/")[-1]]["properties"]
    assert "not_stated" in ask["group_membership"]["enum"]
    assert "not_stated" in ask["input_network"]["enum"]


def test_unstated_overlap_keeps_a_grouping_result_and_stated_overlap_still_rules_it_out():
    keys = ["sambar.subtypes", "condor.communities"]
    assert _fitting(keys, _ask(group_membership="not_stated")) == keys
    assert _fitting(keys, _ask(group_membership="one_group")) == keys
    assert _fitting(keys, _ask(group_membership="several_groups")) == []


def test_an_unstated_network_keeps_condor_and_a_stated_gene_gene_network_does_not():
    keys = ["condor.communities"]
    assert _fitting(keys, _ask(input_network="not_stated")) == keys
    assert _fitting(keys, _ask(input_network="none")) == keys
    assert _fitting(keys, _ask(input_network="gene_gene")) == []


def test_a_verified_overlap_condition_applies_to_an_ask_that_does_not_say():
    ask = _ask_model().model_validate({
        **{name: value for name, value in _ASK.items() if not name.startswith("_") and name != "samples_matched"},
        "group_membership": "not_stated", "quote": "communities", "delivered_by": [], "not_by": [],
        "asked_as": "request", "adds": [], "named_method": "none", "named_method_quote": "", "settings": [],
        "sample_count": None, "sample_count_quote": "", "feature_counts": []})
    assert _with_conditions(ask, {"group_membership": "several_groups"}).group_membership == "several_groups"
