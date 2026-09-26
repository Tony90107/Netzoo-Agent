"""Log 182: a quote that marks an omission is grounded segment by segment."""

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
    explicit_evidence_grounded,
    validate_outcome_hypotheses,
)

TASK = (
    "For the same individuals I have gene expression (data/blind-neutral/case-7/layer1.tsv) "
    "and methylation (layer2.tsv). I want to know which methylation sites and genes are "
    "directly associated, not linked indirectly through other variables."
)


def _quote(span: str, dimension: str = "artifact_type", value: str = "multi_omic_network"):
    return OutcomeEvidence(dimension=dimension, value=value, source="explicit",
                           text_span=span, rationale="test")


@pytest.mark.parametrize("span", [
    "I have gene expression... and methylation...",
    "I have gene expression … and methylation",
    "separate ... for every patient",
])
def test_every_segment_present_grounds(span):
    task = TASK + " I need a separate network for every patient."
    assert explicit_evidence_grounded(task, _quote(span))


@pytest.mark.parametrize("span", [
    "I have gene expression... and proteomics...",
    "regulatory ... network",
    "...",
    "…",
])
def test_a_segment_the_request_lacks_fails_the_quote(span):
    assert not explicit_evidence_grounded(TASK + " Build a network.", _quote(span))


def test_the_recorded_case_7_reading_now_validates():
    outcome = RequestedOutcome(operation="infer", artifact_type="multi_omic_network",
                               granularity="aggregate")
    sentence = "I want to know which methylation sites and genes are directly associated."
    evidence = [
        _quote(sentence, "operation", "infer"),
        _quote("I have gene expression... and methylation..."),
        _quote(sentence, "granularity", "aggregate"),
    ]

    validation = validate_outcome_hypotheses(
        TASK, [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)], "guidance",
    )

    assert validation.valid, validation.issues
