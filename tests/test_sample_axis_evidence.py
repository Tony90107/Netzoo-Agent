"""Log 143: sample-axis evidence entailment and role-evidence retirement."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.stated_field_restoration import (  # noqa: E402
    restore_stated_fields,
)

TASK = (
    "I only have expression data from a handful of patients and no prior files. "
    "I want to see how each patient's own gene co-expression structure differs."
)
SPAN = "I want to see how each patient's own gene co-expression structure differs."


def _evidence(*pairs) -> list[OutcomeEvidence]:
    return [
        OutcomeEvidence(dimension=d, value=v, source="explicit", text_span=s, rationale="t")
        for d, v, s in pairs
    ]


def _hypothesis(granularity="sample_specific", **update) -> OutcomeHypothesis:
    fields = dict(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network", entity_types=["gene", "sample"],
        granularity=granularity,
    )
    fields.update(update)
    return OutcomeHypothesis(
        outcome=RequestedOutcome(**fields), confidence=0.9,
        evidence=_evidence(
            ("operation", "infer", SPAN),
            ("input_artifact", "expression_matrix", "expression data"),
            ("artifact_type", "coexpression_network", SPAN),
            ("granularity", granularity, SPAN),
        ),
    )


def test_sample_specific_granularity_carries_the_sample_entity():
    assert validate_outcome_hypotheses(TASK, [_hypothesis()]).valid


def test_aggregate_request_needs_no_quote_for_the_sample_axis_either():
    """Log 176: on an axis artifact `sample` is the axis at any granularity (Log 172)."""
    issues = validate_outcome_hypotheses(TASK, [_hypothesis("aggregate")]).issues
    assert "hypothesis[0].missing_evidence:entity_type=sample" not in issues
    assert "hypothesis[0].missing_evidence:entity_type=gene" not in issues


def test_role_evidence_is_retired_with_roles_on_a_coexpression_network():
    """The recorded Log 141 F1 shape: target_type gene quoted on a gene-gene network."""
    hypothesis = _hypothesis(target_types=["gene"])
    hypothesis = hypothesis.model_copy(update={
        "evidence": [*hypothesis.evidence, *_evidence(("target_type", "gene", SPAN))],
    })
    interpretation = SemanticInterpretation(
        request_mode="guidance", semantic_goal="per-patient co-expression",
        outcome_hypotheses=[hypothesis],
    )

    restored, records = restore_stated_fields(
        TASK, interpretation, align_artifact_constraints=True,
        restore_explicit_scalar_evidence=True,
    )

    assert any(item["field"] == "roles" for item in records)
    kept = restored.outcome_hypotheses[0]
    assert not any(item.dimension == "target_type" for item in kept.evidence)
    assert validate_outcome_hypotheses(TASK, restored.outcome_hypotheses).valid
