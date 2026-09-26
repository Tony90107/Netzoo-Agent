"""Log 170: an operation erased for guidance is not re-imposed through its evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.graph.condition_recommender import condition_options  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TASK = (
    "I want one cohort-level gene co-expression network from my expression matrix, "
    "and I need to separate the co-expression that comes from the sequencing batch."
)


def _batch_request() -> OutcomeHypothesis:
    """The recorded Log 168 T2-cobra shape: `infer` quoted, no batch tag."""
    return OutcomeHypothesis(
        outcome=RequestedOutcome(operation="infer", input_artifacts=["expression_matrix"],
                                 artifact_type="coexpression_network", entity_types=["gene"],
                                 granularity="aggregate"),
        confidence=0.9,
        evidence=[OutcomeEvidence(dimension=d, value=v, source="explicit", text_span=s, rationale="t")
                  for d, v, s in (("operation", "infer", "I want one cohort-level gene co-expression network"),
                                  ("artifact_type", "coexpression_network", "gene co-expression network"),
                                  ("input_artifact", "expression_matrix", "my expression matrix"),
                                  ("granularity", "aggregate", "one cohort-level"))],
    )


def test_guidance_keeps_cobra_among_the_candidates():
    match = match_semantic_request(TASK, [_batch_request()], request_mode="guidance")

    assert match.status == "ambiguous"
    assert set(match.hypothesis_actions) == {"run_cobra", "run_lioness_coexpression"}
    offered = {option.condition for option in condition_options(list(match.hypothesis_actions))}
    assert {"covariates:yes", "covariates:no"} <= offered


def test_execute_mode_still_reads_the_operation():
    match = match_semantic_request(TASK, [_batch_request()], request_mode="execute")

    assert match.matched_actions == ["run_lioness_coexpression"]
