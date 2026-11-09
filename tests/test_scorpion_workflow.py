"""SCORPION (kuijjerlab/SCORPION, 2026-11-08): single-cell PANDA networks per group of cells, and where it is routed.

Single cells go to SCORPION alone; bulk samples never see it. The toy bundle is SCORPION's own `scorpionTest`
(300 genes x 1,954 colorectal cancer cells, 3 donors x 3 regions) as a 10x directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scorpion_io  # noqa: E402
from netzoo_agent_core.capability_sheet import sheet_entries, takes_unit  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.data.scorpion import inspect_scorpion_inputs_impl  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.data_unit import (  # noqa: E402
    BULK_EXPRESSION_ACTIONS, excluded_actions, scoped_capabilities, single_cell_request,
)
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, ALL_OUTPUT_CAPABILITIES, OUTPUT_CAPABILITIES  # noqa: E402

TOY = ROOT / "data" / "scorpion-toy"
MATRIX, MOTIF, PPI, META = TOY / "counts_10x", TOY / "motif_prior.tsv", TOY / "ppi.tsv", TOY / "cell_metadata.tsv"


def _network_reading(granularity="aggregate"):
    return [OutcomeHypothesis(confidence=.9, outcome=RequestedOutcome(
        operation="infer", artifact_type="regulatory_network", granularity=granularity,
        regulator_types=["tf"], target_types=["gene"], entity_types=["tf", "gene"]))]


# --- input contract --------------------------------------------------------------------------------------------------

def test_the_toy_10x_directory_is_read_without_loading_values():
    matrix = scorpion_io.scan_cell_matrix(MATRIX)
    assert (matrix.layout, len(matrix.genes), len(matrix.cells), matrix.whole_numbers) == ("mtx", 300, 1954, True)
    assert not matrix.errors


def test_a_dense_table_is_read_and_its_values_checked(tmp_path):
    table = tmp_path / "cells.tsv"
    cells = [f"c{i}" for i in range(40)]
    table.write_text("gene\t" + "\t".join(cells) + "\n" + "".join(
        f"G{g}\t" + "\t".join(str((g + i) % 5) for i in range(40)) + "\n" for g in range(12)))
    matrix = scorpion_io.scan_cell_matrix(table)
    assert (matrix.layout, len(matrix.genes), len(matrix.cells), matrix.whole_numbers) == ("text", 12, 40, True)
    bad = tmp_path / "bad.tsv"
    bad.write_text("gene\t" + "\t".join(cells) + "\n" + "".join(
        f"G{g}\t" + "\t".join("-1" for _ in range(40)) + "\n" for g in range(12)))
    assert any("non-negative" in error for error in scorpion_io.scan_cell_matrix(bad).errors)


def test_h5ad_and_too_few_cells_are_refused_with_the_reason(tmp_path):
    h5ad = tmp_path / "data.h5ad"
    h5ad.write_bytes(b"\x89HDF")
    assert "10x Matrix Market directory" in scorpion_io.scan_cell_matrix(h5ad).errors[0]
    small = tmp_path / "small.tsv"
    small.write_text("gene\ta\tb\tc\n" + "".join(f"G{g}\t1\t2\t3\n" for g in range(12)))
    assert any("at least 30" in error for error in scorpion_io.scan_cell_matrix(small).errors)


def test_the_toy_bundle_passes_with_groups_and_a_comparison():
    report, ok = inspect_scorpion_inputs_impl(str(MATRIX), str(MOTIF), str(PPI), {
        "cell_metadata_file": str(META), "group_by": ["donor", "region"],
        "compare_by": "region", "group1": "T", "group2": "N"})
    assert ok, report
    assert "networks: 9 of 9 groups have at least 30 cells" in report
    assert "region=T (3 networks) vs region=N (3 networks)" in report


def test_a_comparison_without_replicates_is_refused_before_anything_runs():
    report, ok = inspect_scorpion_inputs_impl(str(MATRIX), str(MOTIF), str(PPI), {
        "cell_metadata_file": str(META), "group_by": ["region"],
        "compare_by": "region", "group1": "T", "group2": "N"})
    assert not ok
    assert "add a replicate column such as a donor or sample column to group_by" in report


def test_a_motif_in_another_namespace_is_refused(tmp_path):
    motif = tmp_path / "motif.tsv"
    motif.write_text("".join(f"TF{i}\tENSG{i:011d}\t1\n" for i in range(20)))
    report, ok = inspect_scorpion_inputs_impl(str(MATRIX), str(motif), str(PPI))
    assert not ok and "same identifiers" in report


def test_paired_networks_are_matched_on_the_other_group_values():
    built = ["P31--T", "P31--N", "P32--T", "P32--N", "P33--T"]
    plan = scorpion_io.comparison_plan(built, {"group_by": ["donor", "region"], "compare_by": "region",
                                               "group1": "T", "group2": "N", "paired": True})
    assert (plan.group1, plan.group2, plan.errors) == (["P31--T", "P32--T"], ["P31--N", "P32--N"], [])


# --- registry and routing -------------------------------------------------------------------------------------------

def test_policy_and_registry_agree_and_scorpion_hands_off_to_porcupine():
    policy = ProjectPolicyLoader(ROOT).load()
    spec, definition = policy.workflows["run_scorpion"], ACTION_DEFINITIONS["run_scorpion"]
    assert spec.required_inputs == list(definition.required_inputs)
    assert [control.name for control in spec.controls] == [control.name for control in definition.controls]
    assert spec.output_capability.handoff_targets == ["run_porcupine"]


def test_bulk_routing_never_iterates_scorpion_but_a_lookup_finds_it():
    assert "run_scorpion" not in list(OUTPUT_CAPABILITIES) and "run_scorpion" in OUTPUT_CAPABILITIES
    assert OUTPUT_CAPABILITIES["run_scorpion"] is ALL_OUTPUT_CAPABILITIES["run_scorpion"]
    assert len(OUTPUT_CAPABILITIES) == len(ALL_OUTPUT_CAPABILITIES) - 1


@pytest.mark.parametrize("task,single", [
    ("We have scRNA-seq counts from 12 donors.", True),
    ("Our 10x single-cell data from tumour biopsies.", True),
    ("單細胞 RNA 定序資料", True),
    ("Run SCORPION on my counts.", True),
    ("We summed the single cells into pseudo-bulk profiles per donor.", False),
    ("This is bulk RNA-seq, not single-cell data.", False),
    ("Expression from 50 kidney biopsies.", False),
    ("RNA-seq of a single cell line under 6 treatments.", False),
    ("We now have 10x more samples than last year.", False),
    ("Counts from a 10x Chromium run of PBMCs.", True),
])
def test_the_data_unit_is_read_from_the_requests_own_words(task, single):
    assert single_cell_request(task) is single


def test_single_cells_are_matched_to_scorpion_and_bulk_samples_never_are():
    cells = "Infer TF-gene regulatory networks from our single-cell RNA-seq data."
    match = match_semantic_request(cells, _network_reading(), request_mode="guidance")
    assert set(match.matched_actions + match.hypothesis_actions) == {"run_scorpion"}
    bulk = "Infer TF-gene regulatory networks from our bulk RNA-seq data."
    match = match_semantic_request(bulk, _network_reading(), request_mode="guidance")
    assert "run_scorpion" not in match.matched_actions + match.hypothesis_actions
    assert set(scoped_capabilities(cells, OUTPUT_CAPABILITIES)).isdisjoint(BULK_EXPRESSION_ACTIONS)
    assert excluded_actions(bulk) == {"run_scorpion"}


def test_a_bulk_workflow_named_for_single_cells_is_not_selected_by_its_name():
    task = "Run PANDA on my scRNA-seq counts."
    match = match_semantic_request(task, _network_reading(), request_mode="execute")
    assert "run_panda" not in match.matched_actions


def test_the_sheet_credits_single_cells_only_to_scorpion():
    known = sheet_entries()
    assert takes_unit(known["scorpion.per_group_networks"], "single_cells")
    assert not takes_unit(known["scorpion.per_group_networks"], "not_stated")
    assert not takes_unit(known["panda.tf_gene_network"], "single_cells")
    assert takes_unit(known["porcupine.heterogeneous_pathways"], "single_cells")  # it reads SCORPION's networks


def test_a_network_for_each_cell_is_declined_not_given_to_scorpion():
    from netzoo_agent_core.contracts.menu_reading import MenuReading, Said, Wanted
    from netzoo_agent_core.interpretation.menu_decision import decide_menu

    def said(value, quote=""):
        return Said(status="stated", value=value, basis="explicit", quotes=[quote or value])
    reading = MenuReading(wanted=[Wanted(quote="a TF-gene network for each of our 3,000 single cells",
                                         artifact=said("regulatory_network"), granularity=said("per_sample"),
                                         regulators=said("tf"))],
                          conditions={"data_unit": said("single_cells", "single cells")},
                          data=["expression", "motif_prior", "ppi"])
    assert decide_menu(reading, "We want a TF-gene network for each of our 3,000 single cells.").kind == "DECLINE"
    per_donor = reading.model_copy(update={"wanted": [Wanted(quote="one TF-gene network per donor",
                                                             artifact=said("regulatory_network"),
                                                             granularity=said("per_group"), regulators=said("tf"))]})
    decision = decide_menu(per_donor, "From our single-cell data, one TF-gene network per donor.")
    assert decision.kind != "DECLINE" and "SCORPION" in decision.workflows


@pytest.mark.parametrize("task,per_cell", [
    ("a TF-gene network for each of our 3,000 single cells", True),
    ("one network per cell", True),
    ("one network per cell type", False),
    ("a network for each cell state", False),
    ("每個細胞類型一個網路", False),
])
def test_a_network_per_cell_is_told_from_one_per_cell_type(task, per_cell):
    import re
    from workflow_registry import PER_CELL_WITNESS
    assert bool(re.search(PER_CELL_WITNESS, task, re.I)) is per_cell


def test_list_and_mixed_case_controls_are_read_from_the_request():
    from netzoo_agent_core.interpretation.request_parameters import extract_explicit_workflow_controls

    task = ("Run SCORPION with group_by=donor,region compare_by=region group1=T group2=N assoc_method=pcNet "
            "paired=true gamma_value=5.")
    assert extract_explicit_workflow_controls(task, "run_scorpion") == {
        "group_by": ["donor", "region"], "compare_by": "region", "group1": "T", "group2": "N",
        "assoc_method": "pcNet", "paired": True, "gamma_value": 5.0}
    assert extract_explicit_workflow_controls('group_by=["cell_type"]', "run_scorpion") == {"group_by": ["cell_type"]}
    assert extract_explicit_workflow_controls("tf_names=SOX2,MYC", "build_priors") == {}


def test_control_assignments_are_not_words_to_read_again():
    from netzoo_agent_core.interpretation.reread import _covered

    task = "Run SCORPION on my counts group_by=donor,region compare_by=region group1=T group2=N then upload it."
    check = type("Check", (), {"requirements": [type("R", (), {"quote": "Run SCORPION on my counts"})()]})()
    covered = _covered(task, check)
    unread = "".join(char if not flag else "_" for char, flag in zip(task, covered))
    assert "group_by" not in unread and "group2" not in unread and "then upload it" in unread


def test_a_directory_input_stops_before_the_next_words():
    from netzoo_agent_core.routing.discovery import _extract_explicit_role_path

    task = ("Run SCORPION on cell_expression_file=data/scorpion-toy/counts_10x with "
            "motif_file=data/scorpion-toy/motif_prior.tsv ppi_file=data/scorpion-toy/ppi.tsv.")
    assert _extract_explicit_role_path(task, "cell_expression_file") == "data/scorpion-toy/counts_10x"
    assert _extract_explicit_role_path(task, "motif_file") == "data/scorpion-toy/motif_prior.tsv"
    spaced = "Use expression_file=/Users/me/LLM AGENT/data/expr.tsv for PANDA."
    assert _extract_explicit_role_path(spaced, "expression_file") == "/Users/me/LLM AGENT/data/expr.tsv"


def test_a_directory_input_is_fingerprinted_for_the_execute_gate(tmp_path):
    from types import SimpleNamespace

    from netzoo_agent_core.data.artifact_revision import preview_check

    directory = tmp_path / "counts_10x"
    directory.mkdir()
    (directory / "matrix.mtx").write_text("a")
    files = {name: tmp_path / name for name in ("motif.tsv", "ppi.tsv")}
    for path in files.values():
        path.write_text("x")
    decision = SimpleNamespace(cell_expression_file=str(directory), motif_file=str(files["motif.tsv"]),
                               ppi_file=str(files["ppi.tsv"]), cell_metadata_file=None, output_dir=str(tmp_path / "o"))
    shown, problem = preview_check("run_scorpion", decision, None, None)
    assert str(directory) in shown and problem is None
    assert preview_check("run_scorpion", decision, None, shown)[1] is None
    (directory / "matrix.mtx").write_text("b")
    assert "changed after the preview" in preview_check("run_scorpion", decision, None, shown)[1]
