"""The question a one-candidate tie owes the user when routing asked none (Log 194).

Case 9 ("groups of regulators that jointly control groups of genes") was read
as inferring community assignments. CONDOR, the only compatible workflow, is
registered as *analyzing* an existing network, so the guidance match stayed
`ambiguous` with CONDOR as its sole candidate and no clarification question,
and the reply fell through to the response model -- the one path this harness
cannot check. The deterministic reply already exists for a one-candidate tie
with a question; this supplies the question from the registry: which workflow
is compatible, and what the request left unsettled or read differently.
Nothing here selects, recommends or authorizes anything.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES

__all__ = ["single_candidate_question"]

_REQUESTED = {
    "infer": "infer a new result",
    "analyze": "analyze an existing result",
    "prepare": "prepare data",
    "validate": "validate inputs",
    "acquire": "retrieve data",
    "explain": "explain a method",
}
_UNSETTLED = {
    "artifact_type": "the kind of result",
    "granularity": "whether one cohort-wide result or one result per sample is wanted",
    "entity_types": "which entities the result should cover",
    "regulator_types": "which regulator types to model",
    "target_types": "which targets to model",
    "input_artifacts": "which input the analysis starts from",
    "operation": "whether a new result is inferred or an existing one analyzed",
}


def _label(artifact: str) -> str:
    return artifact.replace("_", " ")


def _does(capability) -> str:
    inputs = " or ".join(sorted(_label(item) for item in capability.input_artifacts))
    if capability.operation == "analyze" and inputs:
        return f"analyzes an existing {inputs}"
    if capability.operation == "infer":
        return f"infers a {_label(capability.artifact_type)} from its inputs"
    return f"is registered to {capability.operation} {_label(capability.artifact_type)}"


def _unsettled(outcome) -> list[str]:
    dimensions = list(outcome.unresolved_dimensions)
    if outcome.artifact_type == "unknown":
        dimensions.append("artifact_type")
    if outcome.granularity == "unknown":
        dimensions.append("granularity")
    return [_UNSETTLED[item] for item in dict.fromkeys(dimensions) if item in _UNSETTLED]


def single_candidate_question(decision) -> str | None:
    """Ask whether the sole compatible workflow is wanted, saying what is open."""
    actions = list(getattr(decision, "hypothesis_actions", None) or ())
    if (
        decision.capability_match_status != "ambiguous"
        or decision.clarification_question
        or len(actions) != 1
        or actions[0] not in OUTPUT_CAPABILITIES
    ):
        return None
    capability = OUTPUT_CAPABILITIES[actions[0]]
    name = ACTION_DEFINITIONS[actions[0]].workflow
    outcomes = [item.outcome for item in decision.outcome_hypotheses]
    reasons = []
    read_as = sorted({item.operation for item in outcomes} - {"unknown", "explain", capability.operation})
    if read_as:
        asks = " or ".join(_REQUESTED.get(item, item) for item in read_as)
        reasons.append(f"it {_does(capability)}, while your request reads as asking to {asks}")
    unsettled = list(dict.fromkeys(text for outcome in outcomes for text in _unsettled(outcome)))
    if unsettled:
        reasons.append("your request does not settle " + " or ".join(unsettled))
    lead = f"The only registered workflow compatible with this request is **{name}**"
    if reasons:
        lead += ", but " + "; and ".join(reasons)
    return (
        f"{lead}. Is {name} the analysis you want? If so, say so and name its inputs; "
        "otherwise describe the result you need."
    )
