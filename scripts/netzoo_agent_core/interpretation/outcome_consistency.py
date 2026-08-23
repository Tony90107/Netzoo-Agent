"""Semantic consistency checks for bounded Router outcome hypotheses."""

from __future__ import annotations

from collections.abc import Sequence
import re

from ..contracts import OutcomeEvidence, OutcomeHypothesis, RequestedOutcome
from ..routing.capability import is_workflow_selection_request

__all__ = [
    "deterministic_explicit_outcome_hypotheses",
    "needs_outcome_repair",
    "select_primary_hypothesis",
]


_SAMPLE_SPECIFIC_PATTERN = re.compile(
    r"(?:sample[\s_-]*(?:specific|spefic|specfic)|per[\s_-]*sample|"
    r"individual[\s_-]*specific|樣本(?:特異|特定)|個體(?:特異|特定|化))",
    flags=re.IGNORECASE,
)
_MIRNA_PATTERN = re.compile(
    r"(?:mi[\s_-]*rna|mirna|micro[\s_-]*rna|微小\s*rna)",
    flags=re.IGNORECASE,
)
_REGULATORY_NETWORK_PATTERN = re.compile(
    r"(?:regulat(?:ory|ion|or).{0,20}network|調控.{0,8}網路|network\s+inference)",
    flags=re.IGNORECASE,
)


def deterministic_explicit_outcome_hypotheses(task: str) -> list[OutcomeHypothesis]:
    """Recover one typed outcome only when every required signal is explicit.

    This is deliberately narrower than workflow inference: it describes the
    requested scientific result and leaves workflow selection to the registry.
    Missing any one of selection intent, artifact, regulator, or granularity
    keeps the fallback closed.
    """
    if not (
        is_workflow_selection_request(task)
        and _SAMPLE_SPECIFIC_PATTERN.search(task)
        and _MIRNA_PATTERN.search(task)
        and _REGULATORY_NETWORK_PATTERN.search(task)
    ):
        return []

    return [
        OutcomeHypothesis(
            outcome=RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["mirna"],
                display_entities=["miRNA"],
                regulator_types=["mirna"],
                target_types=[],
                granularity="sample_specific",
                unresolved_dimensions=[],
            ),
            confidence=0.95,
            evidence=[
                OutcomeEvidence(
                    dimension="operation",
                    value="infer",
                    source="inferred",
                    rationale=(
                        "Asking which tool produces the named network implies "
                        "network inference, without selecting a workflow."
                    ),
                ),
                OutcomeEvidence(
                    dimension="artifact_type",
                    value="regulatory_network",
                    source="explicit",
                    rationale="The request explicitly names a regulatory network.",
                ),
                OutcomeEvidence(
                    dimension="regulator_type",
                    value="mirna",
                    source="explicit",
                    rationale="The request explicitly names miRNA regulators.",
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for sample-specific output.",
                ),
            ],
            assumptions=[],
        )
    ]


def _has_usable_evidence(hypothesis: OutcomeHypothesis) -> bool:
    outcome = hypothesis.outcome
    return bool(
        hypothesis.evidence
        or outcome.operation != "unknown"
        or outcome.artifact_type != "unknown"
        or outcome.granularity not in {"unknown", "not_applicable"}
        or set(outcome.entity_types) - {"unknown"}
        or set(outcome.regulator_types) - {"unknown"}
        or set(outcome.target_types) - {"unknown"}
    )


def needs_outcome_repair(
    hypotheses: Sequence[OutcomeHypothesis],
) -> bool:
    """Return True when a Router response has no usable semantic evidence.

    This deliberately inspects the typed response shape, not terms in the user's
    wording or the provider's `in_scope` flag.  Every under-classification gets
    one bounded repair attempt. If that attempt also lacks evidence, only a
    narrow deterministic typed-outcome recovery may add evidence; otherwise
    later gates keep the result at `no_tool`.
    """
    return not any(_has_usable_evidence(item) for item in hypotheses)


def select_primary_hypothesis(
    hypotheses: Sequence[OutcomeHypothesis],
) -> OutcomeHypothesis | None:
    """Select one evidence-leading hypothesis while preserving equal-score ties."""
    scored = sorted(
        (
            sum(
                2 if item.source == "explicit" else 1
                for item in hypothesis.evidence
            ),
            hypothesis.confidence,
            index,
            hypothesis,
        )
        for index, hypothesis in enumerate(hypotheses)
    )
    if not scored:
        return None
    best = scored[-1]
    if len(scored) > 1 and best[:2] == scored[-2][:2]:
        return None
    return best[3]
