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
MUTATION_TASK = TASK


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


def test_whether_an_input_needs_evidence_depends_on_the_request():
    """Superseded the blanket demand: grounding the system already has counts.

    The same outcome and the same evidence: accepted when the request witnesses
    locate that input in the text themselves, rejected when they cannot.
    """
    items = evidence(("operation", "analyze"), ("artifact_type", "sample_cluster_assignment"))

    assert validate(CLUSTER, items, task=MUTATION_TASK).valid
    assert "hypothesis[0].missing_evidence:input_artifact=mutation_matrix" in validate(
        CLUSTER, items, task="Group my patients into subtypes.",
    ).issues


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


# The same reasoning reaches one more dimension, and stops there. The request
# witnesses locate current inputs in the original text on their own -- that is
# what raises `missing_current_input` when the outcome omits one. Where a listed
# input is the artifact those witnesses independently confirmed as current, the
# grounding has already been checked against the request, so asking the model to
# prove it again adds nothing. An input the witnesses cannot see is a different
# matter: there the model's evidence is the only grounding available.


def test_an_input_the_request_confirms_needs_no_evidence_of_its_own():
    result = validate(CLUSTER, evidence(
        ("operation", "analyze"), ("artifact_type", "sample_cluster_assignment"),
    ), task=MUTATION_TASK)

    assert result.valid, result.issues


def test_an_input_the_request_does_not_mention_still_needs_evidence():
    """Without an independent witness, the model's evidence is the only grounding."""
    result = validate(
        {**CLUSTER, "input_artifacts": ["coexpression_network"]},
        evidence(("operation", "analyze"), ("artifact_type", "sample_cluster_assignment")),
        task=MUTATION_TASK,
    )

    assert "hypothesis[0].missing_evidence:input_artifact=coexpression_network" in result.issues


def test_a_historical_input_is_not_treated_as_confirmed():
    task = "我之前用表現量矩陣跑過分析。現在我有體細胞突變矩陣。"
    result = validate(
        {**CLUSTER, "input_artifacts": ["expression_matrix"]},
        evidence(("operation", "analyze"), ("artifact_type", "sample_cluster_assignment")),
        task=task,
    )

    assert "hypothesis[0].missing_evidence:input_artifact=expression_matrix" in result.issues
    assert "hypothesis[0].noncurrent_input:expression_matrix" in result.issues


def test_omitting_a_confirmed_input_is_still_rejected():
    """Dropping the evidence demand must not drop the completeness demand."""
    result = validate(
        {**CLUSTER, "input_artifacts": []},
        evidence(("operation", "analyze"), ("artifact_type", "sample_cluster_assignment")),
        task=MUTATION_TASK,
    )

    assert "hypothesis[0].missing_current_input:mutation_matrix" in result.issues
