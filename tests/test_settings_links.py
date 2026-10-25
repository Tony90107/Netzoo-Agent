"""ROUND-26 2a, with ROUND-27 B1's changes: candidates, verification, the asymmetric merge, and the guard."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.settings_links import (  # noqa: E402
    guarded_links, held_core, link_workflows, links_model, merged_reading, reading_doubts, verified_links,
    without_emptier,
)

TASK = ("With BONOBO, I'd like per-sample co-expression networks for 14 muscle biopsies (log2-transformed, "
        "mean-centered per gene). Please keep the full matrices and save a p-value matrix for every sample.")
MODE_WORDS = "keep the full matrices and save a p-value matrix for every sample"


def _read(workflows, **fields):
    model = links_model(tuple(workflows))
    values = {name: ("not_stated" if name.endswith("__output_mode") else False if name.endswith("_unsure") else "")
              for name in model.model_fields}
    return model(**{**values, **fields})


def _reading(*asks, settings=(), **conditions):
    return {"s1": {"role": "asks", "has": [], "about_methods": [], "asks": list(asks)},
            "conditions": {"settings": list(settings), **conditions}}


def _ask(quote, settings=(), delivered_by=(), named="none"):
    return {"quote": quote, "settings": list(settings), "delivered_by": list(delivered_by), "named_method": named}


def test_candidates_are_the_credited_workflows_only():
    reading = _reading(_ask("per-sample co-expression networks", delivered_by=["bonobo.per_sample_networks"]),
                       _ask("a regulatory network", delivered_by=["panda.tf_gene_network"], named="OTTER"),
                       named_method="none")
    # B1 change 1: OTTER, named in the request and as the ask's method but credited nowhere, is no candidate
    assert link_workflows("Run PUMA and GIRAFFE, then OTTER.", reading) == ["BONOBO", "PANDA"]


def test_free_text_settings_are_never_linked():
    assert "BONOBO__sample_names_words" not in links_model(("BONOBO",)).model_fields
    assert "BONOBO__sparsify_unsure" in links_model(("BONOBO",)).model_fields


def test_a_link_needs_its_words_in_the_request_and_a_number_for_a_number():
    read = _read(["BONOBO"], BONOBO__delta_words="delta at 0.4", BONOBO__bonobo_confidence_words="confidence",
                 BONOBO__bonobo_confidence_value_words="confidence", BONOBO__sparsify_words="sparsify it")
    links, empty = verified_links("Please sparsify with confidence 0.05.", ["BONOBO"], read)
    assert [(link["name"], link["value_quote"]) for link in links] == [("BONOBO.bonobo_confidence", "")]
    assert "BONOBO.save_pvals" in empty and "BONOBO.delta" not in empty  # unplaced words are not "left empty"


def test_a_mode_turns_on_its_controls_named_by_its_words():
    read = _read(["BONOBO"], BONOBO__output_mode="mode_3", BONOBO__output_mode_words=MODE_WORDS)
    links, _empty = verified_links(TASK, ["BONOBO"], read)
    assert sorted((link["name"], link["quote"], link["value_quote"]) for link in links) == [
        ("BONOBO.save_pvals", MODE_WORDS, ""), ("BONOBO.sparsify", MODE_WORDS, "")]
    off = "Do not keep the full matrices."
    read = _read(["BONOBO"], BONOBO__output_mode="mode_3", BONOBO__output_mode_words=off)
    assert verified_links(off, ["BONOBO"], read)[0] == []  # words that read as off name nothing on


def test_no_link_over_words_the_reading_found_the_user_unsure_of():
    task = "I can't tell whether the values were log-transformed before centering."
    reading = _reading(unknown_facts=[{"quote": "I can't tell whether the values were log-transformed"}])
    read = _read(["BONOBO"], BONOBO__log_transformed_words="I can't tell whether the values were log-transformed")
    assert verified_links(task, ["BONOBO"], read, reading_doubts(task, reading))[0] == []
    assert verified_links(task, ["BONOBO"], read)[0]  # without the doubt it would link


def test_a_mode_replaces_the_readings_other_setting_over_its_words():
    reading = _reading(_ask("Please keep the full matrices", named="BONOBO", settings=[
        {"name": "BONOBO.keep_in_memory", "quote": "keep the full matrices", "value_quote": ""},
        {"name": "BONOBO.save_pvals", "quote": "save a p-value matrix", "value_quote": ""}]))
    read = _read(["BONOBO"], BONOBO__output_mode="mode_3", BONOBO__output_mode_words=MODE_WORDS)
    links, empty = verified_links(TASK, ["BONOBO"], read)
    merged = merged_reading(TASK, reading, links, empty)
    assert merged["s1"]["asks"][0]["settings"] == []
    assert [item["name"] for item in merged["conditions"]["settings"]] == ["BONOBO.sparsify", "BONOBO.save_pvals"]
    assert reading["s1"]["asks"][0]["settings"]  # the reading itself is not changed


def test_a_plain_link_to_another_setting_removes_nothing_and_an_empty_field_removes_nothing():
    reading = _reading(settings=[
        {"name": "BONOBO.log_transformed", "quote": "log2-transformed", "value_quote": ""},
        {"name": "unregistered", "quote": "per-sample co-expression networks", "value_quote": ""}])
    read = _read(["BONOBO"], BONOBO__centered_words="log2-transformed, mean-centered per gene")
    links, empty = verified_links(TASK, ["BONOBO"], read)
    merged = merged_reading(TASK, reading, links, empty)
    assert [item["name"] for item in merged["conditions"]["settings"]] == [
        "BONOBO.log_transformed", "unregistered", "BONOBO.centered"]
    assert merged_reading(TASK, reading, [], {"BONOBO.log_transformed"}) == reading


def test_the_same_setting_or_an_unregistered_one_over_the_same_words_is_replaced():
    task = "For BONOBO, please sparsify at confidence 0.05."
    reading = _reading(settings=[{"name": "BONOBO.sparsify", "quote": "sparsify at confidence 0.05",
                                  "value_quote": "0.05"},
                                 {"name": "unregistered", "quote": "confidence 0.05", "value_quote": "0.05"}])
    read = _read(["BONOBO"], BONOBO__sparsify_words="sparsify", BONOBO__bonobo_confidence_words="confidence 0.05",
                 BONOBO__bonobo_confidence_value_words="0.05")
    links, empty = verified_links(task, ["BONOBO"], read)
    merged = merged_reading(task, reading, links, empty, add=False)
    assert merged["conditions"]["settings"] == []
    merged = merged_reading(task, reading, links, empty)
    assert [(item["name"], item["value_quote"]) for item in merged["conditions"]["settings"]] == [
        ("BONOBO.sparsify", ""), ("BONOBO.bonobo_confidence", "0.05")]


def test_version_two_request_settings_are_scoped_to_every_result():
    reading = _reading(sample_counts=[])
    read = _read(["BONOBO"], BONOBO__genes_axis_words="genes on rows", BONOBO__genes_axis_value_words="rows")
    task = "BONOBO on my table with genes on rows."
    links, empty = verified_links(task, ["BONOBO"], read)
    (item,) = merged_reading(task, reading, links, empty)["conditions"]["settings"]
    assert item == {"name": "BONOBO.genes_axis", "quote": "genes on rows", "value_quote": "rows", "applies_to": None}


def test_the_read_is_off_by_default(monkeypatch):
    from netzoo_agent_core.graph.settings_links_call import apply_settings_links

    monkeypatch.delenv("NETZOO_SETTINGS_LINKS", raising=False)
    proposal = object()
    assert apply_settings_links(None, {}, TASK, proposal, "usage", [], None)[0] is proposal


def test_an_unsure_link_is_held_not_merged():
    task = "Run BONOBO; the lab has not confirmed whether sparsify should be on."
    read = _read(["BONOBO"], BONOBO__sparsify_words="sparsify", BONOBO__sparsify_unsure=True)
    links, empty = verified_links(task, ["BONOBO"], read)
    kept, held = guarded_links(task, _reading(), links, empty, lambda reading: None)
    assert kept == [] and [(link["name"], link["reason"]) for link in held] == [("BONOBO.sparsify", "unsure")]


def test_an_empty_link_never_replaces_a_valued_item_for_the_same_setting():
    task = "BONOBO should write each matrix as a .parquet file."
    reading = _reading(settings=[{"name": "BONOBO.bonobo_output_format", "quote": "as a .parquet file",
                                  "value_quote": ".parquet"}])
    read = _read(["BONOBO"], BONOBO__bonobo_output_format_words="as a .parquet file")
    links, _empty = verified_links(task, ["BONOBO"], read)
    assert links and without_emptier(task, reading, links) == []


class _Row:
    def __init__(self, limits):
        self.limits, self.violations = limits, []


class _Check:
    def __init__(self, limits):
        self.requirements = [_Row(limits)]


def test_a_link_whose_merge_adds_a_limit_is_held_with_the_new_limit_as_its_reason():
    task = "For BONOBO, sparsify the networks and set delta to 0.5; genes on rows."
    read = _read(["BONOBO"], BONOBO__delta_words="delta to 0.5", BONOBO__delta_value_words="0.5",
                 BONOBO__genes_axis_words="genes on rows", BONOBO__genes_axis_value_words="rows")
    links, empty = verified_links(task, ["BONOBO"], read)

    def build(reading):  # the delta link alone adds a limit
        names = {item["name"] for item in reading["conditions"]["settings"]}
        return _Check(["BONOBO: delta must be below 1/3"] if "BONOBO.delta" in names else [])

    kept, held = guarded_links(task, _reading(), links, empty, build)
    assert [link["name"] for link in kept] == ["BONOBO.genes_axis"]
    assert [(link["name"], link["reason"]) for link in held] == [("BONOBO.delta", "BONOBO: delta must be below 1/3")]


def test_held_links_turn_only_a_do_into_an_ask():
    from netzoo_agent_core.contracts.core_decision import CoreDecision
    held = [{"name": "BONOBO.delta", "quote": "delta to 0.5", "value_quote": "0.5", "workflow": "BONOBO",
             "reason": "BONOBO: delta must be below 1/3"}]
    do = CoreDecision(kind="DO", basis="run", workflows=["BONOBO"], run_allowed=True)
    asked = held_core(do, held)
    assert asked.kind == "ASK" and asked.basis == "setting_link_fact"
    assert asked.facts[0].question == "Did you mean BONOBO's delta = \"0.5\"? BONOBO: delta must be below 1/3."
    declined = CoreDecision(kind="DECLINE", basis="x")
    assert held_core(declined, held) is declined and held_core(do, []) is do
