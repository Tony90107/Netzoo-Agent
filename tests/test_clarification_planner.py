from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing.capability_compatibility import (  # noqa: E402
    _accepts_inputs,
    input_availability,
)
from netzoo_agent_core.routing.clarification_planner import (  # noqa: E402
    ClarificationPlanner,
    plan_clarification,
)
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


def test_input_availability_keeps_absent_separate_from_unknown():
    availability = input_availability(
        "I have an expression matrix, TF motif and PPI priors, but no miRNA prior."
    )

    assert availability.status("expression_matrix") == "present"
    assert availability.status("motif_prior") == "present"
    assert availability.status("ppi_prior") == "present"
    assert availability.status("mirna_prior") == "absent"
    assert availability.status("mutation_matrix") == "unknown"


def test_historical_prior_bundle_does_not_become_current_input():
    availability = input_availability(
        "Previously I had miRNA, motif and PPI priors. Now I have expression data."
    )

    assert availability.status("mirna_prior") == "unknown"
    assert availability.status("motif_prior") == "unknown"
    assert availability.status("ppi_prior") == "unknown"


def test_unmentioned_required_input_is_unknown_and_does_not_eliminate_a_candidate():
    requested = RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
    )
    availability = input_availability("I have an expression matrix.")

    assert _accepts_inputs(requested, OUTPUT_CAPABILITIES["run_panda"], availability)


def test_explicitly_absent_required_input_eliminates_a_candidate():
    requested = RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
    )
    availability = input_availability(
        "I have expression data and a TF motif prior, but no PPI data."
    )

    assert not _accepts_inputs(
        requested, OUTPUT_CAPABILITIES["run_panda"], availability
    )


def test_planner_asks_biological_role_before_method_jargon():
    outcome = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["gene"],
        granularity="sample_specific",
    )

    decision = plan_clarification(
        ["run_lioness_panda", "run_lioness_puma"], outcomes=[outcome]
    )

    assert decision is not None
    assert decision.dimension == "regulator_type"
    assert "transcription factors" in decision.question
    assert "run_lioness" not in decision.question


def test_planner_uses_algorithmic_philosophy_when_output_dimensions_are_settled():
    outcome = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
    )

    decision = ClarificationPlanner().plan(
        ["run_panda", "run_otter", "run_giraffe"], outcomes=[outcome]
    )

    assert decision is not None
    assert decision.dimension == "algorithm"
    labels = {option.label for option in decision.options}
    assert "iterative message passing" in labels
    assert "continuous relaxed graph matching" in labels
    assert all(action not in decision.question for action in decision.candidate_actions)


def test_planner_returns_none_when_there_is_no_choice_to_resolve():
    assert plan_clarification(["run_panda"]) is None
