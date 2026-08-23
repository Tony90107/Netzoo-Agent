from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_outcome_hypotheses,
    match_semantic_request,
    guidance_actions_for,
    match_requested_outcome,
)


def outcome(**updates) -> RequestedOutcome:
    values = {
        "operation": "infer",
        "artifact_type": "regulatory_network",
        "entity_types": ["mirna", "gene"],
        "display_entities": ["miRNA", "gene"],
        "regulator_types": ["mirna"],
        "target_types": ["gene"],
        "granularity": "sample_specific",
        "unresolved_dimensions": [],
    }
    values.update(updates)
    return RequestedOutcome(**values)


def advisory_hypothesis(
    requested: RequestedOutcome,
    *evidence: OutcomeEvidence,
    assumptions: list[str] | None = None,
) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=requested,
        confidence=0.9,
        evidence=list(evidence),
        assumptions=assumptions or ["One outcome dimension remains unconfirmed."],
    )


def test_sample_specific_mirna_regulatory_network_matches_lioness_puma():
    result = match_requested_outcome(outcome())

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    assert result.alternative_actions == []
    assert guidance_actions_for("run_lioness_puma") == [
        "run_puma",
        "run_lioness_puma",
    ]


def test_sample_specific_mirna_measurements_are_not_a_workflow_match():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            regulator_types=[],
            target_types=[],
        )
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []
    assert result.alternative_actions[0] == "run_lioness_puma"
    assert "operation" in result.mismatch_dimensions
    assert "artifact_type" in result.mismatch_dimensions


def test_unknown_artifact_stays_ambiguous_instead_of_matching():
    result = match_requested_outcome(
        outcome(
            artifact_type="unknown",
            unresolved_dimensions=["requested artifact"],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.clarification_question is not None


def test_multiple_end_to_end_matches_require_a_selection_dimension():
    result = match_requested_outcome(
        outcome(
            entity_types=["gene"],
            display_entities=["gene"],
            regulator_types=[],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert "regulator type" in result.clarification_question


def test_unrelated_entity_has_no_suggested_alternative():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            entity_types=["protein"],
            display_entities=["protein abundance"],
            regulator_types=[],
            target_types=[],
        )
    )

    assert result.status == "unsupported"
    assert result.alternative_actions == []


def test_unknown_entity_dimension_cannot_match_exactly():
    result = match_requested_outcome(
        outcome(
            entity_types=["unknown"],
            display_entities=[],
            regulator_types=[],
        )
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_partial_mirna_sample_network_uniquely_suggests_lioness_puma():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="unknown",
                    artifact_type="regulatory_network",
                    entity_types=["mirna"],
                    regulator_types=["mirna"],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["operation", "target type"],
                ),
                OutcomeEvidence(
                    dimension="regulator_type",
                    value="mirna",
                    source="explicit",
                    rationale="The request explicitly names miRNA.",
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for one network per sample.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.hypothesis_actions == ["run_lioness_puma"]


def test_generic_sample_network_keeps_all_lioness_families_tied():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="infer",
                    artifact_type="unknown",
                    entity_types=[],
                    display_entities=[],
                    regulator_types=[],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["network type"],
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for a sample-specific result.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert set(result.hypothesis_actions) == {
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
    }


def test_measurement_artifact_conflicts_with_every_network_hypothesis():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="acquire",
                    artifact_type="measurement_dataset",
                    regulator_types=[],
                    target_types=[],
                ),
                OutcomeEvidence(
                    dimension="artifact_type",
                    value="measurement_dataset",
                    source="explicit",
                    rationale="The request asks for measured miRNA values.",
                ),
            )
        ]
    )

    assert result.matched_actions == []
    assert result.hypothesis_actions == []
    assert result.status == "unsupported"


def test_registry_identifier_matches_supporting_action_without_intent_authority():
    not_applicable = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            entity_types=[],
            regulator_types=[],
            target_types=[],
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=0.99,
        evidence=[],
        assumptions=[],
    )

    result = match_semantic_request(
        "Search the web with WEB-SEARCH for current PANDA references.",
        [not_applicable],
    )

    assert result.status == "exact"
    assert result.matched_actions == ["web_search"]
