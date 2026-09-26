"""Log 146: a guidance request's operation needs no quote when the artifact is known."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

TASK = "Our cohort has about 400 tumour samples. I want to see each tumour's own gene co-expression network."
SPAN = "I want to see each tumour's own gene co-expression network."
MISSING = "hypothesis[0].missing_evidence:operation=infer"


def _hypothesis(artifact="coexpression_network") -> OutcomeHypothesis:
    outcome = RequestedOutcome(
        operation="infer", artifact_type=artifact, entity_types=["gene"],
        granularity="sample_specific" if artifact != "unknown" else "unknown",
    )
    evidence = [] if artifact == "unknown" else [
        OutcomeEvidence(dimension=d, value=v, source="explicit", text_span=SPAN, rationale="t")
        for d, v in (("artifact_type", artifact), ("granularity", "sample_specific"))
    ]
    return OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)


def test_guidance_request_does_not_owe_a_quote_for_an_erased_operation():
    result = validate_outcome_hypotheses(TASK, [_hypothesis()], "guidance")
    assert MISSING not in result.issues
    assert result.valid


@pytest.mark.parametrize("mode", ["execute", "unknown"])
def test_requests_whose_operation_is_read_still_need_the_quote(mode):
    assert MISSING in validate_outcome_hypotheses(TASK, [_hypothesis()], mode).issues


def test_default_mode_is_unchanged():
    assert MISSING in validate_outcome_hypotheses(TASK, [_hypothesis()]).issues


def test_unknown_artifact_keeps_the_operation_requirement_in_guidance():
    """Otherwise the only evidenced field disappears and the reading becomes unusable."""
    issues = validate_outcome_hypotheses(TASK, [_hypothesis("unknown")], "guidance").issues
    assert MISSING in issues
    assert "hypothesis[0].unusable_outcome" not in issues
