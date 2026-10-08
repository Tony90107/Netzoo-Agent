# Blinded held-out sessions (part b)

## H106

> We have RNA-seq and genotypes from 50 heart samples. We want to detect genes with allele-specific expression and test whether the allelic imbalance differs between failing and healthy hearts.

- kind: UNSUPPORTED_CORE
- core: allele-specific expression or allelic imbalance
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
For “detect genes with allele-specific expression”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For “test whether the allelic imbalance differs between failing and healthy hearts”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## H107

> Using multi-region sequencing of each tumor, we want to reconstruct the phylogenetic tree of subclones and estimate when each driver mutation arose during tumor evolution.

- kind: UNSUPPORTED_CORE
- core: a phylogeny of tumor subclones
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "estimate when each driver mutation arose during tumor evolution": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H108

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H109

> We have shotgun metagenomic reads from 120 stool samples. We want species-level taxonomic profiles and to find which microbial species differ between patients with and without colitis.

- kind: UNSUPPORTED_CORE
- core: taxonomic profiles of gut microbiome samples
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "species-level taxonomic profiles" -- not matched to any registered workflow.
2. "which microbial species differ between patients with and without colitis" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H110

> We have methylation and expression for 100 patients, half responders. We want a two-layer methylation-expression network for each patient and to compare the networks between responders and non-responders.

- kind: SUPPORTED
- core: per-sample two-layer networks compared between groups
- accept: ['run_lioness_dragon']

Full reply:

```
For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 100 patients, 101 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare the networks between responders and non-responders."):
- **DRAGON** — Build one network per group on the same features of both layers, then compare the cross-layer edges (the partial correlations between the two omics layers) between the group networks; two aggregate networks show where the groups differ but give no per-sample spread to test it.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H111

> We have deep ATAC-seq of sorted B cells. We want base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition.

- kind: UNSUPPORTED_CORE
- core: base-resolution TF footprints from ATAC-seq
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user may also be interested in quantifying transcription factor activity in addition to identifying binding sites.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
```

## H112

> We have expression from 70 breast tumors with motif, protein interaction and microRNA target priors. We want a network of TF and microRNA regulation for every tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA regulatory network for each sample
- accept: ['run_lioness_puma']

Full reply:

```
For the sample-specific output you described, use **LIONESS-PUMA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - `mirna_file`: miRNA list

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PUMA** separately; **LIONESS-PUMA** also produces the aggregate output. Use **PUMA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 70 tumors, 71 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H113

> We only have mRNA expression for 200 kidney tumors and miRNA target predictions. We want to estimate how much each microRNA is expressed in each tumor.

- kind: UNSUPPORTED_CORE
- core: miRNA expression levels estimated from mRNA data
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "estimate how much each microRNA is expressed in each tumor" -- not available here: no registered workflow produces this. PUMA does not give it: the miRNA's own expression is not an input.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H114

> We have matched expression, DNA methylation and proteomics from 70 tumors. We want one joint network over all three layers that estimates their conditional dependencies simultaneously.

- kind: UNSUPPORTED_CORE
- core: one multi-omic network over three omics layers jointly
- nearest (may be offered only with the core stated as not produced): ['run_dragon', 'run_lioness_dragon']

Full reply:

```
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H115

> Our expression data come from three sequencing batches. We want to separate the part of gene-gene co-expression explained by batch from the rest, and keep an adjusted co-expression matrix.

- kind: SUPPORTED
- core: co-expression attributable to batch, and batch-adjusted co-expression
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H116

> We ran a genome-wide CRISPR knockout screen with guide counts before and after drug selection. We want to rank which genes, when lost, confer resistance, with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: hit genes from a CRISPR knockout screen
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "rank which genes, when lost, confer resistance" -- not matched to any registered workflow.
2. "with a false discovery rate" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H117

> We ran a genome-wide CRISPR knockout screen with guide counts before and after drug selection. We want to rank which genes, when lost, confer resistance, with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: hit genes from a CRISPR knockout screen
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "rank which genes, when lost, confer resistance" -- not matched to any registered workflow.
2. "with a false discovery rate" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H118

> We have methylation and expression for 100 patients, half responders. We want a two-layer methylation-expression network for each patient and to compare the networks between responders and non-responders.

- kind: SUPPORTED
- core: per-sample two-layer networks compared between groups
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer methylation-expression network for each patient" -- available from DRAGON or LIONESS-DRAGON.
2. "compare the networks between responders and non-responders" -- available from DRAGON or LIONESS-DRAGON's output plus a step you run outside NetZoo: One network per group on the same features, then compare; no per-sample spread for a test.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 100 patients, 101 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare the networks between responders and non-responders."):
- **DRAGON** — Build one network per group on the same features of both layers, then compare the cross-layer edges (the partial correlations between the two omics layers) between the group networks; two aggregate networks show where the groups differ but give no per-sample spread to test it.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H119

> We identified 2,000 tumor neoantigen peptides and want to predict their binding affinity to each patient's HLA class I alleles to prioritize vaccine candidates.

- kind: UNSUPPORTED_CORE
- core: peptide binding affinity to HLA alleles
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H120

> Using expression from 90 leukemia samples with motif and protein interaction priors, we want each TF's activity per sample, and then a machine-learning model that predicts relapse from those activities.

- kind: HALF
- core: a classifier predicting relapse from the activities
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "a machine-learning model that predicts relapse from those activities" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "a machine-learning model that predicts relapse from those activities": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H121

> We have RNA-seq and genotypes from 50 heart samples. We want to detect genes with allele-specific expression and test whether the allelic imbalance differs between failing and healthy hearts.

- kind: UNSUPPORTED_CORE
- core: allele-specific expression or allelic imbalance
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
For “detect genes with allele-specific expression”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For “test whether the allelic imbalance differs between failing and healthy hearts”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## H122

> We have single-cell RNA-seq from twelve donors processed on different days. We need to integrate them into one batch-corrected embedding so that the same cell types cluster together.

- kind: UNSUPPORTED_CORE
- core: integrated, batch-corrected single-cell embedding across donors
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "integrate them into one batch-corrected embedding" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
2. "the same cell types cluster together" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H123

> We have RNA-seq and genotypes from 50 heart samples. We want to detect genes with allele-specific expression and test whether the allelic imbalance differs between failing and healthy hearts.

- kind: UNSUPPORTED_CORE
- core: allele-specific expression or allelic imbalance
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H124

> We have RNA-seq from 150 glioma patients with survival data, plus motif and protein interaction priors. We want each patient's TF targeting scores and to test which are associated with survival.

- kind: SUPPORTED
- core: per-sample TF targeting scores related to survival
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "We want each patient's TF targeting scores and to test which are associated with survival." — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H125

> Using expression of 300 breast cancer patients with follow-up, we want to build a multigene risk score, fit a Cox model with hazard ratios, and validate it in an independent cohort.

- kind: UNSUPPORTED_CORE
- core: a hazard-ratio survival model with a risk score validated on new patients
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "build a multigene risk score": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- "build a multigene risk score"**
Result: regulatory networks, from inputs the request does not state.
- TF-only regulatory network:
  - **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
  - **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.
- TF-only signed regulatory-effect network:
  - **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.
- TF/miRNA regulatory network:
  - **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Reading 2 -- "validate it in an independent cohort"**
Result: validation reports, from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

## H126

> We have bulk expression from 40 patients and no prior knowledge of regulators. We want a separate gene co-expression network for each patient sample.

- kind: SUPPORTED
- core: a co-expression network for each individual sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "40 patients". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H127

> From our annotated single-cell atlas of the tumor microenvironment, we want to infer which ligand-receptor pairs mediate communication between macrophages and T cells. Which analysis fits?

- kind: UNSUPPORTED_CORE
- core: ligand-receptor cell-cell communication between cell types
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H128

> We have RNA-seq from 150 glioma patients with survival data, plus motif and protein interaction priors. We want each patient's TF targeting scores and to test which are associated with survival.

- kind: SUPPORTED
- core: per-sample TF targeting scores related to survival
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The RNA-seq data is suitable for inferring TF activity scores.
- Survival data is available for statistical testing.

Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** is related to that result and scale.

What you asked about:

- "test which are associated with survival" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H129

> We identified 2,000 tumor neoantigen peptides and want to predict their binding affinity to each patient's HLA class I alleles to prioritize vaccine candidates.

- kind: UNSUPPORTED_CORE
- core: peptide binding affinity to HLA alleles
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict their binding affinity to each patient's HLA class I alleles" -- not matched to any registered workflow.
2. "prioritize vaccine candidates" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H130

> We have expression from 70 breast tumors with motif, protein interaction and microRNA target priors. We want a network of TF and microRNA regulation for every tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA regulatory network for each sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network of TF and microRNA regulation for every tumor separately" -- available from LIONESS-PUMA.

For the sample-specific output you described, use **LIONESS-PUMA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - `mirna_file`: miRNA list

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PUMA** separately; **LIONESS-PUMA** also produces the aggregate output. Use **PUMA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 70 tumors, 71 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H131

> Using multi-region sequencing of each tumor, we want to reconstruct the phylogenetic tree of subclones and estimate when each driver mutation arose during tumor evolution.

- kind: UNSUPPORTED_CORE
- core: a phylogeny of tumor subclones
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H132

> We have whole-exome sequencing of 45 tumor-normal pairs. We need to call copy-number segments and find which chromosomal regions are recurrently amplified across the cohort. How should we proceed?

- kind: UNSUPPORTED_CORE
- core: copy-number segments and amplification calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call copy-number segments" -- not matched to any registered workflow.
2. "find which chromosomal regions are recurrently amplified across the cohort" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H133

> We have matched expression, DNA methylation and proteomics from 70 tumors. We want one joint network over all three layers that estimates their conditional dependencies simultaneously.

- kind: UNSUPPORTED_CORE
- core: one multi-omic network over three omics layers jointly
- nearest (may be offered only with the core stated as not produced): ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "one joint network over all three layers that estimates their conditional dependencies simultaneously" -- available from DRAGON.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H134

> We found communities in our TF-gene network and now want a p-value for each community saying whether its modularity is significantly higher than expected by chance.

- kind: UNSUPPORTED_CORE
- core: statistical significance (p-values) for each detected community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a p-value for each community saying whether its modularity is significantly higher than expected by chance" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H135

> We have whole-exome sequencing of 45 tumor-normal pairs. We need to call copy-number segments and find which chromosomal regions are recurrently amplified across the cohort. How should we proceed?

- kind: UNSUPPORTED_CORE
- core: copy-number segments and amplification calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H136

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call chromatin loops and topologically associating domain boundaries" -- not matched to any registered workflow.
2. "see which loops connect enhancers to their target promoters" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H137

> From our annotated single-cell atlas of the tumor microenvironment, we want to infer which ligand-receptor pairs mediate communication between macrophages and T cells. Which analysis fits?

- kind: UNSUPPORTED_CORE
- core: ligand-receptor cell-cell communication between cell types
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which ligand-receptor pairs mediate communication between macrophages and T cells" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
2. "Which analysis fits?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H138

> With expression from 120 liver samples plus motif and protein interaction priors, we want to know whether each transcription factor activates or represses each of its target genes.

- kind: SUPPORTED
- core: signed activating or repressing TF-gene effects
- accept: ['run_giraffe']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level signed regulatory-effect network. **GIRAFFE** fits that result and scale.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H139

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call chromatin loops and topologically associating domain boundaries" -- not matched to any registered workflow.
2. "see which loops connect enhancers to their target promoters" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H140

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call chromatin loops and topologically associating domain boundaries" -- not matched to any registered workflow.
2. "see which loops connect enhancers to their target promoters" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H141

> We have RNA-seq from 150 glioma patients with survival data, plus motif and protein interaction priors. We want each patient's TF targeting scores and to test which are associated with survival.

- kind: SUPPORTED
- core: per-sample TF targeting scores related to survival
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** is related to that result and scale.

What you asked about:

- "test which are associated with survival" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H142

> We want the overall gene co-expression network of our 55 muscle biopsies and also one co-expression network per biopsy derived from it.

- kind: SUPPORTED
- core: a sample-by-sample co-expression network plus the aggregate
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "the overall gene co-expression network of our 55 muscle biopsies" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network per biopsy derived from it" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per biopsy”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per biopsy”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H143

> We have mutation calls for 180 lung tumors. We want pathway-level mutation scores for each patient and a distance matrix between patients based on them.

- kind: SUPPORTED
- core: pathway mutation scores and patient distance matrix
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "pathway-level mutation scores for each patient" -- available from SAMBAR.
2. "a distance matrix between patients based on them" -- available from SAMBAR.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.
```

## H144

> Our single-nucleus data include spliced and unspliced counts. We want RNA velocity to infer the direction each cell is moving and predict its future transcriptional state.

- kind: UNSUPPORTED_CORE
- core: RNA velocity and future cell states
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict its future transcriptional state": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H145

> From our annotated single-cell atlas of the tumor microenvironment, we want to infer which ligand-receptor pairs mediate communication between macrophages and T cells. Which analysis fits?

- kind: UNSUPPORTED_CORE
- core: ligand-receptor cell-cell communication between cell types
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which ligand-receptor pairs mediate communication between macrophages and T cells" -- not matched to any registered workflow.
2. "Which analysis fits?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H146

> We sampled immune cells at twelve time points after vaccination. We want a time-lagged network in which a regulator's change at one time point predicts its targets' changes at the next.

- kind: UNSUPPORTED_CORE
- core: a time-lagged (Granger-type) directed regulatory network
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a time-lagged network in which a regulator's change at one time point predicts its targets' changes at the next." -- not available here: no registered workflow produces this. DRAGON does not give it: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H147

> We have shotgun metagenomic reads from 120 stool samples. We want species-level taxonomic profiles and to find which microbial species differ between patients with and without colitis.

- kind: UNSUPPORTED_CORE
- core: taxonomic profiles of gut microbiome samples
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H148

> We have bulk RNA-seq from 60 biopsies along disease progression. We want a co-expression network for each sample, and then to order the samples along a pseudotime of progression.

- kind: HALF
- core: pseudotime ordering of the samples
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

No files were inspected and no analysis ran.
```

## H149

> We have bulk expression from 40 patients and no prior knowledge of regulators. We want a separate gene co-expression network for each patient sample.

- kind: SUPPORTED
- core: a co-expression network for each individual sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a separate gene co-expression network for each patient sample" -- available from LIONESS-COEXPRESSION.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "40 patients". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H150

> We have expression from treated and control fibroblasts, plus motif and protein interaction priors. We want to see which transcription factors change how strongly they target genes between conditions.

- kind: SUPPORTED
- core: comparing regulator targeting between two conditions
- accept: ['run_panda', 'run_lioness_panda', 'run_otter']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors.

**GIRAFFE**: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.

Routing-level input modality: expression matrix.

Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix; interpret TF-gene regulatory weights as coefficients in a linear expression model; estimate positive activating and negative inhibitory partial regulatory effects; model gene expression with transcription factor activities as predictors.

GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

For your question ("which transcription factors change how strongly they target genes between conditions"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H151

> With lung expression data, a motif prior and a protein interaction network, we want one TF-gene network for the cohort and then to simulate how it would rewire after adding a drug.

- kind: HALF
- core: simulating the network after a drug perturbation
- accept: ['run_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene network for the cohort" -- available from PANDA or OTTER.
2. "simulate how it would rewire after adding a drug" -- not matched to any registered workflow.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

No files were inspected and no analysis ran.
```

## H152

> From our annotated single-cell atlas of the tumor microenvironment, we want to infer which ligand-receptor pairs mediate communication between macrophages and T cells. Which analysis fits?

- kind: UNSUPPORTED_CORE
- core: ligand-receptor cell-cell communication between cell types
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H153

> We ran a genome-wide CRISPR knockout screen with guide counts before and after drug selection. We want to rank which genes, when lost, confer resistance, with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: hit genes from a CRISPR knockout screen
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level gene mutation scores. **SAMBAR** fits that result and scale.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H154

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H155

> We have expression from 70 breast tumors with motif, protein interaction and microRNA target priors. We want a network of TF and microRNA regulation for every tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA regulatory network for each sample
- accept: ['run_lioness_puma']

Full reply:

```
For the sample-specific output you described, use **LIONESS-PUMA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - `mirna_file`: miRNA list

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PUMA** separately; **LIONESS-PUMA** also produces the aggregate output. Use **PUMA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 70 tumors, 71 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H156

> We have mutation calls for 180 lung tumors. We want pathway-level mutation scores for each patient and a distance matrix between patients based on them.

- kind: SUPPORTED
- core: pathway mutation scores and patient distance matrix
- accept: ['run_sambar']

Full reply:

```
**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.
```

## H157

> We have somatic mutations for 250 colorectal tumors. We want to subtype the patients by pathway mutation scores and then map where each subtype's cells sit within the tissue sections.

- kind: HALF
- core: spatial location of the subtypes in tissue sections
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "subtype the patients by pathway mutation scores" -- available from SAMBAR.
2. "map where each subtype's cells sit within the tissue sections" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H158

> We have deep ATAC-seq of sorted B cells. We want base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition.

- kind: UNSUPPORTED_CORE
- core: base-resolution TF footprints from ATAC-seq
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> Using expression from 90 leukemia samples with motif and protein interaction priors, we want each TF's activity per sample, and then a machine-learning model that predicts relapse from those activities.

- kind: HALF
- core: a classifier predicting relapse from the activities
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "a machine-learning model that predicts relapse from those activities" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "a machine-learning model that predicts relapse from those activities": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H160

> We have bulk expression from 40 patients and no prior knowledge of regulators. We want a separate gene co-expression network for each patient sample.

- kind: SUPPORTED
- core: a co-expression network for each individual sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "40 patients". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H161

> We have somatic mutations for 250 colorectal tumors. We want to subtype the patients by pathway mutation scores and then map where each subtype's cells sit within the tissue sections.

- kind: HALF
- core: spatial location of the subtypes in tissue sections
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H162

> From our expression data with motif and protein interaction priors, we want to predict each gene's protein abundance from the activity of the transcription factors that regulate it.

- kind: UNSUPPORTED_CORE
- core: a gene's protein abundance predicted from its regulators
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "predict each gene's protein abundance from the activity of the transcription factors that regulate it" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H163

> We have RNA-seq and genotypes from 50 heart samples. We want to detect genes with allele-specific expression and test whether the allelic imbalance differs between failing and healthy hearts.

- kind: UNSUPPORTED_CORE
- core: allele-specific expression or allelic imbalance
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H164

> We identified 2,000 tumor neoantigen peptides and want to predict their binding affinity to each patient's HLA class I alleles to prioritize vaccine candidates.

- kind: UNSUPPORTED_CORE
- core: peptide binding affinity to HLA alleles
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H165

> We already have a TF-gene network from kidney tissue. We want its communities and, within each community, a score saying which regulators and genes are most central to it.

- kind: SUPPORTED
- core: each node's core score within its community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a score saying which regulators and genes are most central to it" -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H166

> We have RNA-seq from 85 liver biopsies and a motif prior, but no protein interaction data. We want to infer the protein-protein interaction network itself from these samples.

- kind: UNSUPPORTED_CORE
- core: a PPI network inferred from the expression data
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_otter']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H167

> Using expression of 300 breast cancer patients with follow-up, we want to build a multigene risk score, fit a Cox model with hazard ratios, and validate it in an independent cohort.

- kind: UNSUPPORTED_CORE
- core: a hazard-ratio survival model with a risk score validated on new patients
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "we want to build a multigene risk score": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- "build a multigene risk score"**
Result: regulatory networks, from inputs the request does not state.
- TF-only regulatory network:
  - **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
  - **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.
- TF-only signed regulatory-effect network:
  - **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.
- TF/miRNA regulatory network:
  - **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Reading 2 -- "validate it in an independent cohort"**
Result: validation reports, from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

## H168

> We want the overall gene co-expression network of our 55 muscle biopsies and also one co-expression network per biopsy derived from it.

- kind: SUPPORTED
- core: a sample-by-sample co-expression network plus the aggregate
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "the overall gene co-expression network of our 55 muscle biopsies" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network per biopsy derived from it" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per biopsy”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per biopsy”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H169

> We have mutation calls for 180 lung tumors. We want pathway-level mutation scores for each patient and a distance matrix between patients based on them.

- kind: SUPPORTED
- core: pathway mutation scores and patient distance matrix
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "pathway-level mutation scores for each patient" -- available from SAMBAR.
2. "a distance matrix between patients based on them" -- available from SAMBAR.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.
```

## H170

> We have matched expression, DNA methylation and proteomics from 70 tumors. We want one joint network over all three layers that estimates their conditional dependencies simultaneously.

- kind: UNSUPPORTED_CORE
- core: one multi-omic network over three omics layers jointly
- nearest (may be offered only with the core stated as not produced): ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "one joint network over all three layers that estimates their conditional dependencies simultaneously" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- The user has the necessary data for expression, DNA methylation, and proteomics.
- The joint network will be inferred from the combined data of the three layers.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H171

> We have expression from 300 lung samples, a motif prior and a protein interaction network, and memory is tight. We want one TF-gene regulatory network for the whole cohort.

- kind: SUPPORTED
- core: a TF-gene network fitted to agree with PPI and co-expression
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

About your concern that memory is a limiting factor (for example, an earlier run ran out of memory):
- **OTTER** — `precision=single` keeps OTTER's largest array, the gene-by-gene co-expression matrix, in single precision during the optimization. The loader first computes that matrix in double precision, so peak memory while loading is not reduced, and the optimization and the output network stay in double precision.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression data from 300 lung samples is sufficient for inferring a regulatory network.
- The motif prior and protein interaction network will be utilized in the inference process.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H172

> We only have mRNA expression for 200 kidney tumors and miRNA target predictions. We want to estimate how much each microRNA is expressed in each tumor.

- kind: UNSUPPORTED_CORE
- core: miRNA expression levels estimated from mRNA data
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "estimate how much each microRNA is expressed in each tumor" -- not available here: no registered workflow produces this. PUMA does not give it: the miRNA's own expression is not an input.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H173

> We have whole-exome sequencing of 45 tumor-normal pairs. We need to call copy-number segments and find which chromosomal regions are recurrently amplified across the cohort. How should we proceed?

- kind: UNSUPPORTED_CORE
- core: copy-number segments and amplification calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H174

> We have RNA-seq from 85 liver biopsies and a motif prior, but no protein interaction data. We want to infer the protein-protein interaction network itself from these samples.

- kind: UNSUPPORTED_CORE
- core: a PPI network inferred from the expression data
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_otter']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The RNA-seq data provides sufficient information to infer protein interactions.
- The motif prior can guide the inference process.
- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H175

> We found communities in our TF-gene network and now want a p-value for each community saying whether its modularity is significantly higher than expected by chance.

- kind: UNSUPPORTED_CORE
- core: statistical significance (p-values) for each detected community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a p-value for each community saying whether its modularity is significantly higher than expected by chance" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H176

> We identified 2,000 tumor neoantigen peptides and want to predict their binding affinity to each patient's HLA class I alleles to prioritize vaccine candidates.

- kind: UNSUPPORTED_CORE
- core: peptide binding affinity to HLA alleles
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict their binding affinity to each patient's HLA class I alleles" -- not matched to any registered workflow.
2. "prioritize vaccine candidates" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H177

> We have bulk RNA-seq from 60 biopsies along disease progression. We want a co-expression network for each sample, and then to order the samples along a pseudotime of progression.

- kind: HALF
- core: pseudotime ordering of the samples
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

No files were inspected and no analysis ran.
```

## H178

> We have single-cell RNA-seq from twelve donors processed on different days. We need to integrate them into one batch-corrected embedding so that the same cell types cluster together.

- kind: UNSUPPORTED_CORE
- core: integrated, batch-corrected single-cell embedding across donors
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

## H179

> We have RNA-seq from 85 liver biopsies and a motif prior, but no protein interaction data. We want to infer the protein-protein interaction network itself from these samples.

- kind: UNSUPPORTED_CORE
- core: a PPI network inferred from the expression data
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_otter']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H180

> Our single-nucleus data include spliced and unspliced counts. We want RNA velocity to infer the direction each cell is moving and predict its future transcriptional state.

- kind: UNSUPPORTED_CORE
- core: RNA velocity and future cell states
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want RNA velocity to infer the direction each cell is moving" -- not matched to any registered workflow.
2. "predict its future transcriptional state" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H181

> We generated Hi-C contact maps from two cell lines and want to call chromatin loops and topologically associating domain boundaries, then see which loops connect enhancers to their target promoters.

- kind: UNSUPPORTED_CORE
- core: chromatin loops and TAD boundaries from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H182

> Using multi-region sequencing of each tumor, we want to reconstruct the phylogenetic tree of subclones and estimate when each driver mutation arose during tumor evolution.

- kind: UNSUPPORTED_CORE
- core: a phylogeny of tumor subclones
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "reconstruct the phylogenetic tree of subclones" -- not matched to any registered workflow.
2. "estimate when each driver mutation arose during tumor evolution" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H183

> We have shotgun metagenomic reads from 120 stool samples. We want species-level taxonomic profiles and to find which microbial species differ between patients with and without colitis.

- kind: UNSUPPORTED_CORE
- core: taxonomic profiles of gut microbiome samples
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "species-level taxonomic profiles" -- not matched to any registered workflow.
2. "which microbial species differ between patients with and without colitis" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H184

> We found communities in our TF-gene network and now want a p-value for each community saying whether its modularity is significantly higher than expected by chance.

- kind: UNSUPPORTED_CORE
- core: statistical significance (p-values) for each detected community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result.

**BONOBO** — Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H185

> From our expression data with motif and protein interaction priors, we want to predict each gene's protein abundance from the activity of the transcription factors that regulate it.

- kind: UNSUPPORTED_CORE
- core: a gene's protein abundance predicted from its regulators
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "predict each gene's protein abundance from the activity of the transcription factors that regulate it" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H186

> We have expression from treated and control fibroblasts, plus motif and protein interaction priors. We want to see which transcription factors change how strongly they target genes between conditions.

- kind: SUPPORTED
- core: comparing regulator targeting between two conditions
- accept: ['run_panda', 'run_lioness_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "which transcription factors change how strongly they target genes between conditions" -- available from PANDA, PUMA, LIONESS-PANDA or LIONESS-PUMA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors.

**GIRAFFE**: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.

Routing-level input modality: expression matrix.

Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix; interpret TF-gene regulatory weights as coefficients in a linear expression model; estimate positive activating and negative inhibitory partial regulatory effects; model gene expression with transcription factor activities as predictors.

GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

For your question ("which transcription factors change how strongly they target genes between conditions"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H187

> We have expression from 300 lung samples, a motif prior and a protein interaction network, and memory is tight. We want one TF-gene regulatory network for the whole cohort.

- kind: SUPPORTED
- core: a TF-gene network fitted to agree with PPI and co-expression
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

About your concern that memory is a limiting factor (for example, an earlier run ran out of memory):
- **OTTER** — `precision=single` keeps OTTER's largest array, the gene-by-gene co-expression matrix, in single precision during the optimization. The loader first computes that matrix in double precision, so peak memory while loading is not reduced, and the optimization and the output network stay in double precision.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H188

> We have somatic mutations for 250 colorectal tumors. We want to subtype the patients by pathway mutation scores and then map where each subtype's cells sit within the tissue sections.

- kind: HALF
- core: spatial location of the subtypes in tissue sections
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H189

> We have whole-exome sequencing of 45 tumor-normal pairs. We need to call copy-number segments and find which chromosomal regions are recurrently amplified across the cohort. How should we proceed?

- kind: UNSUPPORTED_CORE
- core: copy-number segments and amplification calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H190

> Our expression data come from three sequencing batches. We want to separate the part of gene-gene co-expression explained by batch from the rest, and keep an adjusted co-expression matrix.

- kind: SUPPORTED
- core: co-expression attributable to batch, and batch-adjusted co-expression
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H191

> We have whole-exome sequencing of 45 tumor-normal pairs. We need to call copy-number segments and find which chromosomal regions are recurrently amplified across the cohort. How should we proceed?

- kind: UNSUPPORTED_CORE
- core: copy-number segments and amplification calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call copy-number segments" -- not matched to any registered workflow.
2. "find which chromosomal regions are recurrently amplified across the cohort" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H192

> We have single-cell RNA-seq from twelve donors processed on different days. We need to integrate them into one batch-corrected embedding so that the same cell types cluster together.

- kind: UNSUPPORTED_CORE
- core: integrated, batch-corrected single-cell embedding across donors
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "integrate them into one batch-corrected embedding" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
2. "the same cell types cluster together" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H193

> We measured methylation and expression in the same 80 tumors. We want a partial-correlation network linking the two layers, and then to prove that its hub genes cause the aggressive phenotype.

- kind: HALF
- core: a proof that the hub genes cause the phenotype
- accept: ['run_dragon']

Full reply:

```
About "to prove that its hub genes cause the aggressive phenotype": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Assumptions behind this recommendation (not confirmed facts):

- The user has the necessary data for both methylation and expression measurements.
- The user is interested in a network that captures relationships across the entire cohort of tumors.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H194

> With expression from 120 liver samples plus motif and protein interaction priors, we want to know whether each transcription factor activates or represses each of its target genes.

- kind: SUPPORTED
- core: signed activating or repressing TF-gene effects
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "whether each transcription factor activates or represses each of its target genes" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H195

> We identified 2,000 tumor neoantigen peptides and want to predict their binding affinity to each patient's HLA class I alleles to prioritize vaccine candidates.

- kind: UNSUPPORTED_CORE
- core: peptide binding affinity to HLA alleles
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H196

> We have bulk RNA-seq from 60 biopsies along disease progression. We want a co-expression network for each sample, and then to order the samples along a pseudotime of progression.

- kind: HALF
- core: pseudotime ordering of the samples
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user has the necessary expression data for the 60 biopsies.
- The user is interested in analyzing gene interactions within each sample.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

No files were inspected and no analysis ran.
```

## H197

> We already have a TF-gene network from kidney tissue. We want its communities and, within each community, a score saying which regulators and genes are most central to it.

- kind: SUPPORTED
- core: each node's core score within its community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a score saying which regulators and genes are most central to it" -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H198

> We have deep ATAC-seq of sorted B cells. We want base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition.

- kind: UNSUPPORTED_CORE
- core: base-resolution TF footprints from ATAC-seq
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> Using multi-region sequencing of each tumor, we want to reconstruct the phylogenetic tree of subclones and estimate when each driver mutation arose during tumor evolution.

- kind: UNSUPPORTED_CORE
- core: a phylogeny of tumor subclones
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "estimate when each driver mutation arose during tumor evolution": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H200

> We have single-cell RNA-seq from twelve donors processed on different days. We need to integrate them into one batch-corrected embedding so that the same cell types cluster together.

- kind: UNSUPPORTED_CORE
- core: integrated, batch-corrected single-cell embedding across donors
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "integrate them into one batch-corrected embedding" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
2. "the same cell types cluster together" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H201

> With lung expression data, a motif prior and a protein interaction network, we want one TF-gene network for the cohort and then to simulate how it would rewire after adding a drug.

- kind: HALF
- core: simulating the network after a drug perturbation
- accept: ['run_panda', 'run_otter']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

No files were inspected and no analysis ran.
```

## H202

> We have expression from treated and control fibroblasts, plus motif and protein interaction priors. We want to see which transcription factors change how strongly they target genes between conditions.

- kind: SUPPORTED
- core: comparing regulator targeting between two conditions
- accept: ['run_panda', 'run_lioness_panda', 'run_otter']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors.

**GIRAFFE**: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.

Routing-level input modality: expression matrix.

Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix; interpret TF-gene regulatory weights as coefficients in a linear expression model; estimate positive activating and negative inhibitory partial regulatory effects; model gene expression with transcription factor activities as predictors.

GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

For your question ("which transcription factors change how strongly they target genes between conditions"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H203

> We have deep ATAC-seq of sorted B cells. We want base-resolution transcription factor footprints showing exactly which binding sites are occupied in each condition.

- kind: UNSUPPORTED_CORE
- core: base-resolution TF footprints from ATAC-seq
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will focus on transcription factors and their binding sites in B cells.
- The user has access to sorted B cell ATAC-seq data for multiple conditions.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
```

## H204

> Using expression from 90 leukemia samples with motif and protein interaction priors, we want each TF's activity per sample, and then a machine-learning model that predicts relapse from those activities.

- kind: HALF
- core: a classifier predicting relapse from the activities
- accept: ['run_giraffe']

Full reply:

```
About "a machine-learning model that predicts relapse from those activities": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** is related to that result and scale.

What you asked about:

- "a machine-learning model that predicts relapse from those activities" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H205

> We have methylation and expression for 100 patients, half responders. We want a two-layer methylation-expression network for each patient and to compare the networks between responders and non-responders.

- kind: SUPPORTED
- core: per-sample two-layer networks compared between groups
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer methylation-expression network for each patient" -- available from DRAGON or LIONESS-DRAGON.
2. "compare the networks between responders and non-responders" -- available from DRAGON or LIONESS-DRAGON's output plus a step you run outside NetZoo: One network per group on the same features, then compare; no per-sample spread for a test.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 100 patients, 101 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare the networks between responders and non-responders."):
- **DRAGON** — Build one network per group on the same features of both layers, then compare the cross-layer edges (the partial correlations between the two omics layers) between the group networks; two aggregate networks show where the groups differ but give no per-sample spread to test it.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H206

> We only have mRNA expression for 200 kidney tumors and miRNA target predictions. We want to estimate how much each microRNA is expressed in each tumor.

- kind: UNSUPPORTED_CORE
- core: miRNA expression levels estimated from mRNA data
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
**GIRAFFE** fits the result you describe, but it needs a motif prior and a PPI network, which you said you do not have.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

**What your data allows.** Your request names only a miRNA list. GIRAFFE needs a motif prior and a PPI network, which you said you do not have ("we only have mRNA expression for 200 kidney tumors").

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H207

> We have methylation and expression for 100 patients, half responders. We want a two-layer methylation-expression network for each patient and to compare the networks between responders and non-responders.

- kind: SUPPORTED
- core: per-sample two-layer networks compared between groups
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer methylation-expression network for each patient" -- available from DRAGON or LIONESS-DRAGON.
2. "compare the networks between responders and non-responders" -- available from DRAGON or LIONESS-DRAGON's output plus a step you run outside NetZoo: One network per group on the same features, then compare; no per-sample spread for a test.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 100 patients, 101 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare the networks between responders and non-responders."):
- **DRAGON** — Build one network per group on the same features of both layers, then compare the cross-layer edges (the partial correlations between the two omics layers) between the group networks; two aggregate networks show where the groups differ but give no per-sample spread to test it.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H208

> We ran a genome-wide CRISPR knockout screen with guide counts before and after drug selection. We want to rank which genes, when lost, confer resistance, with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: hit genes from a CRISPR knockout screen
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level gene mutation scores. **SAMBAR** fits that result and scale.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H209

> From our expression data with motif and protein interaction priors, we want to predict each gene's protein abundance from the activity of the transcription factors that regulate it.

- kind: UNSUPPORTED_CORE
- core: a gene's protein abundance predicted from its regulators
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
About "we want to predict each gene's protein abundance from the activity of the transcription factors that regulate it.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H210

> From our annotated single-cell atlas of the tumor microenvironment, we want to infer which ligand-receptor pairs mediate communication between macrophages and T cells. Which analysis fits?

- kind: UNSUPPORTED_CORE
- core: ligand-receptor cell-cell communication between cell types
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which ligand-receptor pairs mediate communication between macrophages and T cells" -- not matched to any registered workflow.
2. "Which analysis fits?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```
