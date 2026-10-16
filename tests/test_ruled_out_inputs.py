"""Core decision spec, phase 4b (section 12.3): an input the user says they do not have.

Round p0-p3 C18: "Run CONDOR directly on expr_kidney_fibrosis.tsv ... I don't have any motif or PPI files, just this
expression table" was offered CONDOR through PANDA -> CONDOR in 3 of 4 rounds. One rule, `route_available`, now
decides it for the check's credits and for the two-step routes.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import ruled_out_inputs  # noqa: E402
from netzoo_agent_core.interpretation.ruled_out import route_available, without_ruled_out  # noqa: E402

TASK = "Run CONDOR directly on expr.tsv to get gene communities. I don't have any motif or PPI files, just this table."
NO_PRIORS = {"motif_prior": "I don't have any motif or PPI files", "ppi": "I don't have any motif or PPI files"}


def _condor_row(network="none"):
    return CheckedRequirement(quote="to get gene communities", kind="result", status="available",
                              delivered_by=["condor.communities"], attrs={"input_network": network})


def test_a_ruled_out_input_no_registered_route_provides_makes_the_workflow_unavailable():
    assert "PANDA needs it" in route_available("run_panda", NO_PRIORS)
    assert route_available("run_panda", {"ppi": "no PPI"}) is None  # a PPI network can be downloaded from STRING
    assert route_available("run_lioness_coexpression", NO_PRIORS) is None  # it needs neither
    assert "COBRA needs it" in route_available("run_cobra", {"covariates": "we have no covariate table"})
    assert route_available("run_otter", {"expression": "no expression"}) is None  # it can take co-expression instead


def test_condor_without_a_network_is_unavailable_when_every_route_to_one_is_blocked():
    reason = route_available("run_condor", NO_PRIORS, frozenset({"network"}))
    assert reason.startswith("CONDOR needs a regulator-gene network; every registered route to one (OTTER, PANDA, PUMA)")
    assert route_available("run_condor", {}, frozenset({"network"})) is None  # nothing ruled out: PANDA can make it


def test_the_check_loses_the_credit_and_the_reason_is_said():
    check = CapabilityCheck(requirements=[_condor_row()], ruled_out=NO_PRIORS)
    lifted = without_ruled_out(check)
    (row,) = lifted.results()
    assert (row.status, row.delivered_by, lifted.full_gap) == ("not_available", [], True)
    assert "every registered route to one" in row.limits[0]


def test_a_check_with_nothing_ruled_out_or_an_existing_network_is_unchanged():
    plain = CapabilityCheck(requirements=[_condor_row()])
    assert without_ruled_out(plain) is plain
    has_network = CapabilityCheck(requirements=[_condor_row("regulator_gene")], ruled_out=NO_PRIORS)
    assert without_ruled_out(has_network).results()[0].delivered_by == ["condor.communities"]


def test_ruled_out_words_are_kept_only_when_they_are_in_the_request():
    item = lambda kind, quote: SimpleNamespace(kind=kind, quote=quote)
    proposal = SimpleNamespace(conditions=SimpleNamespace(ruled_out_inputs=[
        item("motif_prior", "I don't have any motif or PPI files"), item("ppi", "we never had a PPI network")]))
    assert ruled_out_inputs(TASK, proposal) == {"motif_prior": "I don't have any motif or PPI files"}


def test_two_step_routes_skip_a_producer_the_user_cannot_run():
    from netzoo_agent_core.interpretation.hypothesis_routes import _handoff_routes
    from netzoo_agent_core.policy import ProjectPolicyLoader

    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    reading = SimpleNamespace(outcome=SimpleNamespace(artifact_type="community_assignment", regulator_types=[],
                                                      entity_types=["gene"]))
    stated = frozenset({"expression_matrix"})
    assert ("run_panda", "run_condor") in _handoff_routes(reading, stated, policy)
    assert _handoff_routes(reading, stated, policy, NO_PRIORS) == []


def test_stated_inputs_without_a_network_make_the_network_absent():
    """Smoke S1: "I only have expr_liver.tsv; we have no motif prior and no PPI network" typed the CONDOR ask's
    input_network as regulator_gene (the kind CONDOR takes); the routing reading's stated inputs hold no network."""
    check = CapabilityCheck(requirements=[_condor_row("regulator_gene")], ruled_out=NO_PRIORS)
    assert without_ruled_out(check, frozenset({"expression_matrix"})).results()[0].status == "not_available"
    assert without_ruled_out(check, frozenset({"expression_matrix", "regulatory_network"})).results()[0].delivered_by == [
        "condor.communities"]
    assert without_ruled_out(check, frozenset()).results()[0].delivered_by == ["condor.communities"]  # unknown inputs
