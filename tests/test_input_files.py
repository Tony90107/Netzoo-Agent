"""M2 C (2026-10-14): the files a request names are the ones used, and shipped toy data never stands in for them.

Final acceptance a24b: 18 of the 24 runs that reached the input gate offered or filled in the repository's toy or
fixture datasets -- for P21's `yeast_stress_logc.tsv`, P16's two DRAGON layers, P24's edge list and P33's missing
`/proj/mac/priors`, and P19 ("endometrial" read as a demo request) was filled with `dragon-toy`. AGENTS.md: a real
analysis never takes toy data because it is in the workspace.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.data.discovery import SHIPPED_DATA_DIRECTORIES, is_shipped_data  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings  # noqa: E402
from netzoo_agent_core.presentation import _is_demo_request  # noqa: E402


def test_the_shipped_data_list_is_every_tracked_data_folder():
    tracked = subprocess.run(["git", "ls-files", "data"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    folders = {line.split("/")[1] for line in tracked.splitlines() if line.count("/") >= 2}
    assert folders == SHIPPED_DATA_DIRECTORIES
    assert is_shipped_data("data/dragon-toy/layer1.tsv") and not is_shipped_data("data/my-cohort/expr.tsv")


@pytest.mark.parametrize(("task", "demo"), [
    ("Run it now: LIONESS-DRAGON on 30 endometrial tumours.", False),
    ("Our samples come from a clinical trial.", False),
    ("Demographic covariates are in design.tsv.", False),
    ("Do a trial run of PANDA.", True),
    ("Run a demo of DRAGON.", True),
    ("Run it once on the toy data.", True),
    ("先試跑一下 PANDA", True),
])
def test_a_demo_request_is_a_whole_word(task, demo):
    assert _is_demo_request(task) is demo


def test_the_request_records_the_files_and_folders_it_names():
    p21 = request_input_bindings("Run BONOBO on samples S03 and S11 from yeast_stress_logc.tsv; save the matrices "
                                 "as csv.", ["expression_file"])
    assert p21.values == {} and p21.named_paths == ("yeast_stress_logc.tsv",)
    p08 = request_input_bindings("Run LIONESS-PUMA on gbm_expr.tsv, and write the per-sample networks to "
                                 "lioness_gbm.npy.", ["expression_file"])
    assert p08.named_paths == ("gbm_expr.tsv",)  # where a result is written is not an input
    p33 = request_input_bindings("LIONESS-PANDA with the motif and PPI priors in /proj/mac/priors, please.",
                                 ["motif_file", "ppi_file"])
    assert p33.missing_directories == ("/proj/mac/priors",)
    plain = request_input_bindings("Outputs can go to /registry/run1. We want TF/miRNA networks.", ["expression_file"])
    assert plain.named_paths == () and plain.missing_directories == ()


def _plan(action, task, **fields):
    decision = agent.TaskDecision(action=action, in_scope=True, should_execute=True, confidence=0.99,
                                  reason="formal run", **fields)
    plan = agent.build_workflow_plan(decision, task, profile=agent.UserProfile(profile_id="alice"),
                                     retrieved_episodes=[])
    return plan, {item.field: item for item in plan.evidence}


def _no_shipped_data(evidence):
    return all(not is_shipped_data(value) for item in evidence.values()
               for value in [item.value or "", *item.candidates] if value)


def test_p21_a_named_file_no_role_hint_matches_is_the_users():
    plan, evidence = _plan("run_bonobo", "Go ahead and run BONOBO on samples S03, S07 and S11 only from "
                           "yeast_stress_logc.tsv (log2, centred, 14 samples in total); save the matrices as csv.")
    assert evidence["expression_file"].status == "provided"
    assert evidence["expression_file"].value == "yeast_stress_logc.tsv"
    assert _no_shipped_data(evidence)


def test_p16_the_two_named_dragon_layers_are_bound_in_order():
    plan, evidence = _plan("run_dragon", "Run DRAGON on methylation_beta.csv and rnaseq_log.csv (the same 140 lung "
                           "adenocarcinoma patients, patients as rows) and give me the partial-correlation network.")
    assert (evidence["omics_layer_1"].value, evidence["omics_layer_2"].value) == (
        "methylation_beta.csv", "rnaseq_log.csv")
    assert _no_shipped_data(evidence)


def test_p24_a_named_edge_list_is_not_replaced_by_a_demo_network():
    plan, evidence = _plan("run_condor", "Run CONDOR community detection on panda_edges_thresholded.tsv (source, "
                           "target, weight; TFs to genes) and report each node's core score.")
    assert evidence["network_file"].value == "panda_edges_thresholded.tsv"
    assert evidence["network_file"].status == "provided"
    assert _no_shipped_data(evidence)


def test_p33_a_named_folder_that_is_missing_is_reported_not_replaced():
    plan, evidence = _plan("run_lioness_panda", "Go ahead: LIONESS-PANDA on the 15 macaque PBMC samples with the "
                           "motif and PPI priors in /proj/mac/priors, but in the end I only need the network for "
                           "animal M07.")
    assert plan.status == "needs_input"
    assert evidence["motif_file"].status == "missing" and not evidence["motif_file"].candidates
    assert "/proj/mac/priors" in evidence["motif_file"].reason and "does not exist" in evidence["motif_file"].reason
    assert _no_shipped_data(evidence)


def test_a_formal_run_naming_no_file_is_offered_no_toy_data():
    plan, evidence = _plan("run_dragon", "Run DRAGON on our methylation and expression matrices from the same 88 "
                           "patients.")
    assert plan.status == "needs_input" and _no_shipped_data(evidence)


def test_p19_endometrial_is_not_a_demo_but_a_demo_request_still_gets_the_demo_bundle():
    _plan_, evidence = _plan("run_lioness_dragon", "Run it now: LIONESS-DRAGON on the paired miRNA (300 features) "
                             "and mRNA (600 features) tables from 30 endometrial tumours, with lambda1 0.3 and "
                             "lambda2 0.4.")
    assert all(item.status != "demo_bundle" for item in evidence.values()) and _no_shipped_data(evidence)
    _plan_, evidence = _plan("run_dragon", "Run a demo of DRAGON on the toy layers.")
    assert any(is_shipped_data(item.value or "") for item in evidence.values())


def test_p33_the_wizard_says_the_named_folder_does_not_exist():
    from netzoo_agent_core.cli.clarification import clarification_prompt

    plan, _evidence = _plan("run_lioness_panda", "Go ahead: LIONESS-PANDA on the 15 macaque PBMC samples with the motif "
                            "and PPI priors in /proj/mac/priors.")
    text = clarification_prompt(plan)
    assert "/proj/mac/priors) does not exist" in text and "dragon-toy" not in text and "-toy/" not in text
