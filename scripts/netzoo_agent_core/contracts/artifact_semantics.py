"""Workflow-independent output ontology shared by validation and rendering.

Entities describe the output, not every entity appearing in the input or in an
algorithm's intermediate calculations. Sample-specific means separately inferred
results per sample; a cohort's distance matrix or cluster labels are aggregate.
Unknown fields remain unresolved rather than being silently filled in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from .repair_scope import Issue


class OutcomeFields(Protocol):
    operation: str
    artifact_type: str
    entity_types: list[str]
    granularity: str
    regulator_types: list[str]
    target_types: list[str]
    unresolved_dimensions: list[str]


@dataclass(frozen=True)
class ArtifactSemantics:
    description: str
    entities: frozenset[str] | None = None
    granularities: frozenset[str] | None = None
    operations: frozenset[str] | None = None


ARTIFACT_SEMANTICS = {
    "measurement_dataset": ArtifactSemantics("Source measurements, not an inferred network"),
    "expression_matrix": ArtifactSemantics("Gene-by-sample expression measurements", frozenset({"gene", "sample"})),
    "mutation_matrix": ArtifactSemantics("Gene-by-sample mutation measurements", frozenset({"gene", "sample"})),
    "regulatory_network": ArtifactSemantics("Inferred regulator-to-target associations", granularities=frozenset({"aggregate", "sample_specific"})),
    "coexpression_network": ArtifactSemantics("Inferred gene-to-gene associations", frozenset({"gene", "sample"}), frozenset({"aggregate", "sample_specific"})),
    "multi_omic_network": ArtifactSemantics("Inferred associations between omics features", granularities=frozenset({"aggregate", "sample_specific"})),
    "gene_mutation_scores": ArtifactSemantics("Gene-by-sample mutation scores, not pathway scores", frozenset({"gene", "sample"}), frozenset({"aggregate"})),
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
    if artifact not in {"regulatory_network", "unknown"}:
        fields.update(regulator_types={"maxItems": 0}, target_types={"maxItems": 0})
    return fields


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
            and outcome.granularity not in rule.granularities):
        issues.append(Issue(
            f"artifact_granularity:{outcome.artifact_type}",
            {"granularity", "artifact_type"},
        ))
    roles = {"regulator_type", "regulator_types", "target_type", "target_types"}
    if outcome.artifact_type not in {"regulatory_network", "unknown"} and (
        outcome.regulator_types or outcome.target_types
        or roles.intersection(outcome.unresolved_dimensions)
    ):
        issues.append(Issue(
            f"artifact_roles:{outcome.artifact_type}",
            {"regulator_types", "target_types", "unresolved_dimensions",
             "artifact_type"},
        ))
    if outcome.artifact_type == "regulatory_network":
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
