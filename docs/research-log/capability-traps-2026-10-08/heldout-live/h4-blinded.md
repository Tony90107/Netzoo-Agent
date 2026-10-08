# Blinded held-out sessions for labelling

## H001

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "each patient's TF-gene network" -- available from LIONESS-PANDA.
2. "to relate TF targeting to treatment response" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H002

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H003

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "methylation at one time point predicts expression at the next": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: six

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H004

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

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

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H005

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

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

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H006

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
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

For your question ("detect genes that switch polyadenylation sites between the two states"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## H007

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect genes that switch polyadenylation sites between the two states" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H008

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H009

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "partition this co-expression network into communities of genes" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H010

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

## H011

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
- accept: ['run_cobra']

Full reply:

```
Based on what you said — "We want the co-expression attributable to diet after adjusting for batch." — **COBRA** fits better: co-expression must be separated or adjusted for batch, site or other covariates.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** (recommend) — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern. Needs expression matrix and sample covariate design matrix. Produces inferred gene-to-gene associations (one cohort-level result).

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use COBRA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## H012

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H013

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "to prove the miRNAs drive the aggressive subtype" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H014

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "PANDA's refined TF-TF cooperativity network itself as the output" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H016

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
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

## H017

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network of TF and microRNA regulation for each tumor separately" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H018

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which transcription factors activate and which repress their target genes" -- available from GIRAFFE.

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

## H019

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
About "to predict new microRNA binding sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H020

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "We want a gene co-expression network for each donor." -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H021

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
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

## H022

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a co-expression network for each sample in which every edge has a direction showing which gene drives the other" -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: co-expression is undirected gene-gene similarity, with no regulator layer.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H023

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to annotate the detected features with metabolite identities using spectral libraries." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H024

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "We want to subtype the patients from their copy-number alterations at pathway level." — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H025

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which transcription factors activate and which repress their target genes" -- available from GIRAFFE.

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

## H026

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to annotate the detected features with metabolite identities using spectral libraries." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H027

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
- accept: ['run_cobra']

Full reply:

```
Based on what you said — "We want the co-expression attributable to diet after adjusting for batch." — **COBRA** fits better: co-expression must be separated or adjusted for batch, site or other covariates.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** (recommend) — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern. Needs expression matrix and sample covariate design matrix. Produces inferred gene-to-gene associations (one cohort-level result).

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use COBRA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## H028

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities of regulators and genes" -- available from CONDOR.
2. "to map where each module is active within tissue sections" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is already established and available for analysis.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H029

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `sparsify`=False, `bonobo_confidence`=0.05, `save_pvals`=False, `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

For your question ("we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene."):
- **BONOBO** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H030

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "We want to subtype the patients from their copy-number alterations at pathway level." — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H031

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
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

## H032

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a co-expression network for each sample in which every edge has a direction showing which gene drives the other" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H033

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "multiple sequence alignment" -- not matched to any registered workflow.
2. "maximum-likelihood tree" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H034

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H035

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per biopsy" -- available from GIRAFFE.
2. "the same activities resolved for individual cells" -- not matched to any registered workflow.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H036

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "ranked by on-target efficiency and predicted off-target sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H037

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "ranked by on-target efficiency and predicted off-target sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H038

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "cluster the patients into subtypes based on pathway-level mutation scores" -- available from SAMBAR.

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

## H039

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H040

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "direct associations between proteins and metabolites, with a p-value for every edge" -- available from DRAGON.

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

## H041

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "co-expression attributable to diet after adjusting for batch" -- available from COBRA.
2. "a GSEA run inside the same tool" -- not matched to any registered workflow.

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

## H042

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
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

## H043

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H044

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H045

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H046

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H047

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect and remove doublets" -- not matched to any registered workflow.
2. "correct ambient contamination before clustering" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H048

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
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

## H049

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "PANDA's refined TF-TF cooperativity network itself as the output" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H050

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H051

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene regulatory network for the whole cohort" -- available from PANDA, OTTER or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H052

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities of regulators and genes" -- available from CONDOR.
2. "to map where each module is active within tissue sections" -- not matched to any registered workflow.

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

## H053

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H054

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "to prove the miRNAs drive the aggressive subtype" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H055

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H056

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "which transcription factors activate and which repress their target genes" -- available from GIRAFFE.

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

## H057

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "each patient's TF-gene network" -- available from LIONESS-PANDA.
2. "to relate TF targeting to treatment response" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H058

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per biopsy" -- available from GIRAFFE.
2. "the same activities resolved for individual cells" -- not matched to any registered workflow.

Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

## H059

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how active each transcription factor is in each patient, apart from its mRNA level" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "scan 3' UTR sequences to predict new microRNA binding sites" -- not matched to any registered workflow.
2. "use them as a prior for a regulatory network" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H061

> We have only gene expression for 58 donors, without regulator priors. We want a gene co-expression network for each donor.

- kind: SUPPORTED
- core: per-sample co-expression networks
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "58 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H062

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "genes whose expression variance, not mean, differs significantly, with a p-value for each gene." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H063

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
About "to predict new microRNA binding sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H064

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network for each patient" -- available from LIONESS-DRAGON.
2. "forecast which patients will respond to therapy next year" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 85 patients, 86 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H065

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
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

## H067

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H068

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "modules of regulators and genes" -- available from CONDOR.
2. "a score saying which nodes are most central to each module" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The existing TF-gene network is suitable for module detection.

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

## H069

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H070

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
It sounds like you want sample-specific TF/gene/sample regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H071

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "subtype the patients from their copy-number alterations at pathway level" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H072

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
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

## H073

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "PANDA's refined TF-TF cooperativity network itself as the output" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H074

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates" -- available from COBRA.

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

## H075

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

- kind: SUPPORTED
- core: one TF-gene network for the cohort
- accept: ['run_panda', 'run_otter']

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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## H076

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H077

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `sparsify`=False, `bonobo_confidence`=0.05, `save_pvals`=False, `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

For your question ("we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene."):
- **BONOBO** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H078

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "associations where methylation at one time point predicts expression at the next" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H079

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "overall gene co-expression network for our 72 lung samples" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network per sample derived from that overall network" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H080

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one TF and miRNA network" -- available from PUMA.
2. "to prove the miRNAs drive the aggressive subtype" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H081

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
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

## H082

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "subtype the patients from their copy-number alterations at pathway level" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H083

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants." -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H084

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "find genes whose expression varies smoothly along spatial gradients in the tissue" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H085

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "pooled estimate" -- not matched to any registered workflow.
2. "heterogeneity" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H086

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 85 patients, 86 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H087

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its modules of regulators and genes" -- available from CONDOR.
2. "a score saying which nodes are most central to each module" -- available from CONDOR.

Selected path: **CONDOR**.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H089

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "its communities of regulators and genes" -- available from CONDOR.
2. "to map where each module is active within tissue sections" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is already established and available for analysis.

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

## H090

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H091

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 85 patients, 86 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H092

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Assumptions behind this recommendation (not confirmed facts):

- The user has access to the necessary expression, motif, protein interaction, and miRNA target prior data for analysis.

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

## H093

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "We want to subtype the patients from their copy-number alterations at pathway level." — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

## H094

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H095

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
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

## H096

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
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

## H097

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "We want direct associations between proteins and metabolites, with a p-value for every edge." -- available from DRAGON.

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

## H098

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect and remove doublets" -- not matched to any registered workflow.
2. "correct ambient contamination" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H099

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect genes that switch polyadenylation sites between the two states" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H100

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "methylation at one time point predicts expression at the next.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: six

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H101

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H102

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "co-expression attributable to diet after adjusting for batch" -- available from COBRA.
2. "a GSEA run inside the same tool" -- not matched to any registered workflow.

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

## H103

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H104

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H105

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
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

## H106

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "70 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H107

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H108

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H109

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "find genes whose expression varies smoothly along spatial gradients in the tissue" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H110

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
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

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H111

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
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

## H112

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
- accept: ['run_condor']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The existing TF-gene network is suitable for module detection.

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

## H113

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "associations where methylation at one time point predicts expression at the next" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H114

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
About "to predict new microRNA binding sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H115

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
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

## H116

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants." -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H117

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H118

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate methylation-expression partial-correlation network for each patient" -- available from LIONESS-DRAGON.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H119

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H120

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network for each patient" -- available from LIONESS-DRAGON.
2. "forecast which patients will respond to therapy next year" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H121

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "70 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H122

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to knock out 50 transcription factors." -- not matched to any registered workflow.
2. "We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites." -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H123

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "70 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H124

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

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

## H125

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect genes that switch polyadenylation sites between the two states" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H126

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
It sounds like you want sample-specific TF/gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## H127

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H128

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

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

## H129

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "pooled estimate" -- not matched to any registered workflow.
2. "heterogeneity" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H130

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "modules of regulators and genes" -- available from CONDOR.
2. "a score saying which nodes are most central to each module" -- available from CONDOR.

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

## H131

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H132

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "multiple sequence alignment" -- not matched to any registered workflow.
2. "maximum-likelihood tree" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H133

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "scan 3' UTR sequences to predict new microRNA binding sites" -- not matched to any registered workflow.
2. "use them as a prior for a regulatory network" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H134

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "genes whose expression variance, not mean, differs significantly, with a p-value for each gene" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H135

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H136

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "a population pharmacokinetic model with clearance and volume estimates" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H137

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "assemble its genome de novo" -- not matched to any registered workflow.
2. "annotate the predicted genes" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H138

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
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

## H139

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "a population pharmacokinetic model with clearance and volume estimates" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H140

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want a population pharmacokinetic model with clearance and volume estimates." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H141

> We have RNA-seq from 210 liver tumors, a TF motif prior and a protein interaction network. We want one TF-gene regulatory network for the whole cohort.

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

## H142

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "cluster the patients into subtypes based on pathway-level mutation scores" -- available from SAMBAR.

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

## H143

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "overall gene co-expression network" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network per sample derived from that overall network" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H144

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H145

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "assemble its genome de novo" -- not matched to any registered workflow.
2. "annotate the predicted genes" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H146

> We have copy-number segment profiles for 300 tumors and no mutation calls. We want to subtype the patients from their copy-number alterations at pathway level.

- kind: UNSUPPORTED_CORE
- core: subtypes from copy-number data
- nearest (may be offered only with the core stated as not produced): ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "subtype the patients from their copy-number alterations at pathway level" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H147

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H148

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
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

## H149

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "each patient's TF-gene network" -- available from LIONESS-PANDA.
2. "to relate TF targeting to treatment response" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale.

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

## H150

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
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

## H151

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "co-expression attributable to diet after adjusting for batch" -- available from COBRA.
2. "a GSEA run inside the same tool" -- not matched to any registered workflow.

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

## H152

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H153

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H154

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H155

> We already have a TF-gene network from pancreas. We want its modules of regulators and genes and a score saying which nodes are most central to each module.

- kind: SUPPORTED
- core: communities with core scores
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

## H156

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H157

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per biopsy" -- available from GIRAFFE.
2. "the same activities resolved for individual cells" -- not matched to any registered workflow.

Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

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

## H158

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a two-layer network for each patient" -- available from LIONESS-DRAGON.
2. "forecast which patients will respond to therapy next year" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 85 patients, 86 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H160

> With expression, motif and protein interaction priors for 90 melanoma patients, we want each patient's TF-gene network and to relate TF targeting to treatment response.

- kind: SUPPORTED
- core: per-sample TF-gene networks related to treatment response
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 patients, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

No files were inspected and no analysis ran.
```

## H161

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
Selected path: **GIRAFFE**.

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

## H162

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "We want to partition this co-expression network into communities of genes." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H163

> From expression of 70 samples we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other.

- kind: UNSUPPORTED_CORE
- core: directed causal edges between co-expressed genes
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "we want a co-expression network for each sample in which every edge has a direction showing which gene drives the other." -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: co-expression is undirected gene-gene similarity, with no regulator layer.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H164

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H165

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network of TF and microRNA regulation for each tumor separately." -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H166

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

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

## H167

> We have 3'-end sequencing from proliferating and quiescent fibroblasts. We want to detect genes that switch polyadenylation sites between the two states.

- kind: UNSUPPORTED_CORE
- core: alternative polyadenylation site usage
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H168

> We have somatic mutation calls for 280 kidney tumors. We want to cluster the patients into subtypes based on pathway-level mutation scores.

- kind: SUPPORTED
- core: mutation-based patient subtypes
- accept: ['run_sambar']

Full reply:

```
What I understood you are asking for:
1. "cluster the patients into subtypes based on pathway-level mutation scores" -- available from SAMBAR.

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

## H169

> We want the overall gene co-expression network for our 72 lung samples and one co-expression network per sample derived from that overall network.

- kind: SUPPORTED
- core: an aggregate and per-sample co-expression network
- accept: ['run_lioness_coexpression', 'run_bonobo']

Full reply:

```
What I understood you are asking for:
1. "overall gene co-expression network" -- available from LIONESS-COEXPRESSION.
2. "one co-expression network per sample" -- available from LIONESS-COEXPRESSION.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “overall gene co-expression network” and “one co-expression network per sample”:

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “one co-expression network per sample”:

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H170

> We want to scan 3' UTR sequences to predict new microRNA binding sites and then use them as a prior for a regulatory network.

- kind: UNSUPPORTED_CORE
- core: new miRNA binding sites predicted from sequence
- nearest (may be offered only with the core stated as not produced): ['run_puma']

Full reply:

```
What I understood you are asking for:
1. "scan 3' UTR sequences to predict new microRNA binding sites" -- not matched to any registered workflow.
2. "use them as a prior for a regulatory network" -- available from PUMA.

About "to predict new microRNA binding sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H171

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how active each transcription factor is in each patient, apart from its mRNA level" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
What I understood you are asking for:
1. "associations where methylation at one time point predicts expression at the next" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H173

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H174

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

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

## H175

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "genes whose expression variance, not mean, differs significantly, with a p-value for each gene." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H176

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want a random-effects meta-analysis with a pooled estimate and heterogeneity." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H177

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
- accept: ['run_condor']

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is already established and available for analysis.

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

## H178

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "ranked by on-target efficiency and predicted off-target sites": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H179

> With expression, a motif prior and a protein interaction network for 120 samples, we want PANDA's refined TF-TF cooperativity network itself as the output, not the TF-gene network.

- kind: UNSUPPORTED_CORE
- core: the refined TF-TF cooperativity network as an output
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H180

> We ran untargeted LC-MS on 60 urine samples. We want to annotate the detected features with metabolite identities using spectral libraries.

- kind: UNSUPPORTED_CORE
- core: metabolite identification from untargeted LC-MS
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "annotate the detected features with metabolite identities using spectral libraries" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H181

> We measured plasma drug concentrations at eight time points in 20 volunteers. We want a population pharmacokinetic model with clearance and volume estimates.

- kind: UNSUPPORTED_CORE
- core: a pharmacokinetic model of drug concentration
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H182

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect and remove doublets" -- not matched to any registered workflow.
2. "correct ambient contamination" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H183

> Our Slide-seq data covers mouse hippocampus sections. We want to find genes whose expression varies smoothly along spatial gradients in the tissue.

- kind: UNSUPPORTED_CORE
- core: a spatial map of gene expression gradients in tissue
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to find genes whose expression varies smoothly along spatial gradients in the tissue." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H184

> Between 50 cases and 50 controls we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene.

- kind: UNSUPPORTED_CORE
- core: single-gene differential variability between groups
- nearest (may be offered only with the core stated as not produced): ['run_cobra']

Full reply:

```
Fallback recommendation: **BONOBO**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a p-value matrix. **BONOBO** is related to that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `sparsify`=False, `bonobo_confidence`=0.05, `save_pvals`=False, `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

For your question ("we want genes whose expression variance, not mean, differs significantly, with a p-value for each gene."):
- **BONOBO** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H185

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "partition this co-expression network into communities of genes" -- available from CONDOR.

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

## H186

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "direct associations between proteins and metabolites, with a p-value for every edge" -- available from DRAGON.

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

## H187

> We have expression from 75 asthma patients with motif and protein interaction priors. We want how active each transcription factor is in each patient, apart from its mRNA level.

- kind: SUPPORTED
- core: TF activity per sample
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "how active each transcription factor is in each patient, apart from its mRNA level" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "how active each transcription factor is in each patient, apart from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

> Using bulk expression of 70 biopsies with motif and protein interaction priors, we want each TF's activity per biopsy, and then the same activities resolved for individual cells.

- kind: HALF
- core: single-cell resolution of the TF activities
- accept: ['run_giraffe']

Full reply:

```
**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
```

## H189

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H190

> From expression of 130 kidney samples with motif and protein interaction priors, we want to know which transcription factors activate and which repress their target genes.

- kind: SUPPORTED
- core: signed regulation for the cohort
- accept: ['run_giraffe']

Full reply:

```
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

## H191

> We have protein sequences for a gene family from 40 species. We want a multiple sequence alignment and a maximum-likelihood tree to study how the family evolved.

- kind: UNSUPPORTED_CORE
- core: a multiple sequence alignment and phylogenetic tree of gene families
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "multiple sequence alignment" -- not matched to any registered workflow.
2. "maximum-likelihood tree" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H192

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H193

> With expression, motif, protein interaction and miRNA target priors for 120 samples, we want one TF and miRNA network, then to prove the miRNAs drive the aggressive subtype.

- kind: HALF
- core: a causal claim that miRNAs drive the subtype
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
About "to prove the miRNAs drive the aggressive subtype.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

## H194

> We want the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates.

- kind: SUPPORTED
- core: co-expression attributable to a covariate
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "the part of gene-gene co-expression in 180 samples explained by BMI, adjusting for age, using a design matrix of covariates" -- available from COBRA.

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

## H195

> We collected odds ratios for one biomarker from twelve published studies. We want a random-effects meta-analysis with a pooled estimate and heterogeneity.

- kind: UNSUPPORTED_CORE
- core: a meta-analysis effect size across studies
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H196

> We have a TF-gene network for breast tumors. We want its communities of regulators and genes, and then to map where each module is active within tissue sections.

- kind: HALF
- core: spatial location of the modules in tissue
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

## H197

> With expression, motif, protein interaction and microRNA target priors for 64 tumors, we want a network of TF and microRNA regulation for each tumor separately.

- kind: SUPPORTED
- core: a TF and miRNA network per sample
- accept: ['run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network of TF and microRNA regulation for each tumor separately" -- available from LIONESS-PUMA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 64 tumors, 65 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## H198

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> Our droplet single-cell data likely contain doublets and ambient RNA. We want to detect and remove doublets and correct ambient contamination before clustering.

- kind: UNSUPPORTED_CORE
- core: a doublet-filtered single-cell count matrix
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## H200

> We want to knock out 50 transcription factors. We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites.

- kind: UNSUPPORTED_CORE
- core: a CRISPR guide design with off-target scores
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to knock out 50 transcription factors." -- not matched to any registered workflow.
2. "We need guide RNAs for each, ranked by on-target efficiency and predicted off-target sites." -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H201

> Our 150 samples span two batches and two diets. We want the co-expression attributable to diet after adjusting for batch, and a GSEA run inside the same tool.

- kind: HALF
- core: pathway enrichment computed by the tool itself with GSEA
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

## H202

> We measured proteomics and metabolomics in the same 100 patients. We want direct associations between proteins and metabolites, with a p-value for every edge.

- kind: SUPPORTED
- core: a two-layer partial-correlation network with edge p-values
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

## H203

> We want a directed TF-to-TF regulatory network that identifies feedback loops and feed-forward motifs among the transcription factors themselves.

- kind: UNSUPPORTED_CORE
- core: a network where TFs regulate other TFs only, with feedback loops
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

> We have proteomics and expression for 85 patients. We want a two-layer network for each patient, and then to forecast which patients will respond to therapy next year.

- kind: HALF
- core: forecasting each patient's response
- accept: ['run_lioness_dragon']

Full reply:

```
About "to forecast which patients will respond to therapy next year.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## H205

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate methylation-expression partial-correlation network for each patient" -- available from LIONESS-DRAGON.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H206

> We have methylation and expression at six time points per patient. We want associations where methylation at one time point predicts expression at the next.

- kind: UNSUPPORTED_CORE
- core: time-lagged associations between omics layers
- nearest (may be offered only with the core stated as not produced): ['run_dragon']

Full reply:

```
About "methylation at one time point predicts expression at the next": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: six

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H207

> We have methylation and expression from the same 80 patients. We want a separate methylation-expression partial-correlation network for each patient.

- kind: SUPPORTED
- core: per-patient two-layer networks
- accept: ['run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "a separate methylation-expression partial-correlation network for each patient" -- available from LIONESS-DRAGON.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 80 patients, 81 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## H208

> Using published GWAS weights, we want to compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.

- kind: UNSUPPORTED_CORE
- core: polygenic risk scores for individuals
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "compute a polygenic risk score for type 2 diabetes for each of our 2,000 genotyped participants.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H209

> We built a gene-gene co-expression network from 90 samples. We want to partition this co-expression network into communities of genes.

- kind: UNSUPPORTED_CORE
- core: community detection on a gene-gene co-expression network
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

## H210

> We sequenced a newly isolated bacterium with long and short reads. We want to assemble its genome de novo and annotate the predicted genes.

- kind: UNSUPPORTED_CORE
- core: de novo genome assembly
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "assemble its genome de novo" -- not matched to any registered workflow.
2. "annotate the predicted genes" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```
