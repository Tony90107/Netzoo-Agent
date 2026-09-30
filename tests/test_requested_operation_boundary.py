"""An existing result request cannot turn into inferred workflow guidance."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import IntentDecision, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.interpretation.assembly import assemble_task_decision  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_capability_gap  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402


@pytest.mark.parametrize("request_mode", ["guidance", "execute"])
@pytest.mark.parametrize("granularity", ["aggregate", "unknown"])
def test_acquiring_existing_network_is_not_inference(request_mode, granularity):
    task = "我想要下載gene regulatory network (BioGRID)"
    outcome = RequestedOutcome(
        operation="acquire",
        artifact_type="regulatory_network",
        granularity=granularity,
        unresolved_dimensions=["granularity"] if granularity == "unknown" else [],
    )

    match = match_semantic_request(
        task,
        [OutcomeHypothesis(outcome=outcome, confidence=0.95)],
        request_mode=request_mode,
    )

    assert match.status == "unsupported"
    assert "operation" in match.mismatch_dimensions
    assert not match.matched_actions
    assert not match.hypothesis_actions


def test_acquisition_gap_answers_the_requested_operation_concisely():
    outcome = RequestedOutcome(
        operation="acquire", artifact_type="regulatory_network",
        granularity="unknown", unresolved_dimensions=["granularity"],
    )
    decision = TaskDecision(
        action="no_tool", in_scope=False, should_execute=False,
        intent_type="answer_question", confidence=0.95, reason="unsupported operation",
        requested_outcome=outcome, capability_match_status="unsupported",
        mismatch_dimensions=["operation"],
    )

    answer = render_capability_gap(
        decision, ProjectPolicyLoader(Path(__file__).parents[1]).load(),
    )

    assert "Direct download currently supports only STRING" in answer
    assert "Registered outputs are:" not in answer


def test_unsupported_acquisition_cannot_become_an_executable_workflow():
    task = "Download an existing regulatory network from an external source."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="acquire", artifact_type="regulatory_network",
            granularity="unknown", unresolved_dimensions=["granularity"],
        ),
        confidence=0.95,
    )
    match = match_semantic_request(task, [hypothesis], request_mode="execute")
    decision = assemble_task_decision(
        SemanticInterpretation(
            request_mode="execute", semantic_goal="Acquire an existing network",
            outcome_hypotheses=[hypothesis],
        ),
        match,
        IntentDecision(mode="execute", confidence=0.95, reason="Explicit request"),
        task=task,
    )

    assert decision.action == "no_tool"
    assert decision.should_execute is False
    assert decision.capability_match_status == "unsupported"


def test_explicit_download_cannot_become_inference_after_semantic_misreading():
    task = "Download an existing regulatory network from BioGRID."
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network",
            granularity="unknown", unresolved_dimensions=["granularity"],
        ),
        confidence=0.95,
    )
    match = match_semantic_request(task, [hypothesis], request_mode="execute")
    assert match.status == "unsupported"
    assert "operation" in match.mismatch_dimensions
    assert not match.matched_actions
