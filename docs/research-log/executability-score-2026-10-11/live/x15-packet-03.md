## S051

Request (turn 1): We have expression from 90 samples and want one TF-gene regulatory network for them.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network for them" -- available from PANDA, OTTER, LIONESS-PANDA or GIRAFFE.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**What your data allows.** PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Leads to PANDA, OTTER or GIRAFFE
- next step: Start a new task

## S052

Request (turn 1): We have expression, motifs and PPI for 100 samples. We want to know which TFs physically form complexes and in what stoichiometry.

Requirements to judge (in the user's words):
R1: "which TFs physically form complexes and in what stoichiometry"

Reply:

````
What I understood you are asking for:
1. "which TFs physically form complexes and in what stoichiometry" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “which TFs physically form complexes and in what stoichiometry” — PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- next step: Start a new task

## S053

Request (turn 1): We have expression, motifs and PPI from 85 samples. We want to rank the TFs by how strongly they target genes in each sample.

Requirements to judge (in the user's words):
R1: "rank the TFs by how strongly they target genes in each sample"

Reply:

````
What I understood you are asking for:
1. "rank the TFs by how strongly they target genes in each sample" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: Sum edge weights per TF per sample from the edge-by-sample table; NetZoo does not compute it.

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

For your question ("rank the TFs by how strongly they target genes in each sample."):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- point: Your question: which regulators change most; the reply says what GIRAFFE give toward it and the step after each.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S054

Request (turn 1): We want CRISPR guide RNAs designed to knock out the 20 hub TFs of our network.

Requirements to judge (in the user's words):
R1: "CRISPR guide RNAs designed to knock out the 20 hub TFs"

Reply:

````
What I understood you are asking for:
1. "CRISPR guide RNAs designed to knock out the 20 hub TFs of our network" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “CRISPR guide RNAs designed to knock out the 20 hub TFs of our network” — Not matched to any registered workflow.
- next step: Start a new task

## S055

Request (turn 1): We have Visium spatial transcriptomics of 3,000 spots. We want TF-gene networks that borrow information from each spot's neighbouring spots.

Requirements to judge (in the user's words):
R1: "TF-gene networks that borrow information from each spot's neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks that borrow information from each spot's neighbouring spots" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene networks that borrow information from each spot's neighbouring spots” — Not matched to any registered workflow.
- next step: Start a new task

## S056

Request (turn 1): We have RNA-seq from 140 liver biopsies, a TF motif prior and a PPI network. We want a single TF-gene regulatory network for the whole cohort.

Requirements to judge (in the user's words):
R1: "a single TF-gene regulatory network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "a single TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S057

Request (turn 1): We have somatic mutations for 250 tumors. We want to know which of the mutations are drivers.

Requirements to judge (in the user's words):
R1: "which of the mutations are drivers"

Reply:

````
What I understood you are asking for:
1. "which of the mutations are drivers" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “which of the mutations are drivers” — SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.
- next step: Start a new task

## S058

Request (turn 1): We have expression, TF motifs, PPI and miRNA target predictions for 60 patients. We want a separate TF and miRNA regulatory network for each patient.

Requirements to judge (in the user's words):
R1: "a separate TF and miRNA regulatory network for each patient"

Reply:

````
What I understood you are asking for:
1. "a separate TF and miRNA regulatory network for each patient" -- available from LIONESS-PUMA.

Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- sample-specific regulatory networks**
Result: regulatory networks (sample-specific), from inputs the request does not state.
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

**Reading 2 -- sample-specific regulatory networks**
Result: regulatory networks (sample-specific), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA → LIONESS-PUMA**
  - Registered purpose: Infer aggregate PUMA and sample-specific LIONESS-PUMA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

Which reading should we start with: 1 (LIONESS-PANDA), 2 (LIONESS-PUMA)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1 — LIONESS-PANDA: a per-sample TF-gene regulatory network · One TF-gene network per sample, derived leave-one-out from the cohort
- option: Reading 2 — LIONESS-PUMA: a per-sample miRNA-gene regulatory network · One TF + miRNA network per sample, derived leave-one-out from the cohort
- next step: Plan LIONESS-PUMA with my data
- next step: Start a new task

## S059

Request (turn 1): We have ATAC-seq peaks and expression from 40 samples. We want to discover new TF binding motifs de novo.

Requirements to judge (in the user's words):
R1: "discover new TF binding motifs de novo"

Reply:

````
What I understood you are asking for:
1. "discover new TF binding motifs de novo" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “discover new TF binding motifs de novo” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S060

Request (turn 1): We have proteomics and phosphoproteomics for 75 matched samples. We want a two-layer network of direct associations between them.

Requirements to judge (in the user's words):
R1: "a two-layer network of direct associations between them"

Reply:

````
What I understood you are asking for:
1. "a two-layer network of direct associations between them" -- available from DRAGON.

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

For your question ("a two-layer network of direct associations between them"):
- **DRAGON** — Build one network per time point or condition on the same features and compare the cross-layer edges; this does not use the pairing -- to keep it, use LIONESS-DRAGON and compare each individual's samples.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what DRAGON give toward it and the step after each.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S061

Request (turn 1): We want 3D structures predicted for 12 TF proteins from their amino-acid sequences.

Requirements to judge (in the user's words):
R1: "3D structures predicted for 12 TF proteins"

Reply:

````
What I understood you are asking for:
1. "3D structures predicted" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “3D structures predicted” — Not matched to any registered workflow.
- next step: Start a new task

## S062

Request (turn 1): We have expression, motifs and PPI from 100 samples. We want the TF-gene network and also the refined TF-TF cooperation network the method estimates along the way.

Requirements to judge (in the user's words):
R1: "the TF-gene network"
R2: "the refined TF-TF cooperation network the method estimates along the way"

Reply:

````
What I understood you are asking for:
1. "TF-gene network" -- available from PANDA.
2. "refined TF-TF cooperation network the method estimates along the way" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The expression, motifs, and PPI data are compatible for constructing the requested networks.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level regulatory network with TF activities.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “refined TF-TF cooperation network the method estimates along the way” — Not matched to any registered workflow.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S063

Request (turn 1): We have RNA-seq from 140 liver biopsies, a TF motif prior and a PPI network. We want a single TF-gene regulatory network for the whole cohort.

Requirements to judge (in the user's words):
R1: "a single TF-gene regulatory network for the whole cohort"

Reply:

````
What I understood you are asking for:
1. "a single TF-gene regulatory network for the whole cohort" -- available from PANDA or OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S064

Request (turn 1): We have expression from 200 samples processed in 4 batches. We want gene co-expression with the batch-associated part separated out.

Requirements to judge (in the user's words):
R1: "gene co-expression with the batch-associated part separated out"

Reply:

````
What I understood you are asking for:
1. "gene co-expression with the batch-associated part separated out" -- available from COBRA.

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
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “We want gene co-expression with the…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S065

Request (turn 1): We want one gene co-expression network across our 120 samples.
Request (turn 2): Actually we need one for each sample.

Requirements to judge (in the user's words):
R1: "one for each sample"

Reply:

````
What I understood you are asking for:
1. "one for each sample" -- available from LIONESS-PANDA or LIONESS-PUMA.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S066

Request (turn 1): We have expression, motifs and PPI from 80 patients. We want to prove which TFs causally drive the disease state.

Requirements to judge (in the user's words):
R1: "prove which TFs causally drive the disease state"

Reply:

````
What I understood you are asking for:
1. "prove which TFs causally drive the disease state" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “prove which TFs causally drive the disease state” — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S067

Request (turn 1): We have raw FASTQ files from 30 exomes. We want germline variant calls in VCF format.

Requirements to judge (in the user's words):
R1: "germline variant calls in VCF format"

Reply:

````
What I understood you are asking for:
1. "germline variant calls in VCF format" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “germline variant calls in VCF format” — Not matched to any registered workflow.
- next step: Start a new task

## S068

Request (turn 1): We want the communities of our bipartite TF-gene network, and then to fine-map the causal GWAS variants inside each community.

Requirements to judge (in the user's words):
R1: "the communities of our bipartite TF-gene network"
R2: "fine-map the causal GWAS variants inside each community"

Reply:

````
What I understood you are asking for:
1. "We want the communities of our bipartite TF-gene network" -- available from CONDOR.
2. "to fine-map the causal GWAS variants inside each community." -- not available here: no registered workflow produces this. CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).

About "to fine-map the causal GWAS variants inside each community.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Assumptions behind this recommendation (not confirmed facts):

- The user intends to analyze causal GWAS variants in relation to the identified communities.

Fallback recommendation: **CONDOR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a community assignment. **CONDOR** is related to that result.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: CONDOR is the closest registered match, but it is not a verified match for your request.
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- not available: “to fine-map the causal GWAS variants inside each community.” — CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Start a new task

## S069

Request (turn 1): We have expression at 10 time points after drug treatment, with motifs and PPI. We want a model that simulates how the regulatory network evolves between time points.

Requirements to judge (in the user's words):
R1: "a model that simulates how the regulatory network evolves between time points"

Reply:

````
What I understood you are asking for:
1. "a model that simulates how the regulatory network evolves between time points" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that simulates how the regulatory network evolves between time points” — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S070

Request (turn 1): We have motifs, PPI and expression from 50 samples. Is there a method that fits one TF-gene network to agree with both the PPI and the co-expression?

Requirements to judge (in the user's words):
R1: "fits one TF-gene network to agree with both the PPI and the co-expression"

Reply:

````
What I understood you are asking for:
1. "fits one TF-gene network to agree with both the PPI and the co-expression" -- available from OTTER.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S071

Request (turn 1): We want per-sample TF-gene networks from expression, motifs and PPI of 50 samples.
Request (turn 2): Those samples are 50 spatial spots from one tissue section, and neighbouring spots should share information.

Requirements to judge (in the user's words):
R1: "neighbouring spots should share information"

Reply:

````
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample distance matrix. **SAMBAR** fits that result and scale.

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
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level sample distance matrix.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S072

Request (turn 1): We have raw FASTQ files from 30 exomes. We want germline variant calls in VCF format.

Requirements to judge (in the user's words):
R1: "germline variant calls in VCF format"

Reply:

````
What I understood you are asking for:
1. "germline variant calls in VCF format" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “germline variant calls in VCF format” — Not matched to any registered workflow.
- next step: Start a new task

## S073

Request (turn 1): We have somatic mutation calls for 310 tumors. We want to group the patients into subtypes using pathway-level mutation scores.

Requirements to judge (in the user's words):
R1: "group the patients into subtypes using pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "group the patients into subtypes using pathway-level mutation scores" -- available from SAMBAR.

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
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level set of sample subtypes.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S074

Request (turn 1): We have expression, motifs and PPI from 88 samples. We want each TF's activity in every sample, estimated apart from the TF's own mRNA level.

Requirements to judge (in the user's words):
R1: "each TF's activity in every sample, estimated apart from the TF's own mRNA level"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in every sample, estimated apart from the TF's own mRNA level." -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "estimated apart from the TF's own mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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
````

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S075

Request (turn 1): We have expression, motifs and PPI from 85 samples. We want to rank the TFs by how strongly they target genes in each sample.

Requirements to judge (in the user's words):
R1: "rank the TFs by how strongly they target genes in each sample"

Reply:

````
What I understood you are asking for:
1. "rank the TFs by how strongly they target genes in each sample" -- available from LIONESS-PANDA or LIONESS-PUMA's output plus a step you run outside NetZoo: Sum edge weights per TF per sample from the edge-by-sample table; NetZoo does not compute it.

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

For your question ("rank the TFs by how strongly they target genes in each sample."):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- point: Your question: which regulators change most; the reply says what GIRAFFE give toward it and the step after each.
- next step: Plan GIRAFFE with my data
- next step: Start a new task
