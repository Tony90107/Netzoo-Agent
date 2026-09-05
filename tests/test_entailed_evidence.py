"""Do not demand evidence for a dimension the chosen artifact already fixes.

`missing_evidence` is the largest blocker in the live record -- 29 of the final
failures across 63 trials -- and 21 of those are `entity_type`. The artifact
involved is `sample_cluster_assignment`, whose ontology declares exactly one
legal entity set and one legal granularity. `outcome_consistency_issues` already
rejects any other value, so a separate evidence entry for it carries no
information: the artifact_type evidence is what justifies the choice.

This follows a rule the validator already applied to roles -- an entity named as
a regulator or target needs no second evidence entry -- and extends it to the
dimensions an artifact uniquely entails. Artifacts that permit several entities
or granularities are untouched, because there the value is a real choice.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402


TASK = ("我有一份癌症病患的體細胞突變矩陣，想把病患分成不同的亞型群組。")


def evidence(*pairs):
    return [{"dimension": dimension, "value": value, "source": "inferred",
             "rationale": "Entailed by the stated goal."} for dimension, value in pairs]


def validate(outcome, items, task=TASK):
    hypothesis = OutcomeHypothesis.model_validate(
        {"outcome": outcome, "confidence": 0.9, "evidence": items}
    )
    return validate_outcome_hypotheses(task, [hypothesis])


CLUSTER = {
    "operation": "analyze", "input_artifacts": ["mutation_matrix"],
    "artifact_type": "sample_cluster_assignment", "entity_types": ["sample"],
    "granularity": "aggregate",
}


def test_a_uniquely_entailed_entity_needs_no_evidence_of_its_own():
    result = validate(CLUSTER, evidence(
        ("operation", "analyze"),
        ("input_artifact", "mutation_matrix"),
        ("artifact_type", "sample_cluster_assignment"),
    ))

    assert result.valid, result.issues


def test_a_uniquely_entailed_granularity_needs_no_evidence_of_its_own():
    assert ARTIFACT_SEMANTICS["sample_cluster_assignment"].granularities == frozenset({"aggregate"})

    result = validate(CLUSTER, evidence(
        ("operation", "analyze"),
        ("input_artifact", "mutation_matrix"),
        ("artifact_type", "sample_cluster_assignment"),
    ))

    assert "hypothesis[0].missing_evidence:granularity=aggregate" not in result.issues


def test_the_artifact_choice_itself_still_needs_evidence():
    result = validate(CLUSTER, evidence(
        ("operation", "analyze"), ("input_artifact", "mutation_matrix"),
    ))

    assert "hypothesis[0].missing_evidence:artifact_type=sample_cluster_assignment" in result.issues


def test_the_current_input_still_needs_evidence():
    result = validate(CLUSTER, evidence(
        ("operation", "analyze"), ("artifact_type", "sample_cluster_assignment"),
    ))

    assert "hypothesis[0].missing_evidence:input_artifact=mutation_matrix" in result.issues


def test_an_artifact_that_permits_several_entities_still_needs_evidence():
    """Two legal entities make the value a choice, so it must be justified."""
    assert len(ARTIFACT_SEMANTICS["pathway_mutation_matrix"].entities) > 1

    result = validate(
        {**CLUSTER, "artifact_type": "pathway_mutation_matrix",
         "entity_types": ["pathway"]},
        evidence(("operation", "analyze"), ("input_artifact", "mutation_matrix"),
                 ("artifact_type", "pathway_mutation_matrix")),
    )

    assert "hypothesis[0].missing_evidence:entity_type=pathway" in result.issues


def test_an_artifact_that_permits_several_granularities_still_needs_evidence():
    assert len(ARTIFACT_SEMANTICS["regulatory_network"].granularities) > 1

    result = validate(
        {"operation": "infer", "artifact_type": "regulatory_network",
         "entity_types": ["tf", "gene"], "regulator_types": ["tf"],
         "target_types": ["gene"], "granularity": "sample_specific"},
        evidence(("operation", "infer"), ("artifact_type", "regulatory_network"),
                 ("regulator_type", "tf"), ("target_type", "gene")),
        task="Build one TF-to-gene regulatory network per patient.",
    )

    assert "hypothesis[0].missing_evidence:granularity=sample_specific" in result.issues


@pytest.mark.parametrize("field, value, issue", [
    ("entity_types", ["gene"], "hypothesis[0].artifact_entity:sample_cluster_assignment"),
    ("granularity", "sample_specific", "hypothesis[0].artifact_granularity:sample_cluster_assignment"),
])
def test_a_value_the_artifact_forbids_is_still_rejected(field, value, issue):
    """Dropping the evidence demand must not drop the consistency check."""
    result = validate({**CLUSTER, field: value}, evidence(
        ("operation", "analyze"),
        ("input_artifact", "mutation_matrix"),
        ("artifact_type", "sample_cluster_assignment"),
    ))

    assert issue in result.issues
