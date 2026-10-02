"""Workflow-independent output ontology shared by validation and rendering.

Entities describe the output, not every entity appearing in the input or in an
algorithm's intermediate calculations. Sample-specific means separately inferred
results per sample; a cohort's distance matrix or cluster labels are aggregate.
Unknown fields remain unresolved rather than being silently filled in.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol
from .repair_scope import Issue


class OutcomeFields(Protocol):
    operation: str
    artifact_type: str
    input_artifacts: list[str]
    entity_types: list[str]
    granularity: str
    regulator_types: list[str]
    target_types: list[str]
    unresolved_dimensions: list[str]


#: Operations that ask for an explanation rather than for a result. A request
#: of this shape produces no artifact, so no capability can satisfy it and
#: none should be offered.
NO_RESULT_OPERATIONS = frozenset({"unknown", "explain"})


def is_outcome_not_applicable(outcome: OutcomeFields) -> bool:
    """True when the request asks for no result at all.

    This predicate existed twice -- once in interpretation, once in capability
    matching -- and the two copies disagreed. Validation accepted `explain`
    while matching required `unknown`, so a concept question read correctly as
    `explain` passed validation and then came back from the matcher as
    `ambiguous`: the reader was asked a clarifying question instead of being
    answered. One definition is the only thing that keeps the two layers from
    drifting apart again.
    """
    return (
        outcome.operation in NO_RESULT_OPERATIONS
        and outcome.artifact_type == "unknown"
        and outcome.granularity == "not_applicable"
        and not outcome.input_artifacts
        and not outcome.entity_types
        and not outcome.regulator_types
        and not outcome.target_types
        and not outcome.unresolved_dimensions
    )


def is_acquisition_without_result_granularity(outcome: OutcomeFields) -> bool:
    """True when an acquisition asks for an existing artifact, not a result.

    Granularity in this ontology describes the scientific result an operation
    produces (for example, an aggregate or per-sample inferred network). A
    request to download an existing artifact has no *produced result*
    granularity. This is distinct from a no-result question: acquisition still
    requires a grounded operation and must proceed through its own capability.
    """
    return (
        outcome.operation == "acquire"
        and outcome.granularity == "not_applicable"
        and (
            outcome.artifact_type != "unknown"
            or (
                not outcome.input_artifacts
                and not outcome.entity_types
                and not outcome.regulator_types
                and not outcome.target_types
                and not outcome.unresolved_dimensions
            )
        )
    )


@dataclass(frozen=True)
class ArtifactSemantics:
    """What an artifact is, and what a request may say about it.

    ``operations`` are the operations a request may ask *about* this artifact.
    Any artifact can be the subject of a question, so restricting this set
    rejects guidance -- "which tools produce a regulatory network?" carries the
    operation ``explain``, not the operation that would build one.

    ``produced_by`` answers the different question of which operation creates
    the artifact. Where exactly one does, naming it in a request adds nothing
    that choosing the artifact had not already established, so evidence for it
    is not required. It constrains nothing: an artifact with a single producing
    operation can still be explained, analyzed or acquired.
    """

    description: str
    entities: frozenset[str] | None = None
    granularities: frozenset[str] | None = None
    operations: frozenset[str] | None = None
    produced_by: frozenset[str] | None = None


ARTIFACT_SEMANTICS = {
    "measurement_dataset": ArtifactSemantics("Source measurements, not an inferred network"),
    "expression_matrix": ArtifactSemantics("Gene-by-sample expression measurements", frozenset({"gene", "sample"})),
    "tf_activity_matrix": ArtifactSemantics(
        "Inferred transcription-factor-by-sample activity values",
        frozenset({"tf", "sample"}),
        frozenset({"aggregate"}),
        frozenset({"infer"}),
    ),
    "regulatory_network_and_tf_activity": ArtifactSemantics(
        "A jointly inferred TF-gene regulatory network and TF-by-sample activity matrix",
        frozenset({"tf", "gene", "sample"}),
        frozenset({"aggregate"}),
        frozenset({"infer"}),
    ),
    "signed_regulatory_effect_network": ArtifactSemantics(
        "A TF-gene network whose signed partial effects are linear-model coefficients",
        frozenset({"tf", "gene"}),
        frozenset({"aggregate"}),
        frozenset({"infer"}),
    ),
    "mutation_matrix": ArtifactSemantics("Gene-by-sample mutation measurements", frozenset({"gene", "sample"})),
    "regulatory_network": ArtifactSemantics(
        "Inferred regulator-to-target associations",
        granularities=frozenset({"aggregate", "sample_specific"}),
        produced_by=frozenset({"infer"}),
    ),
    "coexpression_network": ArtifactSemantics("Inferred gene-to-gene associations", frozenset({"gene", "sample"}), frozenset({"aggregate", "sample_specific"})),
    "pvalue_matrix": ArtifactSemantics(
        "P-value matrix paired with a sample-specific gene-gene co-expression result",
        frozenset({"gene", "sample"}),
        frozenset({"sample_specific"}),
        frozenset({"infer"}),
    ),
    "multi_omic_network": ArtifactSemantics("Inferred associations between omics features", granularities=frozenset({"aggregate", "sample_specific"})),
    "gene_mutation_scores": ArtifactSemantics("Sample-by-gene mutation scores, not pathway scores", frozenset({"gene", "sample"}), frozenset({"aggregate"})),
    "pathway_mutation_matrix": ArtifactSemantics("Pathway-by-sample mutation scores, not cluster labels", frozenset({"pathway", "sample"}), frozenset({"aggregate"})),
    "sample_distance_matrix": ArtifactSemantics("Pairwise sample distances, not cluster labels", frozenset({"sample"}), frozenset({"aggregate"})),
    "sample_cluster_assignment": ArtifactSemantics(
        "Sample-to-cluster labels, separate from score and distance matrices",
        frozenset({"sample"}),
        frozenset({"aggregate"}),
        frozenset({"analyze"}),
    ),
    # One partition of one network, not one partition per sample, so the single
    # legal value is aggregate. Leaving this unconstrained made every CONDOR-
    # selecting outcome require granularity=not_applicable, which the semantic
    # prompt reserves for a request with no scientific result at all.
    "community_assignment": ArtifactSemantics("Network-node community memberships, not patient subtype labels", granularities=frozenset({"aggregate"})),
    "validation_report": ArtifactSemantics("Validation findings, not an inferred network"),
    "unknown": ArtifactSemantics("Unresolved output type"),
}


# Composite terminal results are ontology-level conjunctions. A capability
# supports one exactly when it declares every concrete component as an output;
# the mapping never names a workflow and therefore also applies to future
# implementations that expose the same result pair.
ARTIFACT_COMPONENTS: dict[str, frozenset[str]] = {
    "regulatory_network_and_tf_activity": frozenset(
        {"regulatory_network", "tf_activity_matrix"}
    ),
}


_REGULATORY_ARTIFACTS = frozenset(
    {
        "regulatory_network",
        "regulatory_network_and_tf_activity",
        "signed_regulatory_effect_network",
        "unknown",
    }
)


def artifact_field_constraints(artifact: str) -> dict:
    """Generation constraints from the same ontology used by strict validation."""
    rule = ARTIFACT_SEMANTICS[artifact]
    fields = {"artifact_type": {"const": artifact}}
    if rule.operations is not None:
        fields["operation"] = {"enum": sorted(rule.operations | {"unknown"})}
    if rule.entities is not None:
        fields["entity_types"] = {"items": {"enum": sorted(rule.entities | {"unknown"})}}
    if rule.granularities is not None:
        fields["granularity"] = {"enum": sorted(rule.granularities | {"unknown"})}
    if artifact not in _REGULATORY_ARTIFACTS:
        fields.update(regulator_types={"maxItems": 0}, target_types={"maxItems": 0})
    return fields


def artifacts_supporting_regulatory_roles(
    roles: Iterable[tuple[str, str]],
) -> frozenset[str]:
    """Return ontology artifacts that can carry every witnessed regulator/target role."""
    role_entities = {
        entity
        for regulator, target in roles
        for entity in (regulator, target)
        if entity != "unknown"
    }
    if not role_entities:
        return frozenset()
    return frozenset(
        artifact
        for artifact, rule in ARTIFACT_SEMANTICS.items()
        if artifact != "unknown"
        and artifact in _REGULATORY_ARTIFACTS
        and (rule.entities is None or role_entities.issubset(rule.entities))
    )


def outcome_consistency_issues(outcome: OutcomeFields) -> tuple[str, ...]:
    """Reject contradictions without choosing a workflow or resolving unknowns."""
    rule = ARTIFACT_SEMANTICS[outcome.artifact_type]
    issues = []
    known_entities = set(outcome.entity_types) - {"unknown"}
    # Each rule declares the fields it just read. Written here rather than in a
    # table elsewhere so the declaration cannot drift from the comparison.
    if rule.entities is not None and not known_entities.issubset(rule.entities):
        issues.append(Issue(
            f"artifact_entity:{outcome.artifact_type}",
            {"entity_types", "artifact_type"},
        ))
    if (rule.granularities is not None and outcome.granularity != "unknown"
            and not is_acquisition_without_result_granularity(outcome)
            and outcome.granularity not in rule.granularities):
        issues.append(Issue(
            f"artifact_granularity:{outcome.artifact_type}",
            {"granularity", "artifact_type"},
        ))
    roles = {"regulator_type", "regulator_types", "target_type", "target_types"}
    if outcome.artifact_type not in _REGULATORY_ARTIFACTS and (
        outcome.regulator_types or outcome.target_types
        or roles.intersection(outcome.unresolved_dimensions)
    ):
        issues.append(Issue(
            f"artifact_roles:{outcome.artifact_type}",
            {"regulator_types", "target_types", "unresolved_dimensions",
             "artifact_type"},
        ))
    if outcome.artifact_type in {
        "regulatory_network",
        "regulatory_network_and_tf_activity",
        "signed_regulatory_effect_network",
    }:
        role_entities = (set(outcome.regulator_types) | set(outcome.target_types)) - {"unknown"}
        if known_entities and not role_entities.issubset(known_entities):
            issues.append(Issue(
                "role_entity:regulatory_network",
                {"entity_types", "regulator_types", "target_types"},
            ))
    return tuple(issues)


def fields_opened_by_artifact(artifact_type: str) -> frozenset[str]:
    """The fields an artifact's own ontology constrains.

    Read from `ARTIFACT_SEMANTICS` rather than listed here: when a review is
    allowed to correct `artifact_type`, the fields the new artifact governs have
    to move with it or the result is a combination the ontology forbids.
    """
    rule = ARTIFACT_SEMANTICS.get(artifact_type)
    if rule is None:
        return frozenset()
    opened = {"artifact_type"}
    if rule.entities is not None:
        opened.add("entity_types")
    if rule.operations is not None:
        opened.add("operation")
    if rule.granularities is not None:
        opened.add("granularity")
    return frozenset(opened)
