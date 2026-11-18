"""What the window shows as "Understood": typed values and the user's own words, never model prose."""

from netzoo_agent_core.contracts import OutcomeEvidence, OutcomeHypothesis, RequestedOutcome
from netzoo_agent_core.interpretation.reading_view import reading_view

TASK = "I want one regulatory network per sample from my expression matrix"


def _hypothesis(*evidence):
    outcome = RequestedOutcome(operation="infer", artifact_type="regulatory_network", granularity="sample_specific",
                               regulator_types=["tf"], target_types=["gene"])
    return OutcomeHypothesis(outcome=outcome, confidence=.9, evidence=list(evidence))


def test_stated_values_carry_their_quote_and_inferred_ones_are_marked():
    view = reading_view([_hypothesis(
        OutcomeEvidence(dimension="granularity", value="sample_specific", source="explicit",
                        text_span="one regulatory network per sample", rationale="MODEL PROSE"),
        OutcomeEvidence(dimension="regulator_type", value="tf", source="inferred", rationale="MODEL PROSE"),
    )], TASK)
    assert view[0]["artifact_type"] == "regulatory_network" and view[0]["granularity"] == "sample_specific"
    assert view[0]["stated"] == [{"dimension": "granularity", "value": "sample_specific",
                                  "quote": "one regulatory network per sample"}]
    assert view[0]["inferred"] == [{"dimension": "regulator_type", "value": "tf"}]
    assert "MODEL PROSE" not in repr(view)


def test_a_quote_that_is_not_in_the_request_is_dropped():
    view = reading_view([_hypothesis(
        OutcomeEvidence(dimension="granularity", value="sample_specific", source="explicit",
                        text_span="for every patient separately", rationale="x"),
    )], TASK)
    assert view[0]["stated"] == []
