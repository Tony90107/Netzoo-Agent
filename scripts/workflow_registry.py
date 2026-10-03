"""Code-enforced workflow/action registry for the NetZoo harness.

The YAML workflow files remain independently validated policy data. This module
is the single Python source for action names, inputs, controls, validation steps,
executor arguments, output capabilities, and memory metadata.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Mapping, NamedTuple, get_args


ActionName = Literal[
    "no_tool",
    "inspect_inputs",
    "inspect_condor_inputs",
    "inspect_cobra_inputs",
    "inspect_sambar_inputs",
    "inspect_dragon_inputs",
    "inspect_otter_inputs",
    "inspect_giraffe_inputs",
    "inspect_bonobo_inputs",
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
    "run_cobra",
    "run_sambar",
    "run_dragon",
    "run_lioness_dragon",
    "run_otter",
    "run_giraffe",
    "run_bonobo",
    "query_context7",
    "web_search",
    "download_string",
]

RecommendedAction = Literal[
    "inspect_inputs",
    "inspect_condor_inputs",
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
    "run_cobra",
    "run_sambar",
    "run_dragon",
    "run_lioness_dragon",
    "run_otter",
    "run_giraffe",
    "run_bonobo",
]

IntentType = Literal[
    "answer_question",
    "inspect_input",
    "prepare_input",
    "run_analysis",
    "demo_run",
    "unknown",
]

PreferenceKey = Literal[
    "default_output_dir",
    "allow_demo_autofill",
    "reuse_last_inputs",
    "preferred_workflow",
]

Operation = Literal[
    "acquire",
    "prepare",
    "validate",
    "infer",
    "analyze",
    "explain",
    "unknown",
]
ArtifactType = Literal[
    "measurement_dataset",
    "expression_matrix",
    "tf_activity_matrix",
    "regulatory_network_and_tf_activity",
    "signed_regulatory_effect_network",
    "regulatory_network",
    "coexpression_network",
    "pvalue_matrix",
    "mutation_matrix",
    "pathway_mutation_matrix",
    "gene_mutation_scores",
    "sample_distance_matrix",
    "sample_cluster_assignment",
    "community_assignment",
    "validation_report",
    "multi_omic_network",
    "unknown",
]
InputModality = Literal[
    "gene_expression",
    "somatic_mutation",
    "coexpression",
    "regulatory_network",
    "multi_omic_continuous",
    "unknown",
]
EntityType = Literal[
    "tf", "mirna", "gene", "protein", "metabolite", "sample", "pathway",
    "omics_layer_1_feature", "omics_layer_2_feature", "unknown",
]
Granularity = Literal["aggregate", "sample_specific", "not_applicable", "unknown"]
ControlType = Literal[
    "boolean", "integer", "number", "string", "string_list", "enum"
]


# Workflow-independent meanings for the registry signals exposed to the semantic
# interpreter.  Bare identifiers such as ``tfa`` and ``bayesian`` made the model
# guess what counted as support and, in live routing, it usually returned an empty
# list.  Keep the scientific vocabulary here beside the capability registry so
# every consumer sees the same meanings without exposing action names.
SELECTION_TAG_GLOSSARY: Mapping[str, str] = {
    "aggregate_network": "one cohort-wide or population-level network",
    "batch_correction": "remove or adjust technical batch effects",
    "bayesian": "Bayesian shrinkage estimation of sample-specific co-expression",
    "sparse_pvalue_coexpression": (
        "sparsify sample-specific co-expression and return matching p-value matrices"
    ),
    "biologically_informed_matrix_factorization": (
        "factor gene expression using motif and TF-protein interaction priors"
    ),
    "bipartite_community_detection": "find communities in a two-mode network",
    "cancer_subtyping": "derive patient or tumor subtypes",
    "coexpression": "infer gene-gene co-expression relationships",
    "covariate_association": "estimate how sample covariates change co-expression",
    "high_order_correlation": "model higher-order covariance or correlation structure",
    "hospital_effect_assessment": "assess or remove hospital or site effects",
    "joint_grn_tfa_inference": (
        "jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix"
    ),
    "linear_model_coefficients": (
        "interpret TF-gene regulatory weights as coefficients in a linear expression model"
    ),
    "leave_one_out_network_inference": (
        "derive each sample network from all-sample and leave-one-out networks"
    ),
    "message_passing": (
        "iteratively exchange information across biological evidence networks; "
        "the participating layers depend on the registered workflow"
    ),
    "lioness_base_compatibility": (
        "aggregate LIONESS-compatible base network"
    ),
    "mirna_regulation": "model miRNA-to-gene regulation",
    "modules": "return network modules or community membership",
    "multi_omic_network": "infer one network spanning two omics layers",
    "partial_correlation": "infer conditional associations using partial correlation",
    "pathway_scores": "produce pathway-level mutation scores",
    "relaxed_graph_matching": (
        "continuous relaxed graph-matching; explicit objective/loss, gradient descent, "
        "convergence; not heuristic message passing"
    ),
    "sample_specific": "infer a separate network for each sample",
    "signed_partial_regulatory_effects": (
        "estimate positive activating and negative inhibitory partial regulatory effects"
    ),
    "sequencing_batch_effect_assessment": "assess or remove sequencing-batch effects",
    "somatic_mutation": "analyze somatic mutation measurements",
    "tf_gene_regulation": "model transcription-factor-to-gene regulation",
    "tfa": "estimate transcription factor activity (TFA) for each sample",
    "tfa_covariate_regression": (
        "model gene expression with transcription factor activities as predictors"
    ),
}

# Log 302: words a quote must contain before the discriminator may let a tag
# break a tie. A verbatim quote proves the words occurred, not that they state
# the method: "regulatory communication between TFs and target genes" was
# taken as matrix factorization and picked GIRAFFE over PANDA and OTTER. Only
# the tags that separate PANDA, OTTER and GIRAFFE are listed; read per key and
# never shown to the model.
_TF_ACTIVITY_WITNESS = r"\bactiv(?:e|ity|ities)\b|活性|活躍|活跃"
SELECTION_TAG_WITNESSES: Mapping[str, str] = {
    "message_passing": (
        r"message[- ]?passing|pass(?:es|ing)?\s+messages|iterat|"
        r"訊息傳遞|消息傳遞|消息传递|信息傳遞|信息传递|迭代"
    ),
    "relaxed_graph_matching": (
        r"graph[- ]?matching|objective|loss|optimi[sz]|gradient|converge|convex|heuristic|"
        r"圖匹配|图匹配|目標|目标|損失|损失|最佳化|最優化|优化|梯度|收斂|收敛|凸|啟發式|启发式"
    ),
    "biologically_informed_matrix_factorization": (
        # Log 306: the verb form ("factor gene expression"), but not
        # "transcription factor expression".
        r"factori[sz]|(?<!transcription\s)\bfactor(?:s|ed|ing)?\s+(?:the\s+)?(?:gene\s+)?expression|"
        r"decompos|矩陣分解|矩阵分解|因子分解|分解"
    ),
    "linear_model_coefficients": (
        r"linear|regression|coefficient|線性|线性|迴歸|回归|係數|系数"
    ),
    "signed_partial_regulatory_effects": (
        r"\bsign(?:ed)?\b|activat|repress|inhibit|positive|negative|"
        r"正負|正负|活化|抑制|促進|促进"
    ),
    "tfa": _TF_ACTIVITY_WITNESS,
    "joint_grn_tfa_inference": _TF_ACTIVITY_WITNESS,
    "tfa_covariate_regression": _TF_ACTIVITY_WITNESS,
    "lioness_base_compatibility": (
        r"\bLIONESS\b|base(?:line)?\s+network|per[- ]sample|sample[- ]specific|"
        r"each\s+(?:sample|patient|individual)|基礎網路|基础网络|每個樣本|每个样本|個體|个体"
    ),
}

# Log 318: a bare model preference stands on a method signal only when one of
# its quotes contains that tag's words. The discriminator's table plus tags
# that separate the co-expression and per-sample workflows; read per key and
# never shown to the model. lioness_base_compatibility is left out: its words
# ("each patient") would let PANDA win a per-sample request over LIONESS-PANDA.
_REGULATOR_CLASS_WITNESS = (
    r"\bmi(?:cro)?[- ]?rnas?\b|\bmir[- ]?\d|non[- ]?coding|\bnc[- ]?rnas?\b|"
    r"\bsmall\s+(?:[\w-]+\s+)?rnas?\b|post[- ]?transcription|"
    r"微小核糖核酸|微型\s*RNA|小\s*RNA|非編碼|轉錄後"
)
_COVARIATE_WITNESS = (
    r"\bbatch\w*|covariat\w*|confound\w*|\bsites?\b|hospital\w*|\bcent(?:er|re)s?\b|sequencing\s+runs?|"
    r"批次|共變|混雜|醫院|中心"
)
PREFERENCE_TAG_WITNESSES: Mapping[str, str] = {
    **{tag: words for tag, words in SELECTION_TAG_WITNESSES.items() if tag != "lioness_base_compatibility"},
    "bayesian": r"\bbayes\w*|posterior|probabilist\w*|shrink\w*|uncertaint\w*|貝氏|貝葉斯|機率|不確定",
    "sparse_pvalue_coexpression": (
        r"p[- ]?values?|significan\w*|confiden\w*|trustworth\w*|reliab\w*|\bspars\w*|顯著|信心|可信|可靠"
    ),
    "leave_one_out_network_inference": r"leave[- ]one[- ]out|\bLIONESS\b|留一",
    "mirna_regulation": _REGULATOR_CLASS_WITNESS,
    "batch_correction": _COVARIATE_WITNESS,
    "covariate_association": _COVARIATE_WITNESS,
    "hospital_effect_assessment": _COVARIATE_WITNESS,
    "sequencing_batch_effect_assessment": _COVARIATE_WITNESS,
}
# What a stated method signal means to the user, for the recommendation's reason.
STATED_TAG_PHRASES: Mapping[str, str] = {
    "message_passing": "you asked for iterative message passing",
    "relaxed_graph_matching": "you asked for an explicit objective that is optimized",
    "biologically_informed_matrix_factorization": "you asked for a factorization of the expression data",
    "linear_model_coefficients": "you asked for linear-model coefficients",
    "signed_partial_regulatory_effects": "you asked for signed (activating or repressing) effects",
    "tfa": "you asked for TF activity",
    "joint_grn_tfa_inference": "you asked for TF activity",
    "tfa_covariate_regression": "you asked for TF activity",
    "bayesian": "you asked for probabilistic (Bayesian) uncertainty",
    "sparse_pvalue_coexpression": "you asked for a p-value or confidence for each connection",
    "leave_one_out_network_inference": "you asked for leave-one-out (LIONESS) sample networks",
    "mirna_regulation": "your regulators include miRNAs",
    "batch_correction": "you asked to separate batch or covariate effects",
    "covariate_association": "you asked to separate batch or covariate effects",
    "hospital_effect_assessment": "you asked to separate batch or covariate effects",
    "sequencing_batch_effect_assessment": "you asked to separate batch or covariate effects",
}

# Experimental-condition axes (Log 139). When compatible workflows produce the
# same result and differ only in method, these are the facts a user can state
# about their study that separate them. Each workflow declares the values it is
# preferred under as ``prefer_when: ["axis:value", ...]``. Labels are
# user-facing English and deliberately qualitative: there is no accepted
# numeric cut-off for "few" samples.
_COHORT_UNITS = (
    r"(?:samples?|patients?|individuals?|subjects?|donors?|participants?|people|mice|animals?|replicates?|"
    r"tumou?rs?|cases?|biops(?:y|ies))"
)
SELECTION_AXES: Mapping[str, Mapping[str, Any]] = {
    # Log 269 (user decision): a functional description of the regulators
    # (short non-coding RNAs degrading transcripts) may point to miRNA methods,
    # as a quoted condition the user confirms. Asked first: a biological fact
    # comes before algorithm choices. Offered only when the tie mixes TF-only
    # and TF/miRNA methods, so it never overrides a stated regulator scope.
    "regulator_class": {
        "question": (
            "Do the regulators include miRNAs, short non-coding RNAs that repress or degrade "
            "their target transcripts after transcription?"
        ),
        "values": {
            "mirna": (
                "the regulators include miRNAs or similar short non-coding RNAs that repress "
                "or degrade target transcripts after transcription"
            ),
        },
        "confirm": {
            "mirna": (
                "This reads the molecules you describe as miRNAs. Confirm that, and that you have "
                "a miRNA-target prior and a list of the miRNAs, before analysis."
            ),
        },
        # Log 300: the request must describe such molecules somewhere. A quote
        # of "Which workflow finds gene modules within each patient?" was taken
        # as stating that the regulators include miRNAs.
        "witness": _REGULATOR_CLASS_WITNESS,
    },
    "cohort_size": {
        "question": "About how many samples do you have?",
        "values": {
            "few": "only a handful of samples",
            "many": "dozens of samples or more",
        },
        # Log 315 (user decision 2026-09-27 #3, reconfirmed 2026-10-02): the
        # agent never maps a sample count to these values; only the user's own
        # words do, so a number is no witness. One witness per value: "a
        # handful" states few and never many.
        "witness": {
            "few": (
                r"\bhandful\b|\b(?:a\s+|very\s+|only\s+(?:a\s+)?)?few\s+(?:[\w-]+\s+){0,2}" + _COHORT_UNITS + r"\b|"
                r"\bsmall\s+(?:number\s+of\s+" + _COHORT_UNITS + r"|cohort|sample\s+size|study)\b|"
                r"\blimited\s+(?:number\s+of\s+)?" + _COHORT_UNITS + r"\b|\bonly\s+a\s+couple\b|"
                r"少數|少量(?:的)?(?:樣本|病人|患者)|幾個(?:病人|患者|樣本)|幾位|小樣本|樣本(?:數|量)?(?:很|太)?少"
            ),
            "many": (
                r"\b(?:dozens|hundreds|thousands)\b|\blarge\s+(?:number\s+of\s+" + _COHORT_UNITS
                + r"|cohort|sample\s+size|study)\b|"
                r"\bmany\s+(?:[\w-]+\s+){0,2}" + _COHORT_UNITS + r"\b|\blarge[- ]scale\s+cohort\b|"
                r"數十|數百|上百|上千|大量(?:的)?(?:樣本|病人|患者)|大型(?:世代|隊列|族群)|樣本(?:數|量)?(?:很)?多"
            ),
        },
    },
    "per_edge_confidence": {
        "question": "Do you need a confidence value for each connection in each sample?",
        "values": {
            "needed": "a confidence value (p-value) is needed for each connection in each sample",
        },
    },
    "compute_constraints": {
        "question": "Is the network large enough that memory or runtime is a concern?",
        "values": {
            "constrained": "the network is large and memory or runtime is a concern",
        },
        # Log 304: "genome-wide" or "genome-scale" alone states no compute limit.
        "witness": (
            r"\b(?:memory|RAM|runtime|run[- ]time|computational(?:ly)?|compute|CPU|GPU|HPC|"
            r"time[- ]limit|laptop|faster|slow|speed)\b|(?:computational|compute|computing|limited)\s+resources?|"
            r"記憶體|内存|運算資源|计算资源|運算量|计算量|執行時間|运行时间|速度|太慢"
        ),
    },
    "tf_activity_vs_expression": {
        "question": (
            "Do you suspect a regulator's activity differs across samples even when its "
            "own expression does not, or do you need activating versus repressing effects?"
        ),
        "values": {
            "yes": (
                "a regulator's activity may differ from its own expression, or activating "
                "versus repressing effects are needed"
            ),
        },
        # Log 304: "regulatory strengths" states neither activity nor a sign.
        "witness": (
            r"\bactiv(?:e|ity|ities|ated|ation|ating)\b|\brepress|\binhibit|\bsigned\b|"
            r"positive\s+(?:or|and|vs\.?|versus)\s+negative|活性|活躍|活跃|活化|抑制|正負|正负"
        ),
    },
    "established_method": {
        "question": (
            "Do you need results comparable with the widely published approach, or a base "
            "network for later per-sample analysis?"
        ),
        "values": {
            "yes": (
                "results must be comparable with the widely published approach, or serve as "
                "a base network for later per-sample analysis"
            ),
        },
        # Log 304: the goal sentence of the 2026-10-02 lung request was quoted as
        # stating this. "Standard" alone is not a method: "standard transcription
        # factor motif binding sites".
        "witness": (
            r"\b(?:published|publications?|literature|established|benchmark(?:s|ed|ing)?|baseline|"
            r"comparab(?:le|ility)|widely[- ]used|well[- ]known|reproduc(?:e|ible|ibility)|"
            r"standard\s+(?:published\s+)?(?:method|approach|workflow|pipeline|tool)s?|"
            r"previous\s+(?:studies|work|papers)|LIONESS|base\s+network)\b|"
            r"文獻|已發表|發表過|基準|標準方法|标准方法|常用方法|廣泛使用|广泛使用|可比較|可比较|重現|重现"
        ),
    },
    # Log 200: divergent readings of one request, not a method tie. "Each
    # patient's regulatory wiring ... per-TF regulatory strength" reads both
    # as one TF-gene network per sample and as TF activity per sample; the
    # inputs are the same, and the quantity the user will analyze separates them.
    "per_sample_quantity": {
        "question": (
            "For each sample, do you need each regulator's wiring to its targets (edge "
            "weights, summarised for example as targeting scores), or each regulator's "
            "activity level?"
        ),
        "values": {
            "wiring": (
                "each sample's regulator-to-target wiring (edge weights or targeting "
                "scores) is needed"
            ),
            "activity": (
                "each sample's regulator activity level is needed, apart from the "
                "regulator's own expression"
            ),
        },
    },
    "covariates": {
        "question": (
            "Do you need to separate or adjust co-expression for batch, site or other "
            "sample covariates?"
        ),
        "values": {
            "yes": "co-expression must be separated or adjusted for batch, site or other covariates",
            "no": "no sample covariates need to be separated or adjusted",
        },
    },
}


# What a user typically does with a workflow's output next, and what that
# needs beyond the workflow's own inputs (Log 160, extended in Log 166). Each
# entry is (heading, notes). Rendered by deterministic guidance only; never
# part of a model prompt. General advice: the analysis design stays the user's.
_LIONESS_TARGETING_NOTES = (
    "Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights "
    "to its targets) or a gene's indegree, computed in each sample's network, gives a "
    "regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level "
    "variables -- survival, for example, with a Cox model.",
    "That association needs a clinical table (for survival: follow-up time and event "
    "status) keyed by the same sample IDs as the expression matrix; it is not a "
    "workflow input, so supply it separately.",
    "All LIONESS networks are derived from the same cohort, so they are not "
    "statistically independent; account for this in the association test, which is a "
    "later analysis step rather than part of this workflow.",
)
# Log 219: "each person's per-TF regulatory strength" has two per-sample readings
# (TEST_PROMPTS Case 4): a TF's out-degree in each LIONESS network (wiring) or
# GIRAFFE's TF activity. Each side names the other and the difference, so a
# reply never gives one path without it (`per_sample_quantity`, Log 200).
_ACTIVITY_READING_NOTE = (
    "Out-degree measures how strongly a TF is wired to its targets in each sample. If "
    "you mean TF activity instead -- how active a TF is apart from its own mRNA level "
    "-- GIRAFFE's TF-by-sample activity matrix is the other reading, from the "
    "expression, motif and PPI inputs."
)
_WIRING_READING_NOTE = (
    "TF activity is how active a TF is in each sample, apart from its own mRNA level. "
    "If you mean how strongly each TF is wired to its targets in each sample, the "
    "out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the "
    "same inputs."
)
_AGGREGATE_TARGETING_NOTES = (
    "Targeting scores: a regulator's outdegree or a gene's indegree summarizes the "
    "network per regulator or per gene; comparing them between networks built "
    "separately for each condition shows regulators whose targeting changes.",
    "Comparing conditions needs one run per condition on matched inputs (the same "
    "genes and the same motif and PPI priors); edge weights are comparable only within "
    "that shared setup.",
)
_SAMPLE_ANNOTATION_NOTE = (
    "Relating per-sample results to sample-level variables needs an annotation or "
    "clinical table keyed by the same sample IDs, supplied separately."
)
DOWNSTREAM_ANALYSES: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "run_lioness_panda": ("Downstream use of the sample-specific networks:", (
        _LIONESS_TARGETING_NOTES[0], _ACTIVITY_READING_NOTE, *_LIONESS_TARGETING_NOTES[1:],
    )),
    "run_lioness_puma": ("Downstream use of the sample-specific networks:", (
        _LIONESS_TARGETING_NOTES[0], _ACTIVITY_READING_NOTE, *_LIONESS_TARGETING_NOTES[1:],
    )),
    "run_panda": ("Downstream use of the aggregate network:", (
        *_AGGREGATE_TARGETING_NOTES,
        "For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.",
    )),
    "run_puma": ("Downstream use of the aggregate network:", (
        *_AGGREGATE_TARGETING_NOTES,
        "For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.",
    )),
    "run_otter": ("Downstream use of the aggregate network:", (
        *_AGGREGATE_TARGETING_NOTES,
        "OTTER weights are on a different scale from PANDA's; compare OTTER networks only "
        "with other OTTER networks built with the same parameters.",
    )),
    "run_giraffe": ("Downstream use of the regulatory and activity matrices:", (
        "The TF-by-sample activity matrix (TFA) can serve as predictors in association "
        "tests with sample-level variables -- survival, for example, with a Cox model.",
        _WIRING_READING_NOTE,
        _SAMPLE_ANNOTATION_NOTE,
        "Signs in the regulatory matrix are partial linear effects (positive for "
        "activation, negative for repression); read them as model coefficients, not as "
        "proof of direct binding.",
    )),
    "run_bonobo": ("Downstream use of the sample-specific co-expression networks:", (
        "Per-sample gene degree or edge weights can be compared across samples or groups; "
        "with p-value output, edges can be filtered per sample at a chosen confidence.",
        _SAMPLE_ANNOTATION_NOTE,
        "These are co-expression networks, not TF-gene regulation; turning them into "
        "regulatory networks needs a separate, validated conversion before PANDA.",
    )),
    "run_lioness_coexpression": ("Downstream use of the sample-specific co-expression networks:", (
        "Per-sample gene degree or edge weights can be compared across samples or groups.",
        _SAMPLE_ANNOTATION_NOTE,
        "All LIONESS networks are derived from the same cohort, so they are not "
        "statistically independent; account for this in any test across samples.",
    )),
    "run_cobra": ("Downstream use of the covariate-specific co-expression:", (
        "Each covariate's component is a gene-by-gene co-expression attributable to that "
        "covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as "
        "coexpression_file after its identifiers and order are revalidated.",
        "Interpret each component relative to how the design matrix codes that covariate "
        "(for example, which level is the reference).",
    )),
    "run_dragon": ("Downstream use of the partial-correlation network:", (
        "The cross-layer block holds direct associations between features of the two "
        "omics layers; filter edges by the adjusted p-values before interpreting them.",
        "Partial correlations are conditional on every other feature in both layers, so "
        "adding or removing features changes them.",
    )),
    "run_lioness_dragon": ("Downstream use of the sample-specific partial-correlation networks:", (
        "Each sample column holds that sample's edge weights; comparing the columns between "
        "groups of samples shows which within- and cross-layer associations differ.",
        "A sample's edges are estimated from how removing it changes the cohort network, so "
        "they are relative to the cohort the network was built from, not absolute values.",
    )),
    "run_condor": ("Downstream use of the communities:", (
        "Core scores rank each node's contribution to its community's modularity; the "
        "top-scoring regulators and genes are candidates for the community's function.",
        "Gene communities can be tested for pathway enrichment with standard gene-set "
        "tools, which is a separate analysis step.",
    )),
    "run_sambar": ("Downstream use of the subtypes:", (
        "Subtype labels can be compared with clinical variables -- survival between "
        "subtypes, for example; that needs a clinical table keyed by the same sample IDs.",
        "The pathway mutation scores show which pathways separate the subtypes.",
    )),
}


class GuidanceComposition(NamedTuple):
    """Registered workflows plus one step outside NetZoo that reach a result together."""

    lead: str
    # (registered action, the per-sample matrix it gives for the outside step)
    sources: tuple[tuple[str, str], ...]
    outside_step: str
    notes: tuple[str, ...]


# Log 252: a result no registered workflow produces from an input, reached by a
# registered workflow's per-sample output and one step NetZoo does not run.
# Python-only, like DOWNSTREAM_ANALYSES: not part of the policy snapshot, so
# neither the policy hash nor any provider prompt changes, and nothing here is a
# capability -- routing never selects it and it is never executed. Keyed by
# (terminal artifact, input artifact).
GUIDANCE_COMPOSITIONS: Mapping[tuple[str, str], GuidanceComposition] = {
    ("sample_cluster_assignment", "expression_matrix"): GuidanceComposition(
        lead=(
            "No registered workflow assigns samples to clusters from expression. A "
            "registered workflow can give each sample a feature profile to cluster on:"
        ),
        sources=(
            ("run_lioness_panda",
             "a TF-by-sample out-degree matrix -- each TF's summed edge weights to its "
             "targets in each sample's network (how strongly the TF is wired)"),
            ("run_lioness_puma",
             "the same out-degree matrix with miRNAs among the regulators (needs a miRNA list)"),
            ("run_giraffe",
             "its TF-by-sample activity matrix -- how active each TF is apart from its own "
             "mRNA level, a different reading from wiring"),
            ("run_bonobo",
             "one gene co-expression network per sample; with about genes-squared edges "
             "each, summarize them first (for example per-gene degree)"),
            ("run_lioness_coexpression",
             "one gene co-expression network per sample, summarized the same way"),
        ),
        outside_step=(
            "Clustering the samples on that matrix (for example hierarchical clustering or "
            "k-means) is not a NetZoo workflow; run it separately."
        ),
        notes=(
            "Per-sample networks from LIONESS are derived from the same cohort, so they are "
            "not statistically independent; account for this in any test across samples.",
            "Clusters are unsupervised: whether they predict an outcome such as treatment "
            "response has to be tested against that outcome, keyed by the same sample IDs.",
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class RequestConcern:
    """A practical concern a user can state that a workflow's registry answers (Log 223).

    ``concern`` is the id offered to the model and ``label`` the statement it
    looks for, both in the user's terms; ``note`` is the registry-owned answer
    shown with the user's quote; ``controls`` and ``artifacts`` are what the
    note points to, and are listed in full in the reply.
    """

    concern: str
    label: str
    note: str
    controls: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExternalReference:
    """A published method this agent cannot run, named when no workflow fits (Log 267).

    Reference only: it never becomes a candidate, a recommendation or a prompt
    input. ``selection_tags`` is the principle it implements and
    ``artifact_types`` the result it produces, in this registry's vocabulary.
    Each entry must cite a source that was checked when it was added.
    """

    name: str
    selection_tags: frozenset[str]
    artifact_types: frozenset[ArtifactType]
    summary: str
    availability: str
    source: str


# Verified 2026-09-29 against the cited pages.
EXTERNAL_REFERENCES: tuple[ExternalReference, ...] = (
    ExternalReference(
        name="TIGER",
        selection_tags=frozenset({"bayesian"}),
        artifact_types=frozenset({"regulatory_network", "tf_activity_matrix"}),
        summary=(
            "Bayesian matrix factorization of expression with a prior TF-gene network and TF "
            "activities; sparse edge priors let the data shrink unsupported prior edges, one "
            "edge at a time."
        ),
        availability="netZooR, R",
        source="Chen & Padi 2024, doi:10.1038/s41540-024-00386-w",
    ),
    ExternalReference(
        name="Werhli & Husmeier (2007)",
        selection_tags=frozenset({"bayesian"}),
        artifact_types=frozenset({"regulatory_network"}),
        summary=(
            "Bayesian networks that give each prior-knowledge source its own weight, sampled by "
            "MCMC, so the data decide how much each prior counts."
        ),
        availability="published method, no NetZoo implementation",
        source="PMID 17542777",
    ),
    ExternalReference(
        name="LIONESS-OTTER",
        selection_tags=frozenset({"relaxed_graph_matching"}),
        artifact_types=frozenset({"regulatory_network"}),
        summary=(
            "OTTER's relaxed graph matching run once per sample with LIONESS, giving one TF-gene "
            "network per sample; for per-sample TF-gene networks this agent runs LIONESS-PANDA."
        ),
        availability="netZooPy, not registered in this agent",
        source="netZooPy lioness/lioness_for_otter.py and the otterlioness command, netZooPy PR #342",
    ),
)


# Python-only (Log 320): what a user should do or expect before running a
# workflow, said with its inputs. `{base}` is the per-sample extension's base
# method; `{runs}` is filled with the request's own sample count when it gives
# one. Sources: the LIONESS definition in method_philosophy (one base run with
# all samples and one without each), netZooR pandaToCondorObject (threshold
# default) and condorQscore (core scores), checked 2026-10-03.
_LIONESS_COST = (
    "Cost: LIONESS runs {base} once on all samples and once more without each sample, so N samples "
    "take N+1 {base} runs and give N network files{runs}. Plan the runtime and disk space, and filter "
    "edges before downstream statistics."
)
WORKFLOW_PRACTICAL_NOTES: Mapping[str, tuple[str, ...]] = {
    "run_condor": (
        "Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's "
        "pandaToCondorObject keeps only edges above a threshold (by default midway between the median "
        "weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or "
        "otherwise make the weights non-negative, before running it here. CONDOR puts each node in one "
        "community and gives each node a core score, its share of its community's modularity, which "
        "picks out each module's core regulators.",
    ),
    "run_lioness_panda": (_LIONESS_COST.replace("{base}", "PANDA"),),
    "run_lioness_puma": (_LIONESS_COST.replace("{base}", "PUMA"),),
    "run_lioness_dragon": (_LIONESS_COST.replace("{base}", "DRAGON"),),
}
# The same notes, short enough for a reply card's point.
WORKFLOW_PRACTICAL_POINTS: Mapping[str, str] = {
    "run_condor": (
        "Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; "
        "CONDOR then gives each node one community and a core score."
    ),
    **{action: f"Cost: N samples take N+1 {base} runs{{runs}}."
       for action, base in (("run_lioness_panda", "PANDA"), ("run_lioness_puma", "PUMA"),
                            ("run_lioness_dragon", "DRAGON"))},
}


@dataclass(frozen=True, slots=True)
class OutsideStep:
    """A step the request needs that no registered workflow performs (Log 320).

    Reference only, like ExternalReference: it never selects, ranks or
    recommends a workflow. It is said when the request's own words name the
    situation (every pattern in ``witnesses`` matches) and, if ``workflows``
    is set, the reply lists one of them. ``note`` is the paragraph the reply
    adds (the manual route and the published method); ``name`` and ``reason``
    are the card's "not available here" row. Sources were checked when added.
    ``concern_answer`` replaces a listed workflow's own note for a stated
    concern whose quote names this step (Log 331). ``advises_against`` are the
    workflows the note advises against; the reply never offers them as what
    the request's data allows (Log 334).
    """

    key: str
    name: str
    witnesses: tuple[str, ...]
    note: str
    reason: str
    source: str
    workflows: frozenset[str] = frozenset()
    concern_answer: str = ""
    advises_against: frozenset[str] = frozenset()


# Verified 2026-10-03 against the cited pages (TEST_PROMPTS Tests 4, 7, 8, 9).
OUTSIDE_STEPS: tuple[OutsideStep, ...] = (
    OutsideStep(
        key="single_cell",
        name="SCORPION (single-cell networks)",
        witnesses=(r"\bsingle[- ]cell|\bscRNA|\bsnRNA|\bsingle[- ]nucle(?:us|i)\b|單細胞|單核",),
        note=(
            "**Single-cell data.** The registered workflows are built for bulk samples. Co-expression "
            "between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are "
            "not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, "
            "then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; "
            "this needs several donors per state to estimate co-expression. To look within a state, "
            "SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar "
            "cells into metacells and then runs PANDA on them, giving comparable networks per sample or "
            "state."
        ),
        reason="Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.",
        source="Osorio, Capasso & Kuijjer 2024, Nat Comput Sci, doi:10.1038/s43588-024-00597-5; CRAN SCORPION",
        # "per-cell LIONESS or BONOBO networks are not advised" (the note above).
        advises_against=frozenset({"run_lioness_coexpression", "run_bonobo", "run_lioness_panda",
                                   "run_lioness_puma", "run_lioness_dragon"}),
    ),
    OutsideStep(
        key="chromatin_prior",
        name="SPIDER (chromatin-filtered prior)",
        witnesses=(r"\bATAC|\bDNase|chromatin|染色質", r"motif|prior|binding|基序|先驗|結合"),
        note=(
            "**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin "
            "is a step before network inference, and no registered workflow performs it. SPIDER "
            "(Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs "
            "PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the "
            "sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to "
            "genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the "
            "TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and "
            "the expression matrix from the same tissues. A promoter window misses distal enhancers unless "
            "enhancer-gene links are added."
        ),
        reason="Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.",
        source="Sonawane et al. 2021, npj Syst Biol Appl, doi:10.1038/s41540-021-00208-3; netzoo.github.io/zooanimals/panda/spider",
    ),
    OutsideStep(
        key="differential_modules",
        name="ALPACA (differential modularity)",
        witnesses=(
            r"\b(?:two|both|pair\s+of)\s+(?:[\w'-]+\s+){0,3}networks?\b|兩張|兩個網路",
            r"modul|communit|partition|模組|社群",
            r"differ|compar|reorgani[sz]|split|merg|rewir|alter|between|差異|比較|重組|拆|併",
        ),
        note=(
            "**Comparing module structure between two networks.** CONDOR partitions one network at a time. "
            "Running it on each network gives two unaligned sets of communities, so a split or a merge can "
            "only be judged by matching them afterwards, for example by gene overlap. ALPACA (Padi & "
            "Quackenbush 2018; netZooR `pandaToAlpaca`, not registered here) compares the two directly: it "
            "uses the control network as the null model for the disease network's modularity "
            "(differential modularity) and returns each node's module and its contribution score. It "
            "takes both networks as one edge table (TF, target gene, control weight, disease weight), so "
            "they must be given over the same TF-gene pairs."
        ),
        reason="Not registered here; ALPACA is in netZooR. CONDOR run on each network is only an approximation.",
        source="Padi & Quackenbush 2018, npj Syst Biol Appl, doi:10.1038/s41540-018-0052-5; netZooR pandaToAlpaca, alpaca (net.table)",
        workflows=frozenset({"run_condor"}),
        # Test 8 (r5): "how can we directly quantify this differential modular
        # structure" was answered with CONDOR's core scores.
        concern_answer=("CONDOR finds modules in one network at a time; it does not compare two. "
                        "ALPACA, described below, does."),
    ),
    OutsideStep(
        key="convex_guarantee",
        name="A convex, globally optimal method",
        witnesses=(r"\bconvex|global(?:ly)?[- ]optim|global\s+(?:minimum|optimum|solution)|凸|全域最",),
        note=(
            "**On a convex, globally optimal guarantee.** None of the registered methods offers one. OTTER "
            "is posed as a non-convex optimization (Weighill et al. 2021): the network W is fitted so that "
            "W times its transpose matches the PPI and its transpose times W matches co-expression. The "
            "paper derives a spectral solution with recovery guarantees under its assumptions, but the "
            "netZooPy OTTER registered here takes a fixed number of gradient steps from a motif-based start, "
            "which reaches a local solution. PANDA's iterative updates do not minimize a stated objective. "
            "OTTER does give the explicit objective you asked for."
        ),
        reason="No registered workflow guarantees a convex, global optimum; OTTER's objective is non-convex.",
        source="Weighill et al. 2021, AAAI, 'Gene regulatory network inference as relaxed graph matching'; netZooPy otter/otter.py",
        workflows=frozenset({"run_otter", "run_panda"}),
    ),
)


# Python-only, like DOWNSTREAM_ANALYSES: not part of the policy snapshot, so
# neither the policy hash nor any provider prompt changes. Every note must be
# verifiable in the netZooPy source or the executor that wraps it.
_MEMORY_LIMIT = "memory is a limiting factor (for example, an earlier run ran out of memory)"
# Log 263: how each prior-using method treats its prior. netZooPy
# panda/calculations.py:86-110 and puma/calculations.py:50-76 (the motif is the
# starting W, moved by alpha until the mean change is below 0.001), otter/otter.py
# (objective without a motif term), giraffe/giraffe.py:195-268 (R starts from the
# motif; no motif term in the loss).
_UNRELIABLE_PRIOR = "the prior network is noisy, borrowed from a related species, or not trusted"
_PRIOR_AS_START = (
    "The motif prior is only the starting network. Each iteration moves the network a "
    "fraction `alpha` (0.1) toward the agreement of the motif, PPI and co-expression "
    "evidence, which are updated too, and stops when the change falls below 0.001 on "
    "average. No term pulls the result back to the prior, but the starting point still "
    "shapes it, and this agent sets no weight for the prior. To see which edges depend on "
    "it, compare runs with a perturbed or alternative prior."
)
_LIONESS_PRIOR = (
    "Each sample's network comes from two runs of the base method, with and without that "
    "sample, so it inherits the base method's treatment of the prior: a starting network, "
    "not a fixed constraint. LIONESS adds no weighting of its own, and edges present in "
    "every sample's network can simply reflect the shared prior; compare runs with a "
    "perturbed or alternative prior."
)
REQUEST_CONCERNS: Mapping[str, tuple[RequestConcern, ...]] = {
    "run_panda": (
        RequestConcern(concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
                       note=_PRIOR_AS_START, artifacts=("regulatory_network",)),
    ),
    "run_puma": (
        RequestConcern(
            concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
            note=_PRIOR_AS_START + " miRNA edges follow the same rule; their cooperativity "
            "with other regulators stays at its initial value.",
            artifacts=("regulatory_network",),
        ),
    ),
    "run_lioness_panda": (
        RequestConcern(concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
                       note=_LIONESS_PRIOR, artifacts=("regulatory_network",)),
    ),
    "run_lioness_puma": (
        RequestConcern(concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
                       note=_LIONESS_PRIOR, artifacts=("regulatory_network",)),
    ),
    # netZooPy 0.11.0 otter/otter.py:44-69; loader data/otter.py:210, 246-250.
    "run_otter": (
        RequestConcern(
            concern="memory_limit", label=_MEMORY_LIMIT,
            note=(
                "`precision=single` keeps OTTER's largest array, the gene-by-gene "
                "co-expression matrix, in single precision during the optimization. The "
                "loader first computes that matrix in double precision, so peak memory while "
                "loading is not reduced, and the optimization and the output network stay in "
                "double precision."
            ),
            controls=("precision",),
        ),
        RequestConcern(
            concern="iteration_stopping",
            label="a run iterates for a long time or does not stop",
            note=(
                "OTTER runs exactly `iterations` gradient steps (default 60) and then stops; "
                "there is no convergence test to wait for. `eta` is the step size of those steps."
            ),
            controls=("iterations", "eta"),
        ),
        RequestConcern(
            concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
            note=(
                "OTTER's objective has no motif term: the seed matrix only sets where the "
                "gradient steps start. How far the result can move from the seed depends on "
                "`iterations` (default 60) and the step size `eta` (default 1e-5); `lam` "
                "balances the PPI and co-expression fits, and `gamma` shrinks the network "
                "toward zero, not toward the seed."
            ),
            controls=("iterations", "eta", "lam", "gamma"),
        ),
    ),
    # giraffe/giraffe.py:161, 195-268 (fit), :225 (get_tfa returns |TFA|);
    # executor execution.py:913 and data/giraffe.py:298-302 (the .tfa file).
    "run_giraffe": (
        RequestConcern(
            concern="activity_apart_from_expression",
            label="a regulator's activity may differ from its own mRNA level",
            note=(
                "GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of "
                "its target genes and the TF-TF protein interactions; the TF's own mRNA level "
                "is not an input to it. If the TF's gene is among the expression rows it still "
                "counts as an ordinary target, so its activity is not tied to its mRNA rather "
                "than independent of it."
            ),
            artifacts=("tf_activity_matrix",),
        ),
        RequestConcern(
            concern="per_sample_values",
            label="a value is needed for each sample",
            note=(
                "The activity matrix holds one value per TF per sample (TF by sample, written "
                "as the `.tfa` output). GIRAFFE reports absolute activity, so every value is "
                "zero or positive."
            ),
            artifacts=("tf_activity_matrix",),
        ),
        RequestConcern(
            concern="unreliable_prior", label=_UNRELIABLE_PRIOR,
            note=(
                "GIRAFFE starts its regulatory matrix from the motif prior, then fits expression "
                "together with agreement to the PPI and co-expression; no loss term keeps the "
                "matrix close to the motif. How far it moves is set by the optimizer's learning "
                "rate, its iteration limits and the loss weights, none of which this agent sets, "
                "so compare runs with a perturbed or alternative prior to see which effects "
                "depend on it."
            ),
            artifacts=("regulatory_network",),
        ),
    ),
    # bonobo/bonobo.py:59-65, 94-121, 237-245, 350-389; executor execution_bonobo.py:207-218.
    "run_bonobo": (
        RequestConcern(
            concern="per_edge_confidence",
            label="a confidence value is needed for each connection in each sample",
            note=(
                "With `sparsify=true` BONOBO computes a p-value for every connection in every "
                "sample and keeps those with a two-sided p-value below `bonobo_confidence` "
                "(default 0.05), without multiple-testing correction. With `save_pvals=true` as "
                "well, the full network is kept and the p-values are saved beside it instead."
            ),
            controls=("sparsify", "bonobo_confidence", "save_pvals"),
        ),
        RequestConcern(
            concern="memory_limit", label=_MEMORY_LIMIT,
            note=(
                "Each sample's network is written to its own file; `keep_in_memory=false` (the "
                "default) avoids also holding every network in memory. `precision` applies only "
                "to the input expression table: the networks are computed and saved in double "
                "precision either way."
            ),
            controls=("keep_in_memory", "precision"),
        ),
    ),
    # dragon/dragon.py:17-34, 82-107; executor execution.py:740-741, 780-796.
    "run_dragon": (
        RequestConcern(
            concern="penalty_choice",
            label="it is unclear how strongly to regularize or which penalty values to use",
            note=(
                "Leave `lambda1` and `lambda2` empty and DRAGON estimates both shrinkage values "
                "from the data by minimizing an analytic risk, and reports the values it used. "
                "To set them yourself, set both."
            ),
            controls=("lambda1", "lambda2"),
        ),
    ),
    # netZooPy lioness/lioness_for_dragon.py; executor execution_lioness_dragon.py.
    "run_lioness_dragon": (
        RequestConcern(
            concern="penalty_choice",
            label="it is unclear how strongly to regularize or which penalty values to use",
            note=(
                "Leave `lambda1` and `lambda2` empty and DRAGON's two shrinkage values are "
                "estimated once from all samples and reused for every sample's network, as "
                "netZooPy's LIONESS-DRAGON does. To set them yourself, set both."
            ),
            controls=("lambda1", "lambda2"),
        ),
        RequestConcern(
            concern="memory_limit", label=_MEMORY_LIMIT,
            note=(
                "The per-sample table holds one value per feature pair per sample. Above 20 "
                "million values the run is refused before it starts; reduce the features (for "
                "example the most variable ones) or run DRAGON for one aggregate network."
            ),
            artifacts=("multi_omic_network",),
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class WorkflowControlDefinition:
    """One user-facing control and its executor schema contract."""

    name: str
    control_type: ControlType
    default: Any = None
    allowed_values: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    nullable: bool = False
    selection_tags: frozenset[str] = frozenset()
    executor_argument: str | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class ConditionalOutputDefinition:
    """Machine-checkable output semantics for a control combination."""

    when: Mapping[str, Any]
    produced_artifacts: frozenset[ArtifactType]
    semantics: str
    manifest_expectations: Mapping[str, Any] = field(default_factory=dict)
    valid: bool = True


@dataclass(frozen=True, slots=True)
class HandoffConsumerDefinition:
    """A consumer whose registered input schema accepts a producer artifact."""

    action: RecommendedAction
    workflow: str
    input_field: str
    required_prior_inputs: tuple[str, ...] = ()
    accepted_input_granularities: frozenset[Granularity] = frozenset()


@dataclass(frozen=True, slots=True)
class OutputCapabilityDefinition:
    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: frozenset[EntityType]
    granularities: frozenset[Granularity]
    accepted_input_modalities: frozenset[InputModality] = frozenset()
    accepted_input_granularities: frozenset[Granularity] = frozenset()
    produced_artifacts: frozenset[ArtifactType] = frozenset()
    transformations: frozenset[str] = frozenset()
    scientific_objectives: frozenset[str] = frozenset()
    incompatible_input_artifacts: frozenset[ArtifactType] = frozenset()
    selection_phrases: tuple[str, ...] = ()
    regulator_types: frozenset[Literal["tf", "mirna"]] = frozenset()
    target_types: frozenset[Literal["gene"]] = frozenset()
    guidance_predecessors: tuple[RecommendedAction, ...] = ()
    input_artifacts: frozenset[ArtifactType] = frozenset()
    # Executor-level prerequisites that are not themselves output ontology
    # values. Keeping these as registry strings avoids widening the provider
    # outcome schema just to express a missing file requirement.
    required_input_artifacts: frozenset[str] = frozenset()
    handoff_targets: tuple[RecommendedAction, ...] = ()
    selection_tags: frozenset[str] = frozenset()
    guidance_notes: tuple[str, ...] = ()
    prefer_when: tuple[str, ...] = ()
    handoff_contract: str = ""
    conditional_outputs: tuple[ConditionalOutputDefinition, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action: ActionName
    workflow: str
    required_inputs: tuple[str, ...] = ()
    # Each group is an OR-set: at least one field in every group is required.
    # This keeps conditional sources (such as OTTER expression vs precomputed C)
    # explicit without pretending both files are mandatory.
    required_input_groups: tuple[tuple[str, ...], ...] = ()
    optional_inputs: tuple[str, ...] = ()
    executor_fields: tuple[str, ...] = ()
    executor_defaults: Mapping[str, Any] = field(default_factory=dict)
    validation_steps: tuple[str, ...] = ()
    # Stable fail-closed semantic-preflight key. Every run action must set it.
    input_validator: ActionName | None = None
    local: bool = False
    run: bool = False
    memory_metadata: Mapping[str, str] = field(default_factory=dict)
    cli_command: str | None = None
    handoff_cli_commands: Mapping[str, str] = field(default_factory=dict)
    controls: tuple[WorkflowControlDefinition, ...] = ()
    output_capability: OutputCapabilityDefinition | None = None


ACTION_DEFINITIONS: dict[ActionName, ActionDefinition] = {
    "no_tool": ActionDefinition("no_tool", "NO-TOOL"),
    "inspect_inputs": ActionDefinition(
        "inspect_inputs",
        "INPUTS",
        required_inputs=("expression_file", "motif_file", "ppi_file"),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "taxon",
        ),
        executor_defaults={"mirna_file": "", "taxon": ""},
        optional_inputs=("taxon",),
        local=True,
    ),
    "inspect_condor_inputs": ActionDefinition(
        "inspect_condor_inputs",
        "CONDOR-INPUTS",
        required_inputs=("network_file",),
        executor_fields=("network_file",),
        local=True,
    ),
    "inspect_cobra_inputs": ActionDefinition(
        "inspect_cobra_inputs",
        "COBRA-INPUTS",
        required_inputs=("expression_file", "design_file"),
        executor_fields=("expression_file", "design_file"),
        local=True,
    ),
    "inspect_sambar_inputs": ActionDefinition(
        "inspect_sambar_inputs",
        "SAMBAR-INPUTS",
        required_inputs=("mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file"),
        executor_fields=("mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file", "kmin", "kmax", "cluster"),
        local=True,
    ),
    "inspect_dragon_inputs": ActionDefinition(
        "inspect_dragon_inputs",
        "DRAGON-INPUTS",
        required_inputs=("omics_layer_1", "omics_layer_2"),
        executor_fields=("omics_layer_1", "omics_layer_2"),
        local=True,
    ),
    "inspect_otter_inputs": ActionDefinition(
        "inspect_otter_inputs",
        "OTTER-INPUTS",
        required_inputs=("motif_file", "ppi_file"),
        optional_inputs=("expression_file", "coexpression_file"),
        executor_fields=(
            "expression_file", "coexpression_file", "motif_file", "ppi_file", "precision",
        ),
        local=True,
    ),
    "inspect_giraffe_inputs": ActionDefinition(
        "inspect_giraffe_inputs",
        "GIRAFFE-INPUTS",
        required_inputs=("expression_file", "motif_file", "ppi_file"),
        executor_fields=("expression_file", "motif_file", "ppi_file"),
        local=True,
    ),
    "inspect_bonobo_inputs": ActionDefinition(
        "inspect_bonobo_inputs",
        "BONOBO-INPUTS",
        required_inputs=("expression_file",),
        optional_inputs=(
            "output_dir", "bonobo_output_format", "sample_names", "sparsify",
            "bonobo_confidence", "save_pvals", "genes_axis", "log_transformed", "centered",
        ),
        executor_fields=(
            "expression_file", "output_dir", "bonobo_output_format", "sample_names",
            "sparsify", "bonobo_confidence", "save_pvals", "genes_axis", "log_transformed", "centered",
        ),
        local=True,
    ),
    "format_expression": ActionDefinition(
        "format_expression",
        "FORMAT-EXPRESSION",
        required_inputs=("expression_file", "output_file"),
        executor_fields=(
            "expression_file",
            "output_file",
            "genes_axis",
            "with_header",
        ),
        local=True,
    ),
    "convert_expression": ActionDefinition(
        "convert_expression",
        "CONVERT-EXPRESSION",
        required_inputs=("expression_file", "output_file"),
        executor_fields=("expression_file", "output_file"),
        local=True,
    ),
    "run_panda": ActionDefinition(
        "run_panda",
        "PANDA",
        required_inputs=("expression_file", "motif_file", "ppi_file", "output_file"),
        optional_inputs=("with_header", "coexpression_file", "taxon"),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "with_header",
            "coexpression_file",
            "taxon",
        ),
        executor_defaults={"taxon": ""},
        validation_steps=("inspect_inputs",),
        input_validator="run_panda",
        local=True,
        run=True,
        memory_metadata={"method_family": "panda"},
        cli_command="run-panda",
        handoff_cli_commands={"coexpression_file": "run-panda-precomputed"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset(
                {"gene_expression", "coexpression"}
            ),
            accepted_input_granularities=frozenset({"aggregate"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({
                "tf_gene_regulation", "aggregate_network", "message_passing",
                "lioness_base_compatibility",
            }),
            prefer_when=("established_method:yes",),
            handoff_contract=(
                "PANDA consumes a gene-by-sample expression matrix plus motif and "
                "PPI priors, or a validated adjusted gene-by-gene co-expression "
                "matrix through coexpression_file. When supplied, the adjusted matrix "
                "replaces PANDA's Pearson co-expression construction while the expression "
                "file remains the gene-order and prior compatibility source. PANDA "
                "produces a weighted TF-to-gene regulatory network. "
                "Convert that network to a source-target-weight bipartite edge list "
                "before handing it to CONDOR."
            ),
        ),
    ),
    "run_puma": ActionDefinition(
        "run_puma",
        "PUMA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "coexpression_file",
            "taxon",
        ),
        executor_defaults={"taxon": ""},
        optional_inputs=("coexpression_file", "taxon"),
        validation_steps=("inspect_inputs",),
        input_validator="run_puma",
        local=True,
        run=True,
        memory_metadata={"method_family": "puma"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "mirna", "gene"}),
            regulator_types=frozenset({"tf", "mirna"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset(
                {"gene_expression", "coexpression"}
            ),
            accepted_input_granularities=frozenset({"aggregate"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior", "mirna_prior"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({
                "mirna_regulation", "aggregate_network", "message_passing",
            }),
            prefer_when=("regulator_class:mirna",),
            guidance_notes=(
                "PUMA uses message passing to integrate miRNA-target predictions "
                "with target-gene co-expression alongside TF motif and PPI evidence.",
            ),
            handoff_contract=(
                "PUMA consumes a gene-by-sample expression matrix plus motif, PPI, "
                "and miRNA priors, or a validated adjusted gene-by-gene co-expression "
                "matrix through coexpression_file. When supplied, the adjusted matrix "
                "replaces PUMA's Pearson co-expression construction. PUMA produces "
                "a weighted regulator-to-gene network. "
                "Convert that network to a source-target-weight bipartite edge list "
                "before handing it to CONDOR."
            ),
        ),
    ),
    "run_lioness_panda": ActionDefinition(
        "run_lioness_panda",
        "LIONESS-PANDA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "lioness_output",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "output_file",
            "lioness_output",
            "taxon",
        ),
        executor_defaults={"taxon": ""},
        optional_inputs=("taxon",),
        validation_steps=("inspect_inputs",),
        input_validator="run_lioness_panda",
        local=True,
        run=True,
        memory_metadata={"method_family": "lioness", "base_method": "panda"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior"}),
            guidance_predecessors=("run_panda",),
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({
                "sample_specific", "tf_gene_regulation", "message_passing",
                "leave_one_out_network_inference",
            }),
            prefer_when=("cohort_size:many", "per_sample_quantity:wiring",),
            handoff_contract=(
                "LIONESS-PANDA uses the original gene-by-sample expression matrix, "
                "motif and PPI priors to internally infer the aggregate PANDA "
                "network and derive sample-specific TF-to-gene networks. The PANDA "
                "predecessor is a guidance prerequisite, not a direct file handoff."
            ),
        ),
    ),
    "run_lioness_puma": ActionDefinition(
        "run_lioness_puma",
        "LIONESS-PUMA",
        required_inputs=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "lioness_output",
        ),
        executor_fields=(
            "expression_file",
            "motif_file",
            "ppi_file",
            "mirna_file",
            "output_file",
            "lioness_output",
            "taxon",
        ),
        executor_defaults={"taxon": ""},
        optional_inputs=("taxon",),
        validation_steps=("inspect_inputs",),
        input_validator="run_lioness_puma",
        local=True,
        run=True,
        memory_metadata={"method_family": "lioness", "base_method": "puma"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "mirna", "gene"}),
            regulator_types=frozenset({"tf", "mirna"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"regulatory_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior", "mirna_prior"}),
            guidance_predecessors=("run_puma",),
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({
                "sample_specific", "mirna_regulation", "message_passing",
                "leave_one_out_network_inference",
            }),
            prefer_when=("cohort_size:many", "per_sample_quantity:wiring", "regulator_class:mirna",),
            handoff_contract=(
                "LIONESS-PUMA uses the original gene-by-sample expression matrix, "
                "motif, PPI, and miRNA priors to internally infer the aggregate PUMA "
                "network and derive sample-specific TF/miRNA-to-gene networks. The "
                "PUMA predecessor is a guidance prerequisite, not a direct file handoff."
            ),
        ),
    ),
    "run_lioness_coexpression": ActionDefinition(
        "run_lioness_coexpression",
        "LIONESS-COEXPRESSION",
        required_inputs=("expression_file", "output_file", "lioness_output"),
        optional_inputs=("taxon",),
        executor_fields=("expression_file", "output_file", "lioness_output"),
        input_validator="run_lioness_coexpression",
        local=True,
        run=True,
        memory_metadata={
            "method_family": "lioness",
            "base_method": "coexpression",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate", "sample_specific"}),
            accepted_input_modalities=frozenset({"gene_expression"}),
            produced_artifacts=frozenset({"coexpression_network"}),
            incompatible_input_artifacts=frozenset({"mutation_matrix"}),
            input_artifacts=frozenset({"expression_matrix"}),
            selection_tags=frozenset({
                "sample_specific", "coexpression", "leave_one_out_network_inference",
            }),
            prefer_when=("cohort_size:many", "covariates:no",),
            handoff_contract=(
                "LIONESS co-expression consumes a gene-by-sample expression matrix "
                "and produces sample-specific co-expression networks."
            ),
        ),
    ),
    "run_condor": ActionDefinition(
        "run_condor",
        "CONDOR",
        required_inputs=("network_file", "output_dir"),
        optional_inputs=("prefix",),
        executor_fields=("network_file", "output_dir", "prefix"),
        executor_defaults={"prefix": "condor"},
        validation_steps=("inspect_condor_inputs",),
        input_validator="run_condor",
        local=True,
        run=True,
        memory_metadata={"method_family": "condor"},
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="community_assignment",
            entity_types=frozenset({"gene"}),
            # One community assignment per network, not one per sample. The
            # former not_applicable value matched no interpretation the semantic
            # prompt permits, so this capability could never be selected.
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"regulatory_network"}),
            selection_tags=frozenset({"bipartite_community_detection", "modules"}),
            handoff_contract=(
                "CONDOR consumes a weighted source-target bipartite edge list made "
                "from a validated regulator-gene network and returns community "
                "assignments with regulator-side and gene-side partitions."
            ),
        ),
    ),
    "run_cobra": ActionDefinition(
        "run_cobra",
        "COBRA",
        required_inputs=("expression_file", "design_file", "output_dir"),
        optional_inputs=("taxon",),
        executor_fields=("expression_file", "design_file", "output_dir"),
        validation_steps=("inspect_cobra_inputs",),
        input_validator="run_cobra",
        local=True,
        run=True,
        memory_metadata={"method_family": "cobra"},
        cli_command="run-cobra",
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=("run_panda", "run_puma", "run_otter"),
            selection_tags=frozenset(
                {
                    "covariate_association",
                    "hospital_effect_assessment",
                    "sequencing_batch_effect_assessment",
                    "batch_correction",
                    "high_order_correlation",
                }
            ),
            prefer_when=("covariates:yes",),
            handoff_contract=(
                "COBRA consumes a gene-by-sample expression matrix and numeric sample "
                "covariates, then produces a covariate-associated covariance "
                "decomposition and a labeled adjusted gene-by-gene co-expression "
                "artifact. PANDA, PUMA, or OTTER may consume the adjusted artifact "
                "through coexpression_file only after the downstream identifier/order "
                "contract is revalidated; the raw components are not a matrix input "
                "by themselves."
            ),
        ),
    ),
    "run_sambar": ActionDefinition(
        "run_sambar",
        "SAMBAR",
        required_inputs=(
            "mutation_file",
            "exon_size_file",
            "cancer_gene_file",
            "pathway_file",
            "output_dir",
        ),
        optional_inputs=(
            "norm_patient",
            "kmin",
            "kmax",
            "gmt_msigdb",
            "subset_cancer_genes",
            "distance",
            "linkage",
            "cluster",
            "taxon",
        ),
        executor_fields=(
            "mutation_file",
            "exon_size_file",
            "cancer_gene_file",
            "pathway_file",
            "output_dir",
            "norm_patient",
            "kmin",
            "kmax",
            "gmt_msigdb",
            "subset_cancer_genes",
            "distance",
            "linkage",
            "cluster",
        ),
        executor_defaults={
            "norm_patient": True,
            "kmin": 2,
            "kmax": 4,
            "gmt_msigdb": True,
            "subset_cancer_genes": True,
            "distance": "binomial",
            "linkage": "complete",
            "cluster": True,
        },
        validation_steps=("inspect_sambar_inputs",),
        input_validator="run_sambar",
        local=True,
        run=True,
        memory_metadata={"method_family": "sambar"},
        output_capability=OutputCapabilityDefinition(
            operation="analyze",
            artifact_type="pathway_mutation_matrix",
            entity_types=frozenset({"sample", "pathway"}),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset({"somatic_mutation"}),
            produced_artifacts=frozenset(
                {
                    "gene_mutation_scores",
                    "pathway_mutation_matrix",
                    "sample_cluster_assignment",
                    "sample_distance_matrix",
                }
            ),
            transformations=frozenset(
                {
                    "gene_length_normalization",
                    "patient_mutation_burden_normalization",
                    "pathway_aggregation",
                    "sample_distance",
                    "sample_clustering",
                }
            ),
            scientific_objectives=frozenset({"cancer_subtyping"}),
            incompatible_input_artifacts=frozenset({"expression_matrix"}),
            selection_phrases=(
                "somatic mutation",
                "tumor mutation burden",
                "gene length",
                "pathway score",
                "sparse mutation",
                "patient clustering",
                "體細胞突變",
                "突變負荷",
                "基因長度",
                "途徑分數",
                "生物途徑",
                "稀疏",
                "病患分群",
                "亞型分群",
            ),
            input_artifacts=frozenset({"mutation_matrix"}),
            selection_tags=frozenset({"somatic_mutation", "cancer_subtyping", "pathway_scores"}),
            handoff_contract=(
                "SAMBAR consumes a samples-by-genes somatic mutation CSV, a gene-length "
                "CSV, a tab-delimited cancer-gene list, and a GMT pathway file. It produces "
                "gene and pathway mutation-score matrices plus optional sample cluster labels. "
                "These are not direct inputs to PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, "
                "CONDOR, or COBRA; prepare and validate that workflow's declared input "
                "artifact separately before any composition."
            ),
        ),
    ),
    "run_dragon": ActionDefinition(
        "run_dragon",
        "DRAGON",
        required_inputs=("omics_layer_1", "omics_layer_2", "output_file"),
        optional_inputs=("output_format", "lambda1", "lambda2"),
        executor_fields=(
            "omics_layer_1", "omics_layer_2", "output_file",
            "output_format", "lambda1", "lambda2",
        ),
        executor_defaults={"output_format": "matrix"},
        validation_steps=("inspect_dragon_inputs",),
        input_validator="run_dragon",
        local=True,
        run=True,
        memory_metadata={"method_family": "dragon", "api": "netZooPy.dragon"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="multi_omic_network",
            entity_types=frozenset({
                "omics_layer_1_feature", "omics_layer_2_feature",
                "gene", "mirna", "protein", "metabolite",
            }),
            granularities=frozenset({"aggregate"}),
            accepted_input_modalities=frozenset({"multi_omic_continuous"}),
            # `expression_matrix` is one concrete form of the measured omics
            # table that DRAGON can consume. Keep the generic value as well:
            # semantic routing may know only that the inputs are measurements,
            # while the executor still requires exactly two layer files.
            input_artifacts=frozenset({"measurement_dataset", "expression_matrix"}),
            selection_tags=frozenset({"multi_omic_network", "partial_correlation", "aggregate_network"}),
            guidance_notes=(
                "DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, "
                "rather than a generic Graphical Lasso penalty matrix.",
                "DRAGON's precision-derived partial correlations estimate within-layer and "
                "cross-layer conditional associations after accounting for the other modeled "
                "features; this is an undirected association graph, not a causal guarantee "
                "or proof that every indirect effect is removed.",
                "The declared DRAGON API does not expose a separately tunable third "
                "cross-layer penalty such as lambda_inter; three independently controlled "
                "intra/inter-omics penalties are outside this workflow contract.",
            ),
            handoff_contract=(
                "DRAGON consumes exactly two paired sample-by-feature continuous omics tables "
                "and produces one aggregate undirected multi-omic network. The matrix is a "
                "symmetric partial-correlation GGM with layer-qualified node IDs; edge lists "
                "contain source, target, partial_correlation, and precision. This is an "
                "association network, not a causal graph. There is no direct handoff to PANDA, "
                "PUMA, LIONESS, CONDOR, BONOBO, or OTTER; a separate validated conversion would "
                "be required before any tool that consumes a different artifact contract."
            ),
        ),
    ),
    "run_lioness_dragon": ActionDefinition(
        "run_lioness_dragon",
        "LIONESS-DRAGON",
        required_inputs=("omics_layer_1", "omics_layer_2", "output_file", "lioness_output"),
        optional_inputs=("lambda1", "lambda2"),
        executor_fields=(
            "omics_layer_1", "omics_layer_2", "output_file", "lioness_output",
            "lambda1", "lambda2",
        ),
        validation_steps=("inspect_dragon_inputs",),
        input_validator="run_lioness_dragon",
        local=True,
        run=True,
        memory_metadata={"method_family": "lioness", "base_method": "dragon", "api": "netZooPy.dragon"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="multi_omic_network",
            entity_types=frozenset({
                "omics_layer_1_feature", "omics_layer_2_feature",
                "gene", "mirna", "protein", "metabolite",
            }),
            # Sample-specific only: an aggregate request stays DRAGON's, with no
            # new tie, although the run also writes the all-sample network.
            granularities=frozenset({"sample_specific"}),
            accepted_input_modalities=frozenset({"multi_omic_continuous"}),
            input_artifacts=frozenset({"measurement_dataset", "expression_matrix"}),
            guidance_predecessors=("run_dragon",),
            selection_tags=frozenset({
                "multi_omic_network", "partial_correlation", "sample_specific",
                "leave_one_out_network_inference",
            }),
            guidance_notes=(
                "LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, "
                "then derives each sample's network from the all-sample network and the network "
                "refitted without that sample.",
                "Each sample's network is an undirected partial-correlation graph across both "
                "layers; like DRAGON's, it is an association graph, not a causal one.",
            ),
            handoff_contract=(
                "LIONESS-DRAGON consumes exactly two paired sample-by-feature continuous omics "
                "tables, DRAGON's inputs, and produces the aggregate DRAGON matrix plus one "
                "partial-correlation network per sample, written as an edge-by-sample table "
                "(source, target, one column per sample) with layer-qualified node IDs. DRAGON "
                "is a guidance prerequisite, not a file handoff; there is no direct handoff to "
                "PANDA, PUMA, CONDOR, BONOBO or OTTER."
            ),
        ),
    ),
    "run_otter": ActionDefinition(
        "run_otter",
        "OTTER",
        required_inputs=("motif_file", "ppi_file", "output_file"),
        required_input_groups=(("expression_file", "coexpression_file"),),
        optional_inputs=(
            "expression_file", "coexpression_file", "output_format", "computing",
            "precision", "lam", "gamma", "iterations", "eta", "bexp", "taxon",
        ),
        executor_fields=(
            "expression_file", "coexpression_file", "motif_file", "ppi_file", "output_file",
            "output_format", "computing", "precision", "lam", "gamma", "iterations", "eta", "bexp",
        ),
        validation_steps=("inspect_otter_inputs",),
        input_validator="run_otter",
        local=True,
        run=True,
        memory_metadata={"method_family": "otter", "api": "netZooPy.otter.otter"},
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            granularities=frozenset({"aggregate"}),
            guidance_predecessors=(),
            input_artifacts=frozenset({"expression_matrix", "coexpression_network"}),
            accepted_input_granularities=frozenset({"aggregate"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior"}),
            handoff_targets=("run_condor",),
            selection_tags=frozenset({"tf_gene_regulation", "aggregate_network", "relaxed_graph_matching"}),
            prefer_when=("compute_constraints:constrained",),
            handoff_contract=(
                "OTTER consumes an OTTER seed/prior TF-by-gene edge list W, a TF-TF PPI "
                "projection P, and either a gene-by-sample expression matrix (from which "
                "C is computed) or a validated labeled gene-by-gene co-expression matrix. "
                "Its lam parameter weights co-expression versus PPI as (lam, 1-lam), and "
                "gamma is the verified regularization parameter. It produces an aggregate "
                "TF-to-gene network whose edge weight is the optimized OTTER W score. "
                "PPI and co-expression are never PANDA motif priors. Only a validated "
                "source-target-weight edge-list export with disjoint regulator/target IDs "
                "may be handed to CONDOR; a matrix export needs an explicit conversion."
            ),
        ),
    ),
    # An entity list names entities *in the result*. GIRAFFE and BONOBO declared
    # `sample`, which the semantic prompt says a sample-specific result does not
    # create, and SAMBAR declared `gene`, which its own artifact ontology forbids.
    # Those declarations turned one model mistake into a confident wrong-tool
    # recommendation. SAMBAR keeps `sample`: its artifact really is
    # sample-to-cluster labels, where samples are entities in the result.
    "run_giraffe": ActionDefinition(
        "run_giraffe",
        "GIRAFFE",
        required_inputs=("expression_file", "motif_file", "ppi_file", "output_file"),
        optional_inputs=("taxon",),
        executor_fields=("expression_file", "motif_file", "ppi_file", "output_file"),
        validation_steps=("inspect_giraffe_inputs",),
        input_validator="run_giraffe",
        local=True,
        run=True,
        memory_metadata={
            "method_family": "giraffe",
            "api": "netZooPy.giraffe.Giraffe",
            "runtime": "docker",
            "netzoopy_version": "0.11.0",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="signed_regulatory_effect_network",
            entity_types=frozenset({"tf", "gene"}),
            regulator_types=frozenset({"tf"}),
            target_types=frozenset({"gene"}),
            # GIRAFFE returns an aggregate TF-gene regulation matrix plus a
            # TF-by-sample activity matrix; it does not return sample-specific
            # TF-gene networks.
            granularities=frozenset({"aggregate"}),
            produced_artifacts=frozenset({
                "regulatory_network", "tf_activity_matrix",
            }),
            input_artifacts=frozenset({"expression_matrix"}),
            required_input_artifacts=frozenset({"motif_prior", "ppi_prior"}),
            handoff_targets=(),
            selection_tags=frozenset({
                "tf_gene_regulation",
                "tfa",
                "aggregate_network",
                "biologically_informed_matrix_factorization",
                "joint_grn_tfa_inference",
                "linear_model_coefficients",
                "signed_partial_regulatory_effects",
                "tfa_covariate_regression",
            }),
            prefer_when=("tf_activity_vs_expression:yes", "per_sample_quantity:activity",),
            handoff_contract=(
                "GIRAFFE consumes gene-by-sample expression, a TF-by-gene motif/prior, "
                "and a TF-by-TF PPI matrix after explicit labelled-file conversion. "
                "Through biologically informed matrix factorization it jointly fits "
                "gene expression as Y approximately R times absolute TFA. TFA supplies "
                "the sample-varying predictors, while entries of R are signed partial "
                "regulatory effects interpretable as linear-model coefficients: positive "
                "for activation and negative for repression. It returns the aggregate "
                "TF-by-gene R matrix and a TF-by-sample TFA matrix. "
                "This is not a direct CONDOR handoff: it requires validated "
                "matrix-to-edge-list conversion and user confirmation. No other "
                "direct handoff is registered."
            ),
        ),
    ),
    "run_bonobo": ActionDefinition(
        "run_bonobo",
        "BONOBO",
        required_inputs=("expression_file", "output_dir"),
        optional_inputs=(
            "bonobo_output_format", "sample_names", "sparsify", "bonobo_confidence",
            "save_pvals", "precision", "keep_in_memory", "delta", "genes_axis",
            "log_transformed", "centered", "taxon",
        ),
        executor_fields=(
            "expression_file", "output_dir", "bonobo_output_format", "sample_names",
            "sparsify", "bonobo_confidence", "save_pvals", "precision", "keep_in_memory",
            "delta", "genes_axis", "log_transformed", "centered",
        ),
        executor_defaults={
            "bonobo_output_format": ".h5",
            "sample_names": [],
            "sparsify": False,
            "bonobo_confidence": 0.05,
            "save_pvals": False,
            "precision": "single",
            "keep_in_memory": False,
            "genes_axis": "auto",
        },
        validation_steps=("inspect_bonobo_inputs",),
        input_validator="run_bonobo",
        local=True,
        run=True,
        memory_metadata={
            "method_family": "bonobo",
            "api": "netZooPy.bonobo.Bonobo.run_bonobo",
            "netzoopy_version": "0.11.0",
        },
        output_capability=OutputCapabilityDefinition(
            operation="infer",
            artifact_type="coexpression_network",
            entity_types=frozenset({"gene"}),
            granularities=frozenset({"sample_specific"}),
            input_artifacts=frozenset({"expression_matrix"}),
            handoff_targets=(),
            produced_artifacts=frozenset({"coexpression_network", "pvalue_matrix"}),
            conditional_outputs=(
                ConditionalOutputDefinition(
                    when={"sparsify": False, "save_pvals": False},
                    produced_artifacts=frozenset({"coexpression_network"}),
                    semantics=(
                        "full sample-specific gene-gene co-expression matrices; "
                        "no p-value artifact is written"
                    ),
                    manifest_expectations={
                        "sparsify_requested": False,
                        "network_sparsified": False,
                        "pvalue_thresholding_required": False,
                    },
                ),
                ConditionalOutputDefinition(
                    when={"sparsify": True, "save_pvals": False},
                    produced_artifacts=frozenset({"coexpression_network"}),
                    semantics=(
                        "upstream thresholds each sample-specific co-expression "
                        "matrix; no p-value artifact is written"
                    ),
                    manifest_expectations={
                        "sparsify_requested": True,
                        "network_sparsified": True,
                        "pvalue_thresholding_required": False,
                    },
                ),
                ConditionalOutputDefinition(
                    when={"sparsify": True, "save_pvals": True},
                    produced_artifacts=frozenset({"coexpression_network", "pvalue_matrix"}),
                    semantics=(
                        "upstream retains the full co-expression matrix for each "
                        "selected sample and writes a matching p-value matrix; "
                        "threshold it from the saved p-value matrix; it does not "
                        "also emit an already-thresholded network in this mode"
                    ),
                    manifest_expectations={
                        "sparsify_requested": True,
                        "network_sparsified": False,
                        "pvalue_thresholding_required": True,
                    },
                ),
                ConditionalOutputDefinition(
                    when={"sparsify": False, "save_pvals": True},
                    produced_artifacts=frozenset(),
                    semantics="invalid: save_pvals requires sparsify",
                    valid=False,
                ),
            ),
            selection_tags=frozenset({
                "sample_specific", "coexpression", "bayesian",
                "sparse_pvalue_coexpression",
            }),
            prefer_when=("cohort_size:few", "per_edge_confidence:needed",),
            handoff_contract=(
                "BONOBO consumes a labelled gene-by-sample expression matrix and "
                "produces one gene-by-gene sample-specific co-expression matrix per "
                "selected sample, plus optional matching p-value matrices. It does "
                "not produce an aggregate/prior network, GRN, TF-gene regulation, or "
                "causal network. BONOBO output is not a direct PANDA/PUMA "
                "coexpression_file handoff: those workflows require one validated "
                "aggregate labeled gene-by-gene matrix. A separate explicit "
                "sample-selection or aggregation conversion is required, with its "
                "own validation and user confirmation. It is not a direct handoff "
                "to LIONESS, CONDOR, COBRA, DRAGON, or OTTER either."
            ),
        ),
    ),
    "query_context7": ActionDefinition(
        "query_context7",
        "CONTEXT7",
        required_inputs=("library_name", "docs_query"),
        executor_fields=("library_name", "docs_query", "library_id"),
    ),
    "web_search": ActionDefinition(
        "web_search",
        "WEB-SEARCH",
        required_inputs=("web_query",),
        executor_fields=("web_query",),
    ),
    "download_string": ActionDefinition(
        "download_string",
        "STRING-DOWNLOAD",
        required_inputs=("taxon", "string_network_type"),
        executor_fields=("taxon", "string_network_type", "output_dir"),
        local=True,
    ),
}


def _control(
    name: str,
    control_type: ControlType,
    default: Any = None,
    *,
    allowed_values: tuple[Any, ...] = (),
    minimum: float | None = None,
    maximum: float | None = None,
    nullable: bool = False,
    selection_tags: frozenset[str] = frozenset(),
    description: str = "",
) -> WorkflowControlDefinition:
    return WorkflowControlDefinition(
        name=name,
        control_type=control_type,
        default=default,
        allowed_values=allowed_values,
        minimum=minimum,
        maximum=maximum,
        nullable=nullable,
        selection_tags=selection_tags,
        executor_argument=name,
        description=description,
    )


# User-facing controls are registry data, not renderer branches. Optional file
# inputs such as `coexpression_file` remain inputs; this table contains only
# knobs whose values are passed through to a workflow executor.
WORKFLOW_CONTROLS: dict[ActionName, tuple[WorkflowControlDefinition, ...]] = {
    "run_panda": (
        _control("with_header", "boolean", False, description="Expression input has a header."),
    ),
    "run_condor": (
        _control("prefix", "string", "condor", description="Prefix for derived CONDOR artifacts."),
    ),
    "run_sambar": (
        _control("norm_patient", "boolean", True),
        _control("kmin", "integer", 2, minimum=2),
        _control("kmax", "integer", 4, minimum=2),
        _control("gmt_msigdb", "boolean", True),
        _control("subset_cancer_genes", "boolean", True),
        _control("distance", "string", "binomial"),
        _control("linkage", "string", "complete"),
        _control("cluster", "boolean", True),
    ),
    "run_dragon": (
        _control("output_format", "enum", "matrix", allowed_values=("matrix", "edge_list")),
        _control("lambda1", "number", None, minimum=0, maximum=1, nullable=True),
        _control("lambda2", "number", None, minimum=0, maximum=1, nullable=True),
    ),
    "run_lioness_dragon": (
        _control("lambda1", "number", None, minimum=0, maximum=1, nullable=True),
        _control("lambda2", "number", None, minimum=0, maximum=1, nullable=True),
    ),
    "run_otter": (
        _control("output_format", "enum", "matrix", allowed_values=("matrix", "edge_list")),
        _control("computing", "enum", "cpu", allowed_values=("cpu", "gpu")),
        _control("precision", "enum", "double", allowed_values=("single", "double")),
        _control("lam", "number", 0.035, minimum=0, maximum=1),
        _control("gamma", "number", 0.335, minimum=0),
        _control("iterations", "integer", 60, minimum=1),
        _control("eta", "number", 0.00001, minimum=0),
        _control("bexp", "number", 1.0, minimum=0),
    ),
    "run_bonobo": (
        _control(
            "bonobo_output_format", "enum", ".h5",
            allowed_values=(".h5", ".hdf", ".txt", ".csv"),
        ),
        _control(
            "sample_names", "string_list", [],
            selection_tags=frozenset({"sample_specific"}),
            description="Explicit sample IDs; never positional sample indices.",
        ),
        _control(
            "sparsify", "boolean", False,
            selection_tags=frozenset({"sparse_pvalue_coexpression"}),
        ),
        _control(
            "bonobo_confidence", "number", 0.05, minimum=0, maximum=1,
            selection_tags=frozenset({"sparse_pvalue_coexpression"}),
        ),
        _control(
            "save_pvals", "boolean", False,
            selection_tags=frozenset({"sparse_pvalue_coexpression"}),
        ),
        _control("precision", "enum", "single", allowed_values=("single", "double")),
        _control("keep_in_memory", "boolean", False),
        _control(
            "delta", "number", None, minimum=0, maximum=1, nullable=True,
            description=(
                "Weight of the sample in its covariance; empty estimates it per sample. "
                "With sparsify it must be above 0 and below 1/3 (Log 224)."
            ),
        ),
        _control("genes_axis", "enum", "auto", allowed_values=("auto", "rows", "columns")),
        _control("log_transformed", "boolean", None, nullable=True),
        _control("centered", "boolean", None, nullable=True),
    ),
}

ACTION_DEFINITIONS = {
    action: replace(definition, controls=WORKFLOW_CONTROLS.get(action, ()))
    for action, definition in ACTION_DEFINITIONS.items()
}

ACTION_NAMES = frozenset(get_args(ActionName))
PROFILE_PREFERENCE_KEYS = frozenset(get_args(PreferenceKey))
REQUIRED_INPUTS = {
    action: definition.required_inputs
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.required_inputs
}
REQUIRED_INPUT_GROUPS = {
    action: definition.required_input_groups
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.required_input_groups
}
RUN_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.run
)
LOCAL_WORKFLOW_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items() if definition.local
)
LOCAL_EXECUTION_ACTIONS = LOCAL_WORKFLOW_ACTIONS
CODE_VALIDATION_STEPS = {
    action: list(ACTION_DEFINITIONS[action].validation_steps) for action in RUN_ACTIONS
}
WORKFLOW_MEMORY_METADATA = {
    action: dict(ACTION_DEFINITIONS[action].memory_metadata) for action in RUN_ACTIONS
}
OUTPUT_CAPABILITIES = {
    action: definition.output_capability
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.run and definition.output_capability is not None
}
# Log 283 (user decision): downstream-use notes answer a stated concern, like any
# other registry note, instead of being appended to every reply. The notes are
# DOWNSTREAM_ANALYSES's own; only when they are shown changes.
# Log 219's "other per-sample reading" is disambiguation, not downstream use:
# every LIONESS/GIRAFFE reply keeps it (Log 283).
OTHER_READING_NOTES: Mapping[str, str] = {
    "run_lioness_panda": _ACTIVITY_READING_NOTE,
    "run_lioness_puma": _ACTIVITY_READING_NOTE,
    "run_giraffe": _WIRING_READING_NOTE,
}
_DOWNSTREAM_USE = (
    "what to do with the result afterwards, for example comparing conditions or relating it to "
    "clinical variables"
)
REQUEST_CONCERNS = {
    **REQUEST_CONCERNS,
    **{
        action: (
            *REQUEST_CONCERNS.get(action, ()),
            RequestConcern(
                concern="downstream_use", label=_DOWNSTREAM_USE,
                note=" ".join(note for note in DOWNSTREAM_ANALYSES[action][1]
                              if note != OTHER_READING_NOTES.get(action)),
                artifacts=(OUTPUT_CAPABILITIES[action].artifact_type,),
            ),
        )
        for action in OUTPUT_CAPABILITIES if action in DOWNSTREAM_ANALYSES
    },
}


def _registry_definition(workflow_id: str, registry=None):
    source = registry if registry is not None else ACTION_DEFINITIONS
    if hasattr(source, "workflows"):
        source = source.workflows
    definition = source.get(workflow_id) if hasattr(source, "get") else None
    if definition is not None:
        return definition
    for action, candidate in source.items():
        if getattr(candidate, "workflow", None) == workflow_id:
            return candidate
    return None


def get_controls(
    workflow_id: str,
    selection_tags: Sequence[str] = (),
    registry=None,
) -> tuple[WorkflowControlDefinition, ...] | tuple[Any, ...]:
    """Return registry-declared controls applicable to a workflow request.

    ``registry`` may be either ``ACTION_DEFINITIONS`` or a validated project
    policy mapping. This keeps guidance and execution consumers on the same
    accessor while allowing the loaded YAML snapshot to remain authoritative.
    Untagged controls are always applicable; tagged controls require at least
    one matching requested selection tag.
    """
    definition = _registry_definition(workflow_id, registry)
    if definition is None:
        return ()
    controls = tuple(getattr(definition, "controls", ()) or ())
    requested = set(selection_tags)
    if not requested:
        return controls
    return tuple(
        control
        for control in controls
        if not set(getattr(control, "selection_tags", ()) or ())
        or set(getattr(control, "selection_tags", ()) or ()) & requested
    )


def resolve_conditional_output(
    workflow_id: str,
    control_values: Mapping[str, Any],
    registry=None,
) -> ConditionalOutputDefinition | Any | None:
    """Resolve one machine-checkable output rule from registry control values."""
    definition = _registry_definition(workflow_id, registry)
    capability = getattr(definition, "output_capability", None)
    rules = tuple(getattr(capability, "conditional_outputs", ()) or ())
    if not rules:
        return None
    controls = {getattr(item, "name", ""): item for item in get_controls(workflow_id, registry=registry)}
    values = {}
    for name, control in controls.items():
        argument = getattr(control, "executor_argument", None) or name
        value = control_values.get(name, control_values.get(argument, getattr(control, "default", None)))
        values[name] = value
    for rule in rules:
        if all(values.get(name) == expected for name, expected in rule.when.items()):
            return rule
    return None


def _artifact_input_field(artifact: ArtifactType, fields: set[str]) -> str | None:
    """Resolve an artifact to an explicitly registered file input field."""
    stem = artifact.removesuffix("_network")
    candidates = (
        f"{stem}_file",
        f"{artifact}_file",
        "network_file" if artifact == "regulatory_network" else "",
    )
    return next((field for field in candidates if field and field in fields), None)


def registered_handoff_consumers(
    producer_action: str,
    registry=None,
) -> tuple[HandoffConsumerDefinition, ...]:
    """Find consumers whose registered schema accepts the producer output.

    Compatibility requires both an artifact declaration and an explicit input
    granularity declaration. This is intentionally stricter than matching a
    workflow name or assuming that every co-expression matrix is interchangeable.
    """
    source = registry if registry is not None else ACTION_DEFINITIONS
    if hasattr(source, "workflows"):
        source = source.workflows
    producer = _registry_definition(producer_action, source)
    producer_capability = getattr(producer, "output_capability", None)
    if producer_capability is None:
        return ()
    artifacts = set(
        getattr(producer_capability, "produced_artifacts", ())
        or (getattr(producer_capability, "artifact_type", "unknown"),)
    )
    source_granularities = set(getattr(producer_capability, "granularities", ()) or ())
    consumers: list[HandoffConsumerDefinition] = []
    for action, candidate in source.items():
        if (
            action == producer_action
            or action not in RUN_ACTIONS
            or not getattr(candidate, "run", True)
        ):
            continue
        capability = getattr(candidate, "output_capability", None)
        if capability is None:
            continue
        accepted_granularities = set(
            getattr(capability, "accepted_input_granularities", ()) or ()
        )
        if not accepted_granularities or not source_granularities.intersection(
            accepted_granularities
        ):
            continue
        accepted_modalities = set(
            getattr(capability, "accepted_input_modalities", ()) or ()
        )
        if accepted_modalities and "coexpression" not in accepted_modalities:
            continue
        input_artifacts = set(getattr(capability, "input_artifacts", ()) or ())
        fields = set(getattr(candidate, "required_inputs", ()) or ()) | set(
            getattr(candidate, "optional_inputs", ()) or ()
        )
        for artifact in sorted(artifacts & input_artifacts):
            input_field = _artifact_input_field(artifact, fields)
            if input_field is None:
                continue
            prior_fields = tuple(
                field
                for field in getattr(candidate, "required_inputs", ())
                if field not in {"expression_file", "coexpression_file", "output_file", "output_dir"}
            )
            consumers.append(
                HandoffConsumerDefinition(
                    action=action,
                    workflow=getattr(candidate, "workflow", action),
                    input_field=input_field,
                    required_prior_inputs=prior_fields,
                    accepted_input_granularities=frozenset(accepted_granularities),
                )
            )
            break
    return tuple(consumers)


def workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    if definition is not None:
        return definition.workflow
    return (
        action.removeprefix("run_").removeprefix("inspect_").replace("_", "-").upper()
    )


def registered_actions_for_family(family: str) -> tuple[ActionName, ...]:
    """Return registered runnable actions for a declared method family."""
    return tuple(
        action
        for action, definition in ACTION_DEFINITIONS.items()
        if definition.run and definition.memory_metadata.get("method_family") == family
    )


def _is_text_input(decision: Any, field_name: str) -> bool:
    """Report whether the typed decision declares this input as text."""
    fields = getattr(type(decision), "model_fields", None)
    field = fields.get(field_name) if isinstance(fields, dict) else None
    return field is None or "str" in str(field.annotation)


def executor_arguments(action: ActionName, decision: Any) -> dict[str, Any]:
    """Build the allow-listed executor payload for one typed decision."""
    definition = ACTION_DEFINITIONS[action]
    controls = {
        (control.executor_argument or control.name): control
        for control in definition.controls
    }
    arguments = {}
    for field_name in definition.executor_fields:
        value = getattr(decision, field_name, None)
        control = controls.get(field_name)
        if value in (None, "") and control is not None and control.default is not None:
            value = control.default
        elif value in (None, "") and field_name in definition.executor_defaults:
            value = definition.executor_defaults[field_name]
        elif value is None and field_name in definition.optional_inputs:
            # Text adapters use an empty string to mean "optional input omitted",
            # because passing None leaks through their strict tool schema and turns
            # a valid plan preview into a ValidationError. A non-text optional is
            # declared `X | None` in the decision contract and its tool schema
            # rejects "", so it is omitted instead and inherits the adapter's own
            # meaning for an absent value, such as DRAGON estimating omitted
            # penalty parameters.
            if not _is_text_input(decision, field_name):
                continue
            value = ""
        arguments[field_name] = value
    return arguments
