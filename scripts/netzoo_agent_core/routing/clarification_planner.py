"""Choose the smallest scientific question that separates routed candidates.

The planner is deliberately independent of the CLI and HTTP surfaces.  It is a
pure domain service: callers supply the already-qualified candidates and receive
one structured decision that any presentation layer can render.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import log2

from workflow_registry import (
    OUTPUT_CAPABILITIES,
    SELECTION_TAG_GLOSSARY,
    OutputCapabilityDefinition,
    RecommendedAction,
)

from ..contracts import RequestedOutcome


@dataclass(frozen=True, slots=True)
class ClarificationOption:
    """One user-facing answer and the candidates it preserves."""

    value: str
    label: str
    candidate_actions: tuple[RecommendedAction, ...]


@dataclass(frozen=True, slots=True)
class CandidateDifference:
    """A candidate partition along one scientific decision dimension."""

    dimension: str
    information_gain: float
    score: float
    options: tuple[ClarificationOption, ...]


@dataclass(frozen=True, slots=True)
class ClarificationDecision:
    """The highest-value next question for an ambiguous candidate set."""

    dimension: str
    question: str
    information_gain: float
    options: tuple[ClarificationOption, ...]
    candidate_actions: tuple[RecommendedAction, ...]


_UNKNOWN = "unknown"
_INPUT_LABELS = {
    "expression_matrix": "gene-expression matrix",
    "mirna_prior": "miRNA prior",
    "motif_prior": "TF-motif prior",
    "ppi_prior": "protein-interaction prior",
}
_NON_ALGORITHMIC_TAGS = {
    "aggregate_network",
    "coexpression",
    "lioness_base_compatibility",
    "mirna_regulation",
    "multi_omic_network",
    "sample_specific",
    "tf_gene_regulation",
    "tfa",
}
_ALGORITHM_LABELS = {
    "bayesian": "Bayesian shrinkage",
    "biologically_informed_matrix_factorization": "biologically informed matrix factorization",
    "joint_grn_tfa_inference": "joint GRN and TF-activity inference",
    "message_passing": "iterative message passing",
    "partial_correlation": "partial-correlation estimation",
    "relaxed_graph_matching": "continuous relaxed graph matching",
    "signed_partial_regulatory_effects": "signed partial regulatory effects",
}


def algorithm_selection_tags(selection_tags: Iterable[str]) -> tuple[str, ...]:
    """Return the registered method signals used to compare candidate workflows."""
    return tuple(sorted(set(selection_tags) - _NON_ALGORITHMIC_TAGS))


def algorithmic_assumptions_for(selection_tags: Iterable[str]) -> tuple[str, ...]:
    """Explain registered method signals using the shared registry glossary."""
    return tuple(
        SELECTION_TAG_GLOSSARY[tag]
        for tag in algorithm_selection_tags(selection_tags)
        if tag in SELECTION_TAG_GLOSSARY
    )


def _partition_gain(groups: Mapping[tuple[str, ...], Sequence[str]]) -> float:
    total = sum(len(items) for items in groups.values())
    if total < 2 or len(groups) < 2:
        return 0.0
    return -sum(
        (len(items) / total) * log2(len(items) / total)
        for items in groups.values()
    )


def _outcome_is_unresolved(
    outcomes: Sequence[RequestedOutcome],
    dimension: str,
) -> bool:
    if not outcomes:
        return True
    if dimension == "artifact_type":
        values = {item.artifact_type for item in outcomes}
        return _UNKNOWN in values or len(values) > 1
    if dimension == "granularity":
        values = {item.granularity for item in outcomes}
        return _UNKNOWN in values or len(values) > 1
    if dimension == "regulator_type":
        values = {tuple(sorted(item.regulator_types)) for item in outcomes}
        return not all(values) or len(values) > 1
    return False


def _label_values(dimension: str, values: tuple[str, ...]) -> str:
    if dimension == "artifact_type":
        return " + ".join(value.replace("_", " ") for value in values)
    if dimension == "granularity":
        labels = {
            "aggregate": "one cohort-wide result",
            "sample_specific": "one result per sample",
        }
        return " or ".join(labels.get(value, value.replace("_", " ")) for value in values)
    if dimension == "regulator_type":
        labels = {"tf": "transcription factors", "mirna": "miRNA regulators"}
        return " and ".join(labels.get(value, value) for value in values) or "no regulator role"
    if dimension == "required_input":
        return " + ".join(_INPUT_LABELS.get(value, value.replace("_", " ")) for value in values)
    return " + ".join(values)


def _question_for(
    dimension: str,
    options: Sequence[ClarificationOption],
) -> str:
    if dimension == "artifact_type":
        return "What artifact should NetZoo produce?"
    if dimension == "granularity":
        return "Should the result be aggregate or sample-specific?"
    if dimension == "regulator_type":
        return (
            "Which regulator type should the network model: transcription factors, "
            "miRNA regulators, or both?"
        )
    if dimension == "required_input":
        choices = "; ".join(option.label for option in options[:3])
        return f"Which input bundle do you currently have: {choices}?"[:300]
    choices = "; ".join(option.label for option in options[:3])
    if len(choices) <= 215:
        return f"Which modeling assumption best matches your experiment: {choices}?"
    return "Which modeling assumption or algorithmic objective best matches your experiment?"


class ClarificationPlanner:
    """Rank candidate-difference questions by information gain and user cost."""

    def __init__(
        self,
        capabilities: Mapping[
            RecommendedAction, OutputCapabilityDefinition
        ] = OUTPUT_CAPABILITIES,
    ) -> None:
        self._capabilities = capabilities

    def candidate_differences(
        self,
        candidates: Sequence[RecommendedAction],
        *,
        outcomes: Sequence[RequestedOutcome] = (),
    ) -> tuple[CandidateDifference, ...]:
        actions = tuple(dict.fromkeys(
            action for action in candidates if action in self._capabilities
        ))
        if len(actions) < 2:
            return ()

        capabilities = {action: self._capabilities[action] for action in actions}
        value_sets: dict[str, dict[RecommendedAction, tuple[str, ...]]] = {
            "artifact_type": {
                action: tuple(sorted(capability.produced_artifacts or {capability.artifact_type}))
                for action, capability in capabilities.items()
            },
            "granularity": {
                action: tuple(sorted(capability.granularities))
                for action, capability in capabilities.items()
            },
            "regulator_type": {
                action: tuple(sorted(capability.regulator_types))
                for action, capability in capabilities.items()
            },
            "required_input": {
                action: tuple(sorted(capability.required_input_artifacts))
                for action, capability in capabilities.items()
            },
        }

        tag_counts = Counter(
            tag for capability in capabilities.values() for tag in capability.selection_tags
        )
        algorithm_values: dict[RecommendedAction, tuple[str, ...]] = {}
        for action, capability in capabilities.items():
            method_tags = set(algorithm_selection_tags(capability.selection_tags))
            distinctive = sorted(
                method_tags or capability.selection_tags,
                key=lambda tag: (
                    tag_counts[tag],
                    len(SELECTION_TAG_GLOSSARY.get(tag, tag)),
                    tag,
                ),
            )
            algorithm_values[action] = tuple(distinctive[:1])
        value_sets["algorithm"] = algorithm_values

        differences = []
        # A small cost model keeps questions at the user's scientific altitude:
        # output and biological choices beat method jargon when both separate
        # equally well; execution prerequisites come after scientific intent.
        costs = {
            "artifact_type": 0.00,
            "granularity": 0.05,
            "regulator_type": 0.10,
            "algorithm": 0.25,
            "required_input": 0.35,
        }
        for dimension, action_values in value_sets.items():
            groups: dict[tuple[str, ...], list[RecommendedAction]] = defaultdict(list)
            for action, values in action_values.items():
                groups[values].append(action)
            gain = _partition_gain(groups)
            if gain <= 0:
                continue
            unresolved_bonus = (
                0.75 if _outcome_is_unresolved(outcomes, dimension) else 0.0
            )
            options = tuple(
                ClarificationOption(
                    value="|".join(values),
                    label=(
                        _ALGORITHM_LABELS.get(
                            values[0],
                            SELECTION_TAG_GLOSSARY.get(
                                values[0], values[0].replace("_", " ")
                            ),
                        )
                        if dimension == "algorithm" and values
                        else _label_values(dimension, values)
                    ),
                    candidate_actions=tuple(group_actions),
                )
                for values, group_actions in sorted(groups.items())
            )
            differences.append(CandidateDifference(
                dimension=dimension,
                information_gain=gain,
                score=gain + unresolved_bonus - costs[dimension],
                options=options,
            ))
        return tuple(sorted(
            differences,
            key=lambda item: (-item.score, -item.information_gain, item.dimension),
        ))

    def plan(
        self,
        candidates: Sequence[RecommendedAction],
        *,
        outcomes: Sequence[RequestedOutcome] = (),
    ) -> ClarificationDecision | None:
        actions = tuple(dict.fromkeys(candidates))
        differences = self.candidate_differences(actions, outcomes=outcomes)
        if not differences:
            return None
        best = differences[0]
        return ClarificationDecision(
            dimension=best.dimension,
            question=_question_for(best.dimension, best.options),
            information_gain=best.information_gain,
            options=best.options,
            candidate_actions=actions,
        )


def plan_clarification(
    candidates: Sequence[RecommendedAction],
    *,
    outcomes: Sequence[RequestedOutcome] = (),
    capabilities: Mapping[
        RecommendedAction, OutputCapabilityDefinition
    ] = OUTPUT_CAPABILITIES,
) -> ClarificationDecision | None:
    """Pure function API for routing, CLI, or a future transport endpoint."""
    return ClarificationPlanner(capabilities).plan(candidates, outcomes=outcomes)


__all__ = [
    "CandidateDifference",
    "ClarificationDecision",
    "ClarificationOption",
    "ClarificationPlanner",
    "plan_clarification",
]
