from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing import (  # noqa: E402
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
