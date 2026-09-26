"""Log 136: `sample` as the granularity axis and settled clarification dimensions."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.routing.clarification_planner import plan_clarification  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_outcome_hypotheses,
    match_requested_outcome,
)
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402

def _per_patient_coexpression(**update) -> RequestedOutcome:
    fields = dict(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network",
        entity_types=["gene", "sample"],
        granularity="sample_specific",
    )
    fields.update(update)
    return RequestedOutcome(**fields)


def test_sample_in_a_sample_specific_request_does_not_reject_coexpression_workflows():
    outcome = _per_patient_coexpression()

    strict = match_requested_outcome(outcome)
    advisory = match_outcome_hypotheses(
        [OutcomeHypothesis(outcome=outcome, confidence=0.9)]
    )

    assert strict.status == "ambiguous"
    assert "entity_types" not in strict.mismatch_dimensions
    assert set(advisory.hypothesis_actions) == {"run_bonobo", "run_lioness_coexpression"}


def test_sample_axis_rule_does_not_apply_to_aggregate_requests():
    outcome = _per_patient_coexpression(granularity="aggregate")

    assert "run_bonobo" not in match_outcome_hypotheses(
        [OutcomeHypothesis(outcome=outcome, confidence=0.9)]
    ).hypothesis_actions


def test_sample_specific_tf_network_naming_sample_selects_lioness_panda():
    outcome = RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network",
        entity_types=["tf", "gene", "sample"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="sample_specific",
    )

    match = match_requested_outcome(outcome)

    assert match.status == "exact"
    assert match.matched_actions == ["run_lioness_panda"]


def test_sample_axis_premise_no_capability_uses_sample_as_a_node_type_per_sample():
    """The axis rule is only sound while no sample-specific capability treats
    `sample` as a genuine node type of its result. If one is added, this rule
    would wrongly admit requests for it; revisit Log 136 before relaxing this."""
    offenders = [
        action
        for action, capability in OUTPUT_CAPABILITIES.items()
        if "sample_specific" in capability.granularities
        and "sample" in capability.entity_types
    ]

    assert offenders == [], (
        "A sample-specific capability declares `sample` as a node entity; the "
        "Log 136 granularity-axis rule in _supported_entities no longer holds."
    )


def test_planner_does_not_ask_about_an_artifact_and_granularity_already_stated():
    outcome = _per_patient_coexpression()

    decision = plan_clarification(
        ["run_lioness_coexpression", "run_bonobo"], outcomes=[outcome],
    )

    assert decision is not None
    assert decision.dimension == "algorithm"
    assert decision.question.startswith("Which modeling assumption")


def test_planner_still_asks_about_granularity_when_it_is_open():
    outcome = _per_patient_coexpression(granularity="unknown", entity_types=["gene"])

    decision = plan_clarification(
        ["run_lioness_coexpression", "run_cobra"], outcomes=[outcome],
    )

    assert decision is not None
    assert decision.dimension == "granularity"


# Log 172: on an axis artifact, `sample` is the axis at any granularity.
def test_sample_on_an_aggregate_coexpression_request_is_not_a_node_type():
    outcome = _per_patient_coexpression(granularity="aggregate", operation="unknown")

    match = match_outcome_hypotheses([OutcomeHypothesis(outcome=outcome, confidence=0.9)])

    assert set(match.hypothesis_actions) == {"run_cobra", "run_lioness_coexpression"}


def test_sample_on_an_aggregate_regulatory_request_is_still_checked():
    """regulatory_network lists no entities in the ontology, so the axis rule does not apply."""
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network", granularity="aggregate",
        entity_types=["tf", "gene", "sample"], regulator_types=["tf"], target_types=["gene"],
    )

    assert match_requested_outcome(outcome).status == "unsupported"
