"""Log 160: sample-specific composition guidance says what the networks are for next."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_workflow_composition_guidance,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def _decision(final: str, aggregate: str, regulators: list[str]) -> TaskDecision:
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=regulators, target_types=["gene"], entity_types=[*regulators, "gene"],
    )
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        capability_match_status="exact", matched_actions=[final],
        recommended_actions=[aggregate, final],
    )


@pytest.mark.parametrize("final, aggregate, regulators", [
    ("run_lioness_panda", "run_panda", ["tf"]),
    ("run_lioness_puma", "run_puma", ["tf", "mirna"]),
])
def test_sample_specific_guidance_explains_targeting_clinical_data_and_dependence(final, aggregate, regulators):
    answer = render_workflow_composition_guidance(
        _decision(final, aggregate, regulators), ProjectPolicyLoader(ROOT).load(),
    )

    assert "Downstream use of the sample-specific networks:" in answer
    assert "outdegree" in answer and "indegree" in answer
    assert "clinical table" in answer
    assert "not statistically independent" in answer
    assert answer.rstrip().endswith("No files were inspected and no analysis ran.")
