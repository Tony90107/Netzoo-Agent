"""Workflow-independent output ontology shared by validation and rendering.

Entities describe the output, not every entity appearing in the input or in an
algorithm's intermediate calculations. Sample-specific means separately inferred
results per sample; a cohort's distance matrix or cluster labels are aggregate.
Unknown fields remain unresolved rather than being silently filled in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .outcomes import RequestedOutcome


@dataclass(frozen=True)
class ArtifactSemantics:
    description: str
    entities: frozenset[str] | None = None
    granularities: frozenset[str] | None = None


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
    "sample_cluster_assignment": ArtifactSemantics("Sample-to-cluster labels, separate from score and distance matrices", frozenset({"sample"}), frozenset({"aggregate"})),
    "community_assignment": ArtifactSemantics("Network-node community memberships, not patient subtype labels"),
    "validation_report": ArtifactSemantics("Validation findings, not an inferred network"),
    "unknown": ArtifactSemantics("Unresolved output type"),
}


def outcome_consistency_issues(outcome: RequestedOutcome) -> tuple[str, ...]:
    """Reject contradictions without choosing a workflow or resolving unknowns."""
    rule = ARTIFACT_SEMANTICS[outcome.artifact_type]
    issues = []
    known_entities = set(outcome.entity_types) - {"unknown"}
    if rule.entities is not None and not known_entities.issubset(rule.entities):
        issues.append(f"artifact_entity:{outcome.artifact_type}")
    if (rule.granularities is not None and outcome.granularity != "unknown"
            and outcome.granularity not in rule.granularities):
        issues.append(f"artifact_granularity:{outcome.artifact_type}")
    roles = {"regulator_type", "regulator_types", "target_type", "target_types"}
    if outcome.artifact_type not in {"regulatory_network", "unknown"} and (
        outcome.regulator_types or outcome.target_types
        or roles.intersection(outcome.unresolved_dimensions)
    ):
        issues.append(f"artifact_roles:{outcome.artifact_type}")
    if outcome.artifact_type == "regulatory_network":
        role_entities = (set(outcome.regulator_types) | set(outcome.target_types)) - {"unknown"}
        if known_entities and not role_entities.issubset(known_entities):
            issues.append("role_entity:regulatory_network")
    return tuple(issues)
