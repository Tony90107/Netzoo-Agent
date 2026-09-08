"""How compatible capabilities are ordered once more than one still fits.

Split out of `outcome_matching` when that module passed the reviewable-size
limit, at a real seam rather than a convenient cut. Everything here is a
*preference*: each candidate it orders has already been found compatible, and
what these express is which of them the system leans toward when the request
does not say. `match_requested_outcome` decides separately whether a preference
is allowed to make an answer exact -- keeping that decision away from the
preferences themselves is the reason they live apart.

Nothing outside this module imports them, and nothing here reaches past the
registry and contract types, so it sits below the rest of routing with no cycle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from workflow_registry import OutputCapabilityDefinition

from ..contracts.outcomes import OutcomeHypothesis, RequestedOutcome

__all__: list[str] = []

#: The closed-vocabulary value meaning the request did not decide.
_UNKNOWN = "unknown"


def _specificity_score(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> int:
    """Excess a capability carries beyond what the request asked for.

    Roles and entities count: a capability that also handles regulators the
    request never mentioned may need priors the user does not have, which is why
    a `tf`-only request should prefer LIONESS-PANDA over LIONESS-PUMA.

    Granularity breadth does **not** count, and used to. The request names one
    value and every candidate here supports it; that one of them also supports
    another granularity says nothing about this request. That term alone let
    BONOBO beat LIONESS-coexpression, and with `sample` declared as an entity it
    produced this study's only wrong-tool recommendations.
    """
    return (
        len(capability.entity_types - set(outcome.entity_types))
        + len(capability.regulator_types - set(outcome.regulator_types))
        + len(capability.target_types - set(outcome.target_types))
        + len(capability.guidance_predecessors)
    )

def stated_dimension_score(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> int:
    """`_specificity_score`, restricted to dimensions the request actually states.

    The full score also prefers the narrower capability on dimensions the
    outcome left empty, and on `guidance_predecessors`, which an outcome cannot
    speak to at all. That is this system's preference, not the request's. It may
    order candidates; it must not be what makes an answer exact. A request that
    never said which entities it wants has not chosen between two capabilities
    differing only there, however sensible the default -- and reporting that as
    an exact match is what let a trial where the model supplied no distinguishing
    dimension score the same as one where it did.

    An earlier round rejected the blunt form of this rule -- never exact while
    several candidates remain -- and was right to: a `tf`-only request
    preferring LIONESS-PANDA over LIONESS-PUMA reflects a real difference, since
    PUMA needs miRNA priors the user does not have. That case survives here,
    because the request did state `regulator_types` and the restricted score
    still separates them. Only the preferences the request said nothing about
    lose their power to make a match exact.
    """
    return (
        (len(capability.entity_types - set(outcome.entity_types))
         if outcome.entity_types else 0)
        + (len(capability.regulator_types - set(outcome.regulator_types))
           if outcome.regulator_types else 0)
        + (len(capability.target_types - set(outcome.target_types))
           if outcome.target_types else 0)
    )


def _hypothesis_evidence_score(hypothesis: OutcomeHypothesis) -> int:
    return sum(2 if item.source == "explicit" else 1 for item in hypothesis.evidence)

def _advisory_specificity_penalty(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> int:
    """Penalize extra biological roles only when the user specified that role."""
    requested_entities = set(outcome.entity_types) - {_UNKNOWN}
    requested_regulators = set(outcome.regulator_types) - {_UNKNOWN}
    requested_targets = set(outcome.target_types) - {_UNKNOWN}
    return (
        (len(capability.entity_types - requested_entities) if requested_entities else 0)
        + (
            len(capability.regulator_types - requested_regulators)
            if requested_regulators
            else 0
        )
        + (len(capability.target_types - requested_targets) if requested_targets else 0)
    )

def _explicit_evidence_specificity_penalty(
    evidence: Mapping[str, set[str]],
    capability: OutputCapabilityDefinition,
) -> int:
    """Rank evidence-compatible candidates without reintroducing inferred fields."""
    requested_entities = evidence.get("entity_type", set())
    requested_regulators = evidence.get("regulator_type", set())
    requested_targets = evidence.get("target_type", set())
    return (
        (len(capability.entity_types - requested_entities) if requested_entities else 0)
        + (
            len(capability.regulator_types - requested_regulators)
            if requested_regulators
            else 0
        )
        + (len(capability.target_types - requested_targets) if requested_targets else 0)
    )
