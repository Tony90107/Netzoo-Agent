"""dev-bank-2026-11-19: the code paths behind six development-bank misses (D005, D010, D015, D021, D025)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.execution_sponge import sponge_input_errors  # noqa: E402
from netzoo_agent_core.method_names import bare_lioness  # noqa: E402
from netzoo_agent_core.prior_request import prior_decision, requested_tf_names  # noqa: E402
from netzoo_agent_core.routing.named_labels import solely_named_run_action  # noqa: E402

D010 = ("Human AML cohort, 25 bulk bone-marrow samples, expression matrix ready but no prior files at all. Build the "
        "motif and PPI priors with SPONGE for RUNX1, CEBPA, GATA2, SPI1 and MYB on hg38, then run LIONESS on the "
        "expression matrix with those priors.")
D015 = ("Please run LIONESS on our bulk RNA-seq from 48 sigmoid colon samples. I have the gene-by-sample expression "
        "matrix (already normalized), a TF motif prior and a PPI network, all with gene symbols.")
D021 = ("Build human motif and PPI priors for AR, FOXA1, HOXB13 and NKX3-1 for our prostate cancer cohort. The job "
        "runs inside a fully air-gapped enclave: no outbound connections of any kind are permitted.")
D025 = ("Please build human motif and PPI priors for TP53, MYC and E2F1. They must match an old annotation; it is "
        "either hg19 or hg18 and I honestly don't remember which. Internet access is fine.")


@pytest.mark.parametrize("task,workflow", [
    (D015, "LIONESS-PANDA"), (D010, "LIONESS-PANDA"),
    ("Please run LIONESS with our motif prior, PPI and miRNA list.", None),
    ("Run LIONESS on our co-expression data.", None),
    ("Run LIONESS on our metabolomics and proteomics layers.", None),
    ("Run LIONESS-PUMA on expr.tsv.", None)])
def test_a_bare_lioness_is_lioness_panda_unless_the_words_point_elsewhere(task, workflow):
    assert bare_lioness(task) == workflow


def test_build_the_priors_then_run_lioness_chains_to_lioness_panda_with_the_tf_list():
    decision = prior_decision(D010)
    assert decision.action == "build_priors" and decision.then_action == "run_lioness_panda"
    assert decision.sponge_tf_names == ["RUNX1", "CEBPA", "GATA2", "SPI1", "MYB"] and decision.genome_assembly == "hg38"
    assert sponge_input_errors(decision) == []


def test_run_lioness_named_alone_is_a_named_lioness_panda_run():
    assert solely_named_run_action(D015) == "run_lioness_panda"
    assert solely_named_run_action("Please run LIONESS with our motif prior, PPI and miRNA list.") is None


def test_an_offline_request_stops_sponge_with_the_contract_reason():
    errors = sponge_input_errors(prior_decision(D021))
    assert errors and "needs internet access" in errors[0] and '"air-gapped"' in errors[0]


def test_two_assemblies_or_an_unsupported_one_stop_sponge_and_one_supported_is_read():
    decision = prior_decision(D025)
    assert decision.genome_assembly is None
    assert "more than one genome assembly (hg19, hg18)" in sponge_input_errors(decision)[0]
    older = prior_decision("Build the motif and PPI priors for SOX2 and MYC on hg18.")
    assert "the request names hg18" in sponge_input_errors(older)[0]
    plain = prior_decision("Build the motif and PPI priors for SOX2 and MYC on hg19.")
    assert plain.genome_assembly == "hg19" and sponge_input_errors(plain) == []


@pytest.mark.parametrize("task,names", [
    ("Build the motif and PPI priors with SPONGE for RUNX1, CEBPA and MYB.", ["RUNX1", "CEBPA", "MYB"]),
    ("Build the motif and PPI priors for the TFs SOX2, MYC and FOXF2.", ["SOX2", "MYC", "FOXF2"]),
    ("Build the motif and PPI priors for our cohort.", [])])
def test_the_tf_list_is_read_after_priors_for(task, names):
    assert requested_tf_names(task) == names


def test_sponge_asks_the_organism_only_when_the_request_never_says_it():
    d005 = ("I have bulk RNA-seq of skeletal muscle, 20 samples, and no motif or PPI prior files. Please build the "
            "priors with SPONGE for MYOD1, MEF2C, PPARGC1A and ESRRA, then run LIONESS on my expression matrix.")
    errors = sponge_input_errors(prior_decision(d005))
    assert errors and "say whether they are human" in errors[0]
    assert sponge_input_errors(prior_decision(d005.replace("skeletal muscle", "human skeletal muscle"))) == []
    mouse = sponge_input_errors(prior_decision(d005.replace("skeletal muscle", "mouse skeletal muscle")))
    assert mouse and "human priors only" in mouse[0] and "say whether" not in " ".join(mouse)


D011 = ("I downloaded one published PANDA network for human liver, a single TF-by-gene weight table for the tissue as a "
        "whole. I don't have the underlying expression data. Using that network and a KEGG GMT, find the pathways with "
        "heterogeneous regulation.")


def test_porcupine_on_an_aggregate_network_without_expression_is_declined_with_both_quotes():
    from netzoo_agent_core.contracts.core_decision import CoreDecision
    from netzoo_agent_core.interpretation.stated_inputs import porcupine_on_aggregate_core

    do = CoreDecision(kind="DO", basis="results_given", workflows=["PORCUPINE"])
    after, action = porcupine_on_aggregate_core(do, D011)
    assert (after.kind, action) == ("DECLINE", "declined")
    line = after.declined[0].line
    assert "a single TF-by-gene weight table for the tissue as a whole" in line
    assert "I don't have the underlying expression data" in line and "are not valid inputs" in line
    lioness = D011.replace("I don't have the underlying expression data.", "I also have the expression data.")
    assert porcupine_on_aggregate_core(do, lioness)[0] is do  # expression stated: LIONESS -> PORCUPINE stays offered
    per_sample = D011.replace("one published PANDA network", "our LIONESS sample-specific networks")
    assert porcupine_on_aggregate_core(do, per_sample)[0] is do


def test_a_planning_question_in_porcupines_own_words_gets_the_chain():
    from netzoo_agent_core.interpretation.prep_concepts import prep_concept_reply

    d030 = ("I'm planning a study of inter-tumour heterogeneity in pathway regulation across roughly 90 ovarian "
            "carcinomas, starting from bulk expression only. What are the analysis steps in between, and what inputs "
            "does each step need from me?")
    reply = prep_concept_reply(d030)
    assert "1. **LIONESS-PANDA**" in reply and "2. **PORCUPINE**" in reply and "Require at least 8 samples." in reply
    assert prep_concept_reply("Run PORCUPINE on lioness.tsv with hallmark.gmt for inter-tumour heterogeneity.") is None


def test_a_question_about_priors_the_user_lacks_is_answered_with_sponge_and_asks_nothing_said():
    from netzoo_agent_core.interpretation.prep_concepts import prep_concept_reply

    d018 = ("We have bulk expression for a human glioblastoma cohort and want TF-to-gene regulatory networks, but nobody "
            "in the lab has a TF binding prior or a protein interaction file. How do people normally get those two "
            "inputs, and can it be done here?")
    reply = prep_concept_reply(d018)
    assert reply.startswith("What SPONGE does") and "do you already have" not in reply
    assert prep_concept_reply("We want TF-to-gene networks for our cohort.") is None


def test_single_cell_and_heterogeneity_links_go_to_scorpion_and_porcupine():
    sys.path.insert(0, str(Path(__file__).parent))
    from test_jev_forms import _proposal
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    task = ("Single-nucleus RNA-seq from 14 donors as a 10x directory. Build one regulatory network per donor and then "
            "tell me which pathways differ in their regulation across the donors.")
    per_donor, _ = build_capability_check(task, _proposal("Build one regulatory network per donor",
                                                          ("lioness_panda.per_sample_networks",),
                                                          data_unit="single_cells", scale="per_sample"))
    assert per_donor.results()[0].delivered_by == ["scorpion.per_group_networks"]
    pathways, _ = build_capability_check(task, _proposal(
        "tell me which pathways differ in their regulation across the donors", ("condor.enrichment",), scale="per_group"))
    assert pathways.results()[0].delivered_by == ["porcupine.heterogeneous_pathways"]
    bulk, _ = build_capability_check("Build one network per patient.", _proposal(
        "Build one network per patient.", ("lioness_panda.per_sample_networks",), scale="per_sample"))
    assert bulk.results()[0].delivered_by == ["lioness_panda.per_sample_networks"]
