"""Log 184: listing an artifact's complete entity set restates the artifact."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

TASK = (
    "In data/blind-neutral/case-1/ I have expression, a motif table, and a protein-interaction "
    "table. I suspect one transcription factor is doing different amounts of work across samples "
    "even though its own mRNA barely changes. I'd like to know which regulators are more active "
    "in each sample, and see the regulatory relationships too."
)
SENTENCE = "I'd like to know which regulators are more active in each sample."


def _validate(entities: list[str], quoted: list[str], artifact="regulatory_network_and_tf_activity"):
    outcome = RequestedOutcome(operation="infer", artifact_type=artifact,
                               granularity="aggregate", entity_types=entities)
    evidence = [OutcomeEvidence(dimension="artifact_type", value=artifact,
                                source="inferred", rationale="test")]
    evidence += [OutcomeEvidence(dimension="entity_type", value=value, source="explicit",
                                 text_span=SENTENCE, rationale="test") for value in quoted]
    return validate_outcome_hypotheses(
        TASK, [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)], "guidance",
    )


def test_the_recorded_case_1_reading_now_validates():
    validation = _validate(["tf", "sample", "gene"], quoted=["tf", "gene"])

    assert validation.valid, validation.issues


def test_the_complete_set_needs_no_entity_quote_at_all():
    assert _validate(["tf", "sample"], quoted=[], artifact="tf_activity_matrix").valid


def test_a_strict_subset_is_still_a_choice_that_needs_its_quote():
    validation = _validate(["tf", "sample"], quoted=["tf"])

    assert "hypothesis[0].missing_evidence:entity_type=sample" in validation.issues
