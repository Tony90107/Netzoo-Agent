# Blinded held-out sessions (part b)

## H106

> We want a network showing which RNA-binding proteins regulate the stability of which mRNAs, using our expression data and CLIP-derived binding targets.

- kind: UNSUPPORTED_CORE
- core: a network of RNA-binding proteins regulating mRNA stability
- nearest (may be offered only with the core stated as not produced): ['run_puma']

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

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H107

> We have methylation array data from 500 blood donors. We want to estimate each donor's epigenetic age and their age acceleration relative to chronological age.

- kind: UNSUPPORTED_CORE
- core: an epigenetic age estimate from methylation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H108

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H109

> We are planning an RNA-seq study comparing two drug doses. How many biological replicates per group do we need to detect a two-fold change with 80 percent power?

- kind: UNSUPPORTED_CORE
- core: a sample-size or power calculation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "How many biological replicates per group do we need to detect a two-fold change with 80 percent power?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H110

> We have somatic mutation calls for 320 lung tumors with follow-up. We want pathway-based patient subtypes and to compare survival between them.

- kind: SUPPORTED
- core: mutation-based subtypes compared on survival
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compare survival between them" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H111

> In our TF-gene network we want a hierarchy of communities, where large modules split into nested sub-modules at several resolutions.

- kind: UNSUPPORTED_CORE
- core: a nested hierarchy of sub-communities
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
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

## H112

> We measured methylation and expression in the same 130 tumors. We want one network of direct associations between the two layers, with significance for each edge.

- kind: SUPPORTED
- core: a methylation-expression partial-correlation network with significance
- accept: ['run_dragon', 'run_lioness_dragon']

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

## H113

> With expression, motif and protein interaction priors for 60 patients, we want for every patient separately whether each TF activates or represses each target.

- kind: UNSUPPORTED_CORE
- core: a signed (activation/repression) network for each patient
- nearest (may be offered only with the core stated as not produced): ['run_giraffe', 'run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "for every patient separately whether each TF activates or represses each target" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H114

> From phosphoproteomics of 30 tumors, we want to infer which kinases regulate which phosphosites, building a kinase-substrate network.

- kind: UNSUPPORTED_CORE
- core: a kinase-substrate signaling network
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H115

> With expression of 100 sepsis patients plus motif and protein interaction priors, we want each TF's activity in each patient and to compare survivors with non-survivors.

- kind: SUPPORTED
- core: TF activity per sample compared between groups
- accept: ['run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H116

> We scanned 150 H&E slides of colon tumors. We want to segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically.

- kind: UNSUPPORTED_CORE
- core: segmented nuclei and cell counts from histology images
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H117

> We scanned 150 H&E slides of colon tumors. We want to segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically.

- kind: UNSUPPORTED_CORE
- core: segmented nuclei and cell counts from histology images
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H118

> We have somatic mutation calls for 320 lung tumors with follow-up. We want pathway-based patient subtypes and to compare survival between them.

- kind: SUPPORTED
- core: mutation-based subtypes compared on survival
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "pathway-based patient subtypes" -- available from SAMBAR.
2. "compare survival between them" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compare survival between them" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H119

> We sequenced T-cell receptor beta chains from 40 patients before and after immunotherapy. We want clonotype diversity and which clones expand after treatment.

- kind: UNSUPPORTED_CORE
- core: TCR clonotype diversity
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H120

> We have somatic mutations for 260 bladder tumors. We want patient subtypes from pathway mutation scores, and then a classifier that assigns new patients to those subtypes.

- kind: HALF
- core: predicting the subtype of new patients
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a classifier that assigns new patients to those subtypes" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "a classifier that assigns new patients to those subtypes": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H121

> We want a network showing which RNA-binding proteins regulate the stability of which mRNAs, using our expression data and CLIP-derived binding targets.

- kind: UNSUPPORTED_CORE
- core: a network of RNA-binding proteins regulating mRNA stability
- nearest (may be offered only with the core stated as not produced): ['run_puma']

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

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H122

> With genotypes and lung expression from 400 donors, we want to map cis-eQTLs genome-wide and report the lead variant for each gene.

- kind: UNSUPPORTED_CORE
- core: genome-wide eQTL mapping
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

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will utilize both genotype and expression data from the 400 donors.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H123

> We want a network showing which RNA-binding proteins regulate the stability of which mRNAs, using our expression data and CLIP-derived binding targets.

- kind: UNSUPPORTED_CORE
- core: a network of RNA-binding proteins regulating mRNA stability
- nearest (may be offered only with the core stated as not produced): ['run_puma']

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

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H124

> We have RNA-seq from 180 kidney biopsies, a TF motif prior and a protein interaction network. We want one regulatory network linking transcription factors to genes for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort from expression and priors
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

No files were inspected and no analysis ran.
```

## H125

> We have nanopore long-read genomes from 12 patients with a rare disease. We want to detect large structural variants such as inversions and translocations.

- kind: UNSUPPORTED_CORE
- core: structural variant calls from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to detect large structural variants such as inversions and translocations." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H126

> We have 60 tumor and 60 normal samples with motif and protein interaction priors. We want a TF-gene network for each sample and to compare tumor with normal.

- kind: SUPPORTED
- core: per-sample TF-gene networks compared between tumor and normal
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 tumor, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

For your question ("compare tumor with normal"):
- **PANDA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H127

> We ran data-dependent mass spectrometry on 24 plasma samples. We want to search the spectra against a protein database and report identified peptides with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: peptide and protein identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H128

> We have RNA-seq from 180 kidney biopsies, a TF motif prior and a protein interaction network. We want one regulatory network linking transcription factors to genes for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort from expression and priors
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

No files were inspected and no analysis ran.
```

## H129

> We sequenced T-cell receptor beta chains from 40 patients before and after immunotherapy. We want clonotype diversity and which clones expand after treatment.

- kind: UNSUPPORTED_CORE
- core: TCR clonotype diversity
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "clonotype diversity" -- not matched to any registered workflow.
2. "which clones expand after treatment" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H130

> We measured methylation and expression in the same 130 tumors. We want one network of direct associations between the two layers, with significance for each edge.

- kind: SUPPORTED
- core: a methylation-expression partial-correlation network with significance
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "one network of direct associations between the two layers, with significance for each edge." -- available from DRAGON.

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

## H131

> We have methylation array data from 500 blood donors. We want to estimate each donor's epigenetic age and their age acceleration relative to chronological age.

- kind: UNSUPPORTED_CORE
- core: an epigenetic age estimate from methylation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H132

> We just received FASTQ files for 36 mouse liver RNA-seq libraries. We need to quantify transcript abundance from the raw reads and build a count matrix for later analysis.

- kind: UNSUPPORTED_CORE
- core: transcript abundance quantified from raw reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "quantify transcript abundance from the raw reads" -- not matched to any registered workflow.
2. "build a count matrix for later analysis" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H133

> From phosphoproteomics of 30 tumors, we want to infer which kinases regulate which phosphosites, building a kinase-substrate network.

- kind: UNSUPPORTED_CORE
- core: a kinase-substrate signaling network
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "infer which kinases regulate which phosphosites, building a kinase-substrate network." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H134

> For 50 patients we have expression, methylation and proteomics. We want a separate partial-correlation network for each patient that links all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-sample network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate partial-correlation network for each patient that links all three layers" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H135

> We just received FASTQ files for 36 mouse liver RNA-seq libraries. We need to quantify transcript abundance from the raw reads and build a count matrix for later analysis.

- kind: UNSUPPORTED_CORE
- core: transcript abundance quantified from raw reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
The requested result is supported, but no compatible registered workflow matches the input availability you stated.

Which compatible input bundle can you provide?

No files were inspected and no analysis ran.
```

## H136

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "a Mendelian randomization estimate of whether IL-6 levels affect disease risk." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H137

> We ran data-dependent mass spectrometry on 24 plasma samples. We want to search the spectra against a protein database and report identified peptides with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: peptide and protein identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "search the spectra against a protein database and report identified peptides with a false discovery rate" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H138

> We already have a weighted TF-gene network from brain tissue. We want its communities and, for each community, the regulators that contribute most to it.

- kind: SUPPORTED
- core: communities and their core regulators
- accept: ['run_condor']

Full reply:

```
Selected path: **OTTER → CONDOR**.

**OTTER** — Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

Required workflow inputs:

- `motif_file`: motif/prior
- `ppi_file`: PPI network

Required alternative (provide one):

- `expression_file`: expression matrix
- `coexpression_file`: adjusted co-expression matrix

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Runtime limits:

- `computing`: current runtime unavailable: gpu; use `computing=cpu`.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

For your question ("for each community, the regulators that contribute most to it."):
- **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H139

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "a Mendelian randomization estimate of whether IL-6 levels affect disease risk" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H140

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "Mendelian randomization estimate of whether IL-6 levels affect disease risk" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H141

> We have RNA-seq from 180 kidney biopsies, a TF motif prior and a protein interaction network. We want one regulatory network linking transcription factors to genes for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort from expression and priors
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

No files were inspected and no analysis ran.
```

## H142

> Our server has little memory, but we need one TF-gene regulatory network for 400 samples using a motif prior and a protein interaction network. Which method fits?

- kind: SUPPORTED
- core: a low-memory cohort TF-gene network
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for 400 samples using a motif prior and a protein interaction network." -- available from PANDA.

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

## H143

> We want the overall gene co-expression network of our 66 kidney samples and also one co-expression network for each sample derived from it.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "overall gene co-expression network of our 66 kidney samples" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network for each sample derived from it" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network for each sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network for each sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H144

> We have matched ribosome profiling and RNA-seq from stressed and unstressed cells. We want each gene's translation efficiency and which genes change translation under stress.

- kind: UNSUPPORTED_CORE
- core: translation efficiency from ribosome profiling
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

For your question ("which genes change translation under stress"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
- **LIONESS-COEXPRESSION**, **BONOBO** — Comparing each sample's network with the rest of the cohort -- or, with repeated samples, with the same individual's other sample -- shows which individuals change or stand out.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing each sample's edges with the rest of the cohort -- or, with repeated samples, with the same individual's other sample -- shows which individuals change or stand out.
- **GIRAFFE** — The difference between an individual's activity profiles at the time points measures how much that individual's TF activity changed.
- **PANDA**, **PUMA**, **OTTER** — each gives one network from all the samples it is given. With one sample per individual (per time point), that says nothing about a single individual; a result for one individual needs many samples from that individual. Per-sample workflows for the same data: **LIONESS-PANDA**, **LIONESS-PUMA**.
- **COBRA** — gives the co-expression associated with each covariate across all the samples it is given. With one sample per individual (per time point), that says nothing about a single individual; a result for one individual needs many samples from that individual. Per-sample workflows for the same data: **LIONESS-COEXPRESSION**, **BONOBO**.
- **DRAGON** — gives one two-layer network from all the samples it is given. With one sample per individual (per time point), that says nothing about a single individual; a result for one individual needs many samples from that individual. Per-sample workflow for the same data: **LIONESS-DRAGON**.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H145

> We ran data-dependent mass spectrometry on 24 plasma samples. We want to search the spectra against a protein database and report identified peptides with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: peptide and protein identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "search the spectra against a protein database and report identified peptides with a false discovery rate" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H146

> We want a regulatory network in which chromatin-modifying enzymes, such as histone methyltransferases, are the regulators and their target genes are inferred from our expression data.

- kind: UNSUPPORTED_CORE
- core: a network where histone modifiers act as regulators
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network in which chromatin-modifying enzymes, such as histone methyltransferases, are the regulators and their target genes are inferred from our expression data" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H147

> We are planning an RNA-seq study comparing two drug doses. How many biological replicates per group do we need to detect a two-fold change with 80 percent power?

- kind: UNSUPPORTED_CORE
- core: a sample-size or power calculation
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

For your question ("detect a two-fold change with 80 percent power"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **LIONESS-COEXPRESSION**, **BONOBO** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
- **DRAGON** — Build one network per group on the same features of both layers, then compare the cross-layer edges (the partial correlations between the two omics layers) between the group networks; two aggregate networks show where the groups differ but give no per-sample spread to test it.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H148

> With expression, motif, protein interaction and miRNA target priors for 80 tumors, we want a TF and miRNA network per tumor, then to prove which miRNA causes metastasis.

- kind: HALF
- core: proving which miRNA causes the phenotype
- accept: ['run_lioness_puma']

Full reply:

```
About "to prove which miRNA causes metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## H149

> We have 60 tumor and 60 normal samples with motif and protein interaction priors. We want a TF-gene network for each sample and to compare tumor with normal.

- kind: SUPPORTED
- core: per-sample TF-gene networks compared between tumor and normal
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF-gene network for each sample" -- available from LIONESS-PANDA.
2. "to compare tumor with normal" -- available from PANDA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 tumor, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

For your question ("compare tumor with normal"):
- **PANDA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H150

> We have miRNA and mRNA expression from 90 patients with survival data. We want a two-layer network for each patient and to relate its edges to survival.

- kind: SUPPORTED
- core: per-patient two-layer networks related to survival
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 90 patients, 91 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

No files were inspected and no analysis ran.
```

## H151

> We have methylation and expression from 110 tumors. We want one network of direct associations between the two layers, and then to determine which layer is causally upstream.

- kind: HALF
- core: which layer is causally upstream
- accept: ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "one network of direct associations between the two layers" -- available from DRAGON.
2. "to determine which layer is causally upstream" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "to determine which layer is causally upstream": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H152

> We ran data-dependent mass spectrometry on 24 plasma samples. We want to search the spectra against a protein database and report identified peptides with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: peptide and protein identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H153

> We scanned 150 H&E slides of colon tumors. We want to segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically.

- kind: UNSUPPORTED_CORE
- core: segmented nuclei and cell counts from histology images
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H154

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H155

> We measured methylation and expression in the same 130 tumors. We want one network of direct associations between the two layers, with significance for each edge.

- kind: SUPPORTED
- core: a methylation-expression partial-correlation network with significance
- accept: ['run_dragon', 'run_lioness_dragon']

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

## H156

> We want the overall gene co-expression network of our 66 kidney samples and also one co-expression network for each sample derived from it.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network for each sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network for each sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H157

> We have a TF-gene network from liver. We want its communities, then to simulate what happens to each module if we remove its top hub regulator.

- kind: HALF
- core: simulating module collapse after removing a hub
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "to simulate what happens to each module if we remove its top hub regulator" -- not matched to any registered workflow.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H158

> In our TF-gene network we want a hierarchy of communities, where large modules split into nested sub-modules at several resolutions.

- kind: UNSUPPORTED_CORE
- core: a nested hierarchy of sub-communities
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a hierarchy of communities, where large modules split into nested sub-modules at several resolutions." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> We have somatic mutations for 260 bladder tumors. We want patient subtypes from pathway mutation scores, and then a classifier that assigns new patients to those subtypes.

- kind: HALF
- core: predicting the subtype of new patients
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "patient subtypes from pathway mutation scores" -- available from SAMBAR.
2. "a classifier that assigns new patients to those subtypes" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "a classifier that assigns new patients to those subtypes": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H160

> We have 60 tumor and 60 normal samples with motif and protein interaction priors. We want a TF-gene network for each sample and to compare tumor with normal.

- kind: SUPPORTED
- core: per-sample TF-gene networks compared between tumor and normal
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 tumor, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

For your question ("compare tumor with normal"):
- **PANDA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## H161

> We have a TF-gene network from liver. We want its communities, then to simulate what happens to each module if we remove its top hub regulator.

- kind: HALF
- core: simulating module collapse after removing a hub
- accept: ['run_condor']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is well-defined and available for analysis.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

What you asked about:

- "simulate what happens to each module if we remove its top hub regulator" — Core scores rank each node's contribution to its community's modularity; the top-scoring regulators and genes are candidates for the community's function. Gene communities can be tested for pathway enrichment with standard gene-set tools, which is a separate analysis step.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H162

> We built a regulatory network and now want a bootstrap confidence interval for every edge weight by resampling our 70 samples a thousand times.

- kind: UNSUPPORTED_CORE
- core: bootstrap confidence intervals for every edge
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a bootstrap confidence interval for every edge weight" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H163

> We want a network showing which RNA-binding proteins regulate the stability of which mRNAs, using our expression data and CLIP-derived binding targets.

- kind: UNSUPPORTED_CORE
- core: a network of RNA-binding proteins regulating mRNA stability
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "a network showing which RNA-binding proteins regulate the stability of which mRNAs" -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: co-expression is undirected gene-gene similarity, with no regulator layer.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H164

> We sequenced T-cell receptor beta chains from 40 patients before and after immunotherapy. We want clonotype diversity and which clones expand after treatment.

- kind: UNSUPPORTED_CORE
- core: TCR clonotype diversity
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H165

> We have expression for 52 patients and no prior data. We want a co-expression network for each patient, with a p-value for every edge so we can keep only confident ones.

- kind: SUPPORTED
- core: per-sample co-expression networks with edge p-values
- accept: ['run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "a co-expression network for each patient, with a p-value for every edge" -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "we want a co-expression network for each patient, with a p-value for every edge so we can keep only confident ones." — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Controls matching this request:

- `sparsify` (type=boolean; default=False)
- `bonobo_confidence` (type=number; default=0.05; range=0.0..1.0)
- `save_pvals` (type=boolean; default=False)

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H166

> From expression of 90 muscle samples, we want weighted gene co-expression modules and to correlate each module's eigengene with insulin resistance.

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network correlated with traits
- nearest (may be offered only with the core stated as not produced): ['run_condor', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## H167

> We have nanopore long-read genomes from 12 patients with a rare disease. We want to detect large structural variants such as inversions and translocations.

- kind: UNSUPPORTED_CORE
- core: structural variant calls from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H168

> Our server has little memory, but we need one TF-gene regulatory network for 400 samples using a motif prior and a protein interaction network. Which method fits?

- kind: SUPPORTED
- core: a low-memory cohort TF-gene network
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for 400 samples using a motif prior and a protein interaction network." -- available from PANDA.

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

## H169

> We want the overall gene co-expression network of our 66 kidney samples and also one co-expression network for each sample derived from it.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "overall gene co-expression network" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network for each sample" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network for each sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network for each sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H170

> From phosphoproteomics of 30 tumors, we want to infer which kinases regulate which phosphosites, building a kinase-substrate network.

- kind: UNSUPPORTED_CORE
- core: a kinase-substrate signaling network
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "we want to infer which kinases regulate which phosphosites, building a kinase-substrate network." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H171

> With expression from 140 thyroid samples, motif and protein interaction priors and microRNA target predictions, we want one network of how TFs and microRNAs regulate genes.

- kind: SUPPORTED
- core: a TF and miRNA regulatory network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one network of how TFs and microRNAs regulate genes" -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H172

> With expression, motif and protein interaction priors for 60 patients, we want for every patient separately whether each TF activates or represses each target.

- kind: UNSUPPORTED_CORE
- core: a signed (activation/repression) network for each patient
- nearest (may be offered only with the core stated as not produced): ['run_giraffe', 'run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "for every patient separately whether each TF activates or represses each target" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H173

> We just received FASTQ files for 36 mouse liver RNA-seq libraries. We need to quantify transcript abundance from the raw reads and build a count matrix for later analysis.

- kind: UNSUPPORTED_CORE
- core: transcript abundance quantified from raw reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
The requested result is supported, but no compatible registered workflow matches the input availability you stated.

Which compatible input bundle can you provide?

No files were inspected and no analysis ran.
```

## H174

> From expression of 90 muscle samples, we want weighted gene co-expression modules and to correlate each module's eigengene with insulin resistance.

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network correlated with traits
- nearest (may be offered only with the core stated as not produced): ['run_condor', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## H175

> For 50 patients we have expression, methylation and proteomics. We want a separate partial-correlation network for each patient that links all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-sample network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate partial-correlation network for each patient that links all three layers" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H176

> We sequenced T-cell receptor beta chains from 40 patients before and after immunotherapy. We want clonotype diversity and which clones expand after treatment.

- kind: UNSUPPORTED_CORE
- core: TCR clonotype diversity
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "clonotype diversity" -- not matched to any registered workflow.
2. "which clones expand after treatment" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H177

> With expression, motif, protein interaction and miRNA target priors for 80 tumors, we want a TF and miRNA network per tumor, then to prove which miRNA causes metastasis.

- kind: HALF
- core: proving which miRNA causes the phenotype
- accept: ['run_lioness_puma']

Full reply:

```
About "to prove which miRNA causes metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 80 tumors, 81 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H178

> With genotypes and lung expression from 400 donors, we want to map cis-eQTLs genome-wide and report the lead variant for each gene.

- kind: UNSUPPORTED_CORE
- core: genome-wide eQTL mapping
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

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H179

> From expression of 90 muscle samples, we want weighted gene co-expression modules and to correlate each module's eigengene with insulin resistance.

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network correlated with traits
- nearest (may be offered only with the core stated as not produced): ['run_condor', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will be based on the expression data from the 90 muscle samples.
- The eigengenes of the identified modules will be correlated with a measure of insulin resistance.

Which result do you mean: inferred gene-to-gene associations, one cohort-wide result (LIONESS-COEXPRESSION or COBRA); or p-value matrix paired with a sample-specific gene-gene co-expression result (BONOBO)?

No files were inspected and no analysis ran.
```

## H180

> We have matched ribosome profiling and RNA-seq from stressed and unstressed cells. We want each gene's translation efficiency and which genes change translation under stress.

- kind: UNSUPPORTED_CORE
- core: translation efficiency from ribosome profiling
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "each gene's translation efficiency" -- not matched to any registered workflow.
2. "which genes change translation under stress" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H181

> Using GWAS summary statistics for circulating IL-6 and for coronary disease, we want a Mendelian randomization estimate of whether IL-6 levels affect disease risk.

- kind: UNSUPPORTED_CORE
- core: a Mendelian randomization estimate of a causal effect
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H182

> We have methylation array data from 500 blood donors. We want to estimate each donor's epigenetic age and their age acceleration relative to chronological age.

- kind: UNSUPPORTED_CORE
- core: an epigenetic age estimate from methylation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate each donor's epigenetic age" -- not matched to any registered workflow.
2. "their age acceleration relative to chronological age" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H183

> We are planning an RNA-seq study comparing two drug doses. How many biological replicates per group do we need to detect a two-fold change with 80 percent power?

- kind: UNSUPPORTED_CORE
- core: a sample-size or power calculation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "How many biological replicates per group do we need to detect a two-fold change with 80 percent power?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H184

> For 50 patients we have expression, methylation and proteomics. We want a separate partial-correlation network for each patient that links all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-sample network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 50 patients, 51 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H185

> We built a regulatory network and now want a bootstrap confidence interval for every edge weight by resampling our 70 samples a thousand times.

- kind: UNSUPPORTED_CORE
- core: bootstrap confidence intervals for every edge
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_dragon']

Full reply:

```
What I understood you are asking for:
1. "bootstrap confidence interval for every edge weight" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H186

> We have miRNA and mRNA expression from 90 patients with survival data. We want a two-layer network for each patient and to relate its edges to survival.

- kind: SUPPORTED
- core: per-patient two-layer networks related to survival
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network for each patient" -- available from LIONESS-DRAGON.
2. "to relate its edges to survival" -- available from LIONESS-DRAGON's output plus a step you run outside NetZoo: A statistical test outside NetZoo.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 90 patients, 91 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

No files were inspected and no analysis ran.
```

## H187

> With expression from 140 thyroid samples, motif and protein interaction priors and microRNA target predictions, we want one network of how TFs and microRNAs regulate genes.

- kind: SUPPORTED
- core: a TF and miRNA regulatory network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one network of how TFs and microRNAs regulate genes" -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H188

> We have a TF-gene network from liver. We want its communities, then to simulate what happens to each module if we remove its top hub regulator.

- kind: HALF
- core: simulating module collapse after removing a hub
- accept: ['run_condor']

Full reply:

```
Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

What you asked about:

- "simulate what happens to each module if we remove its top hub regulator" — Core scores rank each node's contribution to its community's modularity; the top-scoring regulators and genes are candidates for the community's function. Gene communities can be tested for pathway enrichment with standard gene-set tools, which is a separate analysis step.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H189

> We just received FASTQ files for 36 mouse liver RNA-seq libraries. We need to quantify transcript abundance from the raw reads and build a count matrix for later analysis.

- kind: UNSUPPORTED_CORE
- core: transcript abundance quantified from raw reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
The requested result is supported, but no compatible registered workflow matches the input availability you stated.

Which compatible input bundle can you provide?

No files were inspected and no analysis ran.
```

## H190

> With expression of 100 sepsis patients plus motif and protein interaction priors, we want each TF's activity in each patient and to compare survivors with non-survivors.

- kind: SUPPORTED
- core: TF activity per sample compared between groups
- accept: ['run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The expression data for 100 sepsis patients is available and suitable for analysis.
- The comparison between survivors and non-survivors is based on the TF activity data.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "to compare survivors with non-survivors" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

## H191

> We just received FASTQ files for 36 mouse liver RNA-seq libraries. We need to quantify transcript abundance from the raw reads and build a count matrix for later analysis.

- kind: UNSUPPORTED_CORE
- core: transcript abundance quantified from raw reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "quantify transcript abundance from the raw reads" -- not matched to any registered workflow.
2. "build a count matrix for later analysis" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H192

> With genotypes and lung expression from 400 donors, we want to map cis-eQTLs genome-wide and report the lead variant for each gene.

- kind: UNSUPPORTED_CORE
- core: genome-wide eQTL mapping
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "map cis-eQTLs genome-wide" -- not matched to any registered workflow.
2. "report the lead variant for each gene" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H193

> We have bulk expression from 45 synovial biopsies. We want a co-expression network for each biopsy and also each biopsy's estimated cell-type composition.

- kind: HALF
- core: each sample's cell-type composition
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “co-expression network for each biopsy”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “co-expression network for each biopsy”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

For “each biopsy's estimated cell-type composition”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H194

> We already have a weighted TF-gene network from brain tissue. We want its communities and, for each community, the regulators that contribute most to it.

- kind: SUPPORTED
- core: communities and their core regulators
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "for each community, the regulators that contribute most to it" -- available from CONDOR.

Selected path: **OTTER → CONDOR**.

**OTTER** — Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

Required workflow inputs:

- `motif_file`: motif/prior
- `ppi_file`: PPI network

Required alternative (provide one):

- `expression_file`: expression matrix
- `coexpression_file`: adjusted co-expression matrix

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Runtime limits:

- `computing`: current runtime unavailable: gpu; use `computing=cpu`.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

For your question ("for each community, the regulators that contribute most to it."):
- **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H195

> We sequenced T-cell receptor beta chains from 40 patients before and after immunotherapy. We want clonotype diversity and which clones expand after treatment.

- kind: UNSUPPORTED_CORE
- core: TCR clonotype diversity
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H196

> With expression, motif, protein interaction and miRNA target priors for 80 tumors, we want a TF and miRNA network per tumor, then to prove which miRNA causes metastasis.

- kind: HALF
- core: proving which miRNA causes the phenotype
- accept: ['run_lioness_puma']

Full reply:

```
About "to prove which miRNA causes metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## H197

> We have expression for 52 patients and no prior data. We want a co-expression network for each patient, with a p-value for every edge so we can keep only confident ones.

- kind: SUPPORTED
- core: per-sample co-expression networks with edge p-values
- accept: ['run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "We want a co-expression network for each patient, with a p-value for every edge so we can keep only confident ones." -- available from BONOBO.

Based on what you said — "with a p-value for every edge so we can keep only confident ones." — **BONOBO** fits better: a confidence value (p-value) is needed for each connection in each sample.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale.

**BONOBO** (recommend) — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable. Needs expression matrix. Produces inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result (one result per sample).

Conditional assumptions to confirm:
- It also needs an expression matrix, which the request does not mention.

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use BONOBO, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## H198

> In our TF-gene network we want a hierarchy of communities, where large modules split into nested sub-modules at several resolutions.

- kind: UNSUPPORTED_CORE
- core: a nested hierarchy of sub-communities
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "we want a hierarchy of communities, where large modules split into nested sub-modules at several resolutions." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> We have methylation array data from 500 blood donors. We want to estimate each donor's epigenetic age and their age acceleration relative to chronological age.

- kind: UNSUPPORTED_CORE
- core: an epigenetic age estimate from methylation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H200

> With genotypes and lung expression from 400 donors, we want to map cis-eQTLs genome-wide and report the lead variant for each gene.

- kind: UNSUPPORTED_CORE
- core: genome-wide eQTL mapping
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

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will utilize genotype and expression data from the specified cohort of donors.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H201

> We have methylation and expression from 110 tumors. We want one network of direct associations between the two layers, and then to determine which layer is causally upstream.

- kind: HALF
- core: which layer is causally upstream
- accept: ['run_dragon']

Full reply:

```
About "to determine which layer is causally upstream.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H202

> We have miRNA and mRNA expression from 90 patients with survival data. We want a two-layer network for each patient and to relate its edges to survival.

- kind: SUPPORTED
- core: per-patient two-layer networks related to survival
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 90 patients, 91 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

No files were inspected and no analysis ran.
```

## H203

> In our TF-gene network we want a hierarchy of communities, where large modules split into nested sub-modules at several resolutions.

- kind: UNSUPPORTED_CORE
- core: a nested hierarchy of sub-communities
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
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

## H204

> We have somatic mutations for 260 bladder tumors. We want patient subtypes from pathway mutation scores, and then a classifier that assigns new patients to those subtypes.

- kind: HALF
- core: predicting the subtype of new patients
- accept: ['run_sambar']

Full reply:

```
About "a classifier that assigns new patients to those subtypes": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H205

> We have somatic mutation calls for 320 lung tumors with follow-up. We want pathway-based patient subtypes and to compare survival between them.

- kind: SUPPORTED
- core: mutation-based subtypes compared on survival
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "pathway-based patient subtypes" -- available from SAMBAR.
2. "compare survival between them" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compare survival between them" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H206

> With expression, motif and protein interaction priors for 60 patients, we want for every patient separately whether each TF activates or represses each target.

- kind: UNSUPPORTED_CORE
- core: a signed (activation/repression) network for each patient
- nearest (may be offered only with the core stated as not produced): ['run_giraffe', 'run_lioness_panda']

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

## H207

> We have somatic mutation calls for 320 lung tumors with follow-up. We want pathway-based patient subtypes and to compare survival between them.

- kind: SUPPORTED
- core: mutation-based subtypes compared on survival
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "pathway-based patient subtypes" -- available from SAMBAR.
2. "compare survival between them" -- available from SAMBAR's output plus a step you run outside NetZoo: A test outside NetZoo with a clinical table keyed by sample ID.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compare survival between them" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H208

> We scanned 150 H&E slides of colon tumors. We want to segment every nucleus and count tumor-infiltrating lymphocytes per slide automatically.

- kind: UNSUPPORTED_CORE
- core: segmented nuclei and cell counts from histology images
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H209

> We built a regulatory network and now want a bootstrap confidence interval for every edge weight by resampling our 70 samples a thousand times.

- kind: UNSUPPORTED_CORE
- core: bootstrap confidence intervals for every edge
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_dragon']

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

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H210

> We ran data-dependent mass spectrometry on 24 plasma samples. We want to search the spectra against a protein database and report identified peptides with a false discovery rate.

- kind: UNSUPPORTED_CORE
- core: peptide and protein identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "search the spectra against a protein database and report identified peptides with a false discovery rate" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```
