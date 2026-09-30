"""Short lines for options: what a workflow gives you, and when to pick it.

Presentation only, like ``DOWNSTREAM_ANALYSES``: never part of a prompt or the
policy snapshot, and never used to select anything. Each highlight restates
what the registry already declares for the workflow -- its distinguishing
selection tag and outputs -- and the method notes in
``interpretation/method_philosophy.py``, which cite the netZooPy sources. The
condition phrases are short forms of ``SELECTION_AXES`` values; the long
forms stay what the condition recommender offers the model.
``tests/test_reply_cards.py`` keeps one line per run action and per condition.
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, REQUIRED_INPUT_GROUPS, REQUIRED_INPUTS

from ..routing.capability_compatibility import _supported_artifacts

__all__ = [
    "INPUT_ARTIFACTS",
    "SHORT_INPUT_LABELS",
    "condition_phrase",
    "fit_notes",
    "highlight",
    "input_fields",
    "missing_input_labels",
    "needs_line",
]

_HIGHLIGHTS: dict[str, str] = {
    "run_panda": "Widely used baseline: message passing over motif, PPI and co-expression evidence",
    "run_puma": "PANDA's message passing with miRNA regulators added",
    "run_otter": "Explicit objective (graph matching) with a convergence check; lighter on memory",
    "run_giraffe": "Also estimates per-sample TF activity and signed activating/repressing effects",
    "run_lioness_panda": "One TF-gene network per sample, derived leave-one-out from the cohort",
    "run_lioness_puma": "One TF + miRNA network per sample, derived leave-one-out from the cohort",
    "run_lioness_coexpression": "One gene co-expression network per sample; needs only expression data",
    "run_bonobo": "Per-sample co-expression with Bayesian shrinkage and a p-value per edge",
    "run_cobra": "Separates how covariates (batch, site, condition) reshape co-expression",
    "run_dragon": "Partial-correlation network across two omics layers of the same samples",
    "run_condor": "Finds TF-gene communities (modules) in a two-mode network",
    "run_sambar": "Pathway-level mutation scores, then patient subtypes by clustering",
}

_CONDITIONS: dict[str, str] = {
    "regulator_class:mirna": "the regulators include miRNAs",
    "cohort_size:few": "you have only a handful of samples",
    "cohort_size:many": "you have dozens of samples or more",
    "per_edge_confidence:needed": "you need a p-value for each edge",
    "compute_constraints:constrained": "memory or runtime is a concern",
    "tf_activity_vs_expression:yes": "TF activity may differ from its mRNA level",
    "established_method:yes": "you want the standard published method or a base for LIONESS",
    "per_sample_quantity:wiring": "you need each sample's TF-target wiring",
    "per_sample_quantity:activity": "you need each sample's TF activity",
    "covariates:yes": "batch, site or covariates must be separated",
    "covariates:no": "no covariates need adjusting",
}

SHORT_INPUT_LABELS: dict[str, str] = {
    "expression_file": "expression matrix",
    "coexpression_file": "adjusted co-expression matrix",
    "motif_file": "motif prior",
    "ppi_file": "PPI network",
    "mirna_file": "miRNA list",
    "design_file": "covariate design matrix",
    "network_file": "TF-gene (bipartite) network",
    "omics_layer_1": "omics layer 1",
    "omics_layer_2": "omics layer 2",
    "mutation_file": "somatic mutation matrix",
    "exon_size_file": "gene-length CSV",
    "cancer_gene_file": "cancer-gene list",
    "pathway_file": "GMT pathway file",
}

# The ontology value a request's wording can establish for an input role.
INPUT_ARTIFACTS: dict[str, str] = {
    "expression_file": "expression_matrix",
    "coexpression_file": "coexpression_network",
    "motif_file": "motif_prior",
    "ppi_file": "ppi_prior",
    "mirna_file": "mirna_prior",
    "network_file": "regulatory_network",
    "mutation_file": "mutation_matrix",
}

_REGULATORS = {"tf": "TF", "mirna": "miRNA"}
_NOUNS = {
    "regulatory_network": "a regulatory network",
    "signed_regulatory_effect_network": "a signed regulatory-effect network",
    "coexpression_network": "a co-expression network",
    "community_assignment": "network communities",
    "multi_omic_network": "a multi-omic network",
    "pathway_mutation_matrix": "pathway mutation scores",
}


def highlight(action: str) -> str:
    return _HIGHLIGHTS.get(action, "")


def condition_phrase(condition: str) -> str:
    return _CONDITIONS.get(condition, "")


def _regulators(values) -> str:
    return " + ".join(_REGULATORS.get(value, value) for value in sorted(values, key=lambda v: v != "tf"))


def fit_notes(action: str, outcome) -> tuple[list[str], list[str]]:
    """(matches, mismatches) of one workflow against the typed request.

    Read from typed dimensions only -- regulators, scale, result -- never from
    the request's wording, so a note can explain an option's order but can
    never be a keyword match.
    """
    capability = OUTPUT_CAPABILITIES.get(action)
    if capability is None or outcome is None or outcome.artifact_type == "unknown":
        return [], []
    matches, mismatches = [], []
    requested = set(outcome.regulator_types) - {"unknown"}
    offered = set(capability.regulator_types)
    if requested and offered:
        if requested == offered and len(requested) > 1:
            matches.append(f"models the {_regulators(requested)} regulators you asked for")
        elif requested - offered:
            mismatches.append(f"models {_regulators(offered)} only, not {_regulators(requested - offered)}")
        elif offered - requested:
            mismatches.append(f"also adds {_regulators(offered - requested)} regulators")
    scales = set(capability.granularities)
    if outcome.granularity == "sample_specific" and "sample_specific" not in scales:
        mismatches.append("gives one cohort-level result, not one per sample")
    elif outcome.granularity == "aggregate" and "aggregate" not in scales:
        mismatches.append("gives one result per sample, not one cohort network")
    supported = _supported_artifacts(capability)
    if outcome.artifact_type == "regulatory_network_and_tf_activity" and "regulatory_network" in supported \
            and "tf_activity_matrix" not in supported:
        mismatches.append("gives the network but no TF activity")
    elif outcome.artifact_type not in supported:
        mismatches.append(f"produces {_NOUNS.get(capability.artifact_type, capability.artifact_type.replace('_', ' '))} instead")
    return matches, mismatches


def input_fields(action: str) -> tuple[list[str], list[tuple[str, ...]]]:
    """(always required input roles, one-of groups), outputs excluded."""
    required = [field for field in REQUIRED_INPUTS.get(action, ()) if field in SHORT_INPUT_LABELS]
    groups = [
        tuple(field for field in group if field in SHORT_INPUT_LABELS)
        for group in REQUIRED_INPUT_GROUPS.get(action, ())
    ]
    return required, [group for group in groups if group]


def needs_line(action: str) -> str:
    required, groups = input_fields(action)
    labels = [SHORT_INPUT_LABELS[field] for field in required]
    labels.extend(" or ".join(SHORT_INPUT_LABELS[field] for field in group) for group in groups)
    return ", ".join(labels)


def missing_input_labels(action: str, present: frozenset[str] | set[str]) -> list[str]:
    """Required inputs the request never mentions, when it mentions any at all.

    Only roles whose presence wording can establish are judged; a request that
    names no input says nothing about which ones it lacks.
    """
    if not present:
        return []
    required, groups = input_fields(action)
    missing = [
        SHORT_INPUT_LABELS[field] for field in required
        if field in INPUT_ARTIFACTS and INPUT_ARTIFACTS[field] not in present
    ]
    for group in groups:
        judged = [field for field in group if field in INPUT_ARTIFACTS]
        if judged and not any(INPUT_ARTIFACTS[field] in present for field in judged):
            missing.append(" or ".join(SHORT_INPUT_LABELS[field] for field in group))
    return missing
