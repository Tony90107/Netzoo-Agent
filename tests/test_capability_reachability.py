"""A capability the semantic prompt cannot describe can never be selected.

`run_condor` declared `granularities={"not_applicable"}`. An offline sweep of the
whole outcome ontology found exactly four outcomes that select CONDOR, and every
one of them needs `granularity="not_applicable"`. The semantic interpreter prompt
reserves that value for "a request with no scientific result at all" and requires
the canonical empty hypothesis (`operation=unknown`, `artifact_type=unknown`) to
carry it. The set of outcomes the prompt permits and the set that select CONDOR
were therefore disjoint: no model output could ever reach an exact match, which
is why `bipartite-communities` never got the workflow in either live full-corpus
round (`[]`, then `run_condor` only through a `partial_evidence` fallback).

This is the same defect family as the repair message that pinned a rejected
artifact with `const` -- a contradiction inside what the system itself publishes,
not a model failure. The fix names the single granularity a community assignment
really has: one partition of one network, not one per sample.

These tests pin the invariant generally, so the next capability that declares an
undescribable granularity fails here instead of silently going unreachable.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.contracts.artifact_semantics import (  # noqa: E402
    ARTIFACT_SEMANTICS, outcome_consistency_issues,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.routing.outcome_matching import match_requested_outcome  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


BIPARTITE_TASK = (
    "I already have a bipartite TF-to-gene regulatory network. Which workflow can "
    "partition its nodes into bipartite community modules? I am not asking to "
    "cluster patients or infer a new network. Please recommend a tool only."
)


def community_outcome(granularity: str) -> RequestedOutcome:
    return RequestedOutcome(
        operation="analyze",
        input_artifacts=["regulatory_network"],
        artifact_type="community_assignment",
        entity_types=["gene"],
        granularity=granularity,
    )


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_no_capability_is_reachable_only_through_the_canonical_empty_outcome(action):
    """`not_applicable` belongs to a request with no scientific result at all.

    A runnable capability always produces a scientific artifact, so requiring
    that granularity to select it makes the capability undescribable.
    """
    assert "not_applicable" not in OUTPUT_CAPABILITIES[action].granularities


@pytest.mark.parametrize("artifact", sorted(ARTIFACT_SEMANTICS))
def test_no_artifact_ontology_permits_the_canonical_empty_granularity(artifact):
    granularities = ARTIFACT_SEMANTICS[artifact].granularities
    assert granularities is None or "not_applicable" not in granularities


def test_a_bipartite_community_request_selects_condor_exactly():
    match = match_requested_outcome(community_outcome("aggregate"))

    assert match.status == "exact"
    assert match.matched_actions == ["run_condor"]


@pytest.mark.parametrize("granularity", ["sample_specific", "not_applicable"])
def test_community_assignment_still_rejects_every_other_granularity(granularity):
    outcome = community_outcome(granularity)

    assert "artifact_granularity:community_assignment" in outcome_consistency_issues(outcome)
    assert match_requested_outcome(outcome).status == "unsupported"


def test_the_entailed_community_granularity_needs_no_evidence_of_its_own():
    """One legal value means the artifact_type evidence already establishes it.

    Same rule as `sample_cluster_assignment` in tests/test_entailed_evidence.py:
    the validator must not ask the model to prove what the ontology decides.
    """
    hypothesis = OutcomeHypothesis(
        outcome=community_outcome("aggregate"),
        confidence=0.9,
        evidence=[
            {"dimension": "operation", "value": "analyze", "source": "explicit",
             "text_span": "partition its nodes", "rationale": "The request partitions an existing network."},
            {"dimension": "artifact_type", "value": "community_assignment", "source": "explicit",
             "text_span": "bipartite community modules", "rationale": "The requested result is community membership."},
            {"dimension": "input_artifact", "value": "regulatory_network", "source": "explicit",
             "text_span": "bipartite TF-to-gene regulatory network", "rationale": "The user already holds the network."},
            {"dimension": "entity_type", "value": "gene", "source": "explicit",
             "text_span": "TF-to-gene", "rationale": "Genes are nodes of the partitioned network."},
        ],
    )

    result = validate_outcome_hypotheses(BIPARTITE_TASK, [hypothesis])

    assert result.valid, result.issues
