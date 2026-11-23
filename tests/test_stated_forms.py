"""stated-forms-2026-11-19: spatial and a pooled per-group scale corrected from the request's own words."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from test_jev_forms import _proposal  # noqa: E402

REGIONS = ("We ran spatial transcriptomics on four sections of human cortex and summed the spots into 32 annotated "
           "regions, so I have a gene-by-region matrix. I'd like a co-expression network for each region on its own.")
REGION_QUOTE = "I'd like a co-expression network for each region on its own."
NEIGHBOURS = ("We have 2,500 Visium spots with coordinates. I want a co-expression network for each spot that borrows "
              "information from its neighbouring spots.")
NEIGHBOUR_QUOTE = "I want a co-expression network for each spot that borrows information from its neighbouring spots."
POOLED = ("We harvested leaves at 0, 6, 24 and 72 hours, five replicates per time point. I'd like a separate aggregate "
          "PANDA network for each time point, built on the same genes and priors.")
POOLED_QUOTE = "I'd like a separate aggregate PANDA network for each time point, built on the same genes and priors."
EACH = "For each of our 40 patients I want that patient's own TF-to-gene network, and then compare the two arms."
EACH_QUOTE = "For each of our 40 patients I want that patient's own TF-to-gene network"


def _status(task, quote, keys, **attrs):
    check, _ = build_capability_check(task, _proposal(quote, keys, **attrs))
    return check.results()[0].status, check.results()[0].delivered_by


def test_spatial_data_described_is_not_a_neighbour_request():
    status, keys = _status(REGIONS, REGION_QUOTE, ("lioness_coexpression.per_sample_networks",),
                           spatial="uses_neighbors", scale="per_sample")
    assert status == "available" and keys == ["lioness_coexpression.per_sample_networks"]


def test_a_request_to_use_neighbours_still_rules_the_workflow_out():
    status, _ = _status(NEIGHBOURS, NEIGHBOUR_QUOTE, ("lioness_coexpression.per_sample_networks",),
                        spatial="uses_neighbors", scale="per_sample")
    assert status == "not_available"


def test_an_aggregate_network_per_time_point_typed_per_sample_is_read_per_group():
    status, keys = _status(POOLED, POOLED_QUOTE, ("panda.tf_gene_network",), scale="per_sample")
    assert status == "available" and keys == ["panda.tf_gene_network"]


def test_a_network_for_each_patient_stays_per_sample():
    status, keys = _status(EACH, EACH_QUOTE, ("panda.tf_gene_network", "lioness_panda.per_sample_networks"),
                           scale="per_sample")
    assert keys == ["lioness_panda.per_sample_networks"]
