"""Short English phrases for typed outcomes, shared by every card builder."""

from __future__ import annotations

__all__ = [
    "primary_outcome",
    "artifact_noun",
    "clip",
    "input_phrase",
    "join_names",
    "quote",
    "result_phrase",
    "workflow_name",
]

_NOUNS = {
    "regulatory_network": "regulatory network",
    "signed_regulatory_effect_network": "signed regulatory-effect network",
    "regulatory_network_and_tf_activity": "regulatory network with TF activities",
    "tf_activity_matrix": "TF activity matrix",
    "coexpression_network": "co-expression network",
    "pvalue_matrix": "p-value matrix",
    "community_assignment": "set of network communities (modules)",
    "sample_cluster_assignment": "set of sample subtypes",
    "sample_distance_matrix": "sample distance matrix",
    "pathway_mutation_matrix": "pathway mutation score matrix",
    "gene_mutation_scores": "gene mutation score matrix",
    "multi_omic_network": "multi-omic network",
    "mutation_matrix": "mutation matrix",
    "expression_matrix": "expression matrix",
    "measurement_dataset": "measurement dataset",
    "validation_report": "input validation report",
}
_SCALES = {"aggregate": "cohort-level", "sample_specific": "per-sample"}
_INPUTS = {
    "expression_matrix": "expression data",
    "coexpression_network": "a co-expression matrix",
    "regulatory_network": "an existing network",
    "mutation_matrix": "mutation data",
    "measurement_dataset": "measurement data",
    "motif_prior": "a motif prior",
    "ppi_prior": "a PPI network",
    "mirna_prior": "a miRNA prior",
}
_REGULATORS = {
    ("tf",): "TF-gene",
    ("mirna",): "miRNA-gene",
    ("mirna", "tf"): "TF/miRNA-gene",
}


def primary_outcome(decision):
    """The request's typed outcome: the routed primary, else its only reading."""
    if decision.requested_outcome is not None:
        return decision.requested_outcome
    readings = decision.outcome_hypotheses
    return readings[0].outcome if len(readings) == 1 else None


def artifact_noun(artifact: str) -> str:
    return _NOUNS.get(artifact, artifact.replace("_", " "))


def clip(text: str, limit: int) -> str:
    """Shorten at a word boundary, never mid-word, with an ellipsis."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…"


def quote(text: str, limit: int = 60) -> str:
    return "“" + clip(text, limit) + "”"


def workflow_name(policy, action: str) -> str:
    spec = policy.workflows.get(action)
    return spec.workflow if spec is not None else action.removeprefix("run_").upper()


def join_names(names: list[str], word: str = "or") -> str:
    names = list(dict.fromkeys(names))
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + f" {word} " + names[-1]


def result_phrase(outcome, *, article: bool = True) -> str:
    """`a cohort-level TF-gene regulatory network`, from the typed outcome only."""
    if outcome is None or outcome.artifact_type == "unknown":
        return "the requested result"
    parts = []
    if scale := _SCALES.get(outcome.granularity):
        parts.append(scale)
    if outcome.artifact_type in {"regulatory_network", "signed_regulatory_effect_network",
                                 "regulatory_network_and_tf_activity"}:
        if regulators := _REGULATORS.get(tuple(sorted(set(outcome.regulator_types) - {"unknown"}))):
            parts.append(regulators)
    parts.append(_NOUNS.get(outcome.artifact_type, outcome.artifact_type.replace("_", " ")))
    phrase = " ".join(parts)
    if not article:
        return phrase
    return ("an " if phrase[:1] in "aeiou" else "a ") + phrase


def input_phrase(artifacts) -> str:
    labels = [_INPUTS[item] for item in dict.fromkeys(artifacts) if item in _INPUTS]
    return join_names(labels, "and")
