"""Inspect the single-source claims projection before downstream normalization.

Projection is mechanical, not proof of meaning. Keep inferred and unverified
support visible, and run the same validator used by the legacy contract.
The routing caller must still validate after any deterministic restoration.
"""
from dataclasses import dataclass

from ..contracts.outcomes import OutcomeEvidence, SemanticInterpretation
from ..contracts.semantic_claims import DIMENSIONS, SemanticClaims
from .outcome_validation import (
    OutcomeValidation, explicit_evidence_grounded, validate_outcome_hypotheses,
)


@dataclass(frozen=True, slots=True)
class ClaimProjection:
    interpretation: SemanticInterpretation
    validation: OutcomeValidation
    facts: tuple[dict, ...]


def project_claims(user_task: str, claims: SemanticClaims) -> ClaimProjection:
    """Return an independent projection, validation result and source addresses.

    Failed claims are retained for bounded repair, never silently discarded to
    make a projection pass. quote_grounded means quote alignment only; ontology
    and request-integrity failures remain in validation, including negation.
    """
    interpretation = claims.to_internal()
    validation = validate_outcome_hypotheses(
        user_task, interpretation.outcome_hypotheses, claims.request_mode,
    )
    facts = []
    for index, hypothesis in enumerate(claims.outcome_hypotheses):
        for field, dimension in DIMENSIONS.items():
            value = getattr(hypothesis.outcome, field)
            many = isinstance(value, list)
            for position, claim in enumerate(value if many else [value]):
                path = f"outcome_hypotheses.{index}.outcome.{field}"
                if many:
                    path += f".{position}"
                if claim.value in {"unknown", "not_applicable"}:
                    status = "unresolved"
                elif claim.support.source == "inferred":
                    status = "inferred"
                else:
                    evidence = OutcomeEvidence(
                        dimension=dimension, value=claim.value, **claim.support.model_dump(),
                    )
                    status = ("quote_grounded" if explicit_evidence_grounded(user_task, evidence)
                              else "quote_unverified")
                facts.append({
                    "hypothesis": index, "field": field, "value": claim.value,
                    "claim_path": path, "support_path": path + ".support",
                    "support_status": status,
                })
    return ClaimProjection(interpretation, validation, tuple(facts))
