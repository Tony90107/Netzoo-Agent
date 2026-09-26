"""Log 148: explicit evidence may narrow the typed outcome's candidates, never widen them."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import match_outcome_hypotheses  # noqa: E402


def _hypothesis(granularity: str, granularity_source: str) -> OutcomeHypothesis:
    outcome = RequestedOutcome(
        operation="unknown", input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network", entity_types=["gene", "sample"],
        granularity=granularity,
    )
    evidence = [
        OutcomeEvidence(dimension="artifact_type", value="coexpression_network",
                        source="explicit", text_span="gene co-expression network", rationale="t"),
        OutcomeEvidence(dimension="granularity", value=granularity, source=granularity_source,
                        text_span="each tumour's own" if granularity_source == "explicit" else None,
                        rationale="t"),
        OutcomeEvidence(dimension="input_artifact", value="expression_matrix",
                        source="explicit", text_span="RNA-seq", rationale="t"),
    ]
    return OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)


def test_inferred_granularity_does_not_readmit_an_aggregate_only_workflow():
    """The recorded Log 146 F2 shape: sample-specific stated, but marked inferred."""
    match = match_outcome_hypotheses([_hypothesis("sample_specific", "inferred")])

    assert set(match.hypothesis_actions) == {"run_bonobo", "run_lioness_coexpression"}
    assert "run_cobra" not in match.hypothesis_actions


def test_explicit_granularity_gives_the_same_candidates():
    match = match_outcome_hypotheses([_hypothesis("sample_specific", "explicit")])

    assert set(match.hypothesis_actions) == {"run_bonobo", "run_lioness_coexpression"}


def test_explicit_evidence_still_recovers_when_the_typed_outcome_admits_nothing():
    """Aggregate plus `sample` admits no capability; the explicit artifact still leads somewhere."""
    match = match_outcome_hypotheses([_hypothesis("aggregate", "inferred")])

    assert {"run_cobra", "run_lioness_coexpression"} <= set(match.hypothesis_actions)
