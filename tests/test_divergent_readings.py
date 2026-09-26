"""Log 150: a patch keeps untouched hypotheses; divergent artifact readings stay a choice."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import match_outcome_hypotheses  # noqa: E402


def _regulatory(**update) -> OutcomeHypothesis:
    fields = dict(operation="infer", artifact_type="regulatory_network",
                  granularity="sample_specific", input_artifacts=[])
    fields.update(update)
    return OutcomeHypothesis(outcome=RequestedOutcome(**fields), confidence=0.9)


def _tf_activity() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(operation="infer", artifact_type="tf_activity_matrix",
                                 granularity="aggregate", input_artifacts=[]),
        confidence=0.85,
    )


def test_a_single_workflow_reading_does_not_silence_another_reading():
    """The recorded Case 4 shape: per-patient wiring versus TF activity."""
    match = match_outcome_hypotheses([_regulatory(), _tf_activity()])

    assert match.status == "ambiguous"
    assert "run_giraffe" in match.hypothesis_actions
    assert "run_lioness_panda" in match.hypothesis_actions


def test_divergent_readings_never_become_executable():
    match = match_outcome_hypotheses([
        _regulatory(regulator_types=["tf"], target_types=["gene"], entity_types=["tf", "gene"]),
        _tf_activity(),
    ])

    assert match.status == "ambiguous"
    assert match.matched_actions == []


def test_one_artifact_read_twice_keeps_its_own_handling():
    single = match_outcome_hypotheses([
        _regulatory(regulator_types=["tf"], target_types=["gene"], entity_types=["tf", "gene"]),
    ])
    twice = match_outcome_hypotheses([
        _regulatory(regulator_types=["tf"], target_types=["gene"], entity_types=["tf", "gene"]),
        _regulatory(regulator_types=["tf"], target_types=["gene"], entity_types=["tf", "gene"]),
    ])

    assert single.matched_actions == twice.matched_actions == ["run_lioness_panda"]
