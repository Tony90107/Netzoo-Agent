"""Scientific meaning of registry method tags, shared by advice and rendering.

These explain capabilities; they never select a method from request keywords.
Sources: https://netzoo.github.io/zooanimals/ss/ and
https://netzoo.github.io/netZooR/articles/CONDOR.html
https://netzoo.github.io/zooanimals/cobra/
https://netzoo.github.io/zooanimals/dragon/
https://netzoo.github.io/zooanimals/sambar/
https://netzoo.github.io/zooanimals/panda/panda/
https://netzoo.github.io/zooanimals/panda/puma/ and netZooPy puma/calculations.py
https://netzoo.github.io/netZooR/articles/TutorialOTTER.html
"""

_PHILOSOPHIES = {
    "covariate_association": (
        "COBRA models co-expression as a function of sample covariates through "
        "conditional covariance estimation. Correcting gene means alone may leave "
        "covariance confounding. Covariate-associated components are not TF-to-gene "
        "regulatory edges or proof that a covariate causes the expression pattern."
    ),
    "partial_correlation": (
        "DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. "
        "Partial correlations describe associations conditional on the other measured "
        "features under that model; they are not directed causal effects. The two "
        "omics layers must refer to matched samples."
    ),
    "biologically_informed_matrix_factorization": (
        "GIRAFFE jointly factors expression into a regulatory-effect matrix and "
        "sample-varying TF activities using biological priors. Signed effects describe "
        "the fitted activation/repression relationship, while activity differs from "
        "the TF's own expression. These fitted coefficients do not alone establish causality."
    ),
    "somatic_mutation": (
        "SAMBAR reduces sparse mutation data to pathway-level scores with gene-length "
        "and, when configured, patient mutation-burden normalization. Patient distances "
        "and subtype labels depend on the downstream clustering settings; they are "
        "distinct from gene communities in a regulatory network."
        " This is pathway aggregation followed by distance-based clustering, not "
        "non-negative matrix factorization; a mutation score does not establish "
        "permanent functional loss or equivalence of every mutation in a pathway."
    ),
    "leave_one_out_network_inference": (
        "LIONESS represents the cohort network through sample contributions: "
        "W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the "
        "same base estimator is fitted with and without sample q. The leave-one-out "
        "network alone is not the patient's network. This borrows cohort information; "
        "it does not estimate a correlation from one isolated observation or prove causality."
        " With PANDA, edge weights are inferred regulatory support, not measured "
        "binding strength. Cross-sectional networks do not establish temporal rewiring."
    ),
    "bipartite_community_detection": (
        "CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain "
        "separate partitions, and between-partition connectivity is compared with a "
        "degree/strength-preserving bipartite null model. A giant community can reflect "
        "an unsuitable null model, resolution or weight handling. Hubs alone do not "
        "prove every conventional algorithm fails, and bipartite modularity does not "
        "guarantee biologically meaningful modules. Verify the edge-weight conventions."
    ),
    "bayesian": (
        "BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene "
        "co-expression. It does not model uncertain TF-binding/motif priors or return "
        "TF-to-gene regulatory edges. A shared probabilistic philosophy does not make "
        "these scientific outputs interchangeable."
    ),
    # netZooPy puma/calculations.py: miRNA rows/columns of the cooperativity
    # matrix are reset to their initial values after every update
    # (ppi_matrix[s1] = TFCoopInit[s1]); co-expression is Pearson correlation
    # of target genes compared by continuous Tanimoto similarity (Log 261).
    "mirna_regulation": (
        "PUMA extends PANDA's message passing to miRNA regulators. Their prior "
        "edges usually come from sequence-based target prediction such as "
        "TargetScan or miRanda, and can sit in the same prior as TF motif edges. "
        "Because miRNAs do not form the protein complexes that the cooperativity "
        "network represents, PUMA keeps each miRNA's cooperativity with other "
        "regulators at its initial value instead of updating it. Evidence for a "
        "miRNA-gene edge therefore comes from agreement between the predicted "
        "targets and target-gene co-expression; the miRNA's own expression is not "
        "used, and anti-correlation receives no special weight for repression."
    ),
    "message_passing": (
        "Message passing iteratively reconciles a regulator-target prior with other "
        "biological evidence networks. Other evidence can revise the initial edge "
        "support, but the resulting weights are integrated network scores, not "
        "calibrated posterior probabilities of prior reliability."
    ),
    "relaxed_graph_matching": (
        "OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF "
        "interaction network and W-transpose W matches gene co-expression. Its lambda "
        "balances those two fit terms and gamma regularizes W; a PPI-transformed "
        "motif matrix initializes W rather than contributing a motif-fidelity "
        "term to that loss. "
        "Neither parameter estimates motif-prior reliability, and "
        "optimized edge scores are not posterior probabilities."
    ),
}


# What each required principle means, independent of any workflow (Log 261).
# A capability-gap reply opens with these instead of a glossary fragment.
_PRINCIPLES = {
    "partial_correlation": (
        "Partial correlation asks whether two features stay associated after "
        "conditioning on every other measured feature. Under a Gaussian graphical "
        "model this separates direct links from associations mediated by other "
        "variables; with more features than samples it needs shrinkage or another "
        "regularized estimate, and it still does not give causal direction."
    ),
    "relaxed_graph_matching": (
        "Relaxed graph matching fits a network whose projections reproduce observed "
        "interaction structures, written as an explicit loss that is minimized "
        "numerically. Regularization controls how far the solution may move, and "
        "convergence can be checked against that objective."
    ),
    "message_passing": (
        "Message passing repeatedly exchanges information between evidence networks, "
        "for example a regulator-target prior, regulator cooperativity and target "
        "co-expression, until they agree. The result is a consensus score for each "
        "edge, not a probability."
    ),
    "biologically_informed_matrix_factorization": (
        "Biologically informed matrix factorization explains a data matrix as a "
        "product of factors whose structure is constrained by prior knowledge, such "
        "as which regulators may target which genes, so each factor keeps a "
        "biological meaning."
    ),
    "leave_one_out_network_inference": (
        "Leave-one-out network inference estimates each sample's contribution by "
        "comparing a network fitted to the whole cohort with one fitted without that "
        "sample. It needs a cohort and inherits the assumptions of the base estimator."
    ),
    "covariate_association": (
        "Covariate modeling lets the co-expression structure itself depend on sample "
        "covariates, so structure explained by a variable such as age, stage or batch "
        "can be separated from the rest."
    ),
    "high_order_correlation": (
        "Modeling higher-order structure means estimating how the correlation pattern "
        "itself varies with sample-level variables, rather than one fixed correlation "
        "per feature pair."
    ),
    "linear_model_coefficients": (
        "Linear-model coefficients quantify each predictor's contribution to a response "
        "while holding the other predictors fixed; their signs give the direction of "
        "the fitted effect, not proof of causation."
    ),
    "sparse_pvalue_coexpression": (
        "Test-based sparse co-expression keeps an edge only when its statistic passes a "
        "significance threshold, so each retained edge carries an explicit error level "
        "instead of a dense weight."
    ),
    "bipartite_community_detection": (
        "Bipartite community detection groups two node types, such as regulators and "
        "targets, with a modularity whose null model keeps the two partitions and each "
        "node's degree."
    ),
}


def method_philosophies_for(selection_tags) -> tuple[str, ...]:
    return tuple(text for tag, text in _PHILOSOPHIES.items() if tag in selection_tags)


def question_fit_for(outcome, workflow: str, capability, *, stated_conditions=(), qualified=True) -> str:
    """Connect a qualified method to the user's typed result and stated study facts.

    This is explanatory only: routing already qualified the method. It cannot
    promote an unrelated artifact, an unobserved condition, or a method tag.
    """
    if outcome is None or outcome.artifact_type == "unknown":
        return ""
    artifact = outcome.artifact_type.replace("_", " ").replace("tf ", "TF ")
    scale = {"aggregate": "cohort-level ", "sample_specific": "per-sample "}.get(
        outcome.granularity, ""
    )
    result = scale + artifact
    conditions = "; ".join(stated_conditions)
    if conditions:
        lead = (
            f"Your question asks for {result} and states {conditions}. "
            f"That makes **{workflow}** a conditional fit under the registered "
            "study conditions."
        )
    else:
        relation = "fits" if qualified else "is related to"
        lead = f"Your question asks for {result}. **{workflow}** {relation} that result and scale."
    tags = capability["selection_tags"] if isinstance(capability, dict) else capability.selection_tags
    notes = method_philosophies_for(tags)
    if not notes:
        return lead
    mechanism = notes[0].split(". ", 1)[0].rstrip(".") + "."
    return lead + " " + mechanism


def requested_framework_for(selection_tags, *, artifact_type: str = "unknown") -> str:
    """Explain a requested principle without claiming a registered implementation."""
    if "bayesian" in selection_tags:
        if artifact_type == "regulatory_network":
            return (
                "Yes, in principle, data can weaken an unreliable TF-binding prior "
                "and quantify uncertainty about it, but only if the model explicitly "
                "represents that uncertainty. A hierarchical Bayesian model can treat "
                "binding-site predictions as noisy evidence about latent TF-gene edges, "
                "with a source-reliability parameter and an expression-data likelihood. "
                "Conflicting evidence can lower posterior edge support; learning the "
                "source's reliability itself also requires an identifiable model and "
                "informative data, potentially including independent binding evidence "
                "or multiple priors. A Bayesian label alone does not supply this model."
            )
        return (
            "Bayesian inference represents uncertain quantities probabilistically and "
            "updates them using a data likelihood. To estimate a prior's reliability, "
            "a hierarchical model can include a reliability or prior-strength parameter; "
            "learning it requires an identifiable model and enough relevant data. "
            "A Bayesian label alone does not supply that capability."
        )
    if explained := [_PRINCIPLES[tag] for tag in selection_tags if tag in _PRINCIPLES]:
        return " ".join(explained)
    from workflow_registry import SELECTION_TAG_GLOSSARY
    principles = [SELECTION_TAG_GLOSSARY[tag] for tag in selection_tags if tag in SELECTION_TAG_GLOSSARY]
    return "Requested modeling principle: " + "; ".join(principles) + "."
