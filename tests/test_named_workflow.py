"""A bare command naming a registered workflow is asking for that workflow's own results (10-13b F40, F46).

"請跑 PANDA" and "請跑 CONDOR" name no result, so the second opinion could only answer all/part/none and answered none:
the user's own workflow was refused. "named" says the words only ask to run or use the workflow itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    CapabilityCheck, CheckedRequirement, second_opinion_model,
)
from netzoo_agent_core.interpretation.capability_check import apply_second_opinion, second_opinion_pairs  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False,
         "input_network": "none", "group_membership": "not_about_groups", "time_model": "not_dynamic",
         "spatial": "not_spatial"}


def _gap(quote, **attrs):
    return CapabilityCheck(requirements=[CheckedRequirement(
        quote=quote, kind="result", status="not_available", blank=True, attrs={**PLAIN, **attrs})], full_gap=True)


def test_named_is_an_answer_of_the_contract():
    assert second_opinion_model(1).model_validate({"a1": "named"}).a1 == "named"


def test_a_bare_command_answered_named_credits_the_named_workflow():
    check = _gap("請跑 PANDA")
    pairs = second_opinion_pairs(check, ["run_panda"])
    updated = apply_second_opinion(check, pairs, ["named"])
    assert not updated.full_gap and updated.results()[0].status == "available"
    assert "panda.tf_gene_network" in updated.results()[0].delivered_by


def test_a_named_workflow_its_typed_attributes_rule_out_is_never_asked():
    """Pre-measure: "Run CONDOR on our gene-gene co-expression network" was answered named; a gene-gene input network
    rules CONDOR out before the second opinion is asked."""
    assert second_opinion_pairs(_gap("Run CONDOR on our gene-gene co-expression network", input_network="gene_gene"),
                                ["run_condor"]) == []
