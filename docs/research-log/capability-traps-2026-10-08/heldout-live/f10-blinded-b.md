# Blinded held-out sessions for labelling

## H106

> From spatial transcriptomics of 3 sections, we want a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are.

- kind: UNSUPPORTED_CORE
- core: co-expression weighted by the spatial proximity of spots
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H107

> In our TF-to-gene network, some TFs seem to bridge processes. Is there a method that finds modules where such a TF belongs to two modules at the same time?

- kind: UNSUPPORTED_CORE
- core: TFs that belong to two modules at the same time
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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H108

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> We have direct RNA nanopore sequencing from 8 cell lines. We want to call m6A modification sites on each transcript.

- kind: UNSUPPORTED_CORE
- core: m6A modification sites from nanopore reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call m6A modification sites on each transcript" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H110

> We have somatic mutations for 320 patients with five years of follow-up. Is there a method that subtypes the patients from pathway-level mutation scores and compares survival between the subtypes?

- kind: SUPPORTED
- core: pathway-level mutation subtypes compared on five-year survival
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compares survival between the subtypes" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

> We have H3K27ac and expression from 60 samples. We want a regulatory network in which enhancers, not TFs, are the regulators of each gene.

- kind: UNSUPPORTED_CORE
- core: a network in which enhancers are the regulators of genes
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network in which enhancers, not TFs, are the regulators of each gene" -- available from DRAGON or LIONESS-DRAGON.

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

## H112

> We have expression from 6 brain regions of 15 donors. We want a separate co-expression network for each sample.

- kind: SUPPORTED
- core: a co-expression network for each sample from several brain regions
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a separate co-expression network for each sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "15 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H113

> We have a TF-gene network built from spatial spots. Which method finds communities that are also spatially coherent, occupying contiguous regions of the tissue?

- kind: UNSUPPORTED_CORE
- core: communities that are spatially coherent across tissue regions
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

## H114

> We have Visium spatial transcriptomics with motifs and PPI. Is there a method that builds a regulatory network for each spot, smoothed over its neighbouring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks smoothed over neighbouring spots
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

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

## H115

> We want to partition our bipartite TF-gene network so that every gene sits in exactly one community.

- kind: SUPPORTED
- core: a partition of a TF-gene network where each gene is in one community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "We want to partition our bipartite TF-gene network so that every gene sits in exactly one community." -- available from CONDOR.

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

## H116

> We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes.

- kind: UNSUPPORTED_CORE
- core: design of a synthetic promoter
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "design a synthetic promoter sequence that drives strong expression only in hepatocytes" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H117

> We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes.

- kind: UNSUPPORTED_CORE
- core: design of a synthetic promoter
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H118

> We have somatic mutations for 320 patients with five years of follow-up. Is there a method that subtypes the patients from pathway-level mutation scores and compares survival between the subtypes?

- kind: SUPPORTED
- core: pathway-level mutation subtypes compared on five-year survival
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compares survival between the subtypes" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

> We measured reaction rates of an enzyme at 12 substrate concentrations. Which method fits its Km and Vmax?

- kind: UNSUPPORTED_CORE
- core: Michaelis-Menten kinetic parameters
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H120

> We have expression, motifs and PPI from patients at three hospitals. We want a TF-gene network for each patient, and then a federated learning setup so the hospitals never share raw data.

- kind: HALF
- core: a federated learning setup across hospitals
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF-gene network for each patient" -- available from LIONESS-PANDA.
2. "a federated learning setup so the hospitals never share raw data" -- not matched to any registered workflow.

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

No files were inspected and no analysis ran.
```

## H121

> From spatial transcriptomics of 3 sections, we want a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are.

- kind: UNSUPPORTED_CORE
- core: co-expression weighted by the spatial proximity of spots
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H122

> We have a bipartite TF-gene network from 200 liver samples. We want a fuzzy community structure in which every gene has a degree of membership in each community.

- kind: UNSUPPORTED_CORE
- core: fuzzy community memberships with a degree of belonging to every community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a fuzzy community structure in which every gene has a degree of membership in each community" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H123

> From spatial transcriptomics of 3 sections, we want a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are.

- kind: UNSUPPORTED_CORE
- core: co-expression weighted by the spatial proximity of spots
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H124

> We have expression, motifs and PPI from 90 patients, each sampled at one of three time points. We want a network for each patient and a test of which edges differ with the time point.

- kind: SUPPORTED
- core: per-patient networks with edges tested against the time point
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network for each patient" -- available from LIONESS-PANDA.
2. "a test of which edges differ with the time point" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("a test of which edges differ with the time point"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each individual's networks from the different time points can be compared directly: test the within-individual differences of edge weights or targeting scores, for example with a paired test or a linear model with an individual term.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H125

> We genotyped 1,200 participants. Is there a method that estimates each participant's genetic ancestry proportions?

- kind: UNSUPPORTED_CORE
- core: genetic ancestry estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H126

> We have expression from four developmental stages with motifs and PPI. Which method gives one regulatory network per stage so we can compare the stages?

- kind: SUPPORTED
- core: one network per developmental stage, compared between stages
- accept: ['run_panda', 'run_lioness_panda']

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

## H127

> We have imaging mass cytometry of 30 tumor sections with 40 protein markers. We want to segment the cells and assign each one a phenotype.

- kind: UNSUPPORTED_CORE
- core: cell phenotyping from imaging mass cytometry
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment the cells" -- not matched to any registered workflow.
2. "assign each one a phenotype" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H128

> We have expression, motifs and PPI from 90 patients, each sampled at one of three time points. We want a network for each patient and a test of which edges differ with the time point.

- kind: SUPPORTED
- core: per-patient networks with edges tested against the time point
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network for each patient" -- available from LIONESS-PANDA.
2. "a test of which edges differ with the time point" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- "We want a network for each patient"**
Result: regulatory networks (sample-specific), from inputs the request does not state.
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

**Reading 2 -- "test of which edges differ with the time point."**
Result: matching p-value matrices (sample-specific), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (LIONESS-PANDA), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

## H129

> We measured reaction rates of an enzyme at 12 substrate concentrations. Which method fits its Km and Vmax?

- kind: UNSUPPORTED_CORE
- core: Michaelis-Menten kinetic parameters
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H130

> We have expression from 6 brain regions of 15 donors. We want a separate co-expression network for each sample.

- kind: SUPPORTED
- core: a co-expression network for each sample from several brain regions
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a separate co-expression network for each sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "15 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H131

> In our TF-to-gene network, some TFs seem to bridge processes. Is there a method that finds modules where such a TF belongs to two modules at the same time?

- kind: UNSUPPORTED_CORE
- core: TFs that belong to two modules at the same time
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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H132

> We found 400 intronic variants in patients with muscular dystrophy. We want to predict which of them disrupt splicing and by how much.

- kind: UNSUPPORTED_CORE
- core: predicted effects of variants on splicing
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "predict which of them disrupt splicing and by how much" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H133

> We have Visium spatial transcriptomics with motifs and PPI. Is there a method that builds a regulatory network for each spot, smoothed over its neighbouring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks smoothed over neighbouring spots
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

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

## H134

> We have expression at four clinic visits for 70 patients, with motifs and PPI. We want a dynamic model of how each TF's activity evolves from one visit to the next.

- kind: UNSUPPORTED_CORE
- core: a model of how TF activity evolves between visits
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "a dynamic model of how each TF's activity evolves from one visit to the next" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H135

> We found 400 intronic variants in patients with muscular dystrophy. We want to predict which of them disrupt splicing and by how much.

- kind: UNSUPPORTED_CORE
- core: predicted effects of variants on splicing
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which of them disrupt splicing" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "by how much" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H136

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> We have imaging mass cytometry of 30 tumor sections with 40 protein markers. We want to segment the cells and assign each one a phenotype.

- kind: UNSUPPORTED_CORE
- core: cell phenotyping from imaging mass cytometry
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment the cells" -- not matched to any registered workflow.
2. "assign each one a phenotype" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H138

> Which method shows how co-expression differs between early and late disease stage in our 130 samples, after adjusting for sex?

- kind: SUPPORTED
- core: co-expression differences between early and late stage, adjusted for sex
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "Which method shows how co-expression differs between early and late disease stage in our 130 samples, after adjusting for sex?" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H139

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> We have expression, motifs and PPI from 90 patients, each sampled at one of three time points. We want a network for each patient and a test of which edges differ with the time point.

- kind: SUPPORTED
- core: per-patient networks with edges tested against the time point
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a network for each patient" -- available from LIONESS-PANDA.
2. "a test of which edges differ with the time point" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("a test of which edges differ with the time point"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each individual's networks from the different time points can be compared directly: test the within-individual differences of edge weights or targeting scores, for example with a paired test or a linear model with an individual term.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## H142

> We want one TF-gene network for 30,000 genes from 400 samples, but our machine has little memory. Which method fits?

- kind: SUPPORTED
- core: a cohort TF-gene network for 30,000 genes within limited memory
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene network for 30,000 genes from 400 samples" -- available from PANDA, PUMA, OTTER or LIONESS-PANDA.

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

> After finding communities in our TF-gene network, we want to know which genes are most central inside their own community.

- kind: SUPPORTED
- core: how central each gene is inside its community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "which genes are most central inside their own community" -- available from CONDOR.

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

## H144

> From blood exomes of 3,000 older adults, we want to detect clonal hematopoiesis mutations at low allele fractions.

- kind: UNSUPPORTED_CORE
- core: clonal hematopoiesis variant calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect clonal hematopoiesis mutations at low allele fractions" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H145

> We have imaging mass cytometry of 30 tumor sections with 40 protein markers. We want to segment the cells and assign each one a phenotype.

- kind: UNSUPPORTED_CORE
- core: cell phenotyping from imaging mass cytometry
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment the cells" -- not matched to any registered workflow.
2. "assign each one a phenotype" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H146

> We sampled expression hourly for 24 hours. Which method finds TFs whose changes precede their targets' changes by one sampling interval?

- kind: UNSUPPORTED_CORE
- core: regulatory lags where TF changes precede target changes
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_lioness_panda']

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

**Data your question needs.** A TF-level answer needs a motif prior and a PPI network, which you said you do not have ("We sampled expression hourly for 24 hours.").

No files were inspected and no analysis ran.
```

## H147

> We have direct RNA nanopore sequencing from 8 cell lines. We want to call m6A modification sites on each transcript.

- kind: UNSUPPORTED_CORE
- core: m6A modification sites from nanopore reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call m6A modification sites on each transcript" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H148

> Is there a method that finds the communities of our bipartite TF-gene network and then submits them automatically to a public web database?

- kind: HALF
- core: automatic submission of the communities to a web database
- accept: ['run_condor']

Full reply:

```
Fallback recommendation: **CONDOR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a community assignment. **CONDOR** is related to that result.

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

## H149

> We have expression from four developmental stages with motifs and PPI. Which method gives one regulatory network per stage so we can compare the stages?

- kind: SUPPORTED
- core: one network per developmental stage, compared between stages
- accept: ['run_panda', 'run_lioness_panda']

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

## H150

> At a single time point after infection we profiled mRNA and miRNA in 70 samples. We want one regulatory network with both TFs and miRNAs as regulators.

- kind: SUPPORTED
- core: one TF and miRNA network at a single time point
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "We want one regulatory network with both TFs and miRNAs as regulators." -- available from PUMA.

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

## H151

> We have expression from 140 samples run in four batches. We want the co-expression with batch effects removed, and also a batch-corrected count matrix for later differential expression.

- kind: HALF
- core: a batch-corrected count matrix for later differential expression
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "the co-expression with batch effects removed" -- available from COBRA.
2. "a batch-corrected count matrix for later differential expression" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The user has the necessary expression data from 140 samples.
- Batch effects need to be corrected before co-expression analysis.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

What you asked about:

- "a batch-corrected count matrix for later differential expression" — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

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

> We have imaging mass cytometry of 30 tumor sections with 40 protein markers. We want to segment the cells and assign each one a phenotype.

- kind: UNSUPPORTED_CORE
- core: cell phenotyping from imaging mass cytometry
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment the cells" -- not matched to any registered workflow.
2. "assign each one a phenotype" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H153

> We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes.

- kind: UNSUPPORTED_CORE
- core: design of a synthetic promoter
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H154

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> We have expression from 6 brain regions of 15 donors. We want a separate co-expression network for each sample.

- kind: SUPPORTED
- core: a co-expression network for each sample from several brain regions
- accept: ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a separate co-expression network for each sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "15 donors". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
```

## H156

> After finding communities in our TF-gene network, we want to know which genes are most central inside their own community.

- kind: SUPPORTED
- core: how central each gene is inside its community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "we want to know which genes are most central inside their own community" -- available from CONDOR.

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

## H157

> With expression, motifs and PPI from 50 samples, we want each TF's activity per sample, and also each TF's protein amount quantified from our raw mass spectra.

- kind: HALF
- core: TF protein quantification from mass spectra
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "each TF's protein amount quantified from our raw mass spectra" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

Fallback recommendation: **GIRAFFE**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** is related to that result and scale.

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

## H158

> We have H3K27ac and expression from 60 samples. We want a regulatory network in which enhancers, not TFs, are the regulators of each gene.

- kind: UNSUPPORTED_CORE
- core: a network in which enhancers are the regulators of genes
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network in which enhancers, not TFs, are the regulators of each gene" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H159

> We have expression, motifs and PPI from patients at three hospitals. We want a TF-gene network for each patient, and then a federated learning setup so the hospitals never share raw data.

- kind: HALF
- core: a federated learning setup across hospitals
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF-gene network for each patient" -- available from LIONESS-PANDA.

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

No files were inspected and no analysis ran.
```

## H160

> We have expression from four developmental stages with motifs and PPI. Which method gives one regulatory network per stage so we can compare the stages?

- kind: SUPPORTED
- core: one network per developmental stage, compared between stages
- accept: ['run_panda', 'run_lioness_panda']

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

## H161

> With expression, motifs and PPI from 50 samples, we want each TF's activity per sample, and also each TF's protein amount quantified from our raw mass spectra.

- kind: HALF
- core: TF protein quantification from mass spectra
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "each TF's protein amount quantified from our raw mass spectra" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
```

## H162

> We have phosphoproteomics and expression from 80 tumors. Is there a method that infers a network in which kinases regulate the activity of TFs through phosphorylation?

- kind: UNSUPPORTED_CORE
- core: a network in which kinases regulate TF activity
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
Based on what you said — "Is there a method that infers a network in which kinases regulate the activity of TFs through phosphorylation?" — **GIRAFFE** fits better: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed.

Your question asks for a cohort-level regulatory network. **GIRAFFE** fits that result and scale.

**GIRAFFE** (recommend) — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values (one cohort-level result).

Conditional assumptions to confirm:
- It also needs an expression matrix and TF-motif prior and protein-interaction prior, which the request does not mention.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **OTTER**.
- **PUMA** — preferred when: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription; approach: model miRNA-to-gene regulation.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Should I use GIRAFFE, or does another listed option fit your study better?

**What your data allows.** PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network; PUMA also needs a motif prior, a PPI network and a miRNA list. With the data you describe alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H163

> From spatial transcriptomics of 3 sections, we want a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are.

- kind: UNSUPPORTED_CORE
- core: co-expression weighted by the spatial proximity of spots
- nearest (may be offered only with the core stated as not produced): ['run_bonobo', 'run_lioness_coexpression']

Full reply:

```
What I understood you are asking for:
1. "a gene co-expression network in which each gene pair is weighted by how close in space the spots expressing them are" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H164

> We measured reaction rates of an enzyme at 12 substrate concentrations. Which method fits its Km and Vmax?

- kind: UNSUPPORTED_CORE
- core: Michaelis-Menten kinetic parameters
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H165

> In 100 patients we measured methylation and expression at baseline. Is there a method that finds the direct links between the two layers?

- kind: SUPPORTED
- core: direct links between methylation and expression at baseline
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: baseline

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

## H166

> We collected expression at weeks 0, 2 and 4 from 40 patients with motifs and PPI. We want a model of how each patient's regulatory edges at one week follow from their edges at the previous week.

- kind: UNSUPPORTED_CORE
- core: a transition model of how week-4 edges follow from week-2 edges
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "a model of how each patient's regulatory edges at one week follow from their edges at the previous week" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H167

> We genotyped 1,200 participants. Is there a method that estimates each participant's genetic ancestry proportions?

- kind: UNSUPPORTED_CORE
- core: genetic ancestry estimates
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H168

> We want one TF-gene network for 30,000 genes from 400 samples, but our machine has little memory. Which method fits?

- kind: SUPPORTED
- core: a cohort TF-gene network for 30,000 genes within limited memory
- accept: ['run_otter', 'run_panda']

Full reply:

```
What I understood you are asking for:
1. "one TF-gene network" -- available from PANDA or OTTER.

Based on what you said — "but our machine has little memory." — **OTTER** fits better: the network is large and memory or runtime is a concern.

Your question asks for a cohort-level regulatory network. **OTTER** fits that result and scale.

**OTTER** (recommend) — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- It also needs a TF-motif prior and protein-interaction prior, which the request does not mention.

Other compatible option(s):
- **PANDA** — preferred when: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis; approach: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

About your concern that memory is a limiting factor (for example, an earlier run ran out of memory):
- **OTTER** — `precision=single` keeps OTTER's largest array, the gene-by-gene co-expression matrix, in single precision during the optimization. The loader first computes that matrix in double precision, so peak memory while loading is not reduced, and the optimization and the output network stay in double precision.

Should I use OTTER, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## H169

> After finding communities in our TF-gene network, we want to know which genes are most central inside their own community.

- kind: SUPPORTED
- core: how central each gene is inside its community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "which genes are most central inside their own community." -- available from CONDOR.

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

## H170

> We have Visium spatial transcriptomics with motifs and PPI. Is there a method that builds a regulatory network for each spot, smoothed over its neighbouring spots?

- kind: UNSUPPORTED_CORE
- core: per-spot networks smoothed over neighbouring spots
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

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

## H171

> We took biopsies from four regions of each of 25 tumors, with motifs and PPI. We want a regulatory network for each biopsy so we can compare the regions.

- kind: SUPPORTED
- core: a network per biopsy compared across tumor regions
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network for each biopsy" -- available from LIONESS-PANDA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 25 tumors, 26 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a motif prior and a PPI network. LIONESS-PUMA and PUMA also need an expression matrix and a miRNA list. Do you also have a miRNA list?

No files were inspected and no analysis ran.
```

## H172

> We have a TF-gene network built from spatial spots. Which method finds communities that are also spatially coherent, occupying contiguous regions of the tissue?

- kind: UNSUPPORTED_CORE
- core: communities that are spatially coherent across tissue regions
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

## H173

> We found 400 intronic variants in patients with muscular dystrophy. We want to predict which of them disrupt splicing and by how much.

- kind: UNSUPPORTED_CORE
- core: predicted effects of variants on splicing
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which of them disrupt splicing" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "by how much" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H174

> We collected expression at weeks 0, 2 and 4 from 40 patients with motifs and PPI. We want a model of how each patient's regulatory edges at one week follow from their edges at the previous week.

- kind: UNSUPPORTED_CORE
- core: a transition model of how week-4 edges follow from week-2 edges
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "a model of how each patient's regulatory edges at one week follow from their edges at the previous week" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H175

> We have expression at four clinic visits for 70 patients, with motifs and PPI. We want a dynamic model of how each TF's activity evolves from one visit to the next.

- kind: UNSUPPORTED_CORE
- core: a model of how TF activity evolves between visits
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "a dynamic model of how each TF's activity evolves from one visit to the next" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H176

> We measured reaction rates of an enzyme at 12 substrate concentrations. Which method fits its Km and Vmax?

- kind: UNSUPPORTED_CORE
- core: Michaelis-Menten kinetic parameters
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## H177

> Is there a method that finds the communities of our bipartite TF-gene network and then submits them automatically to a public web database?

- kind: HALF
- core: automatic submission of the communities to a web database
- accept: ['run_condor']

Full reply:

```
Fallback recommendation: **CONDOR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a community assignment. **CONDOR** is related to that result.

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

## H178

> We have a bipartite TF-gene network from 200 liver samples. We want a fuzzy community structure in which every gene has a degree of membership in each community.

- kind: UNSUPPORTED_CORE
- core: fuzzy community memberships with a degree of belonging to every community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "We want a fuzzy community structure in which every gene has a degree of membership in each community." -- available from CONDOR.

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

## H179

> We collected expression at weeks 0, 2 and 4 from 40 patients with motifs and PPI. We want a model of how each patient's regulatory edges at one week follow from their edges at the previous week.

- kind: UNSUPPORTED_CORE
- core: a transition model of how week-4 edges follow from week-2 edges
- nearest (may be offered only with the core stated as not produced): ['run_lioness_panda']

Full reply:

```
What I understood you are asking for:
1. "a model of how each patient's regulatory edges at one week follow from their edges at the previous week" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H180

> From blood exomes of 3,000 older adults, we want to detect clonal hematopoiesis mutations at low allele fractions.

- kind: UNSUPPORTED_CORE
- core: clonal hematopoiesis variant calls
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "detect clonal hematopoiesis mutations at low allele fractions" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H181

> We assembled the genome of a new soil bacterium. Which method should annotate its genes and predict their functions?

- kind: UNSUPPORTED_CORE
- core: bacterial genome annotation
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
About "predict their functions": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

> In our TF-to-gene network, some TFs seem to bridge processes. Is there a method that finds modules where such a TF belongs to two modules at the same time?

- kind: UNSUPPORTED_CORE
- core: TFs that belong to two modules at the same time
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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H183

> We have direct RNA nanopore sequencing from 8 cell lines. We want to call m6A modification sites on each transcript.

- kind: UNSUPPORTED_CORE
- core: m6A modification sites from nanopore reads
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "call m6A modification sites on each transcript" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H184

> We have expression at four clinic visits for 70 patients, with motifs and PPI. We want a dynamic model of how each TF's activity evolves from one visit to the next.

- kind: UNSUPPORTED_CORE
- core: a model of how TF activity evolves between visits
- nearest (may be offered only with the core stated as not produced): ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "a dynamic model of how each TF's activity evolves from one visit to the next" -- available from GIRAFFE.

Assumptions behind this recommendation (not confirmed facts):

- The model will utilize expression data from multiple visits.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors.

Captured request parameters:

- `expression_file`: four

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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H185

> We have phosphoproteomics and expression from 80 tumors. Is there a method that infers a network in which kinases regulate the activity of TFs through phosphorylation?

- kind: UNSUPPORTED_CORE
- core: a network in which kinases regulate TF activity
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H186

> At a single time point after infection we profiled mRNA and miRNA in 70 samples. We want one regulatory network with both TFs and miRNAs as regulators.

- kind: SUPPORTED
- core: one TF and miRNA network at a single time point
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "one regulatory network with both TFs and miRNAs as regulators" -- available from PUMA.

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

## H187

> We took biopsies from four regions of each of 25 tumors, with motifs and PPI. We want a regulatory network for each biopsy so we can compare the regions.

- kind: SUPPORTED
- core: a network per biopsy compared across tumor regions
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network for each biopsy" -- available from LIONESS-PANDA.

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

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 25 tumors, 26 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** Your request names only a motif prior and a PPI network. LIONESS-PUMA and PUMA also need an expression matrix and a miRNA list. Do you also have a miRNA list?

No files were inspected and no analysis ran.
```

## H188

> With expression, motifs and PPI from 50 samples, we want each TF's activity per sample, and also each TF's protein amount quantified from our raw mass spectra.

- kind: HALF
- core: TF protein quantification from mass spectra
- accept: ['run_giraffe']

Full reply:

```
What I understood you are asking for:
1. "each TF's activity per sample" -- available from GIRAFFE.
2. "each TF's protein amount quantified from our raw mass spectra" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## H189

> We found 400 intronic variants in patients with muscular dystrophy. We want to predict which of them disrupt splicing and by how much.

- kind: UNSUPPORTED_CORE
- core: predicted effects of variants on splicing
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which of them disrupt splicing" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "by how much" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H190

> We want to partition our bipartite TF-gene network so that every gene sits in exactly one community.

- kind: SUPPORTED
- core: a partition of a TF-gene network where each gene is in one community
- accept: ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "partition our bipartite TF-gene network so that every gene sits in exactly one community." -- available from CONDOR.

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

## H191

> We found 400 intronic variants in patients with muscular dystrophy. We want to predict which of them disrupt splicing and by how much.

- kind: UNSUPPORTED_CORE
- core: predicted effects of variants on splicing
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "which of them disrupt splicing" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "by how much" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## H192

> We have a bipartite TF-gene network from 200 liver samples. We want a fuzzy community structure in which every gene has a degree of membership in each community.

- kind: UNSUPPORTED_CORE
- core: fuzzy community memberships with a degree of belonging to every community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a fuzzy community structure in which every gene has a degree of membership in each community." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H193

> We have proteomics and metabolomics from 90 patients. We want a network of direct links between the two layers, and then the causal direction of each link.

- kind: HALF
- core: learning the causal direction of each link
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
What I understood you are asking for:
1. "network of direct links between the two layers" -- available from DRAGON.
2. "causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "We want a network of direct links between the two layers, and then the causal direction of each link.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

> Which method shows how co-expression differs between early and late disease stage in our 130 samples, after adjusting for sex?

- kind: SUPPORTED
- core: co-expression differences between early and late stage, adjusted for sex
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "how co-expression differs between early and late disease stage in our 130 samples, after adjusting for sex" -- available from COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## H195

> We measured reaction rates of an enzyme at 12 substrate concentrations. Which method fits its Km and Vmax?

- kind: UNSUPPORTED_CORE
- core: Michaelis-Menten kinetic parameters
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## H196

> Is there a method that finds the communities of our bipartite TF-gene network and then submits them automatically to a public web database?

- kind: HALF
- core: automatic submission of the communities to a web database
- accept: ['run_condor']

Full reply:

```
Fallback recommendation: **CONDOR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a community assignment. **CONDOR** is related to that result.

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

## H197

> In 100 patients we measured methylation and expression at baseline. Is there a method that finds the direct links between the two layers?

- kind: SUPPORTED
- core: direct links between methylation and expression at baseline
- accept: ['run_dragon', 'run_lioness_dragon']

Full reply:

```
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: baseline

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

## H198

> We have H3K27ac and expression from 60 samples. We want a regulatory network in which enhancers, not TFs, are the regulators of each gene.

- kind: UNSUPPORTED_CORE
- core: a network in which enhancers are the regulators of genes
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "a regulatory network in which enhancers, not TFs, are the regulators of each gene" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H199

> In our TF-to-gene network, some TFs seem to bridge processes. Is there a method that finds modules where such a TF belongs to two modules at the same time?

- kind: UNSUPPORTED_CORE
- core: TFs that belong to two modules at the same time
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

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## H200

> We have a bipartite TF-gene network from 200 liver samples. We want a fuzzy community structure in which every gene has a degree of membership in each community.

- kind: UNSUPPORTED_CORE
- core: fuzzy community memberships with a degree of belonging to every community
- nearest (may be offered only with the core stated as not produced): ['run_condor']

Full reply:

```
What I understood you are asking for:
1. "a fuzzy community structure in which every gene has a degree of membership in each community." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H201

> We have expression from 140 samples run in four batches. We want the co-expression with batch effects removed, and also a batch-corrected count matrix for later differential expression.

- kind: HALF
- core: a batch-corrected count matrix for later differential expression
- accept: ['run_cobra']

Full reply:

```
What I understood you are asking for:
1. "co-expression with batch effects removed" -- available from COBRA.
2. "batch-corrected count matrix for later differential expression" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The expression data is suitable for co-expression analysis after batch effect removal.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

What you asked about:

- "a batch-corrected count matrix for later differential expression" — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

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

> At a single time point after infection we profiled mRNA and miRNA in 70 samples. We want one regulatory network with both TFs and miRNAs as regulators.

- kind: SUPPORTED
- core: one TF and miRNA network at a single time point
- accept: ['run_puma', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "We want one regulatory network with both TFs and miRNAs as regulators." -- available from PUMA.

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

## H203

> We have H3K27ac and expression from 60 samples. We want a regulatory network in which enhancers, not TFs, are the regulators of each gene.

- kind: UNSUPPORTED_CORE
- core: a network in which enhancers are the regulators of genes
- nearest (may be offered only with the core stated as not produced): ['run_panda']

Full reply:

```
What I understood you are asking for:
1. "We want a regulatory network in which enhancers, not TFs, are the regulators of each gene." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H204

> We have expression, motifs and PPI from patients at three hospitals. We want a TF-gene network for each patient, and then a federated learning setup so the hospitals never share raw data.

- kind: HALF
- core: a federated learning setup across hospitals
- accept: ['run_lioness_panda', 'run_lioness_puma']

Full reply:

```
What I understood you are asking for:
1. "a TF-gene network for each patient" -- available from LIONESS-PANDA.

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

No files were inspected and no analysis ran.
```

## H205

> We have somatic mutations for 320 patients with five years of follow-up. Is there a method that subtypes the patients from pathway-level mutation scores and compares survival between the subtypes?

- kind: SUPPORTED
- core: pathway-level mutation subtypes compared on five-year survival
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compares survival between the subtypes" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

> We have a TF-gene network built from spatial spots. Which method finds communities that are also spatially coherent, occupying contiguous regions of the tissue?

- kind: UNSUPPORTED_CORE
- core: communities that are spatially coherent across tissue regions
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

## H207

> We have somatic mutations for 320 patients with five years of follow-up. Is there a method that subtypes the patients from pathway-level mutation scores and compares survival between the subtypes?

- kind: SUPPORTED
- core: pathway-level mutation subtypes compared on five-year survival
- accept: ['run_sambar']

Full reply:

```
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "compares survival between the subtypes" — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

> We want to design a synthetic promoter sequence that drives strong expression only in hepatocytes.

- kind: UNSUPPORTED_CORE
- core: design of a synthetic promoter
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "design a synthetic promoter sequence that drives strong expression only in hepatocytes." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

## H209

> We have phosphoproteomics and expression from 80 tumors. Is there a method that infers a network in which kinases regulate the activity of TFs through phosphorylation?

- kind: UNSUPPORTED_CORE
- core: a network in which kinases regulate TF activity
- nearest (may be offered only with the core stated as not produced): ['run_panda', 'run_giraffe']

Full reply:

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- "a network in which kinases regulate the activity of TFs"**
Result: regulatory networks (aggregate), from inputs the request does not state.
- TF-only regulatory network:
  - **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
  - **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.
- TF-only signed regulatory-effect network:
  - **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.
- TF/miRNA regulatory network:
  - **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

**Reading 2 -- aggregate multi omic network**
Result: multi omic network (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PANDA or PUMA or OTTER or GIRAFFE), 2 (no registered workflow)? If a reading should use different data, say which.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## H210

> We have imaging mass cytometry of 30 tumor sections with 40 protein markers. We want to segment the cells and assign each one a phenotype.

- kind: UNSUPPORTED_CORE
- core: cell phenotyping from imaging mass cytometry
- nearest (may be offered only with the core stated as not produced): []

Full reply:

```
What I understood you are asking for:
1. "segment the cells and assign each one a phenotype" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```
