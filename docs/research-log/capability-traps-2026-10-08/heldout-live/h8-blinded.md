# Blinded held-out sessions for labelling

## H001

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network in which both TFs and miRNAs regulate genes?" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix. LIONESS-PUMA and PUMA need a motif prior and a PPI network, which you said you do not have ("We have mRNA and miRNA profiles from 60 patients.").

No files were inspected and no analysis ran.
```

## H002

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

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

## H003

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H004

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method infers one TF-gene regulatory network for the whole cohort?" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H005

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H006

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H007

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H008

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "each patient their own network of direct links between methylation and expression" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H009

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "Which method infers a regulatory network for each spot that borrows information from the neighboring spots?" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H010

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

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

## H011

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "turns them into pathway scores to subtype the patients" -- available from SAMBAR.
2. "predicts neoantigens from the mutations" -- not matched to any registered workflow.

About "Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H012

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H013

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that imputes the missing methylation values and then links the two layers in one network?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H014

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will utilize expression data, motifs, and PPI from the muscle biopsies.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H015

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that builds one network linking all three layers jointly?" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H016

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H017

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "splits it into communities of TFs and genes and scores how central each node is within its community" -- available from CONDOR.

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

## H018

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "estimates direct conditional links between the two data types rather than plain correlations" -- available from DRAGON.

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

## H019

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## H020

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H021

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

No files were inspected and no analysis ran.
```

## H022

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "estimates time-lagged effects of the earlier methylation on the later expression" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H023

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H024

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H025

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "estimates direct conditional links between the two data types rather than plain correlations" -- available from DRAGON.

It sounds like you want aggregate omics_layer_1_feature/omics_layer_2_feature multi omic network.

Registered method and input/output fit:
- **Multi omic network — DRAGON**
  - Registered purpose: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.
  - Method premise: infer conditional associations using partial correlation; DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
  - Mathematical interpretation: DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.
  - Required inputs: all of: DRAGON omics layer 1, DRAGON omics layer 2.
  - Declared output: multi omic network (cohort-level aggregate).

Unconfirmed assumptions in my current interpretation (please correct me if needed):
- The user is interested in understanding the interactions between metabolites and microbial genes.

The only registered workflow compatible with this request is **DRAGON**, but your request does not settle the kind of result or whether one cohort-wide result or one result per sample is wanted. Is DRAGON the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H026

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H027

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "turns them into pathway scores to subtype the patients" -- available from SAMBAR.
2. "predicts neoantigens from the mutations" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predicts neoantigens from the mutations": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H028

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H029

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
Fallback recommendation: **CONDOR**. The request was interpreted and a candidate was found, but at least one quote supporting that reading could not be located in your text -- often a spelling or rephrasing difference, sometimes a detail the reading added. So this is shown as a candidate rather than a verified match, and nothing will run from it. Please check that the reading matches what you meant.

Your question asks for a cohort-level community assignment. **CONDOR** is related to that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H030

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H031

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H032

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H033

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?" -- not matched to any registered workflow.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H034

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "brings predicted miRNA binding sites into regulatory network inference alongside TF motifs" -- available from PUMA.

Based on what you said — "Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?" — **PUMA** fits better: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** (recommend) — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior, PPI network and miRNA list. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- This reads the molecules you describe as miRNAs. Confirm that, and that you have a miRNA-target prior and a list of the miRNAs, before analysis.
- It also needs an expression matrix and TF-motif prior and protein-interaction prior and miRNA list, which the request does not mention.

Other compatible option(s):
- **DRAGON** — approach: infer conditional associations using partial correlation.

Should I use PUMA, or does another listed option fit your study better?

**Data your question needs.** Your question needs a motif prior, a PPI network and a miRNA list, which your request does not mention. Do you have a motif prior, a PPI network and a miRNA list?

No files were inspected and no analysis ran.
```

## H035

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds its communities and then renders them as an interactive 3D visualization?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H036

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
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

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H037

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
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

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H038

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user has access to the necessary expression data for each sample.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H039

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "proves the causal effect of each TF on each of its targets" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H040

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?" -- available from GIRAFFE.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H041

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "predicts neoantigens from the mutations" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H042

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
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

## H043

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H044

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "each patient their own network of direct links between methylation and expression" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H045

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

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

## H046

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
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

## H047

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "Which method gives a separate gene regulatory network for each individual cell?" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H048

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## H049

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that builds one network linking all three layers jointly?" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H050

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H051

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?" -- available from PUMA.

**PUMA** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H052

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs" -- available from PUMA.

**PUMA** fits the result you describe, but it needs a motif prior and a PPI network, which you said you do not have.

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

**What your data allows.** Your request names only a miRNA list. PUMA needs a motif prior and a PPI network, which you said you do not have ("We have miRNA and mRNA expression from 80 samples."). With a miRNA list alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H053

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H054

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that imputes the missing methylation values and then links the two layers in one network?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H055

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

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

## H056

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "estimates direct conditional links between the two data types rather than plain correlations" -- available from DRAGON.

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

## H057

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network in which both TFs and miRNAs regulate genes?" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix. LIONESS-PUMA and PUMA need a motif prior and a PPI network, which you said you do not have ("We have mRNA and miRNA profiles from 60 patients.").

No files were inspected and no analysis ran.
```

## H058

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds its communities and then renders them as an interactive 3D visualization?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H059

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?" -- available from GIRAFFE.

Assumptions behind this recommendation (not confirmed facts):

- The user has access to expression data, motifs, and PPI data from the muscle biopsies.
- The analysis aims to determine the regulatory effects of TFs on target genes.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H060

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that partitions this co-expression network into gene modules?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H061

> We have expression from 200 breast tumors plus motif and PPI data. Which method infers one TF-gene regulatory network for the whole cohort?

- kind: SUPPORTED
- core: one TF-gene network for the whole cohort
- accept: ['run_panda', 'run_otter', 'run_giraffe', 'run_puma']

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

## H062

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds communities in it where one gene can belong to several communities at once?" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The user has a TF-gene network for analysis.

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

## H063

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## H064

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H065

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will utilize expression data, motifs, and PPI from the muscle biopsies.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H066

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
About "a method that proves the causal effect of each TF on each of its targets": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H067

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H068

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H069

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H070

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H071

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H072

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H073

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that builds one network linking all three layers jointly?" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H074

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each tumor its own TF-gene network so we can compare networks between patients?" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H075

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?" -- available from PUMA or LIONESS-PUMA.

**PUMA** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H076

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each tumor its own TF-gene network so we can compare networks between patients?" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H077

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
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

## H078

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?" -- available from LIONESS-PUMA.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H079

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that removes the effects of these covariates from the co-expression before network inference?" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H080

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that imputes the missing methylation values and then links the two layers in one network?" -- available from DRAGON.

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

## H081

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## H082

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H083

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "Is there a method that fine-maps each locus into a credible set of likely causal variants?" -- not available here: no registered workflow produces this. CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H084

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H085

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H086

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor" -- available from LIONESS-PANDA.
2. "predicts each patient's drug response from those networks" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predicts each patient's drug response from those networks": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

Unconfirmed assumptions in my current interpretation (please correct me if needed):
- The user has access to RNA-seq data and motif and PPI data for the tumors.
- The method should allow for individual tumor analysis.
- The user is looking for a method that connects the TF-gene networks to drug response predictions.

The only registered workflow compatible with this request is **LIONESS-PANDA**, but your request does not settle the kind of result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H087

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will utilize expression data from the muscle biopsies to infer regulatory relationships.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H088

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H089

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H090

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H091

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor" -- available from LIONESS-PANDA.
2. "predicts each patient's drug response from those networks" -- not matched to any registered workflow.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but your request does not settle the kind of result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H092

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
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

## H093

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H094

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

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

## H095

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H096

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user has access to the necessary expression data for each sample.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H097

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "estimates how active each TF is in each sample, beyond what its own mRNA level says" -- available from GIRAFFE.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H098

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "Which method gives a separate gene regulatory network for each individual cell?" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H099

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H100

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H101

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H102

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
About "Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

For “predicts neoantigens from the mutations”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

To use subtypes for chemotherapy resistance or another clinical outcome, you would also need outcome labels matched to the patients. Check cluster stability and confounding, then evaluate prediction on held-out patients. Fit feature selection and cohort-dependent network estimation within the training split to avoid information leakage.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## H103

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H104

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

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

## H105

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "each tumor its own TF-gene network" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

No files were inspected and no analysis ran.
```

## H106

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H107

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H108

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H109

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H110

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "each patient their own network of direct links between methylation and expression" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H111

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
About "a method that proves the causal effect of each TF on each of its targets": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H112

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H113

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?" -- available from LIONESS-PUMA.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H114

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## H115

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
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

## H116

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H117

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "fine-maps each locus into a credible set of likely causal variants" -- not available here: no registered workflow produces this. CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H118

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network of direct links between methylation and expression?" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H119

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H120

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor" -- available from LIONESS-PANDA or LIONESS-PUMA.
2. "predicts each patient's drug response from those networks" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predicts each patient's drug response from those networks": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but your request does not settle the kind of result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H121

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H122

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?" -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H123

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H124

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
**PUMA** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H125

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H126

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix. LIONESS-PUMA and PUMA need a motif prior and a PPI network, which you said you do not have ("We have mRNA and miRNA profiles from 60 patients.").

No files were inspected and no analysis ran.
```

## H127

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H128

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
**PUMA** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H129

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H130

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H131

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "a separate gene regulatory network for each individual cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H132

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?" -- not matched to any registered workflow.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H133

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that partitions this co-expression network into gene modules?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H134

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds communities in it where one gene can belong to several communities at once?" -- available from CONDOR.

Fallback recommendation: **CONDOR**. The request was interpreted and a candidate was found, but at least one quote supporting that reading could not be located in your text -- often a spelling or rephrasing difference, sometimes a detail the reading added. So this is shown as a candidate rather than a verified match, and nothing will run from it. Please check that the reading matches what you meant.

Your question asks for a cohort-level community assignment. **CONDOR** is related to that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H135

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H136

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H137

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H138

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

No files were inspected and no analysis ran.
```

## H139

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H140

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H141

> In our liver regeneration study we sequenced small RNA and mRNA. Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?

- kind: SUPPORTED
- core: a network that adds predicted miRNA binding sites to TF motifs
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Based on what you said — "Is there a method that brings predicted miRNA binding sites into regulatory network inference alongside TF motifs?" — **PUMA** fits better: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

**PUMA** (recommend) — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior, PPI network and miRNA list. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- This reads the molecules you describe as miRNAs. Confirm that, and that you have a miRNA-target prior and a list of the miRNAs, before analysis.
- It also needs an expression matrix and TF-motif prior and protein-interaction prior and miRNA list, which the request does not mention.

Other compatible option(s):
- **DRAGON** — approach: infer conditional associations using partial correlation.

Should I use PUMA, or does another listed option fit your study better?

**Data your question needs.** Your question needs a motif prior, a PPI network and a miRNA list, which your request does not mention. Do you have a motif prior, a PPI network and a miRNA list?

No files were inspected and no analysis ran.
```

## H142

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H143

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H144

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H145

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H146

> We have miRNA and mRNA from 60 samples. Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?

- kind: UNSUPPORTED_CORE
- core: a sign on every miRNA-target edge
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that says, for every miRNA-target edge, whether the miRNA represses or activates that target?" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H147

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H148

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
**PUMA** fits the result you describe, but it needs a motif prior and a PPI network, which you said you do not have.

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

**What your data allows.** Your request names only a miRNA list. PUMA needs a motif prior and a PPI network, which you said you do not have ("We have miRNA and mRNA expression from 80 samples."). With a miRNA list alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H149

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network in which both TFs and miRNAs regulate genes?" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix. LIONESS-PUMA and PUMA need a motif prior and a PPI network, which you said you do not have ("We have mRNA and miRNA profiles from 60 patients.").

No files were inspected and no analysis ran.
```

## H150

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
```

## H151

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
About "Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H152

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H153

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H154

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H155

> We have binary mutation calls for 400 tumors. Is there a method that aggregates them into pathway scores and clusters the patients into subtypes?

- kind: SUPPORTED
- core: pathway scores from mutations and patient subtypes
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H156

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H157

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds its communities and then renders them as an interactive 3D visualization?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H158

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that proves the causal effect of each TF on each of its targets?" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor" -- available from LIONESS-PANDA or LIONESS-PUMA.
2. "predicts each patient's drug response from those networks" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predicts each patient's drug response from those networks": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but your request does not settle the kind of result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H160

> We have mRNA and miRNA profiles from 60 patients. Which method gives each patient their own network in which both TFs and miRNAs regulate genes?

- kind: SUPPORTED
- core: a per-patient network where TFs and miRNAs both regulate genes
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "each patient their own network in which both TFs and miRNAs regulate genes" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 60 patients, 61 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix. LIONESS-PUMA and PUMA need a motif prior and a PPI network, which you said you do not have ("We have mRNA and miRNA profiles from 60 patients.").

No files were inspected and no analysis ran.
```

## H161

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

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

## H162

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "Which method infers a regulatory network for each spot that borrows information from the neighboring spots?" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H163

> We measured methylation at diagnosis and expression at relapse in 120 patients. Is there a method that estimates time-lagged effects of the earlier methylation on the later expression?

- kind: UNSUPPORTED_CORE
- core: time-lagged effects of methylation on later expression
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "estimates time-lagged effects of the earlier methylation on the later expression" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H164

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H165

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?" -- available from CONDOR.

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

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

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

## H167

> We collected raw tandem mass spectra from 24 plasma samples. Which method identifies the peptides behind each spectrum?

- kind: UNSUPPORTED_CORE
- core: peptide identification from mass spectra
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H168

> We have expression from 90 samples. Is there a method that builds a separate gene-gene co-expression network for each sample?

- kind: SUPPORTED
- core: a gene-gene co-expression network for each sample
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user has access to the necessary expression data for each sample.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "90 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H169

> We have expression from 150 samples with age and sex recorded. Is there a method that removes the effects of these covariates from the co-expression before network inference?

- kind: SUPPORTED
- core: co-expression with covariate effects removed before network inference
- accept: ['run_cobra']

Full reply:

```
Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H170

> We built a gene-gene co-expression network from 150 samples. Is there a method that partitions this co-expression network into gene modules?

- kind: UNSUPPORTED_CORE
- core: modules of a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that partitions this co-expression network into gene modules?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H171

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?" -- available from GIRAFFE.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H172

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?" -- available from LIONESS-PUMA's output plus a step you run outside NetZoo: Sum edge weights per TF per sample from the edge-by-sample table; NetZoo does not compute it.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H173

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H174

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The user has expression, methylation, and proteomics data available for analysis.

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

## H175

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds communities in it where one gene can belong to several communities at once?" -- available from CONDOR.

Fallback recommendation: **CONDOR**. The request was interpreted and a candidate was found, but at least one quote supporting that reading could not be located in your text -- often a spelling or rephrasing difference, sometimes a detail the reading added. So this is shown as a candidate rather than a verified match, and nothing will run from it. Please check that the reading matches what you meant.

Your question asks for a cohort-level community assignment. **CONDOR** is related to that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H176

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H177

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The user has access to the necessary computational tools for network inference and CRISPR design.

**PUMA** fits the result you describe, but it needs a motif prior and a PPI network, which you said you do not have.

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

**What your data allows.** Your request names only a miRNA list. PUMA needs a motif prior and a PPI network, which you said you do not have ("We have miRNA and mRNA expression from 80 samples."). With a miRNA list alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H178

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
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

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; PUMA and LIONESS-PUMA also need an expression matrix, a motif prior, a PPI network and a miRNA list; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H179

> We measured expression, methylation and proteomics in the same 100 patients. Is there a method that builds one network linking all three layers jointly?

- kind: UNSUPPORTED_CORE
- core: one joint network across three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The user has expression, methylation, and proteomics data available for analysis.

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

## H180

> We found 50 missense variants in a kinase. Which method predicts the 3D structure of each mutant protein?

- kind: UNSUPPORTED_CORE
- core: protein 3D structure prediction
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "Which method predicts the 3D structure of each mutant protein?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H181

> We ran ATAC-seq on 30 samples from two conditions. Is there a tool that calls accessibility peaks and finds the regions that differ between the conditions?

- kind: UNSUPPORTED_CORE
- core: peak calling and differential accessibility
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H182

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "Which method gives a separate gene regulatory network for each individual cell?" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H183

> We have bulk RNA-seq from 40 melanomas. Is there a method that estimates what fraction of each tumor is made of each immune cell type?

- kind: UNSUPPORTED_CORE
- core: immune cell-type proportions per tumor
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H184

> We have a TF-gene network for 300 lung samples. Which method finds communities in it where one gene can belong to several communities at once?

- kind: UNSUPPORTED_CORE
- core: overlapping communities where a gene belongs to several
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "Which method finds communities in it where one gene can belong to several communities at once?" -- available from CONDOR.

Fallback recommendation: **CONDOR**. The request was interpreted and a candidate was found, but at least one quote supporting that reading could not be located in your text -- often a spelling or rephrasing difference, sometimes a detail the reading added. So this is shown as a candidate rather than a verified match, and nothing will run from it. Please check that the reading matches what you meant.

Your question asks for a cohort-level community assignment. **CONDOR** is related to that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H185

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "infers a regulatory network for each spot that borrows information from the neighboring spots" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H186

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "estimates how active each TF is in each sample, beyond what its own mRNA level says" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each TF is in each sample, beyond what its own mRNA level says" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

## H187

> We have expression, motifs and PPI from 90 muscle biopsies. Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?

- kind: SUPPORTED
- core: whether each TF turns its targets on or shuts them off
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "Which method can tell us, for each TF-target pair, whether the TF tends to turn the target on or shut it off?" -- available from GIRAFFE.

Assumptions behind this recommendation (not confirmed facts):

- The analysis will utilize expression data, motifs, and PPI from the muscle biopsies.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H188

> We have a bipartite TF-gene network. Which method finds its communities and then renders them as an interactive 3D visualization?

- kind: HALF
- core: an interactive 3D visualization
- accept: ['run_condor']

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

## H189

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H190

> We measured plasma metabolites and gut microbial gene abundances in 110 people. Is there a method that estimates direct conditional links between the two data types rather than plain correlations?

- kind: SUPPORTED
- core: direct conditional links between metabolites and microbial genes
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

## H191

> We have scRNA-seq of 12,000 bone marrow cells. Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?

- kind: UNSUPPORTED_CORE
- core: pseudotime ordering of single cells
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "Which method can order these cells along a differentiation trajectory and give each cell a pseudotime value?" -- not matched to any registered workflow.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H192

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "infers a regulatory network in which the lncRNAs are the regulators of the coding genes" -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H193

> We have methylation and expression from 90 patients, but 20 patients lack methylation. Is there a method that imputes the missing methylation values and then links the two layers in one network?

- kind: HALF
- core: imputation of missing methylation values
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

## H194

> We have expression, motifs and PPI for 75 colon tumors. Which method gives each tumor its own TF-gene network so we can compare networks between patients?

- kind: SUPPORTED
- core: a TF-gene network for each tumor
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each tumor its own TF-gene network so we can compare networks between patients?" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 75 tumors, 76 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H195

> We sequenced full-length transcripts with long reads from 10 brain samples. Is there a method that discovers new transcript isoforms and quantifies them?

- kind: UNSUPPORTED_CORE
- core: novel isoform discovery from long reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H196

> We have miRNA and mRNA expression from 80 samples. Which method infers a network of TF and miRNA regulators and then designs CRISPR guides to knock out the top miRNAs?

- kind: HALF
- core: CRISPR guide design
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

**What your data allows.** Your request names only a miRNA list. PUMA and LIONESS-PUMA need a motif prior and a PPI network, which you said you do not have ("We have miRNA and mRNA expression from 80 samples."). With a miRNA list alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead.

No files were inspected and no analysis ran.
```

## H197

> We already have a bipartite TF-to-gene network from a kidney study. Is there a method that splits it into communities of TFs and genes and scores how central each node is within its community?

- kind: SUPPORTED
- core: communities of a TF-gene network with node centrality in each
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "splits it into communities of TFs and genes and scores how central each node is within its community" -- available from CONDOR.

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

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "proves the causal effect of each TF on each of its targets" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> We have single-cell RNA-seq from 5,000 T cells plus TF motifs. Which method gives a separate gene regulatory network for each individual cell?

- kind: UNSUPPORTED_CORE
- core: a separate network for each single cell
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H200

> We profiled lncRNAs and protein-coding genes in 80 tumors. Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?

- kind: UNSUPPORTED_CORE
- core: a network with lncRNAs as the regulators
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "Is there a method that infers a regulatory network in which the lncRNAs are the regulators of the coding genes?" -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H201

> We have somatic mutation calls for 300 tumors. Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?

- kind: HALF
- core: neoantigen prediction
- accept: ['run_sambar']

Full reply:

```
About "Is there a method that turns them into pathway scores to subtype the patients and also predicts neoantigens from the mutations?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

For “predicts neoantigens from the mutations”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

To use subtypes for chemotherapy resistance or another clinical outcome, you would also need outcome labels matched to the patients. Check cluster stability and confounding, then evaluate prediction on held-out patients. Fit feature selection and cohort-dependent network estimation within the training split to avoid information leakage.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## H202

> We have expression from 50 samples plus motifs and PPI. Is there a method that estimates how active each TF is in each sample, beyond what its own mRNA level says?

- kind: SUPPORTED
- core: per-sample TF activity apart from the TF's own mRNA
- accept: ['run_giraffe']

Full reply:

```
**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
```

## H203

> We have expression from 200 patients plus TF motifs and PPI. Is there a method that proves the causal effect of each TF on each of its targets?

- kind: UNSUPPORTED_CORE
- core: proof of each TF's causal effect on its targets
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
About "a method that proves the causal effect of each TF on each of its targets": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H204

> We have RNA-seq from 100 tumors with motif and PPI data. Is there a method that builds a TF-gene network for each tumor and then predicts each patient's drug response from those networks?

- kind: HALF
- core: drug response prediction
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "builds a TF-gene network for each tumor" -- available from LIONESS-PANDA.
2. "predicts each patient's drug response from those networks" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predicts each patient's drug response from those networks": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 100 tumors, 101 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H205

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network of direct links between methylation and expression?" -- available from LIONESS-DRAGON.
2. "each patient their own network of direct links between methylation and expression" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H206

> We have miRNA and mRNA measured at 10 time points during infection. Which method models how each miRNA's regulation of its targets evolves over time as a dynamic system?

- kind: UNSUPPORTED_CORE
- core: miRNA dynamics modeled along a time course
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_lioness_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `mirna_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H207

> We have methylation and expression from the same 70 patients. Which method gives each patient their own network of direct links between methylation and expression?

- kind: SUPPORTED
- core: a per-patient network of direct methylation-expression links
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "Which method gives each patient their own network of direct links between methylation and expression?" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H208

> We have summary statistics for 90 GWAS loci. Is there a method that fine-maps each locus into a credible set of likely causal variants?

- kind: UNSUPPORTED_CORE
- core: statistical fine-mapping of GWAS loci
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H209

> We have spatial transcriptomics spots from 4 tissue sections and TF motifs. Which method infers a regulatory network for each spot that borrows information from the neighboring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks that use neighboring spots' expression
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## H210

> We have Hi-C contact maps from two cell lines. Which approach detects topologically associating domains and compares their boundaries between the lines?

- kind: UNSUPPORTED_CORE
- core: TAD calling from Hi-C
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```
