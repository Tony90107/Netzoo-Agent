# Blinded held-out sessions for labelling

## H001

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "We want partial correlations between the two data types." -- available from DRAGON.

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

## H002

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H003

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H004

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "we want TF and microRNA regulation of genes estimated separately for every tumor." -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H005

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "TF and microRNA regulation of genes estimated separately for every tumor" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H006

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H007

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "find which genes oscillate with a circadian rhythm" -- not matched to any registered workflow.
2. "estimate their phases" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H008

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H009

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network in which every cross-layer edge is oriented from cause to effect" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H010

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
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

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Fallback recommendation: **PUMA → LIONESS-PUMA**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

What you asked about:

- **PUMA** · "forecast each patient's treatment response" — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup. For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PUMA** · "forecast each patient's treatment response" — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

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

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H012

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H013

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "each miRNA's expression level per tumor" -- not matched to any registered workflow.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `mirna_file`: target

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H014

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
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

## H015

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how each TF's activating or repressing effect changes over time within each patient" -- available from LIONESS-DRAGON.

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

For your question ("how each TF's activating or repressing effect changes over time within each patient"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H016

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H017

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one network of which TFs and which microRNAs control which genes." -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H018

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "for each patient, a partial-correlation network between proteins and phosphosites" -- available from LIONESS-DRAGON.

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

## H019

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

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

## H020

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "TF and microRNA regulation of genes estimated separately for every tumor" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H021

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
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

## H022

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate partial-correlation network per patient across all three layers" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H023

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict where in the cell each one localizes from its sequence" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H024

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will be based on matched miRNA and mRNA expression data from 90 tumors.
- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H025

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "for each patient, a partial-correlation network between proteins and phosphosites" -- available from LIONESS-DRAGON.

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

## H026

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict where in the cell each one localizes from its sequence" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H027

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Fallback recommendation: **PUMA → LIONESS-PUMA**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H028

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which TFs activate or repress their targets" -- available from GIRAFFE.
2. "predict the effect of knocking each TF out" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

What you asked about:

- "predict the effect of knocking each TF out" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

## H029

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H030

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H031

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
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

## H032

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate partial-correlation network per patient across all three layers" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H033

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call heteroplasmic variants" -- not matched to any registered workflow.
2. "estimate their allele fractions in each sample" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H034

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link." -- available from DRAGON.

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

## H035

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "communities of regulators and genes" -- available from CONDOR.
2. "overlapping memberships so a gene can belong to several modules" -- not matched to any registered workflow.

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

## H036

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "testing whether methylation mediates smoking's effect on expression": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## H037

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "testing whether methylation mediates smoking's effect on expression": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## H038

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "gene-gene co-expression explained by treatment" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H039

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H040

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the cohort" -- available from PANDA, OTTER or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H041

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF and miRNA network per patient" -- available from LIONESS-PUMA.
2. "to forecast each patient's treatment response" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Fallback recommendation: **PUMA → LIONESS-PUMA**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

What you asked about:

- **PUMA** · "to forecast each patient's treatment response" — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup. For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PUMA** · "to forecast each patient's treatment response" — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

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

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H042

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H043

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "we want to predict where in the cell each one localizes from its sequence.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H044

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H045

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H046

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Captured request parameters:

- `mirna_file`: target

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H047

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "which day-1 proteins predict which day-7 metabolites" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H048

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
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

## H049

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how each TF's activating or repressing effect changes over time within each patient" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H050

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H051

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link." -- available from DRAGON.

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

## H052

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which TFs activate or repress their targets" -- available from GIRAFFE.
2. "predict the effect of knocking each TF out" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- The expression data from 110 samples is available for analysis.
- Motif and protein interaction priors are relevant for understanding TF-target interactions.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

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

## H053

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
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

## H054

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "each miRNA's expression level per tumor" -- not matched to any registered workflow.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Captured request parameters:

- `mirna_file`: target

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H055

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H056

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "for each patient, a partial-correlation network between proteins and phosphosites" -- available from LIONESS-DRAGON.

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

## H057

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "partial correlations between the two data types" -- available from DRAGON.

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

## H058

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities of regulators and genes" -- available from CONDOR.
2. "overlapping memberships so a gene can belong to several modules" -- not matched to any registered workflow.

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

## H059

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "whether each transcription factor pushes its target genes up or pushes them down" -- available from GIRAFFE.

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

## H060

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a single score of how each gene's module membership differs between them" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H061

> With the same kind of inputs plus microRNA target predictions for 58 tumors, we want TF and microRNA regulation of genes estimated separately for every tumor.

- kind: SUPPORTED
- core: TF and microRNA regulation for every sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 58 tumors, 59 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a miRNA list. LIONESS-PUMA and PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H062

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to." -- available from CONDOR.

I can map this to more than one compatible network result:

**Community assignments**
- **CONDOR** — CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions. Needs bipartite network.

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE); or network-node community memberships, not patient subtype labels (CONDOR)?

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H063

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

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

## H064

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "one partial-correlation network linking the two layers" -- available from DRAGON.
2. "a flux balance analysis of central metabolism" -- not available here: no registered workflow produces this. DRAGON does not give it: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.

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

## H065

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
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

## H066

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
**GIRAFFE** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** GIRAFFE also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H067

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
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

## H068

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "find the modules" -- available from CONDOR.
2. "rank which transcription factors are most central within each module" -- available from CONDOR.

I can map this to more than one compatible network result:

**Community assignments**
- **CONDOR** — CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions. Needs bipartite network.

**Gene co-expression network**
- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Which result do you mean: network-node community memberships, not patient subtype labels (CONDOR); or inferred gene-to-gene associations, one cohort-wide result (LIONESS-COEXPRESSION or COBRA)?

No files were inspected and no analysis ran.
```

## H069

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H070

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
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

## H071

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "microRNA-target edges inferred from anti-correlation between each miRNA and its targets" -- not available here: no registered workflow produces this. PUMA does not give it: the miRNA's own expression is not an input.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H072

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H073

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how each TF's activating or repressing effect changes over time within each patient" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H074

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "densely connected modules of TFs together with the targets they share" -- available from CONDOR.

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

## H075

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "the direct links between cytokines and bacteria, conditioned on everything else" -- available from DRAGON.
2. "significance for each link" -- available from DRAGON.

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

## H076

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "densely connected modules of TFs together with the targets they share" -- available from CONDOR.

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

## H077

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H078

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which microRNAs activate and which repress each target gene" -- available from DRAGON or LIONESS-DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H079

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "patient subtypes from mutated pathways" -- available from SAMBAR.

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

## H080

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "each miRNA's expression level per tumor" -- not matched to any registered workflow.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Captured request parameters:

- `mirna_file`: target

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H081

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
Fallback recommendation: **DRAGON**. The request was interpreted and a candidate was found, but at least one quote supporting that reading could not be located in your text -- often a spelling or rephrasing difference, sometimes a detail the reading added. So this is shown as a candidate rather than a verified match, and nothing will run from it. Please check that the reading matches what you meant.

Your question asks for a cohort-level multi-omic network. **DRAGON** is related to that result and scale.

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

## H082

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "microRNA-target edges inferred from anti-correlation between each miRNA and its targets" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H083

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "assemble contigs and bin them into metagenome-assembled genomes" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H084

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate the heritability of each gene's expression level" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H085

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H086

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

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

## H087

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
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

## H088

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "find the modules" -- available from CONDOR.
2. "rank which transcription factors are most central within each module" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The TF-to-target network is already established and available for analysis.
- Centrality measures can be applied to the identified modules to rank transcription factors.

Selected path: **CONDOR**.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H089

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which TFs activate or repress their targets" -- available from GIRAFFE.
2. "predict the effect of knocking each TF out" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- The expression data from 110 samples is available for analysis.
- Motif and protein interaction priors are relevant for determining regulatory effects.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

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

## H090

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "we want to predict where in the cell each one localizes from its sequence.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H091

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The proteome and metabolome data are compatible for multi-omic analysis.

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

## H092

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Captured request parameters:

- `mirna_file`: target

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H093

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H094

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H095

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H096

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H097

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the cohort" -- available from PANDA or OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The RNA-seq data is suitable for inferring a regulatory network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H098

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "which day-1 proteins predict which day-7 metabolites" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H099

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "find which genes oscillate with a circadian rhythm" -- not matched to any registered workflow.
2. "estimate their phases" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H100

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H101

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H102

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF and miRNA network per patient" -- available from LIONESS-PUMA.
2. "to forecast each patient's treatment response" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Fallback recommendation: **PUMA → LIONESS-PUMA**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H103

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H104

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H105

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
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

## H106

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 45 patients, 46 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H107

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "which day-1 proteins predict which day-7 metabolites.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H108

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H109

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate the heritability of each gene's expression level" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H110

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H111

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
**GIRAFFE** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** GIRAFFE also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H112

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
- accept: ['run_condor']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The TF-to-target network is already established and available for analysis.
- Centrality measures can be applied to the identified modules.

Selected path: **CONDOR**.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H113

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which microRNAs activate and which repress each target gene" -- not available here: no registered workflow produces this. PANDA does not give it: edge weights are unsigned support scores.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H114

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

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

## H115

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

Full reply:

```
Fallback recommendation: **DRAGON → LIONESS-DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

**LIONESS-DRAGON** — Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample.
- Each sample's network is an undirected partial-correlation graph across both layers; like DRAGON's, it is an association graph, not a causal one.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H116

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "assemble contigs" -- not matched to any registered workflow.
2. "bin them into metagenome-assembled genomes" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H117

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to assemble contigs and bin them into metagenome-assembled genomes." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H118

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network for each donor" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H119

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H120

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "one partial-correlation network linking the two layers" -- available from DRAGON.
2. "a flux balance analysis of central metabolism" -- not available here: no registered workflow produces this. DRAGON does not give it: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.

Assumptions behind this recommendation (not confirmed facts):

- The user has the necessary data for both proteome and metabolome measurements.

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

## H121

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 45 patients, 46 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H122

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a mediation analysis testing whether methylation mediates smoking's effect on expression" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H123

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 45 patients, 46 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H124

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
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

## H125

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "find which genes oscillate with a circadian rhythm" -- not matched to any registered workflow.
2. "estimate their phases" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H126

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
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

## H127

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H128

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
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

## H129

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H130

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "find the modules" -- available from CONDOR.
2. "rank which transcription factors are most central within each module" -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H131

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "which day-1 proteins predict which day-7 metabolites.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H132

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call heteroplasmic variants" -- not matched to any registered workflow.
2. "estimate their allele fractions in each sample" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H133

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a single score of how each gene's module membership differs between them" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H134

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to." -- available from CONDOR.

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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H135

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H136

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate each person's telomere length" -- not matched to any registered workflow.
2. "relate it to frailty" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H137

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "validate 40 candidate genes by qPCR" -- not matched to any registered workflow.
2. "design primer pairs for each gene that avoid genomic DNA amplification" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H138

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
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

## H139

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate each person's telomere length" -- not matched to any registered workflow.
2. "relate it to frailty" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H140

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate each person's telomere length" -- not matched to any registered workflow.
2. "relate it to frailty" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H141

> In 140 people we measured serum cytokines and gut bacterial abundances. We want the direct links between cytokines and bacteria, conditioned on everything else, with significance for each link.

- kind: SUPPORTED
- core: conditional associations between cytokines and bacterial abundances
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

## H142

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "gene-gene co-expression explained by treatment" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H143

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "patient subtypes from mutated pathways" -- available from SAMBAR.

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

## H144

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "we want to predict where in the cell each one localizes from its sequence.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H145

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "validate 40 candidate genes by qPCR" -- not matched to any registered workflow.
2. "design primer pairs for each gene that avoid genomic DNA amplification" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H146

> We have matched miRNA and mRNA expression for 90 tumors. We want microRNA-target edges inferred from anti-correlation between each miRNA and its targets.

- kind: UNSUPPORTED_CORE
- core: miRNA-target edges from anti-correlated miRNA and mRNA expression
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "microRNA-target edges inferred from anti-correlation between each miRNA and its targets" -- not available here: no registered workflow produces this. PUMA does not give it: the miRNA's own expression is not an input.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H147

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H148

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- The analysis will utilize the expression data from 110 samples along with motif and protein interaction priors.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

What you asked about:

- "predict the effect of knocking each TF out" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

## H149

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "partial correlations between the two data types" -- available from DRAGON.

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

## H150

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
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

## H151

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF and miRNA network per patient" -- available from LIONESS-PUMA.
2. "to forecast each patient's treatment response" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 75 patients, 76 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H152

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H153

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H154

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H155

> In our TF-to-target network, we want to find the modules and rank which transcription factors are most central within each module.

- kind: SUPPORTED
- core: the most central regulators within each module
- accept: ['run_condor']

Full reply:

```
Selected path: **CONDOR**.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H156

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
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

## H157

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities of regulators and genes" -- available from CONDOR.
2. "overlapping memberships so a gene can belong to several modules" -- not matched to any registered workflow.

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

## H158

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "one partial-correlation network linking the two layers" -- available from DRAGON.
2. "a flux balance analysis of central metabolism" -- not available here: no registered workflow produces this. DRAGON does not give it: DRAGON returns associations between measured features; it has no stoichiometric or kinetic model.

Assumptions behind this recommendation (not confirmed facts):

- The user intends to analyze the relationship between proteome and metabolome data.

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

## H160

> We have chromatin accessibility at gene promoters and gene expression in the same 80 samples. We want partial correlations between the two data types.

- kind: SUPPORTED
- core: partial correlations between accessibility and expression
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

## H161

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
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

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "we want a two-layer network in which every cross-layer edge is oriented from cause to effect." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H163

> For 45 patients we have expression, proteomics and lipidomics. We want a separate partial-correlation network per patient across all three layers.

- kind: UNSUPPORTED_CORE
- core: a per-patient network over three omics layers
- nearest (may be offered only with the core stated as not produced): ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate partial-correlation network per patient across all three layers" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H164

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H165

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one network of which TFs and which microRNAs control which genes." -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H166

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
```

## H167

> We sampled mouse liver every four hours for two days. We want to find which genes oscillate with a circadian rhythm and estimate their phases.

- kind: UNSUPPORTED_CORE
- core: rhythmic genes from a circadian time series
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H168

> We want the gene-gene co-expression explained by treatment in 120 samples from 30 donors, adjusting for donor in a design matrix.

- kind: SUPPORTED
- core: co-expression explained by treatment adjusting for donor
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "gene-gene co-expression explained by treatment" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H169

> We have somatic mutation calls for 260 head and neck tumors. We want patient subtypes from mutated pathways.

- kind: SUPPORTED
- core: pathway-based mutation subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "patient subtypes from mutated pathways" -- available from SAMBAR.

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

## H170

> We have one TF-gene regulatory network for healthy and one for diseased tissue. We want a single score of how each gene's module membership differs between them.

- kind: UNSUPPORTED_CORE
- core: differential modularity between two networks
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a single score of how each gene's module membership differs between them" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H171

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "whether each transcription factor pushes its target genes up or pushes them down" -- available from GIRAFFE.

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

## H172

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which microRNAs activate and which repress each target gene" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H173

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H174

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
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

For your question ("how each TF's activating or repressing effect changes over time within each patient"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H175

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to." -- available from CONDOR.

I can map this to more than one compatible network result:

**Community assignments**
- **CONDOR** — CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions. Needs bipartite network.

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE); or network-node community memberships, not patient subtype labels (CONDOR)?

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H176

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "to see how often cells switch states" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H177

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- The expression data is sufficient to infer regulatory relationships.
- Motif and protein interaction priors will enhance the accuracy of the predictions.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

What you asked about:

- "predict the effect of knocking each TF out" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

## H178

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "testing whether methylation mediates smoking's effect on expression": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## H179

> With five time points per patient plus motif and protein interaction priors, we want how each TF's activating or repressing effect changes over time within each patient.

- kind: UNSUPPORTED_CORE
- core: per-patient changes of signed TF effects over time
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
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

For your question ("how each TF's activating or repressing effect changes over time within each patient"):
- **GIRAFFE** — The difference between an individual's activity profiles at the time points measures how much that individual's TF activity changed.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H180

> For 600 uncharacterized proteins, we want to predict where in the cell each one localizes from its sequence.

- kind: UNSUPPORTED_CORE
- core: protein subcellular localization predictions
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict where in the cell each one localizes from its sequence" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H181

> From whole-genome sequencing of 500 elderly participants, we want to estimate each person's telomere length and relate it to frailty.

- kind: UNSUPPORTED_CORE
- core: telomere length estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H182

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "which day-1 proteins predict which day-7 metabolites" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H183

> We have blood expression from 400 twin pairs. We want to estimate the heritability of each gene's expression level.

- kind: UNSUPPORTED_CORE
- core: heritability of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "estimate the heritability of each gene's expression level" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H184

> In our TF-gene regulatory network we want overlapping modules, where each regulator and gene gets a membership strength for every module it belongs to.

- kind: UNSUPPORTED_CORE
- core: overlapping communities with membership strengths
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
I can map this to more than one compatible network result:

**Community assignments**
- **CONDOR** — CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions. Needs bipartite network.

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE); or network-node community memberships, not patient subtype labels (CONDOR)?

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H185

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network in which every cross-layer edge is oriented from cause to effect" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H186

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the cohort" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H187

> From kidney expression with motif and protein interaction priors, we want to know whether each transcription factor pushes its target genes up or pushes them down.

- kind: SUPPORTED
- core: whether each TF pushes its targets up or down
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "whether each transcription factor pushes its target genes up or pushes them down." -- available from GIRAFFE.

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

## H188

> We have a TF-gene network from lung tissue. We want its communities of regulators and genes, and then overlapping memberships so a gene can belong to several modules.

- kind: HALF
- core: overlapping community memberships
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

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H190

> We have proteomics and phosphoproteomics from the same 60 patients. We want, for each patient, a partial-correlation network between proteins and phosphosites.

- kind: SUPPORTED
- core: per-patient protein-phosphosite networks
- accept: ['run_lioness_dragon']

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H191

> We sequenced mitochondrial DNA from 70 muscle biopsies. We want to call heteroplasmic variants and estimate their allele fractions in each sample.

- kind: UNSUPPORTED_CORE
- core: mitochondrial heteroplasmy calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call heteroplasmic variants" -- not matched to any registered workflow.
2. "estimate their allele fractions in each sample" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H192

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a mediation analysis testing whether methylation mediates smoking's effect on expression" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H193

> With mRNA expression, motif and protein interaction priors and miRNA target predictions for 70 tumors, we want one TF and miRNA network, and then each miRNA's expression level per tumor.

- kind: HALF
- core: estimated miRNA expression levels
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Captured request parameters:

- `mirna_file`: target

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H194

> We have a weighted network linking transcription factors to their target genes. We want densely connected modules of TFs together with the targets they share.

- kind: SUPPORTED
- core: modules of TFs and their targets
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "densely connected modules of TFs together with the targets they share" -- available from CONDOR.

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

## H195

> We want to simulate stochastic gene expression of a small toggle-switch circuit with the Gillespie algorithm to see how often cells switch states.

- kind: UNSUPPORTED_CORE
- core: a stochastic simulation of gene expression
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H196

> With expression of 110 samples plus motif and protein interaction priors, we want to know which TFs activate or repress their targets, and then predict the effect of knocking each TF out.

- kind: HALF
- core: predicted effects of TF knockouts
- accept: ['run_giraffe']

Full reply:

```
About "predict the effect of knocking each TF out": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Selected path: **GIRAFFE**.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

What you asked about:

- "predict the effect of knocking each TF out" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

## H197

> With expression, motif and protein interaction priors and microRNA target predictions for 105 samples, we want one network of which TFs and which microRNAs control which genes.

- kind: SUPPORTED
- core: one TF and microRNA network for the cohort
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one network of which TFs and which microRNAs control which genes" -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H198

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> We measured proteins on day 1 and metabolites on day 7 in 60 patients. We want which day-1 proteins predict which day-7 metabolites.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations from proteins to metabolites
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "which day-1 proteins predict which day-7 metabolites.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

## H200

> We have methylation and expression from 150 smokers and non-smokers. We want a mediation analysis testing whether methylation mediates smoking's effect on expression.

- kind: UNSUPPORTED_CORE
- core: a mediation analysis of smoking through methylation
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "a mediation analysis testing whether methylation mediates smoking's effect on expression" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H201

> With expression, motif, protein interaction and miRNA target priors for 75 patients, we want a TF and miRNA network per patient, and then to forecast each patient's treatment response.

- kind: HALF
- core: forecasting treatment response
- accept: ['run_lioness_puma']

Full reply:

```
About "to forecast each patient's treatment response": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 75 patients, 76 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H202

> We have RNA-seq from 300 thyroid tumors, a motif prior and a protein interaction network. We want one TF-gene regulatory network for the cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
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

## H203

> We want a TF-gene network whose edge weights are measured dissociation constants of each TF for each promoter, not inferred scores.

- kind: UNSUPPORTED_CORE
- core: measured binding affinities as edge weights
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

## H204

> We measured proteome and metabolome in 85 patients. We want one partial-correlation network linking the two layers, and then a flux balance analysis of central metabolism.

- kind: HALF
- core: flux balance analysis
- accept: ['run_dragon']

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

## H205

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network for each donor" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H206

> With miRNA target predictions and expression for 100 samples, we want to know which microRNAs activate and which repress each target gene.

- kind: UNSUPPORTED_CORE
- core: signed microRNA regulation
- nearest (may be offered only with the core stated as not produced): ['run_puma', 'run_giraffe']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs a motif prior and a PPI network. With a miRNA list alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H207

> We have only expression data for 50 donors. We want a gene co-expression network for each donor to compare between donors.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network for each donor" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "50 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H208

> We have deep shotgun metagenomes from 15 soil samples. We want to assemble contigs and bin them into metagenome-assembled genomes.

- kind: UNSUPPORTED_CORE
- core: metagenome-assembled genome bins
- nearest (may be offered only with the core stated as not produced): []

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

## H209

> From methylation and expression of 110 tumors, we want a two-layer network in which every cross-layer edge is oriented from cause to effect.

- kind: UNSUPPORTED_CORE
- core: a causal direction from methylation to expression for each edge
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

## H210

> We want to validate 40 candidate genes by qPCR. Please design primer pairs for each gene that avoid genomic DNA amplification.

- kind: UNSUPPORTED_CORE
- core: qPCR primer designs
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "validate 40 candidate genes by qPCR" -- not matched to any registered workflow.
2. "design primer pairs for each gene that avoid genomic DNA amplification" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```
