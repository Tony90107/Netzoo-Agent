"""Semantic consistency checks for bounded Router outcome hypotheses."""

from __future__ import annotations

import json
from collections.abc import Sequence

from ..contracts import OutcomeEvidence, OutcomeHypothesis
from .request_integrity import granularity_left_open, granularity_mentions

__all__ = [
    "needs_outcome_repair",
    "select_primary_hypothesis",
    "complete_open_granularity_alternatives",
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
    wording or the provider's `in_scope` flag. The graph now uses the stricter
    evidence validator before invoking the dedicated semantic interpreter; this
    helper remains the compatibility check for callers that only have hypotheses.
    """
    return not any(_has_usable_evidence(item) for item in hypotheses)


def complete_open_granularity_alternatives(
    user_task: str,
    hypotheses: Sequence[OutcomeHypothesis],
) -> list[OutcomeHypothesis]:
    """Represent both literal granularity choices when the request leaves them open.

    This only expands a single shared scientific outcome whose hypotheses differ
    in granularity or its unresolved marker. Distinct artifact, role, input, or
    assumption readings remain untouched.
    """
    original = list(hypotheses)
    if not granularity_left_open(user_task) or not original:
        return original
    spans = {
        mention.granularity: mention.text_span
        for mention in granularity_mentions(user_task)
    }
    alternatives = ("aggregate", "sample_specific")
    if any(value not in spans for value in alternatives):
        return original

    def signature(item: OutcomeHypothesis) -> str:
        outcome = item.outcome.model_dump(mode="json")
        outcome.pop("granularity", None)
        outcome["unresolved_dimensions"] = [
            value for value in outcome["unresolved_dimensions"]
            if "granularity" not in value.casefold()
        ]
        return json.dumps(
            {"outcome": outcome, "assumptions": item.assumptions},
            sort_keys=True,
        )

    if len({signature(item) for item in original}) != 1:
        return original

    template = max(original, key=lambda item: item.confidence)
    shared_evidence: dict[str, OutcomeEvidence] = {}
    for item in original:
        for evidence in item.evidence:
            if evidence.dimension == "granularity":
                continue
            key = json.dumps(evidence.model_dump(mode="json"), sort_keys=True)
            shared_evidence[key] = evidence

    result = []
    for granularity in alternatives:
        outcome = template.outcome.model_copy(update={
            "granularity": granularity,
            "unresolved_dimensions": [
                value for value in template.outcome.unresolved_dimensions
                if "granularity" not in value.casefold()
            ],
        })
        evidence = [
            *shared_evidence.values(),
            OutcomeEvidence(
                dimension="granularity",
                value=granularity,
                source="explicit",
                text_span=spans[granularity],
                rationale=(
                    "The user explicitly names this as one of the undecided "
                    "granularity alternatives."
                ),
            ),
        ]
        result.append(template.model_copy(update={
            "outcome": outcome,
            "confidence": max(item.confidence for item in original),
            "evidence": evidence,
        }))
    return result


def select_primary_hypothesis(
    hypotheses: Sequence[OutcomeHypothesis],
    *,
    user_task: str = "",
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
    granularity_open = bool(user_task and granularity_left_open(user_task))
    tied = len(scored) > 1 and best[:2] == scored[-2][:2]
    if tied:
        if not granularity_open:
            return None
        top_outcomes = [
            item[3].outcome.model_dump(
                exclude={"granularity", "unresolved_dimensions"}
            )
            for item in scored if item[:2] == best[:2]
        ]
        if any(outcome != top_outcomes[0] for outcome in top_outcomes[1:]):
            return None
    primary = best[3]
    if (
        granularity_open
        and primary.outcome.granularity in {"aggregate", "sample_specific"}
    ):
        # Hypotheses may rank a plausible alternative above the neutral reading
        # because inferred evidence adds to the evidence score. A request that
        # explicitly leaves granularity undecided has not selected that result;
        # keep the strongest shared outcome fields while withholding this one.
        unresolved = list(dict.fromkeys([
            *primary.outcome.unresolved_dimensions,
            "granularity",
        ]))[:4]
        outcome = primary.outcome.model_copy(update={
            "granularity": "unknown",
            "unresolved_dimensions": unresolved,
        })
        return primary.model_copy(update={
            "outcome": outcome,
            "evidence": [
                item for item in primary.evidence
                if item.dimension != "granularity"
            ],
        })
    if (
        granularity_open
        and primary.outcome.granularity == "unknown"
        and "granularity" not in primary.outcome.unresolved_dimensions
    ):
        outcome = primary.outcome.model_copy(update={
            "unresolved_dimensions": list(dict.fromkeys([
                *primary.outcome.unresolved_dimensions,
                "granularity",
            ]))[:4],
        })
        return primary.model_copy(update={"outcome": outcome})
    return primary
