"""Log 164: a patch may not strip a grounded citation from a value it keeps."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
    SemanticPatch,
)
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch  # noqa: E402

TASK = "I believe each patient's regulatory wiring is different."
SPAN = "each patient's regulatory wiring is different"


def _proposal(artifact_span: str = SPAN) -> SemanticInterpretation:
    return SemanticInterpretation(
        request_mode="guidance", semantic_goal="g",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                                     granularity="unknown"),
            confidence=0.9,
            evidence=[OutcomeEvidence(dimension="artifact_type", value="regulatory_network",
                                      source="explicit", text_span=artifact_span, rationale="r")],
        )],
    )


def _patch(**extra) -> SemanticPatch:
    """The recorded Log 160 shape: set granularity, withdraw the artifact citation."""
    payload = {
        "hypothesis_index": 0,
        "outcome": {"granularity": "sample_specific"},
        "evidence_additions": [{"dimension": "granularity", "value": "sample_specific",
                                "source": "explicit", "text_span": SPAN, "rationale": "r"}],
        "evidence_removals": [{"dimension": "artifact_type", "value": "regulatory_network"}],
    }
    payload.update(extra)
    return SemanticPatch.model_validate(payload)


def _pairs(interpretation):
    return {(e.dimension, e.value) for e in interpretation.outcome_hypotheses[0].evidence}


def test_a_grounded_citation_for_a_kept_value_survives_its_withdrawal():
    merged, retired = apply_semantic_patch(
        _proposal(), _patch(), permitted_fields=frozenset({"artifact_type", "granularity"}),
        user_task=TASK,
    )

    assert ("artifact_type", "regulatory_network") in _pairs(merged)
    assert {"dimension": "artifact_type", "value": "regulatory_network",
            "field": "artifact_type", "reason": "withdrawal_of_asserted_value"} in retired


def test_a_withdrawal_with_a_replacement_quote_is_honoured():
    replacement = {"dimension": "artifact_type", "value": "regulatory_network",
                   "source": "explicit", "text_span": "regulatory wiring", "rationale": "r"}
    patch = _patch(evidence_additions=[replacement])

    merged, _ = apply_semantic_patch(
        _proposal(), patch, permitted_fields=frozenset({"artifact_type", "granularity"}),
        user_task=TASK,
    )

    spans = [e.text_span for e in merged.outcome_hypotheses[0].evidence
             if e.dimension == "artifact_type"]
    assert spans == ["regulatory wiring"]


def test_withdrawing_an_ungrounded_quote_is_honoured():
    merged, _ = apply_semantic_patch(
        _proposal(artifact_span="a quote the request never contains"), _patch(),
        permitted_fields=frozenset({"artifact_type", "granularity"}), user_task=TASK,
    )

    assert ("artifact_type", "regulatory_network") not in _pairs(merged)


def test_a_withdrawal_for_a_value_the_patch_changed_is_honoured():
    patch = _patch(outcome={"artifact_type": "coexpression_network"})

    merged, _ = apply_semantic_patch(
        _proposal(), patch, permitted_fields=frozenset({"artifact_type", "granularity"}),
        user_task=TASK,
    )

    assert ("artifact_type", "regulatory_network") not in _pairs(merged)
